"""Exact integer image lattices, saturated fibres and original-object populations.

The Smith constructor records elementary unimodular operations; the small
verifier only checks integer products, determinants and diagonal divisibility.
Population ranking always uses original coordinates, never Smith coordinates.
"""
from __future__ import annotations
from fractions import Fraction
from functools import lru_cache
from itertools import product
from math import gcd, lcm


def _int(x):
    if isinstance(x, bool) or not isinstance(x, int):
        raise TypeError('integer required')
    return x


def _matrix(A, rational=False):
    rows = [list(r) for r in A]
    if rows and any(len(r) != len(rows[0]) for r in rows):
        raise ValueError('ragged matrix')
    for r in rows:
        for x in r:
            if isinstance(x, bool) or not isinstance(x, (int, Fraction) if rational else int):
                raise TypeError('exact matrix entries required')
    return rows


def _eye(n):
    return [[int(i == j) for j in range(n)] for i in range(n)]


def _mul(A, B):
    n = len(B[0]) if B else 0
    return [[sum(a*b for a,b in zip(row,col)) for col in zip(*B)] for row in A] if B else [[] for _ in A]


def _mv(A, x):
    return tuple(sum(a*b for a,b in zip(r,x)) for r in A)


def _det(A):
    A = [list(map(Fraction,r)) for r in A]
    n=len(A)
    if any(len(r)!=n for r in A): raise ValueError('square matrix required')
    d=Fraction(1)
    for j in range(n):
        p=next((i for i in range(j,n) if A[i][j]), None)
        if p is None:return 0
        if p!=j:A[p],A[j]=A[j],A[p];d=-d
        v=A[j][j];d*=v
        for i in range(j+1,n):
            z=A[i][j]/v
            for k in range(j+1,n):A[i][k]-=z*A[j][k]
    return int(d) if d.denominator==1 else d


def _inverse(A):
    n=len(A);rows=[list(map(Fraction,r))+list(map(Fraction,e)) for r,e in zip(A,_eye(n))]
    for j in range(n):
        p=next((i for i in range(j,n) if rows[i][j]),None)
        if p is None:raise ValueError('singular matrix')
        rows[j],rows[p]=rows[p],rows[j]
        z=rows[j][j];rows[j]=[x/z for x in rows[j]]
        for i in range(n):
            if i!=j:
                z=rows[i][j];rows[i]=[a-z*b for a,b in zip(rows[i],rows[j])]
    return [r[n:] for r in rows]


