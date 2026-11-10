# Checks of the reflection law: (A) leading epsilon term of b_Q for every pattern; (B) normal form in v=x/(1-x)^2 on hosts from direct integer enumeration.
import sys,json,math,subprocess
from fractions import Fraction as Fr
from analyze import load,pats
from collections import defaultdict
rows=load(sys.argv[1]);Q=pats(sys.argv[1]+'.pats');VM=max(r[0] for r in rows)
col=defaultdict(lambda:defaultdict(dict))
for v,e,d in rows:
    for c,x in d.items(): col[c][v][e]=x
# series v^k(1+4v)^(E-k) in x
def smul(a,b):
    r=[0]*(VM+1)
    for i,x in enumerate(a):
        if x:
            for j,y in enumerate(b):
                if i+j>VM:break
                r[i+j]+=x*y
    return r
vv=[0]*(VM+1)
for n in range(1,VM+1): vv[n]=n   # x/(1-x)^2
one=[1]+[0]*VM
cache={}
def lead(k,E):
    if (k,E) in cache: return cache[(k,E)]
    t=list(one)
    for _ in range(k): t=smul(t,vv)
    w=[4*c for c in vv];w[0]=1
    for _ in range(E-k): t=smul(t,w)
    cache[(k,E)]=t;return t
def eps(P,r): # [eps^r] of sum c q^e at q=e^eps
    return sum(c*Fr(e**r,math.factorial(r)) for e,c in P.items())
bad=n=0
for j,(k,E,cm,ed) in enumerate(Q):
    tar=lead(k,E)
    for V in range(k,VM+1):
        P=col[j+1][V];n+=1
        for r in range(E):
            if eps(P,r)!=0: bad+=1
        if eps(P,E)!=(-2)**E*tar[V]: bad+=1
res={"A_pattern_volume_checks":n,"A_failures":bad}
print(res)
# B: hosts
hosts=open(sys.argv[2]).read().strip().split('\n');bb=0;tot=0;mins={}
for l in hosts:
    w_=l.split();n_=int(w_[0]);o=subprocess.run(['./hist',str(VM)],input=l+'\n',capture_output=True,text=True).stdout.split('\n')[1:]
    Z=[{} for _ in range(VM+1)]
    for x in o:
        if x: a,b,c=map(int,x.split());Z[a][b]=c
    lg=[{} for _ in range(VM+1)]
    for t_ in range(1,VM+1):
        s=defaultdict(Fr)
        for e,c in Z[t_].items(): s[e]+=Fr(c*t_)
        for k in range(1,t_):
            for e1,c1 in lg[k].items():
                for e2,c2 in Z[t_-k].items(): s[e1+e2]-=c1*k*c2
        lg[t_]={e:c/t_ for e,c in s.items() if c}
    # subtract -n log(1-x): x^t coefficient n/t at e=0
    for t_ in range(1,VM+1):
        lg[t_][0]=lg[t_].get(0,Fr(0))-Fr(n_,t_)
    # change variable x->v: x as series in v solved by triangular elimination
    vp=[list(one)]
    for s_ in range(1,VM+1): vp.append(smul(vp[-1],vv))
    Phi={}
    cur=[dict(d) for d in lg]
    for s_ in range(1,VM+1):
        Phi[s_]=dict(cur[s_])
        for t_ in range(s_,VM+1):
            c=vp[s_][t_]
            if c:
                for e,val in Phi[s_].items(): cur[t_][e]=cur[t_].get(e,Fr(0))-c*val
    for s_ in range(1,VM+1):
        tot+=1
        for r in range(s_):
            if eps(Phi[s_],r)!=0: bb+=1;break
res["B_host_layers"]=tot;res["B_failures"]=bb;print(res);json.dump(res,open(sys.argv[3],'w'),indent=1)
