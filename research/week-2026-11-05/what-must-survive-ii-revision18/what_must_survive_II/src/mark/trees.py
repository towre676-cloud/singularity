import networkx as nx,subprocess,sys,json
from collections import defaultdict
res={}
def enc(T):
    order=list(nx.bfs_tree(T,0));ix={v:i for i,v in enumerate(order)};par=[0]*len(order);P=dict(nx.bfs_predecessors(T,0))
    for v in order[1:]: par[ix[v]]=ix[P[v]]
    return f"{len(order)} "+" ".join(map(str,par))
for n in range(int(sys.argv[3]),int(sys.argv[1])+1):
    Ts=list(nx.nonisomorphic_trees(n));inp="\n".join(enc(T) for T in Ts)+"\n"
    V0=7;groups=[list(range(len(Ts)))];hist={};pending=[list(range(len(Ts)))]
    ptr=0
    while pending and V0<=int(sys.argv[2]):
        sub=[i for g in pending for i in g]
        o=subprocess.run(['./tree',str(V0)],input="\n".join(enc(Ts[i]) for i in sub)+"\n",capture_output=True,text=True).stdout.strip().split('\n')
        fp=dict(zip(sub,o));new=[]
        for g in pending:
            b=defaultdict(list)
            for i in g: b[fp[i]].append(i)
            new+= [v for v in b.values() if len(v)>1]
        pending=new;hist[V0]=sum(len(v)-1 for v in pending)
        V0+=3 if V0<16 else 4
    res[n]={"trees":len(Ts),"unseparated_after_V0":hist,"left":[[list(Ts[i].edges()) for i in g] for g in pending][:3]}
    print(n,len(Ts),hist,flush=True)
json.dump(res,open('trees.json','w'),indent=1)
