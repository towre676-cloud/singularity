"""SNG-F36/F37: the pendant-cycle family with visibility depth p + 1."""

from fractions import Fraction
import unittest

from singularity.euler import first_difference
from singularity.families import (
    binary_discrepancy_closed_form, binary_discrepancy_enumerated, chebyshev_u, decorated_deck,
    first_discrepancy, optimal_probe, pendant_cycle,
)
from singularity.heights import local_coefficients, marked_coefficients
from singularity.invariants import laplacian_characteristic_polynomial
from singularity.parameters import vanishes_at
from singularity.polynomials import derivative, evaluate, from_factors, mul


class PendantCycleTests(unittest.TestCase):
    def test_first_difference_volume_and_polynomial(self):
        for l, p in ((3, 2), (4, 2), (4, 3), (5, 3), (5, 4), (6, 4)):
            a = local_coefficients(pendant_cycle(l, p), p + 1)
            b = local_coefficients(pendant_cycle(l, l), p + 1)
            with self.subTest(l=l, p=p):
                self.assertEqual(first_difference(a, b), (p + 1, first_discrepancy(p)))

    def test_discrepancy_is_binary_and_marked_prefix_agrees(self):
        l, p = 5, 3
        left, right = marked_coefficients(pendant_cycle(l, p), p + 1), marked_coefficients(pendant_cycle(l, l), p + 1)
        cells = {k for k in left.keys() | right.keys() if left.get(k, 0) != right.get(k, 0)}
        self.assertEqual({(v, h) for v, _, h in cells}, {(p + 1, 1)})

    def test_closed_binary_form_against_all_subsets(self):
        for l in range(2, 7):
            for p in range(1, l):
                with self.subTest(l=l, p=p):
                    self.assertEqual(binary_discrepancy_closed_form(l, p), binary_discrepancy_enumerated(l, p))
        self.assertEqual(chebyshev_u(2), {(0, 0): 1, (1, 0): 1})

    def test_decorated_decks_agree_exactly_below_p_plus_one(self):
        for l, p in ((3, 2), (4, 3), (5, 3)):
            g, h = pendant_cycle(l, p), pendant_cycle(l, l)
            for size in range(p + 2):
                with self.subTest(l=l, p=p, size=size):
                    self.assertEqual(decorated_deck(g, size) == decorated_deck(h, size), size <= p)

    def test_shared_conventional_data(self):
        g, h = pendant_cycle(5, 3), pendant_cycle(5, 5)
        self.assertEqual(sorted(g.degrees), sorted(h.degrees))
        types = lambda G: sorted(tuple(sorted((G.degrees[u], G.degrees[v]))) for u, v in G.edges)
        self.assertEqual(types(g), types(h))
        # Not cospectral: the separation is not a spectral coincidence.
        self.assertNotEqual(laplacian_characteristic_polynomial(g), laplacian_characteristic_polynomial(h))

    def test_optimal_probe_parameter(self):
        for p in (1, 2, 5, 20):
            probe = optimal_probe(p)
            delta = first_discrepancy(p)
            self.assertTrue(vanishes_at(derivative(delta), probe["root"], probe["defining_polynomial"]))
            self.assertEqual(evaluate(delta, Fraction(1, 2)), probe["value_at_one_half"])
        # Stationary equation: delta' = 2 q (1-q)^2 (1-q^2)^(p-1) (1 - q - (p+2) q^2).
        p = 4
        expected = mul(from_factors(2, 1, [(1, 2), (2, p - 1)]), {0: 1, 1: -1, 2: -(p + 2)})
        self.assertEqual(derivative(first_discrepancy(p)), expected)

    def test_invalid_family_parameters(self):
        for l, j in ((1, 1), (3, 4), (3, 0)):
            with self.assertRaises((TypeError, ValueError)):
                pendant_cycle(l, j)


if __name__ == "__main__":
    unittest.main()
