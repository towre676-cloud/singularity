# Readout trichotomy and Kalman table on an explicit nonsplit rank-3 extension built on the Legendre module:
# L y = s(1-s) y'' + (1-2s) y' - y/4 = w/s..., state (y,y',w), w' = 0 (chi trivial), inhomogeneous term w/s.
import sympy as sp, json, sys
s=sp.Symbol('s')
A=sp.Matrix([[0,1,0],[sp.Rational(1,4)/(s*(1-s)),-(1-2*s)/(s*(1-s)),1/(s*s*(1-s))],[0,0,0]])
def krylov_rank(lam):
    rows=[lam];r=lam
    for i in range(3):
        r=(r.diff(s)+r*A).applyfunc(sp.simplify);rows.append(r)
    return sp.Matrix.vstack(*rows).rank(simplify=True)
res={}
res['lam_y (sees E)']=krylov_rank(sp.Matrix([[1,0,0]]))
res['lam_random (sees E)']=krylov_rank(sp.Matrix([[s+2,sp.Rational(3,7)/s,s**2-1]]))
res['lam_yprime (sees E)']=krylov_rank(sp.Matrix([[0,1,0]]))
res['lam_w (vanishes on E)']=krylov_rank(sp.Matrix([[0,0,1]]))
res['lam_w/s (vanishes on E)']=krylov_rank(sp.Matrix([[0,0,1/s]]))
assert all(v in (1,3) for v in res.values())
# nonsplitting: indicial argument at s=0: s^rho -> rho^2 s^(rho-1); rational particular solution of L y=1/s impossible
rho=sp.Symbol('rho');lead=sp.limit(sp.simplify((s*(1-s)*sp.diff(s**rho,s,2)+(1-2*s)*sp.diff(s**rho,s)-s**rho/4)/s**(rho-1)),s,0)
res['indicial_at_0']=str(sp.factor(lead));print(res);json.dump({k:(int(v) if not isinstance(v,str) else v) for k,v in res.items()},open(sys.argv[1],'w'),indent=1)
