# For shell-3 survivor pairs: is S obtained from T by swapping sets of hanging arms between 2 vertices u,v?
import subprocess,collections,itertools,networkx as nx,json,sys,warnings
warnings.filterwarnings("ignore")
def parse(I):
    v=list(map(int,I.split()));return nx.Graph([(i,v[1+i]) for i in range(1,v[0])])
def swaps(T,S):
    res=[]
    for u,v in itertools.combinations(T,2):
        P=nx.shortest_path(T,u,v);du=[w for w in T[u] if w!=P[1]];dv=[w for w in T[v] if w!=P[-2]]
        if len(du)>7 or len(dv)>7:continue
        def comp(root,par):
            H=T.copy();H.remove_edge(root,par);return nx.node_connected_component(H,par)
        for r in range(0,len(du)+1):
            for Cu in itertools.combinations(du,r):
                for r2 in range(0,len(dv)+1):
                    if r==0 and r2==0:continue
                    for Cv in itertools.combinations(dv,r2):
                        wu=sum(len(comp(u,c)) for c in Cu);wv=sum(len(comp(v,c)) for c in Cv)
                        G=T.copy()
                        for c in Cu:G.remove_edge(u,c);G.add_edge(v,c)
                        for c in Cv:G.remove_edge(v,c);G.add_edge(u,c)
                        if nx.faster_could_be_isomorphic(G,S) and nx.is_isomorphic(G,S):
                            res.append(dict(dist=len(P)-1,wu=wu,wv=wv,nu=r,nv=r2))
    return res
out={}
for n in (16,17,18,19):
    inp=subprocess.run(['python3','/root/wms/cat/genp.py',str(n)],capture_output=True,text=True).stdout
    o=subprocess.run(['/root/wms/tree/shell','3'],input=inp,capture_output=True,text=True).stdout.strip().split('\n');I=inp.strip().split('\n')
    cl=collections.defaultdict(list)
    for L,i in zip(o,I):cl[tuple(L.split()[1:])].append(i)
    col=[v for v in cl.values() if len(v)>1];c=collections.Counter();ex=None
    for v in col:
        r=swaps(parse(v[0]),parse(v[1]))
        if r:
            best=min(r,key=lambda d:(d['dist'],d['wu']+d['wv']));c[(best['dist'],best['wu'],best['wv'])]+=1
        else:c['none']+=1
    print(n,len(col),dict(c),flush=True);out[n]={str(k):z for k,z in c.items()}
json.dump(out,open('sw.json','w'))
