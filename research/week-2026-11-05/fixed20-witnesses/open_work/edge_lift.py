import sys,json,time
from pathlib import Path
from itertools import combinations
sys.path.insert(0,'open_work');sys.path.insert(0,'final_bundle/replay')
from core_search import features,low
from verify_advance import vector,connectivity
from vol8_law import rref

def edge_variants(w,side):
 n=w['n'];E=[tuple(sorted(e)) for e in w[side]]
 for i,j in combinations(range(len(E)),2):
  a,b=E[i];c,d=E[j]
  es=[e for k,e in enumerate(E) if k not in (i,j)]+[(a,n),(b,n),(c,n+1),(d,n+1),(n,n+1)]
  yield [i,j],sorted(tuple(sorted(e)) for e in es)

def find(w,target):
 n=w['n'];by={}
 for mark,A in edge_variants(w,'A_edges'):
  f=features(n+2,A);by.setdefault(low(f),[]).append((mark,A,f))
 for mark,B in edge_variants(w,'B_edges'):
  fb=features(n+2,B)
  for ma,A,fa in by.get(low(fb),[]):
   dd={e:fb[8].get(e,0)-fa[8].get(e,0) for e in fb[8].keys()|fa[8].keys()};dd={e:a for e,a in dd.items() if a}
   if not dd:continue
   v=vector(dd)
   if v[target]:yield {'n':n+2,'A_edges':A,'B_edges':B,'coordinates_B_minus_A':v,'expanded_edges_A':ma,'expanded_edges_B':mark}

if __name__=='__main__':
 s=json.load(open('final_bundle/replay/fresh_small_witnesses.json'))['witnesses']
 out=json.load(open('open_work/lift_checkpoint.json'))
 for label,w,target in [('closed_diamond',s[5],5),('Theta223',s[3],4)]:
  t=time.monotonic();selected=None;tries=0
  for first in find(w,target):
   tries+=1
   if first['n']==20:selected=first;break
   for second in find(first,target):selected=second;selected['first_expansion']={k:v for k,v in first.items() if k not in ('A_edges','B_edges')};break
   if selected:break
  if selected:
   assert all(connectivity(20,selected[side],2) for side in ('A_edges','B_edges'))
   selected['edge_connectivity_lower_bound']=2;selected['target']=label
   out['pairs'].append(selected)
   out['rank']=len(rref([p['coordinates_B_minus_A'] for p in out['pairs']],6)[0])
   Path('open_work/fixed20_checkpoint.json').write_text(json.dumps(out,indent=2)+'\n')
   print('FOUND',label,selected['coordinates_B_minus_A'],'rank',out['rank'],'tries',tries,'seconds',time.monotonic()-t,flush=True)
  else:print('NOT FOUND',label,tries,'seconds',time.monotonic()-t,flush=True)
