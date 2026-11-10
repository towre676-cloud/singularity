import sys,json
from pathlib import Path
from itertools import permutations
from math import lcm
sys.path.insert(0,'open_work');sys.path.insert(0,'final_bundle/replay')
from core_search import c,contribution
from vol8_lib import edges_of,PIDX
from vol8_reader import factors
C=sorted({h for d in c.values() for h in d if h[0]>1})
scale=lcm(*(a.denominator for d in c.values() for p in d.values() for a in p.values()))
with open('open_work/weights.txt','w') as w,open('open_work/orbits.txt','w') as o:
 w.write(f'{len(C)} {scale}\n')
 for ident,(k,m) in enumerate(C):
  w.write(f'{k} {m}\n');cc=contribution(k,m)
  for r in range(3,9):
   p={e:int(a*scale) for e,a in cc[r].items() if a};w.write(str(len(p))+' '+' '.join(f'{e} {a}' for e,a in sorted(p.items()))+'\n')
  orbit=set();E=edges_of(m,k)
  for pp in permutations(range(k)):
   mm=sum(1<<PIDX[k][tuple(sorted((pp[a],pp[b])))] for a,b in E);orbit.add(mm)
  for mm in sorted(orbit):o.write(f'{k} {mm} {ident}\n')
 for i in (0,1,2,3,5,6):
  p=factors()[i];w.write(str(len(p))+' '+' '.join(f'{e} {int(a*scale)}' for e,a in sorted(p.items()))+'\n')
print('TABLES',len(C),scale,flush=True)
