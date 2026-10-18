"""Exact height populations from a supplied, checked tree decomposition.

A decomposition is a tree of bags of original vertex labels with a chosen
root bag.  ``check_decomposition`` verifies the three axioms (every vertex
is covered, every edge lies in some bag, the bags containing a vertex form a
connected subtree) and that the bag graph is a tree.

Charges are owned, never shared: each vertex and each edge is charged at
the unique bag nearest the root among the bags that contain it (that set is
a connected subtree, so it has one top bag).  A bag message maps a height
assignment of the bag's vertices to the (volume, energy) histogram of all
charges owned in the bag's subtree, given those heights.  A parent combines
children by summing each child message over the child's private vertices,
keyed by the shared vertices, and multiplying (SNG-F26).  Volume truncation,
minimum-zero subtraction and exact-span recovery are those of the forest
engine (SNG-F24, SNG-F25).

JSON form, schema ``singularity.tree-decomposition/1``::

    {"bags": [[0, 1], [1, 2]], "edges": [[0, 1]], "root": 0}
"""

from __future__ import annotations

from collections import defaultdict
from itertools import product
from typing import Mapping, Sequence

from .graph import Graph

SCHEMA = "singularity.tree-decomposition/1"
Histogram = dict[tuple[int, int], int]


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class TreeDecomposition:
    """Bags of original labels, undirected tree edges between bag indices, a root."""

    def __init__(self, bags: Sequence[Sequence[int]], edges: Sequence[Sequence[int]] = (), root: int = 0) -> None:
        self.bags = tuple(tuple(bag) for bag in bags)
        self.edges = tuple(tuple(edge) for edge in edges)
        self.root = root

    def to_dict(self) -> dict[str, object]:
        return {"bags": [list(b) for b in self.bags], "edges": [list(e) for e in self.edges], "root": self.root}

    @classmethod
    def from_dict(cls, source: Mapping[str, object]) -> TreeDecomposition:
        if not isinstance(source, Mapping) or set(source) - {"schema"} != {"bags", "edges", "root"}:
            raise ValueError("decomposition must contain exactly bags, edges, root (and optional schema)")
        if source.get("schema", SCHEMA) != SCHEMA:
            raise ValueError("unrecognized decomposition schema")
        return cls(source["bags"], source["edges"], source["root"])  # type: ignore[arg-type]

    @property
    def width(self) -> int:
        return max((len(b) for b in self.bags), default=0) - 1


def check_decomposition(graph: Graph, decomposition: TreeDecomposition) -> list[str]:
    """Return every violated condition; an empty list means valid."""
    errors: list[str] = []
    bags, edges, root = decomposition.bags, decomposition.edges, decomposition.root
    if not bags:
        return ["a decomposition needs at least one bag"]
    for index, bag in enumerate(bags):
        if not all(_is_int(v) for v in bag):
            errors.append(f"bag {index} contains a non-integer label")
        elif any(not 0 <= v < graph.n for v in bag):
            errors.append(f"bag {index} contains a label outside 0..n-1")
        elif len(set(bag)) != len(bag):
            errors.append(f"bag {index} repeats a vertex")
    if not _is_int(root) or not 0 <= root < len(bags):
        errors.append("root is not a bag index")
    adjacency: list[list[int]] = [[] for _ in bags]
    for edge in edges:
        if len(edge) != 2 or not all(_is_int(i) for i in edge) or not all(0 <= i < len(bags) for i in edge) or edge[0] == edge[1]:
            errors.append(f"tree edge {list(edge)} is invalid")
            continue
        adjacency[edge[0]].append(edge[1])
        adjacency[edge[1]].append(edge[0])
    if errors:
        return errors
    if len({tuple(sorted(e)) for e in edges}) != len(edges):
        errors.append("tree edges repeat")
    seen, stack = {0}, [0]
    while stack:
        for j in adjacency[stack.pop()]:
            if j not in seen:
                seen.add(j)
                stack.append(j)
    if len(seen) != len(bags):
        errors.append("bag graph is disconnected")
    if len(edges) != len(bags) - 1:
        errors.append("bag graph is not a tree (edge count differs from bags - 1)")
    if errors:
        return errors
    covering = [set() for _ in range(graph.n)]
    for index, bag in enumerate(bags):
        for v in bag:
            covering[v].add(index)
    for v, holders in enumerate(covering):
        if not holders:
            errors.append(f"vertex {v} is in no bag")
            continue
        start = min(holders)
        reached, stack = {start}, [start]
        while stack:
            for j in adjacency[stack.pop()]:
                if j in holders and j not in reached:
                    reached.add(j)
                    stack.append(j)
        if reached != holders:
            errors.append(f"bags containing vertex {v} are not connected")
    for u, v in graph.edges:
        if not covering[u] & covering[v]:
            errors.append(f"edge {[u, v]} is in no bag")
    return errors


