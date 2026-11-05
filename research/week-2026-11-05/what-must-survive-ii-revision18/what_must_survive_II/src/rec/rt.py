import networkx as nx,json,warnings
warnings.filterwarnings("ignore")
from collections import defaultdict,Counter
exec(open('rs.py').read().split("out={}")[0])
st=Counter();exs=[]
for m,nmax in ((4,30),(5,28),(6,26),(7,23),(8,20)):
    shapes=list(nx.nonisomorphic_trees(m))
    for n in range(m+2,nmax+1):
        cl=defaultdict(lambda:[[],[]])
        for I in shapes:
            I=nx.convert_node_labels_to_integers(I);S=setup(I);c=max(d for _,d in I.degree())<=2
            lo=[1 if I.degree(v)==1 else 0 for v in range(m)]
            for p in comps(n-m,m,lo):
                d=deg(I,p);cl[sig(S,p)][0 if c else 1].append(d)
        for v in cl.values():
            if v[0] and v[1]:
                f=lambda D,k:sum(x**k for x in D)
                a2=[f(d,2) for d in v[0]];b2=[f(d,2) for d in v[1]]
                st[('mix',m)]+=1
                if min(b2)>max(a2):st[('non>cat all',m)]+=1
                elif max(b2)<min(a2):st[('non<cat all',m)]+=1
                else:
                    st[('overlap',m)]+=1
                    if len(exs)<8:exs.append((m,n,sorted(set(v[0]))[:2],sorted(set(v[1]))[:2]))
                if set(v[0])&set(v[1]):st[('EQUAL DEG',m)]+=1
    print(m,dict(st),flush=True)
print(exs)
