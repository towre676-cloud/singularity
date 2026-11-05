# Certificates for promoted defects. Usage: promo.py rows out V j [e_target]
# Works on column classes (identical signature through volume V), all arithmetic mod P on certified-form rows.
import sys,json,itertools
from analyze import load,pats,P
from flint import nmod_mat
from collections import defaultdict
fn,out=sys.argv[1:3];rows=load(fn);Q=pats(fn+'.pats')
fx=lambda x:x.numerator*pow(x.denominator,-1,P)%P
def e22(q):
    k,E,cm,ed=q;deg=[0]*k
    for a,b in ed: deg[a]+=1;deg[b]+=1
    return sum(deg[a]==2 and deg[b]==2 for a,b in ed)
def setup(V,j):
    keep={c+1 for c,q in enumerate(Q) if V-j<=q[0]<=V};colv=defaultdict(dict)
    for v,e,d in rows:
        if v<=V:
            for c,x in d.items():
                if c in keep: colv[c][(v,e)]=fx(x)
    cls=defaultdict(list)
    for c in keep: cls[tuple(sorted(colv[c].items()))].append(c-1)
    keys=[k for k in cls if k];return keys,cls
def rref(A,n):
    if not A: return [],[]
    M=nmod_mat(len(A),n,[v for r in A for v in r],P);R,rk=M.rref()
    Rr=[[int(R[i,c]) for c in range(n)] for i in range(rk)];piv=[next(c for c in range(n) if Rr[i][c]) for i in range(rk)]
    return Rr,piv
def analyse(V,j,extra=None,target=None):
    keys,cls=setup(V,j);n=len(keys)
    B=sorted({ve for k in keys for ve,_ in k if ve[0]<V});bi={ve:i for i,ve in enumerate(B)}
    A=[[0]*n for _ in B];Rm=defaultdict(lambda:[0]*n)
    for jj,k in enumerate(keys):
        for ve,val in k:
            if ve[0]<V: A[bi[ve]][jj]=val
            else: Rm[ve[1]][jj]=val
    # extra constraints: separate by class is invalid unless the invariant is constant on a class; the class is split by a check below
    if extra:
        for fn_ in extra:
            A+=fn_(keys,cls)
    Rr,piv=rref(A,n);ps=set(piv);free=[c for c in range(n) if c not in ps]
    es=sorted(Rm);res={"classes":n,"rank_B":len(piv)}
    vec=[]
    for fc in free:
        p={}
        for e in es:
            s=Rm[e][fc]
            for i,pc in enumerate(piv):
                if Rr[i][fc] and Rm[e][pc]: s=(s-Rr[i][fc]*Rm[e][pc])%P
            if s%P: p[e]=s%P
        if p: vec.append((fc,p))
    # echelon by top exponent gives the full pole profile
    basis={}
    for fc,p in vec:
        p=dict(p)
        while p:
            top=max(p)
            if top in basis:
                f=p[top]
                for e,c in basis[top].items():
                    p[e]=(p.get(e,0)-f*c)%P
                p={e:c for e,c in p.items() if c}
            else:
                iv=pow(p[top],-1,P);basis[top]={e:c*iv%P for e,c in p.items()};break
    prof=sorted((e-3*V)//2 for e in basis)
    res["dim"]=len(basis);res["pole_profile"]=prof;res["max_pole"]=prof[-1] if prof else None
    # witness at target: sparsest found among free variables
    if target is not None:
        res["target_e"]=target;cands=[(fc,p) for fc,p in vec if p.get(target) or max(p)>=target]
        hits=[fc for fc,p in vec if p.get(target,0)]
        res["free_hits"]=len(hits)
        if hits:
            best=None
            for fc in hits:
                sup=[(pc,(-Rr[i][fc])%P) for i,pc in enumerate(piv) if Rr[i][fc]]+[(fc,1)]
                if best is None or len(sup)<len(best): best=sup
            lift=[(cls[keys[c]][0],val) for c,val in best]
            res["witness"]=[{"pattern":Q[c][3],"k":Q[c][0],"E":Q[c][1],"e22":e22(Q[c]),"coef":val} for c,val in lift]
            res["witness_support"]=len(lift);res["lowest_size"]=min(Q[c][0] for c,_ in lift)
            agg=defaultdict(int)
            for c,val in lift:
                if Q[c][0]==V-j: agg[Q[c][1]]=(agg[Q[c][1]]+val*e22(Q[c]))%P
            res["A_E_at_lowest"]={str(k):v for k,v in sorted(agg.items())}
    # ceiling: rows above target lie in span of B
    return res
V,j=int(sys.argv[3]),int(sys.argv[4]);t=int(sys.argv[5]) if len(sys.argv)>5 else None
r=analyse(V,j,target=t);print({k:v for k,v in r.items() if k!='witness'});json.dump(r,open(out,'w'),indent=1)
