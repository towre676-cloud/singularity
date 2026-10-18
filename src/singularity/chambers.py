"""Order-chamber enumeration: a third independent coefficient representation.

Every profile a has one order pi: vertices sorted by (height, label).  Its
gaps are d_0 = a[pi_0] and d_j = a[pi_j] - a[pi_{j-1}] for 1 <= j < n.
They satisfy d_j >= 0, and d_j >= 1 whenever pi_{j-1} > pi_j (a label
descent cannot sit inside a tied block).  Conversely each permutation with
such gaps gives exactly one profile (SNG-F29), so the half-open chambers
partition the nonnegative profiles; summing closed weak-order cones would
count tied profiles repeatedly.

In gap coordinates, with T_j = {pi_j, ..., pi_{n-1}} the top j-suffix,

    volume = n d_0 + sum_{j>=1} (n - j) d_j,
    span   = sum_{j>=1} d_j,          (on d_0 = 0, the normalized profiles)
    energy = sum_{i,j>=1} Q_ij d_i d_j,
    Q_jj = c(T_j),  Q_ij = Q_ji = e(T_max(i,j), V minus T_min(i,j)).

The enumeration visits n! permutations and the gap vectors inside each
chamber; it never composes height tuples, calls ``Graph.energy`` or uses the
weak-composition or chain engines.  Its factorial cost limits it to small n.
"""

from __future__ import annotations

from collections import Counter
from itertools import permutations
from typing import Iterator, Sequence

from .graph import Graph, _integer


def gap_form(graph: Graph, order: Sequence[int]) -> tuple[tuple[int, ...], ...]:
    """Return Q indexed by gaps 1..n-1 (row/column 0 unused, all zero).

    An edge at positions p < q of ``order`` crosses gaps p+1..q, contributing
    one to Q_ij for every pair of crossed gaps.
    """
    order = _permutation(graph.n, order)
    position = {v: k for k, v in enumerate(order)}
    q = [[0] * graph.n for _ in range(graph.n)]
    for u, v in graph.edges:
        low, high = sorted((position[u], position[v]))
        for i in range(low + 1, high + 1):
            for j in range(low + 1, high + 1):
                q[i][j] += 1
    return tuple(tuple(row) for row in q)


def _permutation(n: int, order: Sequence[int]) -> tuple[int, ...]:
    order = tuple(order)
    if sorted(order) != list(range(n)) or not all(isinstance(v, int) and not isinstance(v, bool) for v in order):
        raise ValueError("order must be a permutation of the vertices")
    return order


def descents(order: Sequence[int]) -> tuple[int, ...]:
    """Minimum gap d_j: 1 at a label descent, else 0 (index 0 unused)."""
    return (0,) + tuple(int(order[j - 1] > order[j]) for j in range(1, len(order)))


def chamber_of(a: Sequence[int]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Return the unique (order, gaps) of a nonnegative profile."""
    values = tuple(_integer(v, "height", minimum=0) for v in a)
    if not values:
        raise ValueError("a profile needs at least one vertex")
    order = tuple(sorted(range(len(values)), key=lambda v: (values[v], v)))
    gaps = (values[order[0]],) + tuple(values[order[j]] - values[order[j - 1]] for j in range(1, len(order)))
    return order, gaps


def chamber_profile(order: Sequence[int], gaps: Sequence[int]) -> tuple[int, ...]:
    """Reconstruct the profile of a chamber point; used only for checks."""
    order = _permutation(len(order), order)
    gaps = tuple(_integer(g, "gap", minimum=0) for g in gaps)
    if len(gaps) != len(order):
        raise ValueError("one gap per position is required")
    minimum = descents(order)
    if any(g < m for g, m in zip(gaps, minimum)):
        raise ValueError("a label descent requires a positive gap")
    a = [0] * len(order)
    height = 0
    for k, vertex in enumerate(order):
        height += gaps[k]
        a[vertex] = height
    return tuple(a)


def _gap_vectors(n: int, minimum: Sequence[int], budget: int, first: int) -> Iterator[tuple[int, ...]]:
    """Gaps d_first..d_{n-1} with d_j >= minimum[j] and sum (n-j) d_j <= budget."""
    if first == n:
        yield ()
        return
    weight = n - first
    lowest = minimum[first]
    reserve = sum((n - j) * minimum[j] for j in range(first + 1, n))
    for value in range(lowest, (budget - reserve) // weight + 1 if budget >= reserve else lowest):
        for rest in _gap_vectors(n, minimum, budget - weight * value, first + 1):
            yield (value,) + rest


def chamber_marked_coefficients(graph: Graph, max_volume: int) -> dict[tuple[int, int, int], int]:
    """(volume, energy, span) counts of minimum-zero profiles via chambers (d_0 = 0)."""
    return dict(sorted(_histogram(graph, max_volume, normalized=True).items()))


def chamber_local_coefficients(graph: Graph, max_volume: int) -> list[dict[int, int]]:
    """[x^m] L_G for m <= R via chambers with every d_0 >= 0."""
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    rows: list[Counter[int]] = [Counter() for _ in range(max_volume + 1)]
    for (volume, energy, _), count in _histogram(graph, max_volume, normalized=False).items():
        rows[volume][energy] += count
    return [dict(sorted(row.items())) for row in rows]


def _histogram(graph: Graph, max_volume: int, normalized: bool) -> Counter:
    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    n = graph.n
    result: Counter[tuple[int, int, int]] = Counter()
    for order in permutations(range(n)):
        q = gap_form(graph, order)
        minimum = descents(order)
        for upper in _gap_vectors(n, minimum, max_volume, 1):
            gaps = (0,) + upper
            base_volume = sum((n - j) * gaps[j] for j in range(1, n))
            energy = sum(q[i][j] * gaps[i] * gaps[j] for i in range(1, n) for j in range(1, n))
            span = sum(upper)
            for d0 in range(0, 1 if normalized else (max_volume - base_volume) // n + 1):
                # Span is a translation invariant; for d_0 > 0 the key keeps
                # max - min, and only the local projection uses those cells.
                result[base_volume + n * d0, energy, span] += 1
    return result
