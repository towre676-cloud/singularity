"""Exact weighted tree contraction censuses and integer energy shells."""
from collections import Counter,defaultdict
from itertools import combinations,product
import json,math
from pathlib import Path
import networkx as nx
ROOT=Path(__file__).resolve().parent

def canonical(adj,weights):
    def at(v,p): return (weights[v],tuple(sorted(at(w,v) for w in adj[v] if w!=p)))
    return min(at(v,-1) for v in range(len(weights)))

def quotient(n,edges,selected):
    sel=set(selected);par=list(range(n))
    def find(v):
        while par[v]!=v:
            par[v]=par[par[v]];v=par[v]
        return v
    for i,(a,b) in enumerate(edges):
        if i not in sel: par[find(a)]=find(b)
    ix={};component=[]
    for v in range(n):
        p=find(v)
        if p not in ix:ix[p]=len(ix)
        component.append(ix[p])
    weights=[0]*len(ix)
    for a in component:weights[a]+=1
    adj=[[] for _ in weights]
    for i in selected:
        a,b=map(lambda v:component[v],edges[i]);adj[a].append(b);adj[b].append(a)
    return adj,weights

def census(T,k):
    T=nx.convert_node_labels_to_integers(T);E=list(T.edges())
    return Counter(canonical(*quotient(len(T),E,S)) for S in combinations(range(len(E)),k))

def sign_poly(adj,weights,magnitudes=None):
    n=sum(weights);order=[0];parents={0:-1}
    for v in order:
        for w in adj[v]:
            if w!=parents[v]:parents[w]=v;order.append(w)
    k=len(weights)-1;out=Counter()
    for z in product((-1,1),repeat=k):
        h=[0]*len(weights)
        for i,v in enumerate(order[1:]):h[v]=h[parents[v]]+z[i]*(1 if magnitudes is None else magnitudes[i])
        out[sum(a*b for a,b in zip(weights,h))-n*min(h)]+=1
    return out

def unit_shell(T,k):
    T=nx.convert_node_labels_to_integers(T);E=list(T.edges());out=Counter()
    for S in combinations(range(len(E)),k):out.update(sign_poly(*quotient(len(T),E,S)))
    return out

def full_shells(T,emax):
    T=nx.convert_node_labels_to_integers(T);n=len(T);order=[0];parent={0:-1}
    for v in order:
        for w in T[v]:
            if w!=parent[v]:parent[w]=v;order.append(w)
    out=[Counter() for _ in range(emax+1)];h=[0]*n
    def rec(i,e):
        if i==n:
            out[e][sum(h)-n*min(h)]+=1;return
        v=order[i]
        for z in range(-math.isqrt(emax-e),math.isqrt(emax-e)+1):
            h[v]=h[parent[v]]+z;rec(i+1,e+z*z)
    rec(1,0);return out

def diff(a,b):return {str(k):a[k]-b[k] for k in sorted(a.keys()|b.keys()) if a[k]!=b[k]}

