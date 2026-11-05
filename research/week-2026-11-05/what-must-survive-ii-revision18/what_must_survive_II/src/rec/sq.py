exec(open('ex.py').read().split("res={}")[0])
from fractions import Fraction as Fr
import random,json
out={}
# 1. square identity, exact rationals, truncated heights; brute force on small trees
def G(F,a,x,q,D):
    r=Fr(1)
    for t in F:
        r*=sum(q**((a-b)**2)*x**b*G(t,b,x,q,D) for b in range(D+1))
    return r
def Lsides(L,R,x,q,D):
    return sum(q**((a-b)**2)*x**(a+b)*G(L,a,x,q,D)*G(R,b,x,q,D) for a in range(D+1) for b in range(D+1))
def brute(par,x,q,D):
    n=len(par);tot=Fr(0)
    for h in itertools.product(range(D+1),repeat=n):
        E=sum((h[i]-h[par[i]])**2 for i in range(1,n));tot+=x**sum(h)*q**E
    return tot
ok=True;x,q=Fr(2,7),Fr(3,11)
for A,B,D in [(((),),(((),),),2),((((),),),((),()),2),(((),()),(((),()),),1),((((),),()),(((),()),),1)]:
    d=Lsides(A+A,B+B,x,q,D)-Lsides(A+B,A+B,x,q,D)
    sq=sum(q**((a-b)**2)*x**(a+b)*(G(A,a,x,q,D)*G(B,b,x,q,D)-G(A,b,x,q,D)*G(B,a,x,q,D))**2 for a in range(D+1) for b in range(D+1))/2
    ok&=(d==sq)
    if len(enc(A+A,B+B).split())<=13:
        p=list(map(int,enc(A+A,B+B).split()[1:]));ok&=brute(p,x,q,D)==Lsides(A+A,B+B,x,q,D)
out['square_identity']=bool(ok);print(out)
# 2. volume: fingerprints of G_W(a) mod x^{V+1}
P=(1<<61)-1
def run_fp(V,wmax,qv):
    @lru_cache(None)
    def Gt(t,a):
        # series in x mod x^{V+1}: arm t attached to parent height a: sum_b q^{(a-b)^2}x^b prod children G(c,b)
        r=[0]*(V+1)
        for b in range(0,V+1):
            s=[0]*(V+1);s[b]=pow(qv,(a-b)**2,P)
            for c in t:
                g=Gt(c,b);n_=[0]*(V+1)
                for i,u in enumerate(s):
                    if u:
                        for j,v in enumerate(g):
                            if i+j<=V and v:n_[i+j]=(n_[i+j]+u*v)%P
                s=n_
            for i in range(V+1):r[i]=(r[i]+s[i])%P
        return tuple(r)
    def GF(F,a):
        s=[0]*(V+1);s[0]=1
        for t in F:
            g=Gt(t,a);n_=[0]*(V+1)
            for i,u in enumerate(s):
                if u:
                    for j,v in enumerate(g):
                        if i+j<=V and v:n_[i+j]=(n_[i+j]+u*v)%P
            s=n_
        return tuple(s)
    res=None
    for w in range(2,wmax+1):
        g=defaultdict(list)
        for F in forests(w):
            g[tuple(GF(F,a) for a in range(V+1))].append(F)
        c=[v for v in g.values() if len(v)>1]
        if c:return w,c[0][:2],len(c)
    return None
for V in (1,2,3,4):
    r=run_fp(V,12,random.Random(V).randrange(2,P))
    print('V',V,r and (r[0],str(r[1])[:150],r[2]),flush=True);out[f'V{V}']=r and dict(weight=r[0],pair=str(r[1]),classes=r[2])
    if r:
        a,b=r[1]
        # exact confirm: min-normalised volume histogram of T,S by direct enumeration of multisets
        pass
json.dump(out,open('sq.json','w'),indent=1)
