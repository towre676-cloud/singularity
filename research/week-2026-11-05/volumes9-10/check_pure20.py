"""Close the inherited pending direct replay of the pure Q0/Q1 witnesses."""
from pathlib import Path
import json,sys,subprocess
P=Path(__file__).resolve().parent
def connectivity(n,E,k):
 from collections import deque
 adj=[[] for _ in range(n)]
 for u,v in E:adj[u].append(v);adj[v].append(u)
 for target in range(1,n):
  flow={}
  for _ in range(k):
   parent={0:None};todo=deque([0])
   while todo and target not in parent:
    u=todo.popleft()
    for v in adj[u]:
     if v not in parent and flow.get((u,v),0)<1:parent[v]=u;todo.append(v)
   if target not in parent:return False
   v=target
   while v:
    u=parent[v];flow[u,v]=flow.get((u,v),0)+1;flow[v,u]=flow.get((v,u),0)-1;v=u
 return True

def encode(n,E):
 es={tuple(sorted(e)) for e in E};bits=[int((i,j) in es) for j in range(1,n) for i in range(j)]
 bits += [0]*((-len(bits))%6)
 return chr(n+63)+''.join(chr(63+sum(bits[i+j]<<(5-j) for j in range(6))) for i in range(0,len(bits),6))

def main():
 d=json.loads((P/'pure20_fixture.json').read_text());ws=d['unit_witnesses']
 lines=[]
 for w in ws.values():
  for side in ('A_edges','B_edges'):
   assert connectivity(20,w[side],2)
   lines.append(encode(20,w[side]))
 (P/'pure20.g6').write_text('\n'.join(lines)+'\n')
 subprocess.run([str(P/'direct9'),str(P/'pure20.g6'),str(P/'pure20_direct9.json')],check=True)
 direct=json.loads((P/'pure20_direct9.json').read_text());out=[]
 for j,(name,w) in enumerate(ws.items()):
  A,B=direct[2*j:2*j+2]
  for r in range(8):assert A['coefficients'][str(r)]==B['coefficients'][str(r)]
  aa={int(e):a for e,a in A['coefficients']['8'].items()};bb={int(e):a for e,a in B['coefficients']['8'].items()}
  dd={e:bb.get(e,0)-aa.get(e,0) for e in aa.keys()|bb.keys()};dd={e:v for e,v in dd.items() if v}
  from fractions import Fraction as F
  from vol8_offdiagonal import multiply,power
  kap={1:F(1),3:F(-1)};f={-2:F(1),0:F(-1)}
  expected_poly=power(kap,8)
  if name=='Q1':expected_poly=multiply(expected_poly,f)
  assert dd==expected_poly
  v=[1,0,0,0,0,0] if name=='Q0' else [0,1,0,0,0,0]
  assert v==w['coordinates_B_minus_A']
  out.append({'name':name,'n':20,'coordinates_B_minus_A':v,'bridgeless':True,
              'direct_height_through_volume':9,'source_witness':w})
 (P/'pure20_verified.json').write_text(json.dumps({'witnesses':out,'failures':0},indent=2)+'\n')
 print('PURE Q0 AND Q1 VERIFIED',[(w['name'],w['coordinates_B_minus_A']) for w in out])
if __name__=='__main__':main()
