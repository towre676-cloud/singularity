"""Small exact algebra used by optional target applications; no numerical solver.

The box estimator enumerates independent row supports.  A weighted l1 optimum
has such a support (a basic solution of its split-variable linear program).
"""
from fractions import Fraction as Q
from itertools import combinations, product


def rational(x):
    if isinstance(x, bool) or not isinstance(x, (int, Q)):
        raise TypeError("use int or Fraction for exact arithmetic")
    return Q(x)


def vector(v):
    return tuple(map(rational, v))


def matrix(a, columns=None):
    a = tuple(map(vector, a))
    n = len(a[0]) if a and columns is None else (columns or 0)
    if any(len(r) != n for r in a):
        raise ValueError("ragged matrix")
    return a


def dot(a,b):
    if len(a) != len(b): raise ValueError("dimension mismatch")
    return sum((x*y for x,y in zip(a,b)), Q())


def transpose(a, columns=None):
    a=matrix(a,columns)
    n=len(a[0]) if a else (columns or 0)
    return tuple(tuple(r[j] for r in a) for j in range(n))


def identity(n):
    return tuple(tuple(Q(i==j) for j in range(n)) for i in range(n))


def multiply(a,b):
    a,b=matrix(a),matrix(b)
    if not a or not b: raise ValueError("empty product is ambiguous")
    if len(a[0])!=len(b):raise ValueError("dimension mismatch")
    return tuple(tuple(dot(r,c) for c in transpose(b)) for r in a)


def apply(a,v):return tuple(dot(r,v) for r in a)


def subtract(a,b):
    if len(a)!=len(b) or any(len(x)!=len(y) for x,y in zip(a,b)):raise ValueError("dimension mismatch")
    return tuple(tuple(x-y for x,y in zip(r,s)) for r,s in zip(a,b))


def rref(a, columns=None):
    a=[list(r) for r in matrix(a,columns)]; n=len(a[0]) if a else (columns or 0)
    piv=[]; k=0
    for j in range(n):
        p=next((i for i in range(k,len(a)) if a[i][j]),None)
        if p is None:continue
        a[k],a[p]=a[p],a[k]; c=a[k][j];a[k]=[x/c for x in a[k]]
        for i in range(len(a)):
            if i!=k:
                c=a[i][j];a[i]=[x-c*y for x,y in zip(a[i],a[k])]
        piv.append(j);k+=1
        if k==len(a):break
    return tuple(map(tuple,a)),tuple(piv)


def solve(a,b,variables=None):
    a=matrix(a,variables);b=vector(b)
    if len(a)!=len(b):raise ValueError("dimension mismatch")
    n=len(a[0]) if a else (variables or 0)
    rr,piv=rref([r+(v,) for r,v in zip(a,b)],n+1)
    if n in piv:return None
    out=[Q()]*n
    for r,p in zip(rr,piv):out[p]=r[-1]
    return tuple(out)


def nullspace(a,columns=None):
    a=matrix(a,columns);n=len(a[0]) if a else (columns or 0)
    rr,piv=rref(a,n);out=[]
    for j in range(n):
        if j in piv:continue
        v=[Q()]*n;v[j]=Q(1)
        for r,p in zip(rr,piv):v[p]=-r[j]
        out.append(tuple(v))
    return tuple(out)


def row_factorization(h,g,basis=None):
    h,g=matrix(h),matrix(g)
    if not g:raise ValueError("at least one target row required")
    n=len(g[0])
    if any(len(r)!=n for r in h):raise ValueError("dimension mismatch")
    z=identity(n) if basis is None else matrix(basis)
    if len(z)!=n:raise ValueError("basis has wrong ambient dimension")
    hz=multiply(h,z) if h else ()
    gz=multiply(g,z)
    out=[]
    for r in gz:
        v=solve(transpose(hz,len(z[0])),r,len(h))
        if v is None:return None
        out.append(v)
    return tuple(out)


def null_witness(h,g,basis=None):
    h,g=matrix(h),matrix(g);n=len(g[0])
    z=identity(n) if basis is None else matrix(basis)
    hz=multiply(h,z) if h else ()
    for v in nullspace(hz,len(z[0])):
        x=apply(z,v)
        if any(dot(r,x) for r in g):return x
    return None


def box_estimator(h,target,radii,max_supports=100000):
    """Globally minimum deterministic box error for a scalar linear target.

    Returns (weights, radius), or None when the target is not in the row span.
    Does not use bounded state bias to trade exact recovery for approximation.
    """
    h=matrix(h,len(target));target=vector(target);radii=vector(radii)
    if len(h)!=len(radii) or any(e<0 for e in radii):raise ValueError("bad radii")
    if len(h)>12 or len(target)>16:raise ValueError("application work budget")
    if not any(target):return (tuple(Q() for _ in h),Q())
    best=None;count=0
    for k in range(1,min(len(h),len(target))+1):
        for ix in combinations(range(len(h)),k):
            count+=1
            if count>max_supports:raise ValueError("support work budget")
            rows=tuple(h[i] for i in ix)
            if len(rref(rows)[1])!=k:continue
            w=solve(transpose(rows),target,k)
            if w is None:continue
            full=tuple(w[ix.index(i)] if i in ix else Q() for i in range(len(h)))
            radius=sum((abs(a)*e for a,e in zip(full,radii)),Q())
            candidate=(radius,full)
            if best is None or candidate<best:best=candidate
    return None if best is None else (best[1],best[0])


def box_vertices(center,radii):
    center,radii=vector(center),vector(radii)
    if len(center)!=len(radii) or any(r<0 for r in radii):raise ValueError("invalid box")
    if len(center)>16:raise ValueError("box vertex budget")
    return tuple(tuple(c+s*r for c,r,s in zip(center,radii,signs)) for signs in product((-1,1),repeat=len(center)))


def json_exact(x):
    if isinstance(x,Q):return str(x)
    if isinstance(x,dict):return {str(k):json_exact(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [json_exact(v) for v in x]
    return x
