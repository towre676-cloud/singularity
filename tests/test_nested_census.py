"""P14: the nested-pair census, its span-two projection and the binary pair."""

from collections import Counter
from itertools import combinations
import unittest

from singularity.chains import chain_marked_coefficients
from singularity.examples import GRAPHS
from singularity.graph import Graph
from singularity.heights import marked_coefficients
from singularity.nested_census import (
    binary_marginal, census_difference, nested_pair_census, reflect, span_two_projection,
)


def all_graphs(max_n):
    for n in range(1, max_n + 1):
        pairs = list(combinations(range(n), 2))
        for mask in range(1 << len(pairs)):
            yield Graph(n, [edge for j, edge in enumerate(pairs) if mask >> j & 1])


def span_two(marked):
    return {(v, e): c for (v, e, h), c in marked.items() if h == 2}


class NestedCensusTests(unittest.TestCase):
    def test_raw_total_reflection_and_projection_on_all_small_graphs(self):
        for graph in all_graphs(4):
            census = nested_pair_census(graph)
            self.assertEqual(sum(census.values()), 3 ** graph.n)
            self.assertEqual(reflect(census, graph.n), census)
            bound = 2 * (graph.n - 1)
            expected = span_two(marked_coefficients(graph, bound)) if graph.n > 1 else {}
            self.assertEqual(span_two_projection(census, graph.n), expected, graph)

    def test_projection_matches_both_enumerators_on_reference_pairs(self):
        for name in ("binary_g", "binary_h", "spectral_g"):
            graph = GRAPHS[name]
            projection = span_two_projection(nested_pair_census(graph), graph.n)
            self.assertEqual(projection, span_two(chain_marked_coefficients(graph, 12)))
            self.assertEqual(projection, span_two(marked_coefficients(graph, 12)))

    def test_binary_pair_cells(self):
        g, h = nested_pair_census(GRAPHS["binary_g"]), nested_pair_census(GRAPHS["binary_h"])
        self.assertEqual(binary_marginal(g), binary_marginal(h))  # SNG-E003
        difference = census_difference(g, h)
        low = {k: v for k, v in difference.items() if k[0] + k[1] <= 3}
        # Only S = {i, j}, T = {i} differs at volume 3: cells (d_i+d_j-2A, d_i, d_i-A).
        self.assertTrue(all(k[:2] == (2, 1) for k in low))
        graph_g, graph_h = GRAPHS["binary_g"], GRAPHS["binary_h"]

        def ordered_pairs(graph):
            out = Counter()
            edges = set(graph.edges)
            d = graph.degrees
            for i in range(7):
                for j in range(7):
                    if i != j:
                        a = int((min(i, j), max(i, j)) in edges)
                        out[2, 1, d[i] + d[j] - 2 * a, d[i], d[i] - a] += 1
            return out

        expected = Counter(ordered_pairs(graph_g))
        expected.subtract(ordered_pairs(graph_h))
        self.assertEqual(low, {k: v for k, v in expected.items() if v})
        # Projecting to energy cs + ct + 2x recovers the factorized discrepancy.
        energy = Counter()
        for (s, t, cs, ct, x), c in low.items():
            energy[cs + ct + 2 * x] += c
        self.assertEqual({e: c for e, c in energy.items() if c},
                         {3: 1, 4: -1, 6: -2, 8: 2, 9: 1, 10: 3, 11: -3, 12: -1, 13: -2, 15: 2, 17: 1, 18: -1})

    def test_gap_profiles_are_kept(self):
        census = nested_pair_census(Graph(3, [(0, 1), (1, 2)]))
        # T = S = {1, 2}: the profile (0, 2, 2), cut 1 twice and crossing 1.
        self.assertGreaterEqual(census[2, 2, 1, 1, 1], 1)
        with self.assertRaises(TypeError):
            nested_pair_census({"n": 2})


if __name__ == "__main__":
    unittest.main()
