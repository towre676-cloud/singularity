#!/usr/bin/env python3
"""Deterministic replay of NX25--NX30 exact receipts (stdlib only).

--check compares retained receipts and source manifests; it never fetches data.
Empirical floating regression reruns are optional and are separate from exact
algebra. Raw restricted NFL athlete data must not be published with this script.
"""
from pathlib import Path
import argparse,hashlib,json,sys,csv,datetime as dt,importlib.util
from fractions import Fraction as Q
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"src"))
from singularity._application_exact import json_exact,identity,multiply,apply,box_vertices
from singularity.forecast_targets import ForecastTarget,SensorBlock,forecast_row,target_factorization,target_null_witness,select_target_panel
from singularity.nonlinear_fibres import Polynomial,PolynomialFibre,verify_witness,affine_quadratic_constancy,curved_second_variation,minimum_witness_repair
from singularity.multiscale_transport import linear_commutation_defect,box_defect_bound,exact_target_quotient,propagate_scale_error,compose_linear_defects
from singularity.reactive_transport import conversion_mixing,reaction_flux_step,verify_conservation,verify_positive_step,reactive_target_rows,species_sensor_panel
from singularity.movement_design import movement_condition,target_identifiable,movement_null_witness,minimum_drill_repair,independent_repeat_variance
from singularity.ordered_movement import RationalPath,signature_level_two,direct_segment_integral,signature_population,segmentation_population,feature_uncertainty,finite_population_separation


