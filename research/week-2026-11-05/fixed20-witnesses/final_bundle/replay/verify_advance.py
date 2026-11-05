#!/usr/bin/env python3
"""Fresh exact algebra checks and selected-witness replay; stdlib only."""
from collections import Counter,deque
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import json,argparse
from vol8_lib import edges_of,degrees_of
from vol8_law import rref
from vol8_reader import factors,invert
from vol8_completion import girth12_graph,girth
from connected_check import independent_cores,small_check,distances
HERE=Path(__file__).resolve().parent
KEEP={1:(0,1,2,3,5,6),2:(0,1,2,3,5,6),3:(0,1,2,5)}
PANELS={1:(6,10,14,18,24,26),2:(6,10,14,18,24,26),3:(8,14,18,20)}

def connectivity(n,E,k):
    adj=[[] for _ in range(n)]
    for a,b in E:adj[a].append(b);adj[b].append(a)
    for target in range(1,n):
        flow={}
        for _ in range(k):
            par={0:None};q=deque([0])
            while q and target not in par:
                a=q.popleft()
                for b in adj[a]:
                    if b not in par and flow.get((a,b),0)<1:par[b]=a;q.append(b)
            if target not in par:return False
            v=target
            while v:
                u=par[v];flow[u,v]=flow.get((u,v),0)+1;flow[v,u]=flow.get((v,u),0)-1;v=u
    return True

def admissible(k,m,lam):
    E=edges_of(m,k)
    return all(3*bits.bit_count()-2*sum((bits>>a&1) and (bits>>b&1) for a,b in E)>=lam
               for bits in range(1,1<<k))

def optimize(keep):
    ff=[factors()[i] for i in keep];d=len(ff);degrees=sorted({e for p in ff for e in p})
    best=None;count=full=ties=0
    for pp in combinations(degrees,d):
        count+=1
        try:inv,det=invert([[p.get(e,0) for p in ff] for e in pp])
        except ValueError:continue
        full+=1;norm=max(sum(map(abs,row)) for row in inv)
        if best is None or norm<best[0]:best=(norm,pp,inv,det);ties=1
        elif norm==best[0]:ties+=1
    norm,pp,inv,det=best;M=[[p.get(e,0) for p in ff] for e in pp]
    assert all(sum(inv[i][k]*M[k][j] for k in range(d))==int(i==j) for i in range(d) for j in range(d))
    return {'degrees':pp,'determinant':str(det),'inverse_norm':str(norm),
            'inverse':[[str(x) for x in row] for row in inv],'checked':count,'invertible':full,'optimal_ties':ties}

def algebra():
    s=json.loads((HERE/'vol8_law.json').read_text())
    c={int(r):{(x['k'],x['mask']):{int(e):F(a) for e,a in x['polynomial'].items()} for x in d}
       for r,d in s['reduced_coefficients'].items()}
    keys=sorted({h for d in c.values() for h in d});out=[]
    coords=[{(x['k'],x['mask']):F(x['coefficient']) for x in n['coordinates']} for n in s['natural_observation_basis'][17:]]
    for lam in (1,2,3):
        C=sorted((h for h in keys if h!=(1,0) and admissible(*h,lam)),key=lambda h:(h[0],h[1].bit_count(),h[1]))
        rows={};iso={}
        for h in C:
            row=independent_cores(*h);rows[h]=row;assert row[h]==1
            rel=Counter({h:1})
            for j,v in row.items():
                if j==h:continue
                assert C.index(j)<C.index(h)
                for g,a in iso[j].items():rel[g]-=v*a
            iso[h]={g:a for g,a in rel.items() if a}
            assert all(sum(a*rows[g].get(j,0) for g,a in iso[h].items())==int(j==h) for j in C)
        kk=[(1,0)]+C
        rr=lambda rs:[[c[r].get(h,{}).get(e,0) for h in kk] for r in rs for e in sorted({e for p in c[r].values() for e in p})]
        low,piv=rref(rr(range(1,8)),len(kk));total=rref(rr(range(1,9)),len(kk))[0]
        assert (len(C),len(low),len(total))=={1:(92,15,21),2:(86,13,19),3:(58,11,15)}[lam]
        for e in sorted({e for p in c[8].values() for e in p}|{e for p in factors() for e in p}):
            row=[c[8].get(h,{}).get(e,0)-sum(factors()[i].get(e,0)*coords[i].get(h,0) for i in KEEP[lam]) for h in kk]
            for b,j in zip(low,piv):
                a=row[j];row=[x-a*y for x,y in zip(row,b)]
            assert not any(row)
        out.append({'edge_connectivity':lam,'admissible_cores':len(C),'unit_isolators':len(iso),'lower_rank':len(low),'total_rank':len(total)})
    n,E=girth12_graph();assert girth(n,E)==12 and connectivity(n,E,3)
    ports=sorted(b if a==0 else a for a,b in E if 0 in(a,b));EE=[e for e in E if 0 not in e]
    assert ports==[1,17,125] and min(distances(n,EE,ports)[v] for v in (5,6))>=4
    cert={'classes':out,'small_graphs':small_check(),'reservoir_parent_girth':12,'reservoir_parent_edge_connectivity':3,
          'panels':{'six':optimize(KEEP[2]),'four':optimize(KEEP[3])},
          'evidence':'freshly regenerated after workspace maintenance'}
    (HERE/'fresh_algebra_certificate.json').write_text(json.dumps(cert,indent=2)+'\n')
    print(json.dumps(cert,indent=2),flush=True)

