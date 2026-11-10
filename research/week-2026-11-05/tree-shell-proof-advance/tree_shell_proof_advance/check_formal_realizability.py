"""A nonnegative, boundary-consistent formal census need not be realizable."""
import json
from pathlib import Path
import networkx as nx
from contractions import census,canonical
from symbolic_relation import TERMS,aff
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    out=[]
    adj=[[1],[0,2],[1,3],[2]]
    for m in range(5):
        n=m+10;actual=census(nx.path_graph(n),3);altered=actual.copy()
        for c,w in TERMS:
            weights=[a*m+b for a,b in map(aff,w)];altered[canonical(adj,weights)]+=c
        assert all(v>=0 for v in altered.values()) and altered!=actual
        assert sum(altered.values())==sum(actual.values())
        # The all-parameter proof in symbolic_relation.py supplies equal boundary and shell.
        # No-star implies max degree <=2 in any tree realizer, hence it must be P_n.
        out.append({'n':n,'nonnegative_integer_census':True,'same_total_mass':True,'different_from_path':True,'unrealizable_reason':'Every type is a path. A tree with a degree >=3 has a star three-edge quotient. Thus a realizer must be the unique n-vertex path, whose census is different.'})
    (ROOT/'formal_realizability_checks.json').write_text(json.dumps(out,indent=2)+'\n');print('Five exact base checks passed; all-parameter argument is in the report.')
