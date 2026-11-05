import random,itertools
from collections import Counter
exec(open('/root/wms/ising/e.py').read().split("\nif __name__")[0])
def Fp(a,b,c,N):
    c0=Counter()
    for e,m in ((a-b+c,1),(N+b-a-c,1),(b+c-a,1),(N+c-a-b,1),(N-c+a,1),(c-a-2,-1),(a+c,-1),(b+c,-1),(2*N-b-c,1),(c-2,1),(N-c-2,1)):c0[e]+=m
    return c0
def P(t,N):
    c=Counter()
    for e,m in ((t-2,1),(N+t,1),(t,2),(2*N-t,1)):c[e]+=m
    return c
def Gp(s,t,N,l):
    u=t-s;v=t+s;c=Counter()
    for e,m in ((u,l),(N+u,l),(N-u,l-u+1),(v,t-1),(2*N-v,l-s),(u-2,u-1)):c[e]+=m
    for k_,m in P(t,N).items():c[k_]+=(1-t)*m
    for k_,m in P(N-t,N).items():c[k_]+=(l-t)*m
    for e in (t,N-t,N+t,2*N-t):c[e]+=2*t-l-1
    return c
def Op(t,N,l):
    c=Counter()
    for k_,m in P(t,N).items():c[k_]+=t*(t-1)//2*m
    for k_,m in P(N-t,N).items():c[k_]+=(l-t)*(l-t-1)//2*m
    for e in (t,N-t,N+t,2*N-t):c[e]+=t*(l-t)
    return c
ok=True
for _ in range(2000):
    N=random.randint(5,40);T=sorted(random.sample(range(1,N),random.randint(1,N-1)));l=N+1-len(T);c=Counter()
    for a in itertools.combinations(T,3):c.update(Fp(*a,N))
    for a,b in itertools.combinations(T,2):
        for e,m in Gp(a,b,N,l).items():c[e]+=m
    for t in T:
        for e,m in Op(t,N,l).items():c[e]+=m
    for e in (N-2,2*N,N,N,N):c[e]+=l*(l-1)*(l-2)//6
    d=H3T(T,N)
    if {k:v for k,v in c.items() if v}!={k:v for k,v in d.items() if v}:
        ok=False;print(T,N);break
print('printed F,G,O decomposition',ok)
