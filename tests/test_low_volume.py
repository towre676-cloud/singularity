"""P04-P06: closed low-volume formulas against two enumerators and fixed pairs."""

from collections import Counter
from fractions import Fraction
from itertools import combinations
import json
from math import comb
from pathlib import Path
import unittest

from singularity.chains import chain_marked_coefficients
from singularity.examples import GRAPHS
from singularity.graph import Graph
from singularity.heights import local_coefficients, marked_coefficients, normalized_coefficients
from singularity.lowvolume import (
    degree_histogram, low_volume_local, low_volume_marked, low_volume_normalized,
    ordered_pair_statistics, pattern_sectors, regular_low_volume_local, triple_statistics,
)
from singularity.polynomials import evaluate, from_factors, normalize, sub

ROOT = Path(__file__).resolve().parents[1]


def all_graphs(max_n):
    for n in range(1, max_n + 1):
        pairs = list(combinations(range(n), 2))
        for mask in range(1 << len(pairs)):
            yield Graph(n, [edge for j, edge in enumerate(pairs) if mask >> j & 1])


def cube():
    return Graph(8, ((i, i ^ (1 << b)) for i in range(8) for b in range(3) if i < i ^ (1 << b)))


def mobius_ladder():
    return Graph(8, tuple((i, (i + 1) % 8) for i in range(8)) + tuple((i, i + 4) for i in range(4)))


def petersen():
    outer = [(i, (i + 1) % 5) for i in range(5)]
    spokes = [(i, i + 5) for i in range(5)]
    inner = [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
    return Graph(10, outer + spokes + inner)


class FormulaPopulationTests(unittest.TestCase):
    def test_formulas_equal_both_enumerators_on_all_graphs_through_four_vertices(self):
        checked = 0
        for graph in all_graphs(4):
            with self.subTest(graph=graph):
                self.assertEqual(low_volume_local(graph), local_coefficients(graph, 3))
                self.assertEqual(low_volume_normalized(graph), normalized_coefficients(graph, 3))
                self.assertEqual(low_volume_marked(graph), marked_coefficients(graph, 3))
                self.assertEqual(low_volume_marked(graph), chain_marked_coefficients(graph, 3))
            checked += 1
        self.assertEqual(checked, 75)

    def test_classification_is_disjoint_and_exhaustive(self):
        for graph in (Graph(1), Graph(3, [(0, 1)]), GRAPHS["binary_g"], petersen()):
            sizes = {label: sum(row.values()) for label, row in pattern_sectors(graph).items()}
            n = graph.n
            self.assertEqual(sizes, {
                "e_i": n, "2e_i": n, "e_i+e_j": comb(n, 2),
                "3e_i": n, "2e_i+e_j": n * (n - 1), "e_i+e_j+e_k": comb(n, 3),
            })
            # Pattern sizes add to the weak-composition counts C(m+n-1, n-1).
            self.assertEqual(sizes["e_i"], comb(n, n - 1))
            self.assertEqual(sizes["2e_i"] + sizes["e_i+e_j"], comb(n + 1, n - 1))
            self.assertEqual(sizes["3e_i"] + sizes["2e_i+e_j"] + sizes["e_i+e_j+e_k"], comb(n + 2, n - 1))

    def test_statistics_are_defined_without_profiles(self):
        graph = GRAPHS["spectral_g"]
        pairs = ordered_pair_statistics(graph)
        self.assertEqual(sum(pairs.values()), 42)
        self.assertEqual(sum(c for (_, _, adjacent), c in pairs.items() if adjacent), 2 * len(graph.edges))
        for (a, b, adjacent), count in pairs.items():
            self.assertEqual(pairs[b, a, adjacent], count)
        triples = triple_statistics(graph)
        self.assertEqual(sum(triples.values()), 35)
        self.assertEqual(sum(c for (_, t), c in triples.items() if t == 3), 1)  # one triangle
        self.assertEqual(degree_histogram(graph), {1: 3, 2: 2, 3: 1, 4: 1})

    def test_unordered_two_plus_one_sum_would_be_wrong(self):
        # 2e_i+e_j is ordered: (2,1,0) and (1,2,0) differ.  Halving it breaks the count.
        graph = Graph(3, [(0, 1)])
        sector = pattern_sectors(graph)["2e_i+e_j"]
        self.assertEqual(sum(sector.values()), 6)
        direct = Counter()
        for i in range(3):
            for j in range(3):
                if i != j:
                    a = [0, 0, 0]
                    a[i], a[j] = 2, 1
                    direct[graph.energy(a)] += 1
        self.assertEqual(sector, dict(direct))

    def test_small_order_translation_boundaries(self):
        point = Graph(1)
        self.assertEqual(low_volume_local(point), [{0: 1}] * 4)
        self.assertEqual(low_volume_normalized(point), [{0: 1}, {}, {}, {}])
        self.assertEqual(low_volume_marked(point), {(0, 0, 0): 1})
        edge = Graph(2, [(0, 1)])
        # n=2: [x^2]B = C_2 - C_0 removes (1,1); [x^3]B = C_3 - C_1 removes (2,1),(1,2).
        self.assertEqual(low_volume_local(edge)[2], {0: 1, 4: 2})
        self.assertEqual(low_volume_normalized(edge), [{0: 1}, {1: 2}, {4: 2}, {9: 2}])
        path = Graph(3, [(0, 1), (1, 2)])
        # n=3: the binary triple (1,1,1) is translation, not a span-one profile.
        self.assertNotIn((3, 0, 1), low_volume_marked(path))
        self.assertEqual(low_volume_local(path)[3][0], 1)

    def test_regular_graphs_follow_order_degree_and_triangles(self):
        cases = [
            (cube(), 3, 0), (mobius_ladder(), 3, 0), (petersen(), 3, 0),
            (Graph(4, combinations(range(4), 2)), 3, 4),
            (Graph(5, [(i, (i + 1) % 5) for i in range(5)]), 2, 0),
            (Graph(6, [(i, j) for i in range(3) for j in range(3, 6)]), 3, 0),
            (Graph(6, [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)]), 2, 2),
        ]
        for graph, degree, triangles in cases:
            with self.subTest(n=graph.n, degree=degree, triangles=triangles):
                self.assertEqual(set(graph.degrees), {degree})
                expected = regular_low_volume_local(graph.n, degree, triangles)
                self.assertEqual(low_volume_local(graph), expected)
                self.assertEqual(local_coefficients(graph, 3), expected)
        # SNG-I008: same (n, degree, triangles) gives equal marked prefixes.
        self.assertEqual(marked_coefficients(cube(), 3), marked_coefficients(mobius_ladder(), 3))
        with self.assertRaises(ValueError):
            regular_low_volume_local(5, 3, 0)


class FixedPairAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads((ROOT / "results/pair_acceptance.json").read_text(encoding="utf-8"))

    def test_spectral_pair_degree_pair_proof(self):
        g, h = GRAPHS["spectral_g"], GRAPHS["spectral_h"]

        def edge_degree_sum_polynomial(graph):
            return dict(Counter(graph.degrees[u] + graph.degrees[v] for u, v in graph.edges))

        j_difference = sub(edge_degree_sum_polynomial(g), edge_degree_sum_polynomial(h))
        self.assertEqual(j_difference, normalize({4: 2, 5: -4, 6: 2}))  # 2q^4(1-q)^2
        difference = sub(low_volume_local(g)[2], low_volume_local(h)[2])
        self.assertEqual(difference, from_factors(2, 2, [(1, 2), (2, 1)]))  # 2q^2(1-q)^3(1+q)
        self.assertEqual(evaluate(difference, Fraction(1, 2)), Fraction(3, 32))
        self.assertEqual(low_volume_local(g)[:2], low_volume_local(h)[:2])
        receipt = self.receipt["spectral"]
        self.assertEqual(receipt["first_marked_difference_volume"], 2)
        self.assertEqual(receipt["marked_difference_spans"], [1])
        self.assertTrue(receipt["certificate_replay_valid"])
        self.assertEqual(receipt["left"]["edge_degree_types"], [[1, 3, 2], [1, 4, 1], [2, 2, 1], [2, 4, 2], [3, 4, 1]])
        self.assertEqual(receipt["right"]["edge_degree_types"], [[1, 4, 3], [2, 2, 1], [2, 3, 2], [3, 4, 1]])

    def test_binary_pair_lower_coefficients_and_span_two_sector(self):
        g, h = GRAPHS["binary_g"], GRAPHS["binary_h"]
        sg, sh = pattern_sectors(g), pattern_sectors(h)
        for label in ("e_i", "2e_i", "e_i+e_j", "3e_i", "e_i+e_j+e_k"):
            self.assertEqual(sg[label], sh[label], label)
        difference = sub(sg["2e_i+e_j"], sh["2e_i+e_j"])
        self.assertEqual(difference, from_factors(1, 3, [(1, 1), (3, 2), (4, 2)]))
        self.assertEqual(evaluate(difference, Fraction(1, 2)), Fraction(11025, 262144))
        receipt = self.receipt["binary_census"]
        self.assertTrue(receipt["binary_census_equal"])
        self.assertEqual(receipt["left"]["binary_cut_profile"], receipt["right"]["binary_cut_profile"])
        self.assertEqual(sum(row[2] for row in receipt["left"]["binary_cut_profile"]), 128)
        self.assertEqual(receipt["first_marked_difference_volume"], 3)
        self.assertEqual(receipt["marked_difference_spans"], [2])
        self.assertEqual({row[1]: row[3] for row in receipt["marked_difference"]}, {e: int(c) for e, c in difference.items()})
        self.assertNotEqual(receipt["left"]["edge_degree_types"], receipt["right"]["edge_degree_types"])
        self.assertTrue(receipt["certificate_replay_valid"])


if __name__ == "__main__":
    unittest.main()
