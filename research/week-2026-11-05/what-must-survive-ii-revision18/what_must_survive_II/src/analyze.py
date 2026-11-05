import sys,math
from fractions import Fraction as Fr
from flint import fmpz_mat
P=2**61-1
def rr(a,p=P):
    # rational reconstruction with den<=2^20
    r0,r1,t0,t1=p,a,0,1
    while r1*r1*2>p/ (2**20)*1 and r1> 2**38:
        q=r0//r1;r0,r1=r1,r0-q*r1;t0,t1=t1,t0-q*t1
    if t1<0: r1,t1=-r1,-t1
    return Fr(r1,t1)
def load(fn):
    rows=[]
    for l in open(fn):
        w=l.split();v,e,nz=map(int,w[:3]);d={int(w[3+2*i]):rr(int(w[4+2*i])) for i in range(nz)}
        rows.append((v,e,d))
    return rows
def pats(fn):
    out=[]
    for l in open(fn):
        w=list(map(int,l.split()));out.append((w[0],w[1],w[2],[(w[3+2*i],w[4+2*i]) for i in range(w[1])]))
    return out
if __name__=="__main__":
    rows=load(sys.argv[1]);Q=pats(sys.argv[1]+'.pats')
    dens=set();mx=0
    for v,e,d in rows:
        for c,x in d.items(): dens.add(x.denominator);mx=max(mx,abs(x.numerator))
    print("max den",max(dens),"max |num|",mx,"dens",sorted(dens)[:20])
    Vm=max(r[0] for r in rows)
    for k in range(4):
        cols=[0]+[j+1 for j,q in enumerate(Q) if q[2]>=k];ci={c:i for i,c in enumerate(cols)}
        # modular greedy pivots with exact final rank
        basis={};tot=0;out=[]
        p2=P
        all_rows=[]
        for V in range(1,Vm+1):
            nw=[]
            for v,e,d in rows:
                if v!=V: continue
                r={}
                for c,x in d.items():
                    if c in ci: r[ci[c]]=x.numerator*pow(x.denominator,-1,p2)%p2
                for pc in sorted(list(basis)):
                    if pc in r and r[pc]:
                        f=r[pc]
                        for c2,y in basis[pc].items(): r[c2]=(r.get(c2,0)-f*y)%p2
                r={c:y for c,y in r.items() if y}
                if r:
                    pc=min(r);iv=pow(r[pc],-1,p2);r={c:y*iv%p2 for c,y in r.items()};basis[pc]=r;nw.append(e)
            tot+=len(nw);out.append((V,len(nw),tot,nw))
        print("class",k)
        for o in out: print(" ",o)
        if k==0:
            es={V:sorted(e for v,e,d in rows if v==V and any(c>0 for c in d)) for V in range(1,Vm+1)}
            for V in es: print("  V",V,"cycle-sensitive e: count",len(es[V]),"range",es[V][:1],es[V][-1:])
    # exact rational rank of whole matrix through flint
    cols=sorted({c for r in rows for c in r[2]});ci={c:i for i,c in enumerate(cols)}
    L=1
    for d in dens: L=L*d//math.gcd(L,d)
    M=[[0]*len(cols) for _ in rows]
    for i,(v,e,d) in enumerate(rows):
        for c,x in d.items(): M[i][ci[c]]=int(x*L)
    print("exact integer matrix",len(rows),len(cols),"rank over Q:",fmpz_mat(M).rank())
