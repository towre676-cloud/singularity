"""Independent direct oracles for six bounded application contracts."""
import unittest
from fractions import Fraction as Q
from itertools import product,combinations
from singularity._application_exact import (apply,multiply,identity,box_vertices,
                                           box_estimator,json_exact)
from singularity.forecast_targets import (ForecastTarget,SensorBlock,forecast_row,
 target_factorization,target_null_witness,select_target_panel,known_input_offset)
from singularity.movement_design import (movement_condition,target_identifiable,
 movement_null_witness,bounded_target_estimator,minimum_drill_repair,independent_repeat_variance)
from singularity.nonlinear_fibres import (Polynomial,PolynomialFibre,verify_witness,
 affine_quadratic_constancy,curved_second_variation,minimum_witness_repair)
from singularity.multiscale_transport import (linear_commutation_defect,box_defect_bound,
 propagate_scale_error,exact_target_quotient,reachable_zonotopes,zonotope_range,
 compose_linear_defects,target_transfer_bound)
from singularity.reactive_transport import (conversion_mixing,reaction_flux_step,
 verify_conservation,verify_positive_step,reactive_target_rows,species_sensor_panel)
from singularity.ordered_movement import (RationalPath,signature_level_two,direct_segment_integral,
 chen_compose,time_augment,segmentation_population,signature_population,
 feature_uncertainty,finite_population_separation,flatten_signature)


def model(h=3,basis=None):return ForecastTarget(((1,1),(0,1)),(1,0),h,"state","1 s","box",basis)
def sensor(name,row,radius,cost=1):return SensorBlock(name,(row,),(radius,),cost,"state","box")
def path(points,times=None):return RationalPath(points,tuple(range(len(points))) if times is None else times,("m",)*len(points[0]),"lab")


