from pathlib import Path
from fractions import Fraction as F
from math import lcm
from flint import fmpz_mat
import json,time
r=Path(__file__).parent;t0=time.time();pats=[]
for l in (r/'rows14_p1.txt.pats').read_text().splitlines():
 w=list(map(int,l.split()));pats.append((w[0],w[1]))
rows=[];L=1
for l in (r/'rows14_exact.txt').read_text().splitlines():
 w=l.split();v,e,nz=map(int,w[:3]);d={int(w[3+3*j]):F(int(w[4+3*j]),int(w[5+3*j])) for j in range(nz)}
 if v<=14:
  rows.append((v,e,d))
  for x in d.values():L=lcm(L,x.denominator)
def build(k):
 cols={}
 for i,(v,e,d) in enumerate(rows):
  for c,x in d.items():
   if c>0 and pats[c-1][0]>=k:cols.setdefault(c,{})[i]=int(x*L)
 U={tuple(sorted(z.items())) for z in cols.values()};M=[[0]*len(U) for _ in rows]
 for j,cv in enumerate(U):
  for i,x in cv:M[i][j]=x
 return M,len(U)
out={}
for k in (11,10):
 M,n=build(k);B=[i for i,x in enumerate(rows) if x[0]<14];R=[i for i,x in enumerate(rows) if x[0]==14]
 rank=lambda ids:int(fmpz_mat([M[i] for i in ids]).rank())
 rb=rank(B);dim=rank(B+R)-rb
 res={'lowest_size':k,'column_classes':n,'earlier_rank':rb,'dimension':dim}
 for cut in (72,74,64,62):res['rank_increment_e_ge_'+str(cut)]=rank(B+[i for i in R if rows[i][1]>=cut])-rb
 if k==10:
  profile=[];last=0
  for e in sorted((rows[i][1] for i in R),reverse=True):
   if e>74:continue
   inc=rank(B+[i for i in R if rows[i][1]>=e])-rb
   if inc>last:profile.append((e-42)//2);last=inc
   if last==dim:break
  res['exact_pole_profile']=sorted(profile)
 out[str(k)]=res;print(res,'seconds',round(time.time()-t0,2),flush=True)
json.dump(out,open(r/'rational_profile_V14.json','w'),indent=2)
