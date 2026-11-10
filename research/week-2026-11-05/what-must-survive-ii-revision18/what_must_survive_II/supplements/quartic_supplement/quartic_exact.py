"""Finite fourth-jet formula for any connected leafless subcubic pattern.
Exact Fraction arithmetic. This is a formula evaluator, not a uniform lifting proof.
"""
from fractions import Fraction as F
from itertools import combinations,product,permutations,combinations_with_replacement
from functools import lru_cache
from math import factorial
N=4
ZERO=(F(0),)*5
ONE=(F(1),)+ZERO[1:]
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def scale(a,c):return tuple(c*x for x in a)
def mul(a,b):return tuple(sum(a[i]*b[n-i] for i in range(n+1)) for n in range(5))
def inv(a):
 r=[1/a[0]]
 for n in range(1,5):r.append(-sum(a[i]*r[n-i] for i in range(1,n+1))/a[0])
 return tuple(r)
def log(a):
 assert a[0]==1
 r=[F(0)]
 for n in range(1,5):r.append(a[n]-sum(F(k,n)*r[k]*a[n-k] for k in range(1,n)))
 return tuple(r)
def exp(a):
 assert a[0]==0
 r=[F(1)]
 for n in range(1,5):r.append(sum(F(k,n)*a[k]*r[n-k] for k in range(1,n+1)))
 return tuple(r)
def canon(deg,edges):
 return _canon(tuple(deg),tuple(sorted(tuple(sorted(e)) for e in edges)))
@lru_cache(None)
def _canon(deg,edges):
 n=len(deg);edges=set(edges)
 if n>4:return (tuple(deg),tuple(sorted(edges)))
 return min((tuple(deg[i] for i in p),tuple((i,j) for i in range(n) for j in range(i+1,n) if tuple(sorted((p[i],p[j]))) in edges)) for p in permutations(range(n)))
