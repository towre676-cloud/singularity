"""Exact labeled height populations and their formal-series coefficients.

Meanings, truncation and normalization conventions are frozen in
docs/specifications/COEFFICIENTS-v1.md.  Every ``max_volume`` is inclusive and
returns a complete finite prefix; normalization removes one global common
translation, also for disconnected graphs.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterator, Sequence

from .graph import Graph, _integer


def weak_compositions(total: int, length: int) -> Iterator[tuple[int, ...]]:
    """Yield weak compositions in lexicographic order, with no quotienting."""
    total = _integer(total, "total", minimum=0)
    length = _integer(length, "length", minimum=0)
    if length == 0:
        if total == 0:
            yield ()
        return
    if length == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in weak_compositions(total - first, length - 1):
            yield (first,) + rest


def local_coefficients(graph: Graph, max_volume: int) -> list[dict[int, int]]:
    """Return [x^m] L_G(x,q) as sparse integer q-polynomials for m <= M.

    Row m maps energy to the number of labeled profiles of volume m.
    """
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    return [
        dict(sorted(Counter(graph.energy(a) for a in weak_compositions(m, graph.n)).items()))
        for m in range(max_volume + 1)
    ]


def normalize_local_coefficients(
    coefficients: Sequence[dict[int, int]], n: int
) -> list[dict[int, int]]:
    """Multiply a truncated formal x-series by 1-x^n exactly."""
    n = _integer(n, "n", minimum=1)
    output = []
    for m, coefficient in enumerate(coefficients):
        row = Counter(coefficient)
        if m >= n:
            row.subtract(coefficients[m - n])
        output.append(dict(sorted((e, c) for e, c in row.items() if c)))
    return output


def normalized_coefficients(graph: Graph, max_volume: int) -> list[dict[int, int]]:
    """Return coefficients of B_G=(1-x^n)L_G, with global min(a)=0.

    A component of a disconnected graph may remain entirely positive; see
    ``componentwise_normalized_coefficients`` for the other quotient.
    """
    return normalize_local_coefficients(local_coefficients(graph, max_volume), graph.n)


def componentwise_normalized_coefficients(graph: Graph, max_volume: int) -> list[dict[int, int]]:
    """Count profiles whose minimum is zero on every connected component.

    This is a different quotient from ``normalized_coefficients``: it removes
    one translation per component, so it equals the product of the components'
    B series.  For a connected graph the two coincide.  See
    docs/specifications/COEFFICIENTS-v1.md, section 6.
    """
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    components = graph.components()
    rows: list[Counter[int]] = [Counter() for _ in range(max_volume + 1)]
    for volume in range(max_volume + 1):
        for a in weak_compositions(volume, graph.n):
            if all(min(a[i] for i in component) == 0 for component in components):
                rows[volume][graph.energy(a)] += 1
    return [dict(sorted(row.items())) for row in rows]


def marked_coefficients(graph: Graph, max_volume: int) -> dict[tuple[int, int, int], int]:
    """Count global minimum-zero labeled profiles by (volume, energy, span)."""
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    result: Counter[tuple[int, int, int]] = Counter()
    for volume in range(max_volume + 1):
        for a in weak_compositions(volume, graph.n):
            if min(a) == 0:
                result[volume, graph.energy(a), max(a)] += 1
    return dict(sorted(result.items()))


def normalize_heights(a: Sequence[int]) -> tuple[int, ...]:
    """Choose the unique min-zero representative of a nonempty integer tuple."""
    values = tuple(a)
    if not values:
        raise ValueError("normalization requires at least one height")
    for value in values:
        _integer(value, "height")
    bottom = min(values)
    return tuple(value - bottom for value in values)


def threshold_sets(a: Sequence[int]) -> tuple[frozenset[int], ...]:
    """Return S_1,...,S_h for a nonnegative height assignment; sets may repeat."""
    values = tuple(_integer(value, "height", minimum=0) for value in a)
    if not values:
        raise ValueError("threshold sets require at least one height")
    return tuple(
        frozenset(i for i, value in enumerate(values) if value >= level)
        for level in range(1, max(values) + 1)
    )


def nested_energy(graph: Graph, a: Sequence[int]) -> int:
    """Compute energy by nested cut sizes and multiple-boundary cross terms.

    This second formula is useful for replay: it does not call graph.energy.
    """
    values = graph.validate_heights(a, nonnegative=True)
    sets = threshold_sets(values)
    boundary = sum(graph.cut_size(subset) for subset in sets)
    cross = 0
    for r, outer in enumerate(sets):
        for inner in sets[r + 1 :]:
            cross += sum(
                (i in inner and j not in outer) or (j in inner and i not in outer)
                for i, j in graph.edges
            )
    return boundary + 2 * cross
