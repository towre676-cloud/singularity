import unittest
from fractions import Fraction
from itertools import product

from singularity.graph import Graph
from singularity.pole_divisors import (
    anchored_gaussian_box, divisor_sum_profile, pole_order_certificate,
    recover_component_sizes, theta_upper, uniform_zero_free,
)


def union(*graphs):
    edges, offset = [], 0
    for graph in graphs:
        edges.extend((u + offset, v + offset) for u, v in graph.edges)
        offset += graph.n
    return Graph(offset, edges)


class PoleDivisorTests(unittest.TestCase):
    def test_edge_character_against_one_dimensional_theta(self):
        q = Fraction(1, 2)
        box = anchored_gaussian_box(Graph(2, [(0, 1)]), q, 2, 4)
        expected = sum(((-1 if z % 2 else 1) * q ** (z*z) for z in range(-4, 5)), Fraction())
        self.assertEqual(box.coefficients, (expected,))
        self.assertGreater(expected - box.absolute_error, 0)
        self.assertEqual(box.profiles, 9)

    def test_triangle_character_against_direct_rooted_coordinates(self):
        q = Fraction(1, 3)
        graph = Graph(3, [(0, 1), (1, 2), (0, 2)])
        box = anchored_gaussian_box(graph, q, 3, 2)
        residue = [Fraction(), Fraction(), Fraction()]
        for a, b in product(range(-2, 3), repeat=2):
            residue[(a+b) % 3] += q ** (a*a+b*b+(a-b)**2)
        self.assertEqual(box.coefficients, (residue[0]-residue[2], residue[1]-residue[2]))
        self.assertEqual(box.coefficients[1], 0)
        self.assertGreater(box.coefficients[0]-box.absolute_error, 0)

    def test_tree_change_boxes_overlap_with_certified_tail(self):
        # Rooted trees give different finite truncation sets. Their rational
        # character sums must nonetheless enclose the same infinite value.
        q = Fraction(1, 4)
        a = Graph(3, [(0, 1), (1, 2)])
        b = Graph(3, [(0, 1), (0, 2)])
        x = anchored_gaussian_box(a, q, 3, 3)
        y = anchored_gaussian_box(b, q, 3, 3)
        self.assertEqual(x.coefficients[1], 0)
        self.assertEqual(y.coefficients[1], 0)
        self.assertLessEqual(abs(x.coefficients[0]-y.coefficients[0]), x.absolute_error+y.absolute_error)

    def test_single_vertex_exact_and_parameter_boundaries(self):
        box = anchored_gaussian_box(Graph(1), Fraction(1, 2), 1, 0)
        self.assertEqual(box.coefficients, (Fraction(1),))
        self.assertEqual(box.absolute_error, 0)
        for q in (0, 1, -1, Fraction(3, 2), 0.5, True):
            with self.assertRaises(ValueError):
                theta_upper(q)

    def test_theta_tail_bounds_independent_longer_sum(self):
        for q in (Fraction(1, 2), Fraction(1, 3), Fraction(1, 16)):
            for cutoff in (0, 1, 3):
                lower = 1 + 2*sum((q ** (k*k) for k in range(1, 31)), Fraction())
                self.assertGreater(theta_upper(q, cutoff), lower)
        self.assertTrue(uniform_zero_free(Fraction(1, 16), 6))
        self.assertFalse(uniform_zero_free(Fraction(1, 2), 3))

    def test_profile_inversion_matches_component_population(self):
        sizes = (1, 1, 2, 3, 3, 6)
        profile = divisor_sum_profile(sizes)
        self.assertEqual(profile, {1: 6, 2: 2, 3: 3, 4: 0, 5: 0, 6: 1})
        self.assertEqual(recover_component_sizes(profile), {1: 2, 2: 1, 3: 2, 6: 1})
        with self.assertRaises(ValueError):
            recover_component_sizes({1: 0, 2: 1})
        with self.assertRaises(ValueError):
            recover_component_sizes({1: 1, 3: 1})

    def test_disconnected_cancellation_is_not_assumed_away(self):
        graph = union(Graph(2, [(0, 1)]), Graph(3, [(0, 1), (1, 2)]))
        unsafe = pole_order_certificate(graph, Fraction(1, 2))
        self.assertFalse(unsafe["complete"])
        self.assertEqual(unsafe["orders"], {1: 2})
        self.assertEqual(unsafe["unknown_orders"], (2, 3))
        safe = pole_order_certificate(graph, Fraction(1, 16))
        self.assertTrue(safe["complete"])
        self.assertEqual(safe["orders"], {1: 2, 2: 1, 3: 1})

    def test_same_size_components_and_isolates_all_positive_q(self):
        triangle = Graph(3, [(0, 1), (1, 2), (0, 2)])
        path = Graph(3, [(0, 1), (1, 2)])
        result = pole_order_certificate(union(triangle, path, Graph(1)), Fraction(99, 100))
        self.assertTrue(result["complete"])
        self.assertEqual(result["orders"], {1: 3, 2: 0, 3: 2})
        self.assertEqual(recover_component_sizes(result["orders"]), {1: 1, 3: 2})

    def test_connected_all_roots_and_safe_refusals(self):
        graph = Graph(4, [(0, 1), (1, 2), (2, 3)])
        certificate = pole_order_certificate(graph, Fraction(1, 2))
        self.assertEqual(certificate["orders"], {1: 1, 2: 1, 3: 0, 4: 1})
        with self.assertRaises(ValueError):
            anchored_gaussian_box(graph, Fraction(1, 2), 3, 2)
        with self.assertRaises(ValueError):
            anchored_gaussian_box(Graph(2), Fraction(1, 2), 2, 2)
        with self.assertRaisesRegex(ValueError, "budget"):
            anchored_gaussian_box(graph, Fraction(1, 2), 4, 10, max_profiles=10)


if __name__ == "__main__":
    unittest.main()
