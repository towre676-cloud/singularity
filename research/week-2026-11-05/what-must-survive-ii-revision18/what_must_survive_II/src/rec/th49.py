from collections import Counter
import json
def T_of(p):
    t=0;c=[p[0]]+[1+a for a in p[1:-1]]+[p[-1]];T=[]
    for z in c[:-1]:t+=z;T.append(t)
    return T
def spins(T,N):
    return {min(t,N-t):(1 if t<N-t else -1) for t in T if 2*t!=N and (N-t) not in T}
H=Counter();tot=0;viol=0;mins={}
for n in range(8,31):
    N=n-2
    for l in open(f'/root/wms/spine/d{n}.txt'):
        if not l.startswith('S2'):continue
        ps=[tuple(map(int,x.strip(',').split(','))) for x in l.split()[1:]]
        for i in range(1,len(ps)):
            s1,s2=spins(T_of(ps[0]),N),spins(T_of(ps[i]),N)
            Z=[k for k in s1 if s1[k]!=s2[k]];Y=[k for k in s1 if s1[k]==s2[k]]
            Q=max(Y+Z);M=max(Z) if Q in Y else max(Y);v=2*Q+M-N;tot+=1;viol+=v<0;H[v]+=1
            mins[n]=min(mins.get(n,99),v)
print(dict(pairs=tot,violations=viol),'min by n',mins,'tight',H[0],'smallest values',sorted(H.items())[:6])
json.dump(dict(pairs=tot,violations=viol,min_by_n=mins),open('th49.json','w'))
