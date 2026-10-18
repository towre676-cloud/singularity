"""P20: half-open order chambers against compositions and level chains."""

from itertools import combinations, permutations, product
import unittest

from singularity.chains import chain_marked_coefficients
from singularity.chambers import (
    chamber_local_coefficients, chamber_marked_coefficients, chamber_of, chamber_profile,
    descents, gap_form,
)
from singularity.graph import Graph
from singularity.heights import local_coefficients, marked_coefficients


def all_graphs(max_n):
    for n in range(1, max_n + 1):
        pairs = list(combinations(range(n), 2))
        for mask in range(1 << len(pairs)):
            yield Graph(n, [edge for j, edge in enumerate(pairs) if mask >> j & 1])


class ChamberTests(unittest.TestCase):
    def test_complete_histograms_match_two_enumerators(self):
        graphs = 0
        for graph in all_graphs(4):
            with self.subTest(graph=graph):
                marked = chamber_marked_coefficients(graph, 6)
                self.assertEqual(marked, marked_coefficients(graph, 6))
                self.assertEqual(marked, chain_marked_coefficients(graph, 6))
                self.assertEqual(chamber_local_coefficients(graph, 6), local_coefficients(graph, 6))
            graphs += 1
        self.assertEqual(graphs, 75)

    def test_every_profile_has_exactly_one_chamber(self):
        n, top = 4, 3
        seen = {}
        for order in permutations(range(n)):
            minimum = descents(order)
            for gaps in product(range(top + 1), repeat=n):
                if any(g < m for g, m in zip(gaps, minimum)):
                    continue
                a = chamber_profile(order, gaps)
                if max(a) <= top:
                    self.assertNotIn(a, seen)
                    seen[a] = (order, gaps)
        self.assertEqual(len(seen), (top + 1) ** n)
        for a, point in seen.items():
            self.assertEqual(chamber_of(a), point)

    def test_closed_cones_would_overcount_ties(self):
        # Without strict descents, (1,1,0) lies in the cones of (2,0,1) and (2,1,0).
        a = (1, 1, 0)
        closed = [order for order in permutations(range(3))
                  if all(a[order[j - 1]] <= a[order[j]] for j in range(1, 3))]
        self.assertEqual(len(closed), 2)
        self.assertEqual(chamber_of(a), ((2, 0, 1), (0, 1, 0)))

    def test_tied_blocks_zero_profile_and_labels(self):
        self.assertEqual(chamber_of((0, 0, 0)), ((0, 1, 2), (0, 0, 0)))
        order, gaps = chamber_of((3, 1, 3, 1, 0, 3))
        self.assertEqual(order, (4, 1, 3, 0, 2, 5))
        self.assertEqual(gaps, (0, 1, 0, 2, 0, 0))
        graph = Graph(5, [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)])
        relabeled = graph.relabel((3, 0, 4, 1, 2))
        self.assertEqual(chamber_marked_coefficients(graph, 5), chamber_marked_coefficients(relabeled, 5))
        with self.assertRaises(ValueError):
            chamber_profile((1, 0, 2), (0, 0, 0))  # descent 1 > 0 needs a positive gap

    def test_gap_form_is_the_nested_boundary_matrix(self):
        graph = Graph(5, [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (1, 4)])
        for order in ((0, 1, 2, 3, 4), (4, 2, 0, 3, 1)):
            q = gap_form(graph, order)
            tops = {j: set(order[j:]) for j in range(1, 5)}
            for i in range(1, 5):
                self.assertEqual(q[i][i], graph.cut_size(tops[i]))
                for j in range(i + 1, 5):
                    inner, outer = tops[j], tops[i]
                    crossing = sum((u in inner and v not in outer) or (v in inner and u not in outer) for u, v in graph.edges)
                    self.assertEqual(q[i][j], crossing)
                    self.assertEqual(q[j][i], crossing)
            for gaps in product(range(3), repeat=5):
                if all(g >= m for g, m in zip(gaps, descents(order))):
                    a = chamber_profile(order, gaps)
                    energy = sum(q[i][j] * gaps[i] * gaps[j] for i in range(1, 5) for j in range(1, 5))
                    self.assertEqual(energy, graph.energy(a))
                    self.assertEqual(sum(a), 5 * gaps[0] + sum((5 - j) * gaps[j] for j in range(1, 5)))

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            gap_form(Graph(3), (0, 0, 1))
        with self.assertRaises(TypeError):
            chamber_marked_coefficients({"n": 2}, 2)
        with self.assertRaises((TypeError, ValueError)):
            chamber_local_coefficients(Graph(2), -1)
        with self.assertRaises(ValueError):
            chamber_of(())


if __name__ == "__main__":
    unittest.main()
