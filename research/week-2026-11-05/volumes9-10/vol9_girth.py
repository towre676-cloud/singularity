"""Exact coefficient ranks on combined girth/cut-capacity restrictions."""
from pathlib import Path
from collections import deque
from fractions import Fraction as Q
import json
from vol9_build import lib,rows
from vol9_connectivity import capacity
from vol8_law import rref
P=Path(__file__).resolve().parent

def girth(k,m):
 adj=[[] for _ in range(k)]
 for u,v in lib.edges_of(m,k):adj[u].append(v);adj[v].append(u)
 out=k+1
 for root in range(k):
  dd={root:0};parent={root:-1};todo=deque([root])
  while todo:
   u=todo.popleft()
   for v in adj[u]:
    if v not in dd:dd[v]=dd[u]+1;parent[v]=u;todo.append(v)
    elif parent[u]!=v:out=min(out,dd[u]+dd[v]+1)
 return out

def main():
 d=json.loads((P/'vol9_law.json').read_text())
 c={int(r):{(x['k'],x['mask']):{int(e):Q(a) for e,a in x['polynomial'].items()} for x in rr}
    for r,rr in d['coefficient_rows'].items()}
 keys=[tuple(h) for h in d['core_keys']];gs={h:girth(*h) for h in keys if h[0]>1};caps={h:capacity(*h) for h in gs}
 out=[]
 for g in range(4,11):
  for lam in range(4):
   kk=[h for h in keys if h==(1,0) or gs[h]>=g and caps[h]>=lam]
   _,low=rows(c,8,kk);_,high=rows(c,9,kk)
   a=len(rref(low,len(kk))[0]);b=len(rref(high,len(kk))[0])
   out.append({'girth_at_least':g,'edge_connectivity':lam,'core_count':len(kk)-1,'lower_rank':a,'total_rank':b,'new_rank':b-a,
                'new_core_keys':[list(h) for h in kk if h[0]==9]})
  print('girth',g,[(r['edge_connectivity'],r['new_rank']) for r in out if r['girth_at_least']==g],flush=True)
 (P/'vol9_girth.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
