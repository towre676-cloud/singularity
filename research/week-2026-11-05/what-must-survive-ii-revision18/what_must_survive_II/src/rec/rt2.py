import networkx as nx,warnings
warnings.filterwarnings("ignore")
from collections import defaultdict,Counter
exec(open('rs.py').read().split("out={}")[0])
st=Counter();exs=[]
for m,nmax in ((4,26),(5,24),(6,22),(7,20)):
    shapes=list(nx.nonisomorphic_trees(m))
    for n in range(m+2,nmax+1):
        cl=defaultdict(lambda:[[],[]])
        for I in shapes:
            I=nx.convert_node_labels_to_integers(I);S=setup(I);c=max(d for _,d in I.degree())<=2
            lo=[1 if I.degree(v)==1 else 0 for v in range(m)]
            for p in comps(n-m,m,lo):
                a,b=sig(S,p);cl[a][0 if c else 1].append((sum(x*x for x in deg(I,p)),p,tuple(I.edges())))
        for v in cl.values():
            if v[0] and v[1]:
                a2=[z[0] for z in v[0]];b2=[z[0] for z in v[1]]
                st['mixA']+=1
                st['non>maxcat']+=min(b2)>max(a2)
                st['non>=mincat']+=min(b2)>=min(a2)
                st['non>mincat']+=min(b2)>min(a2)
                if min(b2)<=min(a2) and len(exs)<5:
                    exs.append((n,min(v[0]),min(v[1])))
    print(m,dict(st),flush=True)
print(exs)
