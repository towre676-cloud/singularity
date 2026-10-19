#!/usr/bin/env python3
"""Replay NX07/NX09/NX10-B-C/NX11/NX12 finite decision acceptance evidence."""
import argparse,json,sys,hashlib
from dataclasses import asdict,is_dataclass,replace
from fractions import Fraction as Q
from pathlib import Path
from itertools import product
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from singularity.language_design import *
from singularity.protocol_population import *
from singularity.fidelity_design import *
from singularity.remote_queries import *
from singularity.horizon_design import *
from singularity.thermal_diagnostics import build_plate_candidates,simulate_protocol
from singularity.fault_population import pilot_fault_candidates


def portable(x):
    if isinstance(x,Q):return [x.numerator,x.denominator]
    if is_dataclass(x):return portable(asdict(x))
    if isinstance(x,dict):return {str(k):portable(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [portable(v) for v in x]
    return x

def digest(x):return hashlib.sha256(json.dumps(portable(x),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def flux(candidate,word,sensor):
    """Independent conservative neighbour-flux update, not candidate.step."""
    n=candidate.dimension;x=[Q(0)]*n
    rows=[{} for _ in range(n)]
    for i,j,v in candidate.entries:rows[i][j]=v
    row_sums=[sum(row.values(),Q(0)) for row in rows]
    for u in word:
        x=[row_sums[i]*x[i]+sum(k*(x[j]-x[i]) for j,k in rows[i].items() if j!=i)+candidate.heater[i]*u for i in range(n)]
    return sum(v*w for v,w in zip(candidate.sensors[sensor],x))

def nx07():
    caps=tuple(Capability(s,c) for s,c in (('s1',2),('s2',2),('s3',5)))
    exps=(RequiredExperiment('e1',('s1',),(0,1,0),(Q(1,10),)*3,1),RequiredExperiment('e2',('s2',),(0,0,1),(Q(1,10),)*3,1),RequiredExperiment('e3',('s3',),(0,1,2),(Q(1,10),)*3,1))
    tiny=LanguageDesignProblem(caps,exps,('v1','v2','v3'),('v1','v2','v3'))
    tinyfront=enumerate_installation_frontier(tiny)
    assert tinyfront[0]['total_cost']==6 and len(tinyfront[0]['optima'])==2 and tinyfront[1]['total_cost']==7
    candidates=build_plate_candidates(4);problem=thermal_capability_catalogue(candidates,horizons=(1,2,3,4))
    front=enumerate_installation_frontier(problem,max_panel_nodes=2000000)
    assert all(verify_installation_result(replace(problem,deployments=n),r,max_panel_nodes=2000000) for n,r in zip((1,2,10,100),front))
    # Symmetry is an exact permutation intertwining, so covers every input word.
    grid=4;permutation=tuple((i//grid)*grid+(grid-1-i%grid) for i in range(16));a,b=candidates[4:6]
    transformed=tuple(sorted((permutation[i],permutation[j],v) for i,j,v in a.entries))
    assert transformed==b.entries and all(b.heater[permutation[i]]==a.heater[i] for i in range(16))
    assert all(a.sensors[s][i]==b.sensors[s][permutation[i]] for s in (0,1) for i in range(16))
    from singularity.thermal_diagnostics import AffineCandidate
    asymmetric_six=tuple(Q(int(i==16//2)) for i in range(16))
    for experiment in problem.experiments:
        models=candidates if 'asymmetric_heater' not in experiment.requires else tuple(AffineCandidate(c.identifier,c.dimension,c.entries,asymmetric_six,c.sensors) for c in candidates)
        assert all(flux(c,experiment.protocol,int(experiment.requires[0].split(':')[1]))==reading for c,reading in zip(models,experiment.readings))
    witness=next(e for e in problem.experiments if 'asymmetric_heater' not in e.requires and e.readings[4]!=e.readings[5])
    assert all(flux(c,witness.protocol,int(witness.requires[0].split(':')[1]))==reading for c,reading in zip(candidates,witness.readings))
    pop,expanded=pilot_fault_candidates(grid=4);large=thermal_capability_catalogue(expanded,horizons=(6,))
    original=minimum_installation_panel(large,max_panel_nodes=2000000)
    labels=tuple(tuple(e.readings[i] for e in large.experiments) for i in range(len(expanded)))
    quotient=replace(large,target_labels=labels)
    expandedfront=enumerate_installation_frontier(quotient,max_panel_nodes=2000000)
    assert all(verify_installation_result(replace(quotient,deployments=n),r,max_panel_nodes=2000000) for n,r in zip((1,2,10,100),expandedfront))
    from singularity.thermal_diagnostics import AffineCandidate
    asymmetric=tuple(Q(int(i==16//2)) for i in range(16))
    for e in large.experiments:
        models=expanded if 'asymmetric_heater' not in e.requires else tuple(AffineCandidate(c.identifier,c.dimension,c.entries,asymmetric,c.sensors) for c in expanded)
        assert all(flux(c,e.protocol,int(e.requires[0].split(':')[1]))==r for c,r in zip(models,e.readings))
    indistinguishable=[(expanded[i].identifier,expanded[j].identifier) for i in range(len(expanded)) for j in range(i+1,len(expanded)) if labels[i]==labels[j]]
    return {'units':['NX07-A','NX07-B','NX07-C'],'tiny_problem':tiny,'tiny':tinyfront,'thermal_catalogue':problem,'thermal_six':front,'old_language_intertwining':True,'new_language_witness':witness,'expanded_catalogue':large,'expanded_original_target':original,'expanded_observable_target_frontier':expandedfront,'expanded_response_classes':len(set(labels)),'expanded_unseparated_original_pairs':indistinguishable,'fault_manifest':pop.manifest(),'fault_id_reconstruction':[(c.identifier,pop.unrank(i)) for i,c in enumerate(expanded)],'scope':'79 original fault identities retained; identity target legitimately unseparable in this finite catalogue. Pareto fronts for maximal observable quotient are labelled separately.'}

def nx09():
    candidates=build_plate_candidates(4);checks=[]
    for c in (candidates[0],candidates[2]):
        for word in product((0,1),repeat=2):
            for rank in (1,2):
                for arithmetic in ('exact_rational','binary64_exact_dot'):
                    o=certify_dynacomp_option(c,2,word,rank,arithmetic_protocol=arithmetic)
                    assert replay_dynacomp_option(o)
                    truth=flux(c,word,2)
                    assert abs(o.reading.center-truth)<=o.reading.computational_radius
                    checks.append({'candidate':c.identifier,'word':word,'rank':o.rank,'arithmetic':arithmetic,'full_output':truth,'center':o.reading.center,'bound':o.reading.computational_radius,'source':o.bound_receipt['source_id'],'upstream':o.bound_receipt['upstream']})
    menu=[]
    for h in (2,3):
        groups=[]
        for c in (candidates[0],candidates[2]):
            group=[]
            for rank in (1,2):
                for arithmetic in ('exact_rational','binary64_exact_dot'):
                    group.append(certify_dynacomp_option(c,2,(1,)*h,rank,arithmetic_protocol=arithmetic,physical_radius=Q(1,1000),setup_cost=rank,run_cost=rank))
            groups.append(tuple(group))
        menu.append(FidelityExperiment('step:'+str(h),Q(h+2),tuple(groups),(1,)*h))
    ids=(candidates[0].identifier,candidates[2].identifier)
    plans=tuple(minimum_fidelity_panel(menu,ids,deployments=n) for n in (1,2,10,100))
    assert all(replay_fidelity_result(menu,ids,p,deployments=n) for n,p in zip((1,2,10,100),plans))
    # Full exact reference is separately evaluated, not a low-rank bound relabel.
    full=[]
    for h in (2,3):
        groups=tuple((certify_dynacomp_option(c,2,(1,)*h,16,physical_radius=Q(1,1000),setup_cost=16,run_cost=16,force_full=True),) for c in (candidates[0],candidates[2]))
        full.append(FidelityExperiment('step:'+str(h),Q(h+2),groups,(1,)*h))
    reference=minimum_fidelity_panel(full,ids)
    uniform_rank=[]
    for rank in (1,2):
        restricted=tuple(FidelityExperiment(e.identifier,e.physical_cost,tuple(tuple(o for o in group if o.rank==rank) for group in e.options),e.protocol) for e in menu)
        uniform_rank.append(minimum_fidelity_panel(restricted,ids))
    # One nondegenerate input box is replayed at every vertex independently.
    adapter=bundled_adapter();u=adapter.module('uniform');m=adapter.module('machine');r=adapter.module('rational');binary=adapter.module('binary64')
    c=candidates[0];spec={'n':c.dimension,'entries':[[i,j,str(v)] for i,j,v in c.entries],'B':[[str(v)] for v in c.heater],'C':[[str(v) for v in c.sensors[2]]]}
    model=u.SparseLinearModel.from_spec(spec);zero=(Q(0),)*c.dimension;box_checks=[]
    for rank in (1,2):
        packet=u.uniform_enrichment(model,zero,zero,((Q(1,2),),)*2,Q(0),input_centers=((Q(1,2),),)*2,max_rank=rank,strategy='prefix');assert u.replay_uniform(packet)
        E,G,H,D=map(r.matrix,(packet[k] for k in ('E','G','H','D')))
        execution=m.certify_execution(E,G,H,D,zero,zero,((Q(1,2),),)*2,Q(1),((Q(1,2),),)*2);assert m.replay_execution(execution)
        runtime=m.Binary64Runtime(execution)
        for word in product((0,1),repeat=2):
            z=r.mv(E,zero)
            for a in word:z=r.addv(r.mv(G,z),r.mv(H,(Q(a),)))
            reduced=r.mv(D,z)[0];truth=flux(c,word,2);bits=runtime.simulate_bits(tuple(binary.round_bits(v) for v in zero),tuple((binary.round_bits(Q(a)),) for a in word));machine=binary.exact(bits[-1][0])
            bound=Q(packet['certificate']['output_bounds'][-1][0])+Q(execution['output_error_upper'][-1][0])
            assert abs(machine-truth)<=bound
            box_checks.append({'requested_rank':rank,'actual_rank':packet['rank'],'word':word,'full':truth,'reduced':reduced,'binary64':machine,'combined_bound':bound})
    sample=menu[0].options[0][0]
    return {'units':['NX09-A','NX09-B','NX09-C'],'exhaustive_fixed_inputs_checked':len(checks),'enclosure_checks':checks,'nondegenerate_box_vertices':box_checks,'plans':plans,'complete_evaluator_menu':tuple(menu),'full_exact_everywhere':reference,'same_rank_references':uniform_rank,'sample_complete_upstream_bound':sample.bound_receipt,'cost_model':'declared rational setup/run/physical accounting units, recomputation per diagnosis; not wall-clock forecasts','break_even':'For plans with setup S and per-query Q, compare S1+NQ1 and S2+NQ2 exactly; plans above retain all terms.'}

def nx10():
    def scalar(name,a,b):return step_system(LinearCandidate(name,((a,),),((b,),),((1,),)),(1,),0)
    a,b=scalar('a',Q(1,2),Q(1,2)),scalar('b',Q(1,3),Q(2,3));e=RadiusEnvelope(sensor=Q(1,100))
    finite=maximum_margin_horizon(a,b,e,e,max_prefix=32,epsilon=Q(1,100000));late=minimum_step_horizon(a,b,e,e,IndexCost(1,1),min_index=6,max_prefix=32)
    a,b=scalar('a',Q(1,2),1),scalar('b',Q(1,3),Q(2,3))
    unattained=maximum_margin_horizon(a,b,e,e,max_prefix=64,epsilon=Q(1,1000))
    assert finite.status=='finite_optimum_certified' and late.status=='never_separating_after' and unattained.status=='supremum_bracket'
    records=[finite.record,late.record,unattained.record];thermal=[];candidates=build_plate_candidates(4)
    for ca,cb,sensor in ((0,2,2),(0,3,1),(4,5,0),(4,5,2)):
        for block in ((1,0),(1,1,0)):
            systems=tuple(block_system(LinearCandidate.from_affine(candidates[i]),tuple((u,) for u in block),0,sensor) for i in (ca,cb))
            # Symmetric nonnegative stencil contracts in Euclidean norm by row sum;
            # its exact P=I acceptance is checked, not inferred from stability alone.
            metrics=tuple(certify_metric(s.A,P=tuple(tuple(Q(int(i==j)) for j in range(s.dimension)) for i in range(s.dimension)),rho=Q(99,100)**len(block)) for s in systems)
            result=minimum_step_horizon(*systems,RadiusEnvelope(sensor=Q(1,1000)),RadiusEnvelope(sensor=Q(1,1000)),IndexCost(1,len(block)),max_prefix=24,metric_a=metrics[0],metric_b=metrics[1],tail_mode='separate')
            for k in range(9):
                for s,i in zip(systems,(ca,cb)):assert s.output(s.states(k+1)[k])==flux(candidates[i],block*k,sensor)
            assert replay_horizon_result(result.record)
            thermal.append({'pair':(candidates[ca].identifier,candidates[cb].identifier),'sensor':sensor,'block':block,'decision':result.record,'physical_prefix_flux_checked':9,'effort':'two exact16-state P=I contraction checks and at most25 prefix indices; inconclusive tails retained'})
    assert all(replay_horizon_result(r) for r in records)
    return {'units':['NX10-B','NX10-C'],'analytic_decisions':records,'thermal_fixed_blocks':thermal,'not_claimed':'arbitrary switching, multitime panels, calibrated physical time or attained supremum'}

def nx11():
    adapter=bundled_adapter();q=SequenceQuery('two-mode','two-mode-rational-source')
    response=compile_response(q,((Q(1,2),0),(0,Q(1,3))),(1,1),(1,-1),adapter)
    for n in range(33):assert query_index(response,n,10000,adapter).value==Q(1,2)**n-Q(1,3)**n
    exact=query_index(response,128,10000,adapter);receipt=response_receipt(response,exact);assert replay_remote_receipt(receipt,adapter,10000)
    modular=query_index(response,10**100,adapter=adapter,modulus=101);assert replay_remote_receipt(response_receipt(response,modular),adapter)
    refused=False
    try:query_index(response,10**100,adapter=adapter)
    except ValueError:refused=True
    assert refused
    candidates=build_plate_candidates(4);blocks=[]
    for c in (candidates[0],candidates[2]):
        compiled=compile_repeated_block(c,(1,0),2,1,adapter)
        for k in range(33):assert query_index(compiled,k,10000,adapter).value==flux(c,(1,0)*k+(1,),2)
        blocks.append({'candidate':c.identifier,'dimension':compiled.dimension,'index_map':compiled.index_map,'source_binding':compiled.source_binding,'gf':compiled.sequence_packet})
    from singularity.panels import minimum_cost_panel
    small=[]
    from singularity.thermal_diagnostics import AffineCandidate
    for name,a in (('half',Q(1,2)),('third',Q(1,3))):small.append(compile_constant_input(AffineCandidate(name,1,((0,0,a),),(Q(1),),((Q(1),),)),0,adapter=adapter))
    pool=remote_panel_pool(small,tuple(range(1,17)),adapter=adapter)
    panel=minimum_cost_panel(pool)
    return {'units':['NX11-A','NX11-B','NX11-C'],'two_mode_receipt':receipt,'zero_and_pair_cancellation_verified_in_tests':True,'huge_rational_refused':refused,'huge_modular_receipt':response_receipt(response,modular),'physical_repeated_blocks':blocks,'finite_experiment_selector':{'indices':list(range(1,17)),'status':'optimal' if panel.feasible else 'unseparable','cost':str(panel.cost)},'accounting_example':{'compile_setup':100,'query_cost':1,'direct_cost':10,'one_query_compiled_total':101,'one_query_direct_total':10,'first_strict_break_even_query_count':12,'meaning':'declared exact accounting example, not measured runtime'},'resource_scope':'binary powering stages logarithmic; rational output bit size still grows with index'}

def nx12():
    alphabet=ProtocolAlphabet(('0','2'),(0,2),(1,2),((0,),(2,)));grammar=DeterministicProtocolGrammar(('q',),'q',('q',),(('q','0','q'),('q','2','q')));sensors=(TerminalSensor('corner',1),TerminalSensor('center',1))
    tiny=ProtocolPopulation(alphabet,grammar,ProtocolResources(100,(4,),3,1,1),sensors);bounded=ProtocolPopulation(alphabet,grammar,ProtocolResources(4,(4,),3,1,1),sensors)
    assert tiny.count()==22 and bounded.count()==6
    cert=tiny.completion_certificate();assert verify_completion_certificate(tiny,cert)
    candidates=build_plate_candidates(4);physical=ProtocolPopulation(ProtocolAlphabet(('off','on'),(0,1),(1,1),((0,),(1,))),DeterministicProtocolGrammar(('q',),'q',('q',),(('q','off','q'),('q','on','q'))),ProtocolResources(7,(3,),4,2,1),(TerminalSensor('corner',1),TerminalSensor('center',1),TerminalSensor('left',1),TerminalSensor('right',1)))
    protocols=tuple(physical.iter_protocols(4096));checks=0
    for p in protocols:
        sensor=('corner','center','left','right').index(p.sensor)
        for c in candidates:assert simulate_protocol(c,physical.amplitudes(p),sensor)==flux(c,physical.amplitudes(p),sensor);checks+=1
    # Cheapest robust single experiment for the named nominal/heater-half pair.
    pair=(candidates[0],candidates[2]);read=lambda p:tuple(simulate_protocol(c,physical.amplitudes(p),('corner','center','left','right').index(p.sensor)) for c in pair)
    decision=cheapest_robust_protocol(physical,read,tuple(c.identifier for c in pair),radii=Q(1,1000))
    assert decision['status']=='optimal'
    # Full six-model panel: compare exact backend with an independent subset
    # oracle on the complete short population (<=12 rows after zero masks).
    from singularity.panels import minimum_cost_panel,exhaustive_minimum_panel
    short=ProtocolPopulation(ProtocolAlphabet(('off','on'),(0,1),(1,1),((0,),(1,))),DeterministicProtocolGrammar(('q',),'q',('q',),(('q','off','q'),('q','on','q'))),ProtocolResources(4,(1,),2,1,1),(TerminalSensor('center',1),))
    pool=short.compile_pool(pair,sensor_indices={'center':1});panel=minimum_cost_panel(pool);oracle=exhaustive_minimum_panel(pool,max_subsets=2**16)
    assert panel.feasible==oracle.feasible and panel.cost==oracle.cost
    default_words={(Q(1),)*h for h in (1,2,3,4)}|{(Q(1),)+(Q(0),)*(h-1) for h in (1,2,3,4)}|{tuple(Q(int(i%2==0)) for i in range(h)) for h in (1,2,3,4)}
    omitted=[p for p in protocols if physical.amplitudes(p) not in default_words]
    baseline=tuple(p for p in protocols if physical.amplitudes(p) in default_words)
    baseline_feasible=tuple((physical.cost(p),physical.rank(p)) for p in baseline if abs(read(p)[0]-read(p)[1])>Q(2,1000))
    baseline_single=min((cost for cost,rank in baseline_feasible),default=None)
    from singularity.panels import reading_pool
    baseline_pool=reading_pool(tuple(physical.cost(p) for p in baseline),tuple(read(p) for p in baseline),labels=tuple(p.identifier for p in baseline),candidates=2)
    complete_pair_pool=physical.compile_pool(pair)
    complete_panel=minimum_cost_panel(complete_pair_pool,epsilon=Q(1,1000));baseline_panel=minimum_cost_panel(baseline_pool,epsilon=Q(1,1000))
    assert decision['cost']==complete_panel.cost
    comparison={'same_pair':tuple(c.identifier for c in pair),'same_noise_radius':Q(1,1000),'same_grammar_resources_and_costs':True,'complete_members':physical.count(),'matching_baseline_members':len(baseline),'complete_single_optimum':decision['cost'],'baseline_single_optimum':baseline_single,'complete_panel_cost':complete_panel.cost,'baseline_panel_cost':baseline_panel.cost,'complete_status':'optimal' if complete_panel.feasible else 'unseparable','baseline_status':'optimal' if baseline_panel.feasible else 'unseparable'}
    return {'units':['NX12-A','NX12-B','NX12-C'],'tiny_count':22,'budget4_count':6,'all_tiny_rank_roundtrips':[(i,tiny.unrank(i)) for i in range(22)],'completion_certificate':cert,'physical_population_count':physical.count(),'physical_completion_certificate':physical.completion_certificate(),'physical_source_models':candidates,'physical_sensor_channels':{'corner':0,'center':1,'left':2,'right':3},'physical_source_sha256':digest(candidates),'physical_flux_checks':checks,'single_experiment_decision':decision,'fair_baseline_comparison':comparison,'short_complete_panel':{'count':short.count(),'status':'optimal' if panel.feasible else 'unseparable','cost':str(panel.cost),'independent_exhaustive_agreement':True},'omitted_by_step_pulse_alternating_subset':len(omitted),'omitted_examples':omitted[:8],'scope':'complete declared grammar/resource language; comparison step/pulse/alternating restricted to matching horizons, not a claim about the untouched112-experiment baseline'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--track',choices=('NX07','NX09','NX10','NX11','NX12','all'),default='all');args=parser.parse_args()
    functions={'NX07':nx07,'NX09':nx09,'NX10':nx10,'NX11':nx11,'NX12':nx12};out={}
    for name,fn in functions.items():
        if args.track!='all' and args.track!=name:continue
        payload=portable({'schema':'singularity.nx-decision-recovery/1','track':name,'evidence':fn(),'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/singularity').glob('*.py') if p.name in {'language_design.py','fidelity_design.py','horizon_design.py','remote_queries.py','protocol_population.py','dynacomp_adapter.py'}}})
        path=ROOT/'results'/('nx_'+name[2:]+'_decision_recovery.json')
        if args.check:
            if not path.exists() or json.loads(path.read_text())!=payload:raise SystemExit(str(path)+' stale')
        else:path.write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')
        print(name,'replayed' if args.check else 'retained',flush=True);out[name]=payload
    return out
if __name__=='__main__':main()
