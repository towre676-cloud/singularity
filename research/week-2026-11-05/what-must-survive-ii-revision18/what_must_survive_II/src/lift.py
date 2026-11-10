# Principal-part test of the row k+3 condition from invariants (Theorem 12 form).
import sys,json,itertools
import sympy as sp
from fractions import Fraction as Fr
u=sp.Symbol('u');t=1/u;f=u-1;w=(1+u)/u
Om=2*(t-1)**2*(t+1)**3*(t**5+4*t**4+10*t**3+11*t**2+4*t-1)/t
def laurent(expr,n=7):
    e=sp.cancel(sp.together(expr));nu,de=sp.fraction(e);de=sp.Poly(de,u);m=de.monoms()[-1][0]
    assert de.LC()==de.coeff_monomial(u**de.degree()) and len(de.terms())==1,"denominator must be a power of u"
    c=de.LC();P=sp.Poly(nu,u);return {mon[0]-de.degree():Fr(int(co.p),int(co.q))/Fr(int(c.p),int(c.q)) for mon,co in P.terms()} if False else {mon[0]-de.degree():sp.Rational(co)/c for mon,co in P.terms()}
def inv(q):
    k,E,ed=q;deg=[0]*k;adj=[set() for _ in range(k)]
    for a,b in ed: deg[a]+=1;deg[b]+=1;adj[a].add(b);adj[b].add(a)
    e22=sum(deg[a]==2 and deg[b]==2 for a,b in ed)
    X=sum(1 for v in range(k) if deg[v]==2 and all(deg[x]==2 for x in adj[v]))
    Y=sum(1 for v in range(k) if deg[v]==3 for a,c in itertools.combinations(adj[v],2) if deg[a]==2 and deg[c]==2)
    T={6:0,7:0,8:0,9:0}
    for a,b,c in itertools.combinations(range(k),3):
        if b in adj[a] and c in adj[a] and c in adj[b]: T[deg[a]+deg[b]+deg[c]]+=1
    return {"A":e22,"X":X,"Y":Y,**{f"T{s}":T[s] for s in T}}
_c={}
def pp_basis(E):
    # principal parts at u=0 (orders 1..6, plus order>6 check) of the row k+3 functions for unit invariants at edge count E; poly part ignored.
    if E in _c: return _c[E]
    fE=f**E
    fs={"A":Om*f*fE,"X":t*w**4*f**2*fE,"Y":w**5*f**2*fE}
    for s in (6,7,8,9): fs[f"T{s}"]=t**(9-s)*w**(s-3)*f**3*fE
    out={}
    for n,e in fs.items():
        l=laurent(e);out[n]={o:c for o,c in l.items() if o<0}
    _c[E]=out;return out
def pp_of(vec,E):
    b=pp_basis(E);r={}
    for n,val in vec.items():
        if val:
            for o,c in b[n].items(): r[o]=r.get(o,0)+val*c
    return r
