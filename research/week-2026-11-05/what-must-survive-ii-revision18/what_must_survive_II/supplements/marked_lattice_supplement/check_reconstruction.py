"""Exact sanity checks of the polar-simplex reconstruction identity."""
import json
from pathlib import Path
import sympy as s
import networkx as nx
from theta_arithmetic import load_pair

def check(G):
    n=len(G); L=s.Matrix(nx.laplacian_matrix(G,nodelist=sorted(G)).toarray().tolist())
    P=s.ones(n)/n; J=s.eye(n)-P
    K=(L+P).inv()-P
    verts=[s.ones(n,1)-n*s.eye(n)[:,i] for i in range(n)]
    D=s.Matrix(n,n,lambda i,j:((verts[i]-verts[j]).T*K*(verts[i]-verts[j]))[0])
    K2=-J*D*J/(2*n*n)
    L2=(K2+P).inv()-P
    assert K2==K and L2==L
    return {'n':n,'exact_reconstruction':True,'squared_dual_distances':[[str(D[i,j]) for j in range(n)] for i in range(n)]}
if __name__=='__main__':
    gs={'K4':nx.complete_graph(4),'K3_3':nx.complete_bipartite_graph(3,3),'Petersen':nx.petersen_graph()}
    a,b=load_pair();gs.update(late14_A=a,late14_B=b)
    result={k:check(g) for k,g in gs.items()}
    Path(__file__).with_name('reconstruction_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print({k:v['exact_reconstruction'] for k,v in result.items()})
