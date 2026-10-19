"""A frozen, real-data-only test of post-onset Combine burst and NFL LOS crossing.

Scientific dependencies are optional (install perfectjet[scouting]). NFL plays
construct labels only. Every inner split rebuilds context labels, source nuisance
fits, measurement variances, imputation, scaling and scouting fits. The 2025
cohort is development data because the project already inspected it.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import pandas as pd

from .schema import available, admissible_measurements
from .official import load_official_directory, FRONT_DRILLS, MEASUREMENT_COLUMNS
from .burst import BurstProtocol, extract_bursts, ScalarReliabilityModel, IntegratedScoutCorrection

PROTOCOL = {
    "schema": "perfectjet/nfl-burst-transfer/1",
    "primary": "forty-yard post-onset half-second burst -> context-adjusted rookie LOS-crossing time",
    "secondary": "same functional on predeclared front starts, with drill nuisance adjustment",
    "horizon_seconds": 0.5, "onset_speed_yards_per_second": 0.5,
    "sustained_frames": 3, "maximum_turn_degrees": 15,
    "baseline_penalties": [10.0, 100.0, 1000.0], "inner_player_folds": 3,
    "source_nuisance_penalty": 100.0, "scout_correction_penalty": 1.0,
    "minimum_plays": 30, "primary_metric": "equal-athlete paired squared-error reduction",
    "decision_rule": "shortlist lowest predicted quartile per class; hit = target below training lower quartile",
    "source_noise": "estimated from independent repeat attempts; branch ranges are descriptive",
    "conventional": list(MEASUREMENT_COLUMNS.values()),
    "availability": "all five raw drill flags and attempt counts shared by every model",
    "NGS": "strong comparator includes supplied draft grades under declared pre-draft interpretation; repeat without NGS",
    "context": "starting LOS depth, width, speed, situation and alignment; fit on training athletes only",
    "NFL_horizon": "rookie regular season; training seasons strictly before evaluated class",
    "2025": "previously inspected development evidence, never a fresh holdout",
    "candidate_status": "protocol is fixed before this new experiment, but the data have prior adaptive use",
}


def _finite(x):
    return isinstance(x, (int, float)) and np.isfinite(x)


def _regressor(frame, alpha):
    nums = [c for c in frame if pd.api.types.is_numeric_dtype(frame[c])]
    cats = [c for c in frame if c not in nums]
    transformers = []
    if nums:
        transformers.append(("numeric", make_pipeline(
            SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
            StandardScaler()), nums))
    if cats:
        transformers.append(("category", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cats))
    return make_pipeline(ColumnTransformer(transformers), Ridge(alpha=alpha))


def predictor_frame(ds, ids, include_ngs=True):
    """Only pre-draft source inputs; counts use raw attempts, not NFL-selected events."""
    counts = Counter((a.athlete_id, a.drill) for a in ds.attempts
                     if a.athlete_id in ds.athletes
                     and available(a.recorded_on, f"{ds.athletes[a.athlete_id].draft_year}-04-20"))
    names = [c for c in MEASUREMENT_COLUMNS.values() if include_ngs or not c.startswith("ngs_")]
    rows = []
    for aid in ids:
        athlete = ds.athletes[aid]
        use, _ = admissible_measurements(athlete, f"{athlete.draft_year}-04-20", names)
        row = {name: use.get(name, np.nan) for name in names}
        row["combine_position"] = athlete.position
        for drill in FRONT_DRILLS:
            n = counts[aid, drill]
            row["count__"+drill] = float(n)
            row["available__"+drill] = float(n > 0)
        rows.append(row)
    return pd.DataFrame(rows, index=ids)


def context_frame(plays):
    numeric = ("down", "yards_to_go", "yardline_number", "quarter",
               "pre_snap_home_score", "pre_snap_visitor_score", "snap_depth", "snap_width", "snap_speed")
    categorical = ("lined_up_position", "offense_formation", "blitzing", "team_abbr", "possession_team")
    rows = []
    for play in plays:
        c = play.context
        row = {k: float(c[k]) if _finite(c.get(k)) else np.nan for k in numeric}
        d = c.get("snap_depth")
        row["sqrt_forward_depth"] = np.sqrt(max(0.0, d)) if _finite(d) else np.nan
        row["log_forward_depth"] = np.log1p(max(0.0, d)) if _finite(d) else np.nan
        row.update({k: str(c.get(k, "MISSING")) for k in categorical})
        rows.append(row)
    return pd.DataFrame(rows)


def _groups(ds, ids, k, seed):
    originals = {a: ds.athletes[a].bootstrap_group or a for a in ids}
    unique = sorted(set(originals.values()))
    np.random.default_rng(seed).shuffle(unique)
    assignment = {a: i % k for i, a in enumerate(unique)}
    return {a: assignment[originals[a]] for a in ids}


def _context_predict(train, test):
    if not train or not test:
        raise ValueError("context split has no plays")
    f = context_frame(train)
    reg = _regressor(f, 100.0)
    counts = Counter(p.athlete_id for p in train)
    weights = np.array([1.0/counts[p.athlete_id] for p in train])
    weights *= len(weights)/weights.sum()
    reg.fit(f, [p.outcome for p in train], ridge__sample_weight=weights)
    return reg.predict(context_frame(test))


def targets(ds, train_ids, test_ids, cutoff, seed):
    """Raw residual means; outcome precision is separate from the scoring target."""
    trset, teset = set(train_ids), set(test_ids)
    tr = [p for p in ds.plays if p.athlete_id in trset and p.season < cutoff
          and p.season == ds.athletes[p.athlete_id].draft_year]
    te = [p for p in ds.plays if p.athlete_id in teset
          and p.season == ds.athletes[p.athlete_id].draft_year]
    folds = _groups(ds, train_ids, 3, seed)
    residuals = []
    for fold in range(3):
        a = [p for p in tr if folds[p.athlete_id] != fold]
        b = [p for p in tr if folds[p.athlete_id] == fold]
        if a and b:
            residuals.extend(zip(b, np.array([p.outcome for p in b])-_context_predict(a, b)))
    if tr and te:
        residuals.extend(zip(te, np.array([p.outcome for p in te])-_context_predict(tr, te)))
    rows = [{"athlete": p.athlete_id, "game": p.play_id.split(":")[0], "r": float(r)} for p, r in residuals]
    if not rows:
        raise ValueError("no eligible targets in split")
    table = pd.DataFrame(rows)
    y, precision, counts = {}, {}, {}
    for aid, g in table.groupby("athlete"):
        if len(g) < ds.outcome_definition.get("minimum_plays", 30):
            continue
        y[aid] = float(g.r.mean())
        clusters = g.assign(centered=g.r-g.r.mean()).groupby("game").centered.sum()
        games = len(clusters)
        # Clustered intercept variance for THIS play-weighted player mean.
        # It omits context-reference estimation uncertainty and is descriptive.
        precision[aid] = float(games/(games-1)*np.sum((clusters/len(g))**2)) if games>1 else None
        counts[aid] = len(g)
    return y, precision, counts


def _source_reference(ds, observations, train_ids, test_ids, include_ngs, seed):
    """Cross-fit the source-only conventional/drill reference before latent pooling."""
    train_set = set(train_ids)
    train_obs = [o for o in observations if o.athlete_id in train_set]
    test_obs = [o for o in observations if o.athlete_id in set(test_ids)]
    if not train_obs:
        return [], []
    def frame(obs):
        x = predictor_frame(ds, [o.athlete_id for o in obs], include_ngs).reset_index(drop=True)
        x["source_drill"] = [o.drill for o in obs]
        x["initial_speed"] = [o.initial_speed for o in obs]
        return x
    def predict(a, b):
        reg = _regressor(frame(a), PROTOCOL["source_nuisance_penalty"])
        counts = Counter(o.athlete_id for o in a)
        w = np.array([1.0/counts[o.athlete_id] for o in a]); w *= len(w)/w.sum()
        reg.fit(frame(a), [o.value for o in a], ridge__sample_weight=w)
        return reg.predict(frame(b))
    folds = _groups(ds, train_ids, 3, seed+101)
    residual = []
    for fold in range(3):
        a = [o for o in train_obs if folds[o.athlete_id] != fold]
        b = [o for o in train_obs if folds[o.athlete_id] == fold]
        if a and b:
            residual.extend(replace(o, value=o.value-float(p)) for o,p in zip(b,predict(a,b)))
    evaluated = [replace(o,value=o.value-float(p)) for o,p in zip(test_obs,predict(train_obs,test_obs))] if test_obs else []
    return residual, evaluated


def fit_split(ds, observations, train_ids, test_ids, cutoff, alpha, include_ngs=True, seed=81014):
    if set(train_ids)&set(test_ids):
        raise ValueError("athlete leakage")
    train_groups = {ds.athletes[a].bootstrap_group or a for a in train_ids}
    test_groups = {ds.athletes[a].bootstrap_group or a for a in test_ids}
    if train_groups & test_groups:
        raise ValueError("original-athlete leakage")
    y, nu, n = targets(ds, train_ids, test_ids, cutoff, seed)
    tr, te = sorted(set(train_ids)&set(y)), sorted(set(test_ids)&set(y))
    if len({ds.athletes[a].bootstrap_group or a for a in tr})<6 or not te:
        raise ValueError("insufficient target athletes in split")
    x = predictor_frame(ds,tr,include_ngs)
    base = _regressor(x,alpha).fit(x,[y[a] for a in tr])
    pb = base.predict(predictor_frame(ds,te,include_ngs))
    # Loading learns from out-of-player baseline residuals, not an in-sample fit.
    foldmap = _groups(ds,tr,3,seed+211)
    residual = {}
    for fold in range(3):
        a = [q for q in tr if foldmap[q]!=fold]; b = [q for q in tr if foldmap[q]==fold]
        if a and b:
            yy, _, _ = targets(ds,a,b,cutoff,seed+301+fold)
            aa = [q for q in a if q in yy]; ab = [q for q in b if q in yy]
            if not aa or not ab:
                continue
            xx = predictor_frame(ds,aa,include_ngs)
            bb = _regressor(xx,alpha).fit(xx,[yy[q] for q in aa])
            residual.update({q:yy[q]-float(p) for q,p in zip(ab,bb.predict(predictor_frame(ds,ab,include_ngs)))})
    source_tr, source_te = _source_reference(ds,observations,tr,te,include_ngs,seed)
    reliability = ScalarReliabilityModel.fit(source_tr,train_ids=tr)
    post_tr = [reliability.posterior(source_tr,athlete_id=a) for a in tr]
    post_te = [reliability.posterior(source_te,athlete_id=a) for a in te]
    fallback_variance = float(np.median([v for a,v in nu.items() if a in tr and v is not None])) if any(a in tr and v is not None for a,v in nu.items()) else 0.0
    correction = IntegratedScoutCorrection.fit(post_tr,[residual.get(a,0.0) for a in tr],
                 outcome_variances=[nu[a] if nu[a] is not None else fallback_variance for a in tr],
                 penalty=PROTOCOL["scout_correction_penalty"])
    pm = pb + np.array(correction.predict_many(post_te))
    return {"ids":te,"y":[y[a] for a in te],"baseline":pb.tolist(),"movement":pm.tolist(),
            "training_target_quartile":float(np.quantile([y[a] for a in tr],.25)),
            "counts":[n[a] for a in te],"alpha":alpha,"loading":correction.loading,
            "calibration":{"calibrated":reliability.calibrated,"reason":reliability.calibration_reason,
                           "source_within_variance":reliability.within_variance,"source_prior_variance":reliability.prior_variance},
            "posteriors":[asdict(p) for p in post_te]}


def _score(rows, key):
    return sum((y-p)**2 for row in rows for y,p in zip(row["y"],row[key]))/sum(len(row["y"]) for row in rows)


def nested_fold(ds, observations, tr, te, cutoff, include_ngs, seed):
    assignment = _groups(ds,tr,3,seed)
    scores = {family:[] for family in ("baseline","movement")}
    for alpha in PROTOCOL["baseline_penalties"]:
        fits = []
        for fold in range(3):
            a=[q for q in tr if assignment[q]!=fold]; b=[q for q in tr if assignment[q]==fold]
            fits.append(fit_split(ds,observations,a,b,cutoff,alpha,include_ngs,seed+fold))
        for family in scores:
            scores[family].append(_score(fits,family))
    chosen = {family:PROTOCOL["baseline_penalties"][int(np.argmin(loss))] for family,loss in scores.items()}
    fits = {alpha:fit_split(ds,observations,tr,te,cutoff,alpha,include_ngs,seed+9)
            for alpha in set(chosen.values())}
    result = fits[chosen["movement"]]
    result["baseline"] = fits[chosen["baseline"]]["baseline"]
    result["chosen_penalties"] = chosen
    result["inner_scores"] = scores
    result["year"] = cutoff
    return result


def paired_summary(folds, draws=2000, seed=81014):
    rows = [(a,y,pb,pm) for f in folds for a,y,pb,pm in zip(f["ids"],f["y"],f["baseline"],f["movement"])]
    y=np.array([r[1] for r in rows]); pb=np.array([r[2] for r in rows]); pm=np.array([r[3] for r in rows])
    lb=(y-pb)**2; lm=(y-pm)**2; denom=float(lb.mean())
    gain=1-float(lm.mean())/denom if denom else None
    rng=np.random.default_rng(seed); boot=[]
    for _ in range(draws):
        idx=rng.integers(0,len(rows),len(rows)); b=float(lb[idx].mean())
        if b>0:boot.append(1-float(lm[idx].mean())/b)
    influences=[]
    for i,(aid,*_) in enumerate(rows):
        keep=np.arange(len(rows))!=i
        if lb[keep].mean()>0:influences.append({"athlete":aid,"gain_change_on_removal":float(1-lm[keep].mean()/lb[keep].mean()-gain)})
    decisions=[]
    for fold in folds:
        size=max(1,int(np.ceil(.25*len(fold["ids"]))))
        chosen={key:set(np.argsort(fold[key],kind="stable")[:size].tolist()) for key in ("baseline","movement")}
        hits={key:sum(fold["y"][i]<=fold["training_target_quartile"] for i in indices) for key,indices in chosen.items()}
        decisions.append({"class":fold["year"],"budget":size,"hits":hits,
                          "promoted":len(chosen["movement"]-chosen["baseline"]),
                          "demoted":len(chosen["baseline"]-chosen["movement"])})
    return {"athletes":len(rows),"mse_baseline":denom,"mse_movement":float(lm.mean()),"gain":gain,
            "calibration_mean_error":{"baseline":float(np.mean(pb-y)),"movement":float(np.mean(pm-y))},
            "decisions":decisions,
            "fixed_prediction_interval_90":np.quantile(boot,[.05,.95]).tolist() if boot else None,
            "interval_scope":"fixed fitted predictions; does not include selection/training uncertainty",
            "largest_influences":sorted(influences,key=lambda r:abs(r["gain_change_on_removal"]),reverse=True)[:5]}


def experiment(ds, include_ngs=True, seed=81014):
    if ds.synthetic:
        raise ValueError("this command requires official real inputs; synthetic data cannot establish advantage")
    attempts=[a for a in ds.attempts if available(a.recorded_on,f"{ds.athletes[a.athlete_id].draft_year}-04-20")]
    years=sorted({a.draft_year for a in ds.athletes.values()})
    families={"primary_forty":("FORTY_YARD_DASH",),"secondary_front_starts":FRONT_DRILLS}
    result={"protocol":PROTOCOL,"protocol_sha256":hashlib.sha256(json.dumps(PROTOCOL,sort_keys=True).encode()).hexdigest(),
            "synthetic":False,"status":"real_data_development_experiment","include_ngs":include_ngs,
            "sources":ds.manifest,"outcome_definition":ds.outcome_definition,"families":{}}
    for family,drills in families.items():
        obs=extract_bursts(attempts,BurstProtocol(allowed_drills=tuple(drills)))
        folds=[]
        for year in years[1:]:
            tr=sorted(a for a,v in ds.athletes.items() if v.draft_year<year)
            te=sorted(a for a,v in ds.athletes.items() if v.draft_year==year)
            print(f"{family}: rebuilding temporal class {year}",flush=True)
            folds.append(nested_fold(ds,obs,tr,te,year,include_ngs,seed))
        result["families"][family]={"usable_attempts":len(obs),"source_players":len({o.athlete_id for o in obs}),
            "attempts_by_drill":dict(Counter(o.drill for o in obs)),"summary":paired_summary(folds,seed=seed),"folds":folds}
    result["conclusion"]="Development evidence only. A positive point estimate on inspected cohorts is not independent confirmation."
    return result


def full_refit_sensitivity(ds, draws=64, include_ngs=True, seed=81014):
    """Class-stratified athlete bootstrap; every copy stays in its original group.

    Reextract source trajectories and refit the entire nested procedure. These
    percentile intervals describe the declared empirical refit procedure, not
    protection against the project's earlier adaptive searches or future drift.
    """
    from .schema import Dataset
    rng=np.random.default_rng(seed+901)
    gains={k:[] for k in ("primary_forty","secondary_front_starts")}
    failed=[]
    by_attempt={};by_play={}
    for a in ds.attempts:by_attempt.setdefault(a.athlete_id,[]).append(a)
    for p in ds.plays:by_play.setdefault(p.athlete_id,[]).append(p)
    years=sorted({a.draft_year for a in ds.athletes.values()})
    for draw in range(draws):
        athletes={};attempts=[];plays=[]
        for year in years:
            ids=sorted(a for a,v in ds.athletes.items() if v.draft_year==year)
            copies=Counter()
            for aid in rng.choice(ids,size=len(ids),replace=True):
                copies[aid]+=1;new=f"{aid}#boot{copies[aid]}"
                athletes[new]=replace(ds.athletes[aid],athlete_id=new,
                                      bootstrap_group=ds.athletes[aid].bootstrap_group or aid)
                attempts.extend(replace(a,athlete_id=new,attempt_id=a.attempt_id+f"#{copies[aid]}")
                                for a in by_attempt.get(aid,[]))
                plays.extend(replace(p,athlete_id=new) for p in by_play.get(aid,[]))
        boot=Dataset(athletes,attempts,plays,ds.manifest,ds.outcome_definition,False)
        try:
            run=experiment(boot,include_ngs,seed)
            for family in gains:gains[family].append(run["families"][family]["summary"]["gain"])
        except ValueError as error:
            failed.append({"draw":draw,"reason":str(error)})
        print(f"full pipeline refit {draw+1}/{draws}",flush=True)
    return {"requested_draws":draws,"failed_draws":failed,"families":{
        k:{"completed":len(v),"percentile_90":np.quantile(v,[.05,.95]).tolist() if v else None,
           "median":float(np.median(v)) if v else None,"positive_draws":sum(x>0 for x in v)}
        for k,v in gains.items()},"scope":"full selection/source/context refits with original-athlete grouping; development evidence"}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data",required=True,type=Path);p.add_argument("--out",required=True,type=Path)
    p.add_argument("--without-ngs",action="store_true");p.add_argument("--seed",type=int,default=81014)
    p.add_argument("--verify-known-hashes",action="store_true")
    p.add_argument("--refits",type=int,default=64)
    a=p.parse_args(argv)
    ds=load_official_directory(a.data,minimum_plays=30,verify_known_hashes=a.verify_known_hashes)
    result=experiment(ds,include_ngs=not a.without_ngs,seed=a.seed)
    result["full_refit_sensitivity"]=full_refit_sensitivity(ds,a.refits,not a.without_ngs,a.seed) if a.refits else None
    root=Path(__file__).resolve().parents[4]
    result["code_revision"]=subprocess.run(["git","rev-parse","HEAD"],cwd=root,capture_output=True,text=True).stdout.strip()
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"private_results.json").write_text(json.dumps(result,indent=2)+"\n")
    aggregate={k:v for k,v in result.items() if k!="families"}
    aggregate["families"]={k:{q:r for q,r in v.items() if q!="folds"} for k,v in result["families"].items()}
    for value in aggregate["families"].values():
        value["summary"].pop("largest_influences",None)
    (a.out/"aggregate_results.json").write_text(json.dumps(aggregate,indent=2)+"\n")
    print(json.dumps({"out":str(a.out),"status":result["status"],"families":{k:v["summary"]["gain"] for k,v in result["families"].items()}},indent=2))


if __name__=="__main__":
    main()
