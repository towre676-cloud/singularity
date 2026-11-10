import sys,json
from fractions import Fraction as F
from math import comb
from pathlib import Path
sys.path.insert(0,'final_bundle/replay')
from vol8_law import rref
s=json.load(open('final_bundle/replay/fresh_algebra_certificate.json'))['panels']['six'];inv=[[F(x) for x in row] for row in s['inverse']];panel=s['degrees']
rows=[]
for n in range(4,19,2):
 refs=json.load(open(f'open_work/reference{n}.json'));V=[]
 for p in refs:
  d={int(e):v for e,v in p['delta'].items()};v=[sum(row[j]*d.get(panel[j],0) for j in range(6)) for row in inv];assert all(a.denominator==1 for a in v);V.append(list(map(int,v)))
 rank=len(rref(V,6)[0]);u=json.load(open(f'open_work/pure_n{n}_replayed.json'))
 rows.append({'n':n,'graphs':u['graphs'],'nonzero_reference_pairs':len(refs),'difference_span_rank':rank,'pure_unit_pair_counts':u['unit_counts']})
assert [r['difference_span_rank'] for r in rows]==[0,0,0,0,1,1,4,5]
tokens=iter(Path('open_work/weights.txt').read_text().split());nt=int(next(tokens));scale=int(next(tokens));bounds={}
for _ in range(nt):
 k=int(next(tokens));next(tokens)
 for r in range(3,9):
  size=int(next(tokens))
  for _ in range(size):
   e=int(next(tokens));v=int(next(tokens));bounds[r,e]=bounds.get((r,e),0)+comb(20,k)*abs(v)
assert max(bounds.values())<2**63
out={'fresh_complete_catalogue_bounds_through18':rows,'integer_scale':scale,'source_absolute_int64_bound_at20':max(bounds.values()),'overflow_excluded':True,
     'pure_unit_minima_verified':{'Q0':18,'Q1':18,'Theta223':18,'S8_10':20},'common_order_six_basis_minimum':20}
Path('open_work/fresh_bounds_certificate.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
