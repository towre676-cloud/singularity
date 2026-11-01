#!/usr/bin/env python3
"""Replay the rational rowspace and leaf-extension certificates independently.

Reads vol7_law.json, checks every stored row-combination equality, verifies
that exact agreement through volume six is the twelve-coordinate J6, and
checks the seventh-order residual against its factored closed form.
Independently checks leaf reductions by injective-map enumeration in cubic
hosts, including saturated components. No numerical fitting is involved.
"""
import json
from collections import Counter
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from vol7_reduction import normal_form,edges,automorphisms,degrees,canonical
from vol7_lib import connected_types,edges_of
from vol7_law import rref

HERE=Path(__file__).resolve().parent

def load_poly(p):return {int(e):Fraction(c) for e,c in p.items()}

def count_in_host(k,m,n,es):
    if k>n:return 0
    adj=[set() for _ in range(n)]
    for a,b in es:adj[a].add(b);adj[b].add(a)
    pe=edges(k,m);pa=[set() for _ in range(k)]
    for a,b in pe:pa[a].add(b);pa[b].add(a)
    order=sorted(range(k),key=lambda v:-len(pa[v]))
    assign={};used=set()
    def visit(i):
        if i==k:return 1
        v=order[i];constraints=[assign[w] for w in pa[v] if w in assign]
        cand=set(range(n)) if not constraints else set.intersection(*(adj[w] for w in constraints))
        out=0
        for w in cand-used:
            assign[v]=w;used.add(w);out+=visit(i+1);used.remove(w);del assign[v]
        return out
    result=visit(0);a=automorphisms(k,m);assert result%a==0
    return result//a

def main():
    j=json.loads((HERE/'vol7_law.json').read_text())
    c={int(r):{(x['k'],x['mask']):load_poly(x['polynomial']) for x in data}
       for r,data in j['reduced_coefficients'].items()}
    keys=list(map(tuple,j['lower_core_keys']));z=[Fraction(0)]*len(keys)
    def coeffrow(r,e):return [c[r].get(key,{}).get(e,Fraction(0)) for key in keys]
    stored=[[Fraction(x) for x in row] for row in j['lower_coefficient_rref']]
    for want,combination in zip(stored,j['lower_rref_witnesses']):
        got=z[:]
        for rec in combination:
            got=[a+Fraction(rec['coefficient'])*b for a,b in zip(got,coeffrow(rec['volume'],rec['qexp']))]
        assert got==want
    rows=[coeffrow(r,e) for r,e in j['lower_coefficient_row_labels']]
    got,piv=rref(rows,len(keys));assert got==stored and piv==j['lower_coefficient_pivots']
    # Natural twelve-coordinate invariant vector J6.
    natural=[]
    for key in keys:
        k,m=key
        if k<=4 or(k==5 and m.bit_count() in (5,7)):
            natural.append([Fraction(other==key) for other in keys])
    natural.append([Fraction(k==5 and m.bit_count()==6) for k,m in keys])
    for e in range(6,10):natural.append([Fraction(k==6 and m.bit_count()==e) for k,m in keys])
    assert rref(natural,len(keys))[0]==stored and len(stored)==12
    # Replay seventh lower-support elimination as a polynomial vector.
    residual={(x['k'],x['mask']):load_poly(x['polynomial']) for x in j['seventh_lower_support_residual']}
    eliminated={}
    for x in j['seventh_lower_elimination']:
        row=coeffrow(x['source_volume'],x['source_qexp']);mult=load_poly(x['multiplier_q_polynomial'])
        for e,a in mult.items():
            rr=eliminated.setdefault(e,z[:])
            eliminated[e]=[b+a*d for b,d in zip(rr,row)]
    exps={e for key,p in c[7].items() if key[0]<7 for e in p}|set(eliminated)
    for e in exps:
        lhs=coeffrow(7,e)
        rhs=[a+residual.get(key,{}).get(e,Fraction(0)) for key,a in zip(keys,eliminated.get(e,z))]
        assert lhs==rhs,(e,lhs,rhs)
    assert set(residual)=={(5,221)}
    factored=Counter()
    from math import comb
    for i in range(8):
        for p,a in ((0,3),(1,3),(2,1)):
            factored[9+2*(i+p)]+=(-1)**i*comb(7,i)*a
    assert residual[(5,221)]=={e:Fraction(a) for e,a in factored.items() if a}
    # Top-size core coefficients are q21 f^e, exactly 21 motifs.
    cores=[(7,m) for m in connected_types(7) if min(degrees(7,m))>=2]
    assert len(cores)==21
    for key in cores:
        ee=key[1].bit_count()
        expected={21-2*i:Fraction(comb(ee,i)*(-1)**(ee-i)) for i in range(ee+1)}
        assert c[7][key]==expected
    assert Counter(m.bit_count() for k,m in cores)=={7:1,8:6,9:10,10:4}
    # Independent direct subgraph enumeration of every connected pattern<=7.
    k4=(4,list(combinations(range(4),2)))
    k33=(6,[(i,j) for i in range(3) for j in range(3,6)])
    prism=(6,[(0,1),(1,2),(2,0),(3,4),(4,5),(5,3),(0,3),(1,4),(2,5)])
    cube=(8,[(i,i^(1<<b)) for i in range(8) for b in range(3) if i<(i^(1<<b))])
    def union(*gs):
        n=0;es=[]
        for k,ee in gs:es.extend((a+n,b+n) for a,b in ee);n+=k
        return n,es
    hosts=[k4,k33,prism,cube,union(k4,k4),union(k4,k33),union(k4,prism)]
    checks=0
    for n,es in hosts:
        cache={}
        def cnt(key):
            k,m=key
            if key not in cache:cache[key]=count_in_host(k,m,n,es)
            return cache[key]
        for k in range(1,8):
            for m in connected_types(k):
                nf=normal_form(k,m)
                want=cnt((k,canonical(k,m)))
                got=sum(a*cnt(key) for key,a in nf.items())
                assert got==want,(n,k,m,got,want)
                checks+=1
    summary={'status':'PASS','lower_coefficient_rank':12,'lower_core_coordinates':20,
       'seventh_new_core_motifs':21,'seventh_edge_census':{'7':1,'8':6,'9':10,'10':4},
       'lower_support_residual':'q9(1-q2)^7(q4+3q2+3) N_Theta123',
       'leaf_reduction_direct_host_checks':checks,'cubic_hosts':len(hosts)}
    (HERE/'vol7_law_check.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
