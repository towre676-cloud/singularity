# Exact rational ranks from CRT-certified rows; also records the panel-free cumulative ranks by class.
import sys,json,math
from fractions import Fraction as Fr
from analyze import pats
from flint import fmpz_mat
rf,pf,out=sys.argv[1:4];Q=pats(pf)
rows=[]
for l in open(rf):
    w=l.split();v,e,nz=int(w[0]),int(w[1]),int(w[2]);rows.append((v,e,{int(w[3+3*i]):Fr(int(w[4+3*i]),int(w[5+3*i])) for i in range(nz)}))
L=1
for v,e,d in rows:
    for x in d.values(): L=L*x.denominator//math.gcd(L,x.denominator)
Vm=max(r[0] for r in rows);res={"rows":len(rows),"lcm_den":L,"cross_prime_entries":sum(len(r[2]) for r in rows),"primes":3,"ranks":{}}
for k in range(4):
    keep={0}|{j+1 for j,q in enumerate(Q) if q[2]>=k};seq=[]
    for V in range(1,Vm+1):
        R=[r for r in rows if r[0]<=V];col={}
        for i,(v,e,d) in enumerate(R):
            for c,x in d.items():
                if c in keep: col.setdefault(c,{})[i]=int(x*L)
        U=list({tuple(sorted(cv.items())) for cv in col.values()});M=[[0]*len(U) for _ in R]
        for j,cv in enumerate(U):
            for i,val in cv: M[i][j]=val
        seq.append(int(fmpz_mat(M).rank()))
    res["ranks"][str(k)]=seq;print(k,seq,flush=True)
json.dump(res,open(out,'w'),indent=1)
