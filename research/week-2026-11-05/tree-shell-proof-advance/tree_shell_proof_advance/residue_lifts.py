"""Exact root-of-unity collapse and nonnegative residue-lift decomposition."""
from collections import Counter
from pathlib import Path
import json,math
import networkx as nx
from contractions import full_shells,unit_shell,diff
ROOT=Path(__file__).resolve().parent

def split_sizes(T):
    n=len(T);out=[]
    for u,v in T.edges():
        # Size on u's side, without mutating input.
        seen={u};todo=[u]
        for a in todo:
            for b in T[a]:
                if (a==u and b==v) or (a==v and b==u):continue
                if b not in seen:seen.add(b);todo.append(b)
        out.append(min(len(seen),n-len(seen)))
    return sorted(out)

def residue_product(n,splits,E):
    out=[Counter() for _ in range(E+1)];out[0][0]=1
    for a in splits:
        nxt=[Counter() for _ in range(E+1)]
        for e in range(E+1):
            for z in range(-math.isqrt(E-e),math.isqrt(E-e)+1):
                for r,c in out[e].items():nxt[e+z*z][(r+a*z)%n]+=c
        out=nxt
    return out

def decompose(poly,n):
    R=Counter();H=Counter()
    for v,c in poly.items():
        r=v%n;R[r]+=c
        for j in range(v//n):H[r+j*n]+=c
    return R,H

def main():
    count=0
    for n in range(2,11):
      for T in nx.nonisomorphic_trees(n):
        S=full_shells(T,4);R=residue_product(n,split_sizes(T),4)
        for e in range(5):
            rr,h=decompose(S[e],n);assert rr==R[e]
            rebuilt=Counter(rr)
            for v,c in h.items():rebuilt[v+n]+=c;rebuilt[v]-=c
            assert all(rebuilt[v]==S[e][v] for v in rebuilt.keys()|S[e].keys())
        assert S[2]==unit_shell(T,2)
        assert S[4]==unit_shell(T,4)+Counter({2*v:c for v,c in S[1].items()})
        count+=1
    source=json.loads((ROOT/'n10_input.json').read_text());a,b=map(nx.Graph,source['n10_pair']['edges']);sa,sb=full_shells(a,4),full_shells(b,4)
    ra,ha=decompose(sa[3],10);rb,hb=decompose(sb[3],10)
    assert ra==rb and diff(ha,hb)=={'1':1,'2':-2,'3':1}
    result={'trees_checked':count,'orders':'2 through 10, all nonisomorphic trees','max_energy':4,'exact_integer_arithmetic':True,'n10_pair':{'edges':source['n10_pair']['edges'],'split_sizes_equal':split_sizes(a)==split_sizes(b),'shell3_difference':diff(sa[3],sb[3]),'residue_lift3_difference':diff(ha,hb)}}
    (ROOT/'residue_lift_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
if __name__=='__main__':main()
