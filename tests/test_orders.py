"""P21: poset-constrained heights, order polynomials and quadratic weighting."""

from fractions import Fraction
from math import comb
import unittest

from singularity.graph import Graph
from singularity.orders import (
    Poset, count_by_chambers, count_by_linear_extensions, count_direct, weighted_histogram,
)


POSETS = {
    "chain4": Poset(4, [(0, 1), (1, 2), (2, 3)]),
    "reversed chain": Poset(3, [(2, 1), (1, 0)]),
    "antichain": Poset(3),
    "diamond": Poset(4, [(0, 1), (0, 2), (1, 3), (2, 3)]),
    "unnatural labels": Poset(4, [(3, 0), (1, 0), (2, 3)]),
    "disconnected": Poset(5, [(4, 1), (0, 2)]),
    "redundant relation": Poset(3, [(0, 1), (1, 2), (0, 2)]),
}


class OrderPolytopeTests(unittest.TestCase):
    def test_three_counts_agree(self):
        for name, poset in POSETS.items():
            for height in range(6 if poset.n <= 4 else 4):
                with self.subTest(poset=name, height=height):
                    direct = count_direct(poset, height)
                    self.assertEqual(count_by_chambers(poset, height), direct)
                    self.assertEqual(count_by_linear_extensions(poset, height), direct)

    def test_closed_forms_and_argument_shift(self):
        for height in range(7):
            # Weak chain maps to {0..H}: multisets, C(H+n, n) = Omega(chain, H+1).
            self.assertEqual(count_direct(POSETS["chain4"], height), comb(height + 4, 4))
            # Strict chain maps choose n distinct values from H+1.
            self.assertEqual(count_direct(POSETS["chain4"], height, strict=True), comb(height + 1, 4))
            self.assertEqual(count_direct(POSETS["antichain"], height), (height + 1) ** 3)
            self.assertEqual(count_direct(POSETS["antichain"], height, strict=True), (height + 1) ** 3)
        # Strict and weak differ as soon as a relation exists.
        self.assertNotEqual(count_direct(POSETS["diamond"], 2), count_direct(POSETS["diamond"], 2, strict=True))
        self.assertEqual(count_direct(POSETS["diamond"], 2, strict=True), 1)  # 0 < {1,1} < 2

    def test_linear_extensions_and_natural_labeling(self):
        diamond = POSETS["diamond"]
        self.assertEqual(sorted(diamond.linear_extensions()), [(0, 1, 2, 3), (0, 2, 1, 3)])
        poset = POSETS["unnatural labels"]
        new = poset.natural_labeling()
        for i, j in poset.less:
            self.assertLess(new[i], new[j])
        self.assertEqual(POSETS["redundant relation"].less, Poset(3, [(0, 1), (1, 2)]).less)

    def test_invalid_relations(self):
        for n, relations in ((3, [(0, 1), (1, 2), (2, 0)]), (2, [(0, 1), (1, 0)]), (2, [(0, 0)]), (2, [(0, 2)]), (2, [(0, 1, 1)])):
            with self.subTest(relations=relations), self.assertRaises(ValueError):
                Poset(n, relations)
        with self.assertRaises(TypeError):
            Poset(2, [(True, 1)])
        with self.assertRaises(ValueError):
            weighted_histogram(Poset(2), Graph(3), 1)

    def test_quadratic_weight_is_not_an_ehrhart_polynomial(self):
        # Chain 0 <= 1 with the edge {0,1}: W_H(q) = sum_d (H+1-d) q^(d^2).
        poset, graph = Poset(2, [(0, 1)]), Graph(2, [(0, 1)])
        q = Fraction(1, 2)

        def weighted(height):
            return sum(c * q ** e for (_, e), c in weighted_histogram(poset, graph, height).items())

        values = [weighted(h) for h in range(8)]
        for h in range(8):
            self.assertEqual(values[h], sum((h + 1 - d) * q ** (d * d) for d in range(h + 1)))
        # Second differences equal q^((H+2)^2): positive and tending to zero,
        # impossible for a polynomial in H unless they vanish identically.
        second = [values[h + 2] - 2 * values[h + 1] + values[h] for h in range(6)]
        self.assertEqual(second, [q ** ((h + 2) ** 2) for h in range(6)])
        # The unweighted count on the same points is the polynomial C(H+2, 2).
        self.assertEqual([sum(weighted_histogram(poset, graph, h).values()) for h in range(8)], [comb(h + 2, 2) for h in range(8)])


if __name__ == "__main__":
    unittest.main()
