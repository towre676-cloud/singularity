# Source of high poles: W(V,j) with additional linear constraints on z (invariant sums at given sizes vanish).
import sys,json,itertools
from analyze import load,pats,P
from flint import nmod_mat
from collections import defaultdict
fn=sys.argv[1];rows=load(fn);Q=pats(fn+'.pats');Vm=max(r[0] for r in rows)
fx=lambda x:x.numerator*pow(x.denominator,-1,P)%P
def inv(q):
    k,E,cm,ed=q;deg=[0]*k;adj=[set() for _ in range(k)]
    for a,b in ed: deg[a]+=1;deg[b]+=1;adj[a].add(b);adj[b].add(a)
    e22=sum(deg[a]==2 and deg[b]==2 for a,b in ed)
    P222=sum(1 for v in range(k) if deg[v]==2 and all(deg[w]==2 for w in adj[v]))
    P232=sum(1 for v in range(k) if deg[v]==3 for a,c in itertools.combinations(adj[v],2) if deg[a]==2 and deg[c]==2)
    tri=defaultdict(int)
    for a,b,c in itertools.combinations(range(k),3):
        if b in adj[a] and c in adj[a] and c in adj[b]: tri[sum((deg[a],deg[b],deg[c]))]+=1
    return {"e22":e22,"P222":P222,"P232":P232,**{f"t{s}":tri[s] for s in (6,7,8,9)}}
INV=[inv(q) for q in Q]
def run(V,j,cons):
    # cons: list of (size, names)
    cols=[c for c,q in enumerate(Q) if V-j<=q[0]<=V];n=len(cols)
    colv=defaultdict(dict)
    S=set(cols)
    for v,e,d in rows:
        if v<=V:
            for c,x in d.items():
                if c-1 in S: colv[c-1][(v,e)]=fx(x)
    ix={c:i for i,c in enumerate(cols)}
    Bk=sorted({ve for c in cols for ve in colv[c] if ve[0]<V});bi={ve:i for i,ve in enumerate(Bk)}
    A=[[0]*n for _ in Bk];Rm=defaultdict(lambda:[0]*n)
    for c in cols:
        for ve,val in colv[c].items():
            if ve[0]<V: A[bi[ve]][ix[c]]=val
            else: Rm[ve[1]][ix[c]]=val
    extra=defaultdict(lambda:[0]*n)
    for size,names in cons:
        for c in cols:
            q=Q[c]
            if q[0]==size:
                for nm in names:
                    extra[(size,q[1],nm)][ix[c]]=INV[c][nm]%P
    A+=list(extra.values())
    M=nmod_mat(len(A),n,[v for r in A for v in r],P) if A else None
    R,rk=M.rref();rows_=[[int(R[i,c]) for c in range(n)] for i in range(rk)]
    piv=[next(c for c in range(n) if rows_[i][c]) for i in range(rk)];ps=set(piv)
    es=sorted(Rm);free=[c for c in range(n) if c not in ps]
    # polys as vectors
    top=None;vecs=[]
    Rlist={e:Rm[e] for e in es}
    for fc in free:
        p={}
        for e in es:
            s=Rlist[e][fc]
            for i,pc in enumerate(piv):
                if rows_[i][fc] and Rlist[e][pc]: s=(s-rows_[i][fc]*Rlist[e][pc])%P
            if s%P: p[e]=s%P
        if p: vecs.append(p)
    if not vecs: return (0,None)
    lo=min(min(p) for p in vecs);hi=max(max(p) for p in vecs);D=(hi-lo)//2+1
    rk=int(nmod_mat(len(vecs),D,[p.get(lo+2*i,0) for p in vecs for i in range(D)],P).rank())
    return (rk,(hi-3*V)//2)
out={}
allinv=["e22","P222","P232","t6","t7","t8","t9"]
for V,j in eval(sys.argv[3]):
    tests=[("none",[])]
    tests.append(("e22 at V-j",[(V-j,["e22"])]))
    tests.append(("all J3 inv at V-j",[(V-j,allinv)]))
    if j>=4: tests.append(("e22 at V-j and V-j+1",[(V-j,["e22"]),(V-j+1,["e22"])]))
    if j>=4: tests.append(("all inv at V-j, e22 at V-j+1",[(V-j,allinv),(V-j+1,["e22"])]))
    if j>=4: tests.append(("all inv at V-j and V-j+1",[(V-j,allinv),(V-j+1,allinv)]))
    if j>=5: tests.append(("all inv at V-j,V-j+1,V-j+2",[(V-j,allinv),(V-j+1,allinv),(V-j+2,allinv)]))
    r={}
    for nm,c in tests:
        r[nm]=run(V,j,c)
    out[f"{V},{j}"]=r;print(V,j,r,flush=True)
json.dump(out,open(sys.argv[2],'w'),indent=1)
