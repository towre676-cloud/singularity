"""Exact rational operator calculus recovered from Wilson/Forge task sections.

Constructive arithmetic over Q. No integral lattice or Lean proof is inferred.
"""
from fractions import Fraction as Q
from itertools import combinations


def matrix(rows):
    a=tuple(tuple(row) for row in rows)
    if not a or not a[0] or any(len(row)!=len(a[0]) for row in a):
        raise ValueError('nonempty rectangular matrix required')
    if any(type(x) not in (int,Q) for row in a for x in row):
        raise ValueError('exact integer or Fraction entries required')
    return tuple(tuple(map(Q,row)) for row in a)


def transpose(a):
    return tuple(zip(*a))


def identity(n):
    return tuple(tuple(Q(i==j) for j in range(n)) for i in range(n))


def multiply(a,b):
    if not a or not b or len(a[0])!=len(b):
        raise ValueError('matrix product dimension mismatch')
    return tuple(tuple(sum(x*y for x,y in zip(row,col)) for col in transpose(b)) for row in a)


def apply(a,v):
    if not a or len(a[0])!=len(v):raise ValueError('vector dimension mismatch')
    return tuple(sum(x*y for x,y in zip(row,v)) for row in a)


def rref(rows,columns=None):
    a=[list(map(Q,row)) for row in rows]
    n=len(a[0]) if a else columns
    if n is None:raise ValueError('empty system needs a column count')
    if any(len(row)!=n for row in a):raise ValueError('ragged system')
    pivots=[]
    for c in range(n):
        k=len(pivots);p=next((i for i in range(k,len(a)) if a[i][c]),None)
        if p is None:continue
        a[k],a[p]=a[p],a[k];v=a[k][c];a[k]=[x/v for x in a[k]]
        for i in range(len(a)):
            if i!=k:
                v=a[i][c];a[i]=[x-v*y for x,y in zip(a[i],a[k])]
        pivots.append(c)
    return tuple(tuple(row) for row in a),tuple(pivots)


def rank(a):return len(rref(a)[1])


def kernel(a):
    a=matrix(a);rr,piv=rref(a);n=len(a[0]);basis=[]
    for free in range(n):
        if free in piv:continue
        v=[Q(0)]*n;v[free]=Q(1)
        for i,c in enumerate(piv):v[c]=-rr[i][free]
        basis.append(tuple(v))
    return tuple(basis)


def solve(a,b):
    a=matrix(a);b=tuple(b)
    if len(a)!=len(b):raise ValueError('right-hand dimension mismatch')
    rr,piv=rref([list(row)+[x] for row,x in zip(a,b)]);n=len(a[0])
    if n in piv:return None
    v=[Q(0)]*n
    for i,c in enumerate(piv):v[c]=rr[i][-1]
    return tuple(v)


def inverse(a):
    a=matrix(a);n=len(a)
    if len(a[0])!=n:raise ValueError('square matrix required')
    cols=[solve(a,col) for col in transpose(identity(n))]
    if any(c is None for c in cols):raise ValueError('singular matrix')
    return transpose(cols)


def _columns(vectors):return transpose(vectors)


def _extend(vectors,n):
    out=list(vectors)
    for v in identity(n):
        if len(rref(out+[v])[1])>len(out):out.append(v)
    if len(out)!=n:raise ValueError('input vectors must be independent')
    return tuple(out)


def fitting_decomposition(operator):
    """Construct ker A^k ⊕ im A^k at the first stabilized rank, including k=0."""
    a=matrix(operator);n=len(a)
    if len(a[0])!=n:raise ValueError('square operator required')
    power=identity(n)
    for k in range(n+1):
        nxt=multiply(a,power)
        if rank(power)==rank(nxt):break
        power=nxt
    else:raise AssertionError('rank did not stabilize')
    nil=kernel(power);piv=rref(power)[1];cols=transpose(power)
    stable=tuple(cols[i] for i in piv);basis=_columns(nil+stable);inv=inverse(basis)
    d=len(nil);diag=tuple(tuple(Q(i==j and i<d) for j in range(n)) for i in range(n))
    projector=multiply(multiply(basis,diag),inv)
    block=multiply(multiply(inv,a),basis)
    if multiply(projector,projector)!=projector or multiply(a,projector)!=multiply(projector,a):
        raise AssertionError('invalid Fitting projector')
    return {'stabilization_index':k,'nilpotent_dimension':d,'stable_dimension':n-d,
            'basis':basis,'inverse_basis':inv,'operator_in_basis':block,
            'nilpotent_projector':projector,'stable_projector':tuple(tuple(Q(i==j)-projector[i][j] for j in range(n)) for i in range(n)),
            'kernel_free':rank(a)==n,'execution_verified':False,'field':'Q'}


def target_factor(observation,target):
    """Construct L with target=L observation, or a concrete invisible vector."""
    g,f=matrix(observation),matrix(target)
    if len(g[0])!=len(f[0]):raise ValueError('state dimension mismatch')
    for v in kernel(g):
        out=apply(f,v)
        if any(out):
            return {'status':'AMBIGUOUS','invisible_vector':v,'target_difference':out,
                    'execution_verified':False,'field':'Q'}
    decoder=tuple(solve(transpose(g),row) for row in f)
    if any(row is None for row in decoder) or multiply(decoder,g)!=f:
        raise AssertionError('factorization failure')
    return {'status':'EXACT_TARGET_FACTOR','decoder':decoder,'execution_verified':False,'field':'Q'}