def decode(line):
    n=ord(line[0])-63;bits=[(ord(c)-63)>>j&1 for c in line.strip()[1:] for j in range(5,-1,-1)]
    return n,[e for e,b in zip(((i,j) for j in range(1,n) for i in range(j)),bits) if b]

def vector(delta,lam=2):
    ff=[factors()[i] for i in KEEP[lam]];pp=PANELS[lam];inv,_=invert([[p.get(e,0) for p in ff] for e in pp])
    v=[sum(row[j]*delta.get(pp[j],0) for j in range(len(pp))) for row in inv]
    recon={}
    for a,p in zip(v,ff):
        for e,b in p.items():recon[e]=recon.get(e,0)+a*b
    assert {e:a for e,a in recon.items() if a}==delta and all(a.denominator==1 for a in v)
    return list(map(int,v))

def witnesses():
    from vol7_witnesses import coefficient,coefficient_support
    requested=[(16,288,502,[2,4,2,0,0,0]),(16,493,586,[-2,-2,0,0,0,0]),
               (16,215,879,[1,0,0,0,-1,0]),(16,15,38,[-2,0,0,0,0,0]),
               (18,32611,37672,[0,0,-1,0,0,1])]
    saved=[]
    p=json.loads((HERE/'vol8_witnesses.json').read_text())['pairs'][0]
    cases=[(12,p['A']['edges'],p['B']['edges'],None,'source twelve-vertex witness')]
    for n,a,b,v in requested:
        lines=(HERE/f'cubic{n}.g6').read_text().splitlines();A=decode(lines[a])[1];B=decode(lines[b])[1]
        cases.append((n,A,B,v,f'catalogue {a},{b}'))
    for n,A,B,expected,label in cases:
        for r in range(1,8):assert coefficient(n,A,r)==coefficient(n,B,r)
        aa=coefficient(n,A,8);bb=coefficient(n,B,8)
        assert aa==coefficient_support(n,A,8) and bb==coefficient_support(n,B,8)
        dd={e:bb.get(e,0)-aa.get(e,0) for e in aa.keys()|bb.keys()};dd={e:x for e,x in dd.items() if x};v=vector(dd)
        if expected is not None:assert v==expected
        lam=2 if n==18 else 3;assert connectivity(n,A,lam) and connectivity(n,B,lam)
        saved.append({'n':n,'label':label,'A_edges':A,'B_edges':B,'coordinates_B_minus_A':v,
                      'edge_connectivity_lower_bound':lam,'two_independent_height_enumerators':True})
        print('Fresh independent witness passed',n,label,v,flush=True)
    from vol8_weld import ring_series,WORDS,difference
    weld=json.loads((HERE/'vol8_weld.json').read_text());ss=[ring_series(w) for w in WORDS]
    assert all(ss[0][r]==ss[1][r] for r in range(8));v=vector(difference(ss[0][8],ss[1][8]));assert v==[0,-9,-6,-1,0,0]
    for g,series in zip(weld['graphs'],ss):
        assert connectivity(g['n'],g['edges'],2)
        for r in range(1,9):assert coefficient(g['n'],g['edges'],r)==series[r]
    assert abs(invert([x['coordinates_B_minus_A'] for x in saved[1:]]+[v])[1])==8
    (HERE/'fresh_small_witnesses.json').write_text(json.dumps({'witnesses':saved,'weld_vector':v,
         'six_basis_determinant_absolute':8,'evidence':'fresh direct, support and transfer checks after workspace maintenance'},indent=2)+'\n')
    print('Fresh weld and full six-basis determinant checks passed.',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--witnesses',action='store_true');a=ap.parse_args()
    witnesses() if a.witnesses else algebra()
