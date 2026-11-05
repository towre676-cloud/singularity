# Symbolic and exact checks of the analytic statements. Exits nonzero on failure.
import sympy as sp, sys, json
from fractions import Fraction
q,Qv,x=sp.symbols('q Q x'); R={}
# 1. (star) formula against raw original-coordinate transvectant for generic-degree instances
qq,p=sp.symbols('q p')
def raw(H,f,k=3): return sp.expand(sum((-1)**j*sp.binomial(k,j)*sp.diff(H,qq,k-j,p,j)*sp.diff(f,qq,j,p,k-j) for j in range(k+1)))
def star(Pz,u,fz):
    z=sp.Symbol('z');P1,P2,P3=[sp.diff(Pz,z,i) for i in (1,2,3)];u2,u3=sp.diff(u,qq,2),sp.diff(u,qq,3)
    return P1*u3*sp.diff(fz,z,3)-3*P2*u2*sp.diff(fz,qq,1,z,2)-P3*(sp.diff(fz,qq,3)+3*u2*sp.diff(fz,qq,1,z,1)+u3*sp.diff(fz,z,1))
z=sp.Symbol('z');ok=True
for Pz,u,eps,fz in [(z**3+2*z,qq**3+qq**2,1,qq**2*z**3+qq**4),(z**4,qq**5,3,qq*z**5+z**2),(z**2+z,qq**4,1,qq**3*z**3),(5*z**5-z**3,qq**3,0,qq**3*z**2+z**6)]:
    H=sp.expand(Pz.subs(z,p+u)+eps*qq);lhs=raw(H,sp.expand(fz.subs(z,p+u)));rhs=sp.expand(star(Pz,u,fz).subs(z,p+u))
    ok&=sp.expand(lhs-rhs)==0
R['star_formula']=bool(ok);assert ok
# 2. composite formulas C3(g(H)), C3(QH)
a,c,eps=sp.symbols('a c e');Pz=a*z**4+z**2;u=c*qq**5+qq**3;H=Pz+eps*qq
P1,P2,P3=[sp.diff(Pz,z,i) for i in (1,2,3)];u2,u3=sp.diff(u,qq,2),sp.diff(u,qq,3)
S=P1**4*u3-3*eps*P1**2*P2*u2-eps**3*P3;Rr=3*(P1**2*P2*u3-eps*u2*(P2**2+P1*P3))
for s in (2,3,5):
    assert sp.expand(star(Pz,u,H**s)-(s*(s-1)*(s-2)*H**(s-3)*S+s*(s-1)*H**(s-2)*Rr))==0
assert sp.expand(star(Pz,u,z*H)-(3*P1*P2*u3-3*eps*u2*P3-u3*P3*H))==0
R['composite_formulas']=True
# 3. weight factorisation of the leading symbol
m,d,A,b=sp.symbols('m d A b');k=(m*d*(d-1)*(d-2)*b*(b-1)*(b-2)-3*m*(m-1)*d*(d-1)*A*b*(b-1)-m*(m-1)*(m-2)*(3*d*(d-1)*A*b+d*(d-1)*(d-2)*b))
assert sp.expand(k-m*d*(d-1)*b*(b+m-3)*((d-2)*(b-m)-3*(m-1)*A))==0
R['symbol_factorisation']=True
# 4. Bethe data through low order with sympy series over Laurent polynomials
N=3
def trunc(e): return sp.series(sp.expand(e),x,0,N+1).removeO()
Bs={h:sp.Integer(1) for h in range(0,N+2)}
for t in range(1,N+1):
    # fixed-point on B_0 via B0=B0^2+sum..., iterate
    new={}
    for it in range(t+2):
        S0=sum(x**hp*q**(3*hp**2)*Bs[hp]**2 for hp in range(1,N+1))
        b0=Bs[0];b0=trunc(1-sp.sqrt(1-4*S0) if False else b0)
        # Newton: B0 = 1 - S0 - ... solved as B0=(1-sqrt(1-4S))/... small branch with B0(0)=1
        B0=trunc(sp.series((1+sp.sqrt(1-4*S0))/2,x,0,N+1).removeO())
        Bs={0:B0,**{h:trunc(B0**2+sum(x**hp*q**(3*hp**2-2*h*hp)*Bs[hp]**2 for hp in range(1,N+1))) for h in range(1,N+2)}}
Zv=trunc(sum(x**h*q**(3*h**2)*Bs[h]**3 for h in range(0,N+1)))
Z1=sp.simplify(Zv.coeff(x,1));assert sp.simplify(Z1+2*q**3)==0
f=q**-2-1
F11=q**-2*Zv/(Bs[1]**2)-1;ser=sp.series(F11,x,0,2).removeO();assert sp.simplify(ser-(f*(1-2*q*x)))==0
F01=Zv/(Bs[0]*Bs[1])-1;ser=sp.series(F01,x,0,2).removeO();assert sp.simplify(ser+q**3*f*x)==0
p1=sp.series(x*q**3*Bs[1]**3/Zv,x,0,3).removeO();assert sp.simplify(p1-x*q**3*(1+x*(3*q-4*q**3)))==0
R['bethe_low_order']=True
json.dump(R,open(sys.argv[1],'w'),indent=1);print(R)
