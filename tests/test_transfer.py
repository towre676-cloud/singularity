"""Forest messages cross-checked against Cartesian and composition oracles."""

from math import comb
import random
import unittest

from singularity.graph import Graph
from singularity.heights import local_coefficients, normalized_coefficients
from singularity.transfer import (
    bounded_height_histogram, brute_bounded_height_histogram, histogram_coefficients,
)


class TreeTransferTests(unittest.TestCase):
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
