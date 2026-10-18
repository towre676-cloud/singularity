from collections import Counter
from fractions import Fraction
from itertools import product
from math import prod
import unittest

from singularity.arithmetic import (
    boundary_prime_tail_bound, certified_tail_record, dirichlet_coefficients, normalized_ratio_tail_constant,
    prime_valuations, regularized_prime_tail_bound, regularized_tail_constant, valuation_energy,
)
from singularity.examples import GRAPHS
from singularity.heights import local_coefficients
from singularity.polynomials import evaluate
from singularity.graph import Graph


class ArithmeticTests(unittest.TestCase):
    def test_prime_assembly_matches_original_tuples(self):
        graph = Graph(3, ((0, 1), (1, 2)))
        bound = 20
        direct = {n: Counter() for n in range(1, bound + 1)}
        for values in product(range(1, bound + 1), repeat=3):
            n = prod(values)
            if n <= bound:
                direct[n][valuation_energy(graph, values)] += 1
        self.assertEqual(dirichlet_coefficients(graph, bound), {n: dict(sorted(v.items())) for n,v in direct.items()})

    def test_synchronization_is_integer_equality(self):
        graph = Graph(3, ((0, 1), (1, 2)))
        for values in product(range(1, 7), repeat=3):
            self.assertEqual(valuation_energy(graph, values) == 0, len(set(values)) == 1)
        self.assertEqual(prime_valuations(72), {2: 3, 3: 2})

    def test_tail_constants_exact_and_guarded(self):
        constant = normalized_ratio_tail_constant(7, 3, Fraction(11025, 262144), Fraction(1, 32))
        self.assertIsInstance(constant, Fraction)
        self.assertGreater(constant, 0)
        self.assertEqual(boundary_prime_tail_bound(3, 100, constant), constant * Fraction(3, 100))
        with self.assertRaises(ValueError):
            normalized_ratio_tail_constant(7, 3, 1, Fraction(1, 2))


class RegularizedTailTests(unittest.TestCase):
    """P26: the constant (7.12), cutoff guards and hypothesis-bound records."""

    def test_constant_matches_its_definition(self):
        from math import comb
        k, r, delta, rho = 7, 2, Fraction(3, 32), Fraction(1, 32)
        whole = (1 - rho) ** -k
        expected = (2 * (whole - sum(comb(n + 6, 6) * rho ** n for n in range(3))) / rho ** 3
                    + delta * (whole - 1) / rho + delta * rho / (2 * (1 - rho ** 2)))
        self.assertEqual(regularized_tail_constant(k, r, delta, rho), expected)
        # The sharper constant needs no U < 1 condition, unlike the conservative one.
        self.assertGreater(regularized_tail_constant(7, 2, delta, Fraction(1, 2)), 0)
        with self.assertRaises(ValueError):
            normalized_ratio_tail_constant(7, 2, delta, Fraction(1, 2))
        for bad in ((0, 2, delta, rho), (7, 0, delta, rho), (7, 2, delta, 1), (7, 2, delta, 0)):
            with self.assertRaises(ValueError):
                regularized_tail_constant(*bad)

    def test_local_inequality_with_rigorous_rational_enclosures(self):
        # Spectral pair at q=1/2: r=2, delta=3/32.  Check
        # exp(-C x^3) <= (1-x^2)^delta L_G/L_H <= exp(C x^3) at rational x <= rho,
        # using truncated series with the tail bound (7.14) and Bernoulli bounds.
        q, k, rho, depth, big_r = Fraction(1, 2), 7, Fraction(1, 32), 8, Fraction(1, 4)
        g = [evaluate(row, q) for row in local_coefficients(GRAPHS["spectral_g"], depth)]
        h = [evaluate(row, q) for row in local_coefficients(GRAPHS["spectral_h"], depth)]
        delta = g[2] - h[2]
        self.assertEqual(delta, Fraction(3, 32))
        constant = regularized_tail_constant(k, 2, delta, rho)
        for x in (rho, rho / 2, rho / 5):
            def enclose(series):
                low = sum(c * x ** n for n, c in enumerate(series))
                return low, low + (x / big_r) ** (depth + 1) * (1 - big_r) ** -k
            gl, gh = enclose(g)
            hl, hh = enclose(h)
            y = x ** 2
            factor_low, factor_high = 1 - delta * y / (1 - y), 1 - delta * y
            bound = constant * x ** 3
            self.assertLessEqual(factor_high * gh / hl, 1 + bound)          # <= exp(bound)
            self.assertGreaterEqual(factor_low * gl / hh * (1 + bound), 1)  # >= exp(-bound)

    def test_prime_tail_guards_and_boundary_case(self):
        constant = Fraction(5)
        self.assertEqual(regularized_prime_tail_bound(constant, 3, 1, 3, 100, Fraction(1, 32)), boundary_prime_tail_bound(3, 100, constant))
        # s = 1/2, r = 2: P = N^2, bound C N^(2-3) / (3/2 - 1).
        self.assertEqual(regularized_prime_tail_bound(constant, 2, 1, 2, 40, Fraction(1, 32)), constant * Fraction(1, 40) * 2)
        with self.assertRaises(ValueError):  # (r+1)s <= 1
            regularized_prime_tail_bound(constant, 2, 1, 3, 100, Fraction(1, 32))
        with self.assertRaises(ValueError):  # omitted primes outside the radius
            regularized_prime_tail_bound(constant, 3, 1, 3, 10, Fraction(1, 32))

    def test_record_recomputes_depth_and_rejects_bad_hypotheses(self):
        a, b = local_coefficients(GRAPHS["binary_g"], 4), local_coefficients(GRAPHS["binary_h"], 4)
        record = certified_tail_record(a, b, 7, Fraction(1, 2), Fraction(1, 32), 1, 3, 100)
        self.assertEqual((record["first_depth"], record["delta"]), (3, "11025/262144"))
        self.assertEqual(Fraction(record["tail_bound"]), Fraction(record["local_constant"]) * Fraction(3, 100))
        with self.assertRaises(ValueError):  # truncated before the discrepancy
            certified_tail_record(a[:3], b[:3], 7, Fraction(1, 2), Fraction(1, 32), 1, 3, 100)
        with self.assertRaises(ValueError):  # q = 1 erases the discrepancy
            certified_tail_record(a, b, 7, 1, Fraction(1, 32), 1, 3, 100)
        with self.assertRaises(ValueError):
            certified_tail_record(a, b, 7, Fraction(3, 2), Fraction(1, 32), 1, 3, 100)