class FourthJet:
 def __init__(self,q):
  self.q=F(q);q=self.q;H=6;M=6
  def cv(a,b):return [sum(a[i]*b[n-i] for i in range(n+1)) for n in range(M+1)]
  def iv(a):
   r=[1/a[0]]
   for n in range(1,M+1):r.append(-sum(a[i]*r[n-i] for i in range(1,n+1))/a[0])
   return r
  B=[[F(1)]+[F(0)]*M for _ in range(H+1)]
  for t in range(1,M+1):
   sq=[cv(b,b) for b in B];s0=sum(q**(3*h*h)*sq[h][t-h] for h in range(1,t+1))
   b0=-(sq[0][t]+s0);B[0][t]=b0;sq0=sq[0][t]+2*b0
   for h in range(1,H+1):B[h][t]=sq0+sum(q**(3*g*g-2*h*g)*sq[g][t-g] for g in range(1,t+1))
  B3=[cv(cv(b,b),b) for b in B];Z=[F(0)]*(M+1)
  for h in range(M+1):
   for i in range(M+1-h):Z[i+h]+=q**(3*h*h)*B3[h][i]
  IZ=iv(Z);IB=[iv(b) for b in B]
  ps=[[q**(3*h*h)*c for c in cv(B3[h],IZ)] for h in range(H+1)]
  fs={}
  for a in range(6):
   for b in range(6):
    z=[q**(-2*a*b)*c for c in cv(cv(Z,IB[a]),IB[b])];z[0]-=1;fs[a,b]=z
  self.pi=tuple(c/q**3 for c in ps[1][:5]);self.phi=tuple(c/(q**-2-1) for c in fs[1,1][:5]);self.rho={};self.psi={}
  for d in (2,3):
   for h in (0,2,3,4,5):
    val=d-1 if h==0 else h-1
    rat=tuple(fs[h,1][(1 if h==0 else 0)+i] for i in range(5));rat=mul(rat,inv(tuple(fs[1,1][:5])))
    z=mul(tuple(c/q**3 for c in ps[h][:5]),inv(self.pi))
    for _ in range(d):z=mul(z,rat)
    self.rho[d,h]=tuple([F(0)]*val+list(z))[:5]
  for a in (0,2,3,4,5):
   for b in (0,2,3,4,5):
    va=int(a==0);vb=int(b==0)
    den=mul(tuple(fs[a,1][va:va+5]),tuple(fs[1,b][vb:vb+5]))
    num=mul(tuple(fs[a,b][va+vb:va+vb+5]),tuple(fs[1,1][:5]))
    self.psi[a,b]=mul(num,inv(den))
  self.local_cache={};self.theta_cache={}
 def local(self,deg,edges):
  key=canon(deg,edges)
  if key in self.local_cache:return self.local_cache[key]
  deg,edges=key;n=len(deg);D={0:ONE}
  for mask in range(1,1<<n):
   vs=[i for i in range(n) if mask>>i&1];z=ZERO
   for hs in product((0,2,3,4,5),repeat=len(vs)):
    cost=sum((deg[v]-1 if h==0 else h-1) for v,h in zip(vs,hs))
    if cost>4:continue
    h=dict(zip(vs,hs));t=ONE
    for v in vs:t=mul(t,self.rho[deg[v],h[v]])
    for a,b in edges:
     if a in h and b in h:t=mul(t,self.psi[h[a],h[b]])
    z=add(z,t)
   D[mask]=z
  K=ZERO
  for mask in range(1<<n):
   Z=ZERO;s=mask
   while True:
    Z=add(Z,D[s])
    if s==0:break
    s=(s-1)&mask
   K=add(K,scale(log(Z),(-1)**(n-mask.bit_count())))
  self.local_cache[key]=K;return K
 def theta(self,n,edges):
  edges=tuple(sorted(tuple(sorted(e)) for e in edges));key=n,edges
  if key in self.theta_cache:return self.theta_cache[key]
  deg=[0]*n;adj=[set() for _ in range(n)]
  for a,b in edges:deg[a]+=1;deg[b]+=1;adj[a].add(b);adj[b].add(a)
  assert all(d in (2,3) for d in deg)
  ell=add(scale(log(self.pi),n),scale(log(self.phi),len(edges)))
  for sz in range(1,min(4,n)+1):
   for vs in combinations(range(n),sz):
    seen={vs[0]};changed=True;S=set(vs)
    while changed:
     old=len(seen);seen|={w for v in tuple(seen) for w in adj[v] if w in S};changed=len(seen)>old
    if len(seen)!=sz:continue
    idx={v:i for i,v in enumerate(vs)};es=[(idx[a],idx[b]) for a,b in edges if a in idx and b in idx]
    ell=add(ell,self.local(tuple(deg[v] for v in vs),es))
  val=scale(exp(ell),self.q**(3*n)*(self.q**-2-1)**len(edges));self.theta_cache[key]=val;return val
 def bjet(self,n,edges):
  edges=tuple(tuple(e) for e in edges);m=len(edges);full=(1<<m)-1;pl=[]
  for mask in range(1,1<<m):
   if mask.bit_count()<3:continue
   deg=[0]*n;vs=set();es=[]
   for j,(a,b) in enumerate(edges):
    if mask>>j&1:deg[a]+=1;deg[b]+=1;vs|={a,b};es.append((a,b))
   if any(deg[v]<2 for v in vs):continue
   seen={min(vs)}
   while True:
    nxt=seen|{b for a,b in es if a in seen}|{a for a,b in es if b in seen}
    if nxt==seen:break
    seen=nxt
   if seen!=vs:continue
   idx={v:i for i,v in enumerate(sorted(vs))};ed=tuple((idx[a],idx[b]) for a,b in es)
   pl.append((mask,frozenset(vs),ed))
  out=list(self.theta(n,edges))
  # Connected clusters have total vertex multiplicity >= n+2(p-1), so p<=3 here.
  for p in (2,3):
   for ids in combinations_with_replacement(range(len(pl)),p):
    cov=0;total=0
    for i in ids:cov|=pl[i][0];total+=len(pl[i][1])
    if cov!=full or total>n+4:continue
    conflict=[(a,b) for a in range(p) for b in range(a+1,p) if pl[ids[a]][1]&pl[ids[b]][1]]
    if p==2:phi=-1 if conflict else 0
    else:phi=1 if len(conflict)==2 else 2 if len(conflict)==3 else 0
    if not phi:continue
    den=1
    for i in set(ids):den*=factorial(ids.count(i))
    t=ONE
    for i in ids:t=mul(t,self.theta(len(pl[i][1]),pl[i][2]))
    excess=total-n
    for j in range(excess,5):out[j]+=F(phi,den)*t[j-excess]
  return tuple(out)
