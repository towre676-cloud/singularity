exec(open('ex.py').read().split("res={}")[0])
import time
a=((((), ()), ((),)));
F=[f for f in forests(5)];g=defaultdict(list)
for f in F:g[gen(f)].append(f)
a,b=[v for v in g.values() if len(v)>1][0];print(a,b)
T=enc(a+a,b+b);S=enc(a+b,a+b);print(T);print(S)
for E in (5,6,7,8):
    t=time.time();s=shells([T,S],E);first=next((i for i,(u,v) in enumerate(zip(*s)) if u!=v),None);print(E,first,round(time.time()-t,1),flush=True)
    if first is not None:break
