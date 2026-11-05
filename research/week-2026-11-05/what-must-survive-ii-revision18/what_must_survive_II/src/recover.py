# True recovery test: is the coordinate e_j in the row space of ALL rows through volume V, on ALL columns present?
import sys,json
from analyze import load,pats,P
from flint import nmod_mat,fmpz_mat,fmpq_mat,fmpq
from collections import defaultdict
fn=sys.argv[1];rows=load(fn);Q=pats(fn+'.pats');Vm=max(r[0] for r in rows);out={}
size=lambda c:0 if c==0 else Q[c-1][0]
for V in range(3,Vm+1):
    R=[r for r in rows if r[0]<=V]
    col=defaultdict(dict)
    for i,(v,e,d) in enumerate(R):
        for c,x in d.items(): col[c][i]=x
    allc=[0]+[j+1 for j,q in enumerate(Q) if q[0]<=V]
    cls=defaultdict(list)
    for c in allc: cls[tuple(sorted(col[c].items()))].append(c)
    keys=list(cls);M=[fmpq(0)]*(len(R)*len(keys))
    for j,k in enumerate(keys):
        for i,x in k: M[i*len(keys)+j]=fmpq(x.numerator,x.denominator)
    A=fmpq_mat(len(R),len(keys),M);RR,rk=A.rref()
    rec=set()
    for r in range(rk):
        nz=[j for j in range(len(keys)) if RR[r,j]!=0]
        if len(nz)==1 and len(cls[keys[nz[0]]])==1: rec.add(cls[keys[nz[0]]][0])
    by=defaultdict(lambda:[0,0])
    for c in allc:
        by[size(c)][1]+=1
        if c in rec: by[size(c)][0]+=1
    out[V]={"rank":int(rk),"classes":len(keys),"recoverable_by_size":{k:v for k,v in sorted(by.items())}}
    print(V,rk,len(keys),{k:tuple(v) for k,v in sorted(by.items())},flush=True)
json.dump(out,open(sys.argv[2],'w'),indent=1)
