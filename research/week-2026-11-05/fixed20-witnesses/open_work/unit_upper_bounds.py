import sys,json
from pathlib import Path
from collections import Counter
from fractions import Fraction as F
sys.path.insert(0,'final_bundle/replay')
from connected_check import independent_cores
from verify_advance import admissible
from vol8_lib import degrees_of,edges_of
from vol8_reader import factors
s=json.load(open('final_bundle/replay/vol8_observation.json'));law=json.load(open('final_bundle/replay/vol8_law.json'))
c={int(r):{(x['k'],x['mask']):{int(e):F(a) for e,a in x['polynomial'].items()} for x in d} for r,d in law['reduced_coefficients'].items()}
result=[]
for index in (0,1,2,3,5,6):
 w=s['seven_isolated_observation_witnesses'][index];scale=w['scale'];sides=[];actual=Counter()
 for sign in (1,-1):
  seeds=[];K=D=0
  for h,mult in w['signed_components'].items():
   if h=='0:0' or mult*sign<=0:continue
   k,m=map(int,h.split(':'));assert mult%scale==0 and admissible(k,m,2)
   a=abs(mult)//scale;K+=k*a;D+=(3*k-2*m.bit_count())*a;seeds.append({'k':k,'mask':m,'multiplicity':a})
   for j,v in independent_cores(k,m).items():actual[j]+=sign*a*v
  sides.append({'seeds':seeds,'K':K,'D':D})
 def pad(side,amount):
  if not amount:return
  assert amount>=4 and amount%2==0
  b=int(amount%4==2);a=(amount-6*b)//4;assert a>=0
  for k,m,v in ((1,0,a),(2,1,b)):
   if v:side['seeds'].append({'k':k,'mask':m,'multiplicity':v});side['K']+=k*v;side['D']+=(3*k-2*m.bit_count())*v
 delta=(sides[0]['K']+sides[0]['D'])-(sides[1]['K']+sides[1]['D'])
 if abs(delta)==2:pad(sides[int(delta>0)],6);pad(sides[int(delta<0)],4)
 elif delta:pad(sides[int(delta>0)],abs(delta))
 assert sides[0]['K']+sides[0]['D']==sides[1]['K']+sides[1]['D']
 t=max(6,max(x['D'] for x in sides));t+=t%2
 N=sides[0]['K']+sides[0]['D']+125*t
 for r in range(1,9):
  p={}
  for h,v in actual.items():
   for e,a in c[r].get(h,{}).items():p[e]=p.get(e,0)+v*a
  p={e:a for e,a in p.items() if a}
  assert p==({} if r<8 else factors()[index])
 result.append({'coordinate':w['isolated_observable'],'n':N,'reservoir_blocks':t,'sides':sides,'pure_unit':True,'bridgeless_by_capacity_theorem':True})
Path('open_work/unit_upper_bounds.json').write_text(json.dumps({'construction':'common prism reservoir with 125-vertex Q-minus-vertex blocks; A minus B','recipes':result},indent=2)+'\n')
print([(r['coordinate'],r['n']) for r in result],flush=True)
