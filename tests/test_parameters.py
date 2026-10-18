"""P24: exact exceptional parameters by Sturm isolation and algebraic specialization."""

from fractions import Fraction as F
import unittest

from singularity.examples import GRAPHS
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.parameters import (
    count_roots, gcd, isolate_roots, multiplicity, parameter_strata, rational_roots,
    squarefree, vanishes_at,
)
from singularity.polynomials import evaluate, from_factors, mul


def cube():
    return Graph(8, ((i, i ^ (1 << b)) for i in range(8) for b in range(3) if i < i ^ (1 << b)))


def mobius_ladder():
    return Graph(8, tuple((i, (i + 1) % 8) for i in range(8)) + tuple((i, i + 4) for i in range(4)))


class RootIsolationTests(unittest.TestCase):
    def test_sturm_counts_against_known_factorizations(self):
        f = from_factors(1, 0, [])  # 1
        self.assertEqual(count_roots(f, 0, 1), 0)
        # (q - 1/4)(q - 1/2)(q - 3)(q^2 + 1)
        g = mul(mul(mul({0: F(-1, 4), 1: 1}, {0: F(-1, 2), 1: 1}), {0: -3, 1: 1}), {0: 1, 2: 1})
        self.assertEqual(count_roots(g, 0, 1), 2)
        self.assertEqual(count_roots(g, -10, 10), 3)
        self.assertEqual(isolate_roots(g), [{"rational": F(1, 4)}, {"rational": F(1, 2)}])
        with self.assertRaises(ValueError):
            count_roots({}, 0, 1)

    def test_repeated_roots_and_multiplicity(self):
        f = mul(mul({0: F(-1, 3), 1: 1}, {0: F(-1, 3), 1: 1}), {0: F(1, 5), 1: -1, 2: 1})
        self.assertEqual(squarefree(f), mul({0: F(-1, 3), 1: 1}, {0: F(1, 5), 1: -1, 2: 1}))
        roots = isolate_roots(f)
        self.assertEqual(len(roots), 3)
        self.assertIn({"rational": F(1, 3)}, roots)
        self.assertEqual([multiplicity(f, r, f) for r in roots], [1, 2, 1])

    def test_irrational_root_is_isolated_exactly(self):
        f = {0: F(1, 5), 1: -1, 2: 1}  # roots (5 +- sqrt 5)/10
        roots = isolate_roots(f)
        self.assertEqual(len(roots), 2)
        for root in roots:
            a, b = root["interval"]
            self.assertLess(evaluate(f, a) * evaluate(f, b), 0)
            self.assertTrue(vanishes_at(mul(f, {0: 7, 3: 1}), root, f))
            self.assertFalse(vanishes_at({0: F(-1, 2), 1: 1}, root, f))
        self.assertIsNone(rational_roots({0: 10 ** 7 + 19, 1: 1}, limit=10 ** 6))
        self.assertEqual(rational_roots({1: 1}), [F(0)])
        self.assertEqual(gcd({0: -1, 2: 1}, {0: 1, 1: 1}), {0: 1, 1: 1})


class StrataTests(unittest.TestCase):
    def test_released_pairs_have_no_interior_exceptional_parameter(self):
        pairs = [
            (local_coefficients(GRAPHS["spectral_g"], 3), local_coefficients(GRAPHS["spectral_h"], 3), 2),
            (local_coefficients(GRAPHS["binary_g"], 4), local_coefficients(GRAPHS["binary_h"], 4), 3),
            (local_coefficients(cube(), 5), local_coefficients(mobius_ladder(), 5), 4),
        ]
        for left, right, depth in pairs:
            strata = parameter_strata(left, right)
            self.assertEqual(strata["generic_first_volume"], depth)
            self.assertEqual(strata["exceptional"], [])
        # Endpoints are reported separately: q=0 and q=1 erase the discrepancy.
        self.assertEqual(parameter_strata(*pairs[1][:2])["endpoints"], {"0": None, "1": None})

    def test_artificial_interior_algebraic_and_rational_strata(self):
        f = {0: F(1, 5), 1: -1, 2: 1}
        left = [{0: 1}, f, mul(f, {1: 1}), {1: 1}, {}]
        right = [{0: 1}, {}, {}, {0: F(1, 2)}, {}]
        strata = parameter_strata(left, right)
        self.assertEqual(strata["generic_first_volume"], 1)
        self.assertEqual([e["first_visible_volume"] for e in strata["exceptional"]], [3, 3])
        self.assertTrue(all("isolating_interval" in e["root"] for e in strata["exceptional"]))
        # A rational exceptional value where every later discrepancy also vanishes.
        g = {0: F(-1, 2), 1: 1}
        strata = parameter_strata([{0: 1}, g, mul(g, g)], [{0: 1}, {}, {}])
        self.assertEqual(strata["exceptional"][0]["root"], {"rational": "1/2"})
        self.assertIsNone(strata["exceptional"][0]["first_visible_volume"])
        self.assertIn("agreement through volume 2", strata["exceptional"][0]["status"])

    def test_zero_discrepancies_and_endpoint_shift(self):
        series = local_coefficients(Graph(3, [(0, 1)]), 3)
        strata = parameter_strata(series, series)
        self.assertIsNone(strata["generic_first_volume"])
        self.assertIn("nothing is claimed beyond it", strata["status"])
        left, right = [{0: 1}, {0: 1, 1: -1}, {0: 2}], [{0: 1}, {}, {0: 1}]
        strata = parameter_strata(left, right)
        self.assertEqual(strata["generic_first_volume"], 1)
        self.assertEqual(strata["endpoints"], {"0": 1, "1": 2})
        self.assertEqual(strata["exceptional"], [])  # the root q=1 is an endpoint, not interior


if __name__ == "__main__":
    unittest.main()