def _rooted(decomposition: TreeDecomposition) -> tuple[list[int], list[int]]:
    """Return parent-before-child order and parents of a checked decomposition."""
    adjacency: list[list[int]] = [[] for _ in decomposition.bags]
    for i, j in decomposition.edges:
        adjacency[i].append(j)
        adjacency[j].append(i)
    parent = [-1] * len(decomposition.bags)
    order, stack = [], [decomposition.root]
    visited = {decomposition.root}
    while stack:
        node = stack.pop()
        order.append(node)
        for child in adjacency[node]:
            if child not in visited:
                visited.add(child)
                parent[child] = node
                stack.append(child)
    return order, parent


def charge_owners(graph: Graph, decomposition: TreeDecomposition) -> tuple[dict[int, int], dict[tuple[int, int], int]]:
    """Owning bag of each vertex and edge: the top bag among those containing it."""
    order, _ = _rooted(decomposition)
    depth_rank = {node: rank for rank, node in enumerate(order)}
    vertex_owner: dict[int, int] = {}
    edge_owner: dict[tuple[int, int], int] = {}
    for node in sorted(range(len(decomposition.bags)), key=depth_rank.__getitem__):
        bag = set(decomposition.bags[node])
        for v in bag:
            vertex_owner.setdefault(v, node)
        for u, v in graph.edges:
            if u in bag and v in bag:
                edge_owner.setdefault((u, v), node)
    return vertex_owner, edge_owner


def _convolve(left: Histogram, right: Histogram, max_volume: int) -> Histogram:
    result: defaultdict[tuple[int, int], int] = defaultdict(int)
    for (v1, e1), c1 in left.items():
        for (v2, e2), c2 in right.items():
            if v1 + v2 <= max_volume:
                result[v1 + v2, e1 + e2] += c1 * c2
    return dict(result)


def _box(graph: Graph, decomposition: TreeDecomposition, height: int, max_volume: int, statistics: dict | None,
         root_message: dict | None = None) -> Histogram:
    order, parent = _rooted(decomposition)
    vertex_owner, edge_owner = charge_owners(graph, decomposition)
    bags = decomposition.bags
    children: list[list[int]] = [[] for _ in bags]
    for node in order[1:]:
        children[parent[node]].append(node)
    owned_vertices = [[v for v in bags[node] if vertex_owner[v] == node] for node in range(len(bags))]
    owned_edges = [[e for e, owner in edge_owner.items() if owner == node] for node in range(len(bags))]
    messages: dict[int, dict[tuple[int, ...], Histogram]] = {}
    for node in reversed(order):
        bag = bags[node]
        position = {v: i for i, v in enumerate(bag)}
        projected = []
        for child in children[node]:
            shared = [v for v in bags[child] if v in position]
            child_position = {v: i for i, v in enumerate(bags[child])}
            summed: dict[tuple[int, ...], defaultdict] = {}
            for assignment, histogram in messages.pop(child).items():
                key = tuple(assignment[child_position[v]] for v in shared)
                row = summed.setdefault(key, defaultdict(int))
                for cell, count in histogram.items():
                    row[cell] += count
            projected.append((shared, {k: dict(v) for k, v in summed.items()}))
        message: dict[tuple[int, ...], Histogram] = {}
        for assignment in product(range(height + 1), repeat=len(bag)):
            volume = sum(assignment[position[v]] for v in owned_vertices[node])
            if volume > max_volume:
                continue
            energy = sum((assignment[position[u]] - assignment[position[v]]) ** 2 for u, v in owned_edges[node])
            current: Histogram = {(volume, energy): 1}
            for shared, table in projected:
                key = tuple(assignment[position[v]] for v in shared)
                current = _convolve(current, table.get(key, {}), max_volume)
                if not current:
                    break
            if current:
                message[assignment] = current
        messages[node] = message
        if statistics is not None:
            statistics["bag_assignments"] = statistics.get("bag_assignments", 0) + (height + 1) ** len(bag)
            support = sum(map(len, message.values()))
            statistics["message_support_cells"] = statistics.get("message_support_cells", 0) + support
            statistics["max_message_support"] = max(statistics.get("max_message_support", 0), support)
            largest = max((c for h in message.values() for c in h.values()), default=0)
            statistics["max_count_bits"] = max(statistics.get("max_count_bits", 0), largest.bit_length())
    if root_message is not None:  # conditioned on the root bag's heights (terminal kernels)
        root_message.update(messages[decomposition.root])
    result: defaultdict[tuple[int, int], int] = defaultdict(int)
    for histogram in messages[decomposition.root].values():
        for cell, count in histogram.items():
            result[cell] += count
    return dict(sorted(result.items()))


