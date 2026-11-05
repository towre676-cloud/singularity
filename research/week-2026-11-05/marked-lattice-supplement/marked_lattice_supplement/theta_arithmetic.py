"""Exact arithmetic for the root-of-unity theta decomposition. Python 3 + sympy/networkx."""
from pathlib import Path
import json, math
import sympy as s
import networkx as nx
from sympy.matrices.normalforms import smith_normal_form
ROOT=Path(__file__).resolve().parent

def record(G,d):
    n=len(G); r=n-1
    Q=s.Matrix(nx.laplacian_matrix(G,nodelist=sorted(G)).toarray().tolist())[:-1,:-1]
    H=s.eye(r); H[0,0]=d
    for j in range(1,r): H[0,j]=-1
    B=H.T*(2*Q)*H
    D=B.inv()
    denominators=[int((D[i,i]/2).q) for i in range(r)]
    denominators += [int(D[i,j].q) for i in range(r) for j in range(i)]
    N=math.lcm(*denominators)
    assert abs(H.det())==d
    assert B.det()==d*d*2**r*Q.det()
    assert all((N*D[i,j]).q==1 for i in range(r) for j in range(r))
    assert all((N*D[i,i]/2).q==1 for i in range(r))
    # Minimality follows from exact lcm, tested at all proper divisors as well.
    assert not any(all((m*D[i,j]).q==1 for i in range(r) for j in range(r)) and all((m*D[i,i]/2).q==1 for i in range(r)) for m in s.divisors(N)[:-1])
    S=smith_normal_form(B,domain=s.ZZ)
    return dict(n=n,rank=r,character_order=d,tree_count=int(Q.det()),even_gram_determinant=int(B.det()),even_lattice_level=N,smith=[abs(int(S[i,i])) for i in range(r)],gram=[list(map(int,B.row(i))) for i in range(r)],inverse=[[str(D[i,j]) for j in range(r)] for i in range(r)])

def load_pair():
    p=ROOT/'unseparated_pair_n14.txt'
    out=[]
    for line in p.read_text().splitlines():
        w=list(map(int,line.split()))
        if w: out.append(nx.Graph([(w[2+2*i],w[3+2*i]) for i in range(w[1])]))
    return out[:2]

def main():
    graphs={'K4':nx.complete_graph(4),'K3_3':nx.complete_bipartite_graph(3,3),'Petersen':nx.petersen_graph()}
    a,b=load_pair(); graphs.update(late14_A=a,late14_B=b)
    out={name:[record(g,int(d)) for d in s.divisors(len(g))] for name,g in graphs.items()}
    (ROOT/'theta_arithmetic.json').write_text(json.dumps(out,indent=2)+'\n')
    for name,recs in out.items():
        print(name,[(z['character_order'],z['even_lattice_level'],z['even_gram_determinant']) for z in recs])
if __name__=='__main__': main()
