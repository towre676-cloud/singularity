"""Which elementary graph statistics separate the supplied shell-three survivors?"""
from pathlib import Path
from collections import Counter
import json,networkx as nx,sympy as s
from contractions import diff
ROOT=Path(__file__).resolve().parent

def projections(T):
    deg=dict(T.degree());D=Counter(deg.values());Ed=Counter(deg[u]+deg[v] for u,v in T.edges());A=Counter();L2=Counter()
    vs=list(T)
    for v in vs:L2[4*deg[v]]+=1
    for i,v in enumerate(vs):
      for w in vs[i+1:]:
        A[deg[v]+deg[w]]+=1;L2[deg[v]+deg[w]-2*int(T.has_edge(v,w))]+=1
    q=s.Symbol('q');P=lambda c:sum(v*q**k for k,v in c.items())
    recovered=s.cancel(q*q*(P(L2)-sum(v*q**(4*k) for k,v in D.items())-P(A))/(1-q*q))
    assert s.expand(recovered-P(Ed))==0
    return D,Ed,L2
if __name__=='__main__':
    source=json.loads((ROOT/'survivor_inputs.json').read_text());out=[]
    for n in ('16','17','18'):
      for i,pair in enumerate(source[n]['survivor_edges']):
        a,b=map(nx.Graph,pair);assert nx.is_tree(a) and nx.is_tree(b) and not nx.is_isomorphic(a,b)
        da,ea,la=projections(a);db,eb,lb=projections(b)
        dd,de=diff(da,db),diff(ea,eb)
        assert dd or de
        out.append({'n':int(n),'pair_number':i+1,'degree_difference':dd,'edge_degree_sum_difference':de,'volume2_difference':diff(la,lb),'resolved_by':'degree histogram' if dd else 'edge degree sum histogram'})
    (ROOT/'degree_projection_checks.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
