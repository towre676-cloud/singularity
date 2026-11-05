import networkx as nx,itertools,json,sympy as sp,warnings
warnings.filterwarnings("ignore")
from collections import Counter,defaultdict
def AB(T):
    n=len(T);r=0;E=list(nx.bfs_edges(T,r));order=[r]+[w for u,w in E];par={w:u for u,w in E}
    sz={v:1 for v in T}
    for v in reversed(order[1:]): sz[par[v]]+=sz[v]
    A=Counter();B=Counter();N=Counter()
    for v in order[1:]: A[sz[v]]+=1;A[n-sz[v]]+=1
    # ancestors
    anc={r:set()}
    for v in order[1:]: anc[v]=anc[par[v]]|{par[v]}
    ed=order[1:]
    for e,f in itertools.combinations(ed,2):
        if e in anc[f]: a,c=n-sz[e],sz[f]; b=sz[e]-sz[f]
        elif f in anc[e]: a,c=n-sz[f],sz[e]; b=sz[f]-sz[e]
        else: a,c=sz[e],sz[f]; b=n-a-c
        B[b]+=1;N[abs(a-c)]+=1
    return A,B,N
key=lambda c:tuple(sorted(c.items()))
def spine_len(T):
    return sum(1 for v in T if T.degree(v)>1)
def is_cat(T):
    H=T.subgraph([v for v in T if T.degree(v)>1])
    return len(H)<=1 or max(d for _,d in H.degree())<=2
res={}
# 1. all-tree scope: do short caterpillars collide with ANY tree at A,B?
rows=[];ex7=None
for n in range(3,21):
    g=defaultdict(list)
    for T in nx.nonisomorphic_trees(n):
        A,B,N=AB(T);g[(key(A),key(B))].append((is_cat(T),spine_len(T) if is_cat(T) else None,T.edges() if 0 else None))
    cc=sum(1 for v in g.values() if len(v)>1)
    catmix=[[ (c,s) for c,s,_ in v] for v in g.values() if len(v)>1 and any(c for c,_,_ in v)]
    short=[v for v in catmix if any(c and s<=4 for c,s in v)]
    rows.append((n,cc,len(catmix),len(short),catmix[:3]));print(rows[-1],flush=True)
    if n>=17: pass
res['all_tree']=rows
json.dump(res,open('chk1.json','w'),default=str)
