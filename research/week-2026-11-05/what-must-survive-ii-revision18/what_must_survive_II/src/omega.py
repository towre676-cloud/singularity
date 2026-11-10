import sympy as sp,json,sys
q,t=sp.symbols('q t',positive=True);co=json.load(open('../receipts_replay/j3_coefficients.json'));S=lambda s:sp.sympify(s,locals={'q':q})
w=1+t;f=(1-t)/t;Q=lambda e:sp.simplify(e).subs(q,sp.sqrt(t))
a1,b1,r21,r31=[S(co[n][1]) for n in('pi','phi','r2','r3')]
aq=a1+3*r21-2*r31;bq=b1-2*r21+2*r31
a=sp.cancel(sp.simplify((aq/q**3).subs(q,sp.sqrt(t))));b=sp.cancel(sp.simplify((bq/q**3).subs(q,sp.sqrt(t))))
th=lambda g:-(1-t)*t*sp.diff(g,t)
gam3=sum(c*S(co[n][3]) for n,c in(('G22',1),('G23',-2),('G33',1)))
H=lambda s:q**(23-2*s)*(q**2-1)**2*(q**2+1)**(s-2)
eP=2*H(7)-6*H(8)+4*H(9)
fq=q**-2-1
Gam=sp.cancel(sp.simplify(((gam3+eP)/(q**9*fq)).subs(q,sp.sqrt(t))))
Om=sp.cancel(sp.together(-(2*a+b)*w**3-b*th(w**3)+Gam))
print('a',sp.factor(a),'\nb',sp.factor(b),'\nGamma',sp.factor(Gam),'\nOmega',sp.factor(Om))
num,den=sp.fraction(Om);print('deg num',sp.degree(num,t),'den',den,' pole order at infinity',sp.degree(num,t)-sp.degree(den,t))
print('Omega at t=1',Om.subs(t,1));print('lowest t-order',sp.Poly(num,t).monoms()[-1],den)
json.dump({'Omega':str(sp.factor(Om))},open(sys.argv[1],'w'))
