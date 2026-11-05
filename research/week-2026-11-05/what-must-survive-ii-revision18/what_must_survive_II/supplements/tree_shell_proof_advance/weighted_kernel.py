"""Exact rank and integer obstructions for the weighted three-edge shell transform."""
from collections import Counter,defaultdict
from itertools import product
from pathlib import Path
import sympy as s,json
from contractions import sign_poly,canonical
ROOT=Path(__file__).resolve().parent

def shapes(n):
    seen=set();out=[]
    for a in range(1,n-2):
      for b in range(1,n-a-1):
       for c in range(1,n-a-b):
        w=(a,b,c,n-a-b-c)
        for name,adj in [('path',[[1],[0,2],[1,3],[2]]),('star',[[1,2,3],[0],[0],[0]])]:
            key=canonical(adj,w)
            if key not in seen:
                seen.add(key);out.append((name,w,adj))
    return out

def main():
    result={};examples=[]
    for n in range(4,13):
        objs=shapes(n);polys=[sign_poly(adj,w) for _,w,adj in objs]
        A=s.Matrix(3*n+1,len(objs),lambda i,j:polys[j][i]);rank=A.rank()
        by=defaultdict(list)
        for i,p in enumerate(polys):by[tuple(sorted(p.items()))].append(i)
        collisions=[g for g in by.values() if len(g)>1]
        row={'weighted_types':len(objs),'rank':rank,'nullity':len(objs)-rank,'single_polynomial_collision_classes':len(collisions)}
        if collisions:
            g=collisions[0];row['example']=[{'shape':objs[i][0],'weights':objs[i][1]} for i in g]
            row['example_polynomial']=dict(polys[g[0]])
        if n==6:
            vec=A.nullspace()[0];m=s.ilcm(*[v.q for v in vec]);v=[int(m*x) for x in vec]
            row['integer_kernel']=[{'coefficient':a,'shape':obj[0],'weights':obj[1]} for a,obj in zip(v,objs) if a]
        result[n]=row;print(n,row,flush=True)
    (ROOT/'weighted_three_edge_kernel.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
