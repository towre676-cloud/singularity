import networkx as nx,sympy as sp,numpy as np,json,random,itertools,subprocess,math
from collections import defaultdict,Counter
import mpmath as mp
res={}
def lap(G): return np.array(nx.laplacian_matrix(G,nodelist=sorted(G)).toarray(),dtype=int)
def smith(G):
    L=sp.Matrix(lap(G).tolist())[:-1,:-1]
    from sympy.matrices.normalforms import smith_normal_form
    d=smith_normal_form(L,domain=sp.ZZ);return sorted(abs(int(d[i,i])) for i in range(L.shape[0]) if abs(d[i,i])!=1)
up=open('/root/wms/out/unsep.txt').read().strip().split('\n')
def m(l):
    w=list(map(int,l.split()));return nx.Graph([(w[2+2*i],w[3+2*i]) for i in range(w[1])])
A,B=m(up[0]),m(up[1])
x=sp.Symbol('x')
ca,cb=[sp.Matrix(nx.adjacency_matrix(g,nodelist=sorted(g)).toarray().tolist()).charpoly(x).as_expr() for g in (A,B)]
res["late_pair"]={"cospectral":bool(sp.expand(ca-cb)==0),"jac_A":smith(A),"jac_B":smith(B),"charpoly_difference":str(sp.factor(ca-cb))}
print(res["late_pair"])
def table(g,EM):
    nodes=sorted(g);ix={v:i for i,v in enumerate(nodes)};E=[(ix[a],ix[b]) for a,b in g.edges()]
    s=f"{len(nodes)} {len(E)} "+" ".join(f"{a} {b}" for a,b in E)+"\n"
    o=subprocess.run(['./cut',str(EM)],input=s,capture_output=True,text=True).stdout.split('\n')[1:]
    t={}
    for l in o:
        if l: e,v,c=map(int,l.split());t[(e,v)]=c
    return t
for nm,g in (("A",A),("B",B)): pass
ta,tb=table(A,28),table(B,28);tha,thb=Counter(),Counter()
for (e,v),c in ta.items(): tha[e]+=c
for (e,v),c in tb.items(): thb[e]+=c
ds=[e for e in sorted(set(tha)|set(thb)) if tha[e]!=thb[e]];print("late pair theta first differs at energy",ds[:3],[(tha[e],thb[e]) for e in ds[:3]])
de=sorted({k for k in set(ta)|set(tb) if ta.get(k,0)!=tb.get(k,0)})[:6];print("lowest (e,vol) differences",de)
res["late_pair"]["theta_first_diff"]=ds[:3]
# (1) factorisation against direct histogram
def direct(g,VM):
    n=len(g);nodes=sorted(g);ix={v:i for i,v in enumerate(nodes)};E=[(ix[a],ix[b]) for a,b in g.edges()];c=Counter();h=[0]*n
    def rec(i,left):
        if i==n-1:
            h[i]=left;c[(sum((h[a]-h[b])**2 for a,b in E),V)]+=1;return
        for a in range(left+1): h[i]=a;rec(i+1,left-a)
    for V in range(VM+1): rec(0,V)
    return c
