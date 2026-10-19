"""Exact univariate polynomial algebra over Q (coefficients low-to-high, Fractions).

Everything here is exact rational arithmetic; no floating point is used.
The zero polynomial is represented as (Fraction(0),).
"""
from __future__ import annotations

from fractions import Fraction
from math import gcd, lcm
from typing import Iterable, Sequence

from .core import evaluate, mul, normalize, power, subtract

Poly = tuple  # tuple[Fraction, ...]

ZERO: Poly = (Fraction(0),)
ONE: Poly = (Fraction(1),)
X: Poly = (Fraction(0), Fraction(1))


def poly(coefficients: Iterable) -> Poly:
    return normalize(coefficients)


def is_zero(a: Poly) -> bool:
    return len(a) == 1 and a[0] == 0


def degree(a: Poly) -> int:
    """Degree, with deg(0) = -1 by convention."""
    return -1 if is_zero(a) else len(a) - 1


def lead(a: Poly) -> Fraction:
    return a[-1]


def add(a: Poly, b: Poly) -> Poly:
    return normalize([(a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0)
                      for i in range(max(len(a), len(b)))])


def scale(a: Poly, c) -> Poly:
    return normalize([x * c for x in a])


def monic(a: Poly) -> Poly:
    if is_zero(a):
        return a
    return scale(a, 1 / lead(a))


def divmod_poly(a: Poly, b: Poly) -> tuple[Poly, Poly]:
    if is_zero(b):
        raise ZeroDivisionError('polynomial division by zero')
    a = list(a)
    db, lb = degree(b), lead(b)
    if degree(normalize(a)) < db:
        return ZERO, normalize(a)
    quotient = [Fraction(0)] * (len(a) - db)
    for i in range(len(a) - 1, db - 1, -1):
        c = a[i] / lb
        quotient[i - db] = c
        if c:
            for j in range(db + 1):
                a[i - db + j] -= c * b[j]
    return normalize(quotient), normalize(a[:db] or [0])


def exact_div(a: Poly, b: Poly) -> Poly:
    q, r = divmod_poly(a, b)
    if not is_zero(r):
        raise ArithmeticError('inexact polynomial division')
    return q