def integer_image_certificate(A, *, max_operations=100000, max_entry_bits=100000):
    """Construct UAV=diag(d), with positive d_i dividing d_{i+1}.

    Rational rows are individually denominator-cleared. ``row_scales`` maps
    the supplied rational observations B to the certified integral map A=SB.
    Empty input denotes a 0-by-0 matrix; a zero-row D-dimensional map can be
    represented by one all-zero row, retaining the original ambient dimension.
    """
    raw=_matrix(A,True);m=len(raw);n=len(raw[0]) if m else 0
    if _int(max_operations)<1 or _int(max_entry_bits)<1:raise ValueError('positive limits required')
    scales=[lcm(*(Fraction(x).denominator for x in r)) if r else 1 for r in raw]
    original=[[int(Fraction(x)*s) for x in r] for r,s in zip(raw,scales)]
    T=[r[:] for r in original];U=_eye(m);V=_eye(n);operations=0
    def tick():
        nonlocal operations
        operations+=1
        if operations>max_operations:raise ArithmeticError('Smith operation budget exhausted')
        if max((abs(x).bit_length() for M in (T,U,V) for r in M for x in r), default=0)>max_entry_bits:
            raise ArithmeticError('Smith coefficient-bit budget exhausted')
    def sr(i,j):T[i],T[j]=T[j],T[i];U[i],U[j]=U[j],U[i];tick()
    def sc(i,j):
        for M in (T,V):
            for r in M:r[i],r[j]=r[j],r[i]
        tick()
    def ar(i,j,c):
        T[i]=[a+c*b for a,b in zip(T[i],T[j])];U[i]=[a+c*b for a,b in zip(U[i],U[j])];tick()
    def ac(i,j,c):
        for M in (T,V):
            for r in M:r[i]+=c*r[j]
        tick()
    rank=0
    for k in range(min(m,n)):
        nz=[(abs(T[i][j]),i,j) for i in range(k,m) for j in range(k,n) if T[i][j]]
        if not nz:break
        _,i,j=min(nz);sr(k,i);sc(k,j)
        while True:
            changed=False
            for i in range(k+1,m):
                if T[i][k]:
                    ar(i,k,-(T[i][k]//T[k][k]))
                    if T[i][k]:sr(i,k)
                    changed=True;break
            if changed:continue
            for j in range(k+1,n):
                if T[k][j]:
                    ac(j,k,-(T[k][j]//T[k][k]))
                    if T[k][j]:sc(j,k)
                    changed=True;break
            if changed:continue
            bad=next(((i,j) for i in range(k+1,m) for j in range(k+1,n) if T[i][j]%T[k][k]),None)
            if bad is None:break
            ar(k,bad[0],1)
        if T[k][k]<0:
            T[k]=[-x for x in T[k]];U[k]=[-x for x in U[k]];tick()
        rank+=1
    cert={'schema':'singularity.integer-image/1','A':original,'original_matrix':[[[Fraction(x).numerator,Fraction(x).denominator] for x in row] for row in raw],'U':U,'V':V,
          'diagonal':[T[i][i] for i in range(rank)],'rank':rank,
          'row_scales':scales,'dimension':n,'coordinate_order':list(range(n)),
          'resources':{'operations':operations,'maximum_entry_bits':max((abs(x).bit_length() for M in (T,U,V) for r in M for x in r),default=0)}}
    if not verify_integer_image_certificate(cert):raise ArithmeticError('internal Smith verification failed')
    return cert


def verify_integer_image_certificate(cert):
    """Direct certificate replay; does not call the Smith constructor."""
    try:
        if set(cert)!={'schema','A','original_matrix','U','V','diagonal','rank','row_scales','dimension','coordinate_order','resources'}:return False
        if cert['schema']!='singularity.integer-image/1':return False
        A=_matrix(cert['A']);U=_matrix(cert['U']);V=_matrix(cert['V'])
        m=len(A);n=_int(cert['dimension']);r=_int(cert['rank']);ds=[_int(d) for d in cert['diagonal']]
        if n<0 or len(U)!=m or any(len(a)!=m for a in U) or len(V)!=n or any(len(a)!=n for a in V):return False
        if any(len(a)!=n for a in A) or not 0<=r<=min(m,n) or len(ds)!=r:return False
        if any(d<=0 for d in ds) or any(b%a for a,b in zip(ds,ds[1:])):return False
        if len(cert['row_scales'])!=m or any(_int(s)<=0 for s in cert['row_scales']):return False
        if cert['coordinate_order']!=list(range(n)) or any(type(x) is not int for x in cert['coordinate_order']):return False
        original=cert['original_matrix']
        if len(original)!=m or any(len(row)!=n for row in original):return False
        for i,row in enumerate(original):
            for j,pair in enumerate(row):
                if type(pair) is not list or len(pair)!=2 or any(type(x) is not int for x in pair) or pair[1]<=0:return False
                q=Fraction(*pair)
                if pair!=[q.numerator,q.denominator] or q*cert['row_scales'][i]!=A[i][j]:return False
        if abs(_det(U))!=1 or abs(_det(V))!=1:return False
        diag=[[ds[i] if i==j and i<r else 0 for j in range(n)] for i in range(m)]
        return _mul(_mul(U,A),V)==diag
    except (TypeError,ValueError,KeyError,IndexError,ZeroDivisionError):return False


def _checked(cert,y):
    if not verify_integer_image_certificate(cert):raise ValueError('invalid integer-image certificate')
    y=tuple(_int(x) for x in y)
    if len(y)!=len(cert['A']):raise ValueError('output dimension mismatch')
    return y


def image_contains(cert,y):
    y=_checked(cert,y);z=_mv(cert['U'],y);r=cert['rank']
    return all(z[i]%d==0 for i,d in enumerate(cert['diagonal'])) and all(t==0 for t in z[r:])


def integer_fibre(cert,y):
    """All integer solutions x=particular+sum z_i kernel_basis[i]."""
    y=_checked(cert,y)
    if not image_contains(cert,y):raise ValueError('output is outside image lattice')
    uy=_mv(cert['U'],y);r=cert['rank'];n=cert['dimension'];V=cert['V']
    z=tuple(uy[i]//cert['diagonal'][i] if i<r else 0 for i in range(n))
    return {'particular':_mv(V,z),'kernel_basis':tuple(tuple(V[i][j] for i in range(n)) for j in range(r,n))}


class BoundedFibrePopulation:
    """Original-coordinate finite box fibre with shared completion counts."""
    def __init__(self,cert,y,bounds,*,max_states=1000000):
        self.y=_checked(cert,y);self.cert=cert;self.bounds=tuple(tuple(_int(t) for t in b) for b in bounds)
        self.max_states=_int(max_states)
        if self.max_states<1 or len(self.bounds)!=cert['dimension'] or any(len(b)!=2 or b[0]>b[1] for b in self.bounds):raise ValueError('finite inclusive bounds required')
        self.A=cert['A'];self.states=0
        @lru_cache(None)
        def completions(i,residual):
            self.states+=1
            if self.states>self.max_states:raise ArithmeticError('completion-state budget exhausted')
            if i==len(self.bounds):return int(not any(residual))
            for row,t in zip(self.A,residual):
                lo=sum(min(row[j]*self.bounds[j][0],row[j]*self.bounds[j][1]) for j in range(i,len(self.bounds)))
                hi=sum(max(row[j]*self.bounds[j][0],row[j]*self.bounds[j][1]) for j in range(i,len(self.bounds)))
                if not lo<=t<=hi:return 0
            lo,hi=self.bounds[i]
            return sum(completions(i+1,tuple(t-row[i]*v for row,t in zip(self.A,residual))) for v in range(lo,hi+1))
        self._completions=completions
    def count(self):return self._completions(0,self.y)
    def contains(self,x):
        try:x=tuple(_int(t) for t in x)
        except TypeError:return False
        return len(x)==len(self.bounds) and all(a<=v<=b for v,(a,b) in zip(x,self.bounds)) and _mv(self.A,x)==self.y
    def rank(self,x):
        if not self.contains(x):raise ValueError('not in fibre population')
        rank=0;res=self.y
        for i,v in enumerate(x):
            for w in range(self.bounds[i][0],v):rank+=self._completions(i+1,tuple(t-row[i]*w for row,t in zip(self.A,res)))
            res=tuple(t-row[i]*v for row,t in zip(self.A,res))
        return rank
    def unrank(self,k):
        k=_int(k)
        if not 0<=k<self.count():raise IndexError('rank outside population')
        x=[];res=self.y
        for i,(lo,hi) in enumerate(self.bounds):
            for v in range(lo,hi+1):
                nxt=tuple(t-row[i]*v for row,t in zip(self.A,res));c=self._completions(i+1,nxt)
                if k<c:x.append(v);res=nxt;break
                k-=c
        return tuple(x)


def bounded_fibre_population(cert,y,bounds,*,max_states=1000000):
    return BoundedFibrePopulation(cert,y,bounds,max_states=max_states)


def pushforward_population(cert,bounds,*,max_objects=1000000):
    if not verify_integer_image_certificate(cert):raise ValueError('invalid certificate')
    bounds=tuple(tuple(_int(x) for x in b) for b in bounds)
    if len(bounds)!=cert['dimension'] or any(len(b)!=2 or b[0]>b[1] for b in bounds):raise ValueError('finite inclusive bounds required')
    total=1
    for a,b in bounds:total*=b-a+1
    if total>_int(max_objects):raise ArithmeticError('population budget exhausted')
    out={}
    for x in product(*(range(a,b+1) for a,b in bounds)):
        y=_mv(cert['A'],x);out[y]=out.get(y,0)+1
    return out


def operator_lattice_certificate(cert,M):
    """Certify integral ambient preservation and induced rational output map.

    Rational ambient matrices are rejected unless every entry is integral;
    a different invariant ambient lattice needs its own explicit contract.
    """
    if not verify_integer_image_certificate(cert):raise ValueError('invalid certificate')
    M=_matrix(M,True);n=cert['dimension'];A=cert['A'];m=len(A);r=cert['rank']
    if len(M)!=n or any(len(row)!=n for row in M):raise ValueError('transition dimension mismatch')
    if any(Fraction(v).denominator!=1 for row in M for v in row):raise ValueError('transition does not preserve ambient integer lattice')
    M=[[int(v) for v in row] for row in M];AM=_mul(A,M);V=cert['V'];U=cert['U']
    C=_mul(_mul(U,AM),V)
    if any(C[i][j] for i in range(m) for j in range(r,n)):raise ValueError('transition does not preserve observational kernel')
    H=[[Fraction(C[i][j],cert['diagonal'][j]) if j<r else Fraction(0) for j in range(m)] for i in range(m)]
    Q=_mul(_mul(_inverse(U),H),U)
    if _mul(Q,A)!=AM:raise ArithmeticError('quotient update identity failed')
    return {'schema':'singularity.integer-operator/1','M':M,'quotient_map':[[[v.numerator,v.denominator] for v in row] for row in Q],
            'identity':'QA=AM','domain':'certified image lattice A Z^D'}


def apply_lattice_update(cert,operator_cert,y):
    y=_checked(cert,y)
    if not image_contains(cert,y):raise ValueError('unrealizable quotient state')
    expected=operator_lattice_certificate(cert,operator_cert['M'])
    if operator_cert!=expected:raise ValueError('invalid operator certificate')
    for row in operator_cert['quotient_map']:
        for pair in row:
            if type(pair) is not list or len(pair)!=2 or any(type(x) is not int for x in pair) or pair[1]<=0:raise ValueError('canonical quotient rational pairs required')
            q=Fraction(*pair)
            if pair!=[q.numerator,q.denominator]:raise ValueError('canonical quotient rational pairs required')
    Q=[[Fraction(*v) for v in row] for row in operator_cert['quotient_map']]
    z=_mv(Q,y)
    if any(v.denominator!=1 for v in z):raise ArithmeticError('image-lattice integrality failure')
    return tuple(int(v) for v in z)
