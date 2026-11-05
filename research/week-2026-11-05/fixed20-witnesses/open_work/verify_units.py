import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,'final_bundle/replay');sys.path.insert(0,'open_work')
from verify_advance import decode,vector,connectivity
# No import-time search effects.
def encode(n,E):
 es={tuple(sorted(e)) for e in E};bits=[int((i,j) in es) for j in range(1,n) for i in range(j)];bits += [0]*((-len(bits))%6)
 return chr(n+63)+''.join(chr(63+sum(bits[i+j]<<(5-j) for j in range(6))) for i in range(0,len(bits),6))
s=json.load(open('open_work/pure_n18.json'));lines=Path('final_bundle/replay/cubic18.g6').read_text().splitlines();out=[]
for i in (0,1,4):
 p=next(p for p in s['unit_pairs'] if p['coordinate']==i)
 A=decode(lines[p['A']])[1];B=decode(lines[p['B']])[1]
 assert connectivity(18,A,2) and connectivity(18,B,2)
 path=Path(f'open_work/pure18_{i}.g6');path.write_text(encode(18,A)+'\n'+encode(18,B)+'\n')
 subprocess.run(['open_work/direct_search',str(path),f'open_work/pure18_{i}_direct.json'],check=True,stderr=subprocess.DEVNULL)
 d=json.load(open(f'open_work/pure18_{i}_direct.json'));assert len(d['pairs'])==1
 v=vector({int(e):a for e,a in d['pairs'][0]['delta'].items()});assert v==[int(j==i) for j in range(6)]
 out.append({'n':18,'coordinate':i,'A_index':p['A'],'B_index':p['B'],'A_edges':A,'B_edges':B,'coordinates_B_minus_A':v,'bridgeless':True,'independent_direct_height_check':True})
 print('VERIFIED PURE18',i,p['A'],p['B'],flush=True)
Path('open_work/pure18_certificate.json').write_text(json.dumps({'witnesses':out,'minimum_order':18,'lower_catalogues_exclude_all_units_through16':True},indent=2)+'\n')
