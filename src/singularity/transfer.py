"""Bounded-height population counting by exact forest message passing.

For heights in {0,...,H}, each directed subtree message is indexed by the
height at its root and the joint (total volume, edge energy) accumulated below
it. Combining a child charges its connecting edge exactly once. Disconnected
components are combined by convolution. General graphs are rejected by the
tree algorithm; a separate brute-force routine is provided for small checks.
"""

from collections import defaultdict
from itertools import product
from typing import Mapping

Histogram = dict[tuple[int, int], int]


def _validate_bounds(height: int, max_volume: int | None, n: int) -> tuple[int, int]:
    if not isinstance(height, int) or isinstance(height, bool) or height < 0:
        raise ValueError("height bound must be a nonnegative integer")
    if max_volume is None:
        max_volume = height * n
    if not isinstance(max_volume, int) or isinstance(max_volume, bool) or max_volume < 0:
        raise ValueError("volume bound must be a nonnegative integer")
    return height, min(max_volume, height * n)


def _convolve(left: Mapping[tuple[int, int], int], right: Mapping[tuple[int, int], int], max_volume: int, edge_energy: int = 0) -> Histogram:
    result: defaultdict[tuple[int, int], int] = defaultdict(int)
    for (v1, e1), c1 in left.items():
        for (v2, e2), c2 in right.items():
            volume = v1 + v2
            if volume <= max_volume:
                result[volume, e1 + e2 + edge_energy] += c1 * c2
    return dict(result)


def _forest_order(graph) -> tuple[list[int], list[list[int]], list[int]]:
    """Return parent-before-child order, children, roots; reject any cycle."""
    adjacency = [[] for _ in range(graph.n)]
    for u, v in graph.edges:
        adjacency[u].append(v)
        adjacency[v].append(u)
    parents = [-2] * graph.n
    children = [[] for _ in range(graph.n)]
    order: list[int] = []
    roots: list[int] = []
    for root in range(graph.n):
        if parents[root] != -2:
            continue
        roots.append(root)
        parents[root] = -1
        stack = [root]
        while stack:
            vertex = stack.pop()
            order.append(vertex)
            for neighbor in adjacency[vertex]:
                if neighbor == parents[vertex]:
                    continue
                if parents[neighbor] != -2:
                    raise ValueError("bounded-height tree transfer requires a forest")
                parents[neighbor] = vertex
                children[vertex].append(neighbor)
                stack.append(neighbor)
    return order, children, roots


def _unrestricted_forest(graph, height: int, max_volume: int) -> Histogram:
    order, children, roots = _forest_order(graph)
    messages: dict[int, list[Histogram]] = {}
    for vertex in reversed(order):
        by_height: list[Histogram] = []
        for root_height in range(height + 1):
            current: Histogram = {(root_height, 0): 1} if root_height <= max_volume else {}
            for child in children[vertex]:
                summed_child: defaultdict[tuple[int, int], int] = defaultdict(int)
                for child_height, histogram in enumerate(messages[child]):
                    charge = (root_height - child_height) ** 2
                    for (volume, energy), count in histogram.items():
                        summed_child[volume, energy + charge] += count
                current = _convolve(current, summed_child, max_volume)
            by_height.append(current)
        messages[vertex] = by_height
        for child in children[vertex]:
            del messages[child]
    result: Histogram = {(0, 0): 1}
    for root in roots:
        component: defaultdict[tuple[int, int], int] = defaultdict(int)
        for histogram in messages[root]:
            for key, count in histogram.items():
                component[key] += count
        result = _convolve(result, component, max_volume)
    return dict(sorted(result.items()))


def bounded_height_histogram(graph, height: int, max_volume: int | None = None, min_zero: bool = False) -> Histogram:
    """Count a forest's labeled profiles by (volume,energy) exactly.

    With ``min_zero=True``, subtract the all-positive profiles by the bijection
    a -> a-1: the subtraction is x**n times the height-(H-1) population.
    The volume budget prunes subtree convolutions without changing any retained
    counts. It is especially useful when H is large but only low coefficients
    are required. Work remains sensitive to tree shape and histogram support.
    """
    if not isinstance(min_zero, bool):
        raise ValueError("min_zero must be boolean")
    height, max_volume = _validate_bounds(height, max_volume, graph.n)
    result = _unrestricted_forest(graph, height, max_volume)
    if min_zero and height and max_volume >= graph.n:
        positive = _unrestricted_forest(graph, height - 1, max_volume - graph.n)
        for (volume, energy), count in positive.items():
            key = volume + graph.n, energy
            difference = result.get(key, 0) - count
            if difference < 0:
                raise ArithmeticError("normalization subtraction produced a negative count")
            if difference:
                result[key] = difference
            else:
                result.pop(key, None)
    return dict(sorted(result.items()))


tree_height_histogram = bounded_height_histogram


def brute_bounded_height_histogram(graph, height: int, max_volume: int | None = None, min_zero: bool = False) -> Histogram:
    """Independent Cartesian enumeration, valid for every simple graph.

    This is an oracle for genuinely small inputs. Its (H+1)**n work is not
    disguised by a transfer-style name or silent approximation.
    """
    if not isinstance(min_zero, bool):
        raise ValueError("min_zero must be boolean")
    height, max_volume = _validate_bounds(height, max_volume, graph.n)
    result: defaultdict[tuple[int, int], int] = defaultdict(int)
    for profile in product(range(height + 1), repeat=graph.n):
        volume = sum(profile)
        if volume > max_volume or (min_zero and min(profile) != 0):
            continue
        energy = sum((profile[u] - profile[v]) ** 2 for u, v in graph.edges)
        result[volume, energy] += 1
    return dict(sorted(result.items()))


def histogram_coefficients(histogram: Mapping[tuple[int, int], int], max_volume: int) -> list[dict[int, int]]:
    """Convert a joint histogram to the coefficient interface used by L_G."""
    if not isinstance(max_volume, int) or isinstance(max_volume, bool) or max_volume < 0:
        raise ValueError("max_volume must be a nonnegative integer")
    result: list[dict[int, int]] = [{} for _ in range(max_volume + 1)]
    for (volume, energy), count in histogram.items():
        if volume <= max_volume and count:
            result[volume][energy] = result[volume].get(energy, 0) + count
    return [dict(sorted(poly.items())) for poly in result]
