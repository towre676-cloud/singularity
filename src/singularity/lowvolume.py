"""Closed coefficient formulas through volume three (SNG-F14, SNG-E004).

Coefficients are assembled from graph statistics defined directly from
degrees and adjacency, without enumerating height profiles:

* ``degree_histogram``: N_d = #{i : d_i = d};
* ``ordered_pair_statistics``: P[a, b, eps] = #{(i, j) : i != j, d_i = a,
  d_j = b, A_ij = eps}, ordered pairs;
* ``triple_statistics``: T[s, t] = #{{i, j, k} : d_i + d_j + d_k = s,
  e(G[{i, j, k}]) = t}, unordered triples.

Every profile of volume at most three has exactly one positive-part pattern:

====== ============ ======= ==== =================================
volume pattern      support span energy
====== ============ ======= ==== =================================
1      e_i          1       1    d_i
2      2e_i         1       2    4 d_i
2      e_i+e_j      2       1    d_i + d_j - 2 A_ij   (i < j)
3      3e_i         1       3    9 d_i
3      2e_i+e_j     2       2    4 d_i + d_j - 4 A_ij (ordered i != j)
3      e_i+e_j+e_k  3       1    d_i + d_j + d_k - 2 e(G[ijk])
====== ============ ======= ==== =================================

A pattern is minimum-zero exactly when its support is smaller than n, so the
marked formulas drop patterns whose support covers every vertex.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations

from .graph import Graph

# (volume, support size, span, label) for each positive-part pattern.
PATTERNS = (
    (1, 1, 1, "e_i"),
    (2, 1, 2, "2e_i"),
    (2, 2, 1, "e_i+e_j"),
    (3, 1, 3, "3e_i"),
    (3, 2, 2, "2e_i+e_j"),
    (3, 3, 1, "e_i+e_j+e_k"),
)


def _graph(graph: Graph) -> Graph:
    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    return graph


def degree_histogram(graph: Graph) -> dict[int, int]:
    return dict(sorted(Counter(_graph(graph).degrees).items()))


def ordered_pair_statistics(graph: Graph) -> dict[tuple[int, int, int], int]:
    """Ordered distinct pairs by (d_i, d_j, A_ij)."""
    graph = _graph(graph)
    edges = set(graph.edges)
    d = graph.degrees
    result: Counter[tuple[int, int, int]] = Counter()
    for i in range(graph.n):
        for j in range(graph.n):
            if i != j:
                result[d[i], d[j], int((min(i, j), max(i, j)) in edges)] += 1
    return dict(sorted(result.items()))


def triple_statistics(graph: Graph) -> dict[tuple[int, int], int]:
    """Unordered triples by (degree sum, number of induced edges)."""
    graph = _graph(graph)
    edges = set(graph.edges)
    d = graph.degrees
    result: Counter[tuple[int, int]] = Counter()
    for triple in combinations(range(graph.n), 3):
        induced = sum(pair in edges for pair in combinations(triple, 2))
        result[sum(d[i] for i in triple), induced] += 1
    return dict(sorted(result.items()))


def pattern_sectors(graph: Graph) -> dict[str, dict[int, int]]:
    """Energy polynomial of each pattern, computed from the statistics only."""
    histogram = degree_histogram(graph)
    pairs = ordered_pair_statistics(graph)
    triples = triple_statistics(graph)
    sectors: dict[str, Counter[int]] = {label: Counter() for *_, label in PATTERNS}
    for degree, count in histogram.items():
        sectors["e_i"][degree] += count
        sectors["2e_i"][4 * degree] += count
        sectors["3e_i"][9 * degree] += count
    for (a, b, adjacent), count in pairs.items():
        sectors["2e_i+e_j"][4 * a + b - 4 * adjacent] += count
        # Each unordered pair appears twice among ordered pairs.
        sectors["e_i+e_j"][a + b - 2 * adjacent] += count
    sectors["e_i+e_j"] = Counter({e: c // 2 for e, c in sectors["e_i+e_j"].items()})
    for (degree_sum, induced), count in triples.items():
        sectors["e_i+e_j+e_k"][degree_sum - 2 * induced] += count
    return {label: dict(sorted(row.items())) for label, row in sectors.items()}


def low_volume_local(graph: Graph) -> list[dict[int, int]]:
    """[x^m] L_G for m = 0, 1, 2, 3 from the closed formulas."""
    sectors = pattern_sectors(graph)
    rows: list[Counter[int]] = [Counter({0: 1}), Counter(), Counter(), Counter()]
    for volume, _, _, label in PATTERNS:
        rows[volume].update(sectors[label])
    return [dict(sorted((e, c) for e, c in row.items() if c)) for row in rows]


def low_volume_marked(graph: Graph) -> dict[tuple[int, int, int], int]:
    """Marked minimum-zero counts through volume three from the formulas."""
    graph = _graph(graph)
    sectors = pattern_sectors(graph)
    result: Counter[tuple[int, int, int]] = Counter({(0, 0, 0): 1})
    for volume, support, span, label in PATTERNS:
        if support < graph.n:
            for energy, count in sectors[label].items():
                result[volume, energy, span] += count
    return dict(sorted((k, c) for k, c in result.items() if c))


def low_volume_normalized(graph: Graph) -> list[dict[int, int]]:
    """[x^m] B_G = C_m - C_{m-n} for m <= 3."""
    graph = _graph(graph)
    local = low_volume_local(graph)
    rows = []
    for m, row in enumerate(local):
        out = Counter(row)
        if m >= graph.n:
            out.subtract(local[m - graph.n])
        rows.append(dict(sorted((e, c) for e, c in out.items() if c)))
    return rows


def regular_low_volume_local(n: int, degree: int, triangles: int) -> list[dict[int, int]]:
    """C_0..C_3 of a degree-regular graph from (n, degree, triangle count).

    With m = n d / 2 edges, the triple counts N_j by induced edges j are
    N_3 = T, N_2 = n C(d,2) - 3T, N_1 = m (n-2) - 2 N_2 - 3T and
    N_0 = C(n,3) - N_1 - N_2 - N_3 (SNG-I008).
    """
    from math import comb

    edges, odd = divmod(n * degree, 2)
    if odd or not 0 <= degree < n or triangles < 0:
        raise ValueError("no simple regular graph has these parameters")
    n2 = n * comb(degree, 2) - 3 * triangles
    n1 = edges * (n - 2) - 2 * n2 - 3 * triangles
    n0 = comb(n, 3) - n1 - n2 - triangles
    if min(n0, n1, n2) < 0:
        raise ValueError("triangle count is inconsistent with n and degree")
    rows: list[Counter[int]] = [Counter({0: 1}), Counter({degree: n}), Counter(), Counter()]
    rows[2][4 * degree] += n
    rows[2][2 * degree - 2] += edges
    rows[2][2 * degree] += comb(n, 2) - edges
    rows[3][9 * degree] += n
    rows[3][5 * degree - 4] += 2 * edges
    rows[3][5 * degree] += n * (n - 1) - 2 * edges
    for induced, count in enumerate((n0, n1, n2, triangles)):
        rows[3][3 * degree - 2 * induced] += count
    return [dict(sorted((e, c) for e, c in row.items() if c)) for row in rows]
