#!/usr/bin/env python3
"""Bounded deterministic NX14/15/18/19/20 receipt builders.

Run individual thin script with --check to verify retained evidence. Runtime
is deliberately not serialized, so receipts reproduce across machines.
"""
import argparse
import json
import sys
from collections import Counter
from fractions import Fraction as F
from itertools import combinations,product
from math import comb
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def portable(v):
    if isinstance(v,F):return [v.numerator,v.denominator]
    if isinstance(v,dict):return {str(k):portable(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [portable(x) for x in v]
    return v


def parameter_receipt():
    from singularity.parametric import PolynomialOperatorSystem,symbolic_boundary_system
    from singularity.parameter_receipts import parameter_module_receipt,replay_parameter_module_receipt,guarded_specialization
    from singularity.observability import observable_closure
    a={0:-F(1,2),1:1};false=PolynomialOperatorSystem(2,[[[0,1],[0,0]]],[[1,0],[0,a]])
    true=PolynomialOperatorSystem(2,[[[1,0],[0,2]]],[[1,a]])
    rational=PolynomialOperatorSystem(2,[[[1,0],[0,2]]],[[1,1]])
    fixtures={'false_exception':parameter_module_receipt(false),'true_exception':parameter_module_receipt(true),
              'rational_guard':parameter_module_receipt(rational,denominator={0:-1,1:2})}
    for r in fixtures.values():assert replay_parameter_module_receipt(r)
    coordinates,graph=symbolic_boundary_system(5)
    attempt=parameter_module_receipt(graph,limits={'max_dimension':22,'max_degree':371,'max_coefficient_bits':10000,'max_steps':5,'max_minors':1000,'seconds':2})
    samples=[{'q':q,'rank':observable_closure(graph.specialize(q)).rank,'scope':'exact specialization only'} for q in (F(1,3),F(1,2))]
    for q in (F(1,4),F(3,4)):assert observable_closure(guarded_specialization(fixtures['rational_guard'],q)).rank==2
    return {'track':'NX14','units':['NX14-A','NX14-B','NX14-C'],'fixtures':fixtures,'graph_R5':{'dimension':len(coordinates),'attempt':attempt,'specializations':samples},
            'boundary':'No R5 parameter-wide rank or factor theorem claimed; symbolic attempt stopped at declared preflight dimension.'}


def realizability_receipt():
    from singularity.realizable_interfaces import frontier_vectors,tree_family,dominating_family,complete_bounded_exclusion,threshold_dominating_exclusion,charge_relaxation_contains
    from singularity.graph import Graph
    from singularity.charges import charge_interface
    for mask in range(64):
        possible=tuple(combinations(range(4),2));g=Graph(4,[e for i,e in enumerate(possible) if mask>>i&1])
        assert charge_relaxation_contains(charge_interface(g,(0,1),3),2)
    return {'track':'NX15','units':['NX15-A','NX15-B','NX15-C'],'formal_frontiers':frontier_vectors(),
            'families':{'trees_n_le_5':complete_bounded_exclusion(tree_family(5)),'dominating_interiors_le_4':complete_bounded_exclusion(dominating_family(4))},
            'charge_filter_tiny_graphs':64,'structural_exclusions':[threshold_dominating_exclusion(11),threshold_dominating_exclusion(38)],
            'constructor_completeness':'trees checked independently by all (n-1)-edge subsets and Cayley counts; dominating interiors enumerate every labeled adjacency bit mask',
            'boundary':'No unrestricted graph realization, full-series collision or arbitrary-graph completeness asserted.'}


def conditioning_receipt():
    from singularity.recovery_metrics import (reconstruction_map,box_amplification,compare_recovery_designs,optimize_target,verify_target_certificate,select_target_design,vandermonde,rational_size,vandermonde_uniform_bound,interface_reconstruction_data)
    from singularity.graph import Graph
    from singularity.charges import dominating_block,dominating_sequence,closure_operator,charge_interface,charge_chart,chart_matrix,chart_observations
    from singularity.contexts import finite_difference_probe_set,finite_difference_budget,symmetric_context,symmetric_probe_set,tau
    from singularity.terminals import glue_graphs,kernel_by_enumeration
    from singularity.heights import weak_compositions
    q=F(1,2);R=3;H=Graph(2,[(0,1)]);block,terminals=dominating_block(H)
    A=tuple(sum(c*q**e for e,c in row.items()) for row in dominating_sequence(H,R));designs=[];checks=0
    def direct(g):
        return tuple(sum(q**g.energy(h) for h in weak_compositions(v,g.n)) for v in range(R+1))
    for name,probes in (('edge_free_finite_difference',[(d,0,c) for d,c in finite_difference_probe_set(R)]),('weighted_edge_restoration',[(d,w,0) for d,w in symmetric_probe_set(R,1)])):
        rows=[];costs=[]
        for d,w,c in probes:
            context,cts=symmetric_context(d,terminal_edge=bool(w),common=c);T=closure_operator(context,cts,H.n,R,q)
            # These small weighted fixtures have edge weights only zero/one,
            # so each is an actual simple glued graph, not a contraction-only test.
            g,_=glue_graphs(block,terminals,context,cts)
            predicted=tuple(sum(T[i][j]*A[j] for j in range(R+1)) for i in range(R+1))
            assert predicted==direct(g);checks+=1
            rows.extend(T);costs.extend([1+2*d+c+w]*(R+1))
        method='finite_difference' if name.startswith('edge_free') else 'weighted'
        generic=interface_reconstruction_data(method,R,q)
        target_inverse=[generic['R'][generic['coordinates'].index(((0,0),j))] for j in range(R+1)]
        designs.append({'name':name,'A':rows,'left_inverse':target_inverse,'noise':[1]*len(rows),'costs':costs,'volume_budget':finite_difference_budget(R) if name.startswith('edge_free') else R,'target':[0,0,0,1]})
        # Compare the generic exact recovery implementation on the actual
        # independently counted glued values, not merely a family inverse.
        from singularity.contexts import recover_by_finite_differences,recover_symmetrized_kernel
        values={p:[sum(row[j]*A[j] for j in range(R+1)) for row in rows[i*(R+1):(i+1)*(R+1)]] for i,p in enumerate(generic['probes'])}
        recovered=(recover_by_finite_differences(values,R,q) if method=='finite_difference' else recover_symmetrized_kernel(values,R,q))
        assert tuple(recovered[(0,0)])==A
    interface=charge_interface(block,terminals,R);chart=charge_chart(interface,R)
    kernel=kernel_by_enumeration(block,terminals,chart['budget']);readings=chart_observations(kernel,chart,q)
    rows=[]
    for j in range(R+1):
        J=chart_matrix(interface,chart,j,q);assert len(J)==1 and readings[j][0]==J[0][0]*A[j]
        rows.append([J[0][0] if i==j else F(0) for i in range(R+1)])
    designs.append({'name':'ordered_charge_chart','A':rows,'noise':[1]*len(rows),'costs':[1]*len(rows),'volume_budget':chart['budget'],'target':[0,0,0,1]})
    comparison=compare_recovery_designs(designs)
    for d in comparison:
        C=d['raw_reconstruction'];assert tuple(sum(C[i][k]*sum(d['A'][k][j]*A[j] for j in range(R+1)) for k in range(len(C[i]))) for i in range(R+1))==A
    tiny=reconstruction_map([[1,1],[1,F(17,16)]])
    lp=optimize_target([[1,0],[0,1],[1,1]],[1,0],[1,1,F(1,4)]);assert verify_target_certificate([[1,0],[0,1],[1,1]],[1,0],[1,1,F(1,4)],lp)
    menu=[{'name':'cheap','A':[[1]],'noise':[1],'costs':[1]},{'name':'clear','A':[[100]],'noise':[1],'costs':[3]},{'name':'costly','A':[[200]],'noise':[1],'costs':[7]}]
    circles=[]
    for name,nodes in [('delayed_tau',[tau(o,q) for o in ((0,5),(3,4))]),('weighted_y',[q**((s-t)**2) for s,t in ((0,5),(3,4))])]:
        V=vandermonde(nodes);I=reconstruction_map(V);circles.append({'name':name,'nodes':nodes,'inverse_amplification':box_amplification(I,[1,1]),'forward_bits':rational_size(V),'inverse_bits':rational_size(I),'scope':'conditional isolated collision-circle moments, not raw whole-graph sensor bounds'})
    return {'track':'NX18','units':['NX18-A','NX18-B','NX18-C'],'tiny_box':{'inverse':tiny,'sharp_amplification':box_amplification(tiny,[1,1]),'vertex_witnesses':[[1,-1],[-1,1]]},
            'common_target':{'name':'dominating A_H coefficients 0..3, H=K2','values':A,'parameter':q,'all_other_family_structure_known':True},
            'comparison':comparison,'direct_glued_graph_checks':checks,'collision_moments':circles,
            'finite_difference_preprocessing_l1':[2**j for j in range(5)],'target_LP':lp,'bounded_menu':select_target_design(menu,[1],F(1,50)),
            'uniform_interval':{'q':[F(1,4),F(1,2)],'nodes':'1 and 1+q','M':F(3,2),'gamma':F(1,4),'bound':vandermonde_uniform_bound(2,F(3,2),F(1,4)),
                                'proof':'1<=z_i<=3/2 and gap=q>=1/4 imply the exact Lagrange coefficient bound (1+M)/gamma=10'},
            'boundary':'The real-block comparison is R=3, before any circle collision. R=7 circle data are separate conditional moments. No delayed-budget optimality or all-budget precision bound claimed.'}


def integer_receipt():
    from singularity.integer_quotients import (integer_image_certificate,verify_integer_image_certificate,image_contains,integer_fibre,bounded_fibre_population,pushforward_population,operator_lattice_certificate,apply_lattice_update)
    corpus=0;states=0
    for m,n in ((1,3),(2,2),(3,2)):
        for entries in product((-1,0,1),repeat=m*n):
            A=[entries[i*n:(i+1)*n] for i in range(m)];c=integer_image_certificate(A);assert verify_integer_image_certificate(c);corpus+=1
            for x in product((-1,0,1),repeat=n):
                y=tuple(sum(a*b for a,b in zip(row,x)) for row in A);assert image_contains(c,y);states+=1
    binary=integer_image_certificate([[2,2]]);p=bounded_fibre_population(binary,[2],[(0,1)]*2)
    scale=integer_image_certificate([[F(1,2),F(1,2)]]);op=operator_lattice_certificate(scale,[[0,1],[1,0]])
    transition_checks=0
    for x in product(range(-2,3),repeat=2):
        y=(sum(x),)
        for _ in range(4):y=apply_lattice_update(scale,op,y);assert y==(sum(x),);transition_checks+=1
    return {'track':'NX19','units':['NX19-A','NX19-B','NX19-C'],'matrix_corpus':corpus,'independent_original_states':states,
            'binary':{'certificate':binary,'y1_in_image':image_contains(binary,[1]),'y2_fibre':integer_fibre(binary,[2]),'original_states':[p.unrank(i) for i in range(p.count())],
                      'pushforward':pushforward_population(binary,[(0,1)]*2)},'denominator_clearing':scale,'swap_operator':op,'short_transition_checks':transition_checks,
            'saturation_regression':integer_fibre(integer_image_certificate([[2,1,1]]),[0]),
            'boundary':'Image membership is necessary arithmetic compatibility, never sufficient graph realizability. Fibres need explicit finite original-coordinate bounds.'}


def arithmetic_receipt():
    from singularity.arithmetic_automata import QuadraticUnit,ResidueOrbitSystem,replay_arithmetic_receipt
    u=QuadraticUnit(2,3,2);s=ResidueOrbitSystem(u,5,{'positive':(1,0),'negative':(4,0),'same_residue_distinct_original':(6,0)})
    assert replay_arithmetic_receipt(s.receipt())
    signed=ResidueOrbitSystem(u,5,{'positive':(1,0)},actions={'unit':u,'conjugation':'conjugation'},signed_states=True)
    digits='9876543210'*600;rem=0
    for c in digits:rem=(10*rem+int(c))%6
    remote=s.remote_residue('positive',digits);assert remote==s.cycle('positive')['cycle'][rem]
    blind=ResidueOrbitSystem(u,5,{'positive':(1,0),'negative':(4,0)},observations=('norm',))
    restricted=ResidueOrbitSystem(u,4,{'seed':(1,0)})
    norm_class=[(x,y) for x in range(4) for y in range(4) if (x*x-2*y*y)%4==1]
    assert blind.cheapest_witness('positive','negative') is None
    return {'track':'NX20','units':['NX20-A','NX20-B','NX20-C'],'system':s.receipt(),'cycle':s.cycle('positive'),'behavior':s.behavioral_classes(),
            'cheapest_witness':s.cheapest_witness('positive','negative'),'forever_equivalent':blind.behavioral_classes(),
            'remote':{'decimal_digits':len(digits),'pattern':'9876543210 repeated 600 times','index_mod_cycle':rem,'residue':remote,'method':'decimal-stream binary matrix powering plus independent cycle remainder'},
            'norm_congruence_counterexample':{'modulus':4,'norm_congruence_states':norm_class,'chosen_seed_generated_states':restricted.states,'unlicensed_residue':(1,2)},
            'signed_noncommuting':signed.receipt(),'conjugation_witness':{'unit_then_J':(3,3),'J_then_unit':(3,2),'verified':signed._action('conjugation',u.apply((1,0)))!=(tuple(z%5 for z in u.apply((1,0))))},
            'boundary':'All-future equivalence concerns these finite seed images, legal actions and sensors. No global Pell seed completeness is asserted.'}

BUILDERS={'parameter_module_receipts':parameter_receipt,'realizable_interfaces':realizability_receipt,'recovery_metrics':conditioning_receipt,'integer_quotients':integer_receipt,'arithmetic_automata':arithmetic_receipt}

def run(name):
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    result=portable(BUILDERS[name]());text=json.dumps(result,indent=2,sort_keys=True)+'\n';path=ROOT/'results'/f'{name}.json'
    if args.check:
        if path.read_text()!=text:raise SystemExit(f'retained receipt differs: {path}')
        print(f'{name}: retained exact receipt matches')
    else:path.write_text(text);print(f'wrote {path}')

if __name__=='__main__':
    raise SystemExit('use one of the five individual receipt scripts')
