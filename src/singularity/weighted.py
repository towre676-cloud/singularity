"""Integral vertex masses, parallel edge weights, and exact hard contraction."""
from dataclasses import dataclass
from collections import Counter
from itertools import product


@dataclass(frozen=True)
class WeightedGraph:
    masses: tuple
    edges: tuple

    def __post_init__(self):
        masses = tuple(self.masses)
        if not masses or any(type(m) is not int or m <= 0 for m in masses):
            raise ValueError("vertex masses must be positive integers")
        edge_weights = Counter()
        for i, j, w in self.edges:
            if any(type(v) is not int for v in (i, j, w)):
                raise ValueError("integer endpoints and weights required")
            if i == j or not (0 <= i < len(masses) and 0 <= j < len(masses)) or w <= 0:
                raise ValueError("invalid weighted edge")
            edge_weights[tuple(sorted((i, j)))] += w
        object.__setattr__(self, "masses", masses)
        object.__setattr__(self, "edges", tuple((i, j, w) for (i, j), w in sorted(edge_weights.items())))

    @property
    def n(self):
        return len(self.masses)

    def energy(self, a):
        if len(a) != self.n or any(type(x) is not int or x < 0 for x in a):
            raise ValueError("a nonnegative integer per vertex is required")
        return sum(w * (a[i] - a[j]) ** 2 for i, j, w in self.edges)

    def volume(self, a):
        if len(a) != self.n or any(type(x) is not int or x < 0 for x in a):
            raise ValueError("a nonnegative integer per vertex is required")
        return sum(m * x for m, x in zip(self.masses, a))

    def contract(self, pairs):
        """Enforce equal heights on supplied pairs, summing masses/parallel weights."""
        parent = list(range(self.n))
        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]; i = parent[i]
            return i
        for i, j in pairs:
            if type(i) is not int or type(j) is not int or not (0 <= i < self.n and 0 <= j < self.n):
                raise ValueError("invalid contraction endpoint")
            parent[find(j)] = find(i)
        blocks = {}
        for i in range(self.n):
            blocks.setdefault(find(i), []).append(i)
        groups = sorted(blocks.values(), key=lambda group: group[0])
        mapping = {i: j for j, group in enumerate(groups) for i in group}
        masses = tuple(sum(self.masses[i] for i in group) for group in groups)
        edges = [(mapping[i], mapping[j], w) for i, j, w in self.edges if mapping[i] != mapping[j]]
        return WeightedGraph(masses, tuple(edges)), tuple(mapping[i] for i in range(self.n))


def weighted_coefficients(graph, max_volume, max_profiles=1_000_000):
    if type(max_volume) is not int or max_volume < 0:
        raise ValueError("max_volume must be a nonnegative integer")
    ranges = [range(max_volume // mass + 1) for mass in graph.masses]
    count = 1
    for values in ranges:
        count *= len(values)
    if count > max_profiles:
        raise ValueError(f"weighted box has {count} profiles; budget is {max_profiles}")
    coefficients = [Counter() for _ in range(max_volume + 1)]
    for a in product(*ranges):
        volume = graph.volume(a)
        if volume <= max_volume:
            coefficients[volume][graph.energy(a)] += 1
    return [dict(sorted(row.items())) for row in coefficients]