class ForecastTests(unittest.TestCase):
 def test_rows_against_direct_trajectories(self):
  for h in range(9):
   m=model(h)
   for state in product(range(-2,3),repeat=2):
    x=state
    for _ in range(h):x=(x[0]+x[1],x[1])
    self.assertEqual(sum(a*b for a,b in zip(forecast_row(m),state)),x[0])
 def test_factorization_and_null(self):
  g=(forecast_row(model()),)
  self.assertIsNone(target_factorization(((1,0),),g))
  n=target_null_witness(((1,0),),g);self.assertEqual(n,(0,1))
  self.assertEqual(target_factorization(identity(2),g),((1,3),))
  self.assertEqual(target_factorization(((1,0),),g,((1,),(0,))),((1,),))
 def test_existing_target_recovery_crosswalk(self):
  from singularity.target_recovery import TargetRecoveryProblem,target_identifiability
  for h,z in ((((1,0),),None),(((1,0),),((1,),(0,))),(identity(2),None)):
   g=((1,3),);baseline=target_identifiability(TargetRecoveryProblem(h,g,admissible_basis=z))
   self.assertEqual(target_factorization(h,g,z) is not None,baseline.status=="identifiable")
   if baseline.decoder is not None:self.assertEqual(target_factorization(h,g,z),baseline.decoder)
 def test_box_error_attainability(self):
  w,e=box_estimator(identity(2),(1,3),(Q(1,10),Q(1,5)))
  self.assertEqual(e,Q(7,10))
  self.assertEqual(e,max(abs(sum(a*b for a,b in zip(w,v))) for v in box_vertices((0,0),(Q(1,10),Q(1,5)))))
 def test_panel_exhaustive_and_boundary(self):
  blocks=(sensor("p",(1,0),Q(1,10)),sensor("v",(0,1),Q(1,5)),sensor("direct",(1,3),Q(3,4),3))
  r=select_target_panel(blocks,model(),max_error=Q(7,10));self.assertEqual(r["selected"],("p","v"))
  self.assertEqual(select_target_panel(blocks,model(),max_error=Q(7,10),strict=True)["status"],"infeasible_catalogue")
  self.assertLess(box_estimator(((1,0),(0,1)),(1,3),(1,1))[1],box_estimator(((1,0),(0,Q(1,10))),(1,3),(1,1))[1])
 def test_l1_support_optimizer_against_box_vertex_oracle(self):
  # Any weights with w1+w3=1,w2+w3=2. Breakpoints of convex absolute sum are 0,1,2.
  h=((1,0),(0,1),(1,1));r=(Q(1,3),Q(1,2),Q(1,4))
  w,e=box_estimator(h,(1,2),r)
  brute=min(sum(abs(v)*eps for v,eps in zip((1-t,2-t,t),r)) for t in (0,1,2))
  self.assertEqual(e,brute)
 def test_malformed(self):
  with self.assertRaises(TypeError):model(3.0)
  with self.assertRaises(ValueError):ForecastTarget(((1,),),(1,),0,"","s","D")
  with self.assertRaises(TypeError):sensor("x",(1,0),0.1)
  with self.assertRaises(ValueError):select_target_panel((SensorBlock("x",((1,0),),(0,),1,"other","box"),),model())
 def test_known_inputs_and_bounded_domain(self):
  m=ForecastTarget(((1,1),(0,1)),(1,0),3,"p,v","1s","bounded",None,(0,0),(1,2))
  us=((1,),(2,),(-1,));x=(0,0)
  for u in us:x=(x[0]+x[1],x[1]+u[0])
  self.assertEqual(known_input_offset(m,((0,),(1,)),us),x[0])
 def test_affine_center_offset_is_not_lost(self):
  m=ForecastTarget(identity(2),(1,1),0,"u","s","D",((1,),(0,)),(0,2),(1,0))
  b=SensorBlock("x",((1,0),),(0,),1,"u","D")
  r=select_target_panel((b,),m,max_error=0)
  self.assertEqual(r["affine_offset"],2)
  for x in (-1,0,1):self.assertEqual(r["affine_offset"]+r["weights"][0]*x,x+2)
 def test_independent_panel_oracle(self):
  blocks=(sensor("p",(1,0),Q(1,10)),sensor("v",(0,1),Q(1,5)),sensor("sum",(1,1),Q(1,4),2),sensor("future",(1,3),Q(3,4),3),sensor("fast",(0,2),Q(1,2)),sensor("scaled",(2,6),1,4))
  expected=[]
  for mask in product((0,1),repeat=len(blocks)):
   ix=[i for i,v in enumerate(mask) if v];candidates=[]
   for i in ix:
    a,b=blocks[i].rows[0]
    if a and b==3*a:candidates.append(abs(1/a)*blocks[i].radii[0])
   for i,j in combinations(ix,2):
    a,b=blocks[i].rows[0];c,d=blocks[j].rows[0];det=a*d-b*c
    if det:candidates.append(abs((d-3*c)/det)*blocks[i].radii[0]+abs((3*a-b)/det)*blocks[j].radii[0])
   if candidates and min(candidates)<=Q(7,10):expected.append((sum(blocks[i].cost for i in ix),min(candidates),tuple(blocks[i].identifier for i in ix)))
  actual=select_target_panel(blocks,model(),max_error=Q(7,10));self.assertEqual((actual["cost"],actual["error_radius"],actual["selected"]),min(expected));self.assertEqual(actual["panels_checked"],64)


