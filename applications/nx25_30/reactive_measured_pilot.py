"""Source-bound ozone loss/source discrepancy benchmark, with exact grid fit.

The measured source is R's maintainer-distributed airquality benchmark. A
positive one-box loss/source model is not a validated atmospheric mechanism.
"""
from pathlib import Path
from fractions import Fraction as Q
import csv,datetime as dt,hashlib,json


def run():
 root=Path(__file__).resolve().parents[2];source=Path(__file__).with_name("airquality.tab")
 raw=list(csv.DictReader(source.open(),delimiter="\t"));table={dt.date(1973,int(r["Month"]),int(r["Day"])):(None if r["Ozone"]=="NA" else Q(r["Ozone"])) for r in raw}
 pairs=[(day,value,table[day+dt.timedelta(days=1)]) for day,value in sorted(table.items()) if value is not None and table.get(day+dt.timedelta(days=1)) is not None]
 # The source date and its target must both lie in training. No Jul31 -> Aug1
 # target leaks across the frozen boundary.
 train=[r for r in pairs if r[0]+dt.timedelta(days=1)<dt.date(1973,8,1)];test=[r for r in pairs if r[0]>=dt.date(1973,8,1)]
 fits=[]
 for k in range(101):
  rho=Q(k,100);b=max(Q(),sum((y-rho*x for _,x,y in train),Q())/len(train));sse=sum(((rho*x+b-y)**2 for _,x,y in train),Q())
  fits.append((sse,rho,b))
 best=min(fits);_,rho,b=best
 predictions=[rho*x+b for _,x,y in test];truth=[y for _,x,y in test];baseline=[x for _,x,y in test]
 def metrics(p):
  es=[a-y for a,y in zip(p,truth)];return {"mae":str(sum(map(abs,es),Q())/len(es)),"mse":str(sum((e*e for e in es),Q())/len(es)),"bias":str(sum(es,Q())/len(es))}
 admissible=[f for f in fits if f[0]<=best[0]*Q(11,10)]
 ranges=[(min(r*x+bb for _,r,bb in admissible),max(r*x+bb for _,r,bb in admissible)) for _,x,y in test]
 coverage=sum(lo<=y<=hi for (lo,hi),y in zip(ranges,truth))
 out={"schema":"singularity.reactive-measured-pilot/1","evidence":"measured_primary_maintainer_benchmark","application_scope":"anonymous atmospheric reactive-transport proxy with a reduced one-box loss/source map","physical_reaction_rate_identification":False,"uniform_physical_model_error":"not_identified_from_daily_ozone","source_url":"https://github.com/r-devel/r-svn/blob/main/src/library/datasets/data/airquality.tab","source_git_blob":"d39db693a2c5dd470ed48aa7c86b6a360527b164","source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"source_description_url":"https://www.stat.ethz.ch/R-manual/R-devel/RHOME/library/datasets/html/airquality.html","original_measurement_agencies":["New York State Department of Conservation","National Weather Service"],"site":"Roosevelt Island NYC ozone monitor","target_units":"ppb","target_clock":"mean ozone 1300-1500 hours; next daily window","all_days":len(raw),"observed_ozone_days":sum(v is not None for v in table.values()),"missing_ozone_days":sum(v is None for v in table.values()),"train_consecutive_pairs":len(train),"evaluation_consecutive_pairs":len(test),"train_dates":"1973-05-01 to 1973-07-31; target also training","evaluation_dates":"1973-08-01 to 1973-09-30","model":"c_next=rho*c+b, 0<=rho<=1, b>=0; O3 -> unobserved sink plus constant external source","fitted_rho":str(rho),"fitted_daily_loss":str(1-rho),"fitted_source_ppb_per_step":str(b),"model_score":metrics(predictions),"persistence_score":metrics(baseline),"training_near_optimal_rate_population":len(admissible),"rate_hull_heldout_coverage":str(Q(coverage,len(test))),"rate_set_status":"training loss tolerance only; not a calibrated confidence set","positivity_domain":"nonnegative concentration; fitted map preserves it","conservation":"open measured ozone box; unobserved sink and source make observed species mass nonconserved","latent_species_scored_as_measured":False,"measurement_method":"archived agency ozone summary; instrument and detection limit not retained by benchmark","missing_value_code":"NA","time_zone":"historical local sampling window; UTC offset not provided in source","unit_conversion":"none; all ozone ppb","limits":["Benchmark tests a deliberately reduced open-box model; it does not validate named atmospheric reaction rates.","No spatial transport measurement is present; two-cell transport toy remains synthetic.","Unknown forcing, seasonal changes and missing observations can dominate mismatch.","Meteorological channels have different sites/windows and are not conflated with simultaneous species observations.","EPA 2024 bulk endpoints timed out; fallback was frozen before fitting."]}
 return out


if __name__=="__main__":
 root=Path(__file__).resolve().parents[2];out=run();(root/"results/reactive_transport_empirical.json").write_text(json.dumps(out,indent=2)+"\n");print(json.dumps({"train":out["train_consecutive_pairs"],"evaluation":out["evaluation_consecutive_pairs"],"rho":out["fitted_rho"],"model_mae":out["model_score"]["mae"],"baseline_mae":out["persistence_score"]["mae"]}))
