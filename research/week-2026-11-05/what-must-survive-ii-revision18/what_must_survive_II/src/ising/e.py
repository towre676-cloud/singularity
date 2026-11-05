import sympy as sp,itertools
from collections import Counter
x=sp.Symbol('x')
def H3T(T,N):
    # H3/x as Counter over exponents, from pair/triple closed form
    Ts=sorted(T);k=len(Ts);ell=N+1-k;rk={t:i for i,t in enumerate(Ts)};L={t:t-rk[t] for t in Ts};c=Counter()
    for s,t,r in itertools.combinations(Ts,3):
        for e in (s-t+r,N+t-s-r,t+r-s,N+r-t-s):c[e]+=1
    for s,t in itertools.combinations(Ts,2):
        u=t-s;v=t+s
        for e,m in ((u,ell),(N+u,ell),(N-u,ell+L[s]-L[t]),(v,L[t]),(2*N-v,ell-L[s]),(u-2,L[t]-L[s])):c[e]+=m
    for t in Ts:
        la=L[t];lc=ell-la
        for e in (t-2,N+t,t,t,2*N-t):c[e]+=la*(la-1)//2
        w=N-t-2
        for e in (w,2*N-t,w+2,w+2,N+t):c[e]+=lc*(lc-1)//2
        for e in (N-t,t,N+t,2*N-t):c[e]+=la*lc
    for e in (N-2,2*N,N,N,N):c[e]+=ell*(ell-1)*(ell-2)//6
    return c
def poly(c):return sum(v*x**k for k,v in c.items())
def walsh(sites,N,neutral=()):
    # returns dict pair->Laurent J_pq with H = c0+sum J sigma sigma
    out={}
    conf=list(itertools.product((1,-1),repeat=len(sites)))
    vals={}
    for sg in conf:
        T=set(neutral)
        for p,z in zip(sites,sg):T.add(p if z==1 else N-p)
        vals[sg]=H3T(T,N)
    res={}
    for sub in itertools.chain.from_iterable(itertools.combinations(range(len(sites)),r) for r in range(0,len(sites)+1)):
        c=Counter()
        for sg in conf:
            w=1
            for i in sub:w*=sg[i]
            for e,v in vals[sg].items():c[e]+=sp.Rational(w*v,len(conf))
        res[sub]={e:v for e,v in c.items() if v}
    return res
if __name__=='__main__':
    # validate vs m.py H3
    src=open('/root/wms/spine/m.py').read()
    exec(src.split("# family top difference via H3")[1].split("rows=[]")[0])
    import random
    def p_of(T,N):
        s=[0]+sorted(T)+[N];c=[s[i+1]-s[i] for i in range(len(s)-1)]
        return tuple([c[0]]+[z-1 for z in c[1:-1]]+[c[-1]])
    ok=True
    for _ in range(500):
        N=random.randint(5,40);T=set(random.sample(range(1,N),random.randint(1,N-1)))
        h=H3(p_of(T,N));a={k+1:v for k,v in H3T(T,N).items() if v};b={k:v for k,v in h.items() if v}
        if a!=b:ok=False;print(T,N,set(a.items())^set(b.items()));break
    print('closed form ok',ok)
