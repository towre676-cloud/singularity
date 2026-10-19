"""Exact dimensions: rational commuting operators plus a finite-field rank minor.

No numerical tolerance is used. A nonzero modular minor bounds the cyclotomic
kernel from above; independently checked rational operators bound it from below.
"""
from functools import lru_cache
from math import gcd,isqrt
from .branched_geometry import cyclotomic
from .finite_weil import crt_replay
from .divisor_square import WorkLimit


def _level(n,maximum=64):
    if type(n) is not int or not 2 <= n <= maximum:
        raise ValueError(f'level must be an integer between 2 and {maximum}')


def _prime(p):
    return type(p) is int and p>=2 and all(p%d for d in range(2,isqrt(p)+1))


def _factors(n):
    return [p for p in range(2,n+1) if n%p==0 and _prime(p)]


def _specialization(n):
    q=n+1
    while not _prime(q):q+=n
    for z in range(2,q):
        if pow(z,n,q)==1 and all(pow(z,n//p,q)!=1 for p in _factors(n)):
            return q,z
    raise AssertionError('prime field lacks requested root')


def _identity(n):return tuple(tuple(int(i==j) for j in range(n)) for i in range(n))
def _parity(n):return tuple(tuple(int(i==(-j)%n) for j in range(n)) for i in range(n))
def _mul(a,b):
    n=len(a)
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(n)) for j in range(n)) for i in range(n))


def _independent(candidates,q):
    pivots={};chosen=[]
    for a in candidates:
        v={i:x%q for i,x in enumerate(x for row in a for x in row) if x%q}
        while v:
            p=min(v)
            if p not in pivots:
                inv=pow(v[p],-1,q);pivots[p]={i:x*inv%q for i,x in v.items()};chosen.append(a);break
            scale=v[p]
            for i,x in pivots[p].items():
                value=(v.get(i,0)-scale*x)%q
                if value:v[i]=value
                else:v.pop(i,None)
    return tuple(chosen)


def _tensor(a,b):
    m,n=len(a),len(b);N=m*n;out=[[0]*N for _ in range(N)]
    section=[(n*x+m*y)%N for x in range(m) for y in range(n)]
    for x in range(m):
        for y in range(n):
            for u in range(m):
                for v in range(n):out[section[x*n+y]][section[u*n+v]]=a[x][u]*b[y][v]
    return tuple(map(tuple,out))


