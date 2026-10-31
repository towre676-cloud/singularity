#!/usr/bin/env python3
"""Exact terminating cubic leaf recurrence through volume eight and beyond.

Independent degree-block canonicalisation and automorphism enumeration avoid
an unrestricted factorial loop on every eight-vertex leaf pattern.
normal_form(k,mask) returns {(core_k,core_mask): Fraction(coefficient)}.
"""
from collections import Counter
from functools import lru_cache
from fractions import Fraction
from itertools import combinations,permutations,product

@lru_cache(None)
def pairs(k):return tuple(combinations(range(k),2))

@lru_cache(None)
def positions(k):return {e:i for i,e in enumerate(pairs(k))}

@lru_cache(None)
def edges(k,mask):return tuple(e for p,e in enumerate(pairs(k)) if mask>>p&1)

def make_mask(k,es):
    pos=positions(k)
    return sum(1<<pos[e] for e in set(tuple(sorted(e)) for e in es))

@lru_cache(None)
def degrees(k,mask):
    d=[0]*k
    for a,b in edges(k,mask):d[a]+=1;d[b]+=1
    return tuple(d)

@lru_cache(None)
def degree_orders(k,ds):
    groups=[[v for v,dv in enumerate(ds) if dv==d] for d in sorted(set(ds),reverse=True)]
    return tuple(sum(choice,()) for choice in product(*(tuple(permutations(g)) for g in groups)))

@lru_cache(None)
def canonical(k,mask):
    if k<2:return mask
    ds=degrees(k,mask);es=edges(k,mask);pos=positions(k);best=None
    for order in degree_orders(k,ds):
        inverse=[0]*k
        for new,old in enumerate(order):inverse[old]=new
        out=sum(1<<pos[tuple(sorted((inverse[a],inverse[b])))] for a,b in es)
        if best is None or out<best:best=out
    return best

@lru_cache(None)
def automorphisms(k,mask):
    ds=degrees(k,mask);es=set(edges(k,mask));out=0
    groups=[[v for v,dv in enumerate(ds) if dv==d] for d in sorted(set(ds))]
    slots=sum((tuple(g) for g in groups),())
    for choice in product(*(tuple(permutations(g)) for g in groups)):
        image=dict(zip(slots,sum(choice,())))
        if all(tuple(sorted((image[a],image[b]))) in es for a,b in es):out+=1
    return out

def connected(k,mask):
    if k<1:return False
    seen={0}
    while True:
        old=len(seen)
        for a,b in edges(k,mask):
            if a in seen or b in seen:seen.update((a,b))
        if len(seen)==old:return len(seen)==k

@lru_cache(None)
def _normal_form(k,mask):
    ds=degrees(k,mask)
    if max(ds,default=0)>3:return ()
    if not connected(k,mask):raise ValueError('connected patterns required')
    leaf=next((v for v,d in enumerate(ds) if d==1),None)
    if leaf is None:return (((k,mask),Fraction(1)),)
    es=edges(k,mask);root=next(a if b==leaf else b for a,b in es if leaf in(a,b))
    verts=[v for v in range(k) if v!=leaf];rename={v:i for i,v in enumerate(verts)}
    hk=k-1;hm=make_mask(hk,((rename[a],rename[b]) for a,b in es if leaf not in(a,b)))
    rv=rename[root];hd=degrees(hk,hm);ay=automorphisms(k,mask)
    terms=Counter({(hk,canonical(hk,hm)):Fraction((3-hd[rv])*automorphisms(hk,hm),ay)})
    hes=set(edges(hk,hm))
    for w in range(hk):
        if w==rv or tuple(sorted((rv,w))) in hes:continue
        jm=make_mask(hk,tuple(hes)+(tuple(sorted((rv,w))),))
        if max(degrees(hk,jm))<=3:
            terms[(hk,canonical(hk,jm))]-=Fraction(automorphisms(hk,jm),ay)
    out=Counter()
    for (tk,tm),c in terms.items():
        for core,v in normal_form(tk,tm).items():out[core]+=c*v
    return tuple(sorted((core,c) for core,c in out.items() if c))

def normal_form(k,mask):return dict(_normal_form(k,canonical(k,mask)))

if __name__=='__main__':
    import json
    from pathlib import Path
    from vol8_lib import connected_types
    from vol7_reduction import normal_form as old_normal_form
    data=[];regressions=0
    for k in range(1,9):
        for m in connected_types(k):
            nf=normal_form(k,m)
            if k<=7:
                old={(s,canonical(s,t)):c for (s,t),c in old_normal_form(k,m).items()}
                assert nf==old,(k,m,nf,old)
                regressions+=1
            data.append({'k':k,'mask':m,'normal_form':[{'k':s,'mask':t,'coefficient':str(c)} for(s,t),c in sorted(nf.items())]})
    out={'schema':'singularity-volume-eight-leaf-reductions-v1','volume7_regressions':regressions,'reductions':data}
    Path(__file__).with_name('vol8_leaf_reductions.json').write_text(json.dumps(out,indent=2)+'\n')
    print('Exact leaf reductions',len(data),'legacy regressions',regressions)
