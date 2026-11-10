# Independent replay of the squared-shear core via the (H,Q) filtration: for m=2, eps!=0, solve for f with Df in the six-space at Q-degree 5 in (H,Q) coordinates.
import sympy as sp,json,sys
H,z,qq=sp.symbols('H z q');A,B,C0,e=sp.symbols('A B C0 e',nonzero=True)
U2,U3=sp.symbols('U2 U3')
P=A*z**2+B*z+C0
qexpr=(H-P)/e
def star_HQ(f):
    # f(H,z) -> express with H=P+e q then apply (star) with u'',u''' as independent symbols
    F=f.subs(H,P+e*qq)
    P1,P2,P3=sp.diff(P,z),sp.diff(P,z,2),0
    return sp.expand(P1*U3*sp.diff(F,z,3)-3*P2*U2*sp.diff(F,qq,1,z,2))
six=[sp.Integer(1),H,z,z**2,qexpr*z,qexpr**2]
out={}
for f in six:
    assert sp.simplify(star_HQ(f))==0
out['six_pass_C3']=True
# Integrate each core element in z at fixed H: Q-degree goes up; every extension modulo K[H] must fail
c=sp.symbols('c0:6');g2,g3,g4=sp.symbols('g2 g3 g4')
F=sum(ci*sp.integrate(sp.expand(fi),z) for ci,fi in zip(c,six))
g0=g2*H**2+g3*H**3+g4*H**4
expr=star_HQ(F+g0)
pol=sp.Poly(sp.expand(expr.subs(qq,sp.Symbol('Q0'))),z,sp.Symbol('Q0'),U2,U3)
eqs=[sp.simplify(co) for co in pol.coeffs()]
# unknowns c, g: treat U2,U3 and Q0,z as algebraically independent (top-q-degree argument separates u'' and q u''' only through q; recorded in text)
sol=sp.solve(eqs,list(c)+[g2,g3,g4],dict=True)
out['extension_solutions']=str(sol)
print(out);json.dump(out,open(sys.argv[1],'w'),indent=1)
