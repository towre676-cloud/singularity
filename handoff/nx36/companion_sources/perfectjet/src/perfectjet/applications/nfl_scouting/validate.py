"""Player-grouped temporal validation of the movement readout against a conventional baseline.

Each fold trains on draft classes before year Y and tests on class Y. Everything that
learns from data is refit inside the fold: demand frame, pooled movement model,
context model, shrinkage, standardization, and ridge tuning. Baseline and movement
models share the same availability indicators, missing-data rule and tuning grid,
so a movement gain cannot come from knowing who completed which drills.

Primary metric: G = 1 - MSE_movement / MSE_baseline (positive is improvement).
"""
import random
from .linalg import ridge, dot, mean, Standardizer, quantile
from .readouts import DemandFrame, PooledModel, group
from .outcomes import build_targets, player_folds
from .schema import admissible_measurements, admissible_events

LAMBDAS = (0.1, 1.0, 10.0, 100.0)
MEASUREMENTS = ("weight", "forty", "vertical", "three_cone", "broad", "shuttle", "height", "bench")


def decision_date(athlete):
    return f"{athlete.draft_year}-04-20"


class Featurizer:
    """Pre-draft predictors only: it never sees plays. Fitted on training athletes."""

    def __init__(self, athletes, events_by_athlete, train_ids, readout="intercept", drills=None):
        self.positions = sorted({athletes[a].position for a in train_ids})
        self.meas = [m for m in MEASUREMENTS if any(m in athletes[a].measurements for a in train_ids)]
        self.readout = readout
        self.rejected = {}
        self.rejected_events = {}
        usable_events = {}
        for a in train_ids:
            usable_events[a], rejected = admissible_events(athletes[a], events_by_athlete.get(a, []),
                                                           decision_date(athletes[a]))
            if rejected:
                self.rejected_events[a] = rejected
        self.drills = tuple(drills) if drills is not None else tuple(sorted({e.drill for v in usable_events.values() for e in v}))
        cols = {m: [] for m in self.meas}
        for a in train_ids:
            use, rej = admissible_measurements(athletes[a], decision_date(athletes[a]), self.meas)
            if rej:
                self.rejected[a] = rej
            for m in self.meas:
                if m in use:
                    cols[m].append(use[m])
        self.fill = {m: (mean(v) if v else 0.0) for m, v in cols.items()}
        train_events = [e for a in train_ids for e in usable_events[a]]
        self.frame = DemandFrame(train_events) if train_events else None
        self.model = PooledModel(self.frame, {a: usable_events[a] for a in train_ids if usable_events[a]}) \
            if train_events else None
        self.std = None

    def raw(self, athlete, events, movement):
        use, _ = admissible_measurements(athlete, decision_date(athlete), self.meas)
        events, _ = admissible_events(athlete, events, decision_date(athlete))
        row = [1.0 if athlete.position == p else 0.0 for p in self.positions[1:]]
        for m in self.meas:
            row += [use.get(m, self.fill[m]), 0.0 if m in use else 1.0]
        done = {e.drill for e in events}
        row += [1.0 if d in done else 0.0 for d in self.drills]+[float(len(events))]
        if movement:
            if self.model is None:
                row.append(0.0)
            elif self.readout == "pooled":
                row.append(self.model.readout(events)["theta"])
            else:
                row.append(self.model.intercept_readout(events)["theta"])
        return row

    def matrix(self, athletes, events_by_athlete, ids, movement, fit=False):
        rows = [self.raw(athletes[a], events_by_athlete.get(a, []), movement) for a in ids]
        if fit:
            self.std = Standardizer(rows)
        return [[1.0]+r for r in self.std(rows)]


def tune(x, y, groups, k=5):
    """Ridge penalty by leave-group-out CV over a fixed grid shared by both models."""
    ids = sorted(set(groups))
    fold = {a: i % k for i, a in enumerate(ids)}
    best = None
    for lam in LAMBDAS:
        se = 0.0
        for f in range(k):
            tr = [i for i, g in enumerate(groups) if fold[g] != f]
            te = [i for i, g in enumerate(groups) if fold[g] == f]
            if not tr or not te:
                continue
            b = ridge([x[i] for i in tr], [y[i] for i in tr], lam)
            se += sum((y[i]-dot(x[i], b))**2 for i in te)
        if best is None or se < best[1]-1e-15:
            best = (lam, se)
    return best[0]