def task_section(target,carrier,*,injective=False):
    """Solve carrier T=target; construct an injective lift when requested.

    Injection exists iff im(target)⊆im(carrier) and
    dim ker(target)≤dim ker(carrier). Rational result only.
    """
    f,g=matrix(target),matrix(carrier)
    if len(f)!=len(g):raise ValueError('common output dimension required')
    d,n=len(f[0]),len(g[0]);kf,kg=kernel(f),kernel(g)
    for j,col in enumerate(transpose(f)):
        if solve(g,col) is None:
            witness=next(v for v in kernel(transpose(g)) if sum(x*y for x,y in zip(v,col)))
            return {'status':'IMAGE_OBSTRUCTION','target_column':j,'left_annihilator':witness,
                    'nonzero_pairing':sum(x*y for x,y in zip(witness,col)),'field':'Q','execution_verified':False}
    if injective and len(kf)>len(kg):
        return {'status':'INJECTIVE_DIMENSION_OBSTRUCTION','target_kernel_dimension':len(kf),
                'carrier_kernel_dimension':len(kg),'field':'Q','execution_verified':False}
    if injective:
        domain=_extend(kf,d)
        lifts=kg[:len(kf)]+tuple(solve(g,apply(f,v)) for v in domain[len(kf):])
        t=multiply(_columns(lifts),inverse(_columns(domain)))
    else:t=_columns(tuple(solve(g,col) for col in transpose(f)))
    if multiply(g,t)!=f or (injective and rank(t)!=d):raise AssertionError('incorrect section')
    return {'status':'INJECTIVE_TASK_SECTION' if injective else 'TASK_SECTION','lift':t,
            'lift_rank':rank(t),'constructed_lift_integral':all(x.denominator==1 for row in t for x in row),
            'target_kernel_dimension':len(kf),'carrier_kernel_dimension':len(kg),
            'field':'Q','execution_verified':False}


def intertwiner_space(source,target,*,variable_limit=256):
    """All T satisfying T A_i=B_i T over Q, with all contexts simultaneous.

    Returns a basis of Hom, not an automatic isomorphism claim.
    """
    aa,bb=tuple(map(matrix,source)),tuple(map(matrix,target))
    if not aa or len(aa)!=len(bb):raise ValueError('matching nonempty contexts required')
    n,m=len(aa[0]),len(bb[0])
    if any(len(a)!=n or len(a[0])!=n for a in aa) or any(len(b)!=m or len(b[0])!=m for b in bb):
        raise ValueError('each family needs a fixed square dimension')
    if type(variable_limit) is not int or variable_limit<1 or n*m>variable_limit:
        raise ValueError('intertwiner variable budget exceeded')
    rows=[]
    for a,b in zip(aa,bb):
        for i in range(m):
            for j in range(n):
                row=[Q(0)]*(m*n)
                for k in range(n):row[i*n+k]+=a[k][j]
                for k in range(m):row[k*n+j]-=b[i][k]
                rows.append(row)
    basis=tuple(tuple(tuple(v[i*n+j] for j in range(n)) for i in range(m)) for v in kernel(rows))
    if any(multiply(t,a)!=multiply(b,t) for t in basis for a,b in zip(aa,bb)):
        raise AssertionError('invalid intertwiner')
    return {'dimension':len(basis),'basis':basis,'constraint_rank':rank(rows),
            'variables':m*n,'contexts':len(aa),'field':'Q','execution_verified':False}


def context_profile(contexts,*,subset_limit=1023):
    """Ranks of vertical stacks; rank equivalence is never transport equivalence."""
    items=tuple((name,matrix(a)) for name,a in contexts.items())
    if not items or len({name for name,a in items})!=len(items):raise ValueError('named contexts required')
    if any(len(a[0])!=len(items[0][1][0]) for name,a in items):raise ValueError('common source dimension required')
    if type(subset_limit) is not int or (1<<len(items))-1>subset_limit:
        raise ValueError('context subset budget exceeded')
    return [{'contexts':[items[i][0] for i in inds],
             'rank':rank(tuple(row for i in inds for row in items[i][1]))}
            for size in range(1,len(items)+1) for inds in combinations(range(len(items)),size)]


def injective_coordinates(carrier,vector):
    """Unique coordinates in a full-column-rank rational carrier, with integrality.

    A nonintegral unique coordinate rules out membership in this column lattice;
    this conclusion is not valid for a general noninjective carrier.
    """
    g=matrix(carrier);v=tuple(vector)
    if len(v)!=len(g) or any(type(x) not in (int,Q) for x in v):
        raise ValueError('matching exact vector required')
    if rank(g)!=len(g[0]):raise ValueError('injective carrier required')
    result=task_section(tuple((x,) for x in v),g)
    if result['status']=='IMAGE_OBSTRUCTION':return result
    coordinates=tuple(row[0] for row in result['lift'])
    integral=all(x.denominator==1 for x in coordinates)
    return {'status':'INTEGRAL_COORDINATES' if integral else 'NONINTEGRAL_COORDINATES',
            'coordinates':coordinates,'unique':True,'field':'Q','execution_verified':False,
            'integral_column_lattice_member':integral}
