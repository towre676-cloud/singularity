import itertools
import unittest
from fractions import Fraction

from singularity.graph import Graph
from singularity.pinned_theta import (
    affine_lift_enclosure, boundary_enclosure, coefficient_decay_bounds, pinned_coefficient,
    affine_boundary_enclosure,
    scaled_pinned_coefficient, theta_enclosure,
)


class PinnedThetaTests(unittest.TestCase):
    def setUp(self):
        self.graphs = [Graph(1), Graph(3), Graph(3, [(0, 1), (1, 2)]),
                       Graph(3, [(0, 1), (0, 2), (1, 2)])]

    @staticmethod
    def brute(graph, volume, pinning, q):
        # Product-box oracle does not use the production weak-composition route.
        return sum((q ** (sum((h[a]-h[b])**2 for a, b in graph.edges)
                          + pinning*sum(a*a for a in h))
                    for h in itertools.product(range(volume+1), repeat=graph.n)
                    if sum(h) == volume), Fraction())

    def test_raw_coefficient_and_integer_centering(self):
        t = Fraction(3, 4)
        for graph in self.graphs:
            q = t ** (graph.n*graph.n)
            for pinning in (1, 2):
                for volume in range(5):
                    raw = self.brute(graph, volume, pinning, q)
                    self.assertEqual(pinned_coefficient(graph, volume, pinning, q), raw)
                    self.assertEqual(scaled_pinned_coefficient(graph, volume, pinning, t),
                                     raw * t ** (-graph.n*pinning*volume*volume))

    def test_increasing_subsequences_and_boundary_enclosures(self):
        t = Fraction(4, 5)
        for graph in self.graphs[1:]:
            for residue in range(graph.n):
                values = [scaled_pinned_coefficient(graph, residue+k*graph.n, 2, t)
                          for k in range(3)]
                self.assertLess(values[0], values[1])
                self.assertLess(values[1], values[2])
                first = boundary_enclosure(graph, residue, 2, t)
                second = boundary_enclosure(graph, residue+graph.n, 2, t)
                self.assertLessEqual(values[2], first.upper)
                self.assertLessEqual(values[2], second.upper)
                self.assertLess(second.width, first.width)
                lattice = theta_enclosure(graph, 2, t, residue, 2)
                self.assertLessEqual(first.lower, lattice.upper)
                self.assertLessEqual(lattice.lower, first.upper)
                self.assertLessEqual(second.lower, lattice.upper)
                self.assertLessEqual(lattice.lower, second.upper)

    def test_reflection_and_nested_lattice_windows(self):
        graph = Graph(4, [(0, 1), (1, 2), (1, 3)])
        t = Fraction(4, 5)
        for residue in range(1, graph.n):
            first = theta_enclosure(graph, 1, t, residue, 1)
            reflected = theta_enclosure(graph, 1, t, graph.n-residue, 1)
            self.assertEqual(first.lower, reflected.lower)
            self.assertEqual(first.terms, reflected.terms)
            enlarged = theta_enclosure(graph, 1, t, residue, 2)
            self.assertLessEqual(first.lower, enlarged.lower)
            self.assertLessEqual(enlarged.lower, first.upper)
            self.assertLess(enlarged.width, first.width)

    def test_working_half_parameter_affine_lifts(self):
        graph = Graph(3, [(0, 1), (1, 2)])
        q, pinning = Fraction(1, 2), 2
        for residue in range(graph.n):
            window = affine_lift_enclosure(graph, pinning, q, residue, 3)
            first = affine_boundary_enclosure(graph, residue, pinning, q)
            later = affine_boundary_enclosure(graph, residue+3*graph.n, pinning, q)
            self.assertLess(first.lower, later.lower)
            self.assertLess(later.width, first.width)
            self.assertLessEqual(window.lower, later.upper)
            self.assertLessEqual(later.lower, window.upper)
            volume = residue+3*graph.n
            shift = pinning*(graph.n*9+6*residue)
            self.assertEqual(later.lower, pinned_coefficient(graph, volume, pinning, q)*q**(-shift))
        left = affine_lift_enclosure(graph, pinning, q, 1, 2)
        right = affine_lift_enclosure(graph, pinning, q, 2, 2)
        self.assertEqual(left.lower, q**(-pinning)*right.lower)

    def test_constant_one_vertex_limit(self):
        for volume in range(6):
            interval = boundary_enclosure(Graph(1), volume, 3, Fraction(1, 2))
            self.assertEqual((interval.lower, interval.upper), (1, 1))
        self.assertEqual(theta_enclosure(Graph(1), 2, Fraction(1, 2), 0, 3).width, 0)

    def test_quadratic_decay_bounds(self):
        t = Fraction(4, 5)
        for graph in self.graphs:
            for pinning in (1, 2, 3):
                q = t ** (graph.n*graph.n)
                for volume in range(6):
                    value = pinned_coefficient(graph, volume, pinning, q)
                    bounds = coefficient_decay_bounds(graph, volume, pinning, t)
                    self.assertLessEqual(bounds.lower, value)
                    self.assertLessEqual(value, bounds.upper)

    def test_relabeling(self):
        graph = Graph(4, [(0, 1), (1, 2), (1, 3)])
        other = graph.relabel((2, 0, 3, 1))
        for residue in range(graph.n):
            self.assertEqual(theta_enclosure(graph, 2, Fraction(3, 4), residue, 1),
                             theta_enclosure(other, 2, Fraction(3, 4), residue, 1))

    def test_rejects_inexact_invalid_and_over_budget_inputs(self):
        graph = Graph(3, [(0, 1)])
        for value in (True, 0.5, "1/2"):
            with self.assertRaises(TypeError):
                theta_enclosure(graph, 2, value, 0, 1)
        for value in (0, 1, Fraction(3, 2)):
            with self.assertRaises(ValueError):
                boundary_enclosure(graph, 0, 2, value)
        with self.assertRaises(ValueError):
            theta_enclosure(graph, 0, Fraction(1, 2), 0, 1)
        with self.assertRaises(ValueError):
            theta_enclosure(graph, 2, Fraction(1, 2), 3, 1)
        with self.assertRaises(ValueError):
            theta_enclosure(graph, 2, Fraction(1, 2), 0, 4, max_states=2)
        with self.assertRaises(ValueError):
            pinned_coefficient(graph, 8, 2, Fraction(1, 2), max_states=2)
        with self.assertRaises(TypeError):
            scaled_pinned_coefficient(graph, True, 2, Fraction(1, 2))


if __name__ == '__main__':
    unittest.main()
