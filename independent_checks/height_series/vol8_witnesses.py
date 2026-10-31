#!/usr/bin/env python3
"""Exact connected cubic pairs first separated by volume eight.

The discovery search uses the inherited PR7 graph pool. Replay is fully
independent of that pool: integer height compositions are enumerated from
the retained edge lists, with a second support-based enumeration at8.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from math import comb
from vol7_witnesses import coefficient, coefficient_support, check_cubic, pool_records, polynomial_difference

HERE=Path(__file__).resolve().parent


def motif_data(n,A,B):
    from vol8_lib import count_patterns,degrees_of
    counts=[count_patterns(n,E,8) for E in (A,B)]
    delta={f'{k}:{m}':counts[1].get((k,m),0)-counts[0].get((k,m),0)
           for k,m in sorted(set(counts[0])|set(counts[1]))
           if min(degrees_of(m,k))>=2 and counts[1].get((k,m),0)!=counts[0].get((k,m),0)}
    sums=defaultdict(int)
    for key,c in delta.items():
        k,m=map(int,key.split(':'))
        if k==8:sums[str(m.bit_count())]+=c
    return {'delta_leafless_core_counts':delta,'delta_eighth_core_edge_sums':dict(sorted(sums.items()))}


def small_expected():
    out=defaultdict(int)
    for i in range(9):
        for j,c in enumerate((1,3,3,1)):
            out[8+2*i+2*j]-=((-1)**i)*comb(8,i)*c
    return {str(e):c for e,c in sorted(out.items()) if c}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--search',action='store_true');parser.add_argument('--replay',action='store_true');parser.add_argument('--max-n',type=int,default=14);parser.add_argument('--max-pairs',type=int,default=1)
    args=parser.parse_args();target=HERE/'vol8_witnesses.json'
    if args.replay:
        data=json.loads(target.read_text())
        for p in data['pairs']:
            n=p['n'];A=p['A']['edges'];B=p['B']['edges'];check_cubic(n,A);check_cubic(n,B)
            for r in range(1,8):assert coefficient(n,A,r)==coefficient(n,B,r)
            delta=polynomial_difference(coefficient(n,A,8),coefficient(n,B,8))
            assert delta==p['delta_L8'] and delta
            assert motif_data(n,A,B)=={key:p[key] for key in ('delta_leafless_core_counts','delta_eighth_core_edge_sums')}
            for E in (A,B):assert coefficient(n,E,8)==coefficient_support(n,E,8)
        print('Replayed',len(data['pairs']),'exact connected through-seven pairs; independent enumeration at8.');return
    rows=list(pool_records());groups=defaultdict(list)
    if not args.search:
        rows=[g for g in rows if g['n']==12 and g['name'] in {'n12_g1','n12_g8'}]
    for g in rows:
        if g['n']>args.max_n:continue
        low=tuple(int(g['N'].get(str(i),0)) for i in range(52))
        key=(g['n'],low,tuple(sorted((int(e),str(c)) for e,c in g['L6'].items())))
        groups[key].append(g)
    pairs=[];tested7=0;tested8=0
    for sig,group in sorted(groups.items(),key=lambda kv:(kv[0][0],-len(kv[1]))):
        if len(group)<2:continue
        by7={}
        for g in group:
            seven=coefficient(g['n'],g['edges'],7);tested7+=1
            key=tuple(seven.items())
            if key not in by7:
                by7[key]=[g,None];continue
            old,eight=by7[key]
            if eight is None:
                eight=coefficient(old['n'],old['edges'],8);tested8+=1;by7[key][1]=eight
            now=coefficient(g['n'],g['edges'],8);tested8+=1
            if now==eight:continue
            n=g['n'];A=old['edges'];B=g['edges']
            for r in range(1,8):assert coefficient(n,A,r)==coefficient(n,B,r)
            for E in (A,B):assert coefficient(n,E,8)==coefficient_support(n,E,8)
            pairs.append({'n':n,'A':{'name':old['name'],'edges':A},'B':{'name':g['name'],'edges':B},'agree_through':7,'delta_L8':polynomial_difference(eight,now),
                          'factorization':('-q^8 (1-q^2)^8 (1+q^2)^3 = -kappa^8 (1+q^2)^3' if polynomial_difference(eight,now)==small_expected() else None),
                          **motif_data(n,A,B)})
            print('PAIR',len(pairs),n,old['name'],g['name'],pairs[-1]['delta_L8'],flush=True)
            if len(pairs)>=args.max_pairs:break
        if len(pairs)>=args.max_pairs:break
    data={'dependency_head':'facb450','definition':'delta = B - A; integer q-polynomial coefficients','coefficients7_enumerated':tested7,'coefficients8_enumerated':tested8,'pairs':pairs}
    target.write_text(json.dumps(data,indent=2)+'\n');print('Wrote',target,'pairs',len(pairs),'evaluations',tested7,tested8)
if __name__=='__main__':main()
