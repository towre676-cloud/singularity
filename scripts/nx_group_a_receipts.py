"""Deterministic independent replay pilots for NX02--NX06.

The five public script entry points dispatch here so the source stencil,
cost accounting and rational JSON encoding are reviewed in one place.
"""
from dataclasses import asdict, is_dataclass
from fractions import Fraction as F
from hashlib import sha256
from itertools import combinations, product
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from singularity.thermal_diagnostics import (build_plate_candidates,simulate_protocol,
                                            protocol_pool,default_protocols)
from singularity.candidate_boxes import (from_diagnostic_pool,minimum_candidate_box_panel,
                                         uncoverable_pairs,candidate_box_masks,candidate_box_consistent)
from singularity.joint_uncertainty import (JointObservationFamily,affine_protocol_family,
    joint_pair_certificate,verify_joint_certificate,minimum_joint_panel,project_panel)
from singularity.fault_population import (FaultPopulation,plate_bonds,plate_nominal,
    fault_candidate,pilot_fault_candidates,PILOT_BONDS_12)
from singularity.thermal_parameters import (Polynomial as P,ParametricFaultFamily,
    ThermalParameterDomain,panel_parameter_map,parametric_fault_sample,
    certify_family_separation,verify_family_certificate)
from singularity.reset_policies import (reset_family_from_diagnostics,minimum_reset_policy,
    verify_reset_policy,replay_policy)
from singularity.history_experiments import (HistoryWorld,HistoryBelief,HistoryModel,
    history_policy_search,verify_history_policy,latent_box_world,affine_advance,affine_condition)


def encode(obj):
    if isinstance(obj,F): return f'{obj.numerator}/{obj.denominator}'
    if is_dataclass(obj): return encode(asdict(obj))
    if isinstance(obj,dict):return {str(k):encode(v) for k,v in obj.items()}
    if isinstance(obj,(tuple,list)):return [encode(x) for x in obj]
    return obj