class FibreTests(unittest.TestCase):
 def test_quadratic_witness_and_diameter(self):
  x=Polynomial(2,{(1,0):1});y2=Polynomial(2,{(0,2):1})
  f=PolynomialFibre((-1,-1),(1,1),(x,),y2)
  r=verify_witness(f,(0,0),(0,1));self.assertEqual(r["target_gap"],1);self.assertIsNone(r["complete_diameter"])
  self.assertEqual(y2.gradient((0,0)),(0,0))
 def test_disconnected_branches(self):
  x2=Polynomial(1,{(2,):1});x=Polynomial(1,{(1,):1})
  r=verify_witness(PolynomialFibre((-1,),(1,),(x2,),x),(-1,),(1,))
  self.assertEqual(r["target_gap"],2);self.assertNotEqual(x2.gradient((-1,)),(0,))
 def test_affine_criterion_direct_expansion(self):
  r=affine_quadratic_constancy((1,2),((0,),(1,)),(0,0),((0,0),(0,2)),relatively_open=True)
  self.assertEqual(r["linear_coefficients"],(4,));self.assertEqual(r["quadratic_hessian"],((2,),))
  for z in range(-3,4):self.assertEqual((2+z)**2,4+r["linear_coefficients"][0]*z+r["quadratic_hessian"][0][0]*z*z/2)
 def test_parabola_curvature(self):
  k=Polynomial(2,{(0,1):1,(2,0):-1});t=Polynomial(2,{(0,1):1})
  r=curved_second_variation((k,),t,(0,0),(1,0))
  self.assertEqual(r["second_variation"],2);self.assertEqual(t.hessian((0,0)),((0,0),(0,0)))
  # Direct chart (s,s²): target at +/-1 minus twice at zero is 2.
  self.assertEqual(t.evaluate((1,1))+t.evaluate((-1,1))-2*t.evaluate((0,0)),r["second_variation"])
 def test_circle_two_charts_and_singular(self):
  k=Polynomial(2,{(2,0):1,(0,2):1,(0,0):-1});t=Polynomial(2,{(1,0):1})
  self.assertEqual(curved_second_variation((k,),t,(1,0),(0,1))["second_variation"],-1)
  self.assertEqual(curved_second_variation((k,),t,(1,0),(0,-1))["second_variation"],-1)
  # Two opposite rational circle charts x=(1-u²)/(1+u²), y=+/-2u/(1+u²).
  for u in (Q(1,5),Q(1,3)):
   a=(1-u*u)/(1+u*u);b=2*u/(1+u*u)
   self.assertEqual(k.evaluate((a,b)),0);self.assertEqual(k.evaluate((a,-b)),0)
  for sign in (-1,1):
   self.assertEqual(curved_second_variation((k,),t,(1,0),(0,2*sign))["second_variation"],-4)
  # Both rational chart target functions obey (1+u²)(T(u)-1)=-2u².
  u=Q(1,7);self.assertEqual((1+u*u)*((1-u*u)/(1+u*u)-1),-2*u*u)
  singular=Polynomial(2,{(2,0):1})
  self.assertEqual(curved_second_variation((singular,),t,(0,0),(0,1))["status"],"singular_stratum")
 def test_finite_repair_is_not_global(self):
  sx=Polynomial(2,{(1,0):1});sy=Polynomial(2,{(0,1):1})
  r=minimum_witness_repair((((-1,0),(1,0)),),(("x",sx,0,1),("y",sy,0,2)))
  self.assertEqual(r["selected"],("x",));self.assertFalse(r["global_fibre_constancy"])
  self.assertEqual(sx.evaluate((0,-1)),sx.evaluate((0,1)))
  self.assertEqual(minimum_witness_repair((((-1,0),(1,0)),),(("x",sx,1,1),))["status"],"infeasible_finite_witnesses")
 def test_invalid_domain_and_witness(self):
  p=Polynomial(1,{(1,):1})
  with self.assertRaises(TypeError):PolynomialFibre((float('-inf'),),(1,),(p,),p)
  self.assertEqual(verify_witness(PolynomialFibre((-1,),(1,),(p,),p),(2,),(0,))["status"],"invalid_state")


