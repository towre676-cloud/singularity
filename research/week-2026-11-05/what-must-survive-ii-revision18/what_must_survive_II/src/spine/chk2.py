import networkx as nx,warnings,json
warnings.filterwarnings("ignore")
from collections import defaultdict
exec(open('chk.py').read().split("res={}")[0])
def desc(T):
    H=[v for v in T if T.degree(v)>1]
    I=T.subgraph(H)
    if is_cat(T):
        ends=[v for v in I if I.degree(v)<=1]
        p=nx.shortest_path(I,ends[0],ends[-1]);return ('cat',[T.degree(v)-I.degree(v) for v in p])
    return ('non',sorted((T.degree(v)-I.degree(v),sorted(T.degree(u)-I.degree(u) for u in I[v])) for v in I), sorted(d for _,d in I.degree()))
for n in (10,12,14,16,18,20):
    g=defaultdict(list)
    for T in nx.nonisomorphic_trees(n):
        A,B,N=AB(T);g[(key(A),key(B))].append(T)
    for v in g.values():
        if len(v)>1 and any(is_cat(T) and spine_len(T)<=4 for T in v):
            print(n,[desc(T) for T in v],'deg',[sorted(dict(T.degree()).values())==sorted(dict(v[0].degree()).values()) for T in v])
