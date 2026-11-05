import sys,json
from pathlib import Path
from itertools import permutations
from fractions import Fraction as F
sys.path.insert(0,'open_work');sys.path.insert(0,'final_bundle/replay')
from core_search import features,low,c
from vol8_lib import degrees_of,edges_of
from verify_advance import admissible,connectivity
NAMES=('Q0','Q1','S8_10','S8_11','Theta223','closed_diamond');targets={'closed_diamond','S8_11'}
inv=[[F(x) for x in row] for row in json.load(open('final_bundle/replay/fresh_algebra_certificate.json'))['panels']['six']['inverse']];panel=(6,10,14,18,24,26)
groups={};found={};seen=set();processed=0

def add(E,f,mark):
 global processed
 E=sorted(tuple(sorted(e)) for e in E)
 if tuple(E) in seen:return
 seen.add(tuple(E));processed+=1
 if f is None:f=features(22,E)
 key=low(f)
 if key not in groups:groups[key]={'ref':f[8],'indexes':[{} for _ in range(6)]}
 g=groups[key];d={e:f[8].get(e,0)-g['ref'].get(e,0) for e in f[8].keys()|g['ref'].keys()};v=[sum(row[j]*d.get(panel[j],0) for j in range(6)) for row in inv];assert all(x.denominator==1 for x in v);v=list(map(int,v))
 for i in (3,5):
  h=tuple(x for j,x in enumerate(v) if j!=i);bucket=g['indexes'][i].setdefault(h,{})
  for val in(v[i]-1,v[i]+1):
   if val in bucket and NAMES[i] not in found:
    old=bucket[val];A,B=(old['E'],E) if v[i]>val else(E,old['E'])
    assert connectivity(22,A,2) and connectivity(22,B,2)
    found[NAMES[i]]={'n':22,'A_edges':A,'B_edges':B,'coordinates_B_minus_A':[int(j==i) for j in range(6)],'marks':[old['mark'],mark]}
    Path('open_work/ring22_checkpoint.json').write_text(json.dumps({'processed':processed,'unit_witnesses':found},indent=2)+'\n');print('FOUND22',NAMES[i],processed,flush=True)
  bucket.setdefault(v[i],{'E':E,'mark':mark})

for line in Path('open_work/pool22.jsonl').open():
 row=json.loads(line);f={int(r):{int(e):F(a) for e,a in p.items()} for r,p in row['features'].items()};add(row['edges'],f,['old_pool',row['mark']])
print('PRELOADED',processed,flush=True)
U=[]
for k,m in sorted({h for d in c.values() for h in d}):
 if k not in(4,6,8) or 3*k-2*m.bit_count()!=2 or not admissible(k,m,2):continue
 E=set(edges_of(m,k));ports=[v for v,d in enumerate(degrees_of(m,k)) if d==2];others=[v for v in range(k) if v not in ports]
 sym=False
 for order in permutations(others):
  pp=dict(zip(others,order));pp[ports[0]]=ports[1];pp[ports[1]]=ports[0]
  if all(tuple(sorted((pp[a],pp[b]))) in E for a,b in E):sym=True;break
 U.append((k,m,tuple(sorted(E)),ports,sym))
tokens=[(i,o) for i,u in enumerate(U) for o in range(1 if u[4] else 2)]
def canon(w):
 rev=tuple((i,0 if U[i][4] else 1-o) for i,o in reversed(w));w=tuple(w)
 return min([w[j:]+w[:j] for j in range(len(w))]+[rev[j:]+rev[:j] for j in range(len(rev))])
words=set()
def grow(w,rem):
 if rem==0:words.add(canon(w));return
 for tok in tokens:
  if U[tok[0]][0]<=rem:grow(w+[tok],rem-U[tok[0]][0])
grow([],22);print('RING WORDS',len(words),'unit types',len(U),'oriented tokens',len(tokens),flush=True)
for j,word in enumerate(sorted(words)):
 E=[];offs=[];n=0;ports=[]
 for i,o in word:
  k,m,es,pp,sym=U[i];offs.append(n);E.extend((n+a,n+b) for a,b in es);ports.append(pp if o==0 else pp[::-1]);n+=k
 for i in range(len(word)):E.append((offs[i]+ports[i][1],offs[(i+1)%len(word)]+ports[(i+1)%len(word)][0]))
 add(E,None,['ring',word])
 if j%100==0:print('RINGS',j,'found',list(found),flush=True)
 if targets<=set(found):break
Path('open_work/ring22_checkpoint.json').write_text(json.dumps({'processed':processed,'ring_family_size':len(words),'unit_witnesses':found},indent=2)+'\n');print('DONE RINGS',processed,list(found),flush=True)
