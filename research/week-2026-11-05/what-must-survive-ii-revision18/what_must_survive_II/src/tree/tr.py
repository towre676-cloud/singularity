import networkx as nx,subprocess,json,itertools,sys,warnings
warnings.filterwarnings("ignore")
from collections import Counter,defaultdict
res={}
def enc(T):
    order=[0]+[v for u,v in nx.bfs_edges(T,0)];ix={v:i for i,v in enumerate(order)};par=[0]*len(order)
    for u,v in nx.bfs_edges(T,0): par[ix[v]]=ix[u]
    return f"{len(order)} "+" ".join(map(str,par))
def table(T,E):
    o=subprocess.run(['./shell',str(E),'p'],input=enc(T)+"\n",capture_output=True,text=True).stdout.strip().split('\n')[1:];t=defaultdict(Counter)
    for l in o:
        e,v,c=map(int,l.split());t[e][v]=c
    return t
def profiles(T):
    n=len(T);out=[]
    for r in T:
        size={};
        for v in reversed([r]+[w for u,w in nx.bfs_edges(T,r)]):
            size[v]=1+sum(size[w] for w in T[v] if size.get(w) is not None and w in size and nx.shortest_path_length(T,r,w)>nx.shortest_path_length(T,r,v)) if False else None
        par={w:u for u,w in nx.bfs_edges(T,r)};sz=Counter({v:1 for v in T})
        for v in reversed([w for u,w in nx.bfs_edges(T,r)]): sz[par[v]]+=sz[v]
        out.append(tuple(sorted(sz[v] for v in T if v!=r)))
    return out
# (A) two-edge shell formula
ok=True;tested=0
for n in range(5,11):
    for T in nx.nonisomorphic_trees(n):
        t=table(T,2);pred=Counter();E=list(T.edges())
        for e,f in itertools.combinations(E,2):
            H=T.copy();H.remove_edges_from([e,f]);comp=list(nx.connected_components(H));b=[c for c in comp if (e[0] in c or e[1] in c) and (f[0] in c or f[1] in c)][0];a,c=[len(x) for x in comp if x is not b];b=len(b)
            for v in (b,a+c,2*a+b,b+2*c): pred[v]+=1
        tested+=1;ok&=(dict(pred)==dict(t[2]))
res["two_edge_formula"]={"trees":tested,"ok":bool(ok)};print(res["two_edge_formula"])
# (B) first separating shell by order
tab={}
for n in range(6,int(sys.argv[1])+1):
    Ts=list(nx.nonisomorphic_trees(n));pending=[list(range(len(Ts)))];hist={}
    for E in range(1,9):
        if not pending or E*1>9: break
        sub=[i for g in pending for i in g]
        o=subprocess.run(['./shell',str(E)],input="\n".join(enc(Ts[i]) for i in sub)+"\n",capture_output=True,text=True).stdout.strip().split('\n');fp=dict(zip(sub,o));new=[]
        for g in pending:
            b=defaultdict(list)
            for i in g: b[fp[i]].append(i)
            new+=[v for v in b.values() if len(v)>1]
        pending=new;hist[E]=sum(len(v)-1 for v in pending)
        if sum(len(v) for v in pending)>3000 and E>=5: break
    tab[n]={"trees":len(Ts),"unseparated_through_energy":hist};print(n,tab[n],flush=True)
res["shell_separation"]=tab
# (C) is the multiset of rooted profiles complete?
pc={}
for n in range(4,int(sys.argv[2])+1):
    g=defaultdict(list)
    for T in nx.nonisomorphic_trees(n): g[tuple(sorted(profiles(T)))].append(T)
    col=[v for v in g.values() if len(v)>1];pc[n]={"collision_classes":len(col),"graphs":sum(len(v) for v in col)}
    if col and "example" not in res: res["example"]=[list(x.edges()) for x in col[0][:2]]
    print("profiles",n,pc[n],flush=True)
res["profile_completeness"]=pc
json.dump(res,open('tr.json','w'),indent=1)
