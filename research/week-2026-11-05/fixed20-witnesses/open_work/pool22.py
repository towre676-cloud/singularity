import sys,json
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,'open_work');sys.path.insert(0,'final_bundle/replay')
from core_search import features,low
from edge_lift import edge_variants
from verify_advance import connectivity
NAMES=('Q0','Q1','S8_10','S8_11','Theta223','closed_diamond')
inv=[[F(x) for x in row] for row in json.load(open('final_bundle/replay/fresh_algebra_certificate.json'))['panels']['six']['inverse']];panel=(6,10,14,18,24,26)
groups={};found={};seen=set();count=0;stream=open('open_work/pool22.jsonl','w')
def add(E,mark):
 global count
 E=sorted(tuple(sorted(e)) for e in E)
 if tuple(E) in seen:return
 seen.add(tuple(E));f=features(22,E);key=low(f);count+=1
 stream.write(json.dumps({'n':22,'edges':E,'mark':mark,'features':{str(r):{str(e):str(a) for e,a in p.items()} for r,p in f.items()}},separators=(',',':'))+'\n');stream.flush()
 if key not in groups:groups[key]={'ref':f[8],'indexes':[{} for _ in range(6)]}
 g=groups[key];dd={e:f[8].get(e,0)-g['ref'].get(e,0) for e in f[8].keys()|g['ref'].keys()};v=[sum(row[j]*dd.get(panel[j],0) for j in range(6)) for row in inv];assert all(a.denominator==1 for a in v);v=list(map(int,v))
 for i in range(6):
  h=tuple(a for j,a in enumerate(v) if j!=i);bucket=g['indexes'][i].setdefault(h,{})
  for val in (v[i]-1,v[i]+1):
   if val in bucket and NAMES[i] not in found:
    old=bucket[val];A,B=(old['E'],E) if v[i]>val else(E,old['E'])
    assert connectivity(22,A,2) and connectivity(22,B,2)
    found[NAMES[i]]={'n':22,'A_edges':A,'B_edges':B,'coordinates_B_minus_A':[int(j==i) for j in range(6)],'marks':[old['mark'],mark]}
    Path('open_work/pool22_checkpoint.json').write_text(json.dumps({'processed':count,'unit_witnesses':found},indent=2)+'\n');print('FOUND22',NAMES[i],count,flush=True)
  bucket.setdefault(v[i],{'E':E,'mark':mark})
 if count%200==0:print('COUNT22',count,flush=True)
parents=json.load(open('open_work/fixed20_certificate.json'))['pairs']
# Prioritize the remaining S8_10, closed-diamond and S8_11 directions.
for pi in (0,4,3,5,1,2):
 p=parents[pi]
 for side in ('A_edges','B_edges'):
  for mark,E in edge_variants(p,side):add(E,[pi,side,mark])
Path('open_work/pool22_checkpoint.json').write_text(json.dumps({'processed':count,'unit_witnesses':found},indent=2)+'\n');print('DONE22',count,list(found),flush=True)
