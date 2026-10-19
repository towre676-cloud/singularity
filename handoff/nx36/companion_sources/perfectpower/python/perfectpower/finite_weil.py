"""The recovered pair F[x,y]=zeta_N**(xy), T[x,x]=zeta_N**(x*x).

F is unnormalized; scalar normalization does not change its commutant.
The even-level chirp uses zeta_N, not zeta_(2N). Computations are exact in
Q[zeta_N]. No general prime-power dimension or modular-group theorem follows.
"""
from math import gcd
from .branched_geometry import cyclotomic
from .quotient_algebra import QuotientAlgebra
from .divisor_square import WorkLimit


def _level(n, maximum):
    if type(n) is not int or not 2<=n<=maximum:
        raise ValueError(f'level must be an integer in [2,{maximum}]')


def _nonzero(e):return any(e.coefficients)


def roots(n):
    _level(n,64);field=QuotientAlgebra(tuple(cyclotomic(n)));z=field.element((0,1))
    phases=tuple(z**j for j in range(n))
    if z**n!=field.element(1):raise AssertionError('root order replay failed')
    return field,phases


def _kernel(rows, columns, field, work_limit):
    a=[list(row) for row in rows];piv=[];operations=0
    for c in range(columns):
        k=len(piv);p=next((i for i in range(k,len(a)) if _nonzero(a[i][c])),None)
        if p is None:continue
        a[k],a[p]=a[p],a[k];inv=a[k][c].inverse()
        a[k]=[x*inv for x in a[k]];operations+=columns
        if operations>work_limit:raise WorkLimit('complete cyclotomic reduction exceeds work limit')
        for i in range(len(a)):
            if i!=k and _nonzero(a[i][c]):
                factor=a[i][c];a[i]=[x-factor*y for x,y in zip(a[i],a[k])];operations+=2*columns
                if operations>work_limit:raise WorkLimit('complete cyclotomic reduction exceeds work limit')
        piv.append(c)
    basis=[]
    for free in range(columns):
        if free not in piv:
            v=[field.element(0)]*columns;v[free]=field.element(1)
            for i,c in enumerate(piv):v[c]=-a[i][free]
            basis.append(tuple(v))
    return tuple(basis),tuple(piv),operations


def commutant(level, *, work_limit=200_000):
    _level(level,9)
    if type(work_limit) is not int or work_limit<1:raise ValueError('positive integer work limit required')
    n=level;field,phases=roots(n);zero=field.element(0)
    pairs=tuple((a,b) for a in range(n) for b in range(n) if (a*a-b*b)%n==0)
    rows=[]
    for i in range(n):
        for j in range(n):
            rows.append(tuple((phases[b*j%n] if a==i else zero)-(phases[i*a%n] if b==j else zero) for a,b in pairs))
    vectors,pivots,operations=_kernel(rows,len(pairs),field,work_limit)
    basis=[]
    for v in vectors:
        c=[[zero]*n for _ in range(n)]
        for (i,j),x in zip(pairs,v):c[i][j]=x
        for i in range(n):
            for j in range(n):
                left=sum_field((c[i][k]*phases[k*j%n] for k in range(n)),zero)
                right=sum_field((phases[i*k%n]*c[k][j] for k in range(n)),zero)
                if left!=right or c[i][j]*phases[j*j%n]!=phases[i*i%n]*c[i][j]:
                    raise AssertionError('commutant basis failed exact replay')
        basis.append(tuple(tuple(row) for row in c))
    return {'level':n,'dimension':len(basis),'basis':tuple(basis),
            'allowed_entries':pairs,'equation_rank':len(pivots),'field_entry_operations':operations,
            'field_modulus':field.modulus,'complete_over_cyclotomic_field':True,
            'exact_replay':True,'execution_verified':False,
            'scope':'computed finite level; not a general dimension theorem',
            'convention':'unnormalized F_N; T_N uses zeta_N at even and odd levels'}


def sum_field(values,zero):
    out=zero
    for x in values:out=out+x
    return out


def heisenberg_replay(level):
    _level(level,64);n=level;field,phases=roots(n);zero=field.element(0)
    # ZX = zeta XZ. Distinct clock eigenvalues force a commuting matrix to
    # be diagonal, and commuting with the cyclic shift forces constant diagonal.
    if len(set(phases))!=n:raise AssertionError('clock eigenvalues not distinct')
    for j in range(n):
        if phases[(j+1)%n]!=phases[1]*phases[j]:raise AssertionError('clock/shift relation failed')
    # F^2 = n parity, checked through cyclotomic sums, not approximate roots.
    for i in range(n):
        for j in range(n):
            actual=sum_field((phases[k*(i+j)%n] for k in range(n)),zero)
            expected=field.element(n if (i+j)%n==0 else 0)
            if actual!=expected:raise AssertionError('Fourier square identity failed')
    return {'level':n,'clock_shift_commutant_dimension':1,'fourier_square':'N times parity',
            'exact_replay':True,'execution_verified':False}


def crt_replay(a,b):
    _level(a,64);_level(b,64)
    if gcd(a,b)!=1 or a*b>64:raise ValueError('coprime factors and product at most 64 required')
    m=a*b;labels=[(x,y) for x in range(a) for y in range(b)]
    section=[(b*x+a*y)%m for x,y in labels]
    if sorted(section)!=list(range(m)):raise AssertionError('scaled CRT section is not bijective')
    for (x,y),i in zip(labels,section):
        if (i*i-(b*b*x*x+a*a*y*y))%m:raise AssertionError('CRT chirp phase failed')
        for (u,v),j in zip(labels,section):
            if (i*j-(b*b*x*u+a*a*y*v))%m:raise AssertionError('CRT Fourier phase failed')
    return {'factors':[a,b],'level':m,'scaled_section':section,'phase_checks':m*m+m,
            'fourier_twists':[b%a,a%b],'chirp_twists':[b%a,a%b],
            'identity':'F_ab = F_a^(b) tensor F_b^(a) under x=b*u+a*v; same twists for T',
            'exact_replay':True,'execution_verified':False}


def degeneracy_replay(small,large):
    _level(small,32);_level(large,32)
    if large%small:raise ValueError('large level must be divisible by small level')
    l,m=small,large;d=m//l;field,phases=roots(m);zero=field.element(0);checks=0
    for j in range(m):
        for k in range(l):
            # F_M I = R F_L, and F_M R = d I F_L.
            if phases[j*d*k%m]!=phases[d*(j%l)*k%m]:raise AssertionError('first degeneracy identity failed')
            actual=sum_field((phases[j*(k+t*l)%m] for t in range(d)),zero)
            expected=phases[d*(j//d)*k%m]*d if j%d==0 else zero
            if actual!=expected:raise AssertionError('second degeneracy identity failed')
            if j==d*k and phases[j*j%m]!=phases[d*d*k*k%m]:raise AssertionError('chirp restriction failed')
            checks+=2
    return {'small_level':l,'large_level':m,'degree':d,'fourier_entry_checks':checks,
            'identities':['F_M I = R F_L','F_M R = d I F_L','T_M I = I T_L^d'],
            'exact_replay':True,'execution_verified':False}
