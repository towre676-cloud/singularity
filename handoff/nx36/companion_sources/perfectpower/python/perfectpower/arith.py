"""Exact integer arithmetic: factorization, divisors, Pell-type equations. Stdlib only."""
from __future__ import annotations

import random
from math import gcd, isqrt


def is_probable_prime(n: int) -> bool:
    """Deterministic Miller-Rabin for n < 3.3e24; strong probable-prime test beyond."""
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)
    for p in small:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in small:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _pollard_rho(n: int, rng: random.Random) -> int:
    if n % 2 == 0:
        return 2
    while True:
        c = rng.randrange(1, n)
        f = lambda x: (x * x + c) % n
        x = y = rng.randrange(2, n)
        d = 1
        while d == 1:
            x = f(x)
            y = f(f(y))
            d = gcd(abs(x - y), n)
        if d != n:
            return d


def factorint(n: int) -> dict[int, int]:
    """Prime factorization of |n| (n != 0) as {p: e}."""
    if n == 0:
        raise ValueError('cannot factor 0')
    n = abs(n)
    out: dict[int, int] = {}
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        while n % p == 0:
            out[p] = out.get(p, 0) + 1
            n //= p
    rng = random.Random(12345)
    stack = [n] if n > 1 else []
    while stack:
        m = stack.pop()
        if m == 1:
            continue
        if is_probable_prime(m):
            out[m] = out.get(m, 0) + 1
            continue
        r = isqrt(m)
        if r * r == m:
            stack += [r, r]
            continue
        d = _pollard_rho(m, rng)
        stack += [d, m // d]
    return dict(sorted(out.items()))


def divisors(n: int) -> list[int]:
    """Positive divisors of |n| (n != 0)."""
    ds = [1]
    for p, e in factorint(n).items():
        ds = [x * p ** k for x in ds for k in range(e + 1)]
    return sorted(ds)


def is_square(n: int) -> bool:
    return n >= 0 and isqrt(n) ** 2 == n


def pell_fundamental(D: int) -> tuple[int, int]:
    """Least x, y > 0 with x^2 - D y^2 = 1, for D > 0 not a square (continued fractions)."""
    if D <= 0 or is_square(D):
        raise ValueError('D must be a positive nonsquare')
    a0 = isqrt(D)
    m, d, a = 0, 1, a0
    p_prev, p = 1, a0
    q_prev, q = 0, 1
    while p * p - D * q * q != 1:
        m = d * a - m
        d = (D - m * m) // d
        a = (a0 + m) // d
        p_prev, p = p, a * p + p_prev
        q_prev, q = q, a * q + q_prev
    return p, q


def _sqrt_mod_prime(a: int, p: int) -> list[int]:
    """Roots of z^2 = a (mod p), p prime (Tonelli-Shanks)."""
    a %= p
    if p == 2 or a == 0:
        return sorted({z for z in range(min(p, 2)) if (z * z - a) % p == 0}) if p == 2 else [0]
    if pow(a, (p - 1) // 2, p) != 1:
        return []
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    m, c, t, r = s, pow(z, q, p), pow(a, q, p), pow(a, (q + 1) // 2, p)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1:
            t2 = t2 * t2 % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        m, c, t, r = i, b * b % p, t * b * b % p, r * b % p
    return sorted({r, p - r})


def _sqrt_mod_prime_power(a: int, p: int, e: int) -> list[int]:
    """All z mod p^e with z^2 = a (mod p^e)."""
    pe = p ** e
    a %= pe
    if a == 0:
        h = (e + 1) // 2
        return list(range(0, pe, p ** h))
    v = 0
    while a % p == 0:
        a //= p
        v += 1
    if v:
        if v % 2:
            return []
        # z = p^(v/2) z' with z'^2 = a (mod p^(e-v)), z' a unit
        inner = _sqrt_mod_prime_power(a, p, e - v)
        step = p ** (e - v)
        out = set()
        for z1 in inner:
            for k in range(p ** (v // 2)):
                out.add((p ** (v // 2) * (z1 + step * k)) % pe)
        return sorted(out)
    if p == 2:
        roots = [z for z in range(min(8, pe)) if (z * z - a) % min(8, pe) == 0]
        k = 3
        while k < e:
            roots = sorted({z + j * 2 ** k for z in roots for j in (0, 1)
                            if ((z + j * 2 ** k) ** 2 - a) % 2 ** (k + 1) == 0})
            k += 1
        return sorted({z % pe for z in roots})
    roots = _sqrt_mod_prime(a, p)
    for k in range(1, e):
        mod = p ** (k + 1)
        roots = [(z - (z * z - a) * pow(2 * z, -1, mod)) % mod for z in roots]
    return sorted(roots)


def sqrt_mod(a: int, m: int) -> list[int]:
    """All z in [0, m) with z^2 = a (mod m), m >= 1 (factorization + Hensel + CRT)."""
    if m == 1:
        return [0]
    sols, mod = [0], 1
    for p, e in factorint(m).items():
        pe = p ** e
        rs = _sqrt_mod_prime_power(a, p, e)
        if not rs:
            return []
        inv = pow(mod, -1, pe)
        sols = [x + mod * ((r - x) * inv % pe) for x in sols for r in rs]
        mod *= pe
    return sorted(sols)


def _pqa(P0: int, Q0: int, D: int):
    """PQa continued-fraction iteration for (P0 + sqrt D)/Q0 (Q0 | D - P0^2).

    Yields (i, P_i, Q_i, G_{i-1}, B_{i-1}) until the (P, Q) pair repeats (one full period
    after the expansion becomes purely periodic).
    """
    s = isqrt(D)
    P, Q = P0, Q0
    G2, G1 = -P0, Q0
    B2, B1 = 1, 0
    seen = set()
    i = 0
    while True:
        if Q > 0:
            a = (P + s) // Q
        else:
            a = -((P + s) // (-Q)) - 1
        G2, G1 = G1, a * G1 + G2
        B2, B1 = B1, a * B1 + B2
        P = a * Q - P
        Q = (D - P * P) // Q
        i += 1
        yield i, P, Q, G1, B1
        if (P, Q) in seen:
            return
        seen.add((P, Q))


def _negative_pell(D: int) -> tuple[int, int] | None:
    """Least positive solution of x^2 - D y^2 = -1, or None."""
    for _, P, Q, G, B in _pqa(0, 1, D):
        if Q == 1 or Q == -1:
            if G * G - D * B * B == -1:
                return G, B
            if G * G - D * B * B == 1:
                return None
    return None


def generalized_pell_classes(D: int, M: int) -> list[tuple[int, int]]:
    """Fundamental solutions of x^2 - D y^2 = M (D > 0 nonsquare, M != 0), one per class.

    Lagrange-Matthews-Mollin (LMM) algorithm: for every f > 0 with f^2 | M and every z with
    z^2 = D (mod |m|), m = M / f^2, -|m|/2 < z <= |m|/2, expand (z + sqrt D)/|m| and use the
    first convergent with Q_i = +-1.  Every solution of the equation is +-(x + y sqrt D) times
    a power of the fundamental unit for one of the returned (x, y) or their conjugates.
    """
    if M == 0:
        raise ValueError('M must be nonzero')
    neg = _negative_pell(D)
    reps = []
    f = 1
    while f * f <= abs(M):
        if M % (f * f) == 0:
            m = M // (f * f)
            am = abs(m)
            if am == 1:
                zs = [0]
            else:
                zs = [z if 2 * z <= am else z - am for z in sqrt_mod(D, am)]
            for z in zs:
                for _, P, Q, r, t in _pqa(z, am, D):
                    if Q in (1, -1):
                        v = r * r - D * t * t
                        if v == m:
                            reps.append((f * r, f * t))
                        elif v == -m and neg is not None:
                            a, b = neg
                            reps.append((f * (r * a + t * b * D), f * (r * b + t * a)))
                        break
        f += 1
    return reps


def generalized_pell_classes_bruteforce(D: int, M: int) -> list[tuple[int, int]]:
    """Nagell-bound search (slow reference implementation used by the tests)."""
    x1, y1 = pell_fundamental(D)
    if M > 0:
        ymax = isqrt(y1 * y1 * M // (2 * (x1 + 1)))
    else:
        ymax = isqrt(y1 * y1 * (-M) // (2 * (x1 - 1)))
    reps = []
    for y in range(0, ymax + 1):
        v = M + D * y * y
        if is_square(v):
            x = isqrt(v)
            reps.append((x, y))
            if x:
                reps.append((-x, y))
    return reps


def generalized_pell_solutions(D: int, M: int, xmax: int) -> set[tuple[int, int]]:
    """All integer solutions (x, y) of x^2 - D y^2 = M with |x| <= xmax (D > 0 nonsquare, M != 0)."""
    x1, y1 = pell_fundamental(D)
    out: set[tuple[int, int]] = set()
    for x0, y0 in generalized_pell_classes(D, M):
        for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            for direction in (1, -1):
                x, y = sx * x0, sy * y0
                # Along an orbit x^2 = M + D y^2 and |y_k| is decreasing-then-increasing
                # in k, so once |x| > xmax while |y| grows, it never returns.
                while True:
                    if abs(x) <= xmax:
                        out.add((x, y))
                    nx, ny = x * x1 + direction * D * y * y1, x * direction * y1 + y * x1
                    if abs(x) > xmax and abs(ny) > abs(y):
                        break
                    x, y = nx, ny
    return out
