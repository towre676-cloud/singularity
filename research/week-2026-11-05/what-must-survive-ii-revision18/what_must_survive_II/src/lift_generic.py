# Constructive lift for k>=18: real patterns from Theorem 11's pairs and the triangle gadget; exact principal-part solve.
import sys,json
import networkx as nx
from lift import *
def skel(n3):
    return {4:nx.complete_graph(4),6:nx.circular_ladder_graph(3),8:nx.cubical_graph(),10:nx.petersen_graph(),12:nx.circular_ladder_graph(6)}[n3]
def theta(a,b,c):
    E=[];n=2
    for L in (a,b,c):
        prev=0
        for _ in range(L): E.append((prev,n));prev=n;n+=1
        E.append((prev,1))
    return n,E
def host(n3,n2,keep_uv=True,split=None):
    # simple cubic skeleton with vertex labels; n2 subdividing vertices on one edge (or split among 2), edge uv kept direct
    G=nx.convert_node_labels_to_integers(skel(n3));edges=list(G.edges());uv=edges[0]
    others=[e for e in edges if e!=uv];n=n3;out=[e for e in edges]
    alloc=[(others[0],n2)] if split is None else [(others[0],split[0]),(others[1],split[1])]
    for e,m in alloc:
        out.remove(e);prev=e[0]
        for _ in range(m): out.append((prev,n));prev=n;n+=1
        out.append((prev,e[1]))
    return n,out,uv
def norm(n,E): 
    assert len({tuple(sorted(e)) for e in E})==len(E);G=nx.Graph(E);assert nx.is_connected(G) and G.number_of_nodes()==n and min(d for _,d in G.degree())>=2 and max(d for _,d in G.degree())<=3
    return (n,len(E),tuple(E))
def g1_pair(k,E):
    n3=2*(E-k);n2=k-n3
    if n3==2:
        a=norm(*theta(n2-1,1,0));b=norm(*theta(n2-2,1,1))
    else:
        n,e,_=host(n3,n2);a=norm(n,e);n,e,_=host(n3,n2,split=(n2-1,1));b=norm(n,e)
    return a,b
def g2_pair(k,j):
    kR=k-6;n3=2*j;n2=kR-n3
    if j==1:
        n,e=theta(1,kR-3,0);uv=(0,1)
    else: n,e,uv=host(n3,n2)
    assert n==kR
    e=[x for x in e if tuple(sorted(x))!=tuple(sorted(uv))]
    o=n
    prism=[(0,1),(1,2),(0,2),(3,4),(4,5),(3,5),(1,4),(2,5)];k33=[(0,3),(0,4),(0,5),(1,3),(1,4),(1,5),(2,3),(2,4),(2,5)];k33.remove((0,3))
    A=e+[(a+o,b+o) for a,b in prism]+[(uv[0],0+o),(3+o,uv[1])]
    B=e+[(a+o,b+o) for a,b in k33]+[(uv[0],0+o),(3+o,uv[1])]
    return norm(k,A),norm(k,B)
res=[]
for k in [18,19,20,21,24,30,41]:
    tot={};deg=[];coefs=[]
    Aser=sp.expand((u-1)**(k+2)*u**3)
    P_=sp.Poly(Aser,u)
    # A(f)=f^(k+2)(1+f)^3 = sum binom(3,j) f^(k+2+j)
    for j in range(4):
        E=k+1+j;a,b=g1_pair(k,E);Ia,Ib=inv(a),inv(b);d={n:Ia[n]-Ib[n] for n in Ia};assert a[1]==b[1]==E and d["A"]!=0
        c=sp.Rational(sp.binomial(3,j),d["A"]);r=pp_of(d,E)
        for o,v in r.items(): tot[o]=tot.get(o,0)+c*v
    assert all(v==0 for o,v in tot.items() if o<-6)
    # triangle gadget at six consecutive edge counts
    ev=[]
    for j in range(1,7):
        a,b=g2_pair(k,j);Ia,Ib=inv(a),inv(b);d={n:Ia[n]-Ib[n] for n in Ia};assert a[1]==b[1] and d=={"A":0,"X":0,"Y":0,"T6":0,"T7":0,"T8":0,"T9":2},d
        ev.append((a[1],d))
    M=sp.Matrix(6,6,lambda r_,c_:pp_of(ev[c_][1],ev[c_][0]).get(-(r_+1),0));rhs=sp.Matrix([-tot.get(-(r_+1),0) for r_ in range(6)])
    sol=M.LUsolve(rhs)
    for (E,d),c in zip(ev,sol):
        for o,v in pp_of(d,E).items(): tot[o]=tot.get(o,0)+c*v
    ok=all(v==0 for v in tot.values());res.append({"k":k,"V":k+4,"pp_zero":bool(ok),"gadget_edge_counts":[e[0] for e in ev],"B_at_minus1":(-1)**k});print(res[-1],flush=True);assert ok
json.dump(res,open(sys.argv[1],'w'),indent=1)
