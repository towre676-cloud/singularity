# Conditional rank at volume V as columns of decreasing size are admitted: c(V,j) on patterns with |Q|>=V-j.
import sys,json
from analyze import load,pats,P
from flint import nmod_mat
fn=sys.argv[1];rows=load(fn);Q=pats(fn+'.pats');Vm=max(r[0] for r in rows);out={}
def rk(R,cols):
    ci={c:i for i,c in enumerate(cols)}
    if not R or not cols: return 0
    M=[0]*(len(R)*len(cols))
    for i,(v,e,d) in enumerate(R):
        for c,x in d.items():
            if c in ci: M[i*len(cols)+ci[c]]=x.numerator*pow(x.denominator,-1,P)%P
    return int(nmod_mat(len(R),len(cols),M,P).rank())
bysize={}
for j,q in enumerate(Q): bysize.setdefault(q[0],[]).append(j+1)
for V in range(5,Vm+1):
    B=[r for r in rows if r[0]<V];Rv=[r for r in rows if r[0]==V];seq=[]
    for j in range(0,V-2):
        cols=[c for k,l in bysize.items() if V-j<=k<=V for c in l]
        seq.append(rk(B+Rv,cols)-rk(B,cols))
    full=[0]+[c for l in bysize.values() for c in l if True]
    full=[c for c in full if c==0 or Q[c-1][0]<=V]
    out[V]={"cumulative_by_j":seq,"new":rk(B+Rv,full)-rk(B,full)};print(V,out[V],flush=True)
json.dump(out,open(sys.argv[2],'w'),indent=1)
