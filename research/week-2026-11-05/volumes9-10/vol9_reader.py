"""Construct and certify a ten-coordinate ninth-difference reader."""
from pathlib import Path
from fractions import Fraction as Q
import json
import sympy as S
from vol9_build import rows
P=Path(__file__).resolve().parent

def qp(poly):return {int(e):Q(c) for e,c in poly.items()}
def main():
 d=json.loads((P/'vol9_law.json').read_text())
 residual={(x['k'],x['mask']):qp(x['polynomial']) for x in d['ninth_lower_support_residual']}
 q=S.Symbol('q');t=S.Symbol('t');kap=q*(1-q*q);f=q**-2-1
 def poly(e):
  p=S.Poly(S.expand(e),q)
  return {int(k[0]):Q(c) for k,c in p.terms()}
 basis=[poly(kap**9*f**j) for j in range(5)]
 names=[f'corrected_S9_{9+j}' for j in range(5)]
 keys=sorted(residual)
 exps=sorted({e for p in basis+list(residual.values()) for e in p})
 def mat(ps):return S.Matrix([[p.get(e,0) for p in ps] for e in exps])
 rank=5;chosen=[]
 for h in keys:
  r=mat(basis+[residual[h]]).rank()
  if r>rank:
   basis.append(residual[h]);names.append('delayed_%s_%s'%h);chosen.append(h);rank=r
 assert rank==10
 F=mat(basis)
 panel=tuple(exps[i] for i in F.T.rref()[1])
 M=S.Matrix([[p.get(e,0) for p in basis] for e in panel]);inv=M.inv()
 definitions=[{} for _ in basis]
 # Unreduced top-size terms and the lower-support residual form the entire
 # ninth difference once all coefficients through eight agree.
 allcols=dict(residual)
 for x in d['coefficient_rows']['9']:
  if x['k']==9:allcols[(9,x['mask'])]=qp(x['polynomial'])
 for h,p in allcols.items():
  coords=inv*S.Matrix([p.get(e,0) for e in panel])
  assert F*coords==S.Matrix([p.get(e,0) for e in exps]),h
  for i,c in enumerate(coords):
   if c:definitions[i][h]=str(c)
 # Prove each coordinate row belongs to full source rowspace and the
 # claimed basis reconstructs every q-coefficient modulo lower rows.
 c={int(r):{(x['k'],x['mask']):qp(x['polynomial']) for x in rs}
    for r,rs in d['coefficient_rows'].items()}
 allkeys=[tuple(h) for h in d['core_keys']]
 from vol8_law import rref
 labels,source=rows(c,9,allkeys);rr,piv,trans=rref(source,len(allkeys),True)
 witnesses=[]
 for defi in definitions:
  row=[Q(defi.get(h,0)) for h in allkeys];w={}
  for base,j,tr in zip(rr,piv,trans):
   a=row[j]
   if a:
    row=[x-a*y for x,y in zip(row,base)]
    for ii,z in tr.items():w[ii]=w.get(ii,Q(0))+a*z
  assert not any(row)
  witnesses.append([[*labels[ii],str(z)] for ii,z in sorted(w.items()) if z])
 lowerlabs,lower=rows(c,8,allkeys);lr,lp=rref(lower,len(allkeys))
 for e in sorted({e for p in c[9].values() for e in p}|set(exps)):
  row=[c[9].get(h,{}).get(e,0)-sum(b.get(e,0)*Q(de.get(h,0)) for b,de in zip(basis,definitions)) for h in allkeys]
  for base,j in zip(lr,lp):
   a=row[j];row=[x-a*y for x,y in zip(row,base)]
  assert not any(row),e
 out={'schema':'singularity.volume9.reader/1','delta_convention':'A minus B',
      'names':names,'basis_patterns':chosen,'dimension':10,'coefficient_degrees':panel,
      'determinant':str(M.det()),'inverse':[[str(x) for x in row] for row in inv.tolist()],
      'inverse_infinity_norm':str(max(sum(abs(x) for x in row) for row in inv.tolist())),
      'coordinate_definitions':[[[k,m,a] for(k,m),a in sorted(di.items())] for di in definitions],
      'coefficient_functions':[{str(e):str(c) for e,c in sorted(p.items())} for p in basis],
      'normalized_factors':[str(S.factor(sum(S.Rational(c)*q**e for e,c in p.items())/kap**9)) for p in basis],
      'coordinate_source_witnesses':witnesses,'full_source_row_quotient_check':True,
      'panel_status':'Exact invertible panel; not optimized'}
 (P/'vol9_reader.json').write_text(json.dumps(out,indent=2)+'\n')
 print('NAMES',names,'CHOSEN',chosen,'PANEL',panel,'DET',M.det(),flush=True)
 print('FACTORS',out['normalized_factors'],flush=True)
if __name__=='__main__':main()
