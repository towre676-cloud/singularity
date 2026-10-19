"""Bounded exact CRT and rational reconstruction recovered from tube operators.

Uniqueness requires M>2*A*B; every fraction is checked back against all residues.
A reconstruction is arithmetic, not a proof that a guessed operator annihilates
an infinite sequence. Bad or insufficient data raise instead of being rounded.
"""
from fractions import Fraction
from math import gcd


def combine(residues):
    """Generalized CRT, including consistent non-coprime moduli."""
    residues=tuple(residues)
    if not residues:raise ValueError('nonempty residue system required')
    x,M=0,1
    for residue,m in residues:
        if type(residue) is not int or type(m) is not int or m<2:
            raise ValueError('integer residues and moduli at least two required')
        g=gcd(M,m)
        if (residue-x)%g:raise ValueError('inconsistent CRT residues')
        n=m//g
        digit=0 if n==1 else ((residue-x)//g)*pow(M//g,-1,n)%n
        x=(x+M*digit)%(M*n);M*=n
    return x,M


def reconstruct(residue,modulus,numerator_bound,denominator_bound):
    A,B=numerator_bound,denominator_bound
    if any(type(x) is not int for x in (residue,modulus,A,B)) or A<0 or B<1 or modulus<2:
        raise ValueError('integer bounds A>=0,B>=1 and modulus>=2 required')
    if modulus<=2*A*B:raise ValueError('modulus does not establish bounded uniqueness')
    r0,r1=modulus,residue%modulus;t0,t1=0,1
    while abs(r1)>A:
        q=r0//r1;r0,r1=r1,r0-q*r1;t0,t1=t1,t0-q*t1
    if not t1 or abs(t1)>B or gcd(t1,modulus)!=1:
        raise ValueError('no bounded invertible-denominator reconstruction')
    candidate=Fraction(r1,t1)
    if abs(candidate.numerator)>A or candidate.denominator>B or (
            candidate.numerator-residue*candidate.denominator)%modulus:
        raise ValueError('no bounded rational reconstruction')
    return candidate


def reconstruct_system(residues,A,B):
    residues=tuple(residues);r,M=combine(residues)
    value=reconstruct(r,M,A,B)
    for residue,m in residues:
        if gcd(value.denominator,m)!=1 or (value.numerator-residue*value.denominator)%m:
            raise ValueError('reconstruction fails an input modulus')
    return {'value':str(value),'combined_residue':r,'modulus':M,
            'numerator_bound':A,'denominator_bound':B,
            'uniqueness':M>2*A*B,'execution_verified':False,
            'uniqueness_theorem':'PerfectPower.BoundedReconstruction.unique'}


def berlekamp_massey(terms,p):
    """Minimal prefix recurrence over F_p; caller must certify p prime."""
    from .local_quartic import _prime
    if not _prime(p):raise ValueError('prime field required')
    s=tuple(terms)
    if any(type(x) is not int for x in s):raise ValueError('integer terms required')
    C,B=[1],[1];L,m,b=0,1,1
    for n in range(len(s)):
        d=sum(C[i]*s[n-i] for i in range(len(C)) if n>=i)%p
        if not d:m+=1;continue
        old=C[:];factor=d*pow(b,-1,p)%p
        if len(C)<len(B)+m:C.extend([0]*(len(B)+m-len(C)))
        for j,v in enumerate(B):C[j+m]=(C[j+m]-factor*v)%p
        if 2*L<=n:L=n+1-L;B=old;b=d;m=1
        else:m+=1
    C+= [0]*max(0,L+1-len(C))
    # chronological coefficients: s[n+L]=sum_i c_i*s[n+i].
    return tuple((-C[L-i])%p for i in range(L))