class MultiscaleTests(unittest.TestCase):
 def setUp(self):
  self.a=((Q(7,8),Q(1,8),0,0),(Q(1,8),Q(3,4),Q(1,8),0),(0,Q(1,8),Q(3,4),Q(1,8)),(0,0,Q(1,8),Q(7,8)))
  self.e=((Q(1,2),Q(1,2),0,0),(0,0,Q(1,2),Q(1,2)));self.c=((Q(15,16),Q(1,16)),(Q(1,16),Q(15,16)))
 def test_flux_and_defect(self):
  d=linear_commutation_defect(self.a,self.c,self.e,fine_units="K",coarse_units="K",time_step="1s")
  self.assertEqual(apply(d,(0,1,0,0)),(-Q(1,32),Q(1,32)))
  for x in product((0,1),repeat=4):
   flux=tuple(x[i]+Q(1,8)*sum(x[j]-x[i] for j in (i-1,i+1) if 0<=j<4) for i in range(4))
   self.assertEqual(apply(self.a,x),flux)
  self.assertEqual(exact_target_quotient(self.a,((1,1,1,1),)),((1,),))
 def test_box_vertices_and_enrichment(self):
  d=linear_commutation_defect(self.a,self.c,self.e,fine_units="K",coarse_units="K",time_step="1s")
  bound=box_defect_bound(d,(0,0,0,0),(1,1,1,1))
  for j in range(2):self.assertEqual(bound[j],max(abs(apply(d,v)[j]) for v in box_vertices((0,0,0,0),(1,1,1,1))))
  enriched=self.e+(d[0],);quotient=exact_target_quotient(self.a,enriched)
  self.assertIsNotNone(quotient);self.assertEqual(multiply(enriched,self.a),multiply(quotient,enriched))
  self.assertGreater(max(bound),0)
  newdefect=linear_commutation_defect(self.a,quotient,enriched,fine_units="K",coarse_units="K/step",time_step="1s")
  self.assertEqual(max(box_defect_bound(newdefect,(0,0,0,0),(1,1,1,1))),0)
 def test_reachable_and_horizon(self):
  domains=reachable_zonotopes(self.a,(0,0,0,0),identity(4),8)
  d=linear_commutation_defect(self.a,self.c,self.e,fine_units="K",coarse_units="K",time_step="1s")
  ds=[max(max(abs(a),abs(b)) for a,b in zonotope_range(d,c,g)) for c,g in domains[:-1]]
  bounds=propagate_scale_error(0,1,ds)
  for v in box_vertices((0,0,0,0),(1,1,1,1)):
   x=v;z=apply(self.e,v)
   for t in range(9):
    self.assertLessEqual(max(abs(a-b) for a,b in zip(apply(self.e,x),z)),bounds[t]);x=apply(self.a,x);z=apply(self.c,z)
  self.assertEqual(target_transfer_bound(1,2,3)["total_bound"],7)
 def test_three_scale_composition_and_units(self):
  r=compose_linear_defects(self.a,self.c,((1,),),self.e,((Q(1,2),Q(1,2)),))
  self.assertTrue(r["identity_holds"])
  # Celsius-to-double-degree scaling has to appear in E, not just a label.
  self.assertEqual(linear_commutation_defect(((1,),),((1,),),((2,),),fine_units="C",coarse_units="2C",time_step="s"),((0,),))
  with self.assertRaises(ValueError):linear_commutation_defect(self.a,self.c,self.e,fine_units="",coarse_units="K",time_step="s")
 def test_bounded_inputs_correlated_domain(self):
  a=((1,Q(1,2)),(0,Q(1,2)));g=((1,),(1,));u=((1,),(0,));domains=reachable_zonotopes(a,(0,0),g,3,u)
  for signs in product((-1,1),repeat=4):
   x=(Q(signs[0]),Q(signs[0]))
   for forcing in signs[1:]:x=(x[0]+x[1]/2+forcing,x[1]/2)
   ranges=zonotope_range(identity(2),*domains[-1])
   self.assertTrue(all(lo<=v<=hi for (lo,hi),v in zip(ranges,x)))
  # Initial correlation x1=x2 excludes independent opposite-sign corners.
  self.assertEqual(zonotope_range(((1,-1),),*domains[0]),((0,0),))


