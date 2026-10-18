"""The pendant-cycle family with exactly controlled visibility depth (SNG-F36).

G(l, j) is the cycle C_{2l} on 0..2l-1 with a leaf 2l attached at vertex 0
and a leaf 2l+1 attached at vertex j.  For 2 <= p < l the pair
(G(l, p), G(l, l)) first differs at volume p + 1, with

    [x^(p+1)](L_{G(l,p)} - L_{G(l,l)}) = q^2 (1-q)^2 (1-q^2)^p,

and its complete binary-sector difference is

    q^2 (1-q)^2 (1-q^2)^p z^(p+1) (1-z)^2 U_(l-p)(z, q)^2,

where U_k = (lambda_+^k - lambda_-^k)/(lambda_+ - lambda_-) for the
eigenvalues of [[1, q sqrt z], [q sqrt z, z]], i.e. U_0 = 0, U_1 = 1,
U_k = (1+z) U_(k-1) - z (1-q^2) U_(k-2).
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from itertools import combinations, permutations

from .graph import Graph, _integer
from .polynomials import from_factors

Bivariate = dict[tuple[int, int], int]  # (z exponent, q exponent) -> integer


def pendant_cycle(half_length: int, distance: int) -> Graph:
    """C_{2l} with leaves at vertices 0 and ``distance`` (1 <= distance <= l)."""
    l = _integer(half_length, "half_length", minimum=2)
    j = _integer(distance, "distance", minimum=1)
    if j > l:
        raise ValueError("the attachment distance on C_{2l} is at most l")
    n = 2 * l
    return Graph(n + 2, [(i, (i + 1) % n) for i in range(n)] + [(0, n), (j, n + 1)])


def _mul(a: Bivariate, b: Bivariate) -> Bivariate:
    out: Counter[tuple[int, int]] = Counter()
    for (z1, q1), c1 in a.items():
        for (z2, q2), c2 in b.items():
            out[z1 + z2, q1 + q2] += c1 * c2
    return {k: v for k, v in sorted(out.items()) if v}


def _add(a: Bivariate, b: Bivariate, scale: int = 1) -> Bivariate:
    out = Counter(a)
    for k, v in b.items():
        out[k] += scale * v
    return {k: v for k, v in sorted(out.items()) if v}


def chebyshev_u(k: int) -> Bivariate:
    """U_k in Z[z, q]: U_0 = 0, U_1 = 1, U_k = (1+z) U_{k-1} - z(1-q^2) U_{k-2}."""
    k = _integer(k, "k", minimum=0)
    previous, current = {}, {(0, 0): 1}
    if k == 0:
        return {}
    trace = {(0, 0): 1, (1, 0): 1}
    determinant = {(1, 0): 1, (1, 2): -1}
    for _ in range(k - 1):
        previous, current = current, _add(_mul(trace, current), _mul(determinant, previous), -1)
    return current


def binary_discrepancy_closed_form(half_length: int, distance: int) -> Bivariate:
    """q^2 (1-q)^2 (1-q^2)^p z^(p+1) (1-z)^2 U_(l-p)^2 as {(z, q): coefficient}."""
    l, p = half_length, distance
    if not 1 <= p <= l:
        raise ValueError("need 1 <= distance <= half_length")
    result: Bivariate = {(p + 1, 2): 1}
    for factor in ([(0, 0, 1), (0, 1, -1)],) * 2 + ([(0, 0, 1), (0, 2, -1)],) * p + ([(0, 0, 1), (1, 0, -1)],) * 2:
        result = _mul(result, {(z, q): c for z, q, c in factor})
    u = chebyshev_u(l - p)
    return _mul(result, _mul(u, u))


def binary_discrepancy_enumerated(half_length: int, distance: int) -> Bivariate:
    """Sum over all vertex subsets S of z^|S| (q^cut_G(S) - q^cut_H(S)), H = G(l, l)."""
    out: Counter[tuple[int, int]] = Counter()
    for graph, sign in ((pendant_cycle(half_length, distance), 1), (pendant_cycle(half_length, half_length), -1)):
        for mask in range(1 << graph.n):
            cut = sum(((mask >> u) ^ (mask >> v)) & 1 for u, v in graph.edges)
            out[mask.bit_count(), cut] += sign
    return {k: v for k, v in sorted(out.items()) if v}


def first_discrepancy(distance: int) -> dict[int, Fraction]:
    """delta_p(q) = q^2 (1-q)^2 (1-q^2)^p."""
    p = _integer(distance, "distance", minimum=1)
    return from_factors(1, 2, [(1, 2), (2, p)])


def optimal_probe(distance: int) -> dict[str, object]:
    """The maximizer of delta_p on (0,1): the root of (p+2) q^2 + q - 1, q* = 2/(1+sqrt(4p+9))."""
    from .parameters import isolate_roots

    p = _integer(distance, "distance", minimum=1)
    defining = {0: Fraction(-1), 1: Fraction(1), 2: Fraction(p + 2)}
    (root,) = isolate_roots(defining)
    return {"distance": p, "defining_polynomial": defining, "root": root,
            "value_at_one_half": Fraction(3 ** p, 4 ** (p + 2))}


def decorated_deck(graph: Graph, size: int) -> Counter:
    """Multiset of degree-decorated induced subgraphs on all vertex subsets of a size.

    The canonical form is the lexicographically least (degree labels, adjacency)
    over all orderings of the subset; intended for subsets of at most ~7 vertices.
    """
    size = _integer(size, "size", minimum=0)
    edges = set(graph.edges)
    deck: Counter = Counter()
    for subset in combinations(range(graph.n), size):
        best = None
        for order in permutations(subset):
            key = (tuple(graph.degrees[v] for v in order),
                   tuple(int((min(order[i], order[k]), max(order[i], order[k])) in edges)
                         for i in range(size) for k in range(i + 1, size)))
            if best is None or key < best:
                best = key
        deck[best] += 1
    return deck
