import networkx as nx,sympy as sp,itertools,json,warnings
warnings.filterwarnings("ignore")
from collections import Counter
res={};n_checked=0;ok=True
def S3(T):
    n=len(T);E=list(nx.bfs_edges(T,0));order=[0]+[w for u,w in E];par={w:u for u,w in E};c=Counter()
    for F in itertools.combinations(order[1:],3):
        for sg in itertools.product((-1,1),repeat=3):
            z=dict(zip(F,sg));h={0:0}
            for v in order[1:]: h[v]=h[par[v]]+z.get(v,0)
            vals=list(h.values());c[sum(vals)-n*min(vals)]+=1
    return c
def formula(T):
    n=len(T);E=list(T.edges());prod=Counter();H=Counter()
    def side(e):
        G=T.copy();G.remove_edge(*e);return len(nx.node_connected_component(G,e[0]))
    sz={e:side(e) for e in E}
    for tri in itertools.combinations(E,3):
        for ch in itertools.product(*[(sz[e],n-sz[e]) for e in tri]): prod[sum(ch)]+=1
        G=T.copy();G.remove_edges_from(tri);comp=[frozenset(c) for c in nx.connected_components(G)];cq=nx.Graph();cq.add_nodes_from(comp);loc={v:c for c in comp for v in c}
        for a,b in tri: cq.add_edge(loc[a],loc[b])
        if max(d for _,d in cq.degree())==3:
            ctr=[c for c,d in cq.degree() if d==3][0];w=len(ctr);arms=[len(c) for c in comp if c!=ctr]
            H[w]+=1;H[w+n]+=1
            for p in arms: H[w+2*p]+=1
        else:
            ends=[c for c,d in cq.degree() if d==1];path=nx.shortest_path(cq,ends[0],ends[1]);a,b,c,d=[len(x) for x in path]
            for v in (a+c,b+d,a+2*b+c,b+2*c+d): H[v]+=1
    return prod,H
for n in range(4,12):
    for T in nx.nonisomorphic_trees(n):
        s=S3(T);p,H=formula(T);d=Counter(p);
        for k,v in H.items(): d[k+n]-=v;d[k]+=v
        d={k:v for k,v in d.items() if v};ok&=(d==dict(s));n_checked+=1
res={"trees":n_checked,"ok":bool(ok)};print(res);json.dump(res,open('idn3.json','w'))
