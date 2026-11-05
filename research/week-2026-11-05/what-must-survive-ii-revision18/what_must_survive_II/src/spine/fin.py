import json,random,itertools,networkx as nx,warnings
warnings.filterwarnings("ignore")
from collections import Counter
src=open('v.py').read()
exec(src.split("# seven-vertex")[0])
exec(open('m.py').read().split("# family top difference via H3")[1].split("rows=[]")[0])
out={}
# H3 formula vs direct shell on random caterpillars
ok=True;cnt=0
for _ in range(120):
    m=random.randint(2,6);p=[random.randint(0,3) for _ in range(m)];p[0]=max(1,p[0]);p[-1]=max(1,p[-1])
    n=m+sum(p)
    if n>13:continue
    T=cat(p);d=S(T,3);A,B,_=AB(T)
    # product term
    prod=Counter();sz=[]
    for u,v in T.edges():
        G=T.copy();G.remove_edge(u,v);sz.append(len(nx.node_connected_component(G,u)))
    for tri in itertools.combinations(sz,3):
        for ch in itertools.product(*[(s,n-s) for s in tri]):prod[sum(ch)]+=1
    H=H3(p);tot=Counter(prod)
    for k,v in H.items():tot[k]+=v;tot[k+n]-=v
    ok&=({k:v for k,v in tot.items() if v}=={k:v for k,v in d[3].items() if v});cnt+=1
out['H3_vs_direct']=dict(cases=cnt,ok=bool(ok));print(out)
# linked marginals
okl=True;tested=0
for n in range(3,14):
    g={}
    for T in nx.nonisomorphic_trees(n):
        A,B,N=AB(T);k=key(A);sig=Counter(B);sig.update(N)
        if k in g:okl&=g[k]==sig;tested+=1
        g[k]=sig
out['linked']=dict(comparisons=tested,ok=bool(okl));print(out['linked'])
# first separating volume over all shell-2 caterpillar classes through 20
hist=Counter()
for n in (11,14,17,18,20):
    for l in open(f'd{n}.txt'):
        if not l.startswith('S2'):continue
        ps=[tuple(map(int,x.strip(',').split(','))) for x in l.split()[1:]]
        G,H_=cat(ps[0]),cat(ps[1]);a,b=vol(G),vol(H_);f=next((V for V in (1,2,3,4) if a[V]!=b[V]),None);hist[(n,f)]+=1
out['first_volume']={f"{k[0]},{k[1]}":v for k,v in sorted(hist.items(),key=str)};print(out['first_volume'])
json.dump(out,open('fin.json','w'),indent=1)