def fit_predict(x_tr, y_tr, ids_tr, x_te):
    lam = tune(x_tr, y_tr, ids_tr)
    b = ridge(x_tr, y_tr, lam)
    return [dot(r, b) for r in x_te], lam, b


def original_groups(ds, ids):
    return {a: ds.athletes[a].bootstrap_group or a for a in ids}


def prepare_fold(ds, events_by_athlete, train_ids, test_ids, readout="intercept", minimum_plays=1,
                 train_season_before=None, test_season=None):
    """Rebuild all learned targets and features using only this split's training athletes."""
    plays = ds.plays
    if ds.outcome_definition.get("evaluation_horizon", "rookie_season") == "rookie_season":
        plays = [p for p in plays if p.athlete_id in ds.athletes
                 and p.season == ds.athletes[p.athlete_id].draft_year]
    targets = build_targets(plays, train_ids, test_ids, minimum_plays=minimum_plays,
                            groups=original_groups(ds, train_ids), train_season_before=train_season_before,
                            test_season=test_season)
    tr, te = sorted(targets["train"]), sorted(targets["test"])
    if not tr or not te:
        return None
    feats = Featurizer(ds.athletes, events_by_athlete, tr, readout=readout)
    y_tr = [targets["train"][a]["shrunk"] for a in tr]
    y_te = [targets["test"][a]["shrunk"] for a in te]
    matrices = {}
    for name, movement in (("baseline", False), ("movement", True)):
        x_tr = feats.matrix(ds.athletes, events_by_athlete, tr, movement, fit=True)
        x_te = feats.matrix(ds.athletes, events_by_athlete, te, movement)
        matrices[name] = (x_tr, x_te)
    return targets, feats, tr, te, y_tr, y_te, matrices


def tune_dataset(ds, events_by_athlete, train_ids, readout="intercept", minimum_plays=1,
                 train_season_before=None, k=5):
    """Nested athlete CV: target construction, pooling, imputation and scaling refit in each inner split."""
    fold = player_folds(train_ids, k, original_groups(ds, train_ids))
    scores = {name: {lam: [0.0, 0] for lam in LAMBDAS} for name in ("baseline", "movement")}
    for f in range(k):
        train = [a for a in train_ids if fold[a] != f]
        test = [a for a in train_ids if fold[a] == f]
        if not train or not test:
            continue
        # Inner held-out labels obey the same historical information cutoff as
        # inner training labels; they do not include later NFL seasons either.
        plays = [p for p in ds.plays if train_season_before is None or p.season < train_season_before]
        from dataclasses import replace
        inner_ds = replace(ds, plays=plays)
        prepared = prepare_fold(inner_ds, events_by_athlete, train, test, readout, minimum_plays,
                                train_season_before=train_season_before)
        if prepared is None:
            continue
        _, _, _, _, y_tr, y_te, matrices = prepared
        for name, (x_tr, x_te) in matrices.items():
            for lam in LAMBDAS:
                coef = ridge(x_tr, y_tr, lam)
                scores[name][lam][0] += sum((dot(x, coef)-y)**2 for x, y in zip(x_te, y_te))
                scores[name][lam][1] += len(y_te)
    return {name: min(LAMBDAS, key=lambda lam: (values[lam][0]/values[lam][1]
                                              if values[lam][1] else float("inf"), lam))
            for name, values in scores.items()}


