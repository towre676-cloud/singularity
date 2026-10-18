"""P17: volume-residue filters by degree selection, characters and tuples."""

from fractions import Fraction
from itertools import combinations
import unittest

from singularity.conductor import CyclotomicRing
from singularity.congruence import (
    character_average, residue_class_coefficients, twisted_series, volume_residue,
)
from singularity.graph import Graph
from singularity.heights import local_coefficients, marked_coefficients


def all_graphs(max_n):
    for n in range(1, max_n + 1):
        pairs = list(combinations(range(n), 2))
        for mask in range(1 << len(pairs)):
            yield Graph(n, [edge for j, edge in enumerate(pairs) if mask >> j & 1])


class CongruenceTests(unittest.TestCase):
    def test_three_routes_agree_on_all_graphs_through_three_vertices(self):
        # 11 graphs, volume <= 6, moduli 1..7 (composite 4, 6 included), all residues.
        checks = 0
        for graph in all_graphs(3):
            series = local_coefficients(graph, 6)
            for modulus in range(1, 8):
                for residue in range(modulus):
                    direct = residue_class_coefficients(graph, 6, modulus, residue)
                    self.assertEqual(volume_residue(series, modulus, residue), direct)
                    self.assertEqual(character_average(series, modulus, residue), direct)
                    checks += 1
        self.assertEqual(checks, 11 * 28)

    def test_three_routes_agree_on_all_graphs_with_four_vertices(self):
        # 64 graphs, volume <= 4, moduli 1..5, all residues: 960 comparisons.
        checks = 0
        for graph in all_graphs(4):
            if graph.n != 4:
                continue
            series = local_coefficients(graph, 4)
            for modulus in range(1, 6):
                for residue in range(modulus):
                    direct = residue_class_coefficients(graph, 4, modulus, residue)
                    self.assertEqual(character_average(series, modulus, residue), direct)
                    self.assertEqual(volume_residue(series, modulus, residue), direct)
                    checks += 1
        self.assertEqual(checks, 64 * 15)

    def test_residue_classes_partition_the_series(self):
        graph = Graph(4, [(0, 1), (1, 2), (2, 3), (0, 3)])
        series = local_coefficients(graph, 7)
        for modulus in (1, 3, 5, 9):
            total = [dict() for _ in series]
            for residue in range(modulus):
                for v, row in enumerate(character_average(series, modulus, residue)):
                    for e, c in row.items():
                        total[v][e] = total[v].get(e, 0) + c
            self.assertEqual([dict(sorted(r.items())) for r in total], series)

    def test_nonprimitive_powers_and_cancellation_in_the_ring(self):
        ring = CyclotomicRing(6)
        # w^2 has order 3 and w^3 order 2: their phases are still exact ring elements.
        self.assertEqual(ring.power(ring.phase(2), 3), ring.one)
        self.assertEqual(ring.power(ring.phase(3), 2), ring.one)
        twisted = twisted_series([{0: 1}, {0: 1}, {0: 1}, {0: 1}], 6, 3)
        self.assertEqual([row[0] for row in twisted], [ring.one, ring.scale(ring.one, -1), ring.one, ring.scale(ring.one, -1)])
        # The sum of all sixth roots cancels to zero in Z[t]/Phi_6.
        total = ring.zero
        for j in range(6):
            total = ring.add(total, ring.phase(j))
        self.assertEqual(total, ring.zero)

    def test_normalization_modulus_one_empty_classes_and_short_truncation(self):
        series = local_coefficients(Graph(2, [(0, 1)]), 3)
        self.assertEqual(character_average(series, 1, 5), series)
        self.assertEqual(character_average(series, 5, -1), character_average(series, 5, 4))
        # Truncation below the modulus: residue 4 has no degree in 0..3.
        self.assertEqual(character_average(series, 5, 4), [{}, {}, {}, {}])
        self.assertEqual(character_average([], 3, 1), [])

    def test_rational_coefficients_stay_exact(self):
        series = [{0: Fraction(1, 2)}, {1: Fraction(2, 3)}, {0: 1, 2: Fraction(-5, 7)}]
        self.assertEqual(character_average(series, 2, 0), [{0: Fraction(1, 2)}, {}, {0: 1, 2: Fraction(-5, 7)}])
        self.assertEqual(character_average(series, 2, 1), [{}, {1: Fraction(2, 3)}, {}])

    def test_marks_cannot_be_recovered_by_volume_filters(self):
        # Two different span sectors with the same volume class and energy.
        graph = Graph(3)
        marked = marked_coefficients(graph, 2)
        self.assertEqual(marked[2, 0, 1], 3)  # e_i + e_j
        self.assertEqual(marked[2, 0, 2], 3)  # 2 e_i
        filtered = character_average(local_coefficients(graph, 2), 2, 0)[2]
        self.assertEqual(filtered, {0: 6})  # spans 1 and 2 are merged

    def test_invalid_input(self):
        for modulus in (0, -2, True, 2.0):
            with self.assertRaises((TypeError, ValueError)):
                character_average([{0: 1}], modulus, 0)
            with self.assertRaises((TypeError, ValueError)):
                volume_residue([{0: 1}], modulus, 0)
        with self.assertRaises(TypeError):
            character_average([{0: 1.5}], 2, 0)
        with self.assertRaises(TypeError):
            character_average([{0: True}], 2, 0)
        with self.assertRaises(TypeError):
            residue_class_coefficients({"n": 1}, 2, 2, 0)


if __name__ == "__main__":
    unittest.main()
