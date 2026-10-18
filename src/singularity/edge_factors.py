"""Polynomial edge factors for exact observation maps.

For each edge e use a separate variable t_e and weight a height profile h by
prod_e t_e ** (h_u-h_v)^2. Setting every t_e=q recovers the ordinary local
series. These are factors (e.g. q**w), not polynomially varying energy weights.
Sparse monomials follow graph.edges order. Only small explicit populations
are enumerated; no Noetherian stabilization bound is claimed or computed.
"""
from collections import Counter, defaultdict
from fractions import Fraction
from math import comb, prod

from .graph import Graph, _integer
from .heights import weak_compositions


def edge_factor_moments(graph: Graph, max_volume: int, *, profile_budget: int = 100000) -> dict:
    """Map (total height, squared height) to an edge-factor polynomial.

    A polynomial maps exponent tuples in graph.edges order to integer counts.
    The budget counts all labeled profiles in the complete requested prefix.
    """
    R = _integer(max_volume, 'max_volume', minimum=0)
    budget = _integer(profile_budget, 'profile_budget', minimum=0)
    count = comb(R + graph.n, graph.n)
    if count > budget:
        raise ValueError(f'prefix requires {count} profiles; budget is {budget}')
    out = defaultdict(Counter)
    for r in range(R + 1):
        for heights in weak_compositions(r, graph.n):
            key = (r, sum(h*h for h in heights))
            exponents = tuple((heights[u]-heights[v])**2 for u, v in graph.edges)
            out[key][exponents] += 1
    return {k: dict(sorted(row.items())) for k, row in sorted(out.items())}


def edge_factor_coefficients(graph: Graph, max_volume: int, *, profile_budget: int = 100000) -> list:
    """Complete unmarked prefix as edge-factor polynomials, through R inclusive."""
    marked = edge_factor_moments(graph, max_volume, profile_budget=profile_budget)
    out = [Counter() for _ in range(max_volume + 1)]
    for (r, _), row in marked.items():
        out[r].update(row)
    return [dict(sorted(row.items())) for row in out]


def _values(values):
    values = tuple(values)
    if any(isinstance(v, bool) or not isinstance(v, (int, Fraction)) for v in values):
        raise TypeError('edge factors must be integers or Fractions')
    return tuple(map(Fraction, values))


def evaluate_factors(polynomial: dict, values) -> Fraction:
    """Exact evaluation, including zero factors and empty-edge monomials."""
    values = _values(values)
    if any(len(m) != len(values) for m in polynomial):
        raise ValueError('edge-factor dimension does not match polynomial')
    return sum((c * prod(t**e for t, e in zip(values, m))
                for m, c in polynomial.items()), Fraction(0))


def factor_gradient(polynomial: dict, values) -> tuple:
    """Exact polynomial Jacobian row; valid also at zero edge factors."""
    values = _values(values)
    if any(len(m) != len(values) for m in polynomial):
        raise ValueError('edge-factor dimension does not match polynomial')
    return tuple(sum((c * m[j] * prod(t**(e-(i == j)) for i, (t, e) in enumerate(zip(values, m)))
                      for m, c in polynomial.items() if m[j]), Fraction(0))
                 for j in range(len(values)))
