"""Adaptive local sieve for perfect-power hits F(n)=m^d.

An input n survives modulus q when F(n) mod q is a d-th power residue mod q.
Exclusions are exact: a hit survives every modulus, whatever the test order.
Only the order is adaptive. The next modulus maximizes eliminated density per unit
cost, and the order never changes which inputs are excluded by a fixed set of moduli.
"""
from fractions import Fraction as Q
from math import gcd


def poly_value(coeffs,n):
    out=0
    for c in reversed(coeffs):out=out*n+c
    return out


def _check_coeffs(coeffs):
    if not coeffs or any(isinstance(c,bool) or not isinstance(c,int) for c in coeffs):
        raise ValueError("integer coefficients, lowest degree first, are required")


def integer_root(value,d):
    """m with m^d == value, or None. Odd d accepts negative values."""
    if d<2:raise ValueError("exponent must be at least 2")
    if value<0:
        if d%2==0:return None
        m=integer_root(-value,d);return None if m is None else -m
    if value<2:return value
    lo,hi=0,1<<((value.bit_length()+d-1)//d+1)
    while lo<hi:
        mid=(lo+hi+1)//2
        if mid**d<=value:lo=mid
        else:hi=mid-1
    return lo if lo**d==value else None


def power_residues(d,q):
    return frozenset(pow(x,d,q) for x in range(q))


def allowed_residues(coeffs,d,q):
    _check_coeffs(coeffs);powers=power_residues(d,q)
    return frozenset(n for n in range(q) if poly_value(coeffs,n)%q in powers)


def _combine(m1,r1,m2,r2):
    """Residues mod lcm(m1,m2) whose reductions lie in r1 and r2."""
    m=m1*m2//gcd(m1,m2)
    return m,frozenset(n for n in range(m) if n%m1 in r1 and n%m2 in r2)


def adaptive_sieve(coeffs,d,candidates=range(2,50),max_modulus=10**5):
    """Greedy exact sieve. Returns the combined modulus, its surviving residues, and the step log."""
    _check_coeffs(coeffs)
    local={q:allowed_residues(coeffs,d,q) for q in candidates if q>=2}
    modulus,survivors=1,frozenset({0});log=[];used=[]
    while True:
        best=None
        for q,r in local.items():
            if q in used:continue
            m=modulus*q//gcd(modulus,q)
            if m>max_modulus:continue
            # Density after combining, computed from the combined residue set.
            _,combined=_combine(modulus,survivors,q,r)
            before=Q(len(survivors),modulus);after=Q(len(combined),m)
            score=(before-after)/q
            if after<before and (best is None or score>best[0]):best=(score,q,m,combined,before,after)
        if best is None:break
        _,q,m,combined,before,after=best
        used.append(q);modulus,survivors=m,combined
        log.append({"modulus":q,"cost":q,"density_before":before,"density_after":after})
    return {"modulus":modulus,"survivors":survivors,"density":Q(len(survivors),modulus),"steps":log}


def exclusion_witness(coeffs,d,n,moduli):
    """First modulus showing F(n) is not a d-th power, or None if n survives all of them."""
    v=poly_value(coeffs,n)
    for q in moduli:
        if v%q not in power_residues(d,q):return {"n":n,"modulus":q,"residue":v%q}
    return None


def hits(coeffs,d,limit,start=1):
    """Exact hit list by integer roots, n in [start,limit]."""
    _check_coeffs(coeffs)
    return [(n,integer_root(poly_value(coeffs,n),d)) for n in range(start,limit+1)
            if integer_root(poly_value(coeffs,n),d) is not None]


def sieved_hits(coeffs,d,limit,sieve,start=1):
    """Same list, testing integer roots only on sieve survivors."""
    m,s=sieve["modulus"],sieve["survivors"];out=[];tested=0
    for n in range(start,limit+1):
        if n%m in s:
            tested+=1;root=integer_root(poly_value(coeffs,n),d)
            if root is not None:out.append((n,root))
    return out,tested


def sieve_receipt():
    # Pell7: (x^2+7)/2=y^2 for odd x, written as 2y^2-7 with input y: F(y)=2y^2-7 must be a square.
    pell=[-7,0,2];s=adaptive_sieve(pell,2,range(2,30))
    found,tested=sieved_hits(pell,2,2000,s)
    cubic=[3,0,0,1];c=adaptive_sieve(cubic,2,range(2,30))
    cfound,ctested=sieved_hits(cubic,2,2000,c)
    return {"pell7":{"modulus":s["modulus"],"density":s["density"],"steps":[x["modulus"] for x in s["steps"]],
                     "hits":found,"tested":tested,"brute_force_agrees":found==hits(pell,2,2000)},
            "n3_plus_3":{"modulus":c["modulus"],"density":c["density"],"hits":cfound,"tested":ctested,
                         "brute_force_agrees":cfound==hits(cubic,2,2000)},
            "identity_case":adaptive_sieve([1,2,1],2,range(2,30))["density"]}
