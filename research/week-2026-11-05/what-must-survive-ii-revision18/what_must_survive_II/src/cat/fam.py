import sympy as sp,json,networkx as nx,itertools,warnings,subprocess
warnings.filterwarnings("ignore")
from collections import defaultdict
s=sp.Symbol('s')
def data(p):
    # returns S1 and B as dict (alpha,beta)->coefficient polynomial in s, for exponent alpha*s+beta
    n=sp.expand(len(p)+sum(p));m=len(p);a=[];t=0
    for i in range(m-1): t=sp.expand(t+1+p[i]);a.append(t)
    ell=sp.expand(sum(p));S1=defaultdict(lambda:sp.Integer(0));B=defaultdict(lambda:sp.Integer(0))
    key=lambda e:(sp.Poly(e,s).coeff_monomial(s),sp.Poly(e,s).coeff_monomial(1))
    def add(D,e,c): D[key(sp.expand(e))]+=c
    for t in a: add(S1,t,1);add(S1,n-t,1)
    add(S1,1,ell);add(S1,n-1,ell)
    for i,j in itertools.combinations(range(m-1),2): add(B,a[j]-a[i],1)
    for i,t in enumerate(a):
        L=sp.expand(t-i-1);add(B,t-1,L);add(B,n-t-1,ell-L)
    add(B,n-2,sp.expand(ell*(ell-1)/2))
    return {k:sp.expand(v) for k,v in S1.items() if sp.expand(v)!=0},{k:sp.expand(v) for k,v in B.items() if sp.expand(v)!=0},n
P=[s,s+1,s-1,2*s+1,s+2];Q=[s,2*s+1,s+1,s-1,s+2]
a=data(P);b=data(Q);print("S1 equal",a[0]==b[0],"B equal",a[1]==b[1],"n",a[2],b[2]);res={"family":"p=[s,s+1,s-1,2s+1,s+2], p'=[s,2s+1,s+1,s-1,s+2], n=6s+8","S1_equal":a[0]==b[0],"B_equal":a[1]==b[1]}
def build(p):
    G=nx.path_graph(len(p));k=len(p)
    for i,c in enumerate(p):
        for _ in range(c): G.add_edge(i,k);k+=1
    return G
def enc(T):
    E=list(nx.bfs_edges(T,0));order=[0]+[v for u,v in E];ix={v:i for i,v in enumerate(order)};par=[0]*len(order)
    for u,v in E: par[ix[v]]=ix[u]
    return f"{len(order)} "+" ".join(map(str,par))
rows=[]
for v in (1,2,3):
    pa=[int(e.subs(s,v)) for e in P];qa=[int(e.subs(s,v)) for e in Q]
    A,Bg=build(pa),build(qa);assert not nx.is_isomorphic(A,Bg)
    o=subprocess.run(['/root/wms/tree/shell','3','p'],input=enc(A)+"\n",capture_output=True,text=True).stdout.strip().split('\n')[1:];o2=subprocess.run(['/root/wms/tree/shell','3','p'],input=enc(Bg)+"\n",capture_output=True,text=True).stdout.strip().split('\n')[1:]
    def T(o):
        t=defaultdict(int)
        for l in o:
            e,V,c=map(int,l.split());t[(e,V)]=c
        return t
    ta,tb=T(o),T(o2);d={k:ta[k]-tb[k] for k in set(ta)|set(tb) if ta[k]!=tb[k]}
    rows.append({"s":v,"shells_differing":sorted({k[0] for k in d}),"lowest":sorted(d.items())[:6],"degree_differ":sorted(dict(A.degree()).values())!=sorted(dict(Bg.degree()).values())});print(rows[-1])
res["rows"]=rows;json.dump(res,open('fam.json','w'),indent=1,default=str)
