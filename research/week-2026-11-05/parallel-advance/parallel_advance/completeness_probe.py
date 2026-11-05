import networkx as nx,json,itertools
from collections import defaultdict,Counter
from pathlib import Path
R=Path(__file__).parent
# All simple graphs through seven vertices; compare binary-height partition signatures.
groups=defaultdict(list)
for G in nx.graph_atlas_g():
 n=len(G)
 if n<2 or not nx.is_connected(G):continue
 ed=list(G.edges());c=Counter()
 for mask in range(1<<n):
  e=sum(((mask>>a)&1)!=((mask>>b)&1) for a,b in ed);c[(mask.bit_count(),e)]+=1
 key=n,tuple(sorted(c.items()));groups[key].append(G)
candidates=[gs for gs in groups.values() if len(gs)>1]
def hist(G,V):
 n=len(G);ed=list(G.edges());out=Counter();h=[0]*n
 def rec(i,left):
  if i==n-1:
   h[i]=left;e=sum((h[a]-h[b])**2 for a,b in ed);out[e]+=1;return
  for a in range(left+1):h[i]=a;rec(i+1,left-a)
 rec(0,V);return dict(out)
res={'connected_atlas_binary_collision_classes':len(candidates),'examples':[]}
for gs in candidates:
 G,H=gs[:2];first=None
 for V in range(1,10):
  a,b=hist(G,V),hist(H,V)
  if a!=b:
   diff={str(e):a.get(e,0)-b.get(e,0) for e in sorted(set(a)|set(b)) if a.get(e,0)!=b.get(e,0)}
   first={'volume':V,'difference_by_energy':diff};break
 res['examples'].append({'n':len(G),'edges_G':list(G.edges()),'edges_H':list(H.edges()),'isomorphic':nx.is_isomorphic(G,H),'first_height_difference':first})
(R/'binary_collision_probe.json').write_text(json.dumps(res,indent=2));print({'binary_collision_classes':len(candidates),'tested_pairs':len(res['examples']),'not_separated_through_9':sum(x['first_height_difference'] is None for x in res['examples']),'first_separation_volumes':dict(Counter(x['first_height_difference']['volume'] for x in res['examples'] if x['first_height_difference']))})