def evaluate_fold(ds, events_by_athlete, train_ids, test_ids, readout="intercept", minimum_plays=None):
    minimum_plays = minimum_plays or ds.outcome_definition.get("minimum_plays", 1)
    test_year = min(ds.athletes[a].draft_year for a in test_ids)
    # This is a chronological experiment, not merely a draft-class split.
    # Earlier athletes' later-season outcomes cannot train a historical scout.
    cutoff = test_year if ds.outcome_definition.get("chronological_training", True) else None
    horizon = ds.outcome_definition.get("evaluation_horizon", "rookie_season")
    test_season = test_year if horizon == "rookie_season" else None
    if horizon not in ("rookie_season", "all_observed"):
        raise ValueError("evaluation_horizon must be rookie_season or all_observed")
    prepared = prepare_fold(ds, events_by_athlete, train_ids, test_ids, readout, minimum_plays,
                            train_season_before=cutoff, test_season=test_season)
    if prepared is None:
        return None
    targets, feats, tr, te, y_tr, y_te, matrices = prepared
    if len(tr) < 10 or len(te) < 3:
        return None
    out = {"train": len(tr), "test": len(te), "test_ids": te, "y_test": y_te,
           "train_target_quartile": quantile(y_tr, 0.25), "train_target_upper_quartile": quantile(y_tr, 0.75),
           "plays_test": [targets["test"][a]["n"] for a in te],
           "training_seasons_before": cutoff, "evaluation_horizon": horizon,
           "test_season": test_season}
    chosen = tune_dataset(ds, events_by_athlete, train_ids, readout, minimum_plays,
                          train_season_before=cutoff)
    for name, (x_tr, x_te) in matrices.items():
        lam = chosen[name]
        coef = ridge(x_tr, y_tr, lam)
        pred = [dot(row, coef) for row in x_te]
        out[name] = {"pred": pred, "lambda": lam, "mse": mean((p-y)**2 for p, y in zip(pred, y_te))}
    out["G"] = 1-out["movement"]["mse"]/out["baseline"]["mse"] if out["baseline"]["mse"] > 0 else None
    out["featurizer"] = feats
    out["positions"] = [ds.athletes[a].position for a in te]
    return out


def temporal_folds(ds):
    years = sorted({a.draft_year for a in ds.athletes.values()})
    for y in years[1:]:
        train = [a for a, v in ds.athletes.items() if v.draft_year < y]
        test = [a for a, v in ds.athletes.items() if v.draft_year == y]
        yield y, train, test


def pooled_g(folds):
    se_b = sum((p-y)**2 for f in folds for p, y in zip(f["baseline"]["pred"], f["y_test"]))
    se_m = sum((p-y)**2 for f in folds for p, y in zip(f["movement"]["pred"], f["y_test"]))
    return 1-se_m/se_b if se_b > 0 else None


def run_validation(ds, events, readout="intercept"):
    eba = group(events)
    folds = []
    for year, train, test in temporal_folds(ds):
        f = evaluate_fold(ds, eba, train, test, readout)
        if f is not None:
            f["year"] = year
            folds.append(f)
    return {"folds": folds, "G_pooled": pooled_g(folds) if folds else None}


# ------------------------------------------------------------ uncertainty


def fixed_prediction_interval(folds, b=400, seed=0, level=0.9):
    """Resample test athletes with predictions held fixed."""
    rng = random.Random(seed)
    rows = [(pb, pm, y) for f in folds for pb, pm, y in zip(f["baseline"]["pred"], f["movement"]["pred"], f["y_test"])]
    gs = []
    for _ in range(b):
        s = [rows[rng.randrange(len(rows))] for _ in rows]
        sb = sum((r[0]-r[2])**2 for r in s)
        sm = sum((r[1]-r[2])**2 for r in s)
        if sb > 0:
            gs.append(1-sm/sb)
    return {"lo": quantile(gs, (1-level)/2), "hi": quantile(gs, 1-(1-level)/2), "draws": len(gs)}


def resample_dataset(ds, rng):
    """Cluster bootstrap over athletes; duplicated athletes become distinct ids with all their data."""
    from dataclasses import replace
    from .schema import Dataset
    ids = sorted(ds.athletes)
    pick = [ids[rng.randrange(len(ids))] for _ in ids]
    count = {}
    athletes, attempts, plays = {}, [], []
    by_att, by_play = {}, {}
    for a in ds.attempts:
        by_att.setdefault(a.athlete_id, []).append(a)
    for p in ds.plays:
        by_play.setdefault(p.athlete_id, []).append(p)
    for a in pick:
        count[a] = count.get(a, 0)+1
        new = f"{a}#{count[a]}"
        athletes[new] = replace(ds.athletes[a], athlete_id=new,
                                bootstrap_group=ds.athletes[a].bootstrap_group or a)
        attempts += [replace(x, athlete_id=new, attempt_id=f"{x.attempt_id}#{count[a]}") for x in by_att.get(a, [])]
        plays += [replace(x, athlete_id=new, play_id=f"{x.play_id}#{count[a]}") for x in by_play.get(a, [])]
    return Dataset(athletes, attempts, plays, ds.manifest, ds.outcome_definition, ds.synthetic)


