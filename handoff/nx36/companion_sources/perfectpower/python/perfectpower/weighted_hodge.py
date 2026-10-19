"""Exact finite weighted Hodge geometry; positive rational metrics only.

The mass matrices are supplied data, not inferred conformal metrics. Every
returned projector is checked algebraically; no floating tolerance is used.
"""
from fractions import Fraction as Q
from . import exact_linear as E


def add(a, b, sign=1):
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        raise ValueError('matrix dimension mismatch')
    return tuple(tuple(x+sign*y for x,y in zip(r,s)) for r,s in zip(a,b))


def metric(rows, size=None):
    m=E.matrix(rows); n=len(m)
    if n>64 or len(m[0])!=n or (size is not None and n!=size):
        raise ValueError('square metric of matching dimension, at most 64, required')
    if m!=E.transpose(m):raise ValueError('metric must be symmetric')
    # LDL elimination: positive pivots are equivalent to positive definiteness.
    a=[list(row) for row in m]
    for k in range(n):
        if a[k][k]<=0:raise ValueError('metric must be positive definite')
        for i in range(k+1,n):
            for j in range(i,n):
                a[i][j]-=a[i][k]*a[k][j]/a[k][k]
                a[j][i]=a[i][j]
    return m


def _inverse(a):
    # One augmented reduction, rather than one independent solve per column.
    n=len(a); rr,piv=E.rref([list(r)+list(s) for r,s in zip(a,E.identity(n))])
    if piv!=tuple(range(n)):raise ValueError('singular matrix')
    return tuple(row[n:] for row in rr)


def weighted_adjoint(operator, domain_metric, codomain_metric):
    d=E.matrix(operator); mx=metric(domain_metric,len(d[0])); my=metric(codomain_metric,len(d))
    return E.multiply(E.multiply(_inverse(mx),E.transpose(d)),my)


def image_projector(operator, mass):
    a=E.matrix(operator); m=metric(mass,len(a)); n=len(a)
    if len(a[0])>64:raise ValueError('at most 64 generator columns required')
    piv=E.rref(a)[1]
    if not piv:return tuple((Q(0),)*n for _ in range(n))
    c=tuple(tuple(row[j] for j in piv) for row in a)
    ct_m=E.multiply(E.transpose(c),m)
    p=E.multiply(E.multiply(c,_inverse(E.multiply(ct_m,c))),ct_m)
    if E.multiply(p,p)!=p or E.multiply(E.transpose(p),m)!=E.multiply(m,p):
        raise AssertionError('weighted projector failed exact replay')
    return p


def constraint_projector(operator, domain_metric):
    d=E.matrix(operator); m=metric(domain_metric,len(d[0])); n=len(m)
    normal=E.multiply(_inverse(m),E.transpose(d))
    p=add(E.identity(n),image_projector(normal,m),-1)
    if any(x for row in E.multiply(d,p) for x in row):
        raise AssertionError('constraint projector does not land in the kernel')
    return p


def regularized_constraint(operator, domain_metric, codomain_metric, epsilon):
    if type(epsilon) not in (int,Q) or epsilon<=0:
        raise ValueError('positive exact regularization required')
    d=E.matrix(operator); adj=weighted_adjoint(d,domain_metric,codomain_metric)
    eps=tuple(tuple(Q(epsilon) if i==j else Q(0) for j in range(len(d))) for i in range(len(d)))
    normal=E.multiply(E.multiply(adj,_inverse(add(E.multiply(d,adj),eps))),d)
    return add(E.identity(len(d[0])),normal,-1)


def weighted_hodge(boundary1, boundary2, mass0, mass1, mass2):
    b1,b2=E.matrix(boundary1),E.matrix(boundary2)
    m0,m1,m2=metric(mass0,len(b1)),metric(mass1,len(b1[0])),metric(mass2,len(b2[0]))
    if len(b2)!=len(m1) or any(x for row in E.multiply(b1,b2) for x in row):
        raise ValueError('a matching chain with boundary1 boundary2 = 0 is required')
    a1=weighted_adjoint(b1,m1,m0); a2=weighted_adjoint(b2,m2,m1)
    lap=add(E.multiply(a1,b1),E.multiply(b2,a2))
    grad=image_projector(a1,m1); boundary=image_projector(b2,m1)
    harmonic=add(add(E.identity(len(m1)),grad,-1),boundary,-1)
    projectors=(grad,boundary,harmonic)
    for i,p in enumerate(projectors):
        if E.multiply(p,p)!=p or E.multiply(E.transpose(p),m1)!=E.multiply(m1,p):
            raise AssertionError('Hodge projector identity failed')
        for j,r in enumerate(projectors):
            if i!=j and any(x for row in E.multiply(p,r) for x in row):
                raise AssertionError('Hodge components are not orthogonal')
    if any(x for row in E.multiply(lap,harmonic) for x in row):
        raise AssertionError('harmonic component not killed by Laplacian')
    dims=(E.rank(b1),E.rank(b2),len(m1)-E.rank(b1)-E.rank(b2))
    return {'gradient_projector':grad,'boundary_projector':boundary,
            'harmonic_projector':harmonic,'laplacian':lap,'dimensions':dims,
            'field':'Q','exact_replay':True,'execution_verified':False,
            'scope':'finite chain with supplied positive rational mass matrices'}
