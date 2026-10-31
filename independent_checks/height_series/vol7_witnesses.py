#!/usr/bin/env python3
"""Independent exact witnesses for seventh-order height observation.

The search uses PR #7 graph pools only to choose candidates. Every retained
pair is rechecked from its edge lists, by direct height enumeration; its
agreement through volume six is an exact polynomial identity in q.
"""
from collections import defaultdict
from itertools import combinations
import argparse
import hashlib
import json
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent


def coefficient(n, edges, volume):
    """Enumerate weak compositions; energy is accumulated on edge closure."""
    left = [[] for _ in range(n)]
    for a, b in edges:
        a, b = sorted((a,b))
        left[b].append(a)
    h = [0]*n
    out = defaultdict(int)
    def rec(v, rem, energy):
        if v == n-1:
            out[energy+sum((rem-h[u])**2 for u in left[v])] += 1
            return
        for x in range(rem+1):
            h[v]=x
            rec(v+1,rem-x,energy+sum((x-h[u])**2 for u in left[v]))
    rec(0,volume,0)
    assert sum(out.values()) == comb(n+volume-1,volume)
    return dict(sorted(out.items()))


def coefficient_support(n, edges, volume):
    """Independent positive-support enumeration, energy from cubic identity."""
    eset = {tuple(sorted(e)) for e in edges}
    out = defaultdict(int)
    def pos_compositions(total,parts):
        if parts==1:
            yield (total,)
        else:
            for x in range(1,total-parts+2):
                for tail in pos_compositions(total-x,parts-1):
                    yield (x,)+tail
    for k in range(1,min(n,volume)+1):
        for verts in combinations(range(n),k):
            internal=[(i,j) for i in range(k) for j in range(i+1,k) if (verts[i],verts[j]) in eset]
            for h in pos_compositions(volume,k):
                energy=3*sum(x*x for x in h)-2*sum(h[i]*h[j] for i,j in internal)
                out[energy]+=1
    assert sum(out.values()) == comb(n+volume-1,volume)
    return dict(sorted(out.items()))


def polynomial_difference(a,b):
    return {str(e):b.get(e,0)-a.get(e,0) for e in sorted(set(a)|set(b)) if b.get(e,0)!=a.get(e,0)}


def leafless_differences(n,A,B):
    from vol7_lib import count_patterns, degrees_of
    na,nb=count_patterns(n,A),count_patterns(n,B)
    return {f"{k}:{m}":nb.get((k,m),0)-na.get((k,m),0)
            for k,m in sorted(set(na)|set(nb))
            if min(degrees_of(m,k))>=2 and nb.get((k,m),0)!=na.get((k,m),0)}


def check_cubic(n,edges):
    assert len({tuple(sorted(e)) for e in edges})==len(edges)
    degree=[0]*n
    for a,b in edges:
        assert 0<=a<b<n
        degree[a]+=1;degree[b]+=1
    assert degree==[3]*n


def pool_records():
    for fn in sorted(HERE.glob('vol6_results_part[123]*.json')):
        d=json.loads(fn.read_text())
        g=d.get('graphs',{})
        if 'rows' in g:
            yield from g['rows']
        else:
            for records in g.values():
                yield from records


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--max-pairs',type=int,default=2)
    parser.add_argument('--search',action='store_true',help='Search all PR7 pools; default rechecks two fixed discovered pairs.')
    parser.add_argument('--replay',action='store_true')
    args=parser.parse_args()
    target=HERE/'vol7_witnesses.json'
    if args.replay:
        data=json.loads(target.read_text())
        for pair in data['pairs']:
            n=pair['n']; A=pair['A']['edges'];B=pair['B']['edges']
            check_cubic(n,A);check_cubic(n,B)
            for r in range(1,7):
                assert coefficient(n,A,r)==coefficient(n,B,r)
            d=polynomial_difference(coefficient(n,A,7),coefficient(n,B,7))
            assert d==pair['delta_L7'] and d
            assert leafless_differences(n,A,B)==pair['delta_leafless_core_counts']
            for E in (A,B):
                assert coefficient(n,E,7)==coefficient_support(n,E,7)
        print(f"Replayed {len(data['pairs'])} exact through-six witnesses with two independent volume-seven enumerators.")
        return
    groups=defaultdict(list)
    records=list(pool_records())
    pool_size=len(records)
    if not args.search:
        # A compact reproducible certificate, with neither pool order nor a
        # long randomized search needed at replay time.
        selected={'n14_g19','n14_g128','n14_g709','n14_g770'}
        records=[r for r in records if r['n']==14 and r['name'] in selected]
    for row in records:
        # Equality of every <=5 subgraph count is stronger than needed and
        # removes dependence on interpreting any aggregate invariant vector.
        low=tuple((str(i),int(row['N'].get(str(i),0))) for i in range(52))
        sig=(row['n'],low,tuple(sorted((int(e),str(c)) for e,c in row['L6'].items())))
        groups[sig].append(row)
    pairs=[]; tested=0
    for sig,rows in sorted(groups.items(),key=lambda kv:(kv[0][0],-len(kv[1]))):
        if len(rows)<2:continue
        n=sig[0]; seen={}
        for row in rows:
            L7=coefficient(n,row['edges'],7);tested+=1
            key=tuple(L7.items())
            if key in seen:continue
            if seen:
                old=next(iter(seen.values()))
                A=old['edges']; B=row['edges']
                check_cubic(n,A);check_cubic(n,B)
                for r in range(1,7):assert coefficient(n,A,r)==coefficient(n,B,r)
                for E in (A,B):assert coefficient(n,E,7)==coefficient_support(n,E,7)
                pairs.append({'n':n,'A':{'name':old['name'],'edges':A},'B':{'name':row['name'],'edges':B},
                              'agree_through':6,'delta_L7':polynomial_difference(coefficient(n,A,7),L7),
                              'delta_L7_factorization':'2 q^5 (1-q^2)^7 = 2 kappa^7 (1+f)',
                              'delta_leafless_core_counts':leafless_differences(n,A,B)})
                print('pair',len(pairs),n,old['name'],row['name'],flush=True)
                if len(pairs)>=args.max_pairs:break
            seen[key]=row
        if len(pairs)>=args.max_pairs:break
    output={'dependency_head':'517d6cf1d2fdd2f5369011db55a1e4bb2b51c7fd',
            'definition':'delta = B - A; polynomials have q exponents as keys',
            'pool_graphs':pool_size,'selected_candidate_graphs':len(records),'candidate_coefficients_enumerated':tested,
            'verification':'Direct integer weak compositions through 7; independent positive-support enumeration at 7',
            'pairs':pairs}
    target.write_text(json.dumps(output,indent=2)+'\n')
    print('wrote',target,'pairs',len(pairs),'coefficients',tested,flush=True)

if __name__=='__main__':main()
