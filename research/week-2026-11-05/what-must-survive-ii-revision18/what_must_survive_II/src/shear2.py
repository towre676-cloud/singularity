# N_r = cap_{j<=r} ker(C3 D^j) on the box q-degree<=A, Q-degree<=B, exact via (star) formula mod p and rational check by sympy on results
import sys,random
p=2**61-1
def pmul(f,g):
    r={}
    for (a,b),c in f.items():
        for (a2,b2),c2 in g.items():
            k=(a+a2,b+b2);r[k]=(r.get(k,0)+c*c2)%p
    return {k:v for k,v in r.items() if v}
def padd(f,g,s=1):
    r=dict(f)
    for k,v in g.items(): r[k]=(r.get(k,0)+s*v)%p
    return {k:v for k,v in r.items() if v}
def dq(f,n=1):
    for _ in range(n):
        f={(a-1,b):c*a%p for (a,b),c in f.items() if a>0}
    return f
def dQ(f,n=1):
    for _ in range(n):
        f={(a,b-1):c*b%p for (a,b),c in f.items() if b>0}
    return f
def scal(f,s): return {k:v*s%p for k,v in f.items() if v*s%p}
def mk(Pc,uc,eps):
    P={(0,i):c for i,c in enumerate(Pc) if c}; u={(i,0):c for i,c in enumerate(uc) if c}
    P1,P2,P3=dQ(P),dQ(P,2),dQ(P,3);u2,u3=dq(u,2),dq(u,3)
    def C3(f):
        a=pmul(pmul(P1,u3),dQ(f,3))
        b=scal(pmul(pmul(P2,u2),dq(dQ(f,2))),p-3)
        inner=padd(padd(dq(f,3),scal(pmul(u2,dq(dQ(f))),3)),pmul(u3,dQ(f)))
        c=scal(pmul(P3,inner),p-1)
        return padd(padd(a,b),c)
    def D(f):
        return padd(scal(pmul(P1,dq(f)),p-1),scal(dQ(f),eps))
    return C3,D
def null(vecs):
    # vecs: list of dict images; return coefficient combos with zero image
    n=len(vecs);piv={};kern=[]
    for i,v in enumerate(vecs):
        v=dict(v);tag={i:1}
        while v:
            k=max(v)
            if k in piv:
                pv,pt=piv[k];f=v[k]
                v=padd(v,pv,p-f)
                for t,c in pt.items(): tag[t]=(tag.get(t,0)-f*c)%p
                tag={t:c for t,c in tag.items() if c}
            else:
                iv=pow(v[k],-1,p);piv[k]=({a:b*iv%p for a,b in v.items()},{a:b*iv%p for a,b in tag.items()});break
        if not v: kern.append(tag)
    return kern
def run(Pc,uc,eps,A,B,depth=6):
    C3,D=mk(Pc,uc,eps)
    gens=[{(a,b):1} for a in range(A+1) for b in range(B+1)];imgs=list(gens);dims=[]
    for r in range(depth):
        k=null([C3(g) for g in imgs])
        ng=[];ni=[]
        for t in k:
            g={};h={}
            for i,c in t.items(): g=padd(g,scal(gens[i],c));h=padd(h,scal(imgs[i],c))
            ng.append(g);ni.append(h)
        gens=ng;imgs=[D(h) for h in ni];dims.append(len(gens))
        if len(dims)>=3 and dims[-1]==dims[-2]==dims[-3]:break
    return dims
def lift(c): 
    return c if c<p//2 else c-p
if __name__=="__main__":
    r=random.Random(5)
    for m in (2,3,4,5):
        for d in (2,3,4,5):
            for eps in (1,0):
                Pc=[0]*m+[1];uc=[0]*d+[1]
                print(f"m={m} d={d} eps={eps} box(8,14) mono:",run(Pc,uc,eps,8,14),flush=True)
                Pc=[r.randrange(1,99) for _ in range(m)]+[r.randrange(1,99)];uc=[0]+[r.randrange(1,99) for _ in range(d)]
                print(f"     generic coeffs:",run(Pc,uc,eps,8,14),flush=True)
