import networkx as nx,math,json,warnings
warnings.filterwarnings("ignore")
from collections import Counter
def profiles(T):
    out=[]
    for r in T:
        E=list(nx.bfs_edges(T,r));par={w:u for u,w in E};sz=Counter({v:1 for v in T})
        for u,w in reversed(E): sz[u]+=sz[w]
        out.append(tuple(sorted(sz[v] for v in T if v!=r)))
    return out
def theta(y,q,R=40): return sum(y**z*q**(z*z) for z in range(-R,R+1))
out=[]
for name,T in (("path5",nx.path_graph(5)),("star5",nx.star_graph(4))):
    n=len(T);q=0.35;prof=profiles(T);E=list(nx.bfs_edges(T,0));ord_=[0]+[w for u,w in E];par={w:u for u,w in E};rho=[sum(s*s for s in p) for p in prof];top=max(rho)
    for X in (1.5,3.0,6.0,12.0,24.0):
        tot=0.0;h={0:0};Z=range(-16,17)
        wz={z:q**(z*z) for z in Z}
        def rec(i,w):
            global tot
            if i==n:
                vals=list(h.values());tot+=w*X**(sum(vals)-n*min(vals));return
            v=ord_[i]
            for z in Z:
                h[v]=h[par[v]]+z;rec(i+1,w*wz[z])
        rec(1,1.0)
        F=sum(math.prod(theta(X**s,q) for s in p) for p,r in zip(prof,rho) if r==top)
        out.append({"tree":name,"x":X,"ratio":tot/F,"top_vertices":sum(r==top for r in rho)});print(out[-1],flush=True)
json.dump(out,open('prod.json','w'),indent=1)
