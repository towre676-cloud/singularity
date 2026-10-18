"""Height assignments constrained by a finite poset, and order polytopes (SNG-F32).

A ``Poset`` on 0..n-1 is given by cover or order relations (i, j) meaning
i <=_P j, i != j; the transitive closure must be antisymmetric (no cycles).
Weak assignments satisfy 0 <= a_i <= H and a_i <= a_j whenever i <_P j; they
are exactly the lattice points of H*O(P), O(P) = {x in [0,1]^n : x_i <= x_j
for i <_P j}.  Strict assignments require a_i < a_j instead and are handled
separately.

Counts are produced three ways: direct box enumeration, the order-chamber
decomposition of ``chambers.py`` (valid for any labeling), and Stanley's
linear-extension formula over a natural relabeling,
    #weak(P, H) = Omega(P, H+1) = sum_{sigma in L(P)} C(H + n - des(sigma), n),
where Omega(P, m) counts order-preserving maps to {1..m}: values 0..H shift
the argument by one.  Weighting the same points by x^volume q^energy gives a
finite weighted count, not an Ehrhart polynomial in H.
"""

from __future__ import annotations

from collections import Counter
from itertools import permutations, product
from fractions import Fraction
from math import comb, factorial
from typing import Iterable, Sequence

from .chambers import descents
from .graph import Graph, _integer


class Poset:
    """A finite poset on 0..n-1 with validated transitive closure."""

    def __init__(self, n: int, relations: Iterable[Sequence[int]] = ()) -> None:
        self.n = _integer(n, "n", minimum=1)
        below = [set() for _ in range(self.n)]
        for relation in relations:
            if len(relation) != 2:
                raise ValueError("relations are pairs (i, j) meaning i <= j")
            i, j = (_integer(v, "element", minimum=0) for v in relation)
            if i >= self.n or j >= self.n:
                raise ValueError("relation element outside 0..n-1")
            if i == j:
                raise ValueError("a relation must join distinct elements")
            below[j].add(i)
        changed = True
        while changed:
            changed = False
            for j in range(self.n):
                extra = set().union(*(below[i] for i in below[j])) - below[j] if below[j] else set()
                if extra:
                    below[j] |= extra
                    changed = True
        if any(j in below[j] for j in range(self.n)):
            raise ValueError("relations contain a cycle; a poset must be antisymmetric")
        self.less = frozenset((i, j) for j in range(self.n) for i in below[j])

    def is_weak(self, a: Sequence[int]) -> bool:
        return all(a[i] <= a[j] for i, j in self.less)

    def is_strict(self, a: Sequence[int]) -> bool:
        return all(a[i] < a[j] for i, j in self.less)

    def linear_extensions(self) -> list[tuple[int, ...]]:
        return [order for order in permutations(range(self.n))
                if all(order.index(i) < order.index(j) for i, j in self.less)]

    def natural_labeling(self) -> tuple[int, ...]:
        """A relabeling new[v] such that i <_P j implies new[i] < new[j]."""
        order, placed = [], set()
        while len(order) < self.n:
            ready = min(v for v in range(self.n) if v not in placed and all(i in placed for i, j in self.less if j == v))
            order.append(ready)
            placed.add(ready)
        return tuple(order.index(v) for v in range(self.n))

    def relabel(self, new: Sequence[int]) -> Poset:
        return Poset(self.n, [(new[i], new[j]) for i, j in self.less])


def count_direct(poset: Poset, height: int, strict: bool = False) -> int:
    """Enumerate {0..H}^n and test the order relations."""
    height = _integer(height, "height", minimum=0)
    test = poset.is_strict if strict else poset.is_weak
    return sum(test(a) for a in product(range(height + 1), repeat=poset.n))


def count_by_chambers(poset: Poset, height: int) -> int:
    """Weak count from half-open chambers (SNG-F29), for any labeling.

    In chamber pi with gaps d, a relation i <_P j holds automatically when i
    precedes j; when i follows j it forces every gap between them to zero,
    which is impossible across a label descent.  The surviving gap vectors
    with d_0 + ... + d_{n-1} <= H number C(H - s + f, f), where f counts free
    gaps (d_0 included) and s the forced minimum sum.
    """
    height = _integer(height, "height", minimum=0)
    total = 0
    for order in permutations(range(poset.n)):
        position = {v: k for k, v in enumerate(order)}
        minimum = list(descents(order))
        forced = [False] * poset.n
        for i, j in poset.less:
            if position[i] > position[j]:
                for k in range(position[j] + 1, position[i] + 1):
                    forced[k] = True
        if any(forced[k] and minimum[k] for k in range(1, poset.n)):
            continue
        free = 1 + sum(not forced[k] for k in range(1, poset.n))
        required = sum(minimum[k] for k in range(1, poset.n) if not forced[k])
        if required <= height:
            total += comb(height - required + free, free)
    return total


