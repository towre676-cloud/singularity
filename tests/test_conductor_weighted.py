import unittest
from itertools import product

from singularity.conductor import CyclotomicRing, cyclotomic_polynomial, remote_coefficient, residue_numerator
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.weighted import WeightedGraph, weighted_coefficients


class ConductorTests(unittest.TestCase):
    def test_known_cyclotomic_and_root_relations(self):
        self.assertEqual(cyclotomic_polynomial(1), (-1, 1))
        self.assertEqual(cyclotomic_polynomial(6), (1, -1, 1))
        for order in range(1, 13):
            ring = CyclotomicRing(order)
            self.assertEqual(ring.phase(order), ring.one)
            self.assertEqual(ring.reduce(ring.modulus), ring.zero)
            self.assertEqual(ring.multiply(ring.phase(1), ring.phase(order-1)), ring.one)

    def test_numerator_replays_direct_coefficients(self):
        for graph in (Graph(2, ((0, 1),)), Graph(3, ((0, 1), (1, 2)))):
            coefficients = local_coefficients(graph, 12)
            for order in (1, 2, 3, 4):
                ring = CyclotomicRing(order)
                for index, polynomial in enumerate(coefficients):
                    direct = ring.zero
                    for energy, multiplicity in polynomial.items():
                        direct = ring.add(direct, ring.scale(ring.phase(energy), multiplicity))
                    self.assertEqual(remote_coefficient(graph, order, index), direct)

    def test_remote_and_budget(self):
        graph = Graph(2, ((0, 1),))
        self.assertEqual(remote_coefficient(graph, 1, 10**100), (10**100+1,))
        with self.assertRaises(ValueError):
            residue_numerator(graph, 100, max_profiles=10)


class WeightedTests(unittest.TestCase):
    def test_hard_contraction_preserves_original_energy_and_volume(self):
        graph = WeightedGraph((1, 2, 3, 1), ((0, 1, 2), (1, 2, 1), (0, 2, 3), (2, 3, 1)))
        contracted, mapping = graph.contract(((0, 1),))
        self.assertEqual(contracted.masses, (3, 3, 1))
        self.assertEqual(contracted.edges, ((0, 1, 4), (1, 2, 1)))
        for a in product(range(4), repeat=contracted.n):
            original = tuple(a[mapping[i]] for i in range(graph.n))
            self.assertEqual(graph.energy(original), contracted.energy(a))
            self.assertEqual(graph.volume(original), contracted.volume(a))

    def test_unit_mass_replays_unweighted(self):
        weighted = WeightedGraph((1, 1, 1), ((0, 1, 1), (1, 2, 1)))
        graph = Graph(3, ((0, 1), (1, 2)))
        self.assertEqual(weighted_coefficients(weighted, 5), local_coefficients(graph, 5))

    def test_validation_and_parallel_edges(self):
        self.assertEqual(WeightedGraph((1, 1), ((0, 1, 2), (1, 0, 3))).edges, ((0, 1, 5),))
        with self.assertRaises(ValueError):
            WeightedGraph((0, 1), ())
        with self.assertRaises(ValueError):
            WeightedGraph((1, 1), ((0, 0, 1),))


if __name__ == '__main__':
    unittest.main()
