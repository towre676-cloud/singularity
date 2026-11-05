from pathlib import Path
from fractions import Fraction as F
from math import lcm
from flint import fmpz_mat
import json,time
R=Path(__file__).parent;rows=[];L=1;t0=time.time()
for l in (R/'rows14_exact.txt').read_text().splitlines():
 w=l.split();v,e,n=map(int,w[:3]);d={int(w[3+3*j]):F(int(w[4+3*j]),int(w[5+3*j])) for j in range(n)};rows.append((v,e,d))
 for x in d.values():L=lcm(L,x.denominator)
col={}
for i,(v,e,d) in enumerate(rows):
 for c,x in d.items():col.setdefault(c,{})[i]=int(x*L)
U=list(set(tuple(sorted(x.items())) for x in col.values()));M=[[0]*len(U) for _ in rows]
for j,c in enumerate(U):
 for i,x in c:M[i][j]=x
B=[i for i,(v,e,d) in enumerate(rows) if v<14]
P=B+[i for i,(v,e,d) in enumerate(rows) if v==14 and 0<=e<=64 and e%2==0]
rk=lambda ix:int(fmpz_mat([M[i] for i in ix]).rank())
res={'V':14,'earlier_rank':rk(B),'earlier_plus_window_rank':rk(P),'full_rank':rk(list(range(len(rows)))),'window_energies':list(range(0,65,2)),'column_classes':len(U),'seconds':time.time()-t0}
assert res['earlier_rank']==109 and res['full_rank']==res['earlier_plus_window_rank']==142
(R/'window14_rational.json').write_text(json.dumps(res,indent=2));print(res)
