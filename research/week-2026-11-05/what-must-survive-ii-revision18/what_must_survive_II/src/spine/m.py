import sympy as sp,itertools,json
from collections import Counter
# C's short spine claim: exact, among caterpillars
def AB(p):
    n=len(p)+sum(p);m=len(p);a=[];t=0;l=0;ell=sum(p);A=Counter();B=Counter()
    Ls=[]
    for i in range(m-1):
        t+=1+p[i];l+=p[i];a.append(t);Ls.append(l)
    for i,t in enumerate(a):
        A[t]+=1;A[n-t]+=1;B[t-1]+=Ls[i];B[n-t-1]+=ell-Ls[i]
    A[1]+=ell;A[n-1]+=ell
    for i,j in itertools.combinations(range(m-1),2):B[a[j]-a[i]]+=1
    B[n-2]+=ell*(ell-1)//2
    return {k:v for k,v in A.items() if v},{k:v for k,v in B.items() if v},a
def mu(B,r):return sum(v*k**r for k,v in B.items())
tot=0;fail=0;failmu=0
def comps(ell,m):
    if m==1:yield (ell,);return
    for x in range(ell+1):
        for r in comps(ell-x,m-1):yield (x,)+r
seen=set();rows=[]
for N in range(4,41):
  g={}
  for m in (2,3,4):
    ell=N-m
    if ell<2:continue
    for p in comps(ell,m):
        if p[0]<1 or p[-1]<1 or p[::-1]<p:continue
        tot+=1;A,B,a=AB(p);k=tuple(sorted(A.items()))
        g.setdefault(k,[]).append((p,B))
  for k,v in g.items():
    if len(v)>1:
        s={tuple(sorted(b.items())) for _,b in v}
        if len(s)<len(v):fail+=1
        s2={(mu(b,2),mu(b,3)) for _,b in v}
        if len(s2)<len(v):failmu+=1;print('mu fail',N,[x[0] for x in v])
print('short spine tot',tot,'fail',fail,'mu23 fail',failmu)
# family top difference via H3
def H3(p):
    n=len(p)+sum(p);m=len(p);pre=[0]
    for x in p:pre.append(pre[-1]+1+x)
    seg=lambda i,j:pre[j]-pre[i];pp=lambda i,j:sum(p[i:j]);H=Counter();ell=sum(p)
    def path(mu,a,b,c,d):
        for e in (a+c,b+d,a+2*b+c,b+2*c+d):H[e]+=mu
    def star(mu,w,q,r,s):
        H[w]+=mu;H[w+n]+=mu
        for y in (q,r,s):H[w+2*y]+=mu
    for i,j,k in itertools.combinations(range(1,m),3):path(1,seg(0,i),seg(i,j),seg(j,k),seg(k,m))
    for i,j in itertools.combinations(range(1,m),2):
        A_,B_,C_=seg(0,i),seg(i,j),seg(j,m);la,lb,lc=pp(0,i),pp(i,j),pp(j,m)
        if la:path(la,1,A_-1,B_,C_)
        if lc:path(lc,A_,B_,C_-1,1)
        if lb:star(lb,B_-1,A_,C_,1)
    for i in range(1,m):
        A_,C_=seg(0,i),seg(i,m);la=pp(0,i);lc=ell-la
        if la>=2:star(la*(la-1)//2,A_-2,1,1,C_)
        if lc>=2:star(lc*(lc-1)//2,C_-2,1,1,A_)
        if la and lc:path(la*lc,1,A_-1,C_-1,1)
    if ell>=3:star(ell*(ell-1)*(ell-2)//6,n-3,1,1,1)
    return H
rows=[]
for s in range(1,41):
    P=[s,s+1,s-1,2*s+1,s+2];Q=[s,2*s+1,s+1,s-1,s+2];n=6*s+8
    h1,h2=H3(P),H3(Q);d={k:h1[k]-h2[k] for k in set(h1)|set(h2) if h1[k]!=h2[k]}
    # Delta[q^3]=(1-x^n)Delta H3
    q3=Counter()
    for k,v in d.items():q3[k]+=v;q3[k+n]-=v
    q3={k:v for k,v in q3.items() if v}
    t=max(q3);rows.append((s,t,q3[t],t==15*s+19,q3[t]==s))
print('Delta q3 top: all ok',all(r[3] and r[4] for r in rows),rows[:4],[r for r in rows if not(r[3] and r[4])][:6])
# validate H3 against direct shell
import networkx as nx
def cat(p):
    G=nx.path_graph(len(p));k=len(p)
    for i,c in enumerate(p):
        for _ in range(c):G.add_edge(i,k);k+=1
    return G