class ReactiveTests(unittest.TestCase):
 def test_conservative_oracle_and_blindness(self):
  d=((Q(7,8),Q(1,8)),(Q(1,8),Q(7,8)));m=conversion_mixing(d,Q(1,4));h=((1,0,1,0),(0,1,0,1))
  self.assertTrue(verify_positive_step(m));self.assertTrue(verify_conservation(m));self.assertEqual(multiply(h,m),multiply(d,h))
  for state in identity(4):self.assertEqual(apply(m,state),reaction_flux_step(state,d,Q(1,4)))
  a,b=(1,0,0,0),(0,0,1,0)
  for t in range(9):
   self.assertEqual(apply(h,a),apply(h,b));self.assertEqual(abs(sum(a[2:])-sum(b[2:])),Q(3,4)**t)
   a=apply(m,a);b=apply(m,b)
  self.assertIsNotNone(target_null_witness(h,(reactive_target_rows(m,(0,0,1,1),1)[1],)))
  self.assertEqual(target_factorization(h+((1,1,0,0),),(reactive_target_rows(m,(0,0,1,1),1)[1],)) is not None,True)
 def test_weighted_conservation_and_rate_uncertainty(self):
  # One A molecule produces two B molecules: unweighted count is not conserved.
  m=((Q(3,4),0),(Q(1,2),1))
  self.assertFalse(verify_conservation(m));self.assertTrue(verify_conservation(m,(2,1)))
  hs={"A":((1,),),"B":((0,),)}
  exps=(("total",{"A":(1,),"B":(1,)},0,1),("species",{"A":(Q(1,4),Q(1,2)),"B":(1,)},Q(1,4),1))
  self.assertEqual(species_sensor_panel(hs,exps)["status"],"infeasible_interval_separation")
  exps=exps[:1]+(("species",{"A":(Q(1,4),Q(1,2)),"B":(1,)},Q(1,8),2),)
  self.assertEqual(species_sensor_panel(hs,exps)["selected"],("species",))
 def test_exhaustive_species_panel_oracle(self):
  h={"a":(),"b":(),"c":()};exps=(("one",{"a":(0,),"b":(1,),"c":(1,)},0,1),("two",{"a":(0,),"b":(0,),"c":(1,)},0,2),("all",{"a":(0,),"b":(1,),"c":(2,)},0,4))
  candidates=[]
  for mask in product((0,1),repeat=3):
   ix=[i for i,v in enumerate(mask) if v]
   readings={label:tuple(exps[i][1][label][0] for i in ix) for label in h}
   if len(set(readings.values()))==3:candidates.append((sum(exps[i][3] for i in ix),tuple(exps[i][0] for i in ix)))
  actual=species_sensor_panel(h,exps);self.assertEqual((actual["cost"],actual["selected"]),min(candidates))


class MovementTests(unittest.TestCase):
 def test_four_conditions_and_restricted_target(self):
  kw={"normalization":"fixed s,a","response_definition":"acceleration"}
  x=tuple(movement_condition(s,a,**kw) for s,a in ((0,0),(1,0),(0,1)))
  target=movement_condition(1,1,**kw);n=movement_null_witness(x,target)
  self.assertEqual(n,(0,0,0,1));self.assertFalse(target_identifiable(x,target));self.assertTrue(target_identifiable(x,(1,1,0,0)))
  self.assertTrue(target_identifiable(x+(target,),target))
  for row in x:self.assertEqual(sum(a*b for a,b in zip(row,n)),0)
  beta=(2,3,5,7)
  for s,a in ((0,0),(1,0),(0,1),(1,1)):
   row=movement_condition(s,a,**kw);self.assertEqual(sum(u*v for u,v in zip(row,beta)),2+3*s+5*a+7*s*a)
 def test_robust_minimum_repair_and_replication(self):
  norm="fixed";response="a";existing=((1,0,0,0),(1,1,0,0),(1,0,1,0));target=(1,1,1,1)
  candidates=(SensorBlock("interaction",(target,),(Q(1,10),),2,norm,response),SensorBlock("weak",((1,Q(1,2),Q(1,2),Q(1,4)),),(Q(1,10),),1,norm,response))
  result=minimum_drill_repair(existing,candidates,target,normalization=norm,response_definition=response,max_error=Q(1,5))
  self.assertEqual(result["selected"],("interaction",))
  self.assertIsNone(bounded_target_estimator(existing,target,(Q(1,10),)*3))
  self.assertEqual(independent_repeat_variance(1,4)["variance"],Q(1,4));self.assertEqual(independent_repeat_variance(1,4)["worst_case_radius"],1)
  self.assertFalse(target_identifiable(existing+existing,target))
 def test_no_repair_and_bad_scaling(self):
  with self.assertRaises(ValueError):movement_condition(0,1,normalization="",response_definition="a")
  h=((1,0,0,0),);candidate=SensorBlock("repeat",h,(0,),1,"fixed","response")
  self.assertEqual(minimum_drill_repair(h,(candidate,),(0,0,0,1),normalization="fixed",response_definition="response")["status"],"infeasible_catalogue")


