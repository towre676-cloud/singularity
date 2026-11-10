import sympy as sp
from collections import defaultdict
p,q,r,N,l=sp.symbols('p q r N l')
def add(d,e,c):d[sp.expand(e)]+=c
def P(d,t,c):
    for e,m in ((t-2,1),(N+t,1),(t,2),(2*N-t,1)):add(d,e,c*m)
def Q(d,t,c):P(d,N-t,c)
def M(d,t,c):
    for e in (N-t,t,N+t,2*N-t):add(d,e,c)
def G(s,t):
    d=defaultdict(lambda:sp.Integer(0));u=t-s;v=t+s
    add(d,u,l);add(d,N+u,l);add(d,N-u,l-u+1);add(d,v,t-1);add(d,2*N-v,l-s);add(d,u-2,u-1)
    P(d,t,1-t);Q(d,t,l-t);M(d,t,2*t-l-1);return d
def F(a,b,c):
    d=defaultdict(lambda:sp.Integer(0))
    for e in (a-b+c,N+b-a-c,b+c-a,N+c-b-a):add(d,e,1)
    u=c-a;add(d,N-u,1);add(d,u-2,-1);add(d,c+a,-1)
    add(d,b+c,-1);add(d,2*N-b-c,1);add(d,c-2,1);add(d,N-c-2,1);return d
def combo(ds,cs):
    o=defaultdict(lambda:sp.Integer(0))
    for d,c in zip(ds,cs):
        for e,v in d.items():o[e]+=c*v
    return {e:sp.factor(v) for e,v in o.items() if sp.expand(v)!=0}
def J2():
    return combo([G(p,q),G(N-q,N-p),G(p,N-q),G(q,N-p)],[1,1,-1,-1])
def show(d):
    for e,v in sorted(d.items(),key=str):print('  x^(%s) : %s'%(e,v))
print('4*J0_pq');show(J2())
# F with third element w fixed; site pair (p,q), four orientations. w position cases
def order(xs,key):return sorted(xs,key=key)
vals={p:3,q:7,N:40}
def Jw(wexpr,wnum):
    v={p:3,q:7,N:40};ds=[];cs=[]
    for (a,b),c in (((p,q),1),((N-q,N-p),1),((p,N-q),-1),((q,N-p),-1)):
        trip=[a,b,wexpr];trip=sorted(trip,key=lambda e:e.subs({p:3,q:7,N:40,r:wnum}))
        ds.append(F(*trip));cs.append(c)
    return combo(ds,cs)
for name,w,num in (('r<p',r,1),('p<r<q',r,5),('q<r<N-q',r,15),('N-q<r<N-p',N-r,5),('r>N-p',N-r,1)):
    print('4*J(w=%s), w<-%s'%(name,w));show(Jw(w,num))
