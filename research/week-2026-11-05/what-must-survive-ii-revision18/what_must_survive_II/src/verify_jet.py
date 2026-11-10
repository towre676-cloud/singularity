# Check top-order and first-jet closed forms for every pattern against engine rows.
import sys,sympy as sp,json
from analyze import load,pats,P
from fractions import Fraction as Fr
from collections import defaultdict
rows=load(sys.argv[1]);Q=pats(sys.argv[1]+'.pats')
col=defaultdict(dict)
for v,e,d in rows:
    for c,x in d.items(): col[c][(v,e)]=x
q=sp.Symbol('q');bad0=bad1=0;n0=n1=0;Vm=max(r[0] for r in rows);cache={}
def poly_of(j,V): return {e:x for (v,e),x in col[j+1].items() if v==V}
for j,(k,E,cm,ed) in enumerate(Q):
    n3=2*(E-k);n2=k-n3
    key=(k,E)
    if key not in cache:
        beta0=sp.expand(q**(3*k-2*E)*(1-q**2)**E)
        J=k*(3*q-4*q**3)-2*q*E+n2*(q**3+q**5*(q**2+1)**2)+n3*q**3*(q**2+1)**3
        beta1=sp.expand(beta0*J)
        cache[key]=({int(m[0]):Fr(int(c)) for m,c in sp.Poly(beta0,q).terms()},{int(m[0]):Fr(int(c)) for m,c in sp.Poly(beta1,q).terms()})
    b0,b1=cache[key]
    n0+=1
    if poly_of(j,k)!=b0: bad0+=1
    if k+1<=Vm:
        n1+=1
        if poly_of(j,k+1)!=b1: bad1+=1
r={"patterns_top_checked":n0,"top_failures":bad0,"patterns_first_jet_checked":n1,"first_jet_failures":bad1}
print(r);json.dump(r,open(sys.argv[2],'w'),indent=1)
