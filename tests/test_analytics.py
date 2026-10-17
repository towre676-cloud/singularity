"""Exact algebra, independent recomposition and adversarial certificate checks."""

import copy
from fractions import Fraction
from math import comb
import unittest

from singularity.certificates import build_certificate, replay_certificate
from singularity.euler import (
    euler_exponents, euler_exponents_mobius, finite_signature,
    first_difference, first_difference_at_q, recompose_euler,
)
from singularity.examples import GRAPHS
from singularity.graph import Graph
from singularity.heights import local_coefficients, marked_coefficients
from singularity.polynomials import (
    add, constant, derivative, evaluate, from_factors, mul, normalize,
    polynomial_from_json, polynomial_to_json, power, series_exp,
    series_inverse, series_log, series_mul, sub, verify_factorization,
)


class PolynomialTests(unittest.TestCase):
    def test_sparse_exact_arithmetic(self):
        self.assertEqual(normalize({0: 0, 2: 3}), {2: Fraction(3)})
        self.assertEqual(mul({0: 1, 1: 1}, {0: 1, 1: -1}), {0: 1, 2: -1})
        self.assertEqual(add({1: Fraction(1, 2)}, {1: Fraction(1, 3)}), {1: Fraction(5, 6)})
        self.assertEqual(sub({1: 1}, {1: 1}), {})
        self.assertEqual(power({0: 1, 1: 1}, 3), {0: 1, 1: 3, 2: 3, 3: 1})
        self.assertEqual(derivative({0: 8, 3: Fraction(2, 3)}), {2: 2})
        self.assertEqual(evaluate({0: 1, 2: -1}, Fraction(1, 2)), Fraction(3, 4))
        with self.assertRaises(TypeError):
            evaluate({0: 1}, 0.5)
        with self.assertRaises(ValueError):
            normalize({-1: 1})
        with self.assertRaises(ValueError):
            power({0: 1}, -1)

    def test_factorization_is_verified_not_assumed(self):
        polynomial = {3: 1, 4: -1, 6: -2, 8: 2, 9: 1, 10: 3, 11: -3, 12: -1, 13: -2, 15: 2, 17: 1, 18: -1}
        self.assertEqual(from_factors(1, 3, [(1, 1), (3, 2), (4, 2)]), polynomial)
        self.assertTrue(verify_factorization(polynomial, 1, 3, [(1, 1), (3, 2), (4, 2)]))
        self.assertFalse(verify_factorization(polynomial, 1, 3, [(1, 2), (3, 2), (4, 2)]))
        self.assertEqual(evaluate(polynomial, Fraction(1, 2)), Fraction(11025, 262144))

    def test_json_roundtrip_and_rejections(self):
        polynomial = {0: Fraction(5, 6), 7: Fraction(-3, 5)}
        self.assertEqual(polynomial_from_json(polynomial_to_json(polynomial)), polynomial)
        for entries in ([[0, 1, 0]], [[1, 0, 1]], [[1, 1, 2], [1, 3, 4]], [[True, 1, 1]]):
            with self.assertRaises(ValueError):
                polynomial_from_json(entries)


