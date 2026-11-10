import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,'final_bundle/replay')
from verify_advance import vector,connectivity

def encode(n,E):
 es={tuple(sorted(e)) for e in E};bits=[int((i,j) in es) for j in range(1,n) for i in range(j)];bits += [0]*((-len(bits))%6)
 return chr(n+63)+''.join(chr(63+sum(bits[i+j]<<(5-j) for j in range(6))) for i in range(0,len(bits),6))
subprocess.run(['g++','-O3','-std=c++17','final_bundle/replay/direct_search.cpp','-o','open_work/direct_search'],check=True)
ps=json.load(open('open_work/pure18_certificate.json'))['witnesses']+[json.load(open('open_work/S10_20_certificate.json'))];out=[]
for i,p in enumerate(ps):
 n=p['n'];E=[p[x] for x in('A_edges','B_edges')]
 assert all(connectivity(n,e,3) for e in E)
 path=Path(f'open_work/pure_replay_{i}.g6');path.write_text('\n'.join(encode(n,e) for e in E)+'\n')
 subprocess.run(['open_work/direct_search',str(path),f'open_work/pure_replay_{i}.json'],check=True,stderr=subprocess.DEVNULL)
 d=json.load(open(f'open_work/pure_replay_{i}.json'));assert len(d['pairs'])==1
 v=vector({int(e):a for e,a in d['pairs'][0]['delta'].items()});assert v==p['coordinates_B_minus_A']
 out.append({'n':n,'A_edges':E[0],'B_edges':E[1],'coordinates_B_minus_A':v,'edge_connectivity_lower_bound':3,'independent_direct_height_check':True})
 print('VERIFIED PURE',n,v,flush=True)
Path('open_work/pure_direct_replay_certificate.json').write_text(json.dumps({'pure_unit_witnesses':out},indent=2)+'\n')
