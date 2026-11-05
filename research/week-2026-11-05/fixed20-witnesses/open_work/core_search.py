import sys,json,time
from collections import Counter
from functools import lru_cache
from fractions import Fraction as F
sys.path.insert(0,'final_bundle/replay')
from vol8_lib import canonical,mask_from_edges,spanning_subgraphs,degrees_of
s=json.load(open('final_bundle/replay/vol8_law.json'))
c={int(r):{(x['k'],x['mask']):{int(e):F(a) for e,a in x['polynomial'].items()} for x in d} for r,d in s['reduced_coefficients'].items()}
@lru_cache(None)
def contribution(k,m):
 out={r:Counter() for r in range(1,9)}
 for sm,mult in spanning_subgraphs(m,k).items():
  if min(degrees_of(sm,k))<2:continue
  for r in range(1,9):
   for e,a in c[r].get((k,sm),{}).items():out[r][e]+=mult*a
 return out

def features(n,E):
 adj=[0]*n
 for a,b in E:adj[a]|=1<<b;adj[b]|=1<<a
 seen=set()
 def cycles(start,last,used,depth):
  nbr=adj[last]
  while nbr:
   bit=nbr&-nbr;nbr-=bit;v=bit.bit_length()-1
   if v==start and depth>=3:seen.add(used)
   elif v>start and not(used&bit) and depth<8:cycles(start,v,used|bit,depth+1)
 for v in range(n):cycles(v,v,1<<v,1)
 sets=list(seen)
 for sub in sets:
  if sub.bit_count()==8:continue
  bd=0;rem=sub
  while rem:
   bit=rem&-rem;rem-=bit;bd|=adj[bit.bit_length()-1]
  bd&=~sub
  while bd:
   bit=bd&-bd;bd-=bit;ss=sub|bit
   if ss not in seen:seen.add(ss);sets.append(ss)
 counts=Counter()
 for sub in sets:
  vs=[v for v in range(n) if sub>>v&1]
  if any((adj[v]&sub).bit_count()<2 for v in vs):continue
  k=len(vs);m=mask_from_edges(k,[(i,j) for i in range(k) for j in range(i+1,k) if adj[vs[i]]>>vs[j]&1])
  counts[k,canonical(m,k)]+=1
 out={r:Counter() for r in range(1,9)}
 for h,mult in counts.items():
  for r,p in contribution(*h).items():
   for e,a in p.items():out[r][e]+=mult*a
 return {r:{e:a for e,a in p.items() if a} for r,p in out.items()}

def triangle(n,E,v):
 nbr=sorted(b if a==v else a for a,b in E if v in(a,b));assert len(nbr)==3
 result=[tuple(e) for e in E if v not in e]
 for a,b in ((v,n),(v,n+1),(n,n+1)):result.append((a,b))
 for a,b in zip((v,n,n+1),nbr):result.append(tuple(sorted((a,b))))
 return n+2,sorted(result)

def low(f):return tuple(tuple(sorted(f[r].items())) for r in range(1,8))
if __name__=='__main__':
 w=json.load(open('final_bundle/replay/fresh_small_witnesses.json'))['witnesses'][1]
 t=time.monotonic();f=features(w['n'],w['A_edges']);print('seconds',time.monotonic()-t,'low entries',len(str(low(f))))
 t=time.monotonic();features(*triangle(w['n'],w['A_edges'],0));print('expanded seconds',time.monotonic()-t)
