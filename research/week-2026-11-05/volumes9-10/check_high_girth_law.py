"""Certify that lower supports cancel for girth at least five at volume 9."""
from pathlib import Path
from fractions import Fraction as Q
import json
from vol9_build import rows,lib
from vol8_law import rref
from vol9_girth import girth
P=Path(__file__).resolve().parent

def main():
 d=json.loads((P/'vol9_law.json').read_text());c={int(r):{(x['k'],x['mask']):{int(e):Q(a) for e,a in x['polynomial'].items()} for x in xs} for r,xs in d['coefficient_rows'].items()}
 out=[]
 for g in (5,6,7,8,9):
  keys=[tuple(h) for h in d['core_keys'] if h[0]==1 or girth(*h)>=g]
  _,lo=rows(c,8,keys);rr,piv=rref(lo,len(keys))
  for e in {e for h,p in c[9].items() if h[0]<9 for e in p}:
   row=[c[9].get(h,{}).get(e,0) if h[0]<9 else 0 for h in keys]
   for b,j in zip(rr,piv):
    a=row[j];row=[x-a*y for x,y in zip(row,b)]
   assert not any(row),(g,e)
  new=[h for h in keys if h[0]==9]
  out.append({'girth_at_least':g,'all_lower_support_terms_cancel':True,
              'top_edge_histogram':dict(__import__('collections').Counter(m.bit_count() for k,m in new)),
              'top_patterns':[{'k':k,'mask':m,'edges':lib.edges_of(m,k)} for k,m in new]})
 print(json.dumps([{k:v for k,v in x.items() if k!='top_patterns'} for x in out],indent=2))
 (P/'high_girth_law.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
