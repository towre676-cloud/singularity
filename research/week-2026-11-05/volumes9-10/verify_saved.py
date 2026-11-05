"""Fast exact audit of saved laws, row witnesses, inverses and minimality vectors."""
from pathlib import Path
from fractions import Fraction as F
import json
P=Path(__file__).resolve().parent

def plus(a,b,scale=1):
 out=dict(a)
 for h,c in b.items():out[h]=out.get(h,F(0))+scale*c
 return {h:c for h,c in out.items() if c}

def main():
 report=[]
 for R in (9,10):
  law=json.loads((P/f'vol{R}_law.json').read_text());reader=json.loads((P/f'vol{R}_reader.json').read_text())
  c={int(r):{(x['k'],x['mask']):{int(e):F(a) for e,a in x['polynomial'].items()} for x in xs} for r,xs in law['coefficient_rows'].items()}
  row=lambda r,e:{h:p[e] for h,p in c[r].items() if p.get(e,0)}
  for defi,wit in zip(reader['coordinate_definitions'],reader['coordinate_source_witnesses']):
   target={(k,m):F(a) for k,m,a in defi};got={}
   for r,e,a in wit:got=plus(got,row(r,e),F(a))
   assert got==target
  ff=[{int(e):F(a) for e,a in p.items()} for p in reader['coefficient_functions']]
  panel=reader['coefficient_degrees'];inv=[[F(a) for a in rr] for rr in reader['inverse']];d=len(ff)
  assert all(sum(inv[i][k]*ff[j].get(panel[k],0) for k in range(d))==int(i==j) for i in range(d) for j in range(d))
  residual={(x['k'],x['mask']):{int(e):F(a) for e,a in x['polynomial'].items()} for x in law['ninth_lower_support_residual' if R==9 else 'tenth_lower_support_residual']}
  definitions=[{(k,m):F(a) for k,m,a in ds} for ds in reader['coordinate_definitions']]
  for h in set(c[R])|set(residual):
   expected=c[R].get(h,{}) if h[0]==R else residual.get(h,{})
   reconstructed={}
   for basis,defi in zip(ff,definitions):
    reconstructed=plus(reconstructed,basis,defi.get(h,0))
   assert expected==reconstructed
  for elim in law['lower_elimination']:
   e=elim['qexp'];got={}
   for r,t,a in elim['lower_rows']:got=plus(got,row(r,t),F(a))
   got=plus(got,{h:p[e] for h,p in residual.items() if p.get(e,0)})
   target={h:p[e] for h,p in c[R].items() if h[0]<R and p.get(e,0)}
   assert got==target
  witnesses=json.loads((P/f'vol{R}_witnesses.json').read_text())
  for cls in witnesses['classes']:
   assert len(cls['witnesses'])==cls['new_dimension']
   for w in cls['witnesses']:
    v={(k,m):a for k,m,a in w['core_difference']}
    for r in range(1,R):
     assert all(sum(a*c[r].get(h,{}).get(e,0) for h,a in v.items())==0 for e in {e for p in c[r].values() for e in p})
    delta={e:sum(a*c[R].get(h,{}).get(e,0) for h,a in v.items()) for e in {e for p in c[R].values() for e in p}}
    assert {e:a for e,a in delta.items() if a}=={int(e):F(a) for e,a in w[f'delta{R}'].items()}
    for j,e in enumerate(cls['coefficient_panel']):assert delta.get(e,0)==(w['scale'] if e==w['isolated_degree'] else 0)
  report.append({'volume':R,'rank':law['total_rank'],'new_dimension':d,'source_witnesses':d,'inverse_verified':True,'classes_verified':4})
 out={'checks':report,'failures':0};(P/'saved_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
