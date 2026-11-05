from pathlib import Path
import sympy as S,json
r=Path(__file__).parent;s=S.symbols('s')
b=(2-s)/(s*(s+4))
AE=S.Matrix([[-2*(s+9)/(s*(s+12)),128*(s+6)/(s*(s-4)*(s+12)*(s+16))],[(s+6)/(2*s*(s+12)),-6/(s*(s+12))]])
F=S.Matrix([-4*(2*s*s+15*s+16)/(s*s*(s+12)*(s+16)),(7*s**3+54*s*s-24*s+64)/(8*s*s*(s+4)*(s+12))])
A=S.zeros(3);A[0,0]=b;A[1:3,0]=F;A[1:3,1:3]=AE;out={}
for name,lam in [('character',S.Matrix([[1,0,0]])),('elliptic_1',S.Matrix([[0,1,0]])),('elliptic_2',S.Matrix([[0,0,1]]))]:
 rr=[lam]
 for _ in range(2):rr.append((rr[-1].diff(s)+rr[-1]*A).applyfunc(S.cancel))
 det=S.factor(S.Matrix.vstack(*rr).det());out[name]={'determinant':str(det),'determinant_at_s8':str(det.subs(s,8))}
 assert (det==0)==(name=='character')
assert S.simplify(S.Rational(1,2)/s-S.Rational(3,2)/(s+4)-b)==0
(r/'annular_krylov.json').write_text(json.dumps(out,indent=2));print(out)
