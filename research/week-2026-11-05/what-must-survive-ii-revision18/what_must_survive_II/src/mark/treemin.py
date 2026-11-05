import networkx as nx,subprocess,json
from collections import defaultdict
exec(open('trees.py').read().split("for n in range(4")[0].split("res={}")[1])
out={}
for n in (10,12,14,16,18):
    Ts=list(nx.nonisomorphic_trees(n));o=subprocess.run(['./tree','7'],input="\n".join(enc(T) for T in Ts)+"\n",capture_output=True,text=True).stdout.strip().split('\n')
    rows=[l.split() for l in o];row={}
    for V in range(1,8):
        g=defaultdict(int)
        for w in rows: g[tuple(w[1:V+2])+tuple(w[9:9+V+1])]+=1
        row[V]=sum(c-1 for c in g.values())
    out[n]={"trees":len(Ts),"unseparated_through_volume":row};print(n,out[n],flush=True)
json.dump(out,open('treemin.json','w'),indent=1)