class FormalSeriesTests(unittest.TestCase):
    def test_known_geometric_log_and_binomial_exponents(self):
        geometric = [{0: 1} for _ in range(9)]
        logarithm = series_log(geometric)
        self.assertEqual(logarithm, [{}] + [{0: Fraction(1, n)} for n in range(1, 9)])
        self.assertEqual(euler_exponents(geometric), [{}, {0: 1}] + [{}] * 7)
        # (1-x)^(-3) has independent stars-and-bars coefficients.
        population = [{0: comb(n + 2, 2)} for n in range(9)]
        self.assertEqual(euler_exponents(population), [{}, {0: 3}] + [{}] * 7)

    def test_nonconstant_polynomial_exponents_recompose(self):
        exponents = [{}, {0: Fraction(1, 2), 1: 2}, {3: -1}, {}, {0: Fraction(2, 3)}, {}, {}]
        series = recompose_euler(exponents)
        self.assertEqual(euler_exponents(series), exponents)
        self.assertEqual(euler_exponents_mobius(series), exponents)
        self.assertEqual(series_exp(series_log(series)), series)
        identity = [{0: 1}] + [{}] * 6
        self.assertEqual(series_mul(series, series_inverse(series)), identity)

    def test_independent_finite_product_input(self):
        # L=(1+q*x)/(1-x^2). Coefficients alternate 1 and q.
        series = [{0: 1} if n % 2 == 0 else {1: 1} for n in range(13)]
        exponents = euler_exponents(series)
        self.assertEqual(exponents, euler_exponents_mobius(series))
        self.assertEqual(recompose_euler(exponents), series)
        # At q=1 the input is (1-x)^-1, so all higher exponents vanish.
        self.assertEqual([evaluate(poly, 1) for poly in exponents], [0, 1] + [0] * 11)

    def test_symbolic_difference_can_vanish_after_specialization(self):
        left = [{0: 1}, {0: 1, 1: -1}, {0: 2}]
        right = [{0: 1}, {}, {0: 1}]
        self.assertEqual(first_difference(left, right), (1, {0: 1, 1: -1}))
        self.assertEqual(first_difference_at_q(left, right, 1), (2, Fraction(1)))
        self.assertIsNone(first_difference(left[:1], right))
        self.assertEqual(finite_signature(left, right, 1)["volume"], 2)
        self.assertFalse(finite_signature(left, right, 1)["analytic_hypotheses_checked"])

    def test_graph_factorization_and_endpoints(self):
        a = local_coefficients(GRAPHS["binary_g"], 4)
        b = local_coefficients(GRAPHS["binary_h"], 4)
        r, delta = first_difference(a, b)
        self.assertEqual(r, 3)
        self.assertTrue(verify_factorization(delta, 1, 3, [(1, 1), (3, 2), (4, 2)]))
        self.assertEqual(first_difference_at_q(a, b, Fraction(1, 2)), (3, Fraction(11025, 262144)))
        self.assertIsNone(first_difference_at_q(a, b, 0))
        self.assertIsNone(first_difference_at_q(a, b, 1))
        exponents = euler_exponents(a)
        self.assertEqual(recompose_euler(exponents), [normalize(poly) for poly in a])
        self.assertEqual([evaluate(poly, 1) for poly in exponents], [0, 7, 0, 0, 0])
        # At q=0, a connected seven-vertex graph has L=(1-x^7)^-1.
        connected = euler_exponents(local_coefficients(Graph(2, [(0, 1)]), 8))
        self.assertEqual([evaluate(poly, 0) for poly in connected], [0, 0, 1, 0, 0, 0, 0, 0, 0])

    def test_regular_triangle_free_pair_delays_visibility_to_four(self):
        cube = Graph(8, [(i, i ^ (1 << b)) for i in range(8) for b in range(3) if i < (i ^ (1 << b))])
        mobius = Graph(8, [(i, (i + 1) % 8) for i in range(8)] + [(i, i + 4) for i in range(4)])
        self.assertEqual(cube.degrees, (3,) * 8)
        self.assertEqual(mobius.degrees, (3,) * 8)
        a, b = local_coefficients(cube, 5), local_coefficients(mobius, 5)
        r, delta = first_difference(a, b)
        self.assertEqual(r, 4)
        self.assertTrue(verify_factorization(delta, 2, 4, [(2, 4)]))
        self.assertEqual(first_difference_at_q(a, b, Fraction(1, 2)), (4, Fraction(81, 2048)))
        marked_a, marked_b = marked_coefficients(cube, 5), marked_coefficients(mobius, 5)
        differing = {key for key in marked_a.keys() | marked_b.keys() if marked_a.get(key, 0) != marked_b.get(key, 0)}
        self.assertEqual({span for volume, _, span in differing if volume == 4}, {1})
        self.assertEqual({span for volume, _, span in differing if volume == 5}, {2})
        fifth = sub(a[5], b[5])
        self.assertTrue(verify_factorization(fifth, 8, 9, [(2, 2), (4, 2)]))

    def test_invalid_series_units(self):
        with self.assertRaises(ValueError):
            series_log([{0: 2}, {0: 1}])
        with self.assertRaises(ValueError):
            series_exp([{0: 1}])
        with self.assertRaises(ValueError):
            series_inverse([{1: 1}])


class CertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.certificate = build_certificate(
            GRAPHS["binary_g"], 3, comparison=GRAPHS["binary_h"], label="exact binary-census example",
            factorization={"coefficient": "1", "monomial": 3, "factors": [[1, 1], [3, 2], [4, 2]]},
        )

    def test_independent_replay(self):
        result = replay_certificate(self.certificate)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["checks"]["profiles_recomputed"], 2 * comb(10, 7))
        self.assertTrue(result["checks"]["euler_recomposition"])

    def test_normalization_actually_crosses_translation_degree(self):
        certificate = build_certificate(Graph(2, [(0, 1)]), 5)
        self.assertTrue(replay_certificate(certificate)["valid"])
        self.assertNotEqual(certificate["local_coefficients"][2], certificate["normalized_coefficients"][2])

    def test_tamper_each_mathematical_sector(self):
        for sector in ("local_coefficients", "normalized_coefficients", "marked_coefficients"):
            altered = copy.deepcopy(self.certificate)
            if sector == "marked_coefficients":
                altered[sector][0][-1] += 1
            else:
                altered[sector][1][0][1] += 1
            with self.subTest(sector=sector):
                self.assertFalse(replay_certificate(altered)["valid"])
        altered = copy.deepcopy(self.certificate)
        altered["comparison"]["first_difference"]["volume"] = 2
        self.assertFalse(replay_certificate(altered)["valid"])
        altered = copy.deepcopy(self.certificate)
        altered["comparison"]["factorization"]["factors"][0][1] = 2
        self.assertFalse(replay_certificate(altered)["valid"])
        altered = copy.deepcopy(self.certificate)
        altered["euler_exponents"][1][0][1] += 1
        self.assertFalse(replay_certificate(altered)["valid"])

    def test_source_checks_and_budget(self):
        altered = copy.deepcopy(self.certificate)
        altered["graph_sha256"] = "0" * 64
        self.assertFalse(replay_certificate(altered)["valid"])
        altered = copy.deepcopy(self.certificate)
        altered["graph"]["edges"].reverse()
        self.assertFalse(replay_certificate(altered)["valid"])
        result = replay_certificate(self.certificate, max_profiles=1)
        self.assertFalse(result["valid"])
        self.assertIn("budget", result["errors"][0])

    def test_boolean_count_cannot_impersonate_integer_one(self):
        altered = copy.deepcopy(self.certificate)
        altered["local_coefficients"][0][0][1] = True
        self.assertFalse(replay_certificate(altered)["valid"])

    def test_invalid_factor_claim_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            build_certificate(GRAPHS["binary_g"], 3, GRAPHS["binary_h"], factorization={"coefficient": "1", "monomial": 3, "factors": [[1, 2]]})


if __name__ == "__main__":
    unittest.main()
