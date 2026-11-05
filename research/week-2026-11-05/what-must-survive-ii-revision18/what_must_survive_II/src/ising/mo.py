exec(open('e.py').read().split("if __name__")[0])
from math import comb
exec(open('/root/wms/spine/fl.py').read().split("tot={}")[0].split("def T_of")[1].join(["def T_of",""]) if 0 else "")
def T_of(p):
    t=0;c=[p[0]]+[1+a for a in p[1:-1]]+[p[-1]];T=[]
    for z in c[:-1]:t+=z;T.append(t)
    return T,sum(c)
def mom(c,r):return sum(v*k**r for k,v in c.items())
stats=Counter();mins=[];z=[]
for n in range(8,31):
    for l in open(f'/root/wms/spine/d{n}.txt'):
        if not l.startswith('S2'):continue
        ps=[tuple(map(int,a.strip(',').split(','))) for a in l.split()[1:]]
        Ts=[T_of(p)[0] for p in ps];N=n-2
        h=[H3T(t,N) for t in Ts]
        for i in range(1,len(h)):
            d=Counter(h[0]);d.subtract(h[i]);d={k:v for k,v in d.items() if v}
            # order of vanishing at 1
            f=[sum(v*comb(k,r) for k,v in d.items()) for r in range(0,8)]
            o=next((r for r,y in enumerate(f) if y),None);stats[o]+=1
            if o==4:mins.append((n,abs(f[4]),Ts[0],Ts[i]))
            else:z.append((n,o,Ts[0],Ts[i]))
print(stats,z[:5]);print(sorted(mins,key=lambda a:a[1])[:6])
