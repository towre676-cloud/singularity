"""Independent coefficient enumeration by weakly nested level chains.

A minimum-zero profile of span h is the same object as a chain

    S_1 >= S_2 >= ... >= S_h,   V > S_1,   S_h nonempty,

with repetitions allowed (SNG-F09).  This module generates those chains as
its primary search objects: it never produces a height tuple in order to find
the next chain, and it never calls ``Graph.energy`` or the weak-composition
engine in ``heights.py``.  Volume is the sum of level sizes and energy is the
nested-boundary formula of SNG-F10,

    E = sum_t c(S_t) + 2 * sum_{r<t} e(S_t, V minus S_r),

accumulated as each level is appended.  The empty chain is the all-zero
profile.  Heights are reconstructed only by ``chain_heights`` for output
checks.

Sets are integer bit masks over the original labels.  Every nonempty level
costs at least one unit of volume, so chain length never exceeds the volume
bound and the search is finite for every finite bound.
"""

from __future__ import annotations

from collections import Counter
from math import comb
from typing import Iterator, Sequence

from .graph import Graph, _integer

Chain = tuple[int, ...]


def _edge_masks(graph: Graph) -> tuple[tuple[int, int], ...]:
    return tuple((1 << u, 1 << v) for u, v in graph.edges)


def _submasks(mask: int) -> Iterator[int]:
    """Yield the nonempty submasks of ``mask`` in decreasing integer order."""
    sub = mask
    while sub:
        yield sub
        sub = (sub - 1) & mask


def level_chains(n: int, max_volume: int, *, allow_repeats: bool = True) -> Iterator[Chain]:
    """Yield every weakly nested chain of total size at most ``max_volume``.

    The first level is a nonempty proper subset of ``{0,...,n-1}``; each later
    level is a nonempty subset of its predecessor.  ``allow_repeats=False``
    forbids equal consecutive levels.  That restricted population is not the
    height population: it exists only to expose profiles with height gaps.
    """
    n = _integer(n, "n", minimum=1)
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    if not isinstance(allow_repeats, bool):
        raise TypeError("allow_repeats must be a boolean")
    full = (1 << n) - 1
    yield ()

    def extend(prefix: Chain, outer: int, remaining: int) -> Iterator[Chain]:
        for level in _submasks(outer):
            if not allow_repeats and level == outer:
                continue
            size = level.bit_count()
            if size <= remaining:
                chain = prefix + (level,)
                yield chain
                yield from extend(chain, level, remaining - size)

    for first in range(1, full):
        size = first.bit_count()
        if size <= max_volume:
            yield (first,)
            yield from extend((first,), first, max_volume - size)


def _cut(edges: Sequence[tuple[int, int]], level: int) -> int:
    return sum(bool(level & u) != bool(level & v) for u, v in edges)


def _inner_to_outside(edges: Sequence[tuple[int, int]], inner: int, outer: int) -> int:
    """Count edges joining ``inner`` to the complement of ``outer``."""
    return sum(
        (bool(inner & u) and not outer & v) or (bool(inner & v) and not outer & u)
        for u, v in edges
    )


def chain_energy(graph: Graph, chain: Sequence[int]) -> int:
    """Evaluate SNG-F10 on a validated chain of bit masks."""
    levels = validate_chain(graph.n, chain)
    edges = _edge_masks(graph)
    energy = sum(_cut(edges, level) for level in levels)
    for r, outer in enumerate(levels):
        for inner in levels[r + 1 :]:
            energy += 2 * _inner_to_outside(edges, inner, outer)
    return energy


def validate_chain(n: int, chain: Sequence[int]) -> Chain:
    """Return ``chain`` as a tuple after checking the nesting conditions."""
    n = _integer(n, "n", minimum=1)
    full = (1 << n) - 1
    levels = tuple(_integer(level, "chain level", minimum=1) for level in chain)
    if levels and levels[0] >= full + 1:
        raise ValueError("chain level uses a vertex outside 0, ..., n-1")
    if levels and levels[0] == full:
        raise ValueError("the first level must be a proper subset")
    for outer, inner in zip(levels, levels[1:]):
        if inner & ~outer:
            raise ValueError("chain levels must be weakly nested")
    return levels