@lru_cache(maxsize=64)
def _basis(n):
    if n==1:return (_identity(1),)
    q,_=_specialization(n)
    # Coprime tensor bases are rational and therefore unchanged by Galois twists.
    split=next(((d,n//d) for d in range(2,n) if n%d==0 and gcd(d,n//d)==1),None)
    if split:
        a,b=split
        return tuple(_tensor(x,y) for x in _basis(a) for y in _basis(b))
    candidates=[_identity(n),_parity(n)]
    if n%4==0:
        shift=tuple(tuple(int(i==(j+n//2)%n) for j in range(n)) for i in range(n))
        clock=tuple(tuple((-1)**i if i==j else 0 for j in range(n)) for i in range(n))
        plus=tuple(tuple(shift[i][j]+clock[i][j] for j in range(n)) for i in range(n))
        both=_mul(shift,clock)
        candidates.extend([plus,both,_mul(_parity(n),plus),_mul(_parity(n),both)])
    # The old-level embedding has support d|x and is constant on fibres x/d mod m.
    for d in range(2,isqrt(n)+1):
        if n%(d*d):continue
        m=n//(d*d)
        for c in _basis(m):
            candidates.append(tuple(tuple(c[(x//d)%m][(y//d)%m] if x%d==0 and y%d==0 else 0 for y in range(n)) for x in range(n)))
    return _independent(candidates,q)


def _allowed(n):return [(a,b) for a in range(n) for b in range(n) if (a*a-b*b)%n==0]

def _row(n,phases,pairs,i,j,q):
    return [( (phases[b*j%n] if a==i else 0)-(phases[i*a%n] if b==j else 0))%q for a,b in pairs]


def _minor(n,q,z,target,work_limit):
    pairs=_allowed(n);phases=[pow(z,k,q) for k in range(n)];pivots={};rows=[];cols=[];work=0
    for i in range(n):
        for j in range(n):
            v={k:x for k,x in enumerate(_row(n,phases,pairs,i,j,q)) if x}
            while v:
                p=min(v)
                if p not in pivots:
                    inv=pow(v[p],-1,q);pivots[p]={k:x*inv%q for k,x in v.items()};rows.append([i,j]);cols.append(p);break
                scale=v[p];work+=len(pivots[p])
                if work>work_limit:raise WorkLimit('exact modular rank exceeds work limit')
                for k,x in pivots[p].items():
                    value=(v.get(k,0)-scale*x)%q
                    if value:v[k]=value
                    else:v.pop(k,None)
            if len(rows)==target:return rows,cols,work
    raise ValueError('constructed commuting operators do not close the dimension bound')


def _remainder(poly,modulus):
    p=list(poly);degree=len(modulus)-1
    for k in range(len(p)-1,degree-1,-1):
        coefficient=p[k]
        if coefficient:
            for j in range(degree+1):p[k-degree+j]-=coefficient*modulus[j]
    return p[:degree]


def _check_basis(n,basis):
    modulus=tuple(cyclotomic(n))
    for a in basis:
        if len(a)!=n or any(len(row)!=n for row in a):return False
        if any(type(x) is not int for row in a for x in row):return False
        for i in range(n):
            for j in range(n):
                if a[i][j] and (i*i-j*j)%n:return False
                coefficients=[0]*n
                for k in range(n):
                    coefficients[k*j%n]+=a[i][k]
                    coefficients[i*k%n]-=a[k][j]
                if any(_remainder(coefficients,modulus)):return False
    return True


def _det_mod(a,q):
    """Independent dense determinant replay of the selected original-equation minor."""
    # Optional integer-array acceleration; every product is below 10^10.
    # This is exact modular elimination, with no floating-point linear algebra.
    if len(a)>=96 and 2<=q<=100000:
        try:
            import numpy as np
        except ImportError:
            pass
        else:
            a=np.array([[int(x)%q for x in row] for row in a],dtype=np.int64)
            det=1;n=len(a)
            for k in range(n):
                candidates=np.flatnonzero(a[k:,k])
                if not len(candidates):return 0
                pivot=k+int(candidates[0])
                if pivot!=k:a[[k,pivot]]=a[[pivot,k]];det=-det
                value=int(a[k,k]);det=det*value%q;inv=pow(value,-1,q)
                factors=(a[k+1:,k]*inv)%q
                a[k+1:,k+1:]=(a[k+1:,k+1:]-factors[:,None]*a[k,k+1:][None,:])%q
                a[k+1:,k]=0
            return det%q
    a=[list(row) for row in a];det=1;n=len(a)
    for k in range(n):
        pivot=next((i for i in range(k,n) if a[i][k]%q),None)
        if pivot is None:return 0
        if pivot!=k:a[k],a[pivot]=a[pivot],a[k];det=-det
        value=a[k][k]%q;det=det*value%q;inv=pow(value,-1,q)
        for i in range(k+1,n):
            factor=a[i][k]*inv%q
            if factor:
                for j in range(k+1,n):a[i][j]=(a[i][j]-factor*a[k][j])%q
    return det%q


def certify_commutant(level,*,work_limit=20_000_000):
    _level(level,128)
    if type(work_limit) is not int or not 1<=work_limit<=100_000_000:raise ValueError('invalid work limit')
    n=level;q,z=_specialization(n);basis=_basis(n)
    if not _check_basis(n,basis):raise AssertionError('explicit operator failed exact cyclotomic replay')
    target=len(_allowed(n))-len(basis);rows,cols,work=_minor(n,q,z,target,work_limit)
    packet={'schema':'pp-weil-commutant/1','level':n,'dimension':len(basis),
            'basis':[[list(row) for row in a] for a in basis],
            'prime':q,'root':z,'minor_rows':rows,'minor_columns':cols,
            'allowed_entries':len(_allowed(n)),'rank_lower_bound':target,
            'rank_work':work,'complete_over_cyclotomic_field':True,
            'execution_verified':False,'method':'exact rational lower bound and modular minor upper bound'}
    return packet


def verify_commutant(packet):
    try:
        if not isinstance(packet,dict) or packet.get('schema')!='pp-weil-commutant/1':return False
        n=packet['level'];_level(n,128);q=packet['prime'];z=packet['root'];d=packet['dimension']
        if type(q) is not int or not 2<=q<=100_000 or not _prime(q) or type(z) is not int or not 1<z<q:return False
        if pow(z,n,q)!=1 or any(pow(z,n//p,q)==1 for p in _factors(n)):return False
        if sum(c*pow(z,i,q) for i,c in enumerate(cyclotomic(n)))%q:return False
        if type(d) is not int or not 1<=d<=n*n:return False
        basis=packet['basis']
        if len(basis)!=d or not _check_basis(n,basis) or len(_independent(basis,q))!=d:return False
        pairs=_allowed(n);r=len(pairs)-d;rows=packet['minor_rows'];cols=packet['minor_columns']
        if packet['allowed_entries']!=len(pairs) or packet['rank_lower_bound']!=r:return False
        if len(rows)!=r or len(cols)!=r or len(set(cols))!=r or len(set(map(tuple,rows)))!=r:return False
        if any(type(c) is not int or not 0<=c<len(pairs) for c in cols):return False
        if any(len(row)!=2 or any(type(i) is not int or not 0<=i<n for i in row) for row in rows):return False
        phases=[pow(z,k,q) for k in range(n)]
        minor=[]
        for i,j in rows:
            full_row=_row(n,phases,pairs,i,j,q)
            minor.append([full_row[c] for c in cols])
        if not _det_mod(minor,q):return False
        return packet['complete_over_cyclotomic_field'] is True and packet['execution_verified'] is False
    except (KeyError,TypeError,ValueError,IndexError,ZeroDivisionError):return False


def certify_product(a,b,*,work_limit=20_000_000):
    _level(a);_level(b)
    if gcd(a,b)!=1 or a*b>64:raise ValueError('coprime product at most 64 required')
    left=certify_commutant(a,work_limit=work_limit);right=certify_commutant(b,work_limit=work_limit)
    product=certify_commutant(a*b,work_limit=work_limit)
    if product['dimension']!=left['dimension']*right['dimension']:raise AssertionError('CRT dimensions disagree')
    return {'factors':[a,b],'dimension':product['dimension'],'left':left,'right':right,'product':product,
            'crt':crt_replay(a,b),'exact_finite_multiplicativity':True,'execution_verified':False}
