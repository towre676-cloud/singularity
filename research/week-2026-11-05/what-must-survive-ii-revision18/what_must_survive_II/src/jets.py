import sys
from analyze import load,pats
from collections import defaultdict
fn=sys.argv[1]
rows=load(fn);Q=pats(fn+'.pats');Vm=max(r[0] for r in rows)
# column vectors: b[j][(V,e)]
col=defaultdict(dict)
for v,e,d in rows:
    for c,x in d.items(): col[c][(v,e)]=x
def inv(q):
    n,m,cm,E=q;deg=[0]*n
    for a,b in E: deg[a]+=1;deg[b]+=1
    e22=sum(1 for a,b in E if deg[a]==2 and deg[b]==2)
    return (n,m,e22)
for eps in range(0,6):
    line=[]
    for k in range(3,Vm-eps+1):
        idx=[j for j,q in enumerate(Q) if q[0]==k]
        # jet of order eps: coefficients at V=k..k+eps
        cl=defaultdict(list)
        for j in idx:
            key=tuple(sorted((ve,x) for ve,x in col[j+1].items() if ve[0]<=k+eps))
            cl[key].append(j)
        inv0={}
        line.append(f"k{k}:{len(idx)}->{len(cl)}")
    print("eps",eps," ".join(line))
# test: eps=1 determined by (k,E); eps=2 by (k,E,e22,+?) 
for eps,fn_inv in [(1,lambda q:(q[0],q[1]))]:
    bad=0;seen={}
    for j,q in enumerate(Q):
        if q[0]+eps>Vm: continue
        key=tuple(sorted((ve,x) for ve,x in col[j+1].items() if ve[0]<=q[0]+eps))
        i=fn_inv(q)
        if i in seen and seen[i]!=key: bad+=1
        seen.setdefault(i,key)
    print("eps",eps,"violations of (k,E) determination:",bad)
