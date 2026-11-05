# Independent of the closed forms: every shell-2 collision through n=18 by direct sign enumeration, compare top of Delta[q^3]M
import itertools,networkx as nx
from collections import Counter
exec(open("mf.py").read().split("\nif __name__")[0])
def cat(p):
    G=nx.path_graph(len(p));k_=len(p)
    for i,c in enumerate(p):
        for _ in range(c):G.add_edge(i,k_);k_+=1
    return G
def S3(T):
    n=len(T);E=list(nx.bfs_edges(T,0));o=[0]+[w for u,w in E];par={w:u for u,w in E};c=Counter()
    for F in itertools.combinations(o[1:],3):
        for sg in itertools.product((-1,1),repeat=3):
            z=dict(zip(F,sg));h_={0:0}
            for v in o[1:]:h_[v]=h_[par[v]]+z.get(v,0)
            vals=list(h_.values());c[sum(vals)-n*min(vals)]+=1
    return c
ok=tot=0
for n in (11,14,17,18):
    for l in open(f'/root/wms/spine/d{n}.txt'):
        if not l.startswith('S2'):continue
        ps=[tuple(map(int,a.strip(',').split(','))) for a in l.split()[1:]];N=n-2
        T1,T2=T_of(ps[0])[0],T_of(ps[1])[0];s1,s2=spins(T1,N),spins(T2,N);ks=sorted(s1);r1=ks[0]
        Z=[a for a in ks if s1[a]!=s2[a]]
        if r1 in Z:Z=[a for a in ks if a not in Z]
        q=Z[0];nu=sum(1 for r in folds(T1,N) if r<r1)
        a=S3(cat(ps[0]));a.subtract(S3(cat(ps[1])));d={k_:v for k_,v in a.items() if v}
        tot+=1;ok+=max(d)==3*n-3-q-r1 and 2*d[max(d)]==s1[r1]*s1[q]*(2*r1-nu)
print('direct enumeration top term',ok,tot)
