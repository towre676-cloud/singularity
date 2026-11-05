"""Readers for every connectivity class, directly in measured-coefficient coordinates."""
from pathlib import Path
from fractions import Fraction as Q
import json
from vol9_build import rows
from vol8_law import rref
P=Path(__file__).resolve().parent

def main():
 out=[]
 for R in (9,10):
  law=json.loads((P/f'vol{R}_law.json').read_text());ws=json.loads((P/f'vol{R}_witnesses.json').read_text());cs=json.loads((P/f'vol{R}_connectivity.json').read_text())
  c={int(r):{(x['k'],x['mask']):{int(e):Q(a) for e,a in x['polynomial'].items()} for x in rr} for r,rr in law['coefficient_rows'].items()}
  for cls,cl in zip(ws['classes'],cs):
   keys=[tuple(h) for h in cl['keys']];panel=cls['coefficient_panel'];ff=[{int(e):Q(a)/w['scale'] for e,a in w[f'delta{R}'].items()} for w in cls['witnesses']]
   assert all(p.get(e,0)==int(i==j) for i,p in enumerate(ff) for j,e in enumerate(panel))
   _,lo=rows(c,R-1,keys);rr,piv=rref(lo,len(keys))
   for e in {e for p in c[R].values() for e in p}:
    row=[c[R].get(h,{}).get(e,0)-sum(p.get(e,0)*c[R].get(h,{}).get(j,0) for j,p in zip(panel,ff)) for h in keys]
    for base,j in zip(rr,piv):
     a=row[j];row=[x-a*y for x,y in zip(row,base)]
    assert not any(row),(R,cls['edge_connectivity'],e)
   out.append({'volume':R,'edge_connectivity':cls['edge_connectivity'],'degrees':panel,
                'reconstruction_basis':[{str(e):str(a) for e,a in sorted(p.items())} for p in ff],
                'formula':'Delta L_R(q)=sum_j ([q^degree_j] Delta L_R) * basis_j(q)',
                'full_source_row_quotient_check':True})
   print('CLASS READER',R,cls['edge_connectivity'],panel,flush=True)
 (P/'class_readers.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
