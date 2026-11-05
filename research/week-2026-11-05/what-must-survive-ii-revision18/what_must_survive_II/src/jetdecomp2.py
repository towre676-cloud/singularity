import sys,json
from analyze import load,pats,P
from flint import nmod_mat
fn=sys.argv[1];rows=load(fn);Q=pats(fn+'.pats');Vm=max(r[0] for r in rows);out={}
def rk(R,cols):
    if not R or not cols: return 0
    ci={c:i for i,c in enumerate(cols)};M=[0]*(len(R)*len(cols))
    for i,(v,e,d) in enumerate(R):
        for c,x in d.items():
            if c in ci: M[i*len(cols)+ci[c]]=x.numerator*pow(x.denominator,-1,P)%P
    return int(nmod_mat(len(R),len(cols),M,P).rank())
for k in range(4):
    by={}
    for j,q in enumerate(Q):
        if q[2]>=k: by.setdefault(q[0],[]).append(j+1)
    out[k]={}
    for V in range(4,Vm+1):
        B=[r for r in rows if r[0]<V];Rv=[r for r in rows if r[0]==V];seq=[];prev=0
        for j in range(0,V-2):
            cols=[c for s,l in by.items() if V-j<=s<=V for c in l]
            c=rk(B+Rv,cols)-rk(B,cols);seq.append(c-prev);prev=c
        cols=[0]+[c for s,l in by.items() if s<=V for c in l]
        tot=rk(B+Rv,cols)-rk(B,cols)
        out[k][V]={"c":seq,"tail_n":tot-prev,"new":tot};print(k,V,seq,tot-prev,tot,flush=True)
json.dump(out,open(sys.argv[2],'w'),indent=1)
