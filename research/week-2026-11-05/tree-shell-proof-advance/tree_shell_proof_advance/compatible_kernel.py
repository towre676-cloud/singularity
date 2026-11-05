"""Kernel of shell-three observation, with all two-edge contraction consistency retained."""
from collections import Counter
from pathlib import Path
import sympy as s,json
from weighted_kernel import shapes
from contractions import canonical,sign_poly
ROOT=Path(__file__).resolve().parent

def boundary(adj,weights):
    out=Counter()
    for u in range(len(weights)):
      for v in adj[u]:
       if v<=u:continue
       reps=[w for w in range(len(weights)) if w!=v];ix={w:i for i,w in enumerate(reps)};ix[v]=ix[u]
       ww=[weights[w] for w in reps];ww[ix[u]]+=weights[v]
       aa=[[] for _ in ww]
       for a in range(len(weights)):
        for b in adj[a]:
         if b>a and ix[a]!=ix[b]:aa[ix[a]].append(ix[b]);aa[ix[b]].append(ix[a])
       out[canonical(aa,ww)]+=1
    return out

def main():
    out={}
    for n in range(4,13):
        objs=shapes(n);polys=[sign_poly(adj,w) for _,w,adj in objs];bd=[boundary(adj,w) for _,w,adj in objs];keys=sorted(set().union(*(x.keys() for x in bd)))
        A=s.Matrix(3*n+1,len(objs),lambda i,j:polys[j][i]);D=s.Matrix(len(keys),len(objs),lambda i,j:bd[j][keys[i]])
        K=A.col_join(D);null=K.nullspace();row={'types':len(objs),'rank_shell_plus_boundary':len(objs)-len(null),'compatible_nullity':len(null)}
        if null:
            v=min(null,key=lambda v:sum(x!=0 for x in v));m=s.ilcm(*[x.q for x in v]);vi=[int(m*x) for x in v]
            assert A*s.Matrix(vi)==s.zeros(A.rows,1) and D*s.Matrix(vi)==s.zeros(D.rows,1)
            row['witness']=[{'coefficient':a,'shape':o[0],'weights':o[1]} for a,o in zip(vi,objs) if a]
            row['positive_mass']=sum(x for x in vi if x>0);row['negative_mass']=-sum(x for x in vi if x<0)
        out[n]=row;print(n,row,flush=True)
    (ROOT/'compatible_three_edge_kernel.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
