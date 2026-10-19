#!/usr/bin/env python3
"""Deterministic NX31–36 receipts; --slow independently replays both loop paths."""
from __future__ import annotations
import argparse
from dataclasses import is_dataclass,fields,replace
from fractions import Fraction as Q
from pathlib import Path
import hashlib,json,sys,time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def encode(value):
    if isinstance(value,Q):return [value.numerator,value.denominator]
    if hasattr(value,'packet'):return encode(value.packet())
    if is_dataclass(value):return {f.name:encode(getattr(value,f.name))for f in fields(value)}
    if isinstance(value,dict):return {str(k):encode(v)for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [encode(v)for v in value]
    return value


def digest(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def period_receipt():
    from singularity.period_observations import (RationalConnection,differential_closure,
        transport_targets,legendre_connection,legendre_series,legendre_quadrature)
    connection=RationalConnection(((0,1,0),(0,0,0),(0,0,2)))
    closure=differential_closure(connection,((1,0,0),))
    nilpotent=transport_targets(connection,((1,0,0),),(0,Q(1,2)),(2,3,5),(Q(1,10),Q(1,5),7))
    family=legendre_connection();seed,radii=legendre_series(Q(1,2),48)
    target=differential_closure(family,((1,0),))
    transported=transport_targets(family,((1,0),),(Q(1,2),Q(9,16)),seed,radii)
    direct,errors=legendre_series(Q(9,16),80)
    quadrature=legendre_quadrature(Q(9,16),128)
    interval=transported['outputs'][0]['interval']
    assert interval[0]<=direct[0]<=direct[0]+errors[0]<=interval[1]
    assert quadrature[0]<=interval[0]<=interval[1]<=quadrature[1]
    return {'schema':'nx31.acceptance/1','nilpotent':{'closure':closure,'transport':nilpotent},
        'geometric':{'family':'Legendre y²=x(1-x)(1-tx); F=2K/pi',
            'observable_rank':target.rank,'full_rank':2,'transport':transported,
            'independent_hypergeometric':(direct,errors),'independent_euler_quadrature':quadrature},
        'scope':'rational connections dim<=4, input degrees<=6, regular real charts; no flux interpretation'}


def monodromy_receipt(slow=False):
    from singularity.monodromy_experiments import MonodromyLanguage,bounded_robust_experiments
    from singularity.period_observations import _backend
    paths=(['1/2',[0,'1/2'],'-1/2',[0,'-1/2'],'1/2'],
           ['1/2',[1,'-1/2'],'3/2',[1,'1/2'],'1/2'])
    receipts=tuple(json.loads((ROOT/f'results/nx36/nx32_legendre_loop{i}.json').read_text())for i in range(2))
    if slow:
        for p,r in zip(paths,receipts):
            assert _backend('period_matrix_balls').verify_marked_legendre_monodromy(p,r,order=16,rounding_bits=96)
    matrices=tuple(r['monodromy']for r in receipts)
    assert matrices==([[1,2],[0,1]],[[1,0],[-2,1]])
    for r in receipts:
        assert Q(r['enclosure']['row_error_bound'])<Q(1,2)
        assert len(r['continued']['transport']['steps'])==215
    language=MonodromyLanguage(matrices,((1,0),),basepoint='t=1/2',basis='marked Legendre a,b',
        loops=('loop around0','loop around1'),source_revision='pinned PerfectPower',geometric=True)
    toy=MonodromyLanguage((((1,1),(0,1)),((1,0),(1,1))),((1,0),))
    robust=bounded_robust_experiments(toy,(0,Q(1,100)),4,Q(1,100))
    return {'schema':'nx32.acceptance/1','actual_matrices':matrices,'closure_rank':language.closure().rank,
        'paths':paths,'continuation_files':{f'results/nx36/nx32_legendre_loop{i}.json':digest(f'results/nx36/nx32_legendre_loop{i}.json')for i in range(2)},
        'toy_chronological_readings':(toy.reading((1,0),0,(0,1)),toy.reading((1,0),0,(1,0))),
        'cheapest_exact':toy.cheapest((0,Q(1,100))),
        'cheapest_robust':next(r for r in robust if r[-1]),
        'integrality_premise':'continuation of the explicitly marked integral a,b cycles, not numerical proximity',
        'relations_checked':'each determinant1; each unipotent (T-I)^2=0; commutator nonidentity; no unsupported finite-presentation claim'}


def quotient_receipt():
    from singularity.period_observations import (RationalConnection,legendre_connection,legendre_series,
        transport_targets,differential_closure)
    from singularity.moving_quotients import construct_quotient,gauge_quotient,verify_overlap,obstruction_at
    source=RationalConnection(((0,-1),(0,0)))
    q=construct_quotient(source,((1,(0,1)),),((1,(0,1)),))
    g=gauge_quotient(q,(((1,1),),));assert verify_overlap(q,g,(((1,1),),))
    bad=obstruction_at(RationalConnection(((0,0),(0,1))),((1,(0,1)),),Q(0))
    family=legendre_connection();base=construct_quotient(family,((1,0),(0,1)),((1,0),))
    changed=gauge_quotient(base,((1,0),(0,(0,1))))
    seed,radii=legendre_series(Q(1,2),48);bseed=(seed[0],Q(1,2)*seed[1]);brad=(radii[0],Q(1,2)*radii[1])
    reduced=RationalConnection(changed.reduced_connection,family.chart,family.source_revision)
    predictions=[]
    for path in ((Q(1,2),Q(9,16)),(Q(1,2),Q(17,32),Q(9,16))):
        predictions.append(transport_targets(reduced,changed.target_coordinates,path,bseed,brad))
    direct,error=legendre_series(Q(9,16),80)
    for record in predictions:
        a,b=record['outputs'][0]['interval'];assert a<=direct[0]<=direct[0]+error[0]<=b
    parameter_ranks=tuple((p,differential_closure(RationalConnection(((0,0),(0,1))),((p,1),)).rank)for p in (-1,0,1))
    return {'schema':'nx33.acceptance/1','moving_constant':q,'gauged':g,'leakage':bad,
        'legendre_full':base,'legendre_chart':changed,'independent_predictions':predictions,
        'external_constant_parameter_rank_strata':parameter_ranks,
        'chart_scope':'Legendre excludes0,1; gauge second coordinate t excludes0; no claim of holonomy from a local gauge law'}


def visibility_receipt():
    from singularity.complex_visibility import (improved_visibility_certificate,combinatorial_tail,
        polynomial_rectangle_certificate,factored_polynomial_zero_count)
    from singularity.examples import GRAPHS
    r=improved_visibility_certificate(GRAPHS['spectral_g'],GRAPHS['spectral_h'],Q(1,2),2,Q(1,25000))
    return {'schema':'nx34.acceptance/1','improved_reference':r,'old_radius':Q(1,100000),'improvement_factor':4,
        'geometric_tail':combinatorial_tail(1,3,Q(1,2)),
        'interior_zero':factored_polynomial_zero_count((-Q(1,4),1),(Q(1,4),),0,Q(1,2)),
        'subdivision':polynomial_rectangle_certificate((1,0,1),(-Q(9,10),Q(9,10),-Q(1,10),Q(1,10)),max_depth=4),
        'limiter':'graph-span derivative perturbation; not an obstruction to the actual analytic domain'}


def thermal_refinement():
    from singularity.thermal_diagnostics import build_plate_candidates,simulate_protocol
    from singularity.fidelity_design import certify_dynacomp_option
    from singularity.refinement_planner import (RefinementProblem,margin_from_readings,
        refine_decision,decision_bounds,replay_refinement)
    models=build_plate_candidates(4)[:3];protocols=(((2,0,2),2),((2,2),1));ids=('left-pulse3','center-step2')
    coarse={};fine={};required=[];pairs=((0,1),(0,2),(1,2))
    for e,(word,sensor)in enumerate(protocols):
        for c,m in enumerate(models):coarse[e,c]=certify_dynacomp_option(m,sensor,word,1,physical_radius=Q(1,100000))
        required.append(tuple(margin_from_readings(ids[e],p,coarse[e,p[0]].reading,coarse[e,p[1]].reading,
            binding=('source-bound-4x4',))for p in pairs))
    problem=RefinementProblem(ids,(1,2),tuple(m.identifier for m in models),required)
    refined_keys=[]
    def oracle(e,p,old):
        a,b=pairs[p];word,sensor=protocols[e]
        for c in (a,b):
            if(e,c)not in fine:
                fine[e,c]=certify_dynacomp_option(models[c],sensor,word,16,physical_radius=Q(1,100000));refined_keys.append((e,c))
        return margin_from_readings(ids[e],(a,b),fine[e,a].reading,fine[e,b].reading,
            fidelity=old.fidelity+1,binding=('source-bound-4x4',))
    result=refine_decision(problem,oracle);assert replay_refinement(problem,result)
    assert result['status']=='optimal'and result['upper']==1
    plan_refinements=tuple(refined_keys)
    # Full evaluation is an independent validation baseline, counted separately.
    for e,(word,sensor)in enumerate(protocols):
        for c,m in enumerate(models):
            option=fine.get((e,c))or certify_dynacomp_option(m,sensor,word,16,physical_radius=Q(1,100000))
            fine[e,c]=option
            exact=simulate_protocol(m,word,sensor)
            assert abs(exact-option.reading.center)<=option.reading.computational_radius
            assert abs(exact-coarse[e,c].reading.center)<=coarse[e,c].reading.computational_radius
    fullrows=tuple(tuple(margin_from_readings(ids[e],p,fine[e,p[0]].reading,fine[e,p[1]].reading,
        fidelity=1,binding=('source-bound-4x4',))for p in pairs)for e in range(2))
    full=decision_bounds(problem,fullrows);assert full['upper']==result['upper']
    dominated=tuple(tuple(replace(m,lower=m.lower-2,upper=m.upper-2)for m in row)for row in fullrows)
    source_dominated=decision_bounds(problem,dominated);assert source_dominated['lower']is None
    return {'problem':problem,'result':result,'full_fidelity_bounds':full,
        'source_uncertainty_dominated':source_dominated,'initial_evaluations':6,
        'planner_high_fidelity_evaluations':len(plan_refinements),'full_fidelity_baseline_evaluations':6,
        'validation_evaluations_separate_from_planner':6-len(plan_refinements),
        'refined_original_models':tuple((ids[e],models[c].identifier)for e,c in plan_refinements),
        'source_receipts':tuple(coarse.values())+tuple(fine.values()),
        'interpretation':'synthetic 4x4 source-bound model; physical radius is an assumption'},models,protocols,fine


def decisions_receipt(thermal,models,protocols,fine):
    from singularity.decision_certificates import make_problem,make_decision_certificate,verify_decision_certificate
    from singularity.thermal_diagnostics import simulate_protocol
    source={'models':encode(models),'protocols':encode(protocols)}
    source_digest=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()
    intervals=tuple(tuple((fine[e,c].reading.lower,fine[e,c].reading.upper)for c in range(3))for e in range(2))
    problem=make_problem(tuple(m.identifier for m in models),tuple(m.identifier for m in models),
        ('left-pulse3','center-step2'),(1,2),intervals,model_revision='source-bound-4x4',
        source_bindings=(source_digest,),catalogue_scope='exactly the two declared reset protocols; not all heater words')
    cert=make_decision_certificate(problem,(0,));assert verify_decision_certificate(cert,problem)
    return {'schema':'nx36.acceptance/1','thermal_source':source,'thermal_certificate':cert,
        'external_premises':'each source-bound DynaComp error enclosure and synthetic physical radius1/100000',
        'checker_scope':'primitive exact schema, strict interval gaps, complete local mask-DP transitions and external domain binding',
        'formal_scope':'semantic pair separation plus exclusion of every cheaper admissible panel; no Python/parser/calibration verification'}


def receipts(slow=False):
    thermal,models,protocols,fine=thermal_refinement()
    return {'NX31':period_receipt(),'NX32':monodromy_receipt(slow),'NX33':quotient_receipt(),
        'NX34':visibility_receipt(),'NX35':thermal,'NX36':decisions_receipt(thermal,models,protocols,fine)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--slow',action='store_true')
    args=parser.parse_args();data=receipts(args.slow)
    for track,record in data.items():
        path=ROOT/f'results/nx36/{track.lower()}_acceptance.json'
        text=json.dumps(encode(record),indent=2,sort_keys=True)+'\n'
        if args.check:
            if not path.is_file()or path.read_text()!=text:raise SystemExit(f'{track} receipt mismatch')
        else:path.write_text(text)
    print('NX31–NX36 deterministic receipts '+('replayed'if args.check else'written'))

if __name__=='__main__':main()