def _validated(graph: Graph, decomposition: TreeDecomposition, height: int, max_volume: int | None) -> tuple[int, int]:
    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    if not isinstance(decomposition, TreeDecomposition):
        raise TypeError("decomposition must be a TreeDecomposition")
    errors = check_decomposition(graph, decomposition)
    if errors:
        raise ValueError("invalid tree decomposition: " + "; ".join(errors))
    if not _is_int(height) or height < 0:
        raise ValueError("height bound must be a nonnegative integer")
    if max_volume is None:
        max_volume = height * graph.n
    if not _is_int(max_volume) or max_volume < 0:
        raise ValueError("volume bound must be a nonnegative integer")
    return height, min(max_volume, height * graph.n)


def decomposition_histogram(graph: Graph, decomposition: TreeDecomposition, height: int,
                            max_volume: int | None = None, min_zero: bool = False) -> Histogram:
    """Labeled profiles in {0..H}^n with volume <= budget, by (volume, energy).

    ``min_zero=True`` subtracts x^n times the height-(H-1) box computed with
    budget R-n: one global translation (SNG-F25).
    """
    if not isinstance(min_zero, bool):
        raise ValueError("min_zero must be boolean")
    height, max_volume = _validated(graph, decomposition, height, max_volume)
    result = _box(graph, decomposition, height, max_volume, None)
    if min_zero and height and max_volume >= graph.n:
        positive = _box(graph, decomposition, height - 1, max_volume - graph.n, None)
        for (volume, energy), count in positive.items():
            key = volume + graph.n, energy
            difference = result.get(key, 0) - count
            if difference < 0:
                raise ArithmeticError(f"negative normalized count at {key} for graph {graph.to_dict()}")
            if difference:
                result[key] = difference
            else:
                result.pop(key, None)
    return dict(sorted(result.items()))


def marked_decomposition_coefficients(graph: Graph, decomposition: TreeDecomposition, max_volume: int,
                                      max_span: int | None = None) -> dict[tuple[int, int, int], int]:
    """(volume, energy, span) counts of global minimum-zero profiles, via SNG-F25."""
    if not _is_int(max_volume) or max_volume < 0:
        raise ValueError("max_volume must be a nonnegative integer")
    max_span = max_volume if max_span is None else max_span
    if not _is_int(max_span) or max_span < 0:
        raise ValueError("max_span must be a nonnegative integer")
    result: dict[tuple[int, int, int], int] = {}
    previous: Histogram = {}
    for span in range(min(max_span, max_volume) + 1):
        current = decomposition_histogram(graph, decomposition, span, max_volume, min_zero=True)
        for key in current.keys() | previous.keys():
            count = current.get(key, 0) - previous.get(key, 0)
            if count < 0:
                raise ArithmeticError(f"negative exact-span count {count} at span {span}, cell {key}, graph {graph.to_dict()}")
            if count:
                result[key[0], key[1], span] = count
        previous = current
    return dict(sorted(result.items()))


def decomposition_statistics(graph: Graph, decomposition: TreeDecomposition, height: int,
                             max_volume: int | None = None) -> dict[str, int]:
    """Separate costs: bag assignments sum (H+1)^|X|, sparse support, bit size."""
    height, max_volume = _validated(graph, decomposition, height, max_volume)
    statistics: dict[str, int] = {"width": decomposition.width}
    _box(graph, decomposition, height, max_volume, statistics)
    return dict(sorted(statistics.items()))


def elimination_decomposition(graph: Graph, order: Sequence[int]) -> TreeDecomposition:
    """Build a decomposition from an elimination order of all vertices.

    Bag i is v_i with its later neighbours in the filled graph; its parent is
    the bag of the earliest-eliminated of those neighbours.  Bags without a
    parent (one per component) are attached to the last bag.
    """
    order = tuple(order)
    if sorted(order) != list(range(graph.n)) or not all(_is_int(v) for v in order):
        raise ValueError("order must be a permutation of the vertices")
    rank = {v: i for i, v in enumerate(order)}
    neighbours = [set(row) for row in graph.neighbors]
    bags, parents = [], []
    for v in order:
        later = {u for u in neighbours[v] if rank[u] > rank[v]}
        for a in later:
            neighbours[a] |= later - {a}
        bags.append(tuple(sorted({v} | later)))
        parents.append(rank[min(later, key=rank.__getitem__)] if later else None)
    last = len(order) - 1
    edges = [(i, p if p is not None else last) for i, p in enumerate(parents) if i != last]
    return TreeDecomposition(bags, edges, root=last)


def forest_decomposition(graph: Graph) -> TreeDecomposition:
    """A width-one decomposition of a forest: eliminate leaves first."""
    remaining = {v: set(graph.neighbors[v]) for v in range(graph.n)}
    order = []
    while remaining:
        leaf = min(v for v, row in remaining.items() if len(row) <= 1)
        order.append(leaf)
        for u in remaining.pop(leaf):
            remaining[u].discard(leaf)
    decomposition = elimination_decomposition(graph, order)
    if decomposition.width > 1:
        raise ValueError("forest_decomposition requires a forest")
    return decomposition
