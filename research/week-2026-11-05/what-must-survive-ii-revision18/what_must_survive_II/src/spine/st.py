exec(open('fl.py').read().split("tot={}")[0])
import math,random,networkx as nx
exec(open('m.py').read().split("# C's short")[1].split("tot=0;fail")[0].replace("spine claim: exact, among caterpillars",""))
def ABT(T,N):return AB(p_of(T,N))[:2]
T1={1,4,5,6,9};T2={1,5,6,8,9}
print(p_of(T1,12),p_of(T2,12),ABT(T1,12)==ABT(T2,12),canon(T1,12),canon(T2,12))
# Ising identity W(T) on random sets vs direct B
x=sp.Symbol('x')
def Wdirect(T,N):
    Ts=sorted(T);c=Counter()
    for i,s in enumerate(Ts):
        for t in Ts[i+1:]:
            c[t-s]+=1;c[t]-=1;c[N-s]-=1
    return {k:v for k,v in c.items() if v}
def Bfrom(T,N):
    # B = theta(T+T^R) +(1-|T|)... check: B= W + theta(S') + C(l,2)x^N, l=N+2-(|T|+1)
    n=N+2;m=len(T)+1;ell=n-m;c=Counter(Wdirect(T,N))
    for t in T:c[t]+=t;c[N-t]+=N-t
    c[N]+=ell*(ell-1)//2
    # correction: pendant count formula
    return {k:v for k,v in c.items() if v}
okB=True
for _ in range(3000):
    N=random.randint(4,40);T=set(random.sample(range(1,N),random.randint(1,N-1)))
    p=p_of(T,N)
    if p[0]<1 or p[-1]<1:continue
    b=AB(p)[1]
    if Bfrom(T,N)!={k:v for k,v in b.items() if v}:okB=False;print('B mismatch',T,N,Bfrom(T,N),b);break
print('W formula for B',okB)
# Ising: W(T)-W(T') = sum over pairs p<q, one flipped
def spins(T,N):
    return {min(t,N-t):(1 if t<N-t else -1) for t in T if t!=N-t and (N-t) not in T}
def Delta(T1,T2,N):
    s1,s2=spins(T1,N),spins(T2,N);c=Counter()
    ks=sorted(s1)
    for i,p in enumerate(ks):
        for q in ks[i+1:]:
            tau=s1[p]*s1[q]-s2[p]*s2[q]
            if tau:
                for e,v in ((q-p,1),(q,-1),(N-q-p,-1),(N-q,1)):c[e]+=v*tau
    return {k:v for k,v in c.items() if v}
okI=True
for _ in range(4000):
    N=random.randint(4,40);T=set(random.sample(range(1,N),random.randint(1,N-1)))
    T2={(N-t if random.random()<.5 and (N-t) not in T else t) for t in T}
    if len(T2)!=len(T) or set(T2)|{N-t for t in T2}!=set(T)|{N-t for t in T}:continue
    w1,w2=Counter(Wdirect(T,N)),Counter(Wdirect(T2,N))
    w1.subtract(w2);d={k:v for k,v in w1.items() if v}
    D_=Counter(Delta(T,T2,N));D_={k:v/2 for k,v in D_.items() if v}
    if d!=D_:okI=False;print('Ising mismatch',T,T2,N,d,D_);break
print('Ising identity',okI)
# structure on census
sumr={}
for n in range(8,33):
    try:L=open(f'd{n}.txt')
    except:continue
    N=n-2;cls=[[T_of(tuple(map(int,x_.strip(',').split(','))))[0] for x_ in l.split()[1:]] for l in L if l.startswith('S2')]
    pairs=0;good=0;bad=[]
    for c in cls:
        for A_,B_ in itertools.combinations(c,2):
            pairs+=1;found=False
            for BB in (B_,frozenset(N-t for t in B_)):
                Y=A_&BB;Z=A_-BB
                if {N-z for z in Z}!=set(BB-A_):continue
                g=0
                for z in Z:g=math.gcd(g,z)
                g=math.gcd(g,N)
                for v in [d for d in range(3,N) if N%d==0 and g%d==0 and N/d>=3]:
                    u=N//v;Ym=Counter(Y);Ym.subtract(Counter(N-y for y in Y));Ym={k:w for k,w in Ym.items() if w}
                    # periodic: coefficient depends only on residue, and no residue 0
                    res={}
                    ok=all(y%v!=0 for y in Ym)
                    for y,w in Ym.items():
                        res.setdefault(y%v,set()).add(w)
                    cnt=Counter(y%v for y in Ym)
                    ok=ok and all(len(s)==1 for s in res.values()) and all(cnt[r]==u for r in res)
                    if ok:found=True;break
                if found:break
            good+=found
            if not found:bad.append((A_,B_))
    sumr[n]=(N,len(cls),pairs,good);print(n,N,len(cls),'pairs',pairs,'structured',good,[ (sorted(a),sorted(b)) for a,b in bad[:1]],flush=True)
