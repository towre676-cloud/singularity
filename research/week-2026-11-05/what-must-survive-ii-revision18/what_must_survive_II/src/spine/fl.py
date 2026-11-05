import sys,itertools,sympy as sp,json
from collections import Counter
exec(open('m.py').read().split("# family top")[1].split("rows=[]")[0].replace("difference via H3",""))
def T_of(p):
    t=0;c=[p[0]]+[1+x for x in p[1:-1]]+[p[-1]];T=[];
    for z in c[:-1]:t+=z;T.append(t)
    return frozenset(T),sum(c)
def p_of(T,N):
    s=[0]+sorted(T)+[N];c=[s[i+1]-s[i] for i in range(len(s)-1)]
    return tuple([c[0]]+[z-1 for z in c[1:-1]]+[c[-1]])
def canon(T,N):
    return min(tuple(sorted(T)),tuple(sorted(N-t for t in T)))
def flips(T,N):
    for v in range(2,N):
        if N%v: continue
        u=N//v
        if u<2: continue
        I={t%v for t in T if t%v}
        if not all((k*v+i) in T for k in range(u) for i in I): continue
        if any(t%v and t%v not in I for t in T): continue
        O={t//v for t in T if t%v==0}
        Op={u-k for k in O}
        yield v,u,I,O,frozenset({k*v+i for k in range(u) for i in I}|{k*v for k in Op})
def orbit(T,N):
    S={canon(T,N)};st=[frozenset(canon(T,N))]
    while st:
        X=st.pop()
        for *_,Y in flips(X,N):
            c=canon(Y,N)
            if c not in S:S.add(c);st.append(frozenset(c))
    return S
tot={}
for n in range(8,int(sys.argv[1])+1):
    N=n-2;cl=[[tuple(map(int,x.strip(',').split(','))) for x in l.split()[1:]] for l in open(f'd{n}.txt') if l.startswith('S2')]
    bad=0;seen=set()
    for c in cl:
        Ts=[T_of(p)[0] for p in c];can={canon(t,N) for t in Ts}
        if orbit(Ts[0],N)!=can:bad+=1;print('NOT ORBIT',n,c)
        seen|=can
    tot[n]=(len(cl),bad);print(n,N,'classes',len(cl),'nonorbit',bad,flush=True)
