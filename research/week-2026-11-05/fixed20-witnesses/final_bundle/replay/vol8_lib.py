#!/usr/bin/env python3
"""Exact, stdlib-only connected-support machinery for subcubic graphs.

The catalogue is generated recursively by adding one vertex and at most
three incident edges.  A canonical mask orders vertices by decreasing
degree, then minimises over permutations within equal-degree classes.
This convention preserves vol7_lib masks on sizes <=7. At size8 an
orbit cache avoids repeating 8! searches on regular graph labellings.
It is deliberately independent of vol6_lib's mask numbering.
Patterns are keyed by (number_of_vertices, canonical_mask).
"""
from collections import Counter, defaultdict
from functools import lru_cache
from fractions import Fraction
from itertools import combinations, permutations, product
from math import factorial

MAXV = 8
PAIRS = {k: tuple(combinations(range(k), 2)) for k in range(9)}
PIDX = {k: {p:i for i,p in enumerate(PAIRS[k])} for k in range(9)}

def mask_from_edges(k, edges):
    return sum(1 << PIDX[k][tuple(sorted(e))] for e in set(tuple(sorted(e)) for e in edges))

def edges_of(mask, k):
    return tuple(e for i,e in enumerate(PAIRS[k]) if mask >> i & 1)

def degrees_of(mask, k):
    out = [0]*k
    for a,b in edges_of(mask,k): out[a] += 1; out[b] += 1
    return tuple(out)

def connected_mask(mask,k):
    if k == 0: return False
    seen = 1
    while True:
        new = seen
        for a,b in edges_of(mask,k):
            if seen >> a & 1: new |= 1 << b
            if seen >> b & 1: new |= 1 << a
        if new == seen: return seen == (1<<k)-1
        seen = new

_canonical8_orbits = {}

@lru_cache(None)
def canonical(mask,k):
    if k == 8:
        ds = degrees_of(mask,k)
        order=sorted(range(k),key=lambda v:(-ds[v],v))
        inv={v:i for i,v in enumerate(order)}
        normalized=mask_from_edges(k,((inv[a],inv[b]) for a,b in edges_of(mask,k)))
        if normalized in _canonical8_orbits: return _canonical8_orbits[normalized]
        sorted_degrees=tuple(ds[v] for v in order)
        classes=[[i for i in range(k) if sorted_degrees[i]==d]
                 for d in sorted(set(ds),reverse=True)]
        es=edges_of(normalized,k);orbit=set()
        for blocks in product(*(permutations(c) for c in classes)):
            perm=sum((tuple(c) for c in blocks),())
            relabelled=0
            for a,b in es:
                aa,bb=perm[a],perm[b]
                if aa>bb: aa,bb=bb,aa
                relabelled |= 1 << PIDX[k][(aa,bb)]
            orbit.add(relabelled)
        best=min(orbit)
        for m in orbit: _canonical8_orbits[m]=best
        return best
    if k < 2: return mask
    ds = degrees_of(mask,k)
    classes = [[i for i in range(k) if ds[i] == d] for d in sorted(set(ds),reverse=True)]
    best = None
    for choices in product(*(permutations(c) for c in classes)):
        order = sum((tuple(c) for c in choices), ())
        m = 0
        for i,(a,b) in enumerate(PAIRS[k]):
            a,b = sorted((order[a],order[b]))
            if mask >> PIDX[k][(a,b)] & 1: m |= 1 << i
        if best is None or m < best: best = m
    return best

@lru_cache(None)
def catalogue(k):
    """All unlabelled simple subcubic graph types on exactly k vertices."""
    if k == 0: return (0,)
    out = set()
    for old in catalogue(k-1):
        base = mask_from_edges(k,edges_of(old,k-1))
        eligible = [v for v,d in enumerate(degrees_of(old,k-1)) if d < 3]
        for s in range(min(3,len(eligible))+1):
            for nbrs in combinations(eligible,s):
                mask = base
                for v in nbrs: mask |= 1 << PIDX[k][(v,k-1)]
                out.add(canonical(mask,k))
    return tuple(sorted(out, key=lambda m:(m.bit_count(),m)))

@lru_cache(None)
def full_catalogue(k):
    """All simple graph types, without the subcubic restriction (audit only)."""
    if k == 0: return (0,)
    out = set()
    for old in full_catalogue(k-1):
        base = mask_from_edges(k,edges_of(old,k-1))
        for nbrmask in range(1 << (k-1)):
            mask = base
            for v in range(k-1):
                if nbrmask >> v & 1: mask |= 1 << PIDX[k][(v,k-1)]
            out.add(canonical(mask,k))
    return tuple(sorted(out,key=lambda m:(m.bit_count(),m)))

@lru_cache(None)
def connected_types(k):
    return tuple(m for m in catalogue(k) if connected_mask(m,k))

def induced_mask(mask,k,vertices):
    return mask_from_edges(len(vertices),((i,j) for i,j in PAIRS[len(vertices)] if mask >> PIDX[k][tuple(sorted((vertices[i],vertices[j])))] & 1))

@lru_cache(None)
def proper_connected_induced_counts(mask,k):
    counts = Counter()
    for s in range(1,k):
        for vs in combinations(range(k),s):
            m = induced_mask(mask,k,vs)
            if connected_mask(m,s): counts[(s,canonical(m,s))] += 1
    return dict(counts)

@lru_cache(None)
def spanning_subgraphs(mask,k,connected_only=True):
    """Map a canonical spanning pattern mask to its edge-subset multiplicity."""
    es = edges_of(mask,k)
    result = Counter()
    for subset in range(1<<len(es)):
        if connected_only and subset.bit_count() < k-1: continue
        m = mask_from_edges(k,(e for i,e in enumerate(es) if subset >> i & 1))
        if not connected_only or connected_mask(m,k): result[canonical(m,k)] += 1
    return dict(result)