def count_by_linear_extensions(poset: Poset, height: int) -> int:
    """Omega(P, H+1) = sum over linear extensions of C(H + n - des, n)."""
    height = _integer(height, "height", minimum=0)
    natural = poset.relabel(poset.natural_labeling())
    return sum(comb(height + poset.n - sum(descents(sigma)), poset.n) for sigma in natural.linear_extensions())


def weighted_histogram(poset: Poset, graph: Graph, height: int) -> dict[tuple[int, int], int]:
    """(volume, energy) counts of the weak lattice points of H*O(P)."""
    if not isinstance(graph, Graph) or graph.n != poset.n:
        raise ValueError("graph and poset must have the same vertex set")
    height = _integer(height, "height", minimum=0)
    result: Counter[tuple[int, int]] = Counter()
    for a in product(range(height + 1), repeat=poset.n):
        if poset.is_weak(a):
            result[sum(a), graph.energy(a)] += 1
    return dict(sorted(result.items()))


def order_polynomial(poset: Poset) -> list[Fraction]:
    """Coefficients (constant first) of Omega(P, m) as a polynomial in m.

    Omega(P, m) = sum_{sigma in L(P)} C(m - 1 + n - des(sigma), n) for a
    natural labeling, expanded exactly over Q; it may be evaluated at any
    integer, including negative ones.
    """
    natural = poset.relabel(poset.natural_labeling())
    n = poset.n
    total = [Fraction(0)] * (n + 1)
    for sigma in natural.linear_extensions():
        shift = n - 1 - sum(descents(sigma))  # C(m + shift, n) = prod_{i<n} (m + shift - i) / n!
        poly = [Fraction(1)]
        for i in range(n):
            root = shift - i
            poly = [Fraction(0)] + poly
            for k in range(len(poly) - 1):
                poly[k] += root * poly[k + 1]
        for k, c in enumerate(poly):
            total[k] += c / factorial(n)
    return total


def evaluate_order_polynomial(coefficients: Sequence[Fraction], m: int) -> Fraction:
    return sum((c * Fraction(m) ** k for k, c in enumerate(coefficients)), Fraction(0))


def p_partition_series(poset: Poset, max_volume: int, strict: bool = False, energy_graph: Graph | None = None) -> list[dict[int, int]]:
    """Truncated sum of x^|a| q^E(a) over weak maps a >= 0, or strict maps a >= 1.

    Enumerated directly in the box of heights at most max_volume; without
    ``energy_graph`` every energy is 0 (the volume-only weight).
    """
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    rows: list[Counter[int]] = [Counter() for _ in range(max_volume + 1)]
    low = 1 if strict else 0
    test = poset.is_strict if strict else poset.is_weak
    for a in product(range(low, max_volume + 1), repeat=poset.n):
        volume = sum(a)
        if volume <= max_volume and test(a):
            rows[volume][energy_graph.energy(a) if energy_graph is not None else 0] += 1
    return [dict(sorted(r.items())) for r in rows]


def p_partition_rational(poset: Poset, strict: bool = False) -> tuple[dict[int, int], int]:
    """(numerator, n) with sum_a x^|a| = numerator(x) / prod_{i=1}^n (1 - x^i).

    Weak maps a >= 0: break ties by increasing natural label (SNG-F29); the
    chamber order is a linear extension sigma, gaps are positive at its
    descents, and sigma contributes x^(sum_{j in Des} (n - j)).  Strict maps
    a >= 1: break ties by decreasing natural label; the chamber order is again
    a linear extension, a tied block is a decreasing run and hence an
    antichain, d_0 >= 1, and gaps are positive at ascents, contributing
    x^(n + sum_{j in Asc} (n - j)).
    """
    natural = poset.relabel(poset.natural_labeling())
    n = poset.n
    numerator: Counter[int] = Counter()
    for sigma in natural.linear_extensions():
        down = descents(sigma)
        if strict:
            numerator[n + sum(n - j for j in range(1, n) if not down[j])] += 1
        else:
            numerator[sum(n - j for j in range(1, n) if down[j])] += 1
    return dict(sorted(numerator.items())), n
