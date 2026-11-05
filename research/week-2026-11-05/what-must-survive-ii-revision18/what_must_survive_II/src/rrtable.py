# For each V and j: the polynomial space W(V,j) of row values on ker(earlier rows), directions supported on sizes >= V-j.
import sys,json
from analyze import load,pats,P
from flint import nmod_mat
from collections import defaultdict
fn=sys.argv[1];rows=load(fn);Q=pats(fn+'.pats');Vm=max(r[0] for r in rows);out={}
fx=lambda x:x.numerator*pow(x.denominator,-1,P)%P
def nullsp(A,n):
    # A list of dict rows; dense mod p via nmod_mat rref
    if not A: return [[int(i==j) for j in range(n)] for i in range(n)]
    M=nmod_mat(len(A),n,[v for r in A for v in r],P);R,rk=M.rref()
    piv=[];r=0
    for c in range(n):
        if r<rk and int(R[r,c])!=0: piv.append(c);r+=1
    free=[c for c in range(n) if c not in set(piv)];res=[]
    for fc in free:
        v=[0]*n;v[fc]=1
        for i,pc in enumerate(piv): v[pc]=(-int(R[i,fc]))%P
        res.append(v)
    return res
for V in range(7,Vm+1):
    out[V]={}
    for j in range(0,V-2):
        cols=[c+1 for c,q in enumerate(Q) if V-j<=q[0]<=V]
        ci={c:i for i,c in enumerate(cols)}
        # merge identical columns over rows<=V
        sig=defaultdict(list);colv=defaultdict(dict)
        for idx,(v,e,d) in enumerate(rows):
            if v<=V:
                for c,x in d.items():
                    if c in ci: colv[c][(v,e)]=fx(x)
        for c in cols: sig[tuple(sorted(colv[c].items()))].append(c)
        reps=[k for k in sig if k];n=len(reps)
        rowidx=sorted({ve for k in reps for ve,_ in k});ri={ve:i for i,ve in enumerate(rowidx)}
        Bk=[ve for ve in rowidx if ve[0]<V];bi={ve:i for i,ve in enumerate(Bk)}
        A=[[0]*n for _ in Bk];Rm=defaultdict(lambda:[0]*n)
        for jj,k in enumerate(reps):
            for ve,val in k:
                if ve[0]<V: A[bi[ve]][jj]=val
                else: Rm[ve[1]][jj]=val
        ns=nullsp(A,n)
        es=sorted(Rm)
        polys=[]
        for v in ns:
            polys.append({e:sum(a*b for a,b in zip(Rm[e],v))%P for e in es})
        polys=[{e:c for e,c in p.items() if c} for p in polys]
        polys=[p for p in polys if p]
        if not polys: out[V][j]={"dim":0};continue
        allE=sorted({e for p in polys for e in p})
        lo,hi=allE[0],allE[-1];D=(hi-lo)//2+1
        Mt=nmod_mat(len(polys),D,[p.get(lo+2*i,0) for p in polys for i in range(D)],P)
        dim=int(Mt.rank())
        # order at t=1: largest o such that all polys vanish to order o: Hasse derivatives
        def ordt1(p):
            o=0
            coeff=[p.get(lo+2*i,0) for i in range(D)]
            while True:
                s=sum(c for c in coeff)%P
                if s: return o
                # divide by (t-1)
                new=[0]*(len(coeff)-1);car=0
                for i in range(len(coeff)-1,0,-1):
                    car=(car+coeff[i])%P;new[i-1]=car
                coeff=new;o+=1
        ord1=min(ordt1(p) for p in polys[:400])
        out[V][j]={"dim":dim,"emin":lo,"emax":hi,"ord_t1":ord1,"L_dim":D-ord1}
    print(V,{j:(d['dim'],d.get('emin'),d.get('emax'),d.get('ord_t1'),d.get('L_dim')) for j,d in out[V].items() if j<=6},flush=True)
json.dump(out,open(sys.argv[2],'w'),indent=1)
