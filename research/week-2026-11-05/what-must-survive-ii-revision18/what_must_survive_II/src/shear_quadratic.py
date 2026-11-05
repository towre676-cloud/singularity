# Direct original-coordinate gates for quadratic u: no change of variables is used.
import sympy as sp,json,sys
q,p=sp.symbols('q p')
def gate(H,f,k): return sp.expand(sum((-1)**j*sp.binomial(k,j)*sp.diff(H,q,k-j,p,j)*sp.diff(f,q,j,p,k-j) for j in range(k+1)))
out=[]
for u in (q**2,3*q**2+q):
    Q=p+u
    for Pz,eps in ((Q**2+q,1),(Q**3+2*Q+q,1),(Q**4+q,3),(Q**5,0)):
        H=sp.expand(Pz+eps*q) if False else sp.expand(Pz)
        for f in (Q**3,Q**5,Q**6,q):
            for k in (3,5,7,9): assert gate(H,sp.expand(f),k)==0
    H=sp.expand(Q**2+q)
    for f in (q*Q,q**2):
        for k in (3,5,7,9): assert gate(H,sp.expand(f),k)==0
# non-covariance witness: the gate is NOT that of flat (q,Q) coordinates
Q=p+q**2;H=sp.expand(Q**3+q);f=sp.expand(q*Q)
g=gate(H,f,3);out.append(str(sp.factor(g)));assert g!=0
json.dump({"all_odd_gates_vanish_through_9":True,"qQ_gate_for_m3":out},open(sys.argv[1],'w'),indent=1);print(out)
