#!/usr/bin/env python3
"""Deterministic cubic completion and exact isolation of every small core.

No random graphs or fitted identities: the completion matrix is unitriangular.
Run this file to replay and write vol7_completion_certificate.json.
"""
import json
from collections import Counter, deque
from functools import lru_cache
from itertools import combinations
from math import gcd
from pathlib import Path
from vol7_lib import (canonical, connected_types, count_patterns, degrees_of,
                      edges_of, mask_from_edges)

HERE = Path(__file__).resolve().parent

def perfect_matchings(points):
    if not points:
        yield ()
        return
    a = points[0]
    for b in points[1:]:
        rest = tuple(x for x in points if x not in (a,b))
        for matching in perfect_matchings(rest):
            yield ((a,b),)+matching

def girth8_graph():
    """Duad-syntheme incidence graph, with its 30 vertices labelled explicitly."""
    duads = list(combinations(range(6),2))
    index = {p:i for i,p in enumerate(duads)}
    matchings = list(perfect_matchings(tuple(range(6))))
    return 30, tuple((index[p],15+j) for j,M in enumerate(matchings) for p in M)

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
    """Attach one subdivided girth-eight cap per missing cubic half-edge."""
    nQ,eQ = girth8_graph()
    cut = eQ[0]
    cap = tuple(e for e in eQ if e != cut)+((cut[0],30),(cut[1],30))
    es = list(edges_of(mask,k)); n = k
    for v,d in enumerate(degrees_of(mask,k)):
        for _ in range(3-d):
            es.extend((a+n,b+n) for a,b in cap)
            es.append((v,n+30)); n += 31
    return n,tuple(es)

def cores(maxk=7):
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

    A component (0,0) denotes the 30-vertex girth-eight padding graph.
    Pattern (k,m) denotes its deterministic cubic completion.
    """
    C,rows,iso = isolation_data()
    relation = Counter()
    for h,mult in vector.items():
        for g,c in iso[h].items(): relation[g] += mult*c
    relation = {g:c for g,c in relation.items() if c}
    ndiff = sum(c*(94*g[0]-62*g[1].bit_count()) for g,c in relation.items())
    scale = 30//gcd(abs(ndiff),30)
    relation = {g:c*scale for g,c in relation.items()}
    if ndiff: relation[(0,0)] = -ndiff*scale//30
    assert sum(c*(30 if g==(0,0) else 94*g[0]-62*g[1].bit_count()) for g,c in relation.items()) == 0
    return relation,scale

def connected_subset_counts(n,edges,maxk=7):
    """Independently count small patterns in a large sparse completed graph.

    Enumerates connected vertex subsets by their least vertex.  Unlike
    count_patterns, the cost does not include all binomial(n,7) subsets.
    """
    from vol7_lib import connected_mask, spanning_subgraphs
    adj = [set() for _ in range(n)]
    for a,b in edges: adj[a].add(b); adj[b].add(a)
    induced = Counter()
    for root in range(n):
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
    p.add_argument('--full-host-check',action='store_true',help='enumerate all small connected supports in every completed host')
    args = p.parse_args()
    nQ,eQ = girth8_graph()
    assert nQ==30 and len(eQ)==45 and girth(nQ,eQ)==8
    assert all(sum(v in e for e in eQ)==3 for v in range(nQ))
    C,rows,iso = isolation_data()
    records = []
    for h in C:
        n,es = completion(*h)
        assert n==94*h[0]-62*h[1].bit_count()
        ds = Counter(v for e in es for v in e)
        assert all(ds[v]==3 for v in range(n)) and len(set(tuple(sorted(e)) for e in es))==len(es)
        if args.full_host_check:
            actual = connected_subset_counts(n,es)
            assert all(actual.get(j,0)==rows[h].get(j,0) for j in C),h
        relation,scale = realize_core_vector({h:1})
        order = sum(c*(30 if g==(0,0) else completion(*g)[0]) for g,c in relation.items() if c>0)
        records.append({'core':key(h),'core_edges':list(edges_of(h[1],h[0])),
                        'completion_order':n,'counts':{key(j):c for j,c in rows[h].items()},
                        'isolation_scale':scale,'pair_order':order,
                        'signed_components':{key(g):c for g,c in sorted(relation.items())}})
    out = {'schema':'singularity.volume7.cubic-completion.v1',
           'dependency':'517d6cf1d2fdd2f5369011db55a1e4bb2b51c7fd',
           'padding_graph':{'n':nQ,'edges':eQ,'girth':8},
           'core_count':len(C),'seven_core_count':sum(k==7 for k,m in C),
           'matrix_determinant':1,'full_host_check':args.full_host_check,'isolators':records}
    (HERE/'vol7_completion_certificate.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('padding_graph','isolators')}),flush=True)

if __name__=='__main__': main()
