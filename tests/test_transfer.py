"""Forest messages cross-checked against Cartesian and composition oracles."""

from math import comb
import random
import unittest

from itertools import combinations, product

from singularity.chains import chain_local_coefficients, chain_marked_coefficients
from singularity.graph import Graph
from singularity.heights import local_coefficients, marked_coefficients, normalized_coefficients
from singularity.transfer import (
    bounded_height_histogram, brute_bounded_height_histogram, histogram_coefficients,
    marked_forest_coefficients, root_messages, transfer_statistics,
)


def named_trees():
    """Fixed acceptance trees with their original labels."""
    return {
        "path7": Graph(7, [(i, i + 1) for i in range(6)]),
        "star7": Graph(7, [(0, i) for i in range(1, 7)]),
        "balanced7": Graph(7, [(i, (i - 1) // 2) for i in range(1, 7)]),
        "branched8": Graph(8, [(0, 1), (1, 2), (1, 3), (3, 4), (3, 5), (5, 6), (0, 7)]),
        "forest7": Graph(7, [(0, 1), (1, 2), (3, 4), (3, 5)]),
    }


def all_forests(max_n):
    for n in range(1, max_n + 1):
        pairs = list(combinations(range(n), 2))
        for mask in range(1 << len(pairs)):
            edges = [edge for j, edge in enumerate(pairs) if mask >> j & 1]
            graph = Graph(n, edges)
            if len(edges) == n - len(graph.components()):
                yield graph


class TreeTransferTests(unittest.TestCase):
    def test_named_trees_against_cartesian_and_chain_oracles(self):
        for name, graph in named_trees().items():
            for height in (0, 1, 2):
                for min_zero in (False, True):
                    with self.subTest(tree=name, height=height, normalized=min_zero):
                        self.assertEqual(
                            bounded_height_histogram(graph, height, min_zero=min_zero),
                            brute_bounded_height_histogram(graph, height, min_zero=min_zero),
                        )
            # H=R reaches the unrestricted prefix, checked against level chains.
            local = bounded_height_histogram(graph, 4, max_volume=4)
            self.assertEqual(histogram_coefficients(local, 4), chain_local_coefficients(graph, 4), name)

    def test_root_messages_condition_on_the_least_label(self):
        graph = named_trees()["branched8"]
        messages = root_messages(graph, 2)
        self.assertEqual(list(messages), [0])
        for t, histogram in enumerate(messages[0]):
            expected = {}
            for a in product(range(3), repeat=graph.n):
                if a[0] == t:
                    key = sum(a), graph.energy(a)
                    expected[key] = expected.get(key, 0) + 1
            self.assertEqual(histogram, dict(sorted(expected.items())))
        forest = named_trees()["forest7"]
        self.assertEqual(sorted(root_messages(forest, 1)), [0, 3, 6])

    def test_cost_measures_are_separate(self):
        graph = named_trees()["star7"]
        stats = transfer_statistics(graph, 3, max_volume=5)
        self.assertEqual(stats["height_states"], 7 * 4)
        self.assertEqual(stats["output_support_cells"], len(bounded_height_histogram(graph, 3, max_volume=5)))
        self.assertGreaterEqual(stats["message_support_cells"], stats["max_message_support"])
        self.assertGreater(stats["max_count_bits"], 0)

    def test_marked_forest_span_subtraction_all_small_forests(self):
        # Declared population: every labeled forest on 1..5 vertices, volume <= 5.
        forests = cells = 0
        for graph in all_forests(5):
            marked = marked_forest_coefficients(graph, 5)
            self.assertEqual(marked, marked_coefficients(graph, 5), graph)
            forests += 1
            cells += len(marked)
        self.assertEqual(forests, 1 + 2 + 7 + 38 + 291)
        for name, graph in named_trees().items():
            with self.subTest(tree=name):
                self.assertEqual(marked_forest_coefficients(graph, 6), chain_marked_coefficients(graph, 6))
                normalized = [{} for _ in range(7)]
                for (v, e, _), c in marked_forest_coefficients(graph, 6).items():
                    normalized[v][e] = normalized[v].get(e, 0) + c
                self.assertEqual([dict(sorted(r.items())) for r in normalized], normalized_coefficients(graph, 6))

    def test_marked_forest_boundaries(self):
        self.assertEqual(marked_forest_coefficients(Graph(1), 4), {(0, 0, 0): 1})
        self.assertEqual(marked_forest_coefficients(Graph(3, [(0, 1)]), 0), {(0, 0, 0): 1})
        # Span cap: only spans 0 and 1 survive, matching the reference cells.
        graph = Graph(3, [(0, 1), (1, 2)])
        capped = marked_forest_coefficients(graph, 5, max_span=1)
        self.assertEqual(capped, {k: c for k, c in marked_coefficients(graph, 5).items() if k[2] <= 1})
        # Crossing volume n: (1,1,0) on a disconnected forest is globally normalized.
        self.assertEqual(marked_forest_coefficients(Graph(3, [(0, 1)]), 2)[2, 0, 1], 1)
        for bad in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                marked_forest_coefficients(graph, bad)
        with self.assertRaises(ValueError):
            marked_forest_coefficients(Graph(3, [(0, 1), (1, 2), (0, 2)]), 2)

    def test_unrestricted_large_tree_independent_moments(self):
        # H=R=8 on a 40-vertex branched tree: every profile of volume <= 8.
        n, bound = 40, 8
        graph = Graph(n, [(i, (i - 1) // 3) for i in range(1, n)])
        histogram = bounded_height_histogram(graph, bound, max_volume=bound)
        sides = []
        for u, v in graph.edges:
            # Size of the side containing v after deleting edge uv.
            stack, seen = [v], {u, v}
            while stack:
                for w in graph.neighbors[stack.pop()]:
                    if w not in seen:
                        seen.add(w)
                        stack.append(w)
            sides += [len(seen) - 1, n - len(seen) + 1]
        for volume in range(bound + 1):
            row = {e: c for (v, e), c in histogram.items() if v == volume}
            # Stars and bars, the first energy moment and the energy-one
            # profiles (one edge cut, sides at heights 0 and 1) are
            # independent of the message recursion.
            self.assertEqual(sum(row.values()), comb(volume + n - 1, n - 1))
            self.assertEqual(sum(e * c for e, c in row.items()), (n - 1) * 2 * comb(volume + n, n + 1))
            self.assertEqual(row.get(1, 0), sides.count(volume))
            self.assertEqual(row.get(0, 0), int(volume == 0))

    def test_sparse_high_energy_pruning_and_disconnected_budget(self):
        star = Graph(6, [(0, i) for i in range(1, 6)])
        full = bounded_height_histogram(star, 9)
        for budget in (0, 3, 9, 20):
            expected = {k: c for k, c in full.items() if k[0] <= budget}
            self.assertEqual(bounded_height_histogram(star, 9, max_volume=budget), expected)
        self.assertEqual(max(e for _, e in full), 5 * 81)
        forest = named_trees()["forest7"]
        full = bounded_height_histogram(forest, 3, min_zero=True)
        for budget in (0, 6, 7, 8, 13):
            expected = {k: c for k, c in full.items() if k[0] <= budget}
            self.assertEqual(bounded_height_histogram(forest, 3, max_volume=budget, min_zero=True), expected)

    def test_all_small_labeled_forests_randomized(self):
        rng = random.Random(20261017)
        for n in range(1, 8):
            for trial in range(4):
                # Choosing zero or one earlier parent cannot form a cycle.
                edges = [(i, rng.randrange(i)) for i in range(1, n) if rng.randrange(4)]
                graph = Graph(n, edges)
                for height in (0, 1, 2):
                    for min_zero in (False, True):
                        with self.subTest(n=n, trial=trial, height=height, normalized=min_zero):
                            self.assertEqual(
                                bounded_height_histogram(graph, height, min_zero=min_zero),
                                brute_bounded_height_histogram(graph, height, min_zero=min_zero),
                            )

    def test_total_counts_and_independent_isolated_polynomial(self):
        for n in (1, 2, 5):
            graph = Graph(n)
            for height in range(4):
                raw = bounded_height_histogram(graph, height)
                normalized = bounded_height_histogram(graph, height, min_zero=True)
                self.assertEqual(sum(raw.values()), (height + 1) ** n)
                self.assertEqual(sum(normalized.values()), (height + 1) ** n - height ** n)
                self.assertTrue(all(energy == 0 for _, energy in raw))
        # In the unconstrained low-volume range, stars-and-bars is independent.
        histogram = bounded_height_histogram(Graph(6), 8, max_volume=8)
        self.assertEqual(histogram, {(v, 0): comb(v + 5, 5) for v in range(9)})

    def test_volume_pruning_matches_unpruned_population(self):
        graph = Graph(7, [(0, 1), (1, 2), (1, 3), (3, 4), (3, 5), (5, 6)])
        full = bounded_height_histogram(graph, 3)
        for budget in (0, 1, 4, 9, 50):
            expected = {key: count for key, count in full.items() if key[0] <= budget}
            self.assertEqual(bounded_height_histogram(graph, 3, max_volume=budget), expected)

    def test_large_population_against_inclusion_exclusion(self):
        # A nonenumerable cube, checked by the independent closed volume count
        # [x^v](1+x+x²)^n = sum_j (-1)^j*C(n,j)*C(v-3j+n-1,n-1).
        n, height, budget = 96, 2, 12
        graph = Graph(n, [(i, i + 1) for i in range(n - 1)])
        histogram = bounded_height_histogram(graph, height, max_volume=budget)
        for volume in range(budget + 1):
            expected = sum((-1) ** j * comb(n, j) * comb(volume - 3 * j + n - 1, n - 1) for j in range(volume // 3 + 1))
            self.assertEqual(sum(c for (v, _), c in histogram.items() if v == volume), expected)
        self.assertEqual(sum(histogram.values()), 2506262962660245)

    def test_low_coefficients_equal_unbounded_composition_engine(self):
        graph = Graph(6, [(0, 1), (0, 2), (2, 3), (3, 4)])
        volume = 5
        local = bounded_height_histogram(graph, volume, max_volume=volume)
        normalized = bounded_height_histogram(graph, volume, max_volume=volume, min_zero=True)
        self.assertEqual(histogram_coefficients(local, volume), local_coefficients(graph, volume))
        self.assertEqual(histogram_coefficients(normalized, volume), normalized_coefficients(graph, volume))

    def test_global_shift_subtraction_on_disconnected_forest(self):
        graph = Graph(5, [(0, 1), (2, 3)])
        raw = bounded_height_histogram(graph, 2)
        previous = bounded_height_histogram(graph, 1)
        expected = dict(raw)
        for (volume, energy), count in previous.items():
            key = volume + graph.n, energy
            expected[key] -= count
            if expected[key] == 0:
                del expected[key]
        self.assertEqual(bounded_height_histogram(graph, 2, min_zero=True), expected)

    def test_relabeling_preserves_counts(self):
        graph = Graph(6, [(0, 1), (0, 2), (2, 3), (3, 4), (2, 5)])
        permutation = (5, 3, 4, 0, 2, 1)
        self.assertEqual(
            bounded_height_histogram(graph, 3, max_volume=7, min_zero=True),
            bounded_height_histogram(graph.relabel(permutation), 3, max_volume=7, min_zero=True),
        )

    def test_cycles_are_rejected_and_bounds_validated(self):
        triangle = Graph(3, [(0, 1), (1, 2), (0, 2)])
        with self.assertRaises(ValueError):
            bounded_height_histogram(triangle, 0)
        # Brute-force deliberately remains valid on the same graph.
        self.assertEqual(sum(brute_bounded_height_histogram(triangle, 2).values()), 27)
        for height in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                bounded_height_histogram(Graph(1), height)
        with self.assertRaises(ValueError):
            bounded_height_histogram(Graph(1), 2, max_volume=-1)


if __name__ == "__main__":
    unittest.main()
