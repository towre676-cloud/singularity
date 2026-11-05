# Exact rational witness check, plus an independent re-evaluation of the series in pure Python.
# Usage: witness_verify.py rows promo.json V out
import sys,json,itertools,math
from fractions import Fraction as Fr
from analyze import load,pats,rr,P
from collections import defaultdict
fn,pj,V,out=sys.argv[1],sys.argv[2],int(sys.argv[3]),sys.argv[4]
rows=load(fn);Q=pats(fn+'.pats');w=json.load(open(pj));idx={tuple(map(tuple,q[3])):i for i,q in enumerate(Q)}
sup=[(idx[tuple(map(tuple,x['pattern']))],rr(x['coef'])) for x in w['witness']]
# clear scaling
L=1
for _,c in sup: L=L*c.denominator//math.gcd(L,c.denominator)
sup=[(i,c*L) for i,c in sup]
col={i+1:c for i,c in sup};bad=0;Rv={}
for v,e,d in rows:
    if v>V: continue
    s=sum(c*d.get(k,0) for k,c in col.items())
    if v<V and s!=0: bad+=1
    if v==V and s!=0: Rv[e]=s
res={"support":len(sup),"coeffs":{str(i):str(c) for i,c in sup},"earlier_row_violations":bad,"poly_top_e":max(Rv),"poly_low_e":min(Rv),"pole":(max(Rv)-3*V)//2,"top_coefficient":str(Rv[max(Rv)])}
agg=defaultdict(Fr);low=min(Q[i][0] for i,_ in sup)
for i,c in sup:
    q=Q[i]
    if q[0]==low:
        deg=[0]*q[0]
        for a,b in q[3]: deg[a]+=1;deg[b]+=1
        agg[q[1]]+=c*sum(deg[a]==2 and deg[b]==2 for a,b in q[3])
res["lowest_size"]=low;res["A_by_E"]={str(k):str(v) for k,v in sorted(agg.items())}
print(res)
# independent evaluation with Fractions at a rational q
VM=V
def smul(a,b):
    r=[Fr(0)]*(VM+1)
    for i,x in enumerate(a):
        if x:
            for j,y in enumerate(b):
                if i+j>VM:break
                if y: r[i+j]+=x*y
    return r
def sinv(a):
    r=[Fr(0)]*(VM+1);r[0]=1/a[0]
    for n in range(1,VM+1): r[n]=-sum(a[i]*r[n-i] for i in range(1,n+1))/a[0]
    return r
def setup(q):
    H=VM;B=[[Fr(1)]+[Fr(0)]*VM for _ in range(H+1)]
    for t in range(1,VM+1):
        sq=[smul(b,b) for b in B]
        s0=sum(q**(3*h*h)*sq[h][t-h] for h in range(1,min(t,H)+1))
        b0=-(sq[0][t]+s0);B[0][t]=b0;sq0=sq[0][t]+2*b0
        for h in range(1,H+1):
            B[h][t]=sq0+sum(q**(3*g*g-2*h*g)*sq[g][t-g] for g in range(1,min(t,H)+1))
    B3=[smul(smul(b,b),b) for b in B]
    Z=[Fr(0)]*(VM+1)
    for h in range(H+1):
        for i in range(VM+1-h): Z[i+h]+=q**(3*h*h)*B3[h][i]
    IZ=sinv(Z);IB=[sinv(b) for b in B]
    p=[]
    for h in range(H+1):
        t=smul(B3[h],IZ);a=[Fr(0)]*(VM+1)
        for i in range(VM+1-h): a[i+h]=q**(3*h*h)*t[i]
        p.append(a)
    F={}
    for a in range(0,7):
        for b in range(a,7):
            t=smul(smul(Z,IB[a]),IB[b]);t=[c*q**(-2*a*b) for c in t];t[0]-=1;F[(a,b)]=t;F[(b,a)]=t
    return p,F
def theta(n,ed,p,F):
    adj=[[] for _ in range(n)]
    for a,b in ed: adj[a].append(b);adj[b].append(a)
    order=[0];seen={0}
    for u in order:
        for w_ in adj[u]:
            if w_ not in seen: seen.add(w_);order.append(w_)
    pos={v:i for i,v in enumerate(order)};res=[Fr(0)]*(VM+1);h={}
    def ordp(s): return s
    def rec(i,cur,cost):
        if i==n:
            for t in range(VM+1): res[t]+=cur[t]
            return
        v=order[i]
        for s in range(0,7):
            c=cost+s;back=[w_ for w_ in adj[v] if pos[w_]<i]
            for w_ in back:
                if s==0 and h[w_]==0: c+=2
                elif s==0 or h[w_]==0: c+=1
            h[v]=s
            lb=c+(n-i-1)+sum(1 for j in range(i+1) if h[order[j]]==0 for w_ in adj[order[j]] if pos[w_]>i)
            if lb<=VM:
                nx=smul(cur,p[s])
                for w_ in back: nx=smul(nx,F[(s,h[w_])])
                rec(i+1,nx,c)
            del h[v]
    rec(0,[Fr(1)]+[Fr(0)]*VM,0);return res
def polys(n,ed):
    m=len(ed);o=[]
    for mask in range(1,1<<m):
        if bin(mask).count('1')<3: continue
        d=[0]*n;vm=0
        for i in range(m):
            if mask>>i&1:a,b=ed[i];d[a]+=1;d[b]+=1;vm|=1<<a|1<<b
        if any((vm>>v&1) and d[v]<2 for v in range(n)):continue
        seen=vm&-vm;ch=True
        while ch:
            ch=False
            for i in range(m):
                if mask>>i&1:
                    a,b=ed[i];x,y=seen>>a&1,seen>>b&1
                    if x!=y: seen|=1<<a|1<<b;ch=True
        if seen==vm:o.append((mask,vm))
    return o
def urs(g):
    m=len(g);ed=[(i,j) for i in range(m) for j in range(i+1,m) if g[i][j]];s=0
    for k in range(1<<len(ed)):
        f=list(range(m))
        def fd(x):
            while f[x]!=x:x=f[x]
            return x
        c=m
        for t,(i,j) in enumerate(ed):
            if k>>t&1:
                a,b=fd(i),fd(j)
                if a!=b:f[a]=b;c-=1
        if c==1:s+=(-1)**bin(k).count('1')
    return s
def b_series(i,p,F):
    n,E,cm,ed=Q[i];ed=[tuple(x) for x in ed];r=theta(n,ed,p,F)
    if n+2>VM: return r
    pl=polys(n,ed);full=(1<<len(ed))-1;memo={};st=[]
    def th(mask):
        if mask not in memo:
            es=[ed[t] for t in range(len(ed)) if mask>>t&1];vs=sorted({v for e in es for v in e});mp={v:u for u,v in enumerate(vs)}
            memo[mask]=theta(len(vs),[(mp[a],mp[b]) for a,b in es],p,F)
        return memo[mask]
    def dfs(s,bud,cov):
        if len(st)>=2 and cov==full:
            m=len(st);g=[[bool(i_!=j_ and pl[st[i_]][1]&pl[st[j_]][1]) for j_ in range(m)] for i_ in range(m)];ph=urs(g)
            if ph:
                den=1
                for u in set(st): den*=math.factorial(st.count(u))
                t=[Fr(1)]+[Fr(0)]*VM
                for u in st:t=smul(t,th(pl[u][0]))
                for z in range(VM+1): r[z]+=Fr(ph,den)*t[z]
        for u in range(s,len(pl)):
            sz=bin(pl[u][1]).count('1')
            if sz<=bud: st.append(u);dfs(u,bud-sz,cov|pl[u][0]);st.pop()
    dfs(0,VM,0);return r
ok=True
for q in (Fr(3,2),):
    p,F=setup(q);Y=[Fr(0)]*(VM+1)
    for i,c in sup:
        b=b_series(i,p,F)
        for t in range(VM+1):Y[t]+=c*b[t]
    low_ok=all(Y[t]==0 for t in range(VM));exp=sum(c*q**e for e,c in Rv.items())
    res[f"independent_q={q}"]={"lower_orders_vanish":low_ok,"matches_row_polynomial":Y[VM]==exp}
    ok&=low_ok and Y[VM]==exp
print(res[f"independent_q={Fr(3,2)}"]);json.dump(res,open(out,'w'),indent=1);assert bad==0 and ok
