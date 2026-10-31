#!/usr/bin/env python3
"""Deterministic cubic completion and exact isolation of every small core.

No random graphs or fitted identities: the completion matrix is unitriangular.
Run this file to replay and write vol8_completion_certificate.json.
"""
import json
from collections import Counter, deque
from functools import lru_cache
from itertools import combinations
from math import gcd
from pathlib import Path
from vol8_lib import (canonical, connected_types, count_patterns, degrees_of,
                      edges_of, mask_from_edges)

HERE = Path(__file__).resolve().parent

def girth12_graph():
    """Explicit126-vertex cubic graph; all properties are checked at replay."""
    shifts = [17,27,-13,-59,-35,35,-11,13,-53,53,-27,21,57,11,-21,-57,59,-17]*7
    n = len(shifts)
    edges = {tuple(sorted((i,(i+1)%n))) for i in range(n)}
    edges |= {tuple(sorted((i,(i+d)%n))) for i,d in enumerate(shifts)}
    return n,tuple(sorted(edges))

def girth(n,edges):
    adj = [set() for _ in range(n)]
    for a,b in edges: adj[a].add(b); adj[b].add(a)
    result = n+1
    for start in range(n):
        dist = {start:0}; parent = {start:-1}; queue = deque([start])
        while queue:
            v = queue.popleft()
            for w in adj[v]:
                if w not in dist:
                    dist[w] = dist[v]+1; parent[w] = v; queue.append(w)
                elif parent[v] != w:
                    result = min(result,dist[v]+dist[w]+1)
    return result

def completion(k,mask):
    """Attach one subdivided girth-twelve cap per missing cubic half-edge."""
    nQ,eQ = girth12_graph()
    cut = eQ[0]
    cap = tuple(e for e in eQ if e != cut)+((cut[0],126),(cut[1],126))
    es = list(edges_of(mask,k)); n = k
    for v,d in enumerate(degrees_of(mask,k)):
        for _ in range(3-d):
            es.extend((a+n,b+n) for a,b in cap)
            es.append((v,n+126)); n += 127
    return n,tuple(es)

def cores(maxk=8):
    return tuple((k,m) for k in range(3,maxk+1) for m in connected_types(k)
                 if min(degrees_of(m,k)) >= 2)

def key(pattern):
    return '%s:%s'%pattern

@lru_cache(None)
def isolation_data():
    """Signed completion combinations whose core count vectors are unit vectors."""
    C = cores()
    rows = {}
    isolators = {}
    for h in C:
        k,m = h
        counts = count_patterns(k,edges_of(m,k),k)
        rows[h] = {j:counts.get(j,0) for j in C if counts.get(j,0)}
        assert rows[h].get(h) == 1
        relation = Counter({h:1})
        for j,mult in rows[h].items():
            if j == h: continue
            assert C.index(j) < C.index(h), (h,j)
            for g,c in isolators[j].items(): relation[g] -= mult*c
        isolators[h] = {g:c for g,c in relation.items() if c}
        assert all(sum(c*rows[g].get(j,0) for g,c in isolators[h].items()) == (j==h) for j in C)
    return C,rows,isolators

def realize_core_vector(vector):
    """Return integer signed cubic components, equal-order sides, and scale.

    A component (0,0) denotes the 126-vertex girth-twelve padding graph.
    Pattern (k,m) denotes its deterministic cubic completion.
    """
    C,rows,iso = isolation_data()
    relation = Counter()
    for h,mult in vector.items():
        for g,c in iso[h].items(): relation[g] += mult*c
    relation = {g:c for g,c in relation.items() if c}
    ndiff = sum(c*(382*g[0]-254*g[1].bit_count()) for g,c in relation.items())
    scale = 126//gcd(abs(ndiff),126)
    relation = {g:c*scale for g,c in relation.items()}
    if ndiff: relation[(0,0)] = -ndiff*scale//126
    assert sum(c*(126 if g==(0,0) else 382*g[0]-254*g[1].bit_count()) for g,c in relation.items()) == 0
    return relation,scale

def connected_subset_counts(n,edges,maxk=8,root_limit=None):
    """Independently count small patterns in a large sparse completed graph.

    Enumerates connected vertex subsets by their least vertex.  Unlike
    count_patterns, the cost does not include all binomial(n,8) subsets.
    """
    from vol8_lib import connected_mask, spanning_subgraphs
    adj = [set() for _ in range(n)]
    for a,b in edges: adj[a].add(b); adj[b].add(a)
    induced = Counter()
    for root in range(n if root_limit is None else root_limit):
        level = {frozenset((root,))}
        for k in range(1,maxk+1):
            nxt = set()
            for S in level:
                vs = sorted(S)
                m = mask_from_edges(k,((i,j) for i,j in combinations(range(k),2) if vs[j] in adj[vs[i]]))
                induced[(k,canonical(m,k))] += 1
                if k < maxk:
                    for v in S:
                        for w in adj[v]:
                            if w > root and w not in S: nxt.add(S|{w})
            level = nxt
    out = Counter()
    for (k,m),c in induced.items():
        for sub,mult in spanning_subgraphs(m,k).items(): out[(k,sub)] += c*mult
    return dict(out)

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--boundary-check',action='store_true',help='enumerate all boundary supports; pure-cap cores excluded by exact girth')
    args = p.parse_args()
    nQ,eQ = girth12_graph()
    assert nQ==126 and len(eQ)==189 and girth(nQ,eQ)==12
    assert all(sum(v in e for e in eQ)==3 for v in range(nQ))
    C,rows,iso = isolation_data()
    records = []
    for h in C:
        n,es = completion(*h)
        assert n==382*h[0]-254*h[1].bit_count()
        ds = Counter(v for e in es for v in e)
        assert all(ds[v]==3 for v in range(n)) and len(set(tuple(sorted(e)) for e in es))==len(es)
        if args.boundary_check:
            actual = connected_subset_counts(n,es,root_limit=h[0])
            assert all(actual.get(j,0)==rows[h].get(j,0) for j in C),h
        relation,scale = realize_core_vector({h:1})
        order = sum(c*(126 if g==(0,0) else completion(*g)[0]) for g,c in relation.items() if c>0)
        records.append({'core':key(h),'core_edges':list(edges_of(h[1],h[0])),
                        'completion_order':n,'counts':{key(j):c for j,c in rows[h].items()},
                        'isolation_scale':scale,'pair_order':order,
                        'signed_components':{key(g):c for g,c in sorted(relation.items())}})
    out = {'schema':'singularity.volume8.cubic-completion.v1',
           'dependency':'facb4506d1e9b1667b877815777566296572a4fb',
           'padding_graph':{'n':nQ,'edges':eQ,'girth':12},
           'core_count':len(C),'eight_core_count':sum(k==8 for k,m in C),
           'matrix_determinant':1,'boundary_support_check':args.boundary_check,'pure_cap_core_exclusion':'girth12 exceeds cutoff8','isolators':records}
    (HERE/'vol8_completion_certificate.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('padding_graph','isolators')}),flush=True)

if __name__=='__main__': main()
