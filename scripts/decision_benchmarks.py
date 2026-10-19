#!/usr/bin/env python3
"""Actual bounded cold/setup/warm timings; no performance threshold gates correctness."""
import argparse,hashlib,json,platform,statistics,sys,time
from fractions import Fraction as Q
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from singularity.dynacomp_adapter import bundled_adapter
from singularity.fidelity_design import certify_dynacomp_option
from singularity.thermal_diagnostics import build_plate_candidates,simulate_protocol
from singularity.remote_queries import SequenceQuery,compile_response,query_index
REPORT=ROOT/'results/nx_decision_benchmarks.json'

def median_ns(fn,loops=20,trials=5):
    values=[]
    for _ in range(trials):
        t=time.perf_counter_ns()
        for _ in range(loops):fn()
        values.append(Q(time.perf_counter_ns()-t,loops))
    return int(statistics.median(values))

def break_even(setup,query,direct):
    return None if query>=direct else setup//(direct-query)+1

def run():
    adapter=bundled_adapter();r=adapter.module('rational');m=adapter.module('machine');b=adapter.module('binary64');candidates=(build_plate_candidates(4)[0],build_plate_candidates(4)[2]);word=(1,1);rows=[]
    direct=lambda:tuple(simulate_protocol(c,word,2) for c in candidates)
    direct_ns=median_ns(direct)
    for rank in (1,2):
        for arithmetic in ('exact_rational','binary64_exact_dot'):
            def setup():return tuple(certify_dynacomp_option(c,2,word,rank,arithmetic_protocol=arithmetic) for c in candidates)
            setup_ns=median_ns(setup,loops=1,trials=3);options=setup()
            prepared=[];prepare_start=time.perf_counter_ns()
            for o in options:
                packet=o.bound_receipt['reduction'];E,G,H,D=map(r.matrix,(packet[k] for k in ('E','G','H','D')))
                runtime=m.Binary64Runtime(o.bound_receipt['execution']) if arithmetic=='binary64_exact_dot' else None
                prepared.append((E,G,H,D,runtime))
            prepare_ns=time.perf_counter_ns()-prepare_start
            def query():
                outputs=[]
                for c,(E,G,H,D,runtime) in zip(candidates,prepared):
                    if runtime is not None:
                        bits=runtime.simulate_bits((b.round_bits(Q(0)),)*c.dimension,tuple((b.round_bits(Q(a)),) for a in word));outputs.append(b.exact(bits[-1][0]))
                    else:
                        z=r.mv(E,(Q(0),)*c.dimension)
                        for a in word:z=r.addv(r.mv(G,z),r.mv(H,(Q(a),)))
                        outputs.append(r.mv(D,z)[0])
                return tuple(outputs)
            query_ns=median_ns(query);values=query();truth=direct()
            assert all(abs(v-t)<=o.reading.computational_radius for v,t,o in zip(values,truth,options))
            total_setup=setup_ns+prepare_ns
            rows.append({'requested_rank':rank,'actual_ranks':[o.rank for o in options],'arithmetic':arithmetic,'certification_setup_median_ns':setup_ns,'executor_preparation_ns':prepare_ns,'total_setup_ns':total_setup,'cold_one_query_total_ns':total_setup+query_ns,'warm_pair_query_median_ns':query_ns,'full_exact_pair_query_median_ns':direct_ns,'measured_first_strict_break_even_queries':break_even(total_setup,query_ns,direct_ns),'setup_bindings':[o.bound_receipt['setup_binding'] for o in options]})
    def gf_setup():return compile_response(SequenceQuery('two-mode','rational-two-mode'),((Q(1,2),0),(0,Q(1,3))),(1,1),(1,-1),adapter)
    gf_setup_ns=median_ns(gf_setup,1,3);compiled=gf_setup();gf_query_ns=median_ns(lambda:query_index(compiled,128,10000,adapter),5,3);value=query_index(compiled,128,10000,adapter)
    def direct_sequence(n):
        a,b=Q(1),Q(1)
        for _ in range(n):a*=Q(1,2);b*=Q(1,3)
        return a-b
    direct_remote_ns=median_ns(lambda:direct_sequence(128),5,3)
    direct_one_ns=median_ns(lambda:direct_sequence(1),20,3)
    warm_one_ns=median_ns(lambda:query_index(compiled,1,10000,adapter),5,3)
    return {'schema':'singularity.nx-decision-benchmark/1','timing_semantics':'perf_counter_ns medians; observed on this machine; informational and never an exact cost law','environment':{'python':platform.python_version(),'platform':platform.platform(),'upstream':adapter.binding()},'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/singularity/fidelity_design.py',ROOT/'src/singularity/remote_queries.py',ROOT/'src/singularity/dynacomp_adapter.py')},'NX09':{'fixed_word':word,'sensor':2,'candidate_ids':[c.identifier for c in candidates],'rows':rows,'declared_cost_break_even':{'reduced_setup':2,'reduced_per_diagnosis':6,'full_setup':32,'full_per_diagnosis':36,'reduced_strictly_cheaper_for_all_positive_N':True,'first_strict_break_even_N':1}},'NX11':{'gf_compile_median_ns':gf_setup_ns,'cold_compile_plus_index128_ns':gf_setup_ns+gf_query_ns,'warm_index128_median_ns':gf_query_ns,'direct_step_index128_median_ns':direct_remote_ns,'measured_first_strict_break_even_index128_queries':break_even(gf_setup_ns,gf_query_ns,direct_remote_ns),'one_query_index1':{'compiled_cold_ns':gf_setup_ns+warm_one_ns,'direct_ns':direct_one_ns},'output_bits':value.cost_metadata['output_bits'],'stages_upper':value.cost_metadata['powering_stages_upper'],'declared_cost_example':{'setup':100,'compiled_query':1,'direct_query':10,'break_even_N':12}}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    if args.check:
        p=json.loads(REPORT.read_text());assert p['schema']=='singularity.nx-decision-benchmark/1'
        for name,digest in p['source_sha256'].items():assert hashlib.sha256((ROOT/'src/singularity'/name).read_bytes()).hexdigest()==digest
        for row in p['NX09']['rows']:
            assert row['measured_first_strict_break_even_queries']==break_even(row['total_setup_ns'],row['warm_pair_query_median_ns'],row['full_exact_pair_query_median_ns'])
            assert row['cold_one_query_total_ns']==row['total_setup_ns']+row['warm_pair_query_median_ns']
        print('retained timing arithmetic/source bindings replay; no speed threshold asserted')
    else:REPORT.write_text(json.dumps(run(),indent=2,sort_keys=True)+'\n');print(REPORT)
if __name__=='__main__':main()
