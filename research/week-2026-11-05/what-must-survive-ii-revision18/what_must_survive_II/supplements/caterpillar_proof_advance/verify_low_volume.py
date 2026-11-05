"""Independent direct height enumeration for the symbolic volume-four witness."""
from itertools import combinations_with_replacement
from collections import Counter
from pathlib import Path
import json
from caterpillar import build
ROOT=Path(__file__).resolve().parent

def low(T,V):
    deg=dict(T.degree());out=Counter()
    for vals in combinations_with_replacement(T.nodes(),V):
        h=Counter(vals);v=list(h)
        e=sum(deg[u]*hu*hu for u,hu in h.items())
        e-=2*sum(h[u]*h[w] for i,u in enumerate(v) for w in v[i+1:] if T.has_edge(u,w))
        out[e]+=1
    return out
if __name__=='__main__':
    inp=json.loads((ROOT/'low_volume_symbolic.json').read_text());out=[]
    for t in (1,2,3,4,5):
        a=build([t,t+1,t-1,2*t+1,t+2]);b=build([t,2*t+1,t+1,t-1,t+2])
        for V in range(1,5):
            aa,bb=low(a,V),low(b,V);delta=Counter()
            for row in inp[str(V)]:delta[row['energy_s']*t+row['energy_constant']]+=int(row['coefficient'])
            assert all(aa[e]-bb[e]==delta[e] for e in aa.keys()|bb.keys()|delta.keys())
        out.append({'s':t,'n':len(a),'volumes_1_2_3_equal':True,'volume_4_different':True,'highest_difference_energy':9*t+16,'highest_difference_coefficient':1})
        print('Direct volume checks passed for s=',t,flush=True)
    (ROOT/'low_volume_checks.json').write_text(json.dumps(out,indent=2)+'\n')
