from pathlib import Path
src=(Path(__file__).parent/'quartic_exact.py').read_text().replace('self.q=F(q);q=self.q;H=6;M=6','self.q=q;q=self.q;H=6;M=6')
ns={};exec(compile(src,'quartic_symbolic','exec'),ns)
from sympy.polys.fields import field
from sympy.polys.domains import QQ
from itertools import combinations,product
import json,time
K,q=field('q',QQ);E=ns['FourthJet'](q);out={};t0=time.time()
for n in (3,4):
 seen=set();records=[];poss=list(combinations(range(n),2))
 for mask in range(1,1<<len(poss)):
  edges=tuple(e for j,e in enumerate(poss) if mask>>j&1);ds=[sum(v in e for e in edges) for v in range(n)]
  if max(ds)>3:continue
  reach={0}
  while True:
   nxt=reach|{b for a,b in edges if a in reach}|{a for a,b in edges if b in reach}
   if nxt==reach:break
   reach=nxt
  if len(reach)!=n:continue
  for deg in product((2,3),repeat=n):
   if any(deg[i]<ds[i] for i in range(n)):continue
   key=ns['canon'](deg,edges)
   if key in seen:continue
   seen.add(key);c=E.local(deg,edges)[4]
   if c==0:pole=None
   else:pole=(c.numer.degree()-c.denom.degree()-12)//2
   allp=[]
   for j in range(1,5):
    z=E.local(deg,edges)[j]
    allp.append(None if not z else (z.numer.degree()-z.denom.degree()-3*j)/2)
   records.append({'degree_labels':deg,'edges':edges,'pole_after_q12':pole,'poles_by_jet':allp})
 out[str(n)]={'types':len(records),'maximum':max(r['pole_after_q12'] for r in records if r['pole_after_q12'] is not None),'records':records}
 print(n,out[str(n)]['types'],out[str(n)]['maximum'],'seconds',time.time()-t0,flush=True)
assert out['3']['maximum']<=13 and out['4']['maximum']<=9
assert all(r['poles_by_jet'][2] is None or r['poles_by_jet'][2]<=10 for r in out['3']['records'])
json.dump(out,open(Path(__file__).parent/'local_pole_bounds.json','w'),indent=2)
