"""Numerical checks only; modularity proof is in the accompanying report."""
import itertools, json
from pathlib import Path
import numpy as np
import networkx as nx

def gaussian(Q,b,tau,R=20):
    Q=np.array(Q,dtype=float);b=np.array(b,dtype=float);r=len(b)
    grid=np.array(list(itertools.product(range(-R,R+1),repeat=r)),dtype=float)
    if tau.imag>=.1:
        E=np.einsum('ni,ij,nj->n',grid,Q,grid)
        return np.exp(2j*np.pi*(tau*E+grid@b)).sum()
    y=grid-b
    E=np.einsum('ni,ij,nj->n',y,np.linalg.inv(2*Q),y)
    return (-1j*tau)**(-r/2)/np.sqrt(np.linalg.det(2*Q))*np.exp(-1j*np.pi*E/tau).sum()

if __name__=='__main__':
    Q=nx.laplacian_matrix(nx.complete_graph(4)).toarray()[:-1,:-1]
    tau=.17+.8j;b=[.25]*3
    f=gaussian(Q,b,tau)
    checks=[]
    for A,B,C,D in [(1,0,64,1),(1,0,128,1),(1,1,0,1)]:
        t=(A*tau+B)/(C*tau+D)
        lhs=gaussian(Q,b,t)
        jt=gaussian([[1]],[0],t)/gaussian([[1]],[0],tau)
        # det(Q)=16: its Kronecker character is 1 on the subgroup.
        rhs=jt**3*f
        err=float(abs(lhs-rhs)/max(1,abs(lhs),abs(rhs)))
        assert err<1e-10,err
        checks.append({'gamma':[A,B,C,D],'relative_error':err,'radius':20})
    G=nx.cycle_graph(4);G.add_edge(0,2)
    Q=nx.laplacian_matrix(G).toarray()[:-1,:-1]
    u=(3*tau+1)/(32*tau+11)
    lhs=gaussian(Q,[0]*3,u,40)
    jt=gaussian([[1]],[0],u,40)/gaussian([[1]],[0],tau,40)
    rhs=-jt**3*gaussian(Q,[0]*3,tau,40)  # (8/11)=-1; level is 32
    err=float(abs(lhs-rhs)/max(1,abs(lhs),abs(rhs)))
    assert err<1e-10,err
    checks.append({'graph':'diamond','gamma':[3,1,32,11],'kronecker_character':-1,'relative_error':err,'radius':40})
    Path(__file__).with_name('modular_numerical_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(checks)
