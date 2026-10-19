"""Corrected energy identities, reduction defects, and decision margins."""
from fractions import Fraction as Q
from .exact import matrix,matmul,transpose


def vdot(a,b):
    if len(a)!=len(b):raise ValueError("vector sizes differ")
    return sum((Q(x)*Q(y) for x,y in zip(a,b)),Q(0))


def mv(a,v):
    if a and len(a[0])!=len(v):raise ValueError("matrix/vector sizes differ")
    return [vdot(row,v) for row in a]


def energy_balance(a,m,u,forcing=None):
    """For constant SPD M and u'=Au+f. SPD is a caller assumption, checked via LDL pivots."""
    a,m=matrix(a),matrix(m);u=list(map(Q,u));n=len(u)
    if len(a)!=n or len(m)!=n or any(len(row)!=n for row in a+m):
        raise ValueError("incompatible system shapes")
    if transpose(m)!=m:raise ValueError("mass matrix must be symmetric")
    work=[row[:] for row in m]
    for k in range(n):
        pivot=work[k][k]
        if pivot<=0:raise ValueError("mass matrix must be positive definite")
        for i in range(k+1,n):
            for j in range(k+1,n):work[i][j]-=work[i][k]*work[k][j]/pivot
    forcing=list(map(Q,forcing if forcing is not None else [0]*n))
    if len(forcing)!=n:raise ValueError("forcing dimension differs")
    mass=vdot(u,mv(m,u))
    if mass==0:raise ValueError("nonzero state required")
    ma,atm=matmul(m,a),matmul(transpose(a),m)
    symmetric=[[Q(1,2)*(x+y) for x,y in zip(r,s)] for r,s in zip(ma,atm)]
    drain=vdot(u,mv(symmetric,u));source=vdot(u,mv(m,forcing))
    lam=-2*drain/mass;zeta=2*source/mass
    return {"energy":mass/2,"energy_derivative":drain+source,
            "lambda":lam,"zeta":zeta,"log_energy_derivative":-lam+zeta,
            "rho":None if lam==0 else 1-zeta/lam}


def reduction_defect(a,b,v,g,h):
    a,b,v,g,h=map(matrix,(a,b,v,g,h))
    av,vg=matmul(a,v),matmul(v,g);vh=matmul(v,h)
    if len(b)!=len(vh) or len(b[0])!=len(vh[0]):raise ValueError("input dimensions differ")
    return [[x-y for x,y in zip(r,s)] for r,s in zip(av,vg)],[[x-y for x,y in zip(r,s)] for r,s in zip(b,vh)]


def contraction_error(gamma,initial,defects):
    gamma,initial=Q(gamma),Q(initial)
    if not 0<=gamma<1 or initial<0 or any(Q(x)<0 for x in defects):
        raise ValueError("need contracting gamma and nonnegative bounds")
    out=initial
    for d in defects:out=gamma*out+Q(d)
    return out


def certified_best(estimates,errors):
    if len(estimates)!=len(errors) or not estimates:raise ValueError("matching nonempty values required")
    if any(Q(e)<0 for e in errors):raise ValueError("negative error bound")
    low=[Q(v)-Q(e) for v,e in zip(estimates,errors)]
    high=[Q(v)+Q(e) for v,e in zip(estimates,errors)]
    winners=[i for i in range(len(low)) if all(low[i]>high[j] for j in range(len(low)) if j!=i)]
    return winners[0] if winners else None
