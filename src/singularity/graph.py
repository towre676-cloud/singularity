"""Validated finite simple graphs and their exact integer quadratic forms.

Vertices are the original labels ``0, ..., n - 1``.  No isomorphism quotient
is taken: permutations give bijections of height populations, not divisions of
their multiplicities by automorphism-group orders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence


def _integer(value: object, name: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


@dataclass(frozen=True, init=False)
class Graph:
    """An immutable, nonempty-vertex, finite simple undirected graph.

    Disconnected graphs and isolated vertices are supported.  ``n >= 1`` is
    required because normalized height representatives use their minimum.
    Repeated edges, including an edge repeated in reverse order, are rejected.
    """

    n: int
    edges: tuple[tuple[int, int], ...]
    _degrees: tuple[int, ...] = field(repr=False, compare=False)
    _neighbors: tuple[tuple[int, ...], ...] = field(repr=False, compare=False)

    def __init__(self, n: int, edges: Iterable[Sequence[int]] = ()) -> None:
        n = _integer(n, "n", minimum=1)
        canonical: set[tuple[int, int]] = set()
        adjacency: list[list[int]] = [[] for _ in range(n)]
        for edge in edges:
            try:
                u, v = edge
            except (TypeError, ValueError) as exc:
                raise ValueError("every edge must have exactly two endpoints") from exc
            u = _integer(u, "edge endpoint", minimum=0)
            v = _integer(v, "edge endpoint", minimum=0)
            if u >= n or v >= n:
                raise ValueError("edge endpoint is outside 0, ..., n-1")
            if u == v:
                raise ValueError("loops are not allowed")
            pair = (min(u, v), max(u, v))
            if pair in canonical:
                raise ValueError(f"duplicate edge {pair}")
            canonical.add(pair)
            adjacency[u].append(v)
            adjacency[v].append(u)
        object.__setattr__(self, "n", n)
        object.__setattr__(self, "edges", tuple(sorted(canonical)))
        object.__setattr__(self, "_degrees", tuple(map(len, adjacency)))
        object.__setattr__(
            self, "_neighbors", tuple(tuple(sorted(row)) for row in adjacency)
        )

    @property
    def degrees(self) -> tuple[int, ...]:
        return self._degrees

    @property
    def neighbors(self) -> tuple[tuple[int, ...], ...]:
        return self._neighbors

    def components(self) -> tuple[tuple[int, ...], ...]:
        remaining = set(range(self.n))
        result: list[tuple[int, ...]] = []
        while remaining:
            start = min(remaining)
            remaining.remove(start)
            seen = {start}
            stack = [start]
            while stack:
                for j in self.neighbors[stack.pop()]:
                    if j in remaining:
                        remaining.remove(j)
                        seen.add(j)
                        stack.append(j)
            result.append(tuple(sorted(seen)))
        return tuple(result)

    @property
    def connected(self) -> bool:
        return len(self.components()) == 1

    def laplacian(self) -> tuple[tuple[int, ...], ...]:
        rows = [[0] * self.n for _ in range(self.n)]
        for i, degree in enumerate(self.degrees):
            rows[i][i] = degree
        for i, j in self.edges:
            rows[i][j] = rows[j][i] = -1
        return tuple(tuple(row) for row in rows)

    def validate_heights(self, a: Sequence[int], *, nonnegative: bool = False) -> tuple[int, ...]:
        values = tuple(a)
        if len(values) != self.n:
            raise ValueError(f"expected {self.n} heights")
        return tuple(
            _integer(value, "height", minimum=0 if nonnegative else None)
            for value in values
        )

    def energy(self, a: Sequence[int]) -> int:
        """Return the exact energy; signed integer heights are permitted."""
        values = self.validate_heights(a)
        return sum((values[i] - values[j]) ** 2 for i, j in self.edges)

    def cut_size(self, subset: Iterable[int]) -> int:
        vertices = set(subset)
        for vertex in vertices:
            _integer(vertex, "vertex", minimum=0)
            if vertex >= self.n:
                raise ValueError("cut vertex is outside the graph")
        return sum((i in vertices) != (j in vertices) for i, j in self.edges)

    def relabel(self, permutation: Sequence[int]) -> Graph:
        """Relabel old vertex i as permutation[i]."""
        labels = tuple(permutation)
        if len(labels) != self.n:
            raise ValueError("a relabeling must specify every vertex")
        for label in labels:
            _integer(label, "permutation label", minimum=0)
        if set(labels) != set(range(self.n)):
            raise ValueError("relabeling must be a permutation of the vertices")
        return Graph(self.n, ((labels[i], labels[j]) for i, j in self.edges))

    def to_dict(self) -> dict[str, object]:
        return {"n": self.n, "edges": [list(edge) for edge in self.edges]}

    @classmethod
    def from_dict(cls, source: Mapping[str, object]) -> Graph:
        if not isinstance(source, Mapping):
            raise TypeError("graph source must be an object with n and edges")
        if "n" not in source or "edges" not in source:
            raise ValueError("graph source must contain n and edges")
        return cls(source["n"], source["edges"])  # type: ignore[arg-type]
