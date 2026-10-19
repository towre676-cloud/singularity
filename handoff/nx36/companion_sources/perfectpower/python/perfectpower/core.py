"""Exact arithmetic for polynomial perfect-power hits. Coefficients are low-to-high."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
from math import gcd, isqrt, lcm
from typing import Iterable


def normalize(coefficients: Iterable[int | Fraction]) -> tuple[Fraction, ...]:
    a = [Fraction(c) for c in coefficients]
    if not a:
        raise ValueError('polynomial requires at least one coefficient')
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return tuple(a)


def evaluate(coefficients: Iterable[int | Fraction], n: int) -> Fraction:
    out = Fraction(0)
    for c in reversed(tuple(coefficients)):
        out = out * n + c
    return out


def mul(a: tuple[Fraction, ...], b: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return normalize(out)


def power(a: tuple[Fraction, ...], d: int) -> tuple[Fraction, ...]:
    if d < 0:
        raise ValueError('negative polynomial exponent')
    result = (Fraction(1),)
    while d:
        if d & 1:
            result = mul(result, a)
        a = mul(a, a)
        d //= 2
    return result


def subtract(a: tuple[Fraction, ...], b: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    return normalize([(a[i] if i < len(a) else 0) - (b[i] if i < len(b) else 0)
                      for i in range(max(len(a), len(b)))])


def floor_nth_root(n: int, d: int) -> int:
    """Largest nonnegative r with r**d <= n, using integer arithmetic."""
    if d < 2 or n < 0:
        raise ValueError('requires d >= 2 and n >= 0')
    if n < 2:
        return n
    if d == 2:
        return isqrt(n)
    lo, hi = 0, 1 << ((n.bit_length() + d - 1) // d)
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if mid ** d <= n:
            lo = mid
        else:
            hi = mid
    return lo if hi ** d > n else hi


def integer_power_root(v: int, d: int) -> int | None:
    if d < 2:
        raise ValueError('d >= 2 is required')
    if v < 0 and d % 2 == 0:
        return None
    sign = -1 if v < 0 else 1
    r = floor_nth_root(abs(v), d)
    return sign * r if r ** d == abs(v) else None


def hit_indices(coefficients: Iterable[int], d: int, k: int, end: int, start: int = 1):
    if d < 2 or start < 1 or end < 0:
        raise ValueError('requires d >= 2, start >= 1 and end >= 0')
    c = normalize(coefficients)
    if any(x.denominator != 1 for x in c):
        raise ValueError('S must be in Z[x]')
    ints = [int(x) for x in c]
    for n in range(start, end + 1):
        v = 0
        for x in reversed(ints):
            v = v * n + x
        v += k
        m = integer_power_root(v, d)
        if m is not None:
            yield (n, m)


def count(coefficients: Iterable[int], d: int, k: int, end: int) -> int:
    return sum(1 for _ in hit_indices(coefficients, d, k, end))


def windows(coefficients: Iterable[int], d: int, k: int, end: int) -> list[dict]:
    if end < 1:
        return []
    hits = set(n for n, _ in hit_indices(coefficients, d, k, end))
    running = 0
    maxima: dict[int, tuple[int, int]] = {}
    for n in range(1, end + 1):
        running += n in hits
        j = n.bit_length() - 1
        current = maxima.get(j)
        if current is None or running * current[0] > current[1] * n:
            maxima[j] = (n, running)
    return [{'lo': 1 << j, 'hi': min(end, (1 << (j + 1)) - 1),
             'maximum_at': n, 'count_at_maximum': a, 'max_ratio': a / n}
            for j, (n, a) in sorted(maxima.items())]


def leading_integer_root(a: int, d: int) -> int | None:
    return integer_power_root(a, d)


@dataclass(frozen=True)
class RigidCertificate:
    d: int
    coefficients: tuple[int, ...]  # F, low-to-high
    root_numerators: tuple[int, ...]  # Q = sum root_numerators[i] x^i / denominator
    denominator: int
    remainder_numerators: tuple[int, ...]  # R=F-Q^d, divided by denominator**d
    cutoff: int  # no integer-power hits n >= cutoff, unless exact_identity
    exact_identity: bool

    def to_json(self):
        return asdict(self)


def rigid_certificate(coefficients: Iterable[int], d: int) -> RigidCertificate | None:
    """Construct a rational truncation and an independently checkable finite-hit cutoff.

    Returns None outside the rigid leading-degree branch. The cutoff can be very large.
    """
    if d < 2:
        raise ValueError('d >= 2 is required')
    f = normalize(coefficients)
    if any(c.denominator != 1 for c in f):
        raise ValueError('F must be in Z[x]')
    if f == (0,):
        return RigidCertificate(d, (0,), (0,), 1, (0,), 1, True)
    M = len(f) - 1
    if M % d:
        return None
    b = leading_integer_root(int(f[-1]), d)
    if b is None:
        return None
    q = M // d
    Q = [Fraction(0)] * (q + 1)
    Q[q] = Fraction(b)
    for j in range(1, q + 1):
        coefficient = M - j
        current = power(normalize(Q), d)
        known = current[coefficient] if coefficient < len(current) else 0
        Q[q - j] = (f[coefficient] - known) / (d * b ** (d - 1))
    Q = normalize(Q)
    R = subtract(f, power(Q, d))
    D = lcm(*(c.denominator for c in Q))
    qnum = tuple(int(c * D) for c in Q)
    rnum = tuple(int(c * D ** d) for c in R)
    if R == (0,):
        if any(c.denominator != 1 for c in Q):
            raise ArithmeticError('integral closure violated')
        return RigidCertificate(d, tuple(map(int, f)), qnum, D, rnum, 1, True)
    r = len(R) - 1
    if q == 0 or r >= (d - 1) * q:
        raise ArithmeticError('truncation degree invariant failed')
    # At n >= B, |Q(n)| >= |b| n^q/2; |R(n)| <= C n^r.
    L = sum(abs(c) for c in Q[:-1])
    C = sum(abs(c) for c in R)
    LR = sum(abs(c) for c in R[:-1])
    B0 = max(1, (2 * L / abs(b)).__ceil__(),
             (2 * LR / abs(R[-1])).__ceil__())
    a = Fraction(abs(b), 2)
    def sufficient(n: int) -> bool:
        return (C * n ** r <= a ** d * n ** (d * q) / 2
                and C * n ** r < a ** (d - 1) * n ** ((d - 1) * q) / (2 * D))
    hi = B0
    while not sufficient(hi):
        hi *= 2
    lo = B0
    while lo < hi:
        mid = (lo + hi) // 2
        if sufficient(mid):
            hi = mid
        else:
            lo = mid + 1
    return RigidCertificate(d, tuple(map(int, f)), qnum, D, rnum, lo, False)


def verify_certificate(cert: RigidCertificate) -> bool:
    """Rebuild Q,R and check all integer inequalities at the cutoff exactly."""
    d, D, B = cert.d, cert.denominator, cert.cutoff
    if d < 2 or D < 1 or B < 1:
        return False
    try:
        F = normalize(cert.coefficients)
        Q = normalize(Fraction(x, D) for x in cert.root_numerators)
        R = subtract(F, power(Q, d))
        if tuple(int(x * D ** d) for x in R) != tuple(cert.remainder_numerators):
            return False
        if R == (0,):
            return cert.exact_identity and B == 1 and all(x.denominator == 1 for x in Q)
        if cert.exact_identity or len(F) < 2 or len(Q) < 2:
            return False
        q, r = len(Q) - 1, len(R) - 1
        b = Q[-1]
        if b.denominator != 1 or len(F) - 1 != d * q or r >= (d - 1) * q:
            return False
        L, C = sum(abs(c) for c in Q[:-1]), sum(abs(c) for c in R)
        LR = sum(abs(c) for c in R[:-1])
        a = abs(b) / 2
        return (B >= 1 and abs(b) * B >= 2 * L
                and abs(R[-1]) * B >= 2 * LR
                and C * B ** r <= a ** d * B ** (d * q) / 2
                and C * B ** r < a ** (d - 1) * B ** ((d - 1) * q) / (2 * D))
    except (ValueError, ZeroDivisionError, OverflowError):
        return False
