import networkx as nx,itertools,warnings,json
warnings.filterwarnings("ignore")
from collections import Counter
exec(open('mx.py').read().split("res={}")[0].replace("import networkx as nx,itertools,json,warnings,sys",""))
def arm(G,par,size,kids,nxt):
    v=nxt[0];nxt[0]+=1;G.add_edge(par,v)
    used=1+sum(k[0] for k in kids)
    for k in kids:arm(G,v,k[0],k[1],nxt)
    for _ in range(size-used):
        G.add_edge(v,nxt[0]);nxt[0]+=1
    return v
D,E,a,b=13,6,2,3
def build(forest,n):
    G=nx.Graph();nxt=[1]
    for s,k in forest:arm(G,0,s,k,nxt)
    u=n-nxt[0]
    return G
S=build([(D,[]),(D,[(E,[]),(E,[(a,[]),(b,[])])])],27)
T=build([(D,[(E,[(a,[])])]),(D,[(E,[(b,[])])])],27)
print(len(S),len(T),is_cat(T),is_cat(S))
print('A,B equal',AB2(T)==AB2(S),'branches',sum(1 for _,d in S.subgraph([v for v in S if S.degree(v)>1]).degree() if d>=3))
ds=lambda G:sum(d*d for _,d in G.degree())
print('sum d^2 diff',ds(S)-ds(T))
# all caterpillars with same folded cuts
n=27;folds=[13,13,6,6,2,3]
cats=[]
seen=set()
for sg in itertools.product((0,1),repeat=6):
    pos=sorted(f if z==0 else n-f for f,z in zip(folds,sg))
    if len(set(pos))<6:continue
    gaps=[pos[0]]+[pos[i+1]-pos[i] for i in range(5)]+[n-pos[-1]]
    p=[gaps[0]-1]+[g-1 for g in gaps[1:-1]]+[gaps[-1]-1]
    if p[0]<1 or p[-1]<1 or min(p)<0:continue
    key_=min(tuple(p),tuple(p[::-1]))
    if key_ in seen:continue
    seen.add(key_)
    G=nx.path_graph(len(p));k=len(p)
    for i,c in enumerate(p):
        for _ in range(c):G.add_edge(i,k);k+=1
    if AB2(G)==AB2(S):cats.append(G);print('cat',key_)
print('cats in class',len(cats),'one exchange from any',any(exch(G,S) for G in cats))
print(sorted(d for _,d in T.degree())[-7:],sorted(d for _,d in S.degree())[-7:])
