"""Exact exceptional parameters of a graph pair's first discrepancy (SNG-F31).

Given two coefficient prefixes, the discrepancies Delta_v(q) are polynomials
over Q.  The generic first visible volume r is the least v with Delta_v != 0.
At a parameter q0 in (0,1) the first visible volume is the least v with
Delta_v(q0) != 0; it exceeds r exactly at the roots of Delta_r.  Those roots
are isolated by Sturm sequences of the square-free part with exact rational
bisection, every interior root is found (Sturm counts are exact), and each is
represented by a square-free defining polynomial and an isolating open
interval containing no other root of it.  Later discrepancies are tested at an
algebraic root exactly: Delta_v(alpha) = 0 iff gcd(f, Delta_v) has a root in
the isolating interval.  The endpoints q = 0 and q = 1 are evaluated directly
and reported separately.  No floating point or sampling is used.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Mapping, Sequence

from .polynomials import derivative, evaluate, normalize, sub

Poly = dict[int, Fraction]


def _degree(f: Mapping[int, Fraction]) -> int:
    return max(f) if f else -1


def _divmod(f: Mapping[int, Fraction], g: Mapping[int, Fraction]) -> tuple[Poly, Poly]:
    f, g = normalize(f), normalize(g)
    if not g:
        raise ZeroDivisionError("polynomial division by zero")
    quotient: Poly = {}
    remainder = dict(f)
    dg, lead = _degree(g), g[_degree(g)]
    while remainder and _degree(remainder) >= dg:
        shift = _degree(remainder) - dg
        factor = remainder[_degree(remainder)] / lead
        quotient[shift] = quotient.get(shift, Fraction(0)) + factor
        for e, c in g.items():
            remainder[e + shift] = remainder.get(e + shift, Fraction(0)) - factor * c
        remainder = normalize(remainder)
    return normalize(quotient), remainder


def gcd(f: Mapping[int, Fraction], g: Mapping[int, Fraction]) -> Poly:
    """Monic greatest common divisor over Q (zero only if both are zero)."""
    a, b = normalize(f), normalize(g)
    while b:
        a, b = b, _divmod(a, b)[1]
    if not a:
        return {}
    lead = a[_degree(a)]
    return {e: c / lead for e, c in a.items()}


def squarefree(f: Mapping[int, Fraction]) -> Poly:
    """f / gcd(f, f'): same roots, each simple."""
    f = normalize(f)
    if _degree(f) <= 0:
        return f
    return _divmod(f, gcd(f, derivative(f)))[0]


def sturm_sequence(f: Mapping[int, Fraction]) -> list[Poly]:
    sequence = [normalize(f), derivative(f)]
    while sequence[-1]:
        remainder = _divmod(sequence[-2], sequence[-1])[1]
        sequence.append({e: -c for e, c in remainder.items()})
    return sequence[:-1]


def _sign_changes(sequence: Sequence[Mapping[int, Fraction]], x: Fraction) -> int:
    signs = [v for v in (evaluate(p, x) for p in sequence) if v]
    return sum((a > 0) != (b > 0) for a, b in zip(signs, signs[1:]))


def count_roots(f: Mapping[int, Fraction], low: Fraction, high: Fraction) -> int:
    """Distinct real roots of f in the half-open interval (low, high] (Sturm)."""
    f = normalize(f)
    if not f:
        raise ValueError("the zero polynomial has infinitely many roots")
    sequence = sturm_sequence(f)
    return _sign_changes(sequence, Fraction(low)) - _sign_changes(sequence, Fraction(high))


def isolate_roots(f: Mapping[int, Fraction], low: Fraction = Fraction(0), high: Fraction = Fraction(1)) -> list[dict]:
    """Isolate every root of f in the open interval (low, high).

    Returns, in increasing order, either {"rational": r} for a rational root
    (met at a bisection point or found by the rational-root theorem), or
    {"interval": (a, b)} with exactly one root of the square-free part
    strictly inside and none at the endpoints.
    """
    base = squarefree(f)
    if not base:
        raise ValueError("the zero polynomial has no isolated roots")
    low, high = Fraction(low), Fraction(high)
    rationals = rational_roots(base)
    roots: list[dict] = []
    stack = [(low, high)]
    while stack:
        a, b = stack.pop()
        # Count roots strictly inside (a, b): (a, b] minus a root at b.
        inside = count_roots(base, a, b) - (evaluate(base, b) == 0)
        if inside == 0:
            continue
        if inside == 1:
            exact = [r for r in (rationals or []) if a < r < b]
            roots.append({"rational": exact[0]} if exact else {"interval": (a, b)})
            continue
        middle = (a + b) / 2
        if evaluate(base, middle) == 0:
            roots.append({"rational": middle})
        stack.extend([(middle, b), (a, middle)])
    return sorted(roots, key=lambda r: r.get("rational", r.get("interval", (0, 0))[0]))


def _divisors(value: int) -> list[int]:
    value = abs(value)
    small = [d for d in range(1, int(value ** 0.5) + 1) if value % d == 0]
    return sorted(set(small + [value // d for d in small]))


def rational_roots(f: Mapping[int, Fraction], limit: int = 10 ** 6) -> list[Fraction] | None:
    """All rational roots by the rational-root theorem, or None above ``limit``.

    None means only that the candidate search was not attempted; isolated
    intervals remain exact either way.
    """
    f = normalize(f)
    if not f:
        raise ValueError("the zero polynomial has every rational root")
    from math import lcm
    scale = lcm(*(c.denominator for c in f.values()))
    low = min(f)
    integral = {e - low: int(c * scale) for e, c in f.items()}
    roots = [Fraction(0)] if low > 0 else []
    constant, leading = integral[0], integral[max(integral)]
    if max(abs(constant), abs(leading)) > limit:
        return None
    for p in _divisors(constant):
        for q in _divisors(leading):
            for candidate in (Fraction(p, q), Fraction(-p, q)):
                if candidate not in roots and evaluate(integral, candidate) == 0:
                    roots.append(candidate)
    return sorted(roots)


def vanishes_at(g: Mapping[int, Fraction], root: dict, defining: Mapping[int, Fraction]) -> bool:
    """Exactly decide g(alpha) = 0 for an isolated root of ``defining``."""
    g = normalize(g)
    if "rational" in root:
        return evaluate(g, root["rational"]) == 0
    if not g:
        return True
    a, b = root["interval"]
    common = gcd(squarefree(defining), g)
    if _degree(common) <= 0:
        return False
    return count_roots(common, a, b) - (evaluate(common, b) == 0) > 0


def multiplicity(g: Mapping[int, Fraction], root: dict, defining: Mapping[int, Fraction]) -> int:
    """Order of vanishing of a nonzero g at the root."""
    g, order = normalize(g), 0
    if not g:
        raise ValueError("the zero polynomial has no finite multiplicity")
    while vanishes_at(g, root, defining):
        g, order = derivative(g), order + 1
    return order


def _root_json(root: dict, defining: Mapping[int, Fraction]) -> dict:
    if "rational" in root:
        value = root["rational"]
        return {"rational": f"{value.numerator}/{value.denominator}"}
    a, b = root["interval"]
    poly = squarefree(defining)
    return {"defining_polynomial": [[e, str(c)] for e, c in sorted(poly.items())],
            "isolating_interval": [f"{a.numerator}/{a.denominator}", f"{b.numerator}/{b.denominator}"],
            "note": "square-free defining polynomial; not necessarily minimal"}


def parameter_strata(left: Sequence[Mapping[int, int | Fraction]], right: Sequence[Mapping[int, int | Fraction]]) -> dict:
    """Generic first visible volume, every exceptional q in (0,1), and endpoints."""
    depth = min(len(left), len(right))
    deltas = [sub(left[v], right[v]) for v in range(depth)]
    bound = depth - 1

    def first_at(value: Fraction) -> int | None:
        return next((v for v, d in enumerate(deltas) if evaluate(d, value) != 0), None)

    endpoints = {"0": first_at(Fraction(0)), "1": first_at(Fraction(1))}
    generic = next((v for v, d in enumerate(deltas) if d), None)
    if generic is None:
        return {"bound": bound, "generic_first_volume": None, "exceptional": [], "endpoints": endpoints,
                "status": "agreement of every coefficient through the bound; nothing is claimed beyond it"}
    leading = deltas[generic]
    exceptional = []
    for root in isolate_roots(leading):
        later = next((v for v in range(generic + 1, depth) if not vanishes_at(deltas[v], root, leading)), None)
        exceptional.append({
            "root": _root_json(root, leading),
            "multiplicity_in_leading_discrepancy": multiplicity(leading, root, leading),
            "first_visible_volume": later,
            "status": "visible" if later is not None else f"agreement through volume {bound} at this parameter",
        })
    return {"bound": bound, "generic_first_volume": generic, "exceptional": exceptional, "endpoints": endpoints,
            "status": "complete: every root of the leading discrepancy in (0,1) is isolated"}