def source_provenance():
    path=ROOT/'scripts'/'thermal_diagnostics.py'
    spec=importlib.util.spec_from_file_location('_nx_thermal_source',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.verify_source_fixture()


def flux(grid,state,amplitude,blocked=(),*,k=F(1,8),loss=F(1,100),gain=1,severity=1):
    """Independent undirected neighbour-flux evolution; no sparse model import."""
    middle=(grid//2-1,grid//2);heat={r*grid+c for r in middle for c in middle}
    output=[(1-loss)*x+gain*amplitude*F(int(i in heat),len(heat)) for i,x in enumerate(state)]
    blocked=set(blocked)
    for r in range(grid):
        for c in range(grid):
            a=r*grid+c
            for rr,cc in ((r+1,c),(r,c+1)):
                if rr<grid and cc<grid:
                    b=rr*grid+cc;conductance=k*(1-severity) if (a,b) in blocked else k
                    transfer=conductance*(state[b]-state[a]);output[a]+=transfer;output[b]-=transfer
    return tuple(output)


def joint_receipt():
    models=build_plate_candidates(4)[4:6]
    protocols=(((2,0),2),((2,0),3))
    diagnostic=protocol_pool(models,protocols,initial_radius=0,sensor_noise=F(1,10000))
    family=affine_protocol_family(models,protocols,persistent_offset=F(1,10),
                                  sensor_noise=F(1,10000),initial_radius=0,
                                  costs=diagnostic.pool.costs)
    assert all(family.centers[c][e]==diagnostic.pool.readings[e][c] for c in range(2) for e in range(2))
    result=minimum_joint_panel(family)
    for panel,certificates in result['checked_panels']:
        assert all(verify_joint_certificate(project_panel(family,panel),cert) for cert in certificates)
    # Independent algebra: common offset cancels exactly under left-minus-right.
    contrast=(F(1),F(-1));differences=tuple(family.centers[c][0]-family.centers[c][1] for c in range(2))
    radii=(F(1,10)+F(1,10000),)*2
    box_overlap=all(abs(family.centers[0][i]-family.centers[1][i])<=2*radii[i] for i in range(2))
    assert box_overlap and result['status']=='optimal' and result['panel']==(0,1)
    # Replacing a persistent source by fresh offsets destroys the certificate.
    independent=tuple(tuple((F(1,10) if e==j else 0) for j in range(2))+
                      tuple((F(1,10000) if e==j else 0) for j in range(2)) for e in range(2))
    false_model=JointObservationFamily(family.candidate_ids,family.experiment_ids,family.centers,
                                      (independent,independent),family.costs)
    restored=joint_pair_certificate(false_model,0,1)
    assert restored['kind']=='overlap' and verify_joint_certificate(false_model,restored)
    return {'schema':'singularity.nx02-thermal/1','source':source_provenance(),
        'family':family,'minimum_panel':result,'box_outer_approximation':'impossible-in-declared-pool',
        'independent_offset_model':restored,'algebraic_contrast':contrast,
        'center_contrasts':differences,'contrast_support_per_world':F(1,5000),
        'reset_semantics':'independent-zero-initial-state;persistent-output-offset',
        'calibration_status':'synthetic-assumptions-not-measured'}


def fault_receipt():
    population,models=pilot_fault_candidates(12)
    masks=tuple(population.iterate_masks())
    assert len(masks)==79 and all(population.rank(m)==i and population.unrank(i)==m for i,m in enumerate(masks))
    prefix_counts=tuple((prefix,population.count(prefix)) for prefix in product((0,1),repeat=3))
    assert sum(c for p,c in prefix_counts)==79
    # Explicit short, complete finite pool, selected before inspecting responses.
    protocols=tuple((word,sensor) for word in ((2,0),(2,)+(0,)*11) for sensor in range(4))
    diagnostic=protocol_pool(models,protocols,sensor_noise=0,initial_radius=0)
    boxes=from_diagnostic_pool(diagnostic);result=minimum_candidate_box_panel(boxes,max_nodes=100000)
    noisy=protocol_pool(models,protocols,sensor_noise=F(1,10000),initial_radius=0)
    noisy_result=minimum_candidate_box_panel(from_diagnostic_pool(noisy),max_nodes=100000)
    spot=[]
    for i in (0,1,20,78):
        blocked=tuple(bond for bond,bit in zip(PILOT_BONDS_12,masks[i]) if bit)
        for e in (0,5):
            word,sensor=protocols[e];state=(F(0),)*144
            for amplitude in word:state=flux(12,state,amplitude,blocked)
            reading=sum(c*x for c,x in zip(models[i].sensors[sensor],state))
            assert reading==diagnostic.pool.readings[e][i]
            spot.append((i,e,reading))
    classes={}
    for c,mask in enumerate(masks):
        signature=tuple(row[c] for row in diagnostic.pool.readings)
        classes.setdefault(signature,[]).append(mask)
    decoded=[]
    for c in range(79):
        observed=tuple(row[c] for row in diagnostic.pool.readings)
        survivors=candidate_box_consistent(boxes,tuple(range(8)),observed)
        assert c in survivors
        decoded.append(tuple(diagnostic.candidate_ids[i] for i in survivors))
    full=FaultPopulation(plate_bonds(12),max_faults=2)
    assert full.count()==34981
    tiny=FaultPopulation(plate_bonds(2),max_faults=2)
    return {'schema':'singularity.nx03-diagnosis/1','source':source_provenance(),
        'population':population.manifest(),'original_masks':masks,'candidate_ids':diagnostic.candidate_ids,
        'prefix_partition':prefix_counts,'nominal_all_bond_count':264,'full_up_to_two_count':full.count(),
        'tiny_physical_count':tiny.count(),'protocols':protocols,'costs':diagnostic.pool.costs,
        'readings':diagnostic.pool.readings,'error_bounds':diagnostic.error_bounds,
        'optimizer':asdict(result),'uncoverable_original_pairs':uncoverable_pairs(boxes),
        'positive_noise_comparison':{'sensor_noise':F(1,10000),'optimizer':asdict(noisy_result)},
        'behavioral_classes':tuple(tuple(group) for group in classes.values()),
        'all79_original_center_decodings':tuple(decoded),
        'independent_flux_spots':tuple(spot),'target':'exact-original-mask',
        'scope':'complete79-masks-and-declared8-protocols;not-all-future-identifiability'}


def severity_receipt():
    g,a=P.variable(2,0),P.variable(2,1)
    nominal=ParametricFaultFamily('nominal',((1,2),(0,0)),(g,(F(1,2)-a*F(1,4))*g))
    fault=ParametricFaultFamily('fault',((1,2),(F(1,2),1)),nominal.observations)
    scalar=certify_family_separation(nominal,fault,noise=F(1,100),contrasts=((F(1,2),-1),),max_cells=127)
    assert scalar['status']=='separated' and verify_family_certificate(nominal,fault,scalar)
    final_nom=ParametricFaultFamily('nominal-final',nominal.domain,(nominal.observations[1],))
    final_fault=ParametricFaultFamily('fault-final',fault.domain,(fault.observations[1],))
    overlap=certify_family_separation(final_nom,final_fault,
                                    overlap_witnesses=(((1,0),(F(4,3),F(1,2))),))
    assert verify_family_certificate(final_nom,final_fault,overlap)
    bonds=((4,5),(6,7),(1,5),(5,6))
    # Central sensor is intentionally symmetric: reflected faults must overlap.
    protocols=(((2,),1),((2,0),1),((2,0,0),1),((2,0,0,0),1))
    maps=tuple(panel_parameter_map(4,bond,protocols) for bond in bonds)
    bands=((F(0),F(0)),(F(1,2),F(3,4)),(F(3,4),F(1)))
    domains=tuple(ThermalParameterDomain(((F(1,8),F(1,8)),(F(1,100),F(1,100)),(1,1),band))
                  for band in bands)
    records=[]
    for band,domain in zip(bands,domains):
        families=tuple(ParametricFaultFamily(str(bond),domain.bounds,m) for bond,m in zip(bonds,maps))
        pairs=[]
        for i,j in combinations(range(4),2):
            cert=certify_family_separation(families[i],families[j],noise=F(1,100000),max_cells=127)
            if cert['status']!='unresolved':assert verify_family_certificate(families[i],families[j],cert)
            pairs.append((i,j,cert))
        records.append({'severity_band':band,'domain':domain,'pairs':tuple(pairs)})
    samples=[]
    for i,bond in enumerate(bonds):
        for alpha in (0,F(1,2),1):
            params=(F(1,8),F(1,100),1,alpha)
            model=parametric_fault_sample(4,bond,params)
            values=tuple(p.evaluate(params) for p in maps[i])
            assert values==tuple(simulate_protocol(model,*protocol) for protocol in protocols)
            # Explicit source-independent flux oracle for every retained sample.
            for e,(word,sensor) in enumerate(protocols):
                state=(F(0),)*16
                for amplitude in word:state=flux(4,state,amplitude,(bond,),severity=alpha)
                assert values[e]==sum(c*x for c,x in zip(model.sensors[sensor],state))
            samples.append((bond,alpha,values))
    # Reflection is a complete domain obstruction under the chosen symmetric sensor.
    assert all(record['pairs'][0][2]['status']=='overlap' for record in records)
    return {'schema':'singularity.nx04-severity/1','source':source_provenance(),
        'scalar_joint_certificate':scalar,'scalar_final_overlap':overlap,
        'declared_bonds':bonds,'protocols':protocols,'maps':maps,'bands':tuple(records),
        'independent_flux_samples':tuple(samples),'noise_per_reading':F(1,100000),
        'semantics':'fixed-within-world;independent-calibration-between-hypotheses',
        'interpretation':'synthetic-location-severity-pilot;unresolved-cells-are-not-separated'}


def adaptive_receipt():
    # Literally unchanged source six-candidate,112-protocol,original uncertainty pool.
    candidates=build_plate_candidates(12)
    protocols=default_protocols()
    diagnostic=protocol_pool(candidates,protocols,initial_radius=F(1,100),sensor_noise=F(1,100))
    assert diagnostic.pool.size==112
    family=reset_family_from_diagnostics(diagnostic)
    adaptive=minimum_reset_policy(family);assert verify_reset_policy(family,adaptive)
    static=minimum_candidate_box_panel(from_diagnostic_pool(diagnostic))
    # A bounded original-mask subset uses the identical second comparison contract.
    population,all_models=pilot_fault_candidates(4)
    selected=all_models[:8]
    small_protocols=tuple((word,s) for word in ((2,),(2,0),(2,2,0)) for s in range(4))
    small_diagnostic=protocol_pool(selected,small_protocols,initial_radius=0,sensor_noise=F(1,100000))
    small_family=reset_family_from_diagnostics(small_diagnostic)
    small_adaptive=minimum_reset_policy(small_family);assert verify_reset_policy(small_family,small_adaptive)
    small_static=minimum_candidate_box_panel(from_diagnostic_pool(small_diagnostic))
    return {'schema':'singularity.nx05-adaptive-thermal/1','source':source_provenance(),
        'six_candidate_contract':{'protocols':protocols,'candidate_ids':diagnostic.candidate_ids,
            'initial_radius':F(1,100),'sensor_noise':F(1,100),'static':asdict(static),'adaptive':adaptive},
        'fault_subset_contract':{'original_masks':tuple(population.unrank(i) for i in range(8)),
            'candidate_ids':small_diagnostic.candidate_ids,'protocols':small_protocols,
            'initial_radius':0,'sensor_noise':F(1,100000),'static':asdict(small_static),
            'adaptive':small_adaptive},'objective':'worst-case-positive-exact-cost',
        'uncertainty_semantics':'independent-adversarial-per-reset'}


def history_receipt():
    source=build_plate_candidates(4)
    candidates=(source[0],source[4],source[5])
    blocked=((),((4,5),),((6,7),))
    transitions={};measurements={'left':{},'right':{}};initial=[];trajectory=[]
    for c,model in enumerate(candidates):
        zero=(F(0),)*16;initial.append(HistoryWorld(model.identifier,model.identifier,(0,zero)))
        frontier={(0,zero)}
        for time in range(3):
            new=set()
            for t,state in frontier:
                for channel,sensor in (('left',2),('right',3)):
                    measurements[channel][model.identifier,(t,state)]=model.observe(state,sensor)
                if time<2:
                    for amplitude in (0,2):
                        evolved=model.step(state,amplitude)
                        assert evolved==flux(4,state,amplitude,blocked[c])
                        target=(time+1,evolved)
                        transitions[model.identifier,(t,state),amplitude]=(target,);new.add(target)
            frontier=new
        state=zero;values=[]
        for amplitude in (2,0,0):
            state=model.step(state,amplitude)
            assert state==flux(4,zero,2,blocked[c]) if len(values)==0 else True
            values.append((model.observe(state,2),model.observe(state,3)))
        trajectory.append(tuple(values))
    model=HistoryModel(tuple(initial),(0,2),transitions,measurements,(1,2),(2,2),
                       ('initial-reset-cost=2;no-further-reset-actions',))
    policy=history_policy_search(model,horizon=4,max_states=20000)
    assert verify_history_policy(model,policy)
    # Every static word admitted by the same at-most-two-control language.
    protocols=tuple((word,sensor) for length in (1,2) for word in product((0,2),repeat=length)
                    for sensor in (2,3))
    diagnostic=protocol_pool(candidates,protocols,initial_radius=0,sensor_noise=0)
    static=minimum_candidate_box_panel(from_diagnostic_pool(diagnostic))
    # Shared-gain affine transcript certificates, independent parameters per world.
    affine=[]
    from singularity.thermal_diagnostics import AffineCandidate
    for a in (F(1,2),F(3,4)):
        dynamics=AffineCandidate(str(a),1,((0,0,a),),(F(3,2),),((1,),))
        world=latent_box_world(str(a),str(a),(0,),((0,),),('persistent:gain',))
        heated=affine_advance(world,dynamics,1,heater_generators=((F(1,2),),))
        first,first_cert=affine_condition(heated,(1,),F(6,5))
        cooled=affine_advance(first,dynamics,0)
        second,second_cert=affine_condition(cooled,(1,),F(3,5))
        affine.append({'slope':a,'first':first_cert,'second':second_cert,'survives':second is not None})
    assert tuple(a['survives'] for a in affine)==(True,False)
    slopes=(F(1,2),F(3,4));noise=F(1,100)
    robust_family=JointObservationFamily(('half','three_quarters'),('pulse_read','cool_read'),
        tuple((F(3,2),a*F(3,2)) for a in slopes),
        tuple(((F(1,2),noise,0),(a*F(1,2),0,noise)) for a in slopes),(1,1))
    robust=joint_pair_certificate(robust_family,0,1)
    final_only=joint_pair_certificate(project_panel(robust_family,(1,)),0,1)
    assert robust['kind']=='separating_contrast' and verify_joint_certificate(robust_family,robust)
    assert final_only['kind']=='overlap'
    return {'schema':'singularity.nx06-history-thermal/1','source':source_provenance(),
        'candidates':tuple(c.identifier for c in candidates),'word':(2,0,0),
        'intermediate_left_right_readings':tuple(trajectory),'history_policy':policy,
        'initial_reset_cost':2,'history_total_cost':None if policy['cost'] is None else policy['cost']+2,
        'separately_reset_panel':asdict(static),'shared_fixed_six_reading_cost':18,
        'separate_fixed_six_reading_cost':42,'initial_domain':'exact-zero',
        'sensor_domain':'exact-zero-error-for-policy;independent-bounded-errors-supported-by-polytope-core',
        'all_control_transitions_independently_flux_checked':True,'affine_shared_gain':tuple(affine),
        'shared_gain_robust_joint_certificate':robust,'shared_gain_final_only_overlap':final_only,
        'shared_gain_sensor_error':noise,
        'scope':'complete-two-control-thermal-language;bounded-horizon4-policy-optimum'}


BUILDERS={'joint_thermal':joint_receipt,'fault_population_diagnostics':fault_receipt,
          'thermal_severity':severity_receipt,'adaptive_thermal':adaptive_receipt,
          'history_thermal':history_receipt}


def main(name=None):
    parser=argparse.ArgumentParser(description=__doc__)
    if name is None:parser.add_argument('name',choices=BUILDERS)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();name=name or args.name
    raw=BUILDERS[name]()
    fractions=[]
    def collect(value):
        if isinstance(value,F):fractions.append(value)
        elif is_dataclass(value):collect(asdict(value))
        elif isinstance(value,dict):
            for x in value.values():collect(x)
        elif isinstance(value,(tuple,list)):
            for x in value:collect(x)
    collect(raw)
    raw['arithmetic']={'fraction_occurrences':len(fractions),
        'maximum_numerator_bits':max((abs(x.numerator).bit_length() for x in fractions),default=0),
        'maximum_denominator_bits':max((x.denominator.bit_length() for x in fractions),default=0)}
    raw['work_limits']={'joint_elimination_rows':20000,'joint_panel_subsets':4096,
        'fault_completion_states':100000,'parameter_cells_per_pair':127,
        'reset_beliefs':100000,'history_states':20000}
    result=encode(raw);path=ROOT/'results'/f'{name}.json'
    payload=json.dumps(result,sort_keys=True,indent=2)+'\n'
    if args.check:
        if not path.exists() or path.read_text()!=payload:raise SystemExit(f'{name}: retained receipt differs')
        print(f'{name}: exact retained receipt replay passed')
    else:
        path.write_text(payload);print(f'{name}: wrote {path.relative_to(ROOT)}')


if __name__=='__main__':main()
