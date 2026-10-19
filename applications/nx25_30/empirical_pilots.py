"""Frozen small empirical pilots. Optional NumPy; never imported by core.

Run with --wind-source recovered/BOS_asos.csv and optional --nfl-root DIR.
Restricted NFL inputs and individual outputs are never copied to the repository.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json,math,sys
from pathlib import Path
from collections import defaultdict
import numpy as np

ROOT=Path(__file__).resolve().parents[2]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def numeric(x):
 try:
  v=float(x)
  return v if math.isfinite(v) else None
 except (TypeError,ValueError):return None


def fit_predict(train_x,train_y,test_x,ridge=0):
 x=np.asarray(train_x,float);y=np.asarray(train_y,float);z=np.asarray(test_x,float)
 mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale==0]=1
 a=np.column_stack((np.ones(len(x)),(x-mean)/scale));b=np.column_stack((np.ones(len(z)),(z-mean)/scale))
 if ridge:
  penalty=np.eye(a.shape[1])*ridge;penalty[0,0]=0
  coef=np.linalg.solve(a.T@a+penalty,a.T@y)
 else:coef=np.linalg.lstsq(a,y,rcond=None)[0]
 return b@coef,a@coef


def metrics(y,p,groups,seed=25030):
 y=np.asarray(y);p=np.asarray(p);errors=p-y;rng=np.random.default_rng(seed)
 labels=sorted(set(groups));samples=[]
 for _ in range(512):
  sampled=rng.choice(labels,len(labels),replace=True)
  ix=[i for label in sampled for i,g in enumerate(groups) if g==label]
  samples.append(float(np.mean(np.abs(errors[ix]))))
 return {"n":len(y),"mae":float(np.mean(abs(errors))),"mse":float(np.mean(errors**2)),"bias":float(np.mean(errors)),"mae_day_or_player_bootstrap_95":list(map(float,np.quantile(samples,[.025,.975]))),"bootstrap_groups":len(labels),"interval_status":"descriptive_small_frozen_pilot_not_asymptotic_guarantee"}


def wind_pilots(source):
 with open(source,newline="") as f:rows=list(csv.DictReader(f))
 selected=[r for r in rows if "2026-09-25"<=r["valid"][:10]<= "2026-09-28"]
 fields=("station","valid","sknt","alti","drct")
 dest=ROOT/"applications/nx25_30/BOS_20260925_28.csv"
 with dest.open("w",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:r[k] for k in fields} for r in selected)
 table={dt.datetime.fromisoformat(r["valid"]):r for r in selected};complete=[]
 missing=defaultdict(int)
 for time,r in sorted(table.items()):
  lag=table.get(time-dt.timedelta(minutes=30));future=table.get(time+dt.timedelta(minutes=60))
  if lag is None or future is None:missing["exact_lag_or_future_timestamp"]+=1;continue
  vals=[numeric(r["sknt"]),numeric(lag["sknt"]),numeric(r["alti"]),numeric(lag["alti"]),numeric(r["drct"]),numeric(future["sknt"])]
  if any(v is None for v in vals):missing["field_missing"]+=1;continue
  w,wl,p,pl,d,y=vals;complete.append((time,((w,wl),(w,p-pl),(p,d)),y))
 train=[r for r in complete if (r[0]+dt.timedelta(minutes=60)).date()<dt.date(2026,9,27)];test=[r for r in complete if r[0].date()>=dt.date(2026,9,27)]
 if len(train)<10 or len(test)<10:raise ValueError("insufficient frozen wind split")
 result={"evidence":"measured_ASOS_reported_wind","target":"+60 minute reported sustained wind knots; not independently validated ten-metre flow","source_sha256":sha(source),"redistributable_subset_sha256":sha(dest),"source_rows":len(rows),"subset_rows":len(selected),"matched_train":len(train),"matched_evaluation":len(test),"missingness":dict(missing),"radar_geometry":"not_applicable_ASOS_station_pilot; original NEXRAD claims not reproduced","policies":{}}
 for j,name in enumerate(("direct_target","driver_aware","generic_information")):
  pred,_=fit_predict([r[1][j] for r in train],[r[2] for r in train],[r[1][j] for r in test])
  result["policies"][name]={"declared_feature_cost":2,**metrics([r[2] for r in test],pred,[str(r[0].date()) for r in test])}
 # Fine/coarse observed time series: exact complete 15-minute blocks.
 fine={t:numeric(r["sknt"]) for t,r in table.items() if t.minute%5==0 and t.second==0};coarse={}
 for t in sorted(fine):
  if t.minute%15:continue
  times=[t+dt.timedelta(minutes=5*k) for k in range(3)]
  if all(s in fine and fine[s] is not None for s in times):coarse[t]=sum(fine[s] for s in times)/3
 fine_pairs=[(t,w,fine.get(t+dt.timedelta(minutes=5))) for t,w in fine.items() if w is not None and fine.get(t+dt.timedelta(minutes=5)) is not None and (t+dt.timedelta(minutes=5)).date()<dt.date(2026,9,27)]
 coarse_pairs=[(t,w,coarse.get(t+dt.timedelta(minutes=15))) for t,w in coarse.items() if coarse.get(t+dt.timedelta(minutes=15)) is not None and (t+dt.timedelta(minutes=25)).date()<dt.date(2026,9,27)]
 def arfit(pairs):
  x=np.array([[1,r[1]] for r in pairs]);y=np.array([r[2] for r in pairs]);return np.linalg.lstsq(x,y,rcond=None)[0]
 af,ac=arfit(fine_pairs),arfit(coarse_pairs);ref=[];pf=[];pc=[];mismatch=[];days=[]
 for t,value in sorted(coarse.items()):
  # Origin is the last measured sample in current complete coarse block.
  if t.date()<dt.date(2026,9,27) or t+dt.timedelta(minutes=15) not in coarse:continue
  current=fine[t+dt.timedelta(minutes=10)];f=current;future=[]
  for _ in range(3):f=af[0]+af[1]*f;future.append(f)
  ref.append(coarse[t+dt.timedelta(minutes=15)]);pf.append(sum(future)/3);pc.append(ac[0]+ac[1]*value);mismatch.append(current-value);days.append(str(t.date()))
 scale={"evidence":"measured_temporal_aggregation_benchmark","fine_step_minutes":5,"coarse_step_minutes":15,"target":"mean of next three measured five-minute reports","n_complete_coarse_blocks":len(coarse),"n_evaluation":len(ref),"fine_vs_measurement":metrics(ref,pf,days),"coarse_vs_measurement":metrics(ref,pc,days),"coarse_vs_fine_prediction_mae":float(np.mean(np.abs(np.array(pc)-pf))),"representation_mismatch_last_sample_vs_current_block_mean_max":float(np.max(abs(np.array(mismatch)))),"physical_model_error":"not_separately_identified","scope":"temporal aggregation only; no spatial continuum claim","fine_ar_parameters":list(map(float,af)),"coarse_ar_parameters":list(map(float,ac))}
 return result,scale


def nfl_pilot(root):
 from fractions import Fraction as Q
 from singularity.ordered_movement import RationalPath,signature_level_two,segmentation_population
 from singularity.movement_design import target_identifiable
 root=Path(root);columns=("forty","vertical","broad_jump","combine_weight")
 official_hashes={"combine_results.csv":"e4773ef68167d508f3916d446cd411dfd77a87e5765d3babcb986201fb143b86","combine_tracking.csv":"541c69f6629f5f803b08033c5c386735582120973562134b2c1e7ec6553fb0d3","player_play.csv":"68926a268c0a49e58616001fb35ea179018d9cbbce1c5c31e7a4095273c35b2a","games.csv":"ca33543f6939af4ee393c568c60920c476ba91ddbfbdce5a06578b9492fa11fd"}
 actual={name:sha(root/name) for name in official_hashes}
 if actual!=official_hashes:raise ValueError("restricted source hashes disagree with recovered official adapter")
 with (root/"games.csv").open(newline="") as f:games={r["game_id"]:r for r in csv.DictReader(f)}
 with (root/"combine_results.csv").open(newline="") as f:
  combine={r["nfl_id"]:r for r in csv.DictReader(f) if r["draft_year"] in ("2023","2024") and all(numeric(r[k]) is not None for k in columns)}
 outcome=defaultdict(list);excluded=defaultdict(int)
 with (root/"player_play.csv").open(newline="") as f:
  for r in csv.DictReader(f):
   aid=r["nfl_id"]
   if aid not in combine:continue
   if r["play_nullified_by_penalty"] not in ("N","FALSE","False","0"):excluded["nullified_or_unknown_penalty"]+=1;continue
   g=games.get(r["game_id"]);v=numeric(r["player_get_off"])
   if g is None or v is None:excluded["missing_game_or_getoff"]+=1;continue
   if int(g["season"])<int(combine[aid]["draft_year"]):excluded["pre_combine_outcome"]+=1;continue
   outcome[aid].append(v)
 eligible={aid for aid in combine if outcome[aid]};tracks=defaultdict(list)
 with (root/"combine_tracking.csv").open(newline="") as f:
  for r in csv.DictReader(f):
   if r["entity_type"]!="PLAYER" or r["nfl_id"] not in eligible:continue
   values=[numeric(r[k]) for k in ("x","y","s","a","dir")]
   if any(v is None for v in values):continue
   tracks[(r["nfl_id"],r["event_id"],r["attempt"])].append((r["time"],values))
 attempts=defaultdict(list)
 for (aid,event,attempt),points in tracks.items():
  if len(points)>=8:attempts[aid].append((event,attempt,sorted(points)))
 selected=[]
 for cohort in ("2023","2024"):
  selected.extend(sorted(aid for aid in eligible if combine[aid]["draft_year"]==cohort and attempts[aid])[:10])
 if len(selected)!=20:raise ValueError("frozen twenty-athlete chronological cohort unavailable")
 records=[];rank_counts=defaultdict(int);attempt_count=0
 for aid in selected:
  event,attempt,points=sorted(attempts[aid])[0];attempt_count+=1
  # Fixed extraction: 33 uniformly indexed samples, <=32 geometric segments.
  indices=np.unique(np.linspace(0,len(points)-1,min(33,len(points))).astype(int));sample=[points[i] for i in indices]
  times=[dt.datetime.fromisoformat(p[0]) for p in sample];seconds=[(t-times[0]).total_seconds() for t in times]
  if seconds[-1]<=0:raise ValueError("invalid attempt clock")
  xy=[p[1][:2] for p in sample]
  path=RationalPath(tuple((Q(str(x)),Q(str(y)),Q(str(t))) for (x,y),t in zip(xy,seconds)),tuple(Q(str(t)) for t in seconds),("yard","yard","second"),"official_field_coordinates")
  sig=signature_level_two(path);areas=[float(sig.second[i][j]-sig.second[j][i]) for i,j in ((0,1),(0,2),(1,2))]
  candidates=sorted(set(int(i) for i in np.linspace(1,len(sample)-2,min(8,len(sample)-2))))
  pop=segmentation_population(path,candidates,3)
  phase_areas=np.array([[float(sum((Q(k+1)*(s.second[i][j]-s.second[j][i]) for k,s in enumerate(r["phase_signatures"])),Q())) for i,j in ((0,1),(0,2),(1,2))] for r in pop])
  uncertainty=phase_areas.max(axis=0)-phase_areas.min(axis=0)
  length=sum(math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(xy,xy[1:]));totals=[xy[-1][0]-xy[0][0],xy[-1][1]-xy[0][1],seconds[-1],length]
  design=[];response=[]
  for (_,p),(_,prev) in zip(points[1:],points):
   stress=p[2]/10;turn=min((p[4]-prev[4])%360,(prev[4]-p[4])%360)/180
   design.append((1,stress,turn,stress*turn));response.append(p[3])
  design=np.asarray(design);response=np.asarray(response);rank=int(np.linalg.matrix_rank(design));rank_counts[str(rank)]+=1
  beta=np.linalg.lstsq(design,response,rcond=None)[0];target=np.array((1,.5,.5,.25));cap=float(target@beta);residual=float(np.sqrt(np.mean((design@beta-response)**2)))
  # Exact row-span check on first four independent rows, with original decimals
  # interpreted as reported rationals; no numerical-rank-as-proof substitution.
  exact_rows=[]
  for row in design:
   r=tuple(Q(str(v)) for v in row)
   if len(exact_rows)<4:
    from singularity._application_exact import rref
    if len(rref(tuple(exact_rows)+(r,))[1])>len(exact_rows):exact_rows.append(r)
  identified=target_identifiable(exact_rows,(1,Q(1,2),Q(1,2),Q(1,4)))
  records.append({"id":aid,"cohort":combine[aid]["draft_year"],"conventional":[float(combine[aid][k]) for k in columns],"totals":totals,"areas":areas,"phase_mean":phase_areas.mean(axis=0).tolist(),"uncertainty":uncertainty.tolist(),"capability":cap,"residual":residual,"identified":identified,"outcome":float(np.mean(outcome[aid])),"segmentation_count":len(pop)})
 train=[r for r in records if r["cohort"]=="2023"];test=[r for r in records if r["cohort"]=="2024"]
 assert not ({r["id"] for r in train}&{r["id"] for r in test})
 definitions={"conventional":lambda r:r["conventional"],"identified_capability":lambda r:r["conventional"]+[r["capability"]],"uncertainty_aware_capability":lambda r:r["conventional"]+[r["capability"]/(1+r["residual"])],"order_insensitive":lambda r:r["conventional"]+r["totals"],"ordered":lambda r:r["conventional"]+r["totals"]+r["areas"],"uncertainty_aware_ordered":lambda r:r["conventional"]+r["totals"]+[a/(1+u) for a,u in zip(r["phase_mean"],r["uncertainty"])]}
 scores={}
 for name,features in definitions.items():
  pred,trainpred=fit_predict([features(r) for r in train],[r["outcome"] for r in train],[features(r) for r in test],ridge=1)
  radius=float(np.quantile(np.abs(trainpred-[r["outcome"] for r in train]),.9));truth=np.array([r["outcome"] for r in test]);residuals=pred-truth
  scores[name]={**metrics(truth,pred,[r["id"] for r in test],2930),"training_residual_90_radius":radius,"heldout_coverage":float(np.mean(abs(residuals)<=radius)),"calibration_status":"empirical_training_radius_not_distribution_free"}
 return {"evidence":"restricted_official_measured_trajectory_and_game_outcome_aggregate","source_sha256":actual,"ingested_files":list(actual),"unused_game_tracking_files":"not_ingested","athletes":len(records),"training_athletes":len(train),"evaluation_athletes":len(test),"attempts":attempt_count,"identity_join":"exact official nfl_id; event/attempt identities retained privately; no recruiting joins","player_overlap":0,"chronology":"2023 combine cohort training; 2024 cohort heldout; outcome games occur in or after draft season","outcome":"mean non-nullified measured player_get_off","full_design_rank_counts":dict(rank_counts),"target_identifiable_count":sum(r["identified"] for r in records),"retained_segmentation_variants_total":sum(r["segmentation_count"] for r in records),"phase_feature_range_max":float(max(max(r["uncertainty"]) for r in records)),"measurement_domain":"reported official x,y yards/time seconds; movement response is raw a; no intrinsic ability claim","model_limits":["Only twenty selected athletes: exploratory sample, no population generalization.","Bilinear response mismatch is empirical residual, not a certified bounded physical error.","Ridge lambda=1 and feature families frozen before fitting; no tuning on heldout players.","Train residual uncertainty features are heuristic; coverage below records their actual heldout behavior.","Complete attempt available for offline scouting; not a real-time forecast.","Conventional baseline has fewer channels than ordered; order-specific comparison uses order_insensitive with matched same geometric channels."],"missingness_counts":dict(excluded),"scores":scores,"restricted_rows_published":False}


def main():
 p=argparse.ArgumentParser();p.add_argument("--wind-source",type=Path);p.add_argument("--nfl-root",type=Path);a=p.parse_args()
 out=ROOT/"results";out.mkdir(exist_ok=True)
 if a.wind_source:
  forecast,scale=wind_pilots(a.wind_source)
  (out/"forecast_targets_empirical.json").write_text(json.dumps(forecast,indent=2)+"\n")
  (out/"multiscale_transport_empirical.json").write_text(json.dumps(scale,indent=2)+"\n")
  print(json.dumps({"NX25":forecast["matched_evaluation"],"NX27":scale["n_evaluation"]}))
 if a.nfl_root:
  r=nfl_pilot(a.nfl_root);(out/"movement_empirical.json").write_text(json.dumps(r,indent=2)+"\n")
  print(json.dumps({"NX29_NX30_athletes":r["athletes"],"heldout":r["evaluation_athletes"],"scores":{k:v["mse"] for k,v in r["scores"].items()}}))


if __name__=="__main__":main()
