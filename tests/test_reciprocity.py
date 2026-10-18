"""P22: established reciprocities checked exactly, and the energy-weighted obstruction."""

from fractions import Fraction
from itertools import permutations
import unittest

from singularity.graph import Graph
from singularity.orders import (
    Poset, count_direct, evaluate_order_polynomial, order_polynomial, p_partition_rational, p_partition_series,
)
from singularity.polynomials import mul, normalize, series_inverse, series_mul

POSETS = {
    "singleton": Poset(1),
    "chain3": Poset(3, [(0, 1), (1, 2)]),
    "antichain3": Poset(3),
    "diamond": Poset(4, [(0, 1), (0, 2), (1, 3), (2, 3)]),
    "unnatural": Poset(4, [(3, 0), (1, 0), (2, 3)]),
    "disconnected": Poset(5, [(4, 1), (0, 2)]),
}


def expand(numerator, n, bound):
    """numerator / prod_{i<=n} (1 - x^i) as a power series through x^bound."""
    denominator = [{0: 1}] + [{} for _ in range(bound)]
    for i in range(1, n + 1):
        factor = [{0: 1}] + [{} for _ in range(bound)]
        if i <= bound:
            factor[i] = {0: -1}
        denominator = series_mul(denominator, factor, bound)
    top = [{0: numerator[k]} if k in numerator else {} for k in range(bound + 1)]
    return series_mul(top, series_inverse(denominator, bound), bound)


def determinant(matrix):
    n, total = len(matrix), {}
    for perm in permutations(range(n)):
        sign = (-1) ** sum(perm[i] > perm[j] for i in range(n) for j in range(i + 1, n))
        term = {0: sign}
        for i, j in enumerate(perm):
            term = mul(term, matrix[i][j])
        for e, c in term.items():
            total[e] = total.get(e, 0) + c
    return normalize(total)


class EstablishedReciprocityTests(unittest.TestCase):
    """Background (Stanley): verified on complete small posets, not new results."""

    def test_order_polynomial_reciprocity(self):
        for name, poset in POSETS.items():
            omega = order_polynomial(poset)
            for height in range(5):
                with self.subTest(poset=name, height=height):
                    self.assertEqual(evaluate_order_polynomial(omega, height + 1), count_direct(poset, height))
                    # Strict maps to {0..H}: (-1)^n Omega(P, -(H+1)).
                    self.assertEqual((-1) ** poset.n * evaluate_order_polynomial(omega, -(height + 1)),
                                     count_direct(poset, height, strict=True))

    def test_p_partition_reciprocity_as_rational_functions(self):
        for name, poset in POSETS.items():
            weak, n = p_partition_rational(poset)
            strict, _ = p_partition_rational(poset, strict=True)
            # Each rational form matches direct enumeration through x^8.
            for numerator, flag in ((weak, False), (strict, True)):
                expected = [{e: Fraction(c) for e, c in row.items()} for row in p_partition_series(poset, 8, flag)]
                self.assertEqual(expand(numerator, n, 8), expected, name)
            # (-1)^n W(1/x) = S(x): x^(n(n+1)/2) W-numerator(1/x) = S-numerator(x).
            top = n * (n + 1) // 2
            self.assertEqual({top - e: c for e, c in weak.items()}, strict, name)


class EnergyObstructionTests(unittest.TestCase):
    """SNG-F34: the energy-weighted series of the 2-chain with its edge is not rational."""

    def test_closed_forms_through_degree_twelve(self):
        poset, graph = Poset(2, [(0, 1)]), Graph(2, [(0, 1)])
        weak = p_partition_series(poset, 12, energy_graph=graph)
        strict = p_partition_series(poset, 12, strict=True, energy_graph=graph)
        for v in range(13):
            # W = theta/(1-x^2), S = x^2 (theta - 1)/(1-x^2), theta = sum_d x^d q^(d^2).
            w = {d * d: 1 for d in range(v + 1) if (v - d) % 2 == 0}  # a = (t, t + d)
            s = {d * d: 1 for d in range(1, v - 1) if (v - d) % 2 == 0}  # t >= 1, d >= 1
            self.assertEqual(weak[v], w)
            self.assertEqual(strict[v], s)
        # At q = 1 the classical identity holds: S(x) = x^3 / ((1-x)(1-x^2)) = (-1)^2 W(1/x).
        self.assertEqual(p_partition_rational(poset), ({0: 1}, 2))
        self.assertEqual(p_partition_rational(poset, strict=True), ({3: 1}, 2))

    def test_hankel_certificates_exclude_short_recurrences(self):
        # A linear recurrence of order k over Q(q) for c_d = q^(d^2) from d = 0
        # would make det[c_(i+j)]_{0..k} vanish; it is a nonzero polynomial.
        for k in range(1, 4):
            hankel = [[{(i + j) ** 2: 1} for j in range(k + 1)] for i in range(k + 1)]
            det = determinant(hankel)
            self.assertNotEqual(det, {}, k)
        self.assertEqual(determinant([[{0: 1}, {1: 1}], [{1: 1}, {4: 1}]]), {2: -1, 4: 1})


if __name__ == "__main__":
    unittest.main()
