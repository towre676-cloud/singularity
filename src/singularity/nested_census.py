"""The nested-pair census: five boundary statistics of every T within S (SNG-F40).

For a graph on V, the raw census counts all pairs T subset-of S subset-of V,
empty and full sets and T = S included (3^n pairs), by

    (|S|, |T|, |dS|, |dT|, e(T, V minus S)).

Restricted to nonempty T and proper S, the pairs are exactly the threshold
chains of minimum-zero profiles of span two (SNG-F09 with h = 2): the profile
is 1_S + 1_T, its volume |S| + |T|, and by SNG-F10 its energy is
|dS| + |dT| + 2 e(T, V minus S).  T = S is the gap profile 2 * 1_S.
"""

from __future__ import annotations

from collections import Counter

from .graph import Graph

Cell = tuple[int, int, int, int, int]


def nested_pair_census(graph: Graph) -> dict[Cell, int]:
    """Raw census over all 3^n pairs T within S, keyed (|S|, |T|, cut S, cut T, cross)."""
    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    edges = [(1 << u, 1 << v) for u, v in graph.edges]
    full = (1 << graph.n) - 1
    cut = [sum(bool(m & a) != bool(m & b) for a, b in edges) for m in range(full + 1)]
    census: Counter[Cell] = Counter()
    for s in range(full + 1):
        outside = full & ~s
        t = s
        while True:
            cross = sum((bool(t & a) and bool(outside & b)) or (bool(t & b) and bool(outside & a)) for a, b in edges)
            census[s.bit_count(), t.bit_count(), cut[s], cut[t], cross] += 1
            if t == 0:
                break
            t = (t - 1) & s
    return dict(sorted(census.items()))


def span_two_projection(census: dict[Cell, int], n: int) -> dict[tuple[int, int], int]:
    """(volume, energy) counts of minimum-zero span-two profiles from the census."""
    out: Counter[tuple[int, int]] = Counter()
    for (s, t, cs, ct, x), count in census.items():
        if t >= 1 and s < n:
            out[s + t, cs + ct + 2 * x] += count
    return dict(sorted(out.items()))


def reflect(census: dict[Cell, int], n: int) -> dict[Cell, int]:
    """Image under (T, S) -> (V minus S, V minus T), i.e. a -> 2 - a."""
    return dict(sorted(((n - t, n - s, ct, cs, x), c) for (s, t, cs, ct, x), c in census.items()))


def binary_marginal(census: dict[Cell, int]) -> dict[tuple[int, int], int]:
    """(|S|, cut S) counts with T = empty: the complete binary cut-volume census."""
    out: Counter[tuple[int, int]] = Counter()
    for (s, t, cs, ct, x), count in census.items():
        if t == 0:
            out[s, cs] += count
    return dict(sorted(out.items()))


def census_difference(left: dict[Cell, int], right: dict[Cell, int]) -> dict[Cell, int]:
    keys = sorted(set(left) | set(right))
    return {k: left.get(k, 0) - right.get(k, 0) for k in keys if left.get(k, 0) != right.get(k, 0)}
