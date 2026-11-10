# Trees with internal tree on m vertices, any pendant counts (internal leaves >=1): classes under (A,B); report any class mixing caterpillars and non-caterpillars with equal degree multiset, and shell 3 agreement.
import networkx as nx,itertools,sys,json,warnings
warnings.filterwarnings("ignore")
from collections import defaultdict,Counter
def setup(I):
    m=len(I);E=list(nx.bfs_edges(I,0));o=[0]+[w for u,w in E];par={w:u for u,w in E}
    sub={v:{v} for v in I}
    for v in reversed(o[1:]):sub[par[v]]|=sub[v]
    # pair relation for internal edges (identified by child v)
    rel=[]
    for e,f in itertools.combinations(o[1:],2):
        if f in sub[e]:rel.append((e,f,0))
        elif e in sub[f]:rel.append((f,e,0))
        else:rel.append((e,f,1))
    return m,o,par,sub,rel
def sig(st,p):
    m,o,par,sub,rel=st;n=m+sum(p);ell=sum(p);s={}
    for v in o[1:]:
        s[v]=sum(1+p[u] for u in sub[v])
    A=Counter();B=Counter()
    for v in o[1:]:
        t=s[v];A[min(t,n-t)]+=1
        pin=t-len(sub[v]);B[t-1]+=pin;B[n-t-1]+=ell-pin
    for e,f,k in rel:
        B[s[e]-s[f] if k==0 else n-s[e]-s[f]]+=1
    B[n-2]+=ell*(ell-1)//2
    return tuple(sorted(A.items())),tuple(sorted((a,b) for a,b in B.items() if b))
def deg(I,p):return tuple(sorted(I.degree(v)+p[v] for v in I))
def comps(total,m,lo):
    def rec(i,left,cur):
        if i==m-1:
            if left>=lo[i]:yield cur+[left]
            return
        for x in range(lo[i],left+1):yield from rec(i+1,left-x,cur+[x])
    yield from rec(0,total,[])
out={}
for m,nmax in ((4,44),(5,38),(6,32),(7,26)):
    shapes=list(nx.nonisomorphic_trees(m))
    for n in range(m+2,nmax+1):
        cl=defaultdict(lambda:[set(),set()])
        for I in shapes:
            I=nx.convert_node_labels_to_integers(I);st=setup(I);c=max(d for _,d in I.degree())<=2
            lo=[1 if I.degree(v)==1 else 0 for v in range(m)]
            for p in comps(n-m,m,lo):
                k=sig(st,p);cl[k][0 if c else 1].add(deg(I,p))
        mix=[v for v in cl.values() if v[0] and v[1]];same=[v for v in mix if v[0]&v[1]]
        out[(m,n)]=(len(mix),len(same))
        if same:print('DEGREE-EQUAL MIX',m,n,len(same),list(same[0][0]&same[0][1])[:1],flush=True)
    tot=sum(v[0] for k,v in out.items() if k[0]==m);sm=sum(v[1] for k,v in out.items() if k[0]==m)
    print('m',m,'nmax',nmax,'mixed classes',tot,'degree equal',sm,flush=True)
json.dump({f"{k}":v for k,v in out.items()},open('rs.json','w'))
