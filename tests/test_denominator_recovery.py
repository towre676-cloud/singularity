"""FR02: exact rational inversion, independent populations, and strict scope."""

from fractions import Fraction
from itertools import combinations
from math import comb
import unittest

from singularity.denominator_recovery import (
    denominator_depth, recover_degree_extremum, recovery_volume,
    reconstruct_complete_split,
)
from singularity.graph import Graph


def direct_coefficient(graph, q, volume, shift=0):
    # Stars and bars, rather than the decoder or the project's composition API.
    counts = {}
    for bars in combinations(range(volume + graph.n - 1), graph.n - 1):
        stops = (-1,) + bars + (volume + graph.n - 1,)
        heights = tuple(stops[i + 1] - stops[i] - 1 for i in range(graph.n))
        energy = sum((heights[u] - heights[v]) ** 2 for u, v in graph.edges)
        energy += shift * sum(h * h for h in heights)
        counts[energy] = counts.get(energy, 0) + 1
    return sum((count * q ** energy for energy, count in counts.items()), Fraction())


class DenominatorRecoveryTests(unittest.TestCase):
    def test_strict_volume_cutoff_at_exact_powers(self):
        self.assertEqual(recovery_volume(3, Fraction(1, 2)), 2)
        self.assertEqual(recovery_volume(4, Fraction(1, 2)), 3)
        self.assertEqual(recovery_volume(16, Fraction(1, 2)), 4)
        self.assertEqual(recovery_volume(35, Fraction(5, 6)), 2)
        self.assertEqual(recovery_volume(36, Fraction(5, 6)), 3)

    def test_every_labeled_graph_through_order_four_in_both_series(self):
        checked = 0
        for n in range(1, 5):
            edges = list(combinations(range(n), 2))
            for mask in range(1 << len(edges)):
                graph = Graph(n, [e for i, e in enumerate(edges) if mask >> i & 1])
                for q in (Fraction(1, 2), Fraction(2, 3), Fraction(5, 6)):
                    volume = recovery_volume(n, q)
                    for shift in (0, 2):
                        value = direct_coefficient(graph, q, volume, shift)
                        result = recover_degree_extremum(n, q, value, diagonal_shift=shift)
                        self.assertEqual(result.maximum_degree, max(graph.degrees))
                        self.assertEqual(result.multiplicity, graph.degrees.count(max(graph.degrees)))
                        checked += 1
        self.assertEqual(checked, 450)

    def test_composite_base_clearing_is_not_a_prime_valuation(self):
        self.assertEqual(denominator_depth(72, 6), 3)
        self.assertEqual(denominator_depth(8, 12), 2)
        self.assertEqual(denominator_depth(18, 12), 2)
        self.assertEqual(denominator_depth(1, 6), 0)
        with self.assertRaises(ValueError):
            denominator_depth(5, 6)
        with self.assertRaises(ValueError):
            denominator_depth(72, 6, max_depth=2)

    def test_divisible_extremal_multiplicity_is_recovered(self):
        for n, q in ((4, Fraction(3, 4)), (6, Fraction(5, 6)), (12, Fraction(5, 6))):
            graph = Graph(n, combinations(range(n), 2))
            volume = recovery_volume(n, q)
            result = recover_degree_extremum(n, q, direct_coefficient(graph, q, volume))
            self.assertEqual((result.maximum_degree, result.multiplicity), (n - 1, n))
            self.assertLess(result.denominator_depth, result.maximum_energy)

    def test_lower_degree_spike_controls_the_gap(self):
        # At R=2, Delta=4 the nonsingle gap would be 8, but a degree-3
        # spike is only four energy units below the maximum.
        graph = Graph(5, list(combinations(range(4), 2)) + [(0, 4)])
        q = Fraction(2, 3)
        result = recover_degree_extremum(5, q, direct_coefficient(graph, q, 2))
        self.assertEqual((result.maximum_degree, result.multiplicity), (4, 1))
        self.assertEqual(result.energy_gap, 4)

    def test_edgeless_pinned_and_unpinned_cases_are_distinct(self):
        for n in (1, 3, 8):
            graph, q = Graph(n), Fraction(1, 2)
            volume = recovery_volume(n, q)
            raw = recover_degree_extremum(n, q, Fraction(comb(n + volume - 1, volume)))
            pinned = recover_degree_extremum(n, q, direct_coefficient(graph, q, volume, 2), diagonal_shift=2)
            self.assertEqual((raw.maximum_degree, raw.multiplicity), (0, n))
            self.assertEqual((pinned.maximum_degree, pinned.multiplicity), (0, n))
            self.assertEqual(raw.maximum_energy, 0)
            self.assertEqual(pinned.maximum_energy, 2 * volume * volume)

    def test_known_complete_split_family_reconstruction(self):
        for n in range(1, 8):
            for clique in range(n + 1):
                graph = Graph(n, [(u, v) for u, v in combinations(range(n), 2) if u < clique or v < clique])
                q = Fraction(1, 2)
                volume = recovery_volume(n, q)
                for shift in (0, 2):
                    actual = reconstruct_complete_split(n, q, direct_coefficient(graph, q, volume, shift), diagonal_shift=shift)
                    expected = (n, 0) if clique >= n - 1 else (clique, n - clique)
                    self.assertEqual(actual, expected)

    def test_larger_than_minimal_observation_volume_is_valid(self):
        graph, q = Graph(4, [(0, 1), (1, 2), (2, 3)]), Fraction(5, 6)
        result = recover_degree_extremum(4, q, direct_coefficient(graph, q, 5), volume=5)
        self.assertEqual((result.maximum_degree, result.multiplicity), (2, 2))

    def test_strict_validation_and_impossible_coefficients(self):
        for bad in (True, 2.0, "2"):
            with self.assertRaises(TypeError):
                recovery_volume(bad, Fraction(1, 2))
        for bad in (0.5, True, "1/2"):
            with self.assertRaises(TypeError):
                recovery_volume(4, bad)
        for q in (Fraction(0), Fraction(1), Fraction(-1, 2)):
            with self.assertRaises(ValueError):
                recovery_volume(4, q)
        with self.assertRaises(ValueError):
            recover_degree_extremum(4, Fraction(1, 2), Fraction(1), volume=2)
        for value in (Fraction(0), Fraction(-1), Fraction(1000), Fraction(1, 5), Fraction(1)):
            with self.assertRaises(ValueError):
                recover_degree_extremum(3, Fraction(1, 2), value)
        with self.assertRaises(ValueError):
            recover_degree_extremum(3, Fraction(1, 2), Fraction(10), diagonal_shift=2)
        with self.assertRaises(ValueError):
            recover_degree_extremum(3, Fraction(1, 2), Fraction(10), diagonal_shift=-1)
        for bad in (0.5, True, "1/2"):
            with self.assertRaises(TypeError):
                recover_degree_extremum(3, Fraction(1, 2), bad)


if __name__ == "__main__":
    unittest.main()