class SignatureTests(unittest.TestCase):
 def test_axis_order_and_independent_integral(self):
  p=path(((0,0),(1,0),(1,1)));q=path(((0,0),(0,1),(1,1)))
  a,b=signature_level_two(p),signature_level_two(q)
  self.assertEqual(a,direct_segment_integral(p));self.assertEqual(b,direct_segment_integral(q))
  self.assertEqual(a.first,b.first);self.assertEqual(a.second,((Q(1,2),1),(0,Q(1,2))))
  self.assertEqual(a.second[0][1]-a.second[1][0],1);self.assertEqual(b.second[0][1]-b.second[1][0],-1)
 def test_chen_associative_three_segments(self):
  ps=[signature_level_two(path(((0,0),v))) for v in ((1,0),(0,2),(-1,1))]
  self.assertEqual(chen_compose(chen_compose(ps[0],ps[1]),ps[2]),chen_compose(ps[0],chen_compose(ps[1],ps[2])))
  whole=path(((0,0),(1,0),(1,2),(0,3)))
  self.assertEqual(signature_level_two(whole),chen_compose(chen_compose(ps[0],ps[1]),ps[2]))
 def test_translation_scaling_reparam_reflection_reversal(self):
  p=path(((0,0),(1,0),(1,1)),(0,1,2));s=signature_level_two(p)
  self.assertEqual(s,signature_level_two(path(((3,4),(4,4),(4,5)),(0,Q(1,8),7))))
  self.assertEqual(s,signature_level_two(path(((0,0),(Q(1,3),0),(1,0),(1,1)),(0,Q(1,9),Q(1,2),9))))
  reflected=signature_level_two(path(((0,0),(-1,0),(-1,1))))
  self.assertEqual(reflected.second[0][1]-reflected.second[1][0],-1)
  reverse=signature_level_two(path(tuple(reversed(p.points))))
  self.assertEqual(reverse.first,(-1,-1));self.assertEqual(reverse.second[0][1]-reverse.second[1][0],-1)
  self.assertNotEqual(signature_level_two(time_augment(p)),signature_level_two(time_augment(path(p.points,(0,Q(1,8),7)))))
 def test_population_multiplicity_and_segmentation(self):
  p=path(((0,0),(1,0),(1,1),(2,1),(2,2)))
  pop=signature_population((("a",p,2),("b",path(p.points,(0,1,3,4,8)),3)))
  self.assertEqual(pop["total_multiplicity"],5);self.assertEqual(len(pop["groups"]),1);self.assertEqual(pop["groups"][0]["original_ids"],["a","b"])
  seg=segmentation_population(p,(1,2,3),3);self.assertEqual(len(seg),3)
  self.assertEqual({x["segmentation_id"] for x in seg},set(combinations((1,2,3),2)))
  u=feature_uncertainty(tuple(x["feature"] for x in seg));self.assertGreater(u["distinct_values"],1)
 def test_unsafe_partial_merge_and_overlap(self):
  a=signature_level_two(path(((0,0),(1,0))));b=signature_level_two(path(((0,0),(0,1))));future=b
  self.assertEqual(a.second[0][1]-a.second[1][0],b.second[0][1]-b.second[1][0])
  ca,cb=chen_compose(a,future),chen_compose(b,future)
  self.assertNotEqual(ca.second[0][1]-ca.second[1][0],cb.second[0][1]-cb.second[1][0])
  self.assertFalse(finite_population_separation(((0,),(1,)),((1,),(2,)))["guaranteed_distinction"])
  self.assertFalse(finite_population_separation(((0,),),((2,),),1)["guaranteed_distinction"])
 def test_bad_schema(self):
  with self.assertRaises(ValueError):path(((0,0),(1,1)),(0,0))
  with self.assertRaises(TypeError):path(((0.,0),(1,1)))
 def test_coordinate_frames_preserved(self):
  p=path(((0,0),(1,0)));q=RationalPath(p.points,p.times,p.channel_units,"body")
  a,b=signature_level_two(p),signature_level_two(q)
  self.assertEqual(a.coordinate_frame,"lab");self.assertEqual(b.coordinate_frame,"body")
  with self.assertRaises(ValueError):chen_compose(a,b)
  self.assertEqual(len(signature_population((("lab",p,1),("body",q,1)))["groups"]),2)


if __name__=="__main__":unittest.main()
