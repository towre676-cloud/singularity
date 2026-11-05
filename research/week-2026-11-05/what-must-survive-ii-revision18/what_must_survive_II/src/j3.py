# Explicit J_0..J_3 of b_Q. Computes universal coefficient functions exactly in Q(q), then checks every pattern against certified rows.
import sys,json,itertools,sympy as sp
from fractions import Fraction as Fr
from collections import defaultdict
from analyze import load,pats
q=sp.Symbol('q');N=4;f=q**-2-1
can=lambda e:sp.cancel(sp.together(e))
def smul(a,b):
    r=[sp.Integer(0)]*(N+1)
    for i,x in enumerate(a):
        if x!=0:
            for j,y in enumerate(b):
                if i+j<=N and y!=0: r[i+j]+=x*y
    return [can(z) for z in r]
def sinv(a):
    r=[sp.Integer(0)]*(N+1);r[0]=can(1/a[0])
    for n in range(1,N+1):
        r[n]=can(-sum(a[i]*r[n-i] for i in range(1,n+1))/a[0])
    return r
def slog(a): # a[0]=1
    c=[sp.Integer(0)]*(N+1)
    for n in range(1,N+1):
        c[n]=can(a[n]-sum(sp.Rational(k,n)*c[k]*a[n-k] for k in range(1,n)))
    return c
one=[sp.Integer(1)]+[sp.Integer(0)]*N
HM=N+1
B={h:list(one) for h in range(HM+1)}
for t in range(1,N+1):
    sq={h:smul(B[h],B[h]) for h in B}
    s0=sum(q**(3*h*h)*sq[h][t-h] for h in range(1,t+1))
    b0=can(-(sq[0][t]+s0));B[0][t]=b0;sq0=can(sq[0][t]+2*b0)
    for h in range(1,HM+1):
        B[h][t]=can(sq0+sum(q**(3*hp*hp-2*h*hp)*sq[hp][t-hp] for hp in range(1,t+1)))
B3={h:smul(smul(B[h],B[h]),B[h]) for h in B}
Z=[sp.Integer(0)]*(N+1)
for h in range(0,N+1):
    for i in range(N+1-h): Z[i+h]+=q**(3*h*h)*B3[h][i]
Z=[can(z) for z in Z];IZ=sinv(Z);IB={h:sinv(B[h]) for h in B}
def P(h): # series p(h)/x^h
    return [can(q**(3*h*h)*c) for c in smul(B3[h],IZ)]
def Ft(a,b): # 1+F
    t=smul(smul(Z,IB[a]),IB[b]);return [can(q**(-2*a*b)*c) for c in t]
def F(a,b):
    t=list(Ft(a,b));t[0]=can(t[0]-1);return t
P1=P(1);F11=F(1,1)
pi=[can(c/q**3) for c in P1];phi=[can(c/f) for c in F11]
Fs={(a,b):F(a,b) for a in range(0,5) for b in range(0,5)}
def shift(a,k): # multiply by x^k, truncating
    return ([sp.Integer(0)]*k+list(a))[:N+1]
def spow(a,n):
    r=list(one)
    for _ in range(n): r=smul(r,a)
    return r
Ipi=sinv(pi)
F11i=sinv(F11)
def unshift(a,k):
    return list(a[k:])+[sp.Integer(0)]*k
# ratio F(h,1)/F(1,1) with x-valuation: F(0,1)=x*... so ratio(0)=x*series
rat={}
for h in (0,2,3,4):
    s=Fs[(h,1)]
    if h==0: rat[h]=(1,smul(unshift(s,1),F11i))
    else: rat[h]=(0,smul(s,F11i))
def rho(d,h):
    # p(h)/p(1)*ratio^d as a series in x (valuation h-1 for h>=1; d-1 for h=0)
    base=smul(P(h),Ipi);base=[can(c/q**3) for c in base]
    v0,s=rat[h];t=smul(base,spow(s,d));val=(h-1)+v0*d
    return shift(t,val)
st=(0,2,3,4)
R={d:{h:rho(d,h) for h in st} for d in (2,3)}
r={d:[can(sum(R[d][h][i] for h in st)) for i in range(N+1)] for d in (2,3)}
def psi(a,b):
    # F(a,b)F11/(F(a,1)F(1,b)) with valuations cancelled
    va=rat[a][0];vb=rat[b][0]
    num=Fs[(a,b)]
    # numerator has valuation >= va+vb; divide by ratio series
    den=smul(rat[a][1],rat[b][1])
    u=unshift(num,va+vb)
    t=smul(smul(u,sinv(den)),F11i)
    return t
