"""Integral presentation invariants and exact lattice membership.

Determinantal divisors give Smith factors without rational-nullspace artifacts.
Small-matrix exhaustive minors have a hard budget; no maximal-order claim.
"""
from fractions import Fraction
from itertools import combinations
from math import gcd, comb, lcm
from .quotient_algebra import determinant


class MinorLimit(ValueError):
    """All requested minors were not computed; no certificate is returned."""


def _matrix(matrix):
    a=tuple(tuple(row) for row in matrix)
    if not a or not a[0] or any(len(row)!=len(a[0]) for row in a):
        raise ValueError('nonempty rectangular matrix required')
    if any(type(x) is not int for row in a for x in row):
        raise ValueError('integer presentation entries required')
    return a


def smith_invariants(matrix, *, minor_limit=100_000):
    """Cokernel Z^m / columns(A), with δ_k=gcd of all k-minors.

    δ_0=1; factors are δ_k/δ_(k-1). No unimodular change matrices
    are claimed. The computed free rank is m-rank(A).
    """
    a=_matrix(matrix);m,n=len(a),len(a[0])
    if type(minor_limit) is not int or minor_limit<1:
        raise ValueError('positive minor budget required')
    divisors=[1];trials=0
    for k in range(1,min(m,n)+1):
        count=comb(m,k)*comb(n,k)
        if trials+count>minor_limit:
            raise MinorLimit('minor budget exceeded; no invariant certificate')
        d=0
        for rows in combinations(range(m),k):
            for cols in combinations(range(n),k):
                value=determinant([[a[i][j] for j in cols] for i in rows])
                if value.denominator != 1:
                    raise AssertionError('nonintegral integer determinant')
                d=gcd(d,abs(int(value)));trials+=1
        if d==0:
            break
        divisors.append(d)
    factors=[divisors[i]//divisors[i-1] for i in range(1,len(divisors))]
    if any(divisors[i]%divisors[i-1] for i in range(1,len(divisors))):
        raise AssertionError('invalid determinantal chain')
    if any(y%x for x,y in zip(factors,factors[1:])):
        raise AssertionError('invalid Smith divisibility chain')
    return {'rank':len(factors),'free_rank':m-len(factors),
            'determinantal_divisors':divisors,'smith_factors':factors,
            'torsion_factors':[d for d in factors if d>1],
            'torsion_order':divisors[-1], 'minors_tested':trials,
            'execution_verified':False}


def lattice_membership(matrix, vector, *, minor_limit=100_000):
    """Exact membership for arbitrary integral generating columns.

    Adding b must preserve rational span and the top determinantal divisor.
    Both lattices then have the same index in their common saturation.
    """
    a=_matrix(matrix);b=tuple(vector)
    if len(b)!=len(a) or any(type(x) is not int for x in b):
        raise ValueError('matching integer vector required')
    before=smith_invariants(a,minor_limit=minor_limit)
    after=smith_invariants([list(row)+[x] for row,x in zip(a,b)],minor_limit=minor_limit)
    same_rank=before['rank']==after['rank']
    member=same_rank and before['torsion_order']==after['torsion_order']
    return {'member':member,'same_rational_span':same_rank,
            'before':before,'augmented':after,'execution_verified':False}


def inverse_lattice_conditions(matrix):
    """Full-rank square column lattice: exact congruence rows of A^-1.

    Each condition is (row·b) ≡ 0 mod denominator. The row and denominator
    are reduced together, so prime-power depth is preserved.
    """
    a=_matrix(matrix);n=len(a)
    if len(a[0])!=n:
        raise ValueError('square basis required')
    aug=[[Fraction(x) for x in row]+[Fraction(i==j) for j in range(n)]
         for i,row in enumerate(a)]
    for k in range(n):
        pivot=next((i for i in range(k,n) if aug[i][k]),None)
        if pivot is None:
            raise ValueError('nonsingular basis required')
        aug[k],aug[pivot]=aug[pivot],aug[k]
        scale=aug[k][k];aug[k]=[x/scale for x in aug[k]]
        for i in range(n):
            if i!=k:
                scale=aug[i][k]
                aug[i]=[x-scale*y for x,y in zip(aug[i],aug[k])]
    conditions=[]
    for row in aug:
        inv=row[n:];d=lcm(*(x.denominator for x in inv))
        nums=[int(x*d) for x in inv]
        common=gcd(d,gcd(*nums))
        conditions.append({'row':[x//common for x in nums],'modulus':d//common})
    return conditions


def basis_pullback(matrix, vector):
    a=_matrix(matrix);b=tuple(vector)
    if len(b)!=len(a) or any(type(x) is not int for x in b):
        raise ValueError('matching integer vector required')
    conditions=inverse_lattice_conditions(a)
    values=[sum(x*y for x,y in zip(c['row'],b)) for c in conditions]
    failures=[{'row':c['row'],'modulus':c['modulus'],'residue':v%c['modulus']}
              for c,v in zip(conditions,values) if v%c['modulus']]
    return {'member':not failures,
            'coordinates':None if failures else [v//c['modulus'] for c,v in zip(conditions,values)],
            'obstructions':failures,'execution_verified':False}


def local_torsion_profile(matrix,p,*,minor_limit=100_000):
    """Prime-power lengths, rather than just rank loss modulo p."""
    from .local_quartic import _prime
    if not _prime(p):raise ValueError('prime required')
    result=smith_invariants(matrix,minor_limit=minor_limit)
    lengths=[]
    for d in result['smith_factors']:
        v=0
        while d%p==0:d//=p;v+=1
        if v:lengths.append(v)
    return {'prime':p,'torsion_lengths':lengths,
            'torsion_length_sum':sum(lengths),
            'rank_mod_prime':result['rank']-len(lengths),
            'free_rank':result['free_rank'],'execution_verified':False}
