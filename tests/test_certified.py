"""SNG-F38/F39: certified local factors, logarithms and small finite products."""

from fractions import Fraction as F
from itertools import product
import math
import unittest

from singularity.certified import (
    coefficient_aware_tail_constant, diameter, exp_enclosure, from_fixed, greedy_decomposition,
    height_tail_bound, log_enclosure, min_zero_box_sum, normalized_factor_enclosure,
    prime_power_enclosure, primes_up_to, to_fixed, certified_k,
)
from singularity.arithmetic import regularized_tail_constant
from singularity.examples import GRAPHS
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.polynomials import evaluate


class EnclosureTests(unittest.TestCase):
    def test_prime_powers_are_bracketed_exactly(self):
        for p, a, b in ((2, 1, 2), (3, 1, 3), (7, 3, 5), (9973, 1, 2)):
            lo, hi = prime_power_enclosure(p, a, b)
            self.assertLessEqual(from_fixed(lo) ** b, F(1, p ** a))
            self.assertGreaterEqual(from_fixed(hi) ** b, F(1, p ** a))
            self.assertLessEqual(hi - lo, 2)

    def test_logarithm_and_exponential_enclosures(self):
        for x in (F(1, 7), F(1), F(3, 2), F(2), F(1000, 3)):
            lo, hi = log_enclosure(x, x)
            self.assertLess(hi - lo, F(1, 2 ** 200))
            self.assertLessEqual(float(lo), math.log(x) + 1e-12)
            self.assertGreaterEqual(float(hi), math.log(x) - 1e-12)
        lo, hi = exp_enclosure(F(-1, 3), F(1, 2))
        self.assertTrue(float(lo) <= math.exp(-1 / 3) <= float(lo) + 1e-12)
        self.assertTrue(float(hi) - 1e-12 <= math.exp(0.5) <= float(hi))
        with self.assertRaises(ValueError):
            log_enclosure(F(0), F(1))

    def test_flagged_box_sum_equals_exact_enumeration(self):
        q, t = F(1, 2), F(2, 5)
        for graph in (GRAPHS["spectral_g"], Graph(4, [(0, 1), (1, 2), (2, 3), (0, 3)]), Graph(3, [(0, 1), (1, 2)])):
            dec = greedy_decomposition(graph)
            for height in (1, 2, 3):
                exact = sum(t ** sum(a) * q ** graph.energy(a) for a in product(range(height + 1), repeat=graph.n) if min(a) == 0)
                lo = from_fixed(min_zero_box_sum(graph, dec, height, to_fixed(t, False), q, False))
                hi = from_fixed(min_zero_box_sum(graph, dec, height, to_fixed(t, True), q, True))
                self.assertTrue(lo <= exact <= hi)
                self.assertLess(hi - lo, F(1, 2 ** 200))

    def test_height_tail_bounds_the_omitted_profiles(self):
        graph, q, t = Graph(4, [(0, 1), (1, 2), (2, 3)]), F(1, 2), F(3, 4)
        diam = diameter(graph)
        self.assertEqual(diam, 3)
        big = sum(t ** sum(a) * q ** graph.energy(a) for a in product(range(9), repeat=4) if min(a) == 0)
        for height in (1, 2, 3, 4):
            truncated = sum(t ** sum(a) * q ** graph.energy(a) for a in product(range(height + 1), repeat=4) if min(a) == 0)
            self.assertLessEqual(big - truncated, height_tail_bound(4, diam, height, t, q))
        with self.assertRaises(ValueError):
            diameter(Graph(3, [(0, 1)]))

    def test_local_factor_enclosure_contains_series_value(self):
        graph, q = Graph(3, [(0, 1), (1, 2)]), F(1, 2)
        lo, hi = prime_power_enclosure(5, 1, 2)
        enclosure = normalized_factor_enclosure(graph, lo, hi, q)
        series = sum(evaluate(row, q) * from_fixed(lo) ** m for m, row in enumerate(
            [r for r in __import__("singularity.heights", fromlist=["x"]).normalized_coefficients(graph, 12)]))
        self.assertLessEqual(enclosure["low"], enclosure["high"])
        self.assertLessEqual(series, enclosure["high"])  # partial sums at t_lo stay below B(t)

    def test_coefficient_aware_constant_improves_7_12(self):
        q, k, r, rho = F(1, 2), 7, 2, F(1, 100)
        left = [evaluate(row, q) for row in local_coefficients(GRAPHS["spectral_g"], 6)]
        right = [evaluate(row, q) for row in local_coefficients(GRAPHS["spectral_h"], 6)]
        sharp = coefficient_aware_tail_constant(left, right, k, r, rho)
        self.assertLess(sharp, regularized_tail_constant(k, r, left[r] - right[r], rho))
        with self.assertRaises(ValueError):
            coefficient_aware_tail_constant(left, left, k, r, rho)

    def test_reversal_negates_the_enclosure(self):
        g, h = GRAPHS["spectral_g"], GRAPHS["spectral_h"]
        forward = certified_k(g, h, F(1, 2), 1, 2, 3)
        backward = certified_k(h, g, F(1, 2), 1, 2, 3)
        lo, hi = forward["finite_product_log_interval"]
        blo, bhi = backward["finite_product_log_interval"]
        self.assertLessEqual(lo, -blo + 1e-15)
        self.assertGreaterEqual(hi, -bhi - 1e-15)
        self.assertEqual(primes_up_to(9), [2, 3, 5, 7])
        self.assertLess(hi - lo, 1e-15)

    def test_other_cutoff_and_precision_overlap_retained_enclosure(self):
        import json
        from pathlib import Path
        from singularity import certified
        retained = json.loads((Path(__file__).resolve().parents[1] / "results/certified_k.json").read_text())
        reference = next(r for r in retained["runs"] if r["pair"] == "spectral" and r["s"] == "1/2")
        lo_ref, hi_ref = (F(x) for x in reference["k_interval_exact_dyadic"])
        saved = (certified.BITS, certified.ONE, certified._LOG2)
        try:
            certified.BITS, certified.ONE, certified._LOG2 = 160, 1 << 160, None
            small = certified_k(GRAPHS["spectral_g"], GRAPHS["spectral_h"], F(1, 2), 1, 2, 12)
        finally:
            certified.BITS, certified.ONE, certified._LOG2 = saved
        lo, hi = (F(x) for x in small["k_interval_exact_dyadic"])
        self.assertLess(lo, hi_ref)  # two rigorous enclosures of K(1/2, 1/2) must overlap
        self.assertLess(lo_ref, hi)
        self.assertGreater(hi - lo, hi_ref - lo_ref)  # a smaller cutoff is wider
        self.assertGreater(lo_ref, 0)


if __name__ == "__main__":
    unittest.main()