g={}
for a in st:
    for b in st:
        t=list(psi(a,b));t[0]=can(t[0]-1);g[(a,b)]=t
log1pr={d:slog([can(1+r[d][0])]+r[d][1:]) for d in r}
I1r={d:sinv([can(1+r[d][0])]+r[d][1:]) for d in r}
G={}
for a,b in [(2,2),(2,3),(3,3)]:
    tot=[sp.Integer(0)]*(N+1)
    for h in st:
        for k in st:
            t=smul(smul(R[a][h],R[b][k]),g[(h,k)])
            tot=[x+y for x,y in zip(tot,t)]
    tot=smul(smul(tot,I1r[a]),I1r[b]);G[(a,b)]=slog([can(1+tot[0])]+tot[1:])
def coef3(fn):
    return can(fn)
H={}
for a,b,c in itertools.product((2,3),repeat=3):
    if a>c: continue
    tot=[sp.Integer(0)]*(N+1)
    for x,y,z in itertools.product(st,repeat=3):
        t=smul(smul(smul(R[a][x],R[b][y]),R[c][z]),smul(g[(x,y)],g[(y,z)]))
        tot=[u+v for u,v in zip(tot,t)]
    H[(a,b,c)]=can(tot[3])
T={}
for a,b,c in itertools.combinations_with_replacement((2,3),3):
    tot=[sp.Integer(0)]*(N+1)
    for x,y,z in itertools.product(st,repeat=3):
        t=smul(smul(smul(R[a][x],R[b][y]),R[c][z]),smul(smul(g[(x,y)],g[(y,z)]),g[(x,z)]))
        tot=[u+v for u,v in zip(tot,t)]
    T[(a,b,c)]=can(tot[3])
lpi=slog(pi);lphi=slog(phi)
U={"pi":lpi,"phi":lphi,"r2":log1pr[2],"r3":log1pr[3],"G22":G[(2,2)],"G23":G[(2,3)],"G33":G[(3,3)]}
out={k:[str(sp.factor(c)) for c in v[:4]] for k,v in U.items()}
out["H"]={str(k):str(sp.factor(v)) for k,v in H.items()};out["T"]={str(k):str(sp.factor(v)) for k,v in T.items()}
json.dump(out,open(sys.argv[3],'w'),indent=1)
for k,v in out.items(): print(k,v)
# numeric-free verification on rows: expand everything as polynomials in q via exact rationals
rows=load(sys.argv[1]);Q=pats(sys.argv[1]+'.pats');VM=max(r[0] for r in rows)
col=defaultdict(lambda:defaultdict(dict))
for v,e,d in rows:
    for c,x in d.items(): col[c][v][e]=x
def invariants(k,ed):
    deg=[0]*k;adj=[set() for _ in range(k)]
    for a,b in ed: deg[a]+=1;deg[b]+=1;adj[a].add(b);adj[b].add(a)
    n2=sum(d==2 for d in deg);n3=k-n2
    e={(2,2):0,(2,3):0,(3,3):0}
    for a,b in ed: e[tuple(sorted((deg[a],deg[b])))]+=1
    p=defaultdict(int)
    for v in range(k):
        for a,c in itertools.combinations(sorted(adj[v]),2):
            x,z=sorted((deg[a],deg[c]));p[(x,deg[v],z)]+=1
    t=defaultdict(int)
    for a,b,c in itertools.combinations(range(k),3):
        if b in adj[a] and c in adj[a] and c in adj[b]: t[tuple(sorted((deg[a],deg[b],deg[c])))]+=1
    return n2,n3,e,p,t
def polymers(k,ed):
    m=len(ed);out_=[]
    for mask in range(1,1<<m):
        if bin(mask).count('1')<3: continue
        d=[0]*k;vm=0
        for i in range(m):
            if mask>>i&1:
                a,b=ed[i];d[a]+=1;d[b]+=1;vm|=1<<a|1<<b
        if any((vm>>v&1) and d[v]<2 for v in range(k)): continue
        seen=vm&-vm;ch=True
        while ch:
            ch=False
            for i in range(m):
                if mask>>i&1:
                    a,b=ed[i];A,Bb=seen>>a&1,seen>>b&1
                    if A!=Bb: seen|=1<<a|1<<b;ch=True
        if seen==vm: out_.append((mask,vm))
    return out_
