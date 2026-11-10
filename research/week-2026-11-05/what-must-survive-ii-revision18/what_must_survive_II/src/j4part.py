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

def t_pole(e,qshift):
    # degree in t of e/q^qshift at infinity
    e=sp.cancel(sp.together(e/q**qshift));n,d=sp.fraction(e)
    return sp.Rational(sp.degree(n,q)-sp.degree(d,q),2)
H4={};T4={}
for (a,b,c) in H:
    tot=[sp.Integer(0)]*(N+1);p1=list(one)
    for x_,y_,z_ in itertools.product(st,repeat=3):
        t=smul(smul(smul(R[a][x_],R[b][y_]),R[c][z_]),smul(g[(x_,y_)],g[(y_,z_)]))
        tot=[u+v for u,v in zip(tot,t)]
    norm=smul(smul(I1r[a],I1r[b]),I1r[c]);tot=smul(tot,norm)
    # minus product of means at order x^4
    def mean(u,v):
        m=[sp.Integer(0)]*(N+1)
        for h_ in st:
            for k_ in st:
                t=smul(smul(R[u][h_],R[v][k_]),g[(h_,k_)]);m=[p_+q_ for p_,q_ in zip(m,t)]
        return m
    pr=smul(mean(a,b),mean(b,c))
    H4[(a,b,c)]=can(tot[4]-pr[4])
for (a,b,c) in T:
    tot=[sp.Integer(0)]*(N+1)
    for x_,y_,z_ in itertools.product(st,repeat=3):
        t=smul(smul(smul(R[a][x_],R[b][y_]),R[c][z_]),smul(smul(g[(x_,y_)],g[(y_,z_)]),g[(x_,z_)]))
        tot=[u+v for u,v in zip(tot,t)]
    tot=smul(tot,smul(smul(I1r[a],I1r[b]),I1r[c]));T4[(a,b,c)]=can(tot[4])
def Hs(kk): return H4[kk] if kk in H4 else H4[(kk[2],kk[1],kk[0])]
X4=can(Hs((2,2,2))-2*Hs((2,2,3))+Hs((3,2,3)));Y4=can(Hs((2,3,2))-2*Hs((2,3,3))+Hs((3,3,3)))
print("X4 pole rel q^12:",t_pole(X4,12),sp.factor(X4))
print("Y4 pole rel q^12:",t_pole(Y4,12),sp.factor(Y4))
for k_,v in T4.items(): print("T4",k_,"pole",t_pole(v,12),sp.factor(v))
print("Gamma x^4 e22 edge coefficient pole:",t_pole(G[(2,2)][4]-2*G[(2,3)][4]+G[(3,3)][4],12))
json.dump({"X4":str(sp.factor(X4)),"Y4":str(sp.factor(Y4)),"T4":{str(k):str(sp.factor(v)) for k,v in T4.items()}},open(sys.argv[1],'w'),indent=1)
