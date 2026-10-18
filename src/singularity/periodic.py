"""Periodic edge phases: residue numerators, palindromes and a finite cutoff.

Model
-----
A periodic model consists of a labeled simple graph ``G`` on ``n`` vertices
(isolated vertices and disconnected graphs are allowed), a modulus ``M >= 1``
and an integer phase exponent ``a_e`` for every edge (default ``1``; zero and
negative exponents are allowed).  With ``t_e = zeta_M**a_e`` in the exact ring
``Z[t]/Phi_M(t)`` the series is

    F(x) = sum_{h in N^n} x^{|h|} prod_{uv in E} t_uv^{(h_u - h_v)^2}.

Theorem (sufficient periodic cutoff)
------------------------------------
Let ``K = n(M - 1)``.  Then ``F = P(x)/(1 - x^M)^n`` with
``P(x) = sum_{rho in {0..M-1}^n} x^{|rho|} prod_e t_e^{(rho_u-rho_v)^2}``,
``deg P <= K`` and ``P_k = P_{K-k}``.  Consequently, two models with the same
``n`` and ``M`` whose series agree through volume ``floor(K/2)`` have equal
series in every volume.

Proof.  (1) Since ``(rho + M b)^2 = rho^2 (mod M)`` and ``t_e^M = 1``, writing
``h = rho + M b`` factors ``F`` as ``P(x) * (1 - x^M)^(-n)``.  (2) The
complement ``rho -> (M-1) - rho`` negates every edge difference, so it fixes
every squared difference, and sends ``|rho|`` to ``K - |rho|``; hence ``P`` is
palindromic of degree ``K``.  (3) ``P = F (1 - x^M)^n`` is triangular, so
``F_0..F_k`` determine ``P_0..P_k``; agreement through ``floor(K/2)``
determines the low half of ``P``, the palindrome determines the rest, and ``P``
determines ``F``.

Scope.  The cutoff is sufficient, not a sharpness claim: smaller cutoffs may
suffice for particular families, and nothing here bounds first discrepancies
from below.  The palindrome uses only squared edge-difference weights; unary or
vertex weights are not translation-symmetric under complementation and are not
covered.  The finite numerator is a residue-box computation with an explicit
``M**n`` work budget; a budget refusal is a resource limit, not a mathematical
statement.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import comb
from typing import Mapping, Optional

from .conductor import CyclotomicRing
from .graph import Graph

__all__ = [
    "PeriodicModel",
    "PeriodicComparison",
    "residue_numerator",
    "series_from_numerator",
    "direct_coefficients",
    "is_palindromic",
    "periodic_cutoff",
    "compare_models",
]


def _exact_int(value: object, name: str, *, minimum: Optional[int] = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer (not bool or float)")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


@dataclass(frozen=True, init=False)
class PeriodicModel:
    """Validated graph, modulus and per-edge integer phase exponents.

    ``phases`` is stored as a tuple ``((edge, exponent), ...)`` covering every
    edge in sorted order.  Exponents are kept as given (not reduced modulo
    ``M``), so two models with exponents differing by multiples of ``M`` are
    distinct objects with equal series.
    """

    graph: Graph
    modulus: int
    phases: tuple[tuple[tuple[int, int], int], ...]

    def __init__(self, graph: Graph, modulus: int,
                 phases: Optional[Mapping[tuple[int, int], int]] = None) -> None:
        if not isinstance(graph, Graph):
            raise TypeError("graph must be a singularity.graph.Graph")
        modulus = _exact_int(modulus, "modulus", minimum=1)
        if phases is None:
            phases = {}
        if not isinstance(phases, Mapping):
            raise TypeError("phases must be a mapping from edges to integers")
        edge_set = set(graph.edges)
        for edge, exponent in phases.items():
            if not isinstance(edge, tuple) or len(edge) != 2:
                raise ValueError(f"phase key {edge!r} must be a sorted edge tuple")
            if edge not in edge_set:
                raise ValueError(f"phase key {edge!r} is not an edge of the graph")
            _exact_int(exponent, f"phase exponent on {edge}")
        stored = tuple((edge, phases.get(edge, 1)) for edge in graph.edges)
        object.__setattr__(self, "graph", graph)
        object.__setattr__(self, "modulus", modulus)
        object.__setattr__(self, "phases", stored)

    @property
    def n(self) -> int:
        return self.graph.n

    @property
    def ring(self) -> CyclotomicRing:
        return CyclotomicRing(self.modulus)

    @property
    def K(self) -> int:
        return self.n * (self.modulus - 1)

    def phase_exponent(self, heights) -> int:
        """Return ``sum_e a_e (h_u - h_v)^2`` as an exact integer."""
        return sum(a * (heights[u] - heights[v]) ** 2 for (u, v), a in self.phases)


def _check_model(model: object) -> PeriodicModel:
    if not isinstance(model, PeriodicModel):
        raise TypeError("model must be a PeriodicModel")
    return model


def residue_numerator(model: PeriodicModel, max_profiles: int = 1_000_000) -> list:
    """Return ``P_0..P_K`` with ``F = P/(1-x^M)^n``; work is ``M**n`` profiles."""
    model = _check_model(model)
    max_profiles = _exact_int(max_profiles, "max_profiles", minimum=0)
    profiles = model.modulus ** model.n
    if profiles > max_profiles:
        raise ValueError(f"residue box has {profiles} profiles; budget is {max_profiles}")
    ring = model.ring
    M = model.modulus
    phase_table = [ring.phase(j) for j in range(M)]
    numerator = [ring.zero for _ in range(model.K + 1)]
    for rho in product(range(M), repeat=model.n):
        k = sum(rho)
        numerator[k] = ring.add(numerator[k], phase_table[model.phase_exponent(rho) % M])
    return numerator


def series_from_numerator(model: PeriodicModel, numerator, max_volume: int) -> list:
    """Expand ``P/(1-x^M)^n`` into ``F_0..F_R`` using ``C(m+n-1, n-1)``."""
    model = _check_model(model)
    max_volume = _exact_int(max_volume, "max_volume", minimum=0)
    ring = model.ring
    numerator = [tuple(c) for c in numerator]
    for c in numerator:
        if len(c) != ring.degree:
            raise ValueError("numerator entries must be elements of the model's ring")
    M, n = model.modulus, model.n
    out = [ring.zero for _ in range(max_volume + 1)]
    for j, coefficient in enumerate(numerator):
        m = 0
        while j + M * m <= max_volume:
            k = j + M * m
            out[k] = ring.add(out[k], ring.scale(coefficient, comb(m + n - 1, n - 1)))
            m += 1
    return out


def _weak_compositions(total: int, parts: int):
    if parts == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in _weak_compositions(total - first, parts - 1):
            yield (first,) + rest


def direct_coefficients(model: PeriodicModel, max_volume: int,
                        max_profiles: int = 1_000_000) -> list:
    """Independent oracle: enumerate every ``h`` with ``|h| = k <= R``.

    No residue splitting is used; the exponent ``sum_e a_e (h_u-h_v)^2`` is
    computed from the full heights and only then evaluated as a power of
    ``zeta_M``.  The work is ``C(R+n, n)`` height profiles.
    """
    model = _check_model(model)
    max_volume = _exact_int(max_volume, "max_volume", minimum=0)
    max_profiles = _exact_int(max_profiles, "max_profiles", minimum=0)
    n = model.n
    profiles = comb(max_volume + n, n)
    if profiles > max_profiles:
        raise ValueError(f"direct enumeration has {profiles} profiles; budget is {max_profiles}")
    ring = model.ring
    out = []
    for k in range(max_volume + 1):
        total = ring.zero
        for h in _weak_compositions(k, n):
            total = ring.add(total, ring.phase(model.phase_exponent(h)))
        out.append(total)
    return out


def is_palindromic(numerator) -> bool:
    values = [tuple(c) for c in numerator]
    return values == values[::-1]


def periodic_cutoff(n: int, modulus: int) -> int:
    """Sufficient agreement cutoff ``floor(n(M-1)/2)``; not a sharpness claim."""
    n = _exact_int(n, "n", minimum=1)
    modulus = _exact_int(modulus, "modulus", minimum=1)
    return n * (modulus - 1) // 2


@dataclass(frozen=True)
class PeriodicComparison:
    """Outcome of :func:`compare_models`.

    ``equal`` is a certificate of full-series equality by the cutoff theorem.
    When ``equal`` is false, ``first_difference`` is the first volume at which
    the series differ and the coefficients are the two exact ring elements.
    """

    cutoff: int
    equal: bool
    first_difference: Optional[int] = None
    first_coefficient: Optional[tuple] = None
    second_coefficient: Optional[tuple] = None


def compare_models(first: PeriodicModel, second: PeriodicModel,
                   max_profiles: int = 1_000_000) -> PeriodicComparison:
    """Compare two models with equal ``n`` and ``M`` through the cutoff."""
    first = _check_model(first)
    second = _check_model(second)
    if first.n != second.n or first.modulus != second.modulus:
        raise ValueError("compare_models requires equal n and modulus")
    cutoff = periodic_cutoff(first.n, first.modulus)
    p1 = residue_numerator(first, max_profiles)
    p2 = residue_numerator(second, max_profiles)
    f1 = series_from_numerator(first, p1, cutoff)
    f2 = series_from_numerator(second, p2, cutoff)
    for k, (a, b) in enumerate(zip(f1, f2)):
        if a != b:
            return PeriodicComparison(cutoff, False, k, a, b)
    if p1 != p2:  # pragma: no cover - excluded by the theorem
        raise ArithmeticError("series agree through the cutoff but numerators differ")
    return PeriodicComparison(cutoff, True)
