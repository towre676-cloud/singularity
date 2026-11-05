from pathlib import Path
from collections import Counter
import json,networkx as nx,sympy as s
from caterpillar import build,data
from verify_low_volume import low
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    formula=json.loads((ROOT/'two_parameter_volume.json').read_text());rows=[]
    for a,b in [(1,0),(1,1),(1,2),(1,3),(2,0),(2,1),(2,2),(3,0),(3,1),(3,2),(4,1)]:
        P=(a,b,a-1,a+b,b+1);Q=(a,a+b,b,a-1,b+1);G,H=build(P),build(Q)
        assert data(P)[:2]==data(Q)[:2]
        assert nx.is_isomorphic(G,H)==(a==b+1)
        for V in range(1,5):
            aa,bb=low(G,V),low(H,V);d=Counter()
            for t in formula[str(V)]:d[t['a']*a+t['b']*b+t['constant']]+=int(s.sympify(t['coefficient']).subs({'a':a,'b':b}))
            assert all(aa[e]-bb[e]==d[e] for e in aa.keys()|bb.keys()|d.keys())
            if V==4:assert (aa==bb)==(a==b+1)
        rows.append({'a':a,'b':b,'n':len(G),'isomorphic':a==b+1,'checks_passed':True})
    (ROOT/'two_parameter_checks.json').write_text(json.dumps(rows,indent=2)+'\n');print('Independent height checks passed on',len(rows),'two-parameter instances.')
