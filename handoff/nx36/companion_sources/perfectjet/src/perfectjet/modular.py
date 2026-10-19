"""Groebner bases over a prime field, for loci whose rational computation is too large.

Polynomials are dicts {exponent tuple: int mod P} in graded reverse lexicographic order.
`ideal_of_minors` builds every maximal-rank minor of a matrix whose entries are affine in
the parameters, interreduces the minors linearly (Macaulay style), and runs Buchberger
with the product and chain criteria. Over GF(p) coefficients never grow.

Reduction modulo p is used as evidence, not proof: if an ideal over Q has a point over
the algebraic closure, its reduction has a point modulo every prime outside a finite bad
set, so a unit ideal modulo a large random prime is strong evidence that the rational
ideal is the unit ideal. The length of a zero-dimensional ideal is computed the same way.
"""
import itertools
from .parametric import _key

P = 2147483629  # largest prime below 2^31


def _clean(p):
    return {e: c % P for e, c in p.items() if c % P}


_ORDER = [_key]


def _lead(p):
    e = max(p, key=_ORDER[-1])
    return e, p[e]


def _sub_scaled(p, q, c, mono):
    out = dict(p)
    for e, v in q.items():
        f = tuple(a+b for a, b in zip(e, mono))
        w = (out.get(f, 0)-c*v) % P
        if w:
            out[f] = w
        else:
            out.pop(f, None)
    return out


def _monic(p):
    if not p:
        return {}
    _, c = _lead(p)
    inv = pow(c, P-2, P)
    return {e: v*inv % P for e, v in p.items()}


def _divides(a, b):
    return all(x <= y for x, y in zip(a, b))


def reduce_mod(p, basis):
    leads = [_lead(g) for g in basis]
    p = dict(p)
    rem = {}
    while p:
        e, c = _lead(p)
        for g, (le, lc) in zip(basis, leads):
            if _divides(le, e):
                p = _sub_scaled(p, g, c*pow(lc, P-2, P) % P, tuple(a-b for a, b in zip(e, le)))
                break
        else:
            rem[e] = c
            del p[e]
    return rem


def interreduce_linear(polys):
    """Row-echelon form of the coefficient matrix: a linearly independent spanning set."""
    rows = [_clean(p) for p in polys if _clean(p)]
    basis = []
    for p in rows:
        p = dict(p)
        changed = True
        while p and changed:
            changed = False
            e, c = _lead(p)
            for b in basis:
                be, bc = _lead(b)
                if be == e:
                    p = _sub_scaled(p, b, c*pow(bc, P-2, P) % P, (0,)*len(e))
                    changed = True
                    break
        if p:
            basis.append(_monic(p))
    return basis


def groebner_mod(polys):
    basis = interreduce_linear(polys)
    if not basis:
        return []
    lt = [_lead(g)[0] for g in basis]
    pairs = {(i, j) for j in range(len(basis)) for i in range(j)}
    while pairs:
        i, j = min(pairs, key=lambda ij: (sum(max(x, y) for x, y in zip(lt[ij[0]], lt[ij[1]])), ij))
        pairs.discard((i, j))
        a, b = lt[i], lt[j]
        l = tuple(max(x, y) for x, y in zip(a, b))
        if all(x+y == z for x, y, z in zip(a, b, l)):
            continue
        if any(k not in (i, j) and _divides(lt[k], l) and (min(i, k), max(i, k)) not in pairs
               and (min(j, k), max(j, k)) not in pairs for k in range(len(basis))):
            continue
        sp = _sub_scaled({tuple(x+y for x, y in zip(e, tuple(u-v for u, v in zip(l, a)))): c
                          for e, c in basis[i].items()}, basis[j], 1, tuple(u-v for u, v in zip(l, b)))
        r = reduce_mod(sp, basis)
        if r:
            r = _monic(r)
            e = _lead(r)[0]
            if not any(e):
                return [{e: 1}]
            basis.append(r)
            lt.append(e)
            k = len(basis)-1
            pairs.update((m, k) for m in range(k))
    keep = [i for i, e in enumerate(lt)
            if not any(o != i and _divides(lt[o], e) and (lt[o] != e or o < i) for o in range(len(lt)))]
    kept = [basis[i] for i in keep]
    return [_monic(reduce_mod(g, [h for h in kept if h is not g])) for g in kept]


def is_unit(gb):
    return len(gb) == 1 and not any(next(iter(gb[0])))


def mul_mod(p, q):
    out = {}
    for e, c in p.items():
        for f, d in q.items():
            g = tuple(a+b for a, b in zip(e, f))
            out[g] = (out.get(g, 0)+c*d) % P
    return _clean(out)


def det_mod(m, nvars):
    """Determinant of a square matrix of polynomials mod P by fraction-free Bareiss."""
    n = len(m)
    m = [[_clean(x) for x in row] for row in m]
    sign, prev = 1, {(0,)*nvars: 1}
    for k in range(n-1):
        if not m[k][k]:
            sw = next((i for i in range(k+1, n) if m[i][k]), None)
            if sw is None:
                return {}
            m[k], m[sw] = m[sw], m[k]
            sign = -sign
        for i in range(k+1, n):
            for j in range(k+1, n):
                num = _clean({e: (c) for e, c in mul_mod(m[i][j], m[k][k]).items()})
                for e, c in mul_mod(m[i][k], m[k][j]).items():
                    num[e] = (num.get(e, 0)-c) % P
                num = _clean(num)
                m[i][j] = _exact_div(num, prev)
            m[i][k] = {}
        prev = m[k][k]
    return {e: c*sign % P for e, c in m[n-1][n-1].items()}


