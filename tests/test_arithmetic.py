from collections import Counter
from fractions import Fraction
from itertools import product
from math import prod
import unittest

from singularity.arithmetic import prime_valuations, valuation_energy, dirichlet_coefficients, normalized_ratio_tail_constant, boundary_prime_tail_bound
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


if __name__ == '__main__':
    unittest.main()
