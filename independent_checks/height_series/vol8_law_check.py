#!/usr/bin/env python3
"""Replay every rational eighth-law certificate and direct leaf identities.

The source combinations are checked as exact polynomial-vector equalities.
Direct injective-map counts audit all307 leaf reductions in component-rich
and connected cubic hosts, independent of the support-counting machinery.
"""
import json
from collections import Counter
from fractions import Fraction
from itertools import combinations
from math import comb
from pathlib import Path
from vol8_reduction import normal_form,edges,automorphisms,degrees,canonical
from vol8_lib import connected_types,edges_of
from vol8_law import rref

HERE=Path(__file__).resolve().parent

def poly(p):return {int(e):Fraction(c) for e,c in p.items()}

def mul(a,b):
    out=Counter()
    for i,x in a.items():
        for j,y in b.items():out[i+j]+=x*y
    return {e:c for e,c in out.items() if c}

def add(a,b,f=1):
    out=dict(a)
    for e,x in b.items():out[e]=out.get(e,Fraction(0))+f*x
    return {e:c for e,c in out.items() if c}

def count_in_host(k,m,n,es):
    if k>n:return 0
    adj=[set() for _ in range(n)]
    for a,b in es:adj[a].add(b);adj[b].add(a)
    pe=edges(k,m);pa=[set() for _ in range(k)]
    for a,b in pe:pa[a].add(b);pa[b].add(a)
    order=sorted(range(k),key=lambda v:-len(pa[v]));assign={};used=set()
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
    j=json.loads((HERE/'vol8_law.json').read_text())
    c={int(r):{(x['k'],x['mask']):poly(x['polynomial']) for x in data} for r,data in j['reduced_coefficients'].items()}
    legacy=json.loads((HERE/'vol7_law.json').read_text())
    assert {r:data for r,data in j['reduced_coefficients'].items() if int(r)<=7}==legacy['reduced_coefficients']
    keys=list(map(tuple,j['lower_core_keys']));z=[Fraction(0)]*len(keys)
    def row(r,e,kk=keys):return [c[r].get(key,{}).get(e,Fraction(0)) for key in kk]
    stored=[[Fraction(x) for x in rr] for rr in j['lower_coefficient_rref']]
    for want,cc in zip(stored,j['lower_rref_witnesses']):
        got=z[:]
        for x in cc:got=[a+Fraction(x['coefficient'])*b for a,b in zip(got,row(x['volume'],x['qexp']))]
        assert got==want
    got,piv=rref([row(r,e) for r,e in j['lower_coefficient_row_labels']],len(keys))
    assert got==stored and piv==j['lower_coefficient_pivots'] and len(got)==17
    residual={(x['k'],x['mask']):poly(x['polynomial']) for x in j['eighth_lower_support_residual']}
    eliminated={}
    for x in j['eighth_lower_elimination']:
        rr=row(x['source_volume'],x['source_qexp'])
        for e,a in poly(x['multiplier_q_polynomial']).items():
            eliminated[e]=[b+a*d for b,d in zip(eliminated.get(e,z),rr)]
    exps={e for key,p in c[8].items() if key[0]<8 for e in p}|set(eliminated)
    for e in exps:
        assert row(8,e)==[a+residual.get(key,{}).get(e,Fraction(0)) for key,a in zip(keys,eliminated.get(e,z))]
    kappa8={8+2*i:Fraction((-1)**i*comb(8,i)) for i in range(9)}
    alpha={2:Fraction(3),4:Fraction(3),6:Fraction(1)};f={-2:Fraction(1),0:Fraction(-1)}
    weights={1881:alpha,6265:alpha,6355:add(alpha,{0:1}),5941:{-2:-2,0:2},17142:mul(f,add(alpha,{0:1}))}
    assert set(residual)=={(6,m) for m in weights}
    for m,w in weights.items():assert residual[(6,m)]==mul(kappa8,w)
    allkeys=sorted({key for data in c.values() for key in data})
    obs=[]
    for rec in j['natural_observation_basis']:
        want=[Fraction(0)]*len(allkeys)
        for x in rec['coordinates']:want[allkeys.index((x['k'],x['mask']))]=Fraction(x['coefficient'])
        got=[Fraction(0)]*len(allkeys)
        for x in rec['coefficient_row_witness']:
            got=[a+Fraction(x['coefficient'])*b for a,b in zip(got,row(x['volume'],x['qexp'],allkeys))]
        assert got==want,rec['name'];obs.append(want)
    fullrows=[];ranks=[]
    for r in range(1,9):
        for e in sorted({e for p in c[r].values() for e in p}):fullrows.append(row(r,e,allkeys))
        ranks.append(len(rref(fullrows,len(allkeys))[0]))
    assert ranks==j['cumulative_observation_ranks']==[1,1,2,5,8,12,17,24]
    assert rref(obs,len(allkeys))[0]==rref(fullrows,len(allkeys))[0]
    assert rref(obs[:17],len(allkeys))[0]==rref([row(r,e,allkeys) for r in range(1,8) for e in {ee for p in c[r].values() for ee in p}],len(allkeys))[0]
    cores=[(8,m) for m in connected_types(8) if min(degrees(8,m))>=2]
    assert len(cores)==60
    for key in cores:
        ee=key[1].bit_count();expected={24-2*i:Fraction(comb(ee,i)*(-1)**(ee-i)) for i in range(ee+1)}
        assert c[8][key]==expected
    assert Counter(m.bit_count() for k,m in cores)=={8:1,9:10,10:25,11:19,12:5}
    k4=(4,list(combinations(range(4),2)))
    k33=(6,[(i,j) for i in range(3) for j in range(3,6)])
    prism=(6,[(0,1),(1,2),(2,0),(3,4),(4,5),(5,3),(0,3),(1,4),(2,5)])
    petersen=(10,[(i,(i+1)%5) for i in range(5)]+[(i,i+5) for i in range(5)]+[(i+5,(i+2)%5+5) for i in range(5)])
    def union(*gs):
        n=0;es=[]
        for k,ee in gs:es.extend((a+n,b+n) for a,b in ee);n+=k
        return n,es
    cubic8=[(8,edges_of(m,8)) for m in connected_types(8) if set(degrees(8,m))=={3}]
    assert len(cubic8)==5
    hosts=[k4,k33,prism,petersen,*cubic8,union(k4,k4),union(k4,k33),union(k4,prism)]
    checks=0
    for n,es in hosts:
        cache={}
        def cnt(key):
            k,m=key
            if key not in cache:cache[key]=count_in_host(k,m,n,es)
            return cache[key]
        for k in range(1,9):
            for m in connected_types(k):
                nf=normal_form(k,m);want=cnt((k,canonical(k,m)));got=sum(a*cnt(key) for key,a in nf.items())
                assert got==want,(n,k,m,got,want);checks+=1
    summary={'status':'PASS','lower_coefficient_rank':17,'lower_core_coordinates':41,
      'cumulative_observation_ranks':ranks,'eighth_new_observation_rank':7,'all_core_coordinates':101,
      'eighth_new_core_motifs':60,'eighth_edge_census':{'8':1,'9':10,'10':25,'11':19,'12':5},
      'residual_motifs':{'1881':'Theta124','6265':'Theta133','6355':'barbell','5941':'prism-minus-spoke','17142':'closed-diamond'},
      'leaf_reduction_direct_host_checks':checks,'cubic_hosts':len(hosts),'legacy_coefficient_volumes_preserved':7}
    (HERE/'vol8_law_check.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