def _exact_div(p, q):
    if not p:
        return {}
    quo = {}
    p = dict(p)
    lq, cq = _lead(q)
    inv = pow(cq, P-2, P)
    while p:
        e, c = _lead(p)
        if not _divides(lq, e):
            raise ArithmeticError("inexact division mod P")
        mono = tuple(a-b for a, b in zip(e, lq))
        k = c*inv % P
        quo[mono] = k
        p = _sub_scaled(p, q, k, mono)
    return quo


def to_mod(p):
    """Rational polynomial dict to GF(P)."""
    out = {}
    for e, c in p.items():
        out[e] = c.numerator % P*pow(c.denominator % P, P-2, P) % P
    return _clean(out)


def ideal_of_minors(matrix, size, nvars):
    """All size-by-size minors of a polynomial matrix, mod P."""
    rows, cols = len(matrix), len(matrix[0])
    mm = [[to_mod(x) for x in row] for row in matrix]
    out = []
    for r in itertools.combinations(range(rows), size):
        for c in itertools.combinations(range(cols), size):
            d = det_mod([[mm[i][j] for j in c] for i in r], nvars)
            if d:
                out.append(d)
    return out


def saturated_unit(ideal, avoid, nvars):
    """Is V(ideal) minus V(avoid) empty (Rabinowitsch with one extra variable, mod P)?"""
    ext = [{e+(0,): c for e, c in p.items()} for p in ideal]
    za = {e+(1,): c for e, c in avoid.items()}
    ext.append(_clean({(0,)*(nvars+1): 1, **{e: (-c) % P for e, c in za.items()}}))
    return is_unit(groebner_mod(ext))


def quotient_length(gb, nvars, bound=40):
    leads = [_lead(g)[0] for g in gb]
    count = 0
    for e in itertools.product(range(bound), repeat=nvars):
        if not any(_divides(l, e) for l in leads):
            count += 1
    return count


def _elim_key(e):
    """Block order: the last variable dominates, then grevlex on the rest."""
    return (e[-1], _key(e[:-1]))


def groebner_mod_order(polys, key):
    _ORDER.append(key)
    try:
        return groebner_mod(polys)
    finally:
        _ORDER.pop()


def saturate_mod(ideal, h, nvars):
    """Groebner basis (grevlex) of I : h^infinity modulo P."""
    ext = [{e+(0,): c for e, c in p.items()} for p in ideal]
    ext.append(_clean({(0,)*(nvars+1): 1, **{e+(1,): (-c) % P for e, c in h.items()}}))
    g = groebner_mod_order(ext, _elim_key)
    return groebner_mod([{e[:-1]: c for e, c in p.items()} for p in g if all(e[-1] == 0 for e in p)])


def dimension_mod(gb, nvars):
    if not gb:
        return nvars
    if is_unit(gb):
        return -1
    leads = [_lead(g)[0] for g in gb]
    best = 0
    for mask in itertools.product((0, 1), repeat=nvars):
        free = [i for i in range(nvars) if mask[i]]
        if all(any(e[i] for i in range(nvars) if i not in free) for e in leads):
            best = max(best, len(free))
    return best


def rational_reconstruction(a, m=None):
    """Smallest-height fraction congruent to a modulo m (Wang's algorithm), or None."""
    from fractions import Fraction
    from math import isqrt
    m = m or P
    a %= m
    bound = isqrt(m//2)
    r0, r1, s0, s1 = m, a, 0, 1
    while r1 > bound:
        q = r0//r1
        r0, r1, s0, s1 = r1, r0-q*r1, s1, s0-q*s1
    if s1 == 0 or abs(s1) > bound:
        return None
    return Fraction(r1, s1) if s1 > 0 else Fraction(-r1, -s1)


def nullspace_mod(rows, ncols):
    rows = [[x % P for x in r] for r in rows]
    piv, r = [], 0
    for c in range(ncols):
        k = next((i for i in range(r, len(rows)) if rows[i][c]), None)
        if k is None:
            continue
        rows[r], rows[k] = rows[k], rows[r]
        inv = pow(rows[r][c], P-2, P)
        rows[r] = [x*inv % P for x in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][c]:
                f = rows[i][c]
                rows[i] = [(x-f*y) % P for x, y in zip(rows[i], rows[r])]
        piv.append(c)
        r += 1
    out = []
    for fcol in range(ncols):
        if fcol in piv:
            continue
        v = [0]*ncols
        v[fcol] = 1
        for i, pc in enumerate(piv):
            v[pc] = (-rows[i][fcol]) % P
        out.append(v)
    return out


def standard_monomials_mod(gb, nvars, bound=60):
    leads = [_lead(g)[0] for g in gb]
    std = [e for e in itertools.product(range(bound), repeat=nvars) if not any(_divides(l, e) for l in leads)]
    return sorted(std, key=_key)


def nilpotent_off(gb, h, nvars):
    """For a zero-dimensional ideal: is V(I) contained in V(h)? (h nilpotent in the quotient algebra.)"""
    std = standard_monomials_mod(gb, nvars)
    idx = {e: i for i, e in enumerate(std)}
    n = len(std)
    if n == 0:
        return True, 0
    cols = []
    for e in std:
        nf = reduce_mod(mul_mod(h, {e: 1}), gb)
        col = [0]*n
        for mono, c in nf.items():
            col[idx[mono]] = c
        cols.append(col)
    mat = [list(r) for r in zip(*cols)]
    # h is nilpotent iff mat^n == 0; square repeatedly.
    def mm(a, b):
        bt = list(zip(*b))
        return [[sum(x*y for x, y in zip(row, col)) % P for col in bt] for row in a]
    power, k = mat, 1
    while k < n:
        power = mm(power, power)
        k *= 2
    return all(not any(r) for r in power), n
