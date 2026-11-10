# Two-terminal identity with symmetric middle, exact rationals against brute force
from fractions import Fraction as Fr
import itertools,json
x,q=Fr(2,7),Fr(3,11);D=2
def G(F,a):
    r=Fr(1)
    for t in F:r*=sum(q**((a-b)**2)*x**b*G(t,b) for b in range(D+1))
    return r
leaf=();cher=(leaf,);two=(leaf,leaf);ch2=(cher,)
def tree(mid,left,right):
    # mid: path of vertices with mirrored forests; returns parent list via edges
    edges=[];cnt=[0]
    def new():
        cnt[0]+=1;return cnt[0]-1
    def att(F,p):
        for t in F:
            v=new();edges.append((p,v));att(t,v)
    vs=[new() for _ in mid]
    for i in range(len(vs)-1):edges.append((vs[i],vs[i+1]))
    for i,F in enumerate(mid):att(F,vs[i])
    att(left,vs[0]);att(right,vs[-1])
    return cnt[0],edges,vs
def brute(n,edges):
    return sum(x**sum(h)*q**sum((h[u]-h[v])**2 for u,v in edges) for h in itertools.product(range(D+1),repeat=n))
def K(mid,a,b):
    # transfer along path
    m=len(mid);st={a:x**a*G(mid[0],a)}
    for i in range(1,m):
        ns={}
        for c in (range(D+1) if i<m-1 else [b]):
            ns[c]=sum(st[d]*q**((c-d)**2) for d in st)*x**c*G(mid[i],c)
        st=ns
    return st[b]
ok=True;cases=[([(),()],(leaf,),(cher,),(cher,),(leaf,)),([(),(leaf,),()],(leaf,),(cher,),(leaf,),(cher,)),([(),(),()],(leaf,leaf),(cher,),(cher,),(leaf,))]
for mid,U,V,c1,c2 in cases:
    n,e,_=tree(mid,U+c1,V+c2);n2,e2,_=tree(mid,U+c2,V+c1)
    if max(n,n2)>10:print('skip',n);continue
    d=brute(n,e)-brute(n2,e2)
    W=lambda f,g,a,b:G(f,a)*G(g,b)-G(f,b)*G(g,a)
    s=sum(K(mid,a,b)*W(U,V,a,b)*W(c1,c2,a,b) for a in range(D+1) for b in range(D+1))/2
    ok&=d==s;print(n,d==s)
json.dump(dict(ok=bool(ok)),open('id2.json','w'));print('identity',ok)
