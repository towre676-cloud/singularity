import sys,json,time
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,'open_work');sys.path.insert(0,'final_bundle/replay')
from core_search import features,triangle,low
from verify_advance import connectivity
from edge_lift import edge_variants
from edge_lift import find
from vol8_reader import factors
NAMES=('Q0','Q1','S8_10','S8_11','Theta223','closed_diamond')
inv=[[F(x) for x in row] for row in json.load(open('final_bundle/replay/fresh_algebra_certificate.json'))['panels']['six']['inverse']]
panel=(6,10,14,18,24,26)
groups={};found={};multiples={};seen=set();processed=0
stream=Path('open_work/pure_pool.jsonl').open('w')

def checkpoint():
 Path('open_work/pure_checkpoint.json').write_text(json.dumps({'processed_graphs':processed,'unit_witnesses':found,'pure_multiple_witnesses':multiples},indent=2)+'\n')

def add(E,mark):
 global processed
 E=sorted(tuple(sorted(e)) for e in E);key=tuple(E)
 if key in seen:return
 seen.add(key);f=features(20,E);kk=low(f);processed+=1
 stream.write(json.dumps({'n':20,'edges':E,'mark':mark,'source_features':{str(r):{str(e):str(a) for e,a in p.items()} for r,p in f.items()}},separators=(',',':'))+'\n');stream.flush()
 if kk not in groups:groups[kk]={'ref':f[8],'indexes':[{} for _ in range(6)]}
 g=groups[kk];dd={e:f[8].get(e,0)-g['ref'].get(e,0) for e in f[8].keys()|g['ref'].keys()}
 coords=[sum(row[j]*dd.get(panel[j],0) for j in range(6)) for row in inv]
 assert all(a.denominator==1 for a in coords);coords=list(map(int,coords))
 for i in range(6):
  h=tuple(a for j,a in enumerate(coords) if j!=i);bucket=g['indexes'][i].setdefault(h,{})
  for value,old in list(bucket.items()):
   delta=coords[i]-value
   if not delta:continue
   target=found if abs(delta)==1 else multiples
   if NAMES[i] not in target:
    A,B=(old['edges'],E) if delta>0 else(E,old['edges'])
    target[NAMES[i]]={'n':20,'A_edges':A,'B_edges':B,'coordinates_B_minus_A':[abs(delta) if j==i else 0 for j in range(6)],'scale':abs(delta),'marks':[old['mark'],mark]}
    checkpoint();print('PURE',NAMES[i],'scale',abs(delta),'processed',processed,flush=True)
  bucket.setdefault(coords[i],{'edges':E,'mark':mark})
 if processed%100==0:checkpoint();print('PROCESSED',processed,'groups',len(groups),flush=True)

s=json.load(open('final_bundle/replay/fresh_small_witnesses.json'))['witnesses']
# Existing fixed-order witnesses seed the pool.
for i,p in enumerate(json.load(open('open_work/fixed20_checkpoint.json'))['pairs']):
 for side in ('A_edges','B_edges'):add(p[side],['fixed',i,side])
# All 20-vertex two-edge expansions of the closed-diamond pair.
w=s[5]
for side in ('A_edges','B_edges'):
 for mark,E in edge_variants(w,side):add(E,['edge_D',side,mark])
# Recover one compatible 18-vertex Theta223 lift, then expand every edge pair.
w=next(find(s[3],4))
for side in ('A_edges','B_edges'):
 for mark,E in edge_variants(w,side):add(E,['edge_T',side,mark])
# Two triangle expansions of the three other 16-vertex parent pairs.
for wi in (1,2,4):
 w=s[wi]
 for side in ('A_edges','B_edges'):
  for v in range(16):
   n,E=triangle(16,w[side],v)
   for u in range(18):add(triangle(n,E,u)[1],['two_triangles',wi,side,v,u])
checkpoint();stream.close();print('DONE',processed,'units',list(found),'multiples',list(multiples),flush=True)
