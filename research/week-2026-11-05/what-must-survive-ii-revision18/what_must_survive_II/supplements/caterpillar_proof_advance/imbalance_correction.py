from collections import Counter
from itertools import combinations
from pathlib import Path
import json,networkx as nx
from exact_tree import full_shells,quotient,diff
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    edges=[[(1,0),(1,2),(1,3),(1,4),(0,5),(5,6)],[(1,0),(1,2),(1,3),(0,4),(0,6),(4,5)]]
    Ts=list(map(nx.Graph,edges));tables=[full_shells(T,2) for T in Ts];Bs=[]
    for T in Ts:
        T=nx.convert_node_labels_to_integers(T);E=list(T.edges());B=Counter()
        for F in combinations(range(len(E)),2):
            adj,w=quotient(7,E,F);B[w[next(i for i,v in enumerate(adj) if len(v)==2)]]+=1
        Bs.append(B)
    assert tables[0][1]==tables[1][1]
    db=diff(Bs[0],Bs[1]);ds=diff(tables[0][2],tables[1][2]);assert db=={'1':1,'2':-2,'3':1}
    for k,c in db.items():assert ds[str(7+int(k))]==-c
    out={'n':7,'edges':edges,'common_A':dict(tables[0][1]),'delta_B':db,'delta_shell2':ds,'delta_imbalance_nonzero':True}
    (ROOT/'imbalance_correction.json').write_text(json.dumps(out,indent=2)+'\n');print('Exact seven-vertex counterexample to the interpretation verified.')