ok=True
for name,g in (("K4",nx.complete_graph(4)),("K33",nx.complete_bipartite_graph(3,3)),("Petersen",nx.petersen_graph())):
    n=len(g);EM=18;VM=8 if n>6 else 12;t=table(g,EM);d=direct(g,VM)
    pred=Counter()
    for (e,v),c in t.items():
        for k in range(0,VM//n+1):
            if v+k*n<=VM: pred[(e,v+k*n)]+=c
    d={k:c for k,c in d.items() if k[0]<=EM}
    ok&=dict(pred)=={k:c for k,c in d.items()};print(name,"L=M/(1-x^n) on e<=18:",dict(pred)==d)
res["factorisation_ok"]=bool(ok)
# (2) reflection is lattice inversion: at x=zeta_n graded table symmetric g <-> -g
def graded(t,n):
    c=Counter()
    for (e,v),cc in t.items(): c[(e,v%n)]+=cc
    return c
sym=True
for g in (nx.complete_graph(4),nx.petersen_graph(),A,B):
    n=len(g);c=graded(table(g,22),n)
    sym&=all(c[(e,v)]==c[(e,(-v)%n)] for (e,v) in list(c))
res["graded_inversion_symmetric"]=bool(sym);print("graded symmetric",sym)
# (3) modular inversion with character, numeric
mp.mp.dps=30
def poisson(g,j,eps,R=9):
    nodes=sorted(g);L=sp.Matrix(lap(g).tolist())[:-1,:-1];tau=int(L.det());Li=L.inv();r=L.shape[0];n=r+1
    Lif=np.array(Li.tolist(),dtype=float)
    # direct side
    t=table(g,int(60/eps) if eps>1 else 60)
    return tau,Li
out=[]
for name,g in (("K4",nx.complete_graph(4)),("Petersen",nx.petersen_graph())):
    n=len(g);t=table(g,60 if n==4 else 34);L0=np.array(lap(g),dtype=float)[:-1,:-1];tau=round(np.linalg.det(L0));Li=np.linalg.inv(L0);r=n-1
    for j,eps in ((0,mp.mpf(1)),(1,mp.mpf(1)),(1,mp.mpf('0.7'))):
        z=mp.e**(2j*mp.pi*j/n)
        lhs=sum(c*z**v*mp.e**(-eps*e) for (e,v),c in t.items())
        # dual side via short vectors of inverse form around shift
        s=np.ones(r)*j/n
        S=mp.mpf(0)
        rng=range(-2,3)
        best=None
        for mm in itertools.product(rng,repeat=r) if r<=3 else [tuple(w) for w in small(r)] if False else []:
            d=np.array(mm)-s;val=d@Li@d;S+=mp.e**(-mp.pi**2*mp.mpf(float(val))/eps)
        if r<=3:
            rhs=(mp.pi/eps)**(mp.mpf(r)/2)/mp.sqrt(tau)*S
            out.append((name,j,float(eps),str(mp.nstr(lhs,10)),str(mp.nstr(rhs,10))))
    print(name,"tau",tau)
print(out);res["poisson_K4"]=out
# (4) Whitney twist on an explicitly asymmetric pair
def side(seed,k):
    rnd=random.Random(seed)
    while True:
        # k vertices, ports a,c have degree 2, others 3
        deg=[2,2]+[3]*(k-2);st=[v for v,d in enumerate(deg) for _ in range(d)];rnd.shuffle(st);E=set();ok=True
        for i in range(0,len(st),2):
            a,b=st[i],st[i+1]
            if a==b or (min(a,b),max(a,b)) in E: ok=False;break
            E.add((min(a,b),max(a,b)))
        if not ok: continue
        G=nx.Graph(list(E))
        if not nx.is_connected(G) or len(G)!=k: continue
        # no automorphism swapping ports
        H=G.copy();nx.set_node_attributes(H,{v:(0 if v==0 else 1 if v==1 else 2) for v in H},'c')
        H2=G.copy();nx.set_node_attributes(H2,{v:(1 if v==0 else 0 if v==1 else 2) for v in H2},'c')
        if not nx.is_isomorphic(H,H2,node_match=lambda a,b:a['c']==b['c']): return G
X=None
for s1 in range(1,400):
    X=side(s1,8);Y=side(s1+1000,8);
    G=nx.disjoint_union(X,Y);T=nx.disjoint_union(X,Y)
    G.add_edges_from([(0,8),(1,9)]);T.add_edges_from([(0,9),(1,8)])
    if not nx.is_isomorphic(G,T): break
print("twist pair nonisomorphic",not nx.is_isomorphic(G,T),len(G))
tg,tt=table(G,16),table(T,16);c1,c2=Counter(),Counter()
for (e,v),c in tg.items(): c1[e]+=c
for (e,v),c in tt.items(): c2[e]+=c
dif=sorted({k for k in set(tg)|set(tt) if tg.get(k,0)!=tt.get(k,0)})[:6]
res["twist"]={"n":len(G),"theta_equal_through_16":c1==c2,"energy_volume_first_differences":dif,"spanning_trees":[round(np.linalg.det(lap(G)[:-1,:-1].astype(float))),round(np.linalg.det(lap(T)[:-1,:-1].astype(float)))]};print(res["twist"])
gr=graded(tg,16),graded(tt,16);res["twist"]["graded_equal"]=gr[0]==gr[1];print("graded equal",gr[0]==gr[1])
# (5) binary truncation below 2*lambda
ok2=True
json.dump(res,open('st.json','w'),indent=1,default=str)