def pmul(a,b):
    out = defaultdict(Fraction)
    for i,x in a.items():
        for j,y in b.items(): out[i+j] += x*y
    return {i:x for i,x in out.items() if x}

def padd(a,b,scale=1):
    out = dict(a)
    for i,x in b.items(): out[i] = out.get(i,Fraction(0))+scale*x
    return {i:x for i,x in out.items() if x}

def series_log(a,R=8):
    out = [{} for _ in range(R+1)]
    for r in range(1,R+1):
        acc = {i:Fraction(r*x) for i,x in a[r].items()}
        for j in range(1,r):
            acc = padd(acc,pmul({i:j*x for i,x in out[j].items()},a[r-j]),-1)
        out[r] = {i:x/r for i,x in acc.items() if x}
    return out

def compositions(total,parts):
    if parts == 0:
        if total == 0: yield ()
    elif parts == 1: yield (total,)
    else:
        for i in range(total+1):
            for rest in compositions(total-i,parts-1): yield (i,)+rest

@lru_cache(None)
def local_height_series(mask,k,R=8):
    """Ambient cubic energy 3 sum h_v^2 - 2 sum_{uv in E} h_u h_v."""
    a = [{0:1}]+[{} for _ in range(R)]
    es = edges_of(mask,k)
    for r in range(1,R+1):
        for h in compositions(r,k):
            e = 3*sum(t*t for t in h)-2*sum(h[u]*h[v] for u,v in es)
            a[r][e] = a[r].get(e,0)+1
    return a

@lru_cache(None)
def cumulant_coeffs(mask,k,R=8):
    """Connected-support kernel Phi_H via logZ and proper-support subtraction."""
    mask = canonical(mask,k)
    if not connected_mask(mask,k): return tuple({} for _ in range(R+1))
    out = series_log(local_height_series(mask,k,R),R)
    for (s,m),count in proper_connected_induced_counts(mask,k).items():
        smaller = cumulant_coeffs(m,s,R)
        for r in range(1,R+1): out[r] = padd(out[r],smaller[r],-count)
    return tuple(out)

@lru_cache(None)
def beta_coeffs(mask,k,R=8):
    """Edge Mobius transform of Phi: coefficient of N_H in log L.

    beta_H = sum_{F subset E(H)} (-1)^(e(H)-e(F)) Phi_(V,F).
    Disconnected F have zero Phi. Grouping by isomorphism gives the
    exact spanning-subgraph multiplicities used here.
    """
    out = [{} for _ in range(R+1)]
    e = mask.bit_count()
    for m,count in spanning_subgraphs(mask,k).items():
        sign = (-1)**(e-m.bit_count())
        phi = cumulant_coeffs(m,k,R)
        for r in range(1,R+1): out[r] = padd(out[r],phi[r],sign*count)
    return tuple(out)

def expected_top_beta(mask,k):
    """q^(3k) (q^-2-1)^e, as an exact q-polynomial."""
    from math import comb
    e = mask.bit_count()
    return {3*k-2*j:Fraction(comb(e,j)*(-1)**(e-j)) for j in range(e+1)}

def connected_vertex_sets(n,edges,kmax=8):
    """Connected vertex subsets, generated once at each cardinality.

    Every non-singleton connected set has a removable non-cut vertex,
    so growing all smaller connected sets reaches every set. Integer
    masks deduplicate all growth orders; cubic degree keeps this local.
    """
    adj=[0]*n
    for a,b in edges: adj[a] |= 1 << b; adj[b] |= 1 << a
    level={1 << v for v in range(n)}
    for k in range(1,min(kmax,n)+1):
        yield k,tuple(sorted(level))
        if k == min(kmax,n): break
        larger=set()
        for subset in level:
            boundary=0; remaining=subset
            while remaining:
                bit=remaining & -remaining; remaining-=bit
                boundary |= adj[bit.bit_length()-1]
            boundary &= ~subset
            while boundary:
                bit=boundary & -boundary; boundary-=bit
                larger.add(subset | bit)
        level=larger


def count_patterns(n,edges,kmax=8):
    """All connected non-induced pattern counts through kmax.

    Enumerates connected supports only, then all spanning edge subsets.
    Large weld rings therefore incur local-support rather than binomial
    vertex-subset enumeration.
    """
    adj = [set() for _ in range(n)]
    for a,b in edges: adj[a].add(b); adj[b].add(a)
    result = Counter()
    for k,subsets in connected_vertex_sets(n,edges,kmax):
        induced = Counter()
        for subset in subsets:
            vs=tuple(v for v in range(n) if subset >> v & 1)
            m = mask_from_edges(k,((i,j) for i,j in PAIRS[k] if vs[j] in adj[vs[i]]))
            induced[canonical(m,k)] += 1
        for m,count in induced.items():
            for pattern,mult in spanning_subgraphs(m,k).items(): result[(k,pattern)] += count*mult
    return dict(result)

def height_series(n,edges,R=8):
    """Independent direct weak-composition enumeration in edge energy."""
    a = [{0:1}]+[{} for _ in range(R)]
    for r in range(1,R+1):
        for h in compositions(r,n):
            e = sum((h[u]-h[v])**2 for u,v in edges)
            a[r][e] = a[r].get(e,0)+1
    return a

def log_from_counts(counts,R=8):
    out = [{} for _ in range(R+1)]
    for (k,m),count in counts.items():
        beta = beta_coeffs(m,k,R)
        for r in range(1,R+1): out[r] = padd(out[r],beta[r],count)
    return out

def encode_poly(poly):
    return {str(e):str(c) for e,c in sorted(poly.items())}
