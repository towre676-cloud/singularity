# (1) rational window certificates; (2) general-graph reflection and A1,A2 by exact enumeration.
import sys,json,itertools,math,random
from fractions import Fraction as Fr
from collections import defaultdict
from analyze import load
from flint import fmpq_mat,fmpq
rows=load(sys.argv[1]);res={}
def rank(R):
    cols=sorted({c for r in R for c in r[2]});ci={c:i for i,c in enumerate(cols)}
    sig=defaultdict(dict)
    for i,(v,e,d) in enumerate(R):
        for c,x in d.items(): sig[c][i]=x
    U=list({tuple(sorted(s.items())) for s in sig.values()})
    M=[fmpq(0)]*(len(R)*len(U))
    for j,u in enumerate(U):
        for i,x in u: M[i*len(U)+j]=fmpq(x.numerator,x.denominator)
    return int(fmpq_mat(len(R),len(U),M).rank())
for V,top in ((11,53),(13,75)):
    B=[r for r in rows if r[0]<V];R=[r for r in rows if r[0]==V];hi=[r for r in R if r[1]>top]
    a,b,c=rank(B),rank(B+R),rank(B+hi)
    # columns of n excluded automatically? n column kept: high rows contain n only through earlier span test
    res[f"V{V}"]={"earlier":a,"through":b,"earlier_plus_high":c,"ambient":(top-(V%2))//2+1-V,"high_rows":len(hi)};print(res[f"V{V}"],flush=True)
    assert a==c and b-a==res[f"V{V}"]["ambient"]
# general graphs
def logseries(n,E,VM):
    Z=[defaultdict(int) for _ in range(VM+1)];h=[0]*n
    adj=[[] for _ in range(n)]
    for a,b in E:
        a,b=max(a,b),min(a,b);adj[a].append(b)
    def rec(u,vol,en):
        if u==n: Z[vol][en]+=1;return
        for s in range(VM-vol+1):
            h[u]=s;rec(u+1,vol+s,en+sum((s-h[w])**2 for w in adj[u]))
        h[u]=0
    rec(0,0,0)
    lg=[{} for _ in range(VM+1)]
    for t in range(1,VM+1):
        s=defaultdict(Fr)
        for e,c in Z[t].items(): s[e]+=Fr(c*t)
        for k in range(1,t):
            for e1,c1 in lg[k].items():
                for e2,c2 in Z[t-k].items(): s[e1+e2]-=c1*k*c2
        lg[t]={e:c/t for e,c in s.items() if c}
    return lg
VM=9;rnd=random.Random(7);ok=0;tot=0;fail=0
vv=[0]+list(range(1,VM+1))
def smul(a,b):
    r=[0]*(VM+1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            if i+j<=VM: r[i+j]+=x*y
    return r
vp=[[1]+[0]*VM]
for s in range(1,VM+1): vp.append(smul(vp[-1],vv))
for tr in range(14):
    n=rnd.randint(3,6);P=list(itertools.combinations(range(n),2));E=[e for e in P if rnd.random()<.55] or [P[0]]
    lg=logseries(n,E,VM);m=len(E);deg=[0]*n
    for a,b in E: deg[a]+=1;deg[b]+=1
    S2=sum(d*d for d in deg)
    for t in range(1,VM+1): lg[t][0]=lg[t].get(0,Fr(0))-Fr(n,t)
    cur=[dict(d) for d in lg];Phi={}
    for s in range(1,VM+1):
        Phi[s]=dict(cur[s])
        for t in range(s,VM+1):
            c=vp[s][t]
            if c:
                for e,val in Phi[s].items(): cur[t][e]=cur[t].get(e,Fr(0))-c*val
    eps=lambda P_,r:sum(c*Fr(e**r,math.factorial(r)) for e,c in P_.items())
    for s in range(1,VM+1):
        for r in range(s):
            tot+=1
            if eps(Phi[s],r)!=0: fail+=1
    a1=[eps(Phi[s],1) for s in range(1,VM+1)];a2=[eps(Phi[s],2) for s in range(1,VM+1)]
    if a1[0]!=2*m or any(a1[1:]): fail+=1
    if a2[0]!=Fr(S2,2) or a2[1]!=4*S2+2*m or any(a2[2:]): fail+=1;print("A2",a2[:3],S2,m)
res["general_graphs"]={"graphs":14,"vanishing_checks":tot,"failures":fail};print(res["general_graphs"])
json.dump(res,open(sys.argv[2],'w'),indent=1)