def overlaps(k,ed):
    pl=polymers(k,ed);full=(1<<len(ed))-1;d={"d2":Fr(0),"d32":Fr(0),"d33":Fr(0)}
    for i,(a,va) in enumerate(pl):
        for j,(b,vb) in enumerate(pl[i:],i):
            if a|b!=full: continue
            c=bin(va&vb).count('1');s=bin(a&b).count('1')
            if bin(va).count('1')+bin(vb).count('1')!=k+c: continue
            w=Fr(1,2) if i==j else Fr(1)
            if c==2 and s==1: d["d2"]+=w
            elif c==3 and s==2: d["d32"]+=w
            elif c==3 and s==3: d["d33"]+=w
    return d
Pol=lambda e:sp.Poly(sp.cancel(sp.together(e)),q) if False else e
coefs={}
def lam(j,k,E,n2,n3,e,p,t):
    s=k*lpi[j]+E*lphi[j]+n2*log1pr[2][j]+n3*log1pr[3][j]+sum(e[kk]*G[kk][j] for kk in G)
    if j==3:
        s+=sum(p[kk]*H[kk] for kk in p)+sum(t[kk]*T[kk] for kk in t)
    return s
pts=[sp.Rational(3,7),sp.Rational(5,2),sp.Rational(11,13)]
lams={}
for name,ser in [("pi",lpi),("phi",lphi),("r2",log1pr[2]),("r3",log1pr[3]),("G22",G[(2,2)]),("G23",G[(2,3)]),("G33",G[(3,3)])]:
    lams[name]=[[sp.Rational(c.subs(q,x)) if hasattr(c,'subs') else sp.Rational(c) for c in ser[:4]] for x in pts]
Hv=[{k:sp.Rational(v.subs(q,x)) for k,v in H.items()} for x in pts];Tv=[{k:sp.Rational(v.subs(q,x)) for k,v in T.items()} for x in pts]
toF=lambda r:Fr(int(r.p),int(r.q))
bad=[0,0,0,0];tested=[0,0,0,0];over={}
sols=[]
KMAX=int(sys.argv[4]) if len(sys.argv)>4 else 99
for j_,(k,E,cm,ed) in enumerate(Q):
    if k>KMAX: continue
    n2,n3,e,p,t=invariants(k,ed)
    d=overlaps(k,ed) if k+2<=VM else {"d2":Fr(0),"d32":Fr(0),"d33":Fr(0)}
    for pi_,x in enumerate(pts):
        xF=toF(x);ff=xF**-2-1
        def L(jj):
            s=k*toF(lams["pi"][pi_][jj])+E*toF(lams["phi"][pi_][jj])+n2*toF(lams["r2"][pi_][jj])+n3*toF(lams["r3"][pi_][jj])+e[(2,2)]*toF(lams["G22"][pi_][jj])+e[(2,3)]*toF(lams["G23"][pi_][jj])+e[(3,3)]*toF(lams["G33"][pi_][jj])
            if jj==3: s+=sum(c*toF(Hv[pi_][kk]) for kk,c in p.items())+sum(c*toF(Tv[pi_][kk]) for kk,c in t.items())
            return s
        l1,l2,l3=L(1),L(2),L(3);T0=xF**(3*k)*ff**E
        def J1gen(kk,EE):
            n22=3*kk-2*EE;n33=2*(EE-kk)
            return kk*toF(lams["pi"][pi_][1])+EE*toF(lams["phi"][pi_][1])+n22*toF(lams["r2"][pi_][1])+n33*toF(lams["r3"][pi_][1])
        pred=[T0,T0*l1,T0*(l2+l1*l1/2)-d["d2"]*xF**(3*k+6)*ff**(E+1),
              T0*(l3+l1*l2+l1**3/6)-d["d2"]*xF**(3*k+6)*ff**(E+1)*J1gen(k+2,E+1)-xF**(3*k+9)*(d["d32"]*ff**(E+2)+d["d33"]*ff**(E+3))]
        for jj in range(4):
            V=k+jj
            if V>VM: continue
            val=sum(c*xF**ee for ee,c in col[j_+1][V].items())
            tested[jj]+=1
            if val!=pred[jj]: bad[jj]+=1
res={"evaluations":tested,"failures":bad,"points":[str(x) for x in pts]};print(res)
json.dump(res,open(sys.argv[2],'w'),indent=1)
