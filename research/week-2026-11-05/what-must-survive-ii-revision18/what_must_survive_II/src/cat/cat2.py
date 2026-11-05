# Caterpillar classes: which extra data separates the S1,S2 collisions? Exact tables on order<=23 collisions via direct computation.
import subprocess,json,itertools,sys,networkx as nx,warnings
warnings.filterwarnings("ignore")
from collections import Counter,defaultdict
def build(p):
    G=nx.path_graph(len(p));k=len(p)
    for i,c in enumerate(p):
        for _ in range(c): G.add_edge(i,k);k+=1
    return G
def enc(T):
    E=list(nx.bfs_edges(T,0));order=[0]+[v for u,v in E];ix={v:i for i,v in enumerate(order)};par=[0]*len(order)
    for u,v in E: par[ix[v]]=ix[u]
    return f"{len(order)} "+" ".join(map(str,par))
def comps(n):
    def gen(left,cur):
        if left==0:
            if len(cur)>=2 and cur[0]>=1 and cur[-1]>=1 and tuple(cur[::-1])>=tuple(cur): yield tuple(cur)
            return
        for x in range(left):
            yield from gen(left-x-1,cur+[x])
    yield from gen(n,[])
out={}
for n in (11,14,17,18,20):
    L=list(comps(n));lines="\n".join(enc(build(p)) for p in L)+"\n"
    o=subprocess.run(['/root/wms/tree/shell','3'],input=lines,capture_output=True,text=True).stdout.strip().split('\n');w=[l.split() for l in o]
    def degsig(p):
        G=build(p);d=dict(G.degree());return (tuple(sorted(d.values())),tuple(sorted(d[u]+d[v] for u,v in G.edges())))
    g=defaultdict(list)
    for i,x in enumerate(w): g[tuple(x[2:4])].append(i)
    col=[v for v in g.values() if len(v)>1];d=0;s3=0
    for v in col:
        if len({degsig(L[i]) for i in v})==len(v): d+=1
        if len({w[i][4] for i in v})==len(v): s3+=1
    both=0
    for v in col:
        if len({(degsig(L[i]),w[i][4]) for i in v})==len(v): both+=1
    out[n]={"caterpillars":len(L),"S1S2_collision_classes":len(col),"fully_split_by_D_J":d,"fully_split_by_S3":s3,"split_by_either":both,"examples":[[L[i] for i in v] for v in col[:3]]};print(n,{k:v for k,v in out[n].items() if k!='examples'},out[n]['examples'][:2],flush=True)
json.dump(out,open('cat2.json','w'),indent=1)
