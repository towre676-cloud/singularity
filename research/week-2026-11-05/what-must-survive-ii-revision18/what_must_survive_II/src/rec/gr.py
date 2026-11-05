from collections import Counter
import json
def T_of(p):
    t=0;c=[p[0]]+[1+a for a in p[1:-1]]+[p[-1]];T=[]
    for z in c[:-1]:t+=z;T.append(t)
    return T
def spins(T,N):
    return {min(t,N-t):(1 if t<N-t else -1) for t in T if 2*t!=N and (N-t) not in T}
ok=0;tot=0;onesided=0;minRfrac=None;patterns=Counter()
for n in range(8,31):
    N=n-2
    for l in open(f'/root/wms/spine/d{n}.txt'):
        if not l.startswith('S2'):continue
        ps=[tuple(map(int,x.strip(',').split(','))) for x in l.split()[1:]]
        for p in ps:
            s=spins(T_of(p),N)
            if len(set(s.values()))==1:onesided+=1
        s1,s2=spins(T_of(ps[0]),N),spins(T_of(ps[1]),N)
        Z=[k for k in s1 if s1[k]!=s2[k]];Y=[k for k in s1 if s1[k]==s2[k]]
        S=sum(s1[y]*s1[z]*min(y,z)*(N-2*max(y,z)) for y in Y for z in Z);tot+=1;ok+=S==0
        # each flip block must see both signs
print(dict(pairs=tot,second_moment_zero=ok,one_sided_members=onesided))
json.dump(dict(pairs=tot,second_moment_zero=ok,one_sided_members=onesided),open('gr.json','w'))
# all-tree version: Q fixed by (A,B)
import networkx as nx,itertools,warnings
warnings.filterwarnings("ignore")
exec(open('r.py').read().split("if __name__")[0])
from collections import defaultdict
bad=0;cmp=0
for n in range(10,17):
    g=defaultdict(list)
    for T in nx.nonisomorphic_trees(n):
        n_,c,o,par,s,anc=data(T);A=Counter();B=Counter();Q=0;ed=o[1:]
        for v in ed:A[min(s[v],n-s[v])]+=1
        for e,f in itertools.combinations(ed,2):
            if e in anc[f]:B[s[e]-s[f]]+=1;Q+=(n-2*s[e])*(s[f]-1)
            elif f in anc[e]:B[s[f]-s[e]]+=1;Q+=(n-2*s[f])*(s[e]-1)
            else:B[n-s[e]-s[f]]+=1
        g[(key(A),key(B))].append(Q)
    for v in g.values():
        cmp+=len(v)-1;bad+=len(set(v))>1
print('Q invariant over classes',cmp,'bad',bad)