def chain_heights(n: int, chain: Sequence[int]) -> tuple[int, ...]:
    """Reconstruct a_i = #{t : i in S_t}; used only for output checks."""
    levels = validate_chain(n, chain)
    return tuple(sum(level >> i & 1 for level in levels) for i in range(n))


def heights_chain(a: Sequence[int]) -> Chain:
    """Return the threshold chain of a minimum-zero profile as bit masks."""
    values = tuple(_integer(value, "height", minimum=0) for value in a)
    if not values or min(values) != 0:
        raise ValueError("a threshold chain requires a nonempty minimum-zero profile")
    return tuple(
        sum(1 << i for i, value in enumerate(values) if value >= level)
        for level in range(1, max(values) + 1)
    )


def _marked_search(graph: Graph, max_volume: int, allow_repeats: bool = True) -> tuple[Counter, int]:
    """Depth-first chain search with incremental volume and energy charges."""
    full = (1 << graph.n) - 1
    edges = _edge_masks(graph)
    result: Counter[tuple[int, int, int]] = Counter({(0, 0, 0): 1})
    visited = 1

    def extend(levels: list[int], volume: int, energy: int) -> None:
        nonlocal visited
        outer = levels[-1]
        for level in _submasks(outer):
            if not allow_repeats and level == outer:
                continue
            size = level.bit_count()
            if volume + size > max_volume:
                continue
            charge = _cut(edges, level) + 2 * sum(
                _inner_to_outside(edges, level, previous) for previous in levels
            )
            levels.append(level)
            result[volume + size, energy + charge, len(levels)] += 1
            visited += 1
            extend(levels, volume + size, energy + charge)
            levels.pop()

    for first in range(1, full):
        size = first.bit_count()
        if size <= max_volume:
            energy = _cut(edges, first)
            result[size, energy, 1] += 1
            visited += 1
            extend([first], size, energy)
    return result, visited


def chain_marked_coefficients(graph: Graph, max_volume: int) -> dict[tuple[int, int, int], int]:
    """Count minimum-zero profiles by (volume, energy, span) through chains.

    The output has the same meaning and key layout as
    ``heights.marked_coefficients``; that function is an external oracle in
    tests and is not consulted here.
    """
    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    result, _ = _marked_search(graph, max_volume)
    return dict(sorted(result.items()))


def strict_chain_marked_coefficients(graph: Graph, max_volume: int) -> dict[tuple[int, int, int], int]:
    """The deliberately wrong population with equal consecutive levels removed."""
    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    result, _ = _marked_search(graph, max_volume, allow_repeats=False)
    return dict(sorted(result.items()))


def chain_normalized_coefficients(graph: Graph, max_volume: int) -> list[dict[int, int]]:
    """Forget the span mark: coefficients of B_G through ``max_volume``."""
    rows: list[Counter[int]] = [Counter() for _ in range(_integer(max_volume, "max_volume", minimum=0) + 1)]
    for (volume, energy, _), count in chain_marked_coefficients(graph, max_volume).items():
        rows[volume][energy] += count
    return [dict(sorted(row.items())) for row in rows]


def chain_local_coefficients(graph: Graph, max_volume: int) -> list[dict[int, int]]:
    """Coefficients of L_G=B_G/(1-x^n), adding back common translations.

    [x^m]L = sum_{t>=0} [x^(m-nt)]B, a finite sum of nonnegative counts.
    """
    normalized = chain_normalized_coefficients(graph, max_volume)
    rows: list[Counter[int]] = [Counter() for _ in normalized]
    for volume in range(len(normalized)):
        for base in range(volume, -1, -graph.n):
            rows[volume].update(normalized[base])
    return [dict(sorted(row.items())) for row in rows]


def chain_census(graph: Graph, max_volume: int) -> dict[str, object]:
    """Report the exact chain population size and its stars-and-bars count.

    The number of minimum-zero profiles of volume at most R on n vertices is
    C(R+n,n)-C(R,n): all profiles minus those with every height positive.
    """
    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    result, visited = _marked_search(graph, max_volume)
    expected = comb(max_volume + graph.n, graph.n) - comb(max_volume, graph.n)
    return {
        "chains_visited": visited,
        "minimum_zero_profiles": expected,
        "agrees": visited == expected == sum(result.values()),
    }