class ComplexDiscTests(unittest.TestCase):
    """P28: exact conditions of SNG-F35 for the reference pairs."""

    def test_reference_discs_and_refusals(self):
        from singularity.arithmetic import complex_disc_certificate
        cases = [(7, 2, Fraction(3, 32), 5), (7, 3, Fraction(11025, 262144), 7), (8, 4, Fraction(81, 2048), 9)]
        for k, r, delta, digits in cases:
            record = complex_disc_certificate(k, r, delta, Fraction(1, 10 ** digits))
            self.assertEqual(record["center"], f"1/{r}")
            self.assertGreater(Fraction(record["min_real_part"]) * (r + 1), 1)
            self.assertIn("principal log", record["branches"]["local factors"])
            with self.assertRaisesRegex(ValueError, r"\(c\)"):
                complex_disc_certificate(k, r, delta, Fraction(1, 10 ** (digits - 1)))
        with self.assertRaisesRegex(ValueError, r"\(a\)"):
            complex_disc_certificate(7, 2, Fraction(3, 32), Fraction(1, 6))
        with self.assertRaises(ValueError):
            complex_disc_certificate(7, 2, Fraction(3, 32), 0)

    def test_schwarz_constant_is_the_conservative_one(self):
        from singularity.arithmetic import complex_disc_certificate
        record = complex_disc_certificate(7, 2, Fraction(3, 32), Fraction(1, 10 ** 5))
        rho = Fraction(record["local_radius_rho"])
        self.assertLess((1 - rho) ** -7 - 1, 1)
        self.assertEqual(Fraction(record["schwarz_constant"]), normalized_ratio_tail_constant(7, 2, Fraction(3, 32), rho))
        cutoff = record["primes_beyond_cutoff"]
        self.assertGreaterEqual(Fraction(cutoff), (1 / rho) ** 3)  # P^-sigma <= P^(-1/3) <= rho


if __name__ == '__main__':
    unittest.main()
