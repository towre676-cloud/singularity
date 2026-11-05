import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,'final_bundle/replay')
from verify_advance import vector,connectivity
from vol8_reader import invert

def encode(n,E):
 es={tuple(sorted(e)) for e in E};bits=[int((i,j) in es) for j in range(1,n) for i in range(j)]
 bits += [0]*((-len(bits))%6)
 return chr(n+63)+''.join(chr(63+sum(bits[i+j]<<(5-j) for j in range(6))) for i in range(0,len(bits),6))
subprocess.run(['g++','-O3','-std=c++17','final_bundle/replay/direct_search.cpp','-o','open_work/direct_search'],check=True)
s=json.load(open('open_work/fixed20_checkpoint.json'))
for i,p in enumerate(s['pairs']):
 for side in ('A_edges','B_edges'):
  E=p[side];assert len(E)==30 and len({tuple(e) for e in E})==30
  assert all(sum(v in e for e in E)==3 for v in range(20)) and connectivity(20,E,2)
 path=Path(f'open_work/pair20_{i}.g6');path.write_text('\n'.join(encode(20,p[x]) for x in ('A_edges','B_edges'))+'\n')
 subprocess.run(['open_work/direct_search',str(path),f'open_work/pair20_{i}_direct.json'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 d=json.load(open(f'open_work/pair20_{i}_direct.json'));assert len(d['pairs'])==1
 got=vector({int(e):a for e,a in d['pairs'][0]['delta'].items()});assert got==p['coordinates_B_minus_A']
 p['independent_direct_height_check']=True
 print('VERIFIED',i,got,flush=True)
inv,det=invert([p['coordinates_B_minus_A'] for p in s['pairs']]);assert abs(det)==1
s['coordinate_determinant']=str(det);s['coordinate_inverse']=[[str(x) for x in row] for row in inv]
s['all_pairs_bridgeless']=True;s['all_pairs_order']=20
Path('open_work/fixed20_certificate.json').write_text(json.dumps(s,indent=2)+'\n')
print('UNIMODULAR FIXED20 BASIS VERIFIED',det,flush=True)
