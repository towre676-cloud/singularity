#!/usr/bin/env python3
"""Certify direct delayed-motif extraction from eighth energy sectors28,30."""
import json
from fractions import Fraction as F
from pathlib import Path
from vol8_law import rref
HERE=Path(__file__).resolve().parent


def main():
    saved=json.loads((HERE/'vol8_law.json').read_text())
    c={int(r):{(x['k'],x['mask']):{int(e):F(a)for e,a in x['polynomial'].items()}for x in data}for r,data in saved['reduced_coefficients'].items()}
    keys=sorted({h for r in c for h in c[r]})
    rows=[]
    for r in range(1,8):
        for e in sorted({e for p in c[r].values()for e in p}):
            rows.append([c[r].get(h,{}).get(e,0)for h in keys])
    rr,pivots=rref(rows,len(keys))
    for h,weights in [((6,956),{28:-1,30:-6}),((6,17142),{28:1,30:5})]:
        row=[sum(a*c[8].get(g,{}).get(e,0)for e,a in weights.items())-int(g==h)for g in keys]
        for base,p in zip(rr,pivots):
            a=row[p]
            row=[x-a*y for x,y in zip(row,base)]
        assert not any(row),(h,row)
    assert all(p.get(e,0)==0 for h,p in c[8].items()if h[0]==8 for e in (28,30))
    out={'schema':'singularity.volume8.energy-tail-extraction.v1','hypothesis':'equal height coefficients through7',
      'T':'Theta223','D':'closed diamond','c_j':'[q^j] delta L8',
      'formulas':{'delta N_T':'-c28 - 6 c30','delta N_D':'c28 + 5 c30'},
      'lower_observation_rank':len(rr),'determinant':-1,'failures':0}
    (HERE/'vol8_tail_check.json').write_text(json.dumps(out,indent=2)+'\n')
    print('Exact energy-tail recovery identities passed modulo agreement through7.')

if __name__=='__main__':main()
