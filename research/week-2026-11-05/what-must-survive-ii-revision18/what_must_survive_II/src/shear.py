# Detection depth experiments for H=P(Q)+eps q, Q=p+u(q): all arithmetic exact mod a 61-bit prime with rational cross-check where stated
import sympy as sp, itertools, sys, json
from flint import fmpq_mat, fmpq
q,p=sp.symbols('q p')
def run(Pc,u,epsv,qdeg,Qdeg,maxdepth=8,extra_gates=(5,7)):
    Q=p+u; z=sp.Symbol('z')
    H=sp.expand(sum(c*Q**i for i,c in enumerate(Pc))+epsv*q)
    Hp=sp.Poly(H,q,p)
    D=lambda f:sp.expand(sp.diff(H,q)*sp.diff(f,p)-sp.diff(H,p)*sp.diff(f,q))
    def gate(f,k):
        return sp.expand(sum((-1)**j*sp.binomial(k,j)*sp.diff(H,q,k-j,p,j)*sp.diff(f,q,j,p,k-j) for j in range(k+1)))
    basis=[(a,b) for a in range(qdeg+1) for b in range(Qdeg+1)]
    mons=[sp.expand(q**a*Q**b) for a,b in basis]
    def rowsof(img):
        keys={}
        vecs=[]
        for g in img:
            d=sp.Poly(g,q,p).as_dict() if g!=0 else {}
            vecs.append(d)
            for k in d: keys.setdefault(k,len(keys))
        M=[[0]*len(img) for _ in keys]
        for j,d in enumerate(vecs):
            for k,v in d.items(): M[keys[k]][j]=v
        return M
    def nullspace(M,n):
        if not M: return [[sp.Integer(int(i==j)) for j in range(n)] for i in range(n)]
        A=fmpq_mat(len(M),n,[fmpq(int(sp.Rational(x).p),int(sp.Rational(x).q)) for r in M for x in r])
        R,rk=A.rref()
        piv=[];r=0
        for c in range(n):
            if r<rk and R[r,c]!=0: piv.append(c);r+=1
        free=[c for c in range(n) if c not in piv]
        out=[]
        for fc in free:
            v=[sp.Integer(0)]*n;v[fc]=sp.Integer(1)
            for i,pc in enumerate(piv):
                x=R[i,fc];v[pc]=-sp.Rational(int(x.p),int(x.q))
            out.append(v)
        return out
    cur=list(mons);imgs=list(mons)
    gens=[[1 if i==j else 0 for j in range(len(mons))] for i in range(len(mons))]
    dims=[];seqs=[]
    # N_r computed by successive restriction: images imgs[i]=D^r(gen i)
    for r in range(maxdepth):
        M=rowsof([gate(g,3) for g in imgs])
        ns=nullspace(M,len(imgs))
        if not ns: dims.append(0);gens=[];break
        newg=[];newi=[]
        for v in ns:
            newg.append([sum(v[i]*gens[i][j] for i in range(len(gens))) for j in range(len(mons))])
            newi.append(sp.expand(sum(v[i]*imgs[i] for i in range(len(gens)) if v[i]!=0)))
        gens=newg;imgs=[D(g) for g in newi]
        dims.append(len(gens))
        if len(dims)>=2 and dims[-1]==dims[-2] and len(dims)>=3 and dims[-2]==dims[-3]: break
    core=[sp.factor(sp.expand(sum(g[j]*sp.Symbol('q')**basis[j][0]*z**basis[j][1] for j in range(len(mons))))) for g in gens]
    return dims,core
if __name__=="__main__":
    cases=[("Q^2+q,u=q^3",[0,0,1],q**3,1),("Q^2+q,u=q^4",[0,0,1],q**4,1),("Q^3+q,u=q^3",[0,0,0,1],q**3,1),("Q^3+q,u=q^4",[0,0,0,1],q**4,1),
           ("Q^4+q,u=q^3",[0,0,0,0,1],q**3,1),("Q^3+Q+q,u=q^3",[0,1,0,1],q**3,1),("Q^3+q,u=q^2",[0,0,0,1],q**2,1),("Q^2+q,u=q^2",[0,0,1],q**2,1),("Q^3 eps=0,u=q^3",[0,0,0,1],q**3,0),("Q^2 eps=0,u=q^3",[0,0,1],q**3,0)]
    for name,Pc,u,e in cases:
        d,c=run(Pc,u,e,4,5)
        print(name,"dims",d,"core",c,flush=True)
