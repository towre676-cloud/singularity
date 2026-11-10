import sys,json,time
from pathlib import Path
sys.path.insert(0,'open_work');sys.path.insert(0,'final_bundle/replay')
from core_search import features,triangle,low
from verify_advance import vector,connectivity
from vol8_law import rref
P=Path('open_work/lift_checkpoint.json')
saved=[]

def candidates(w):
 n=w['n']; sides=[]
 for side in ('A_edges','B_edges'):
  rows=[]
  for v in range(n):
   nn,E=triangle(n,w[side],v);f=features(nn,E);rows.append((v,E,f))
  sides.append(rows)
 by={}
 for v,E,f in sides[0]:by.setdefault(low(f),[]).append((v,E,f))
 for vb,B,fb in sides[1]:
  for va,A,fa in by.get(low(fb),[]):
   dd={e:fb[8].get(e,0)-fa[8].get(e,0) for e in fb[8].keys()|fa[8].keys()};dd={e:a for e,a in dd.items() if a}
   if dd:yield {'n':n+2,'A_edges':A,'B_edges':B,'coordinates_B_minus_A':vector(dd),
                 'triangle_vertices':[va,vb],'delta_L8':{str(e):str(a) for e,a in dd.items()}}
ws=json.load(open('final_bundle/replay/fresh_small_witnesses.json'))['witnesses']
for index,w in enumerate(ws[1:]):
 t=time.monotonic();found=None;tries=0
 for first in candidates(w):
  tries+=1
  if first['n']==20:found=first;break
  for second in candidates(first):
   found=second;found['first_triangle_vertices']=first['triangle_vertices'];break
  if found:break
 if found:
  found['original_witness_index']=index+1
  found['edge_connectivity_lower_bound']=2 if w['n']==18 else 3
  assert all(connectivity(20,found[x],found['edge_connectivity_lower_bound']) for x in ('A_edges','B_edges'))
  saved.append(found);P.write_text(json.dumps({'pairs':saved},indent=2)+'\n')
  print('LIFT',index+1,'vector',found['coordinates_B_minus_A'],'tries',tries,'seconds',time.monotonic()-t,flush=True)
 else:print('NO LIFT',index+1,'tries',tries,flush=True)
weld=json.load(open('final_bundle/replay/vol8_weld.json'))
saved.append({'n':20,'A_edges':weld['graphs'][0]['edges'],'B_edges':weld['graphs'][1]['edges'],
              'coordinates_B_minus_A':[0,-9,-6,-1,0,0],'edge_connectivity_lower_bound':2,'construction':'existing weld'})
rank=len(rref([p['coordinates_B_minus_A'] for p in saved],6)[0]);P.write_text(json.dumps({'rank':rank,'pairs':saved},indent=2)+'\n')
print('FINAL RANK',rank,flush=True)
