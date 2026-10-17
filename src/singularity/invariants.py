"""Exact cut, spectral and coefficient observations; no graph-isomorphism claims."""

from __future__ import annotations

from collections import Counter
from itertools import combinations

from .graph import Graph, _integer
from .heights import weak_compositions


def binary_cut_profile(graph: Graph) -> dict[tuple[int, int], int]:
    result: Counter[tuple[int, int]] = Counter()
    for mask in range(1 << graph.n):
        size = mask.bit_count()
        cut = sum(((mask >> i) ^ (mask >> j)) & 1 for i, j in graph.edges)
        result[size, cut] += 1
    return dict(sorted(result.items()))


def minimum_cut_profile(graph: Graph) -> tuple[int, dict[int, int]]:
    """Return edge connectivity and side-size counts, including both orientations.

    Exhaustive in n: appropriate to exact small-graph certificates, not a claim
    of a scalable minimum-cut solver.  Disconnected graphs are rejected.
    """
    if graph.n < 2 or not graph.connected:
        raise ValueError("minimum_cut_profile requires a connected graph with n >= 2")
    profile = binary_cut_profile(graph)
    minimum = min(cut for size, cut in profile if 0 < size < graph.n)
    return minimum, {
        size: count for (size, cut), count in profile.items()
        if 0 < size < graph.n and cut == minimum
    }


def laplacian_characteristic_polynomial(graph: Graph) -> tuple[int, ...]:
    """Return det(t I-L) in descending order using exact Newton identities.

    The divisions by k are checked: no floating-point eigensolver or rounded
    numerical characteristic polynomial participates in this computation.
    """
    matrix = graph.laplacian()
    n = graph.n
    power = tuple(tuple(int(i == j) for j in range(n)) for i in range(n))
    traces: list[int] = []
    coefficients = [1]
    for order in range(1, n + 1):
        power = tuple(
            tuple(sum(power[i][t] * matrix[t][j] for t in range(n)) for j in range(n))
            for i in range(n)
        )
        traces.append(sum(power[i][i] for i in range(n)))
        numerator = -sum(
            coefficients[order - j] * traces[j - 1] for j in range(1, order + 1)
        )
        quotient, remainder = divmod(numerator, order)
        if remainder:
            raise ArithmeticError("Newton identity failed exact divisibility")
        coefficients.append(quotient)
    return tuple(coefficients)


def first_difference(
    graph: Graph, other: Graph, max_volume: int
) -> tuple[int, dict[int, int]] | None:
    """Return the first signed local coefficient difference up to a finite bound.

    ``None`` means only that this finite search did not distinguish the graphs.
    The q-polynomial is formal: a specialization can erase the discrepancy.
    """
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    for volume in range(max_volume + 1):
        difference = Counter(graph.energy(a) for a in weak_compositions(volume, graph.n))
        difference.subtract(
            Counter(other.energy(a) for a in weak_compositions(volume, other.n))
        )
        row = {energy: count for energy, count in sorted(difference.items()) if count}
        if row:
            return volume, row
    return None
