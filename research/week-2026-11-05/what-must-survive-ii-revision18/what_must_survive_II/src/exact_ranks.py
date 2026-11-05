# Exact rational cumulative ranks per class, after cross-checking reconstructed rows against a second prime.
import sys,json,math
from analyze import load,pats,rr
from flint import fmpz_mat
f1,f2,out=sys.argv[1:4];P2=2**61-31
rows=load(f1);Q=pats(f1+'.pats')
# cross check
n=0
idx={(v,e):d for v,e,d in rows}
for l in open(f2):
    w=l.split();v,e,nz=map(int,w[:3]);d={int(w[3+2*i]):int(w[4+2*i]) for i in range(nz)}
    d1=idx[(v,e)];assert set(d)==set(d1)
    for c,x in d.items():
        assert x==d1[c].numerator*pow(d1[c].denominator,-1,P2)%P2;n+=1
assert sum(1 for _ in open(f2))==len(rows)
L=1
for v,e,d in rows:
    for x in d.values(): L=L*x.denominator//math.gcd(L,x.denominator)
Vm=max(r[0] for r in rows);res={"cross_prime_entries":n,"rows":len(rows),"lcm_den":L,"ranks":{}}
for k in range(4):
    cols=[0]+[j+1 for j,q in enumerate(Q) if q[2]>=k];ci={c:i for i,c in enumerate(cols)};seq=[]
    for V in range(1,Vm+1):
        R=[r for r in rows if r[0]<=V]
        col={}
        for i,(v,e,d) in enumerate(R):
            for c,x in d.items():
                if c in ci: col.setdefault(c,{})[i]=int(x*L)
        uniq={tuple(sorted(cv.items())) for cv in col.values()}   # identical columns do not change rank
        uniq=list(uniq);M=[[0]*len(uniq) for _ in R]
        for j,cv in enumerate(uniq):
            for i,val in cv: M[i][j]=val
        seq.append(int(fmpz_mat(M).rank()))
    res["ranks"][str(k)]=seq;print(k,seq,flush=True)
json.dump(res,open(out,'w'),indent=1)
