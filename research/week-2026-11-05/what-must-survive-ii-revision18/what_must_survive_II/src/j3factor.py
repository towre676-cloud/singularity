import sympy as sp,json
q=sp.Symbol('q');co=json.load(open('../receipts_replay/j3_coefficients.json'));S=lambda s:sp.sympify(s)
w=q**2+1;f=q**-2-1
g=lambda n,j:S(co[n][j])
gam2=sp.factor(g('G22',2)-2*g('G23',2)+g('G33',2));gam3=sp.factor(g('G22',3)-2*g('G23',3)+g('G33',3))
print('gamma2',gam2,' check f q^6 w^3:',sp.simplify(gam2-f*q**6*w**3));print('gamma3',gam3)
# Lambda_1 slope data
a1=S(co['pi'][1]);b1=S(co['phi'][1]);r21=S(co['r2'][1]);r31=S(co['r3'][1])
print('L1 per k:',sp.factor(a1+3*r21-2*r31),' per E:',sp.factor(b1-2*r21+2*r31))
H=lambda s:q**(23-2*s)*(q**2-1)**2*w**(s-2)
T=lambda s:-q**(21-2*s)*(q**2-1)**3*w**(s-3)
# With P222=x, P232=y, e22=e: P223=2e-2x; P323=n2-x-(2e-2x)=n2-2e+x; e23=2n2-2e; P233=2e23-2y=4n2-4e-2y; P333=3n3-y-P233=3n3-4n2+4e+y
print('P222 coef:',sp.factor(H(6)-2*H(7)+H(8)));print('P232 coef:',sp.factor(H(7)-2*H(8)+H(9)));print('e22 via paths:',sp.factor(2*H(7)-2*H(8)-4*H(8)+4*H(9)))
print('n2 via paths',sp.factor(H(8)+4*H(8)-4*H(9)),' n3 via paths',sp.factor(3*H(9)))
for s in (6,7,8,9): print('T',s,sp.factor(T(s)/(q**6*f**3)))
