"""All-future identities of explicitly defined recurrences via reachable states.

An exact invariant-subspace calculation, not an OEIS definition proof.
"""
from .exact_linear import matrix,apply,rank,solve,transpose
from .recurrence import Recurrence
from fractions import Fraction as Q


def companion(recurrence):
    if not isinstance(recurrence,Recurrence):raise ValueError('Recurrence required')
    r=len(recurrence.coefficients)
    return tuple(tuple(Q(j==i+1) for j in range(r)) for i in range(r-1))+(tuple(map(Q,recurrence.coefficients)),)


def orbit_identity(operator,seed,readout):
    """Find the first nonzero output or a basis proving zero for all n≥0.

    At the first dependent orbit vector, the previous Krylov span is invariant.
    The closure coordinates supply an independently replayable witness.
    """
    a=matrix(operator);n=len(a)
    if len(a[0])!=n:raise ValueError('square operator required')
    seed,readout=tuple(seed),tuple(readout)
    if len(seed)!=n or len(readout)!=n or any(type(x) not in (int,Q) for x in seed+readout):
        raise ValueError('matching exact seed and readout required')
    vectors=[];v=tuple(map(Q,seed));h=tuple(map(Q,readout))
    for k in range(n+1):
        value=sum(x*y for x,y in zip(h,v))
        if value:
            return {'status':'NONZERO_DEFINED_ORBIT','first_index':k,'value':value,
                    'field':'Q','execution_verified':False}
        if not any(v) or (vectors and rank(vectors+[v])==len(vectors)):
            closure=solve(transpose(vectors),v) if vectors else ()
            if closure is None:raise AssertionError('missing Krylov closure')
            return {'status':'ZERO_FOR_ALL_NONNEGATIVE_INDICES','reachable_dimension':len(vectors),
                    'orbit_basis':tuple(vectors),'closure_coefficients':closure,
                    'field':'Q','execution_verified':False,'definition_scope':'supplied operator, seed and readout'}
        vectors.append(v);v=apply(a,v)
    raise AssertionError('Krylov closure failed')


def compare_recurrences(left,right):
    a,b=companion(left),companion(right);r,s=len(a),len(b)
    op=tuple(tuple(a[i][j] if i<r and j<r else b[i-r][j-r] if i>=r and j>=r else Q(0)
                   for j in range(r+s)) for i in range(r+s))
    h=tuple(Q(1 if j==0 else -1 if j==r else 0) for j in range(r+s))
    result=orbit_identity(op,left.initial+right.initial,h)
    result['definition_scope']='the two supplied exact recurrence definitions; n>=0'
    return result
