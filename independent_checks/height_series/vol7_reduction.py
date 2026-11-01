#!/usr/bin/env python3
"""Universal leaf elimination for ordinary subgraph counts in cubic hosts.

No fitting or host-graph assumptions beyond finite/simple/3-regular are used.
normal_form(k, mask) returns {(core_k, core_mask): Fraction(coefficient)}.
Masks use bit positions (0,1),(0,2),...,(k-2,k-1). Core masks use the
minimum over all vertex relabellings, agreeing with vol6_lib.canonical.
The module has no import-time enumeration or third-party dependency.
"""
from collections import Counter
from functools import lru_cache
from fractions import Fraction
from itertools import permutations

@lru_cache(None)
def pairs(k):
    return tuple((i,j) for i in range(k) for j in range(i+1,k))

@lru_cache(None)
def edges(k, mask):
    return tuple(e for p,e in enumerate(pairs(k)) if mask >> p & 1)

def make_mask(k, es):
    pos = {e:i for i,e in enumerate(pairs(k))}
    return sum(1 << pos[tuple(sorted(e))] for e in set(tuple(sorted(e)) for e in es))

@lru_cache(None)
def degrees(k, mask):
    d = [0]*k
    for a,b in edges(k,mask): d[a] += 1; d[b] += 1
    return tuple(d)

@lru_cache(None)
def canonical(k, mask):
    es = edges(k,mask)
    if k < 2: return mask
    pos = {e:i for i,e in enumerate(pairs(k))}
    best = None
    for p in permutations(range(k)):
        m = sum(1 << pos[tuple(sorted((p[a],p[b])))] for a,b in es)
        if best is None or m < best: best=m
    return best

@lru_cache(None)
def automorphisms(k,mask):
    es = edges(k,mask); eset=set(es); ds=degrees(k,mask)
    return sum(1 for p in permutations(range(k))
               if all(ds[i]==ds[p[i]] for i in range(k))
               and all(tuple(sorted((p[a],p[b]))) in eset for a,b in es))

def connected(k,mask):
    if k < 1: return False
    seen={0}
    while True:
        old=len(seen)
        for a,b in edges(k,mask):
            if a in seen or b in seen: seen.update((a,b))
        if len(seen)==old: return len(seen)==k

@lru_cache(None)
def _normal_form(k,mask):
    ds=degrees(k,mask)
    if max(ds,default=0)>3: return ()
    if not connected(k,mask): raise ValueError('connected patterns required')
    leaf=next((v for v,d in enumerate(ds) if d==1),None)
    if leaf is None: return (((k,mask),Fraction(1)),)
    es=edges(k,mask)
    root=next(a if b==leaf else b for a,b in es if leaf in (a,b))
    verts=[v for v in range(k) if v!=leaf]; rename={v:i for i,v in enumerate(verts)}
    hk=k-1
    hm=make_mask(hk,((rename[a],rename[b]) for a,b in es if leaf not in (a,b)))
    rv=rename[root]
    hd=degrees(hk,hm)
    ay=automorphisms(k,mask)
    terms=Counter()
    terms[(hk,canonical(hk,hm))] += Fraction((3-hd[rv])*automorphisms(hk,hm),ay)
    hes=set(edges(hk,hm))
    for w in range(hk):
        if w==rv or tuple(sorted((rv,w))) in hes: continue
        jm=make_mask(hk,tuple(hes)+(tuple(sorted((rv,w))),))
        if max(degrees(hk,jm))>3: continue
        terms[(hk,canonical(hk,jm))] -= Fraction(automorphisms(hk,jm),ay)
    out=Counter()
    for (tk,tm),c in terms.items():
        for core,v in normal_form(tk,tm).items(): out[core] += c*v
    return tuple(sorted((core,c) for core,c in out.items() if c))

def normal_form(k,mask):
    return dict(_normal_form(k,canonical(k,mask)))


def extension_identity(k,mask,v):
    """Return exact embedding-count equation terms for one rooted H.

    The returned dict gives (graph_k, canonical_mask): integer coefficient
    in a zero identity for ordinary subgraph counts, including the leaf
    extension itself. Repeated isomorphic collision graphs are aggregated.
    """
    ds=degrees(k,mask)
    if not 0<=v<k or ds[v]>=3: raise ValueError('root needs an unused cubic slot')
    ym=make_mask(k+1,edges(k,mask)+((v,k),))
    out=Counter({(k,canonical(k,mask)):(3-ds[v])*automorphisms(k,mask),
                 (k+1,canonical(k+1,ym)):-automorphisms(k+1,ym)})
    es=set(edges(k,mask))
    for w in range(k):
        if w==v or tuple(sorted((v,w))) in es: continue
        jm=make_mask(k,tuple(es)+(tuple(sorted((v,w))),))
        if max(degrees(k,jm))<=3:
            out[(k,canonical(k,jm))]-=automorphisms(k,jm)
    return {key:c for key,c in out.items() if c}

if __name__=='__main__':
    import json
    from pathlib import Path
    p6=Path(__file__).with_name('vol6_types6.json')
    data=json.loads(p6.read_text())
    out={}
    for name,rec in data.items():
        k=6; m=rec['mask']
        nf=normal_form(k,m)
        out[name]={'normal_form':[
            {'k':ck,'mask':cm,'coefficient':str(c)} for (ck,cm),c in nf.items()]}
    target=Path(__file__).with_name('vol7_leaf_reductions.json')
    target.write_text(json.dumps({'theorem':'cubic leaf-extension bijection',
      'volume6_regression':out},indent=2)+'\n')
    print('wrote',target.name,'with',len(out),'exact reductions')
