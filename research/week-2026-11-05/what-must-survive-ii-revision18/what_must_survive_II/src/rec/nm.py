import networkx as nx,warnings,json
warnings.filterwarnings("ignore")
from collections import defaultdict,Counter
exec(open('rs.py').read().split("out={}")[0])
def NN(st,p):
    m,o,par,sub,rel=st;n=m+sum(p);s={v:sum(1+p[u] for u in sub[v]) for v in o[1:]};c=Counter()
    # orient to small side: nest pairs from root at centroid
    return s
# N computed relative to centroid via folded sizes on full tree structure
def Nmat(I,p):
    n=len(I)+sum(p);w={v:1+p[v] for v in I}
    def sizes(r):
        E=list(nx.bfs_edges(I,r));o=[r]+[b for a,b in E];par={b:a for a,b in E};s=dict(w)
        for v in reversed(o[1:]):s[par[v]]+=s[v]
        return o,par,s
    o,par,s=sizes(0);c=min(I,key=lambda v:max([s[u] for u in I[v] if par.get(u)==v]+[n-s[v]]))
    o,par,s=sizes(c);N=Counter()
    for v in o[1:]:
        u=par[v]
        while u!=c:
            if 2*s[u]!=n:N[(s[u],s[v])]+=1
            u=par[u]
    return tuple(sorted(N.items()))
st=Counter()
for m,nmax in ((4,34),(5,30),(6,27),(7,24),(8,22)):
    shapes=list(nx.nonisomorphic_trees(m))
    for n in range(m+2,nmax+1):
        cl=defaultdict(lambda:[[],[]])
        for I in shapes:
            I=nx.convert_node_labels_to_integers(I);S=setup(I);c=max(d for _,d in I.degree())<=2
            lo=[1 if I.degree(v)==1 else 0 for v in range(m)]
            for p in comps(n-m,m,lo):cl[sig(S,p)][0 if c else 1].append((I,tuple(p)))
        for v in cl.values():
            if v[0] and v[1]:
                a={Nmat(*z) for z in v[0]};b={Nmat(*z) for z in v[1]}
                st['classes']+=1
                ok=all(y in a for y in b);st['every noncat N equals a cat N']+=ok
                st['all equal']+=len(a|b)==1
                if not ok:print('N DIFF',m,n,v[0][0][1],v[1][0][1],flush=True)
    print(m,nmax,dict(st),flush=True)
json.dump(dict(st),open('nm.json','w'))
