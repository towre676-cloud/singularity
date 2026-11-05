"""Independent adjacency-preserving backtracking versus nauty group orders."""
from pathlib import Path
import json
import vol10_build
from vol9_build import lib
aut=vol10_build.auto
P=Path(__file__).resolve().parent

def backtrack(k,edges):
 a=[set() for _ in range(k)]
 for u,v in edges:a[u].add(v);a[v].add(u)
 ds=list(map(len,a));order=sorted(range(k),key=lambda v:(-ds[v],v));mapping={}
 def rec(i,used):
  if i==k:return 1
  u=order[i];count=0
  for v in range(k):
   if used>>v&1 or ds[v]!=ds[u]:continue
   if any((old in a[u])!=(new in a[v]) for old,new in mapping.items()):continue
   mapping[u]=v;count+=rec(i+1,used|1<<v);del mapping[u]
  return count
 return rec(0,0)

def main():
 masks=json.loads((P/'catalogue10.json').read_text())['masks']
 hist={}
 for m in masks:
  aa=backtrack(10,lib.edges_of(m,10));assert aa==aut(10,m),(m,aa,aut(10,m))
  hist[aa]=hist.get(aa,0)+1
 out={'ten_vertex_patterns_checked':len(masks),'automorphism_order_histogram':hist,'failures':0}
 (P/'automorphism10_checks.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
if __name__=='__main__':main()
