import networkx as nx,sympy as sp,itertools,json,warnings
warnings.filterwarnings("ignore")
from collections import Counter
x=sp.Symbol('x');res={"checked":0}
def shell(T,EM=2):
    r=0;E=list(nx.bfs_edges(T,r));n=len(T);order=[r]+[w for u,w in E];par={w:u for u,w in E};t={1:Counter(),2:Counter()}
    def rec(i,h,left):
        if i==n:
            vals=list(h.values());
            if EM-left>0: t[EM-left][sum(vals)-n*min(vals)]+=1
            return
        v=order[i]
        for z in (-1,0,1):
            if z*z<=left:
                h[v]=h[par[v]]+z;rec(i+1,h,left-z*z)
    rec(1,{r:0},EM);return t
def split(T):
    n=len(T);A=Counter();E=list(T.edges())
    for e in E:
        H=T.copy();H.remove_edge(*e);c=len(nx.node_connected_component(H,e[0]));A[c]+=1;A[n-c]+=1
    B=Counter()
    for e,f in itertools.combinations(E,2):
        H=T.copy();H.remove_edges_from([e,f]);comp=list(nx.connected_components(H));b=[c for c in comp if (e[0] in c or e[1] in c) and (f[0] in c or f[1] in c)][0];B[len(b)]+=1
    return A,B
ok=True
for n in range(3,13):
    for T in nx.nonisomorphic_trees(n):
        t=shell(T);A,B=split(T);P=lambda c:sum(v*x**k for k,v in c.items())
        Ae=P(A);lhs=P(t[2]);rhs=(Ae**2-Ae.subs(x,x**2))/2-(n-1)*x**n+(1-x**n)*P(B)
        assert sp.expand(P(t[1])-Ae)==0
        ok&=sp.expand(lhs-rhs)==0;res["checked"]+=1
res["identity_ok"]=bool(ok);print(res);json.dump(res,open('idn.json','w'))
