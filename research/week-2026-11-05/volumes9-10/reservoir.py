"""Explicit separated-site cubic reservoir underlying the realization proof."""
from collections import deque,Counter
from pathlib import Path
import json
P=Path(__file__).resolve().parent

def parent():
 shifts=[17,27,-13,-59,-35,35,-11,13,-53,53,-27,21,57,11,-21,-57,59,-17]*7
 E={tuple(sorted((i,(i+1)%126))) for i in range(126)}
 E|={tuple(sorted((i,(i+d)%126))) for i,d in enumerate(shifts)}
 return 126,sorted(E)

def adj(n,E):
 a=[set() for _ in range(n)]
 for u,v in E:a[u].add(v);a[v].add(u)
 return a

def distances(n,E,roots):
 a=adj(n,E);ds={v:0 for v in roots};todo=deque(roots)
 while todo:
  u=todo.popleft()
  for v in a[u]:
   if v not in ds:ds[v]=ds[u]+1;todo.append(v)
 return ds

def girth(n,E):
 a=adj(n,E);best=n+1
 for root in range(n):
  ds={root:0};par={root:-1};todo=deque([root])
  while todo:
   u=todo.popleft()
   for v in a[u]:
    if v not in ds:ds[v]=ds[u]+1;par[v]=u;todo.append(v)
    elif par[u]!=v:best=min(best,ds[u]+ds[v]+1)
 return best

def edge_connected(n,E,k):
 a=adj(n,E)
 for target in range(1,n):
  flow={}
  for _ in range(k):
   par={0:None};todo=deque([0])
   while todo and target not in par:
    u=todo.popleft()
    for v in a[u]:
     if v not in par and flow.get((u,v),0)<1:par[v]=u;todo.append(v)
   if target not in par:return False
   v=target
   while v:
    u=par[v];flow[u,v]=flow.get((u,v),0)+1;flow[v,u]=flow.get((v,u),0)-1;v=u
 return True

def materialize(seed_n,seed_edges,blocks,max_vertices=100000):
 """Attach each missing seed half-edge to a distinct reservoir block.

 seed graph may be disconnected; its component capacities determine the
 resulting edge-connectivity. The output is an explicit finite edge list.
 """
 if blocks<6 or blocks%2:raise ValueError('even prism order at least six')
 a=adj(seed_n,seed_edges);stubs=[v for v in range(seed_n) for _ in range(3-len(a[v]))]
 D=len(stubs)
 if blocks<D:raise ValueError('one site block required per missing half-edge')
 N=seed_n+D+125*blocks
 if N>max_vertices:raise ValueError('materialization budget')
 _,Q=parent();ports=[1,17,125];site=(5,6);m=blocks//2
 skeleton={tuple(sorted((i,(i+1)%m))) for i in range(m)}
 skeleton|={tuple(sorted((m+i,m+(i+1)%m))) for i in range(m)}
 skeleton|={(i,m+i) for i in range(m)}
 sa=adj(blocks,skeleton)
 vertex=lambda block,v:seed_n+125*block+v-1
 E=list(seed_edges)
 for i in range(blocks):
  for u,v in Q:
   if u==0 or v==0 or i<D and (u,v)==site:continue
   E.append((vertex(i,u),vertex(i,v)))
  if i<D:
   x=seed_n+125*blocks+i
   E.extend(((vertex(i,5),x),(vertex(i,6),x),(stubs[i],x)))
 for i,j in sorted(skeleton):
  u=ports[sorted(sa[i]).index(j)];v=ports[sorted(sa[j]).index(i)]
  E.append((vertex(i,u),vertex(j,v)))
 E=sorted(tuple(sorted(e)) for e in E)
 assert len(set(E))==len(E) and all(len(x)==3 for x in adj(N,E))
 return N,E

def main():
 n,E=parent();assert len(E)==189 and all(len(x)==3 for x in adj(n,E))
 assert girth(n,E)==12 and edge_connected(n,E,3)
 block=[e for e in E if 0 not in e];ports=[1,17,125]
 port_distance=min(distances(n,block,[u])[v] for u in ports for v in ports if u!=v)
 site_distance=min(distances(n,block,ports)[v] for v in (5,6))
 assert port_distance>=10 and site_distance>=4
 # A fully materialized small example exercises every construction layer.
 N,A=materialize(3,[(0,1),(1,2),(0,2)],6)
 assert edge_connected(N,A,3)
 out={'parent_vertices':n,'parent_girth':12,'parent_edge_connectivity_at_least':3,
      'port_distance_at_least':port_distance,'site_to_port_distance_at_least':site_distance,
      'triangle_seed_example_order':N,'example_edge_connectivity_at_least':3,'failures':0}
 (P/'reservoir_checks.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
if __name__=='__main__':main()
