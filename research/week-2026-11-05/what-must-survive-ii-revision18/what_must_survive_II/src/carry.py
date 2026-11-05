import sympy as sp,json,sys
t=sp.Symbol('t',positive=True);q=sp.Symbol('q',positive=True)
d=json.load(open(sys.argv[1]));Tq=lambda s:sp.cancel(sp.simplify(sp.sympify(s,locals={'q':q}).subs(q,sp.sqrt(t))))
w=1+t
a=(t**4-3*t**2-3*t+3)/t;b=2*(t+1)*(t**2+t-1)/t
th=lambda g:-(1-t)*t*sp.diff(g,t)
C={'X':t**-1*(t-1)**2*w**4,'Y':t**-2*(t-1)**2*w**5}
c4={'X':d['X4'],'Y':d['Y4']}
for k,s in (("(2, 2, 2)",6),("(2, 2, 3)",7),("(2, 3, 3)",8),("(3, 3, 3)",9)):
    C[f'T{s}']=-t**((21-2*s-9)/sp.Integer(2))*(t-1)**3*w**(s-3);c4[f'T{s}']=d['T4'][k]
res={}
for n in C:
    Om=sp.cancel(sp.together(Tq(c4[n])/t**6-3*a*C[n]-b*th(C[n])))
    nu,de=sp.fraction(Om);p=sp.degree(nu,t)-sp.degree(de,t)
    res[n]={"carry_pole":int(p),"row3_pole":int(sp.degree(sp.fraction(sp.cancel(C[n]))[0],t)-sp.degree(sp.fraction(sp.cancel(C[n]))[1],t)),"Omega":str(sp.factor(Om))};print(n,res[n])
# second differences among triangle types are not reducible; report differences of Omega
json.dump(res,open(sys.argv[2],'w'),indent=1)