def public_measurement_replay():
    """Recompute public measured targets and OLS scores with exact normal equations.

    This is independent of the optional NumPy standardized-lstsq empirical
    runner. Small bootstrap summaries are frozen aggregates, not recomputed.
    """
    from singularity._application_exact import solve
    source=ROOT/"applications/nx25_30/BOS_20260925_28.csv"
    with source.open(newline="") as f:raw=list(csv.DictReader(f))
    table={dt.datetime.fromisoformat(r["valid"]):r for r in raw}
    def q(s):
        try:return Q(s)
        except (ValueError,TypeError):return None
    rows=[]
    for time,r in sorted(table.items()):
        lag=table.get(time-dt.timedelta(minutes=30));future=table.get(time+dt.timedelta(minutes=60))
        if lag is None or future is None:continue
        vals=(q(r["sknt"]),q(lag["sknt"]),q(r["alti"]),q(lag["alti"]),q(r["drct"]),q(future["sknt"]))
        if any(v is None for v in vals):continue
        w,wl,p,pl,d,y=vals;rows.append((time,((1,w,wl),(1,w,p-pl),(1,p,d)),y))
    split=dt.date(2026,9,27)
    train=[r for r in rows if (r[0]+dt.timedelta(minutes=60)).date()<split];test=[r for r in rows if r[0].date()>=split]
    def fit(xs,ys):
        n=len(xs[0]);a=tuple(tuple(sum((r[i]*r[j] for r in xs),Q()) for j in range(n)) for i in range(n));b=tuple(sum((r[i]*y for r,y in zip(xs,ys)),Q()) for i in range(n))
        c=solve(a,b,n)
        if c is None:raise AssertionError("singular public pilot fit")
        return c
    def scores(y,p):
        es=[a-b for a,b in zip(p,y)]
        return {"mae":float(sum(map(abs,es),Q())/len(es)),"mse":float(sum((e*e for e in es),Q())/len(es)),"bias":float(sum(es,Q())/len(es))}
    from singularity._application_exact import dot
    retained=json.loads((ROOT/"results/forecast_targets_empirical.json").read_text())
    if (len(train),len(test))!=(retained["matched_train"],retained["matched_evaluation"]):raise AssertionError("forecast sample changed")
    for j,name in enumerate(("direct_target","driver_aware","generic_information")):
        c=fit([r[1][j] for r in train],[r[2] for r in train]);s=scores([r[2] for r in test],[dot(c,r[1][j]) for r in test])
        for key,value in s.items():
            if abs(value-retained["policies"][name][key])>1e-9:raise AssertionError("forecast score changed")
    fine={t:q(r["sknt"]) for t,r in table.items() if t.minute%5==0 and t.second==0};coarse={}
    for t in sorted(fine):
        if t.minute%15:continue
        ts=[t+dt.timedelta(minutes=5*k) for k in range(3)]
        if all(s in fine and fine[s] is not None for s in ts):coarse[t]=sum((fine[s] for s in ts),Q())/3
    fp=[(w,fine.get(t+dt.timedelta(minutes=5))) for t,w in fine.items() if w is not None and fine.get(t+dt.timedelta(minutes=5)) is not None and (t+dt.timedelta(minutes=5)).date()<split]
    cp=[(w,coarse.get(t+dt.timedelta(minutes=15))) for t,w in coarse.items() if coarse.get(t+dt.timedelta(minutes=15)) is not None and (t+dt.timedelta(minutes=25)).date()<split]
    af=fit([(1,x) for x,y in fp],[y for x,y in fp]);ac=fit([(1,x) for x,y in cp],[y for x,y in cp]);truth=[];pf=[];pc=[]
    for t,value in sorted(coarse.items()):
        if t.date()<split or t+dt.timedelta(minutes=15) not in coarse:continue
        f=fine[t+dt.timedelta(minutes=10)];future=[]
        for _ in range(3):f=af[0]+af[1]*f;future.append(f)
        truth.append(coarse[t+dt.timedelta(minutes=15)]);pf.append(sum(future,Q())/3);pc.append(ac[0]+ac[1]*value)
    retained=json.loads((ROOT/"results/multiscale_transport_empirical.json").read_text())
    if len(truth)!=retained["n_evaluation"]:raise AssertionError("scale sample changed")
    for name,p in (("fine_vs_measurement",pf),("coarse_vs_measurement",pc)):
        for key,value in scores(truth,p).items():
            if abs(value-retained[name][key])>1e-9:raise AssertionError("scale score changed")
    path=ROOT/"applications/nx25_30/reactive_measured_pilot.py";spec=importlib.util.spec_from_file_location("nx28_public_measurement_replay",path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if module.run()!=json.loads((ROOT/"results/reactive_transport_empirical.json").read_text()):raise AssertionError("ozone exact pilot changed")
    return {"public_measured_forecast_cases":len(test),"public_measured_scale_windows":len(truth),"public_measured_ozone_pairs":49,"NFL":"aggregate/source hash integrity only; raw restricted computation not repeated"}


def receipts():
 out={};model=ForecastTarget(((1,1),(0,1)),(1,0),3,"p,v","1 second","[-1,1]x[-2,2]",None,(0,0),(1,2));g=forecast_row(model)
 sensors=(SensorBlock("position",((1,0),),(Q(1,10),),1,model.units,model.domain_id),SensorBlock("velocity",((0,1),),(Q(1,5),),1,model.units,model.domain_id),SensorBlock("future_direct",((1,3),),(Q(3,4),),3,model.units,model.domain_id))
 out["forecast_targets_synthetic.json"]={"schema":"singularity.forecast-targets/1","evidence":"synthetic_exact","horizon":3,"target_row":g,"factorization":target_factorization(identity(2),(g,)),"null_witness_position_only":target_null_witness(((1,0),),(g,)),"admissible_state_box":{"center":model.state_center,"radii":model.state_radii},"known_inputs":"zero in retained pilot; general known-input compiler available","target_values_same_position":(3,-3),"box_error_radius":Q(7,10),"attaining_error":(Q(1,10),Q(1,5)),"panel":select_target_panel(sensors,model,max_error=Q(7,10)),"strict_boundary":select_target_panel(sensors,model,max_error=Q(7,10),strict=True),"constrained_factorization":target_factorization(((1,0),),(g,),((1,),(0,)))}
 x=Polynomial(2,{(1,0):1});y=Polynomial(2,{(0,1):1});y2=Polynomial(2,{(0,2):1});k=Polynomial(2,{(0,1):1,(2,0):-1})
 fibre=PolynomialFibre((-1,-1),(1,1),(x,),y2)
 circle=Polynomial(2,{(2,0):1,(0,2):1,(0,0):-1})
 out["nonlinear_fibres.json"]={"schema":"singularity.nonlinear-fibres/1","evidence":"synthetic_exact","quadratic_witness":verify_witness(fibre,(0,0),(0,1)),"special_case_complete_diameter":{"value":1,"upper_bound_proof":"0<=x2^2<=1 on [-1,1]; witness attains both endpoints"},"affine_quadratic":affine_quadratic_constancy((0,0),((0,),(1,)),(0,0),((0,0),(0,2)),relatively_open=True),"parabola":curved_second_variation((k,),y,(0,0),(1,0)),"circle_two_charts":tuple(curved_second_variation((circle,),x,(1,0),(0,sign*2))["second_variation"] for sign in (-1,1)),"finite_repair":minimum_witness_repair((((-1,0),(1,0)),),(("x",x,0,1),("y",y,0,2))),"missed_new_branch":{"states":((0,-1),(0,1)),"old_observation":"x^2+y^2=1","repair_sensor":"x=0 for both","target":"x+y differs by 2"}}
 a=((Q(7,8),Q(1,8),0,0),(Q(1,8),Q(3,4),Q(1,8),0),(0,Q(1,8),Q(3,4),Q(1,8)),(0,0,Q(1,8),Q(7,8)));e=((Q(1,2),Q(1,2),0,0),(0,0,Q(1,2),Q(1,2)));c=((Q(15,16),Q(1,16)),(Q(1,16),Q(15,16)))
 d=linear_commutation_defect(a,c,e,fine_units="concentration",coarse_units="pair mean concentration",time_step="one step");enriched=e+(d[0],);ac=exact_target_quotient(a,enriched)
 out["multiscale_transport.json"]={"schema":"singularity.multiscale-transport/1","evidence":"synthetic_exact","fine":a,"coarse":c,"projection":e,"defect":d,"witness_state":(0,1,0,0),"projected_fine_next":apply(e,apply(a,(0,1,0,0))),"coarse_next":apply(c,apply(e,(0,1,0,0))),"mass_quotient":exact_target_quotient(a,((1,1,1,1),)),"box_defect_bound":box_defect_bound(d,(0,0,0,0),(1,1,1,1)),"horizon_eight_bound":propagate_scale_error(0,1,(Q(1,8),)*8),"enriched_rows":enriched,"enriched_exact_quotient":ac,"new_defect":linear_commutation_defect(a,ac,enriched,fine_units="state",coarse_units="enriched state",time_step="one step"),"three_scale":compose_linear_defects(a,c,((1,),),e,((Q(1,2),Q(1,2)),)),"physical_error":"not_estimated_from_synthetic_flux"}
 mix=((Q(7,8),Q(1,8)),(Q(1,8),Q(7,8)));m=conversion_mixing(mix,Q(1,4));h=((1,0,1,0),(0,1,0,1));target=(0,0,1,1)
 state1,state2=(1,0,0,0),(0,0,1,0);gaps=[]
 for t in range(9):
  assert apply(h,state1)==apply(h,state2)
  gaps.append(abs(sum(state1[2:])-sum(state2[2:])))
  state1=reaction_flux_step(state1,mix,Q(1,4));state2=reaction_flux_step(state2,mix,Q(1,4))
 hypotheses={"A":((1,),),"B":((0,),)}
 experiments=(("total",{"A":(1,),"B":(1,)},0,1),("species",{"A":(Q(1,4),Q(1,2)),"B":(1,)},Q(1,4),1))
 out["reactive_transport.json"]={"schema":"singularity.reactive-transport/1","evidence":"synthetic_exact","mixing":mix,"step":m,"nonnegative":verify_positive_step(m),"mass_conservation":verify_conservation(m),"HM":multiply(h,m),"DH":multiply(mix,h),"B_target_gaps_horizons_0_to_8":gaps,"target_null_witness":target_null_witness(h,(reactive_target_rows(m,target,1)[1],)),"repair_factorization":target_factorization(h+((1,1,0,0),),(reactive_target_rows(m,target,1)[1],)),"uncertain_rate_panel":species_sensor_panel(hypotheses,experiments),"explicit_overlap_reading":Q(3,4),"overlap_attainment":{"A_species_value":Q(1,2),"A_error":Q(1,4),"B_species_value":1,"B_error":-Q(1,4)},"weighted_conversion":{"step":((Q(3,4),0),(Q(1,2),1)),"unweighted_conserved":False,"conserved_mass_row":(2,1)}}
 kw={"normalization":"fixed s,a","response_definition":"declared drill response"};design=tuple(movement_condition(s,a,**kw) for s,a in ((0,0),(1,0),(0,1)));goal=movement_condition(1,1,**kw)
 additional=(SensorBlock("interaction",(goal,),(Q(1,10),),2,kw["normalization"],kw["response_definition"]),SensorBlock("weak",((1,Q(1,2),Q(1,2),Q(1,4)),),(Q(1,10),),1,kw["normalization"],kw["response_definition"]))
 out["movement_design.json"]={"schema":"singularity.movement-design/1","evidence":"synthetic_exact","three_condition_design":design,"target":goal,"target_identifiable":target_identifiable(design,goal),"null_witness":movement_null_witness(design,goal),"restricted_target_identifiable":target_identifiable(design,(1,1,0,0)),"fourth_condition_identifies":target_identifiable(design+(goal,),goal),"costed_repair":minimum_drill_repair(design,additional,goal,normalization=kw["normalization"],response_definition=kw["response_definition"],max_error=Q(1,5)),"repeat_error_model":independent_repeat_variance(1,4),"replication_adds_structural_rank":False}
 def path(p):return RationalPath(p,tuple(range(len(p))),("m","m"),"lab")
 p,q=path(((0,0),(1,0),(1,1))),path(((0,0),(0,1),(1,1)));sp,sq=signature_level_two(p),signature_level_two(q)
 assert sp==direct_segment_integral(p) and sq==direct_segment_integral(q)
 longer=path(((0,0),(1,0),(1,1),(2,1),(2,2)));pop=segmentation_population(longer,(1,2,3),3)
 out["ordered_movement.json"]={"schema":"singularity.ordered-movement/1","evidence":"synthetic_exact","axis_paths":{"first":sp.first,"P_second":sp.second,"Q_second":sq.second,"P_doubled_area":sp.second[0][1]-sp.second[1][0],"Q_doubled_area":sq.second[0][1]-sq.second[1][0]},"segmentation_ids":tuple(r["segmentation_id"] for r in pop),"segmentation_count":len(pop),"feature_uncertainty":feature_uncertainty(tuple(r["feature"] for r in pop)),"overlap_refusal":finite_population_separation(((0,),(1,)),((1,),(2,))),"population_multiplicity":signature_population((("original-a",p,2),("original-b",p,3)))["total_multiplicity"],"merge_contract":"full signatures compose by Chen; partial current features need not preserve future values"}
 # Signature objects occur only in local population construction, not JSON.
 return {name:json_exact(value) for name,value in out.items()}


def main():
 p=argparse.ArgumentParser();p.add_argument("--check",action="store_true");args=p.parse_args()
 out=receipts()
 for name,receipt in out.items():
  path=ROOT/"results"/name;text=json.dumps(receipt,indent=2,sort_keys=True)+"\n"
  if args.check:
   if path.read_text()!=text:raise SystemExit("stale exact receipt: "+name)
  else:path.write_text(text)
 # Verify public source bytes against retained provenance, without network.
 manifest=ROOT/"applications/nx25_30/source_manifest.json"
 if manifest.exists():
  declared=json.loads(manifest.read_text())
  for entry in declared["public_files"]+declared.get("empirical_aggregate_files",[]):
   actual=hashlib.sha256((ROOT/entry["path"]).read_bytes()).hexdigest()
   if actual!=entry["sha256"]:raise SystemExit("public source hash mismatch: "+entry["path"])
 measured=public_measurement_replay() if args.check else "run --check for independent measured source replay"
 print(json.dumps({"status":"checked" if args.check else "generated","exact_receipts":len(out),"source_replay":"offline; restricted NFL rows not required","measured_replay":measured}))


if __name__=="__main__":main()
