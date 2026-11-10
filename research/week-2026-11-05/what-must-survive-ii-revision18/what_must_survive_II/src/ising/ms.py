exec(open("mf.py").read().split("\nif __name__")[0])
def k(q,N):
    c=Counter({q:q});c[N-q]-=N-q;return c
def sh(c,e,m=1):
    return Counter({a+e:m*b for a,b in c.items()})
def J4(p,q,F,N,ell):
    c=Counter();hq=h(q,N);gp=g(p);sq=s(q,N)
    addc(c,mul(gp,hq),2*ell)
    br=Counter({N-p:ell-(N-2*p-1)});br[p]+=-ell+(N-2*p-3);br[-2]-=ell;br[0]+=2
    addc(c,mul(hq,br))
    addc(c,sh(sq,-2,N-2*q));addc(c,sh(hq,-2));addc(c,sh(k(q,N),-p-2,2));addc(c,sh(hq,-p-2,-2*(p+1)))
    base=Counter({N-p:1});base[p]-=1;base[-p-2]-=1
    for r in F:
        if r==p or r==q:continue
        b=Counter(base);addc(b,mul(gp,s(r,N)))
        if r<p:
            # 4J(r<p)=h_q[2x^{r-p}-2x^r-x^{p-r}+x^{N-p-r}-x^{-r-2}]
            b=Counter();b[r-p]+=2;b[r]-=2;b[p-r]-=1;b[N-p-r]+=1;b[-r-2]-=1
        addc(c,mul(hq,b))
        if r>q:
            d=Counter(sq);addc(d,s(r,N),-1);addc(c,mul(gp,sh(d,-2)))
    return c
ok=True;cnt=0
for _ in range(1500):
    N=random.randint(6,44);T=set(random.sample(range(1,N),random.randint(2,N-1)))
    T2=set()
    for t in T:
        T2.add(N-t if (N-t) not in T and t!=N-t and random.random()<.5 else t)
    if len(T2)!=len(T):continue
    s1,s2=spins(T,N),spins(T2,N);ks=sorted(s1);F=folds(T,N);ell=N+1-len(T);c=Counter()
    if set(s1)!=set(s2):continue
    for i,p in enumerate(ks):
        for q in ks[i+1:]:
            t=s1[p]*s1[q]-s2[p]*s2[q]
            if t:addc(c,J4(p,q,F,N,ell),t)
    d=Counter(H3T(T,N));d.subtract(H3T(T2,N));d={a:4*b for a,b in d.items() if b}
    c={a:b for a,b in c.items() if b};cnt+=1
    if c!=d:ok=False;print('fail',T,T2,N);break
print('general coupling formula',ok,cnt)
# top term theorem on census and exhaustive pairs
good=0;tot=0
for n in range(8,31):
    for l in open(f'/root/wms/spine/d{n}.txt'):
        if not l.startswith('S2'):continue
        ps=[tuple(map(int,a.strip(',').split(','))) for a in l.split()[1:]];N=n-2
        for j in range(1,len(ps)):
            T1,T2=T_of(ps[0])[0],T_of(ps[j])[0]
            s1,s2=spins(T1,N),spins(T2,N);ks=sorted(s1);r1=ks[0]
            Z=[a for a in ks if s1[a]!=s2[a]]
            if r1 in Z:Z=[a for a in ks if a not in Z]
            qs=Z[0];nu=sum(1 for r in folds(T1,N) if r<r1)
            d=Counter(H3T(T1,N));d.subtract(H3T(T2,N));d={a:4*b for a,b in d.items() if b}
            tot+=1;good+=(max(d)==2*N-qs-r1 and d[max(d)]==-2*s1[r1]*s1[qs]*(2*r1-nu)*(1))
print('top term',good,tot)
