import sys
from analyze import load,pats,P
from flint import nmod_mat
fn=sys.argv[1];rows=load(fn);Q=pats(fn+'.pats');Vm=max(r[0] for r in rows);PP=P
print("r(V,K): rank of rows vol<=V on columns n + patterns with |Q|<=K; last col = #columns")
for K in range(3,Vm+1):
    cols=[0]+[j+1 for j,q in enumerate(Q) if q[0]<=K];ci={c:i for i,c in enumerate(cols)};line=[]
    for V in range(max(K-2,1),Vm+1):
        R=[r for r in rows if r[0]<=V]
        M=[0]*(len(R)*len(cols))
        for i,(v,e,d) in enumerate(R):
            for c,x in d.items():
                if c in ci: M[i*len(cols)+ci[c]]=x.numerator*pow(x.denominator,-1,PP)%PP
        line.append(f"V{V}:{nmod_mat(len(R),len(cols),M,PP).rank()}")
    print(f"K={K} cols={len(cols)}"," ".join(line),flush=True)