def _positive_primitive(a: Poly) -> tuple[int, ...]:
    """Integer polynomial equal to a positive rational multiple of a (signs preserved)."""
    D = common_denominator(a)
    ints = [int(x * D) for x in a]
    g = 0
    for x in ints:
        g = gcd(g, x)
    return tuple(x // g for x in ints)


def gcd_poly(a: Poly, b: Poly) -> Poly:
    """Monic gcd (gcd(0,0) = 0)."""
    # Primitive remainder sequence: rescaling each remainder by a nonzero constant keeps the
    # gcd up to a constant and stops rational coefficient growth.
    if not is_zero(a):
        a = poly(_positive_primitive(a))
    if not is_zero(b):
        b = poly(_positive_primitive(b))
    while not is_zero(b):
        r = divmod_poly(a, b)[1]
        a, b = b, (r if is_zero(r) else poly(_positive_primitive(r)))
    return monic(a)


def derivative(a: Poly) -> Poly:
    return normalize([i * a[i] for i in range(1, len(a))] or [0])


def compose_linear(a: Poly, u, v) -> Poly:
    """Return a(u + v x)."""
    out = ZERO
    for c in reversed(a):
        out = add(mul(out, (Fraction(u), Fraction(v))), (Fraction(c),))
    return out


def squarefree_decomposition(a: Poly) -> tuple[Fraction, dict[int, Poly]]:
    """Yun's algorithm: a = lead(a) * prod_j S_j^j with S_j monic, squarefree, pairwise coprime.

    Returns (leading coefficient, {j: S_j}) keeping only nonconstant S_j.
    """
    if degree(a) < 1:
        return (a[0], {})
    c = lead(a)
    f = monic(a)
    out: dict[int, Poly] = {}
    g = gcd_poly(f, derivative(f))
    w = exact_div(f, g)
    y = exact_div(derivative(f), g)
    z = subtract(y, derivative(w))
    j = 1
    while degree(w) > 0:
        s = gcd_poly(w, z)
        if degree(s) > 0:
            out[j] = s
        w = exact_div(w, s)
        y = exact_div(z, s)
        z = subtract(y, derivative(w))
        j += 1
    return c, out


def expand_decomposition(c: Fraction, parts: dict[int, Poly]) -> Poly:
    out: Poly = (Fraction(c),)
    for j, s in parts.items():
        out = mul(out, power(s, j))
    return out


def common_denominator(a: Poly) -> int:
    return lcm(*(x.denominator for x in a))


def integer_primitive(a: Poly) -> tuple[int, ...]:
    """Positive rational multiple of a with coprime integer coefficients (sign kept)."""
    D = common_denominator(a)
    ints = [int(x * D) for x in a]
    g = 0
    for x in ints:
        g = gcd(g, x)
    return tuple(x // g for x in ints) if g else (0,)


# ---------------------------------------------------------------------------
# Real-root counting (Sturm) and exact integer roots.
# ---------------------------------------------------------------------------

def sturm_chain(a: Poly) -> list[tuple[int, ...]]:
    """Sturm sequence of a, each member rescaled by a positive constant to a primitive
    integer polynomial (positive rescaling does not change any sign, so counts are exact)."""
    chain = [poly(_positive_primitive(a)), poly(_positive_primitive(derivative(a)))]
    while True:
        r = divmod_poly(chain[-2], chain[-1])[1]
        if is_zero(r):
            break
        chain.append(poly(_positive_primitive(scale(r, -1))))
    return [tuple(int(c) for c in p) for p in chain]


def _eval_int(p: Sequence[int], x: int) -> int:
    out = 0
    for c in reversed(p):
        out = out * x + c
    return out


def _sign_changes(chain: Sequence[Sequence[int]], x: int) -> int:
    signs = []
    for p in chain:
        v = _eval_int(p, x)
        if v:
            signs.append(v > 0)
    return sum(1 for s, t in zip(signs, signs[1:]) if s != t)


def count_real_roots(chain, lo: int, hi: int) -> int:
    """Number of distinct real roots in (lo, hi] of a squarefree polynomial (integer ends)."""
    return _sign_changes(chain, lo) - _sign_changes(chain, hi)


def cauchy_bound(a: Poly) -> int:
    """Every complex root z satisfies |z| < bound."""
    top = abs(lead(a))
    return int(1 + max((abs(x) / top for x in a[:-1]), default=Fraction(0))) + 1


def integer_roots(a: Iterable, lo: int | None = None, hi: int | None = None) -> list[int]:
    """All integer roots of a nonzero rational polynomial in [lo, hi] (defaults: all roots).

    Uses the squarefree part and Sturm bisection on integer endpoints, then exact evaluation;
    the result is complete, not heuristic.
    """
    a = poly(a)
    if is_zero(a):
        raise ValueError('the zero polynomial has every integer as a root')
    if degree(a) == 0:
        return []
    sq = exact_div(a, gcd_poly(a, derivative(a)))
    B = cauchy_bound(sq)
    lo = -B if lo is None else max(lo, -B)
    hi = B if hi is None else min(hi, B)
    if lo > hi:
        return []
    chain = sturm_chain(sq)
    roots: list[int] = []
    # Roots in (lo - 1, hi] contain every integer root in [lo, hi].
    stack = [(lo - 1, hi)]
    while stack:
        a_, b_ = stack.pop()
        if count_real_roots(chain, a_, b_) == 0:
            continue
        if b_ - a_ == 1:
            if evaluate(sq, b_) == 0:
                roots.append(b_)
            continue
        m = (a_ + b_) // 2
        stack.append((a_, m))
        stack.append((m, b_))
    return sorted(roots)


def resultant(a: Poly, b: Poly) -> Fraction:
    """Resultant Res(a, b) = lc(a)^deg(b) prod_{a(x)=0} b(x), by the Euclidean recursion."""
    a, b = poly(a), poly(b)
    if is_zero(a) or is_zero(b):
        return Fraction(0)
    da, db = degree(a), degree(b)
    if da == 0:
        return a[0] ** db
    if db == 0:
        return b[0] ** da
    if da < db:
        return (-1) ** (da * db) * resultant(b, a)
    r = divmod_poly(a, b)[1]
    if is_zero(r):
        return Fraction(0)
    # Res(a, b) = (-1)^(da db) Res(b, a) = (-1)^(da db) lc(b)^(da - dr) Res(b, r)
    dr = degree(r)
    return (-1) ** (da * db) * lead(b) ** (da - dr) * resultant(b, r)


def interpolate(xs: Sequence[int], ys: Sequence) -> Poly:
    """Lagrange interpolation over Q."""
    out = ZERO
    for i, (xi, yi) in enumerate(zip(xs, ys)):
        term: Poly = (Fraction(yi),)
        for j, xj in enumerate(xs):
            if j != i:
                term = mul(term, (Fraction(-xj, xi - xj), Fraction(1, xi - xj)))
        out = add(out, term)
    return out
