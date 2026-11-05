exec(open('e.py').read().split("if __name__")[0])
import random
from fractions import Fraction
def spins(T,N):
    return {min(t,N-t):(1 if t<N-t else -1) for t in T if t!=N-t and (N-t) not in T}
class L(Counter):pass
def mul(a,b):
    c=Counter()
    for i,u in a.items():
        for j,v in b.items():c[i+j]+=u*v
    return c
def addc(c,d,m=1):
    for k,v in d.items():c[k]+=m*v
def g(p):return Counter({-p:1,0:-1})
def h(q,N):
    c=Counter({q:1});c[N-q]-=1;return c
def s(q,N):
    c=Counter({q:1});c[N-q]+=1;return c
def folds(T,N):return [min(t,N-t) for t in T]
def Lam(p,F,N):
    c=Counter();addc(c,h(p,N),-(2*p+1));c[0]+=1;c[N-2*p]-=1
    for r in F:
        if r<p:
            addc(c,h(p,N));addc(c,h(r,N),-1);c[r-p]+=1;c[p-r]-=1;addc(c,g(p));c2=Counter();addc(c2,g(p));addc(c2,g(r),-1)
            c.subtract(g(p))
            for k,v in c2.items():c[k-2]+=v
    return c
def Pi(q,F,N):
    c=Counter()
    for r in F:
        if r>q:
            for k,v in s(q,N).items():c[k-2]+=v
            for k,v in s(r,N).items():c[k-2]-=v
    addc(c,mul(s(q,N),h(q,N)),-1);return c
def predict(T1,T2,N):
    F=folds(T1,N);s1,s2=spins(T1,N),spins(T2,N);ks=sorted(s1);c=Counter()
    for i,p in enumerate(ks):
        for q in ks[i+1:]:
            t=s1[p]*s1[q]-s2[p]*s2[q]
            if t:
                addc(c,mul(h(q,N),Lam(p,F,N)),t);addc(c,mul(g(p),Pi(q,F,N)),t)
    return {k:v for k,v in c.items() if v}
def T_of(p):
    t=0;c=[p[0]]+[1+a for a in p[1:-1]]+[p[-1]];T=[]
    for z in c[:-1]:t+=z;T.append(t)
    return T,sum(c)
if __name__=='__main__':
    ok=True;cnt=0;cens=[]
    for n in range(8,31):
        for l in open(f'/root/wms/spine/d{n}.txt'):
            if not l.startswith('S2'):continue
            ps=[tuple(map(int,a.strip(',').split(','))) for a in l.split()[1:]];N=n-2
            T1,T2=T_of(ps[0])[0],T_of(ps[1])[0]
            # align orientation: same fold orientation irrelevant
            d=Counter(H3T(T1,N));d.subtract(H3T(T2,N));d={k:4*v for k,v in d.items() if v}
            pr=predict(T1,T2,N);cnt+=1
            if d!=pr:
                ok=False;print('mismatch',n,T1,T2);print(sorted(d.items())[:12]);print(sorted(pr.items())[:12]);break
            top=max(d);cens.append((n,top,d[top],min(d),d[min(d)]))
        if not ok:break
    print('reduced bilinear form on census',ok,cnt)
    import json;json.dump(cens,open('tops.json','w'))
