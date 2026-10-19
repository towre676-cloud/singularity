#!/usr/bin/env python3
"""Retain/check all 264 source-derived plate bonds and exact fault transport."""
import argparse,hashlib,json,time,sys
from pathlib import Path
from fractions import Fraction as Q
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from singularity.fault_transport import *
from singularity.thermal_diagnostics import build_plate_candidates

def enc(x):
    if isinstance(x,Q):return [x.numerator,x.denominator]
    if isinstance(x,tuple):return [enc(y) for y in x]
    if isinstance(x,list):return [enc(y) for y in x]
    if isinstance(x,dict):return {k:enc(v) for k,v in x.items()}
    return x

def run(horizon=6):
    a=build_plate_candidates()[0];bonds=tuple((i,j) for i,j,v in a.entries if i<j and v>0)
    start=time.perf_counter();cache=NominalTransferCache(a,horizon);setup=time.perf_counter()-start
    retained=[];transport=direct=0.;maxbits=0
    for u,v in bonds:
        fault=BondFault(u,v,Q(1,8));start=time.perf_counter();out=bond_transfer(cache,fault);transport+=time.perf_counter()-start
        candidate=apply_faults(a,(fault,),f'bond:{u}:{v}');start=time.perf_counter();state=a.heater;oracle=[]
        for t in range(horizon+1):
            oracle.append(tuple(candidate.observe(state,s) for s in range(4)));state=candidate.step(state,0)
        direct+=time.perf_counter()-start
        assert out==tuple(tuple(row[s] for row in oracle) for s in range(4))
        maxbits=max(maxbits,max(x.numerator.bit_length()+x.denominator.bit_length() for row in out for x in row))
        retained.append({'candidate_id':candidate.identifier,'bond':[u,v],'removed':[1,8],
                         'impulse_sha256':hashlib.sha256(json.dumps(enc(out),separators=(',',':')).encode()).hexdigest()})
    # Symmetry-invariant sensors cannot distinguish a bond and its reflection.
    p=lambda i:(i//12)*12+11-i%12
    lookup={tuple(row['bond']):row for row in retained};symmetric=0
    for u,v in bonds:
        lhs=bond_transfer(cache,BondFault(u,v,Q(1,8)));rhs=bond_transfer(cache,BondFault(p(u),p(v),Q(1,8)))
        assert lhs[:2]==rhs[:2];symmetric+=1
    assert len(bonds)==264 and len(lookup)==264
    cells=sum(len(p)*len(p[0]) for p,_ in cache._columns.values())
    seen=set()
    def size(obj):
        key=id(obj)
        if key in seen:return 0
        seen.add(key);answer=sys.getsizeof(obj)
        if isinstance(obj,dict):answer+=sum(size(k)+size(v) for k,v in obj.items())
        elif isinstance(obj,(tuple,list)):answer+=sum(size(v) for v in obj)
        elif isinstance(obj,Q):answer+=size(obj.numerator)+size(obj.denominator)
        elif hasattr(obj,'__dict__'):answer+=size(obj.__dict__)
        return answer
    memory_bytes=size(cache)
    factors=bond_transfer_factors(cache,BondFault(*bonds[0],Q(1,8)))
    for s,num in enumerate(factors['correction_numerators']):
        correction=tuple(bond_transfer(cache,BondFault(*bonds[0],Q(1,8)))[s][t]-cache.nominal[1][s][t] for t in range(horizon+1))
        for t in range(horizon+1):assert sum(factors['denominator'][j]*correction[t-j] for j in range(t+1))==num[t]
    source=ROOT/'applications/thermal_diagnostics/source_fixture.json'
    stable={'schema':'singularity.bond-fault-transport/1','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'dimension':144,'horizon':horizon,'sensors':4,'bond_count':264,'candidates':retained,
            'reflected_invariant_checks':symmetric,'coefficient_max_bits':maxbits,'stored_bond_vector_cells':cells,
            'formula':'A_fault=A0+delta*b*b.T; finite formal Woodbury; scalar unit denominator',
            'uncertainty':'unchanged original model; transfer supplies exact readings only; no transported uncertainty claim'}
    # Setup-inclusive cost is reported, never an assumed speed improvement.
    one_direct=direct/len(bonds);one_query=transport/len(bonds)
    timing={'setup_seconds':setup,'all_bonds_transport_seconds':transport,'all_bonds_direct_seconds':direct,
            'owned_cache_recursive_bytes':memory_bytes,'memory_measurement':'recursive sys.getsizeof with shared identities counted once, not process RSS','first_population_seconds':setup+transport,'break_even_queries':None if one_query>=one_direct else setup/(one_direct-one_query),
            'memory_contract':'144*(H+1) nominal cells plus 264 lazy bond columns; exact numerator/denominator bits reported',
            'machine_scope':'wall time on this host; setup included; direct candidate construction excluded from both core query timings'}
    return stable,timing

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();data,timing=run();path=ROOT/'results/fault_transport.json'
    if args.check:
        saved=json.loads(path.read_text());assert saved['receipt']==data;print('fault transport: 264 original bonds, exact replay passed')
    else:path.write_text(json.dumps({'receipt':data,'benchmark':timing},indent=2)+'\n');print(json.dumps(timing,indent=2))
if __name__=='__main__':main()
