import networkx as nx,subprocess,json,warnings
warnings.filterwarnings("ignore")
from collections import defaultdict
exec(open('tr.py').read().split("# (A) two-edge")[0].split("res={}")[1])
Ts=list(nx.nonisomorphic_trees(18));o=subprocess.run(['./shell','3'],input="\n".join(enc(T) for T in Ts)+"\n",capture_output=True,text=True).stdout.strip().split('\n');g=defaultdict(list)
for i,l in enumerate(o): g[tuple(l.split()[2:5])].append(i)
left=[v for v in g.values() if len(v)>1];r=[]
for v in left:
    a=[subprocess.run(['./shell','4'],input=enc(Ts[i])+"\n",capture_output=True,text=True).stdout.split()[1:] for i in v];r.append((len(v),len({tuple(x) for x in a})==len(v)))
print(r);json.dump(r,open('rest.json','w'))
