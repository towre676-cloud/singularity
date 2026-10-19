"""Certified scope for the pole divisor of a fixed-positive-q height series.

Every connected n-vertex graph has a simple pole at EVERY nth root of unity.
For disconnected graphs cancellation by another component is not assumed away:
the full divisor is returned only under an explicit zero-free certificate, or
when all nontrivial components have the same size. See FR01_POLE_DIVISORS.md.

The Gaussian box is exact in a cyclotomic ring with a rational absolute tail.
It is a finite approximation, not a finite-prefix completeness test.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product

from .conductor import CyclotomicRing
from .graph import Graph


def _natural(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer at least {minimum}")
    return value


def _parameter(q):
    if isinstance(q, (bool, float)):
        raise ValueError("q must be an exact rational strictly between zero and one")
    q = Fraction(q)
    if not 0 < q < 1:
        raise ValueError("q must be strictly between zero and one")
    return q


def theta_upper(q, terms=8):
    """Rational upper bound for sum_{k in Z} q**(k*k)."""
    q = _parameter(q)
    terms = _natural(terms, "terms")
    partial = 1 + 2 * sum((q ** (k * k) for k in range(1, terms + 1)), Fraction())
    return partial + 2 * q ** ((terms + 1) ** 2) / (1 - q ** (2 * terms + 3))


def uniform_zero_free(q, max_component_size, terms=8):
    """Sufficient certificate for every connected component of bounded size.

    The strict condition is theta_upper(q)**(N-1) < 2. A False result is a
    refusal to certify; it does NOT assert that a unit-circle zero exists.
    """
    size = _natural(max_component_size, "max_component_size", 1)
    return theta_upper(q, terms) ** (size - 1) < 2


def _sizes(component_sizes):
    sizes = tuple(component_sizes)
    if not sizes:
        raise ValueError("at least one component is required")
    for size in sizes:
        _natural(size, "component size", 1)
    return sizes


def divisor_sum_profile(component_sizes):
    """The candidate pole profile p_d=sum_{d|m} b_m, not an unconditional claim."""
    sizes = _sizes(component_sizes)
    return {d: sum(m % d == 0 for m in sizes) for d in range(1, max(sizes) + 1)}


def recover_component_sizes(pole_orders):
    """Invert a complete, independently justified primitive-root pole profile.

    Keys must be every integer 1,...,N. Values are nonnegative exact integers.
    This operation cannot certify that supplied orders are analytic pole data.
    """
    orders = dict(pole_orders)
    if not orders or set(orders) != set(range(1, max(orders) + 1)):
        raise ValueError("pole profile must have all keys 1,...,N")
    for d, value in orders.items():
        _natural(d, "root order", 1)
        _natural(value, "pole multiplicity")
    counts = {}
    for m in range(max(orders), 0, -1):
        count = orders[m] - sum(counts.get(k, 0) for k in range(2 * m, max(orders) + 1, m))
        if count < 0:
            raise ValueError("profile is inconsistent with component-size multiplicities")
        counts[m] = count
    return {m: counts[m] for m in sorted(counts) if counts[m]}


def pole_order_certificate(graph: Graph, q, terms=8):
    """Return only justified pole orders, with unknown orders made explicit.

    All primitive roots of a listed order have the stated multiplicity in
    the certified cases. General-q cancellations outside those cases remain
    unresolved: no numerical sample is promoted to a noncancellation proof.
    """
    q = _parameter(q)
    sizes = tuple(len(component) for component in graph.components())
    proposed = divisor_sum_profile(sizes)
    nontrivial = {size for size in sizes if size > 1}
    if len(sizes) == 1:
        reason = "connected anchored-Gaussian positivity"
        complete = True
    elif len(nontrivial) <= 1:
        reason = "one common nontrivial component size; isolated factors never vanish"
        complete = True
    elif uniform_zero_free(q, max(sizes), terms):
        reason = "uniform spanning-tree theta bound excludes every unit-circle numerator zero"
        complete = True
    else:
        reason = "off-denominator component zeros not excluded"
        complete = False
    certified = dict(proposed) if complete else {d: 0 for d, order in proposed.items() if order == 0}
    certified[1] = len(sizes)
    return {"component_sizes": sizes, "q": q, "complete": complete,
            "reason": reason, "orders": certified,
            "unknown_orders": tuple(d for d in proposed if d not in certified),
            "theta_upper": theta_upper(q, terms)}


@dataclass(frozen=True)
class GaussianBox:
    """Exact cyclotomic partial sum and rigorous absolute error bound."""
    coefficients: tuple[Fraction, ...]
    absolute_error: Fraction
    profiles: int
    order: int
    cutoff: int


def anchored_gaussian_box(graph: Graph, q, order, cutoff, max_profiles=1_000_000):
    """Enclose B_G(zeta,q) at a root with zeta**graph.n=1.

    Coordinates are differences on a rooted spanning tree, truncated in a
    symmetric box. The tail is bounded by a product of scalar theta bounds.
    Ring coefficients represent the principal primitive root exp(2*pi*i/order).
    """
    q = _parameter(q)
    order = _natural(order, "order", 1)
    cutoff = _natural(cutoff, "cutoff")
    max_profiles = _natural(max_profiles, "max_profiles", 1)
    if not graph.connected:
        raise ValueError("anchored Gaussian requires a connected graph")
    if graph.n % order:
        raise ValueError("root order must divide the connected graph size")
    profiles = (2 * cutoff + 1) ** (graph.n - 1)
    if profiles > max_profiles:
        raise ValueError(f"Gaussian box has {profiles} profiles; budget is {max_profiles}")
    parent = {0: -1}
    traversal = [0]
    for u in traversal:
        for v in graph.neighbors[u]:
            if v not in parent:
                parent[v] = u
                traversal.append(v)
    ring = CyclotomicRing(order)
    answer = tuple(Fraction() for _ in ring.zero)
    for differences in product(range(-cutoff, cutoff + 1), repeat=graph.n - 1):
        height = [0] * graph.n
        for vertex, difference in zip(traversal[1:], differences):
            height[vertex] = height[parent[vertex]] + difference
        weight = q ** graph.energy(height)
        answer = ring.add(answer, ring.scale(ring.phase(sum(height)), weight))
    dimension = graph.n - 1
    partial_theta = 1 + 2 * sum((q ** (k * k) for k in range(1, cutoff + 1)), Fraction())
    error = theta_upper(q, max(cutoff, 8)) ** dimension - partial_theta ** dimension
    return GaussianBox(tuple(answer), error, profiles, order, cutoff)
