#!/usr/bin/env python3
import argparse,json,sys,time
from itertools import combinations
from fractions import Fraction as Q
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from singularity.phase_probes import *
from singularity.heights import local_coefficients

def enc(x):
    if isinstance(x,Q):return [x.numerator,x.denominator]
    if isinstance(x,dict):return {str(k):enc(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [enc(v) for v in x]
    return x

def run():
    rows=[]
    for n in range(1,4):
        edges=tuple(combinations(range(n),2))
        for mask in range(1<<len(edges)):
            g=Graph(n,tuple(e for i,e in enumerate(edges) if mask>>i&1));R=2;M=energy_degree_bound(g,R)+1
            a=phase_table(g,R,M);b=phase_table(g,R,M,'residue');hist=recover_energy_histograms(a)
            assert a['samples']==b['samples'];assert hist==tuple(local_coefficients(g,R))
            rows.append({'graph_id':f'n{n}:mask{mask}','bound':a['bound'],'M':M,'field_degree':CyclotomicRing(M).degree,
                         'phase_samples':M,'histograms':hist,'profile_mass':tuple(sum(h.values()) for h in hist)})
    g=Graph(3,((0,1),));a=phase_table(g,2,6);b=phase_table(g,2,6,'residue');assert a['samples']==b['samples']
    edge=Graph(2,((0,1),));alias=recover_energy_histograms(phase_table(edge,2,4),allow_aliasing=True)
    good=recover_energy_histograms(phase_table(edge,2,5));assert good[2]=={0:1,4:2} and alias[2]=={0:3}
    graphs=(Graph(3),Graph(3,((0,1),)),Graph(3,((0,1),(1,2))),Graph(3,((0,1),(0,2),(1,2))))
    tables=tuple(phase_table(g,1,5) for g in graphs);panel=phase_subset_identification(('empty','edge','path','triangle'),tables,(1,2,3,4,5))
    ring=CyclotomicRing(5);sparse=sparse_histogram_recovery(5,(0,4),((1,ring.add(ring.one,ring.scale(ring.phase(4),2))),))
    return enc({'schema':'singularity.phase-probe-census/1','graphs':rows,'composite_order6_nonprimitive_samples_verified':True,
                'single_edge':{'order5':good[2],'order4_alias':alias[2]},'finite_candidate_panel':panel,'support_conditioned':sparse,
                'complexity':'direct C(R+n,n) profiles per phase; residue M^n per phase; complete M-phase transform in phi(M)-dimensional field',
                'rational_alternative':'D+1 distinct rational evaluations also determine a degree-D polynomial by invertible Vandermonde; no efficiency superiority claimed'})

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();data=run();path=ROOT/'results/phase_probes.json'
    if a.check:assert json.loads(path.read_text())==data;print('phase probes: 11 graphs, two routes, aliasing and optimal panel passed')
    else:
        path.write_text(json.dumps(data,indent=2)+'\n')
        g=Graph(2,((0,1),));start=time.perf_counter();symbolic=local_coefficients(g,2)[2];symbolic_time=time.perf_counter()-start
        start=time.perf_counter();table=phase_table(g,2,5);phase_samples_time=time.perf_counter()-start
        start=time.perf_counter();recovered=recover_energy_histograms(table)[2];transform_time=time.perf_counter()-start
        start=time.perf_counter()
        samples=tuple((Q(1,i+2),sum((Q(1,i+2)**((h-(2-h))**2) for h in range(3)),Q())) for i in range(5))
        rational=rational_histogram_interpolation(samples,4);rational_time=time.perf_counter()-start
        assert rational==recovered==symbolic
        bench={'graph':'single edge','R':2,'degree_bound':4,'phase_order':5,'field_degree':4,
               'direct_symbolic_seconds':symbolic_time,'phase_samples_seconds':phase_samples_time,
               'inverse_transform_seconds':transform_time,'rational_samples_and_interpolation_seconds':rational_time,
               'sampling_contract':'all original volume-two profiles replayed per rational node; phase route includes all volumes through two',
               'max_rational_sample_bits':max(q.numerator.bit_length()+q.denominator.bit_length()+y.numerator.bit_length()+y.denominator.bit_length() for q,y in samples),
               'claim':'machine-specific cost comparison, no universal speed superiority'}
        (ROOT/'results/phase_probes_benchmark.json').write_text(json.dumps(bench,indent=2)+'\n')
        print('wrote',path)
if __name__=='__main__':main()
