"""Exact ranks after the cubic cut-capacity restrictions."""
from pathlib import Path
import json
from fractions import Fraction as Q
from itertools import combinations
from vol9_build import lib,rows
from vol8_law import rref
P=Path(__file__).resolve().parent

def capacity(k,mask):
    es=lib.edges_of(mask,k)
    return min(3*S.bit_count()-2*sum((S>>u&1) and (S>>v&1) for u,v in es)
               for S in range(1,1<<k))

def main():
    data=json.loads((P/'vol9_law.json').read_text())
    coeff={int(r):{(x['k'],x['mask']):{int(e):Q(c) for e,c in x['polynomial'].items()}
                       for x in rows0} for r,rows0 in data['coefficient_rows'].items()}
    out=[]
    for lam in range(4):
        keys=[tuple(h) for h in data['core_keys'] if h[0]==1 or not lam or capacity(*h)>=lam]
        _,lo=rows(coeff,8,keys);_,allrows=rows(coeff,9,keys)
        low=len(rref(lo,len(keys))[0]);high=len(rref(allrows,len(keys))[0])
        out.append({'edge_connectivity':lam,'admissible_core_count':len(keys)-1,
                    'lower_rank':low,'total_rank':high,'new_rank':high-low,
                    'allowed_nine_core_histogram':dict(__import__('collections').Counter(m.bit_count() for k,m in keys if k==9)),
                    'keys':keys})
        print(lam,len(keys),low,high,high-low,flush=True)
    (P/'vol9_connectivity.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