def full_refit_interval(ds, extract_fn, b=30, seed=0, level=0.9, readout="intercept"):
    """Refit the entire pipeline, event extraction included, on athlete-resampled data."""
    rng = random.Random(seed)
    gs = []
    for _ in range(b):
        boot = resample_dataset(ds, rng)
        res = run_validation(boot, extract_fn(boot.attempts), readout)
        if res["G_pooled"] is not None:
            gs.append(res["G_pooled"])
    return {"lo": quantile(gs, (1-level)/2), "hi": quantile(gs, 1-(1-level)/2), "median": quantile(gs, 0.5),
            "draws": len(gs)}


# ------------------------------------------------------------ diagnostics


def diagnostics(folds, low_plays=20):
    rows = [(f["year"], a, pos, n, pb, pm, y) for f in folds
            for a, pos, n, pb, pm, y in zip(f["test_ids"], f["positions"], f["plays_test"], f["baseline"]["pred"],
                                            f["movement"]["pred"], f["y_test"])]

    def g(sub):
        sb = sum((r[4]-r[6])**2 for r in sub)
        sm = sum((r[5]-r[6])**2 for r in sub)
        return 1-sm/sb if sb > 0 else None
    by_pos = {p: {"n": len([r for r in rows if r[2] == p]), "G": g([r for r in rows if r[2] == p])}
              for p in sorted({r[2] for r in rows})}
    by_year = {y: g([r for r in rows if r[0] == y]) for y in sorted({r[0] for r in rows})}
    well = [r for r in rows if r[3] >= low_plays]
    full = g(rows)
    influence = sorted(((abs((g([s for s in rows if s is not r]) or 0)-(full or 0)), r[1]) for r in rows),
                       reverse=True)[:5]
    calib_b = sum(r[4]-r[6] for r in rows)/len(rows) if rows else None
    calib_m = sum(r[5]-r[6] for r in rows)/len(rows) if rows else None
    return {"G_all": full, "G_by_position": by_pos, "G_by_year": by_year,
            "G_excluding_low_play_athletes": g(well), "low_play_threshold": low_plays, "athletes_kept": len(well),
            "largest_single_athlete_influence": [{"athlete": a, "delta_G": d} for d, a in influence],
            "mean_error_baseline": calib_b, "mean_error_movement": calib_m}


def decision_eval(folds, share=0.25, lower_is_better=True):
    """Frozen shortlist rule: top share of each class by prediction; hit = target in training best quartile."""
    out = []
    for f in folds:
        k = max(1, round(share*len(f["test_ids"])))
        thr = f["train_target_quartile"] if lower_is_better else f["train_target_upper_quartile"]
        order = (lambda pred: sorted(range(len(pred)), key=lambda i: pred[i])) if lower_is_better else \
            (lambda pred: sorted(range(len(pred)), key=lambda i: -pred[i]))
        sb = set(order(f["baseline"]["pred"])[:k])
        sm = set(order(f["movement"]["pred"])[:k])
        hit = (lambda i: f["y_test"][i] <= thr) if lower_is_better else (lambda i: f["y_test"][i] >= thr)
        out.append({"year": f["year"], "shortlist": k, "hits_baseline": sum(hit(i) for i in sb),
                    "hits_movement": sum(hit(i) for i in sm),
                    "promoted": [{"athlete": f["test_ids"][i], "target": f["y_test"][i], "hit": hit(i)} for i in sm-sb],
                    "demoted": [{"athlete": f["test_ids"][i], "target": f["y_test"][i], "hit": hit(i)} for i in sb-sm]})
    return {"rule": f"top {share:.0%} by predicted target within each class; hit means training best-quartile",
            "folds": out, "hits_baseline": sum(r["hits_baseline"] for r in out),
            "hits_movement": sum(r["hits_movement"] for r in out)}
