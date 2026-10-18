import unittest
from itertools import product
from math import comb

from singularity.conductor import CyclotomicRing, cyclotomic_polynomial, remote_coefficient, residue_numerator
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.weighted import WeightedGraph, weighted_coefficients


class ConductorTests(unittest.TestCase):
    def test_known_cyclotomic_and_root_relations(self):
        self.assertEqual(cyclotomic_polynomial(1), (-1, 1))
        self.assertEqual(cyclotomic_polynomial(6), (1, -1, 1))
        for order in range(1, 13):
            ring = CyclotomicRing(order)
            self.assertEqual(ring.phase(order), ring.one)
            self.assertEqual(ring.reduce(ring.modulus), ring.zero)
            self.assertEqual(ring.multiply(ring.phase(1), ring.phase(order-1)), ring.one)

    def test_numerator_replays_direct_coefficients(self):
        for graph in (Graph(2, ((0, 1),)), Graph(3, ((0, 1), (1, 2)))):
            coefficients = local_coefficients(graph, 12)
            for order in (1, 2, 3, 4):
                ring = CyclotomicRing(order)
                for index, polynomial in enumerate(coefficients):
                    direct = ring.zero
                    for energy, multiplicity in polynomial.items():
                        direct = ring.add(direct, ring.scale(ring.phase(energy), multiplicity))
                    self.assertEqual(remote_coefficient(graph, order, index), direct)

    def test_remote_and_budget(self):
        graph = Graph(2, ((0, 1),))
        self.assertEqual(remote_coefficient(graph, 1, 10**100), (10**100+1,))
        with self.assertRaises(ValueError):
            residue_numerator(graph, 100, max_profiles=10)


def _poly_mul(a, b):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


def _poly_exact_div(a, b):
    a = list(a)
    quotient = [0] * (len(a) - len(b) + 1)
    for shift in range(len(a) - len(b), -1, -1):
        factor, remainder = divmod(a[shift + len(b) - 1], b[-1])
        assert remainder == 0
        quotient[shift] = factor
        for j, value in enumerate(b):
            a[shift + j] -= factor * value
    assert not any(a)
    return quotient


def mobius_cyclotomic(order):
    """Phi_m = prod_{d|m} (t^d-1)^mu(m/d): independent of recursive division."""
    def mu(k):
        sign, p = 1, 2
        while p * p <= k:
            if k % p == 0:
                k //= p
                if k % p == 0:
                    return 0
                sign = -sign
            p += 1
        return -sign if k > 1 else sign
    numerator, denominator = [1], [1]
    for d in range(1, order + 1):
        if order % d == 0 and mu(order // d):
            factor = [-1] + [0] * (d - 1) + [1]
            if mu(order // d) > 0:
                numerator = _poly_mul(numerator, factor)
            else:
                denominator = _poly_mul(denominator, factor)
    return tuple(_poly_exact_div(numerator, denominator))


class RootOfUnityTests(unittest.TestCase):
    """P18: SNG-F28 on composite orders, isolated vertices and remote indices."""

    def test_cyclotomic_polynomials_by_mobius_product(self):
        from math import gcd
        for order in range(1, 25):
            self.assertEqual(cyclotomic_polynomial(order), mobius_cyclotomic(order), order)
            self.assertEqual(CyclotomicRing(order).degree, sum(gcd(k, order) == 1 for k in range(1, order + 1)))

    def test_numerator_expansion_equals_direct_specialization(self):
        graphs = [
            Graph(3, ((0, 1),)),                       # isolated vertex
            Graph(4, ((0, 1), (0, 2), (0, 3))),        # star
            Graph(3, ((0, 1), (1, 2), (0, 2))),        # triangle
            Graph(2),                                  # edgeless
        ]
        for graph in graphs:
            coefficients = local_coefficients(graph, 10)
            for order in (1, 2, 4, 6, 8, 9):
                ring = CyclotomicRing(order)
                for index, polynomial in enumerate(coefficients):
                    direct = ring.zero
                    for energy, multiplicity in polynomial.items():
                        direct = ring.add(direct, ring.scale(ring.phase(energy), multiplicity))
                    with self.subTest(graph=graph.to_dict(), order=order, index=index):
                        self.assertEqual(remote_coefficient(graph, order, index), direct)

    def test_residue_decomposition_preserves_energy_mod_order(self):
        graph = Graph(4, ((0, 1), (1, 2), (2, 3), (0, 2)))
        for order in (2, 3, 6):
            for a in product(range(2 * order), repeat=4):
                residues = tuple(x % order for x in a)
                self.assertEqual((graph.energy(a) - graph.energy(residues)) % order, 0)

    def test_specialized_equality_is_not_series_equality(self):
        from singularity.examples import GRAPHS
        g, h = GRAPHS["spectral_g"], GRAPHS["spectral_h"]
        # At q=-1 only degree parities survive; the pair has equal degrees.
        self.assertEqual(residue_numerator(g, 2)[1], residue_numerator(h, 2)[1])
        self.assertNotEqual(local_coefficients(g, 2), local_coefficients(h, 2))
        self.assertNotEqual(residue_numerator(g, 3)[1], residue_numerator(h, 3)[1])

    def test_remote_index_uses_binomial_tail_not_enumeration(self):
        graph = Graph(3, ((0, 1),))
        index = 10 ** 30 + 7
        ring, numerator = residue_numerator(graph, 4)
        expected = ring.zero
        for j, element in enumerate(numerator):
            if (index - j) % 4 == 0:
                expected = ring.add(expected, ring.scale(element, comb((index - j) // 4 + 2, 2)))
        self.assertEqual(remote_coefficient(graph, 4, index), expected)
        for bad in (-1, True, 2.5):
            with self.assertRaises(ValueError):
                remote_coefficient(graph, 4, bad)
        with self.assertRaises(ValueError):
            residue_numerator(Graph(6), 4, max_profiles=4 ** 6 - 1)
        self.assertEqual(len(residue_numerator(Graph(6), 4, max_profiles=4 ** 6)[1]), 6 * 3 + 1)


class WeightedTests(unittest.TestCase):
    def test_hard_contraction_preserves_original_energy_and_volume(self):
        graph = WeightedGraph((1, 2, 3, 1), ((0, 1, 2), (1, 2, 1), (0, 2, 3), (2, 3, 1)))
        contracted, mapping = graph.contract(((0, 1),))
        self.assertEqual(contracted.masses, (3, 3, 1))
        self.assertEqual(contracted.edges, ((0, 1, 4), (1, 2, 1)))
        for a in product(range(4), repeat=contracted.n):
            original = tuple(a[mapping[i]] for i in range(graph.n))
            self.assertEqual(graph.energy(original), contracted.energy(a))
            self.assertEqual(graph.volume(original), contracted.volume(a))

    def test_unit_mass_replays_unweighted(self):
        weighted = WeightedGraph((1, 1, 1), ((0, 1, 1), (1, 2, 1)))
        graph = Graph(3, ((0, 1), (1, 2)))
        self.assertEqual(weighted_coefficients(weighted, 5), local_coefficients(graph, 5))

    def test_validation_and_parallel_edges(self):
        self.assertEqual(WeightedGraph((1, 1), ((0, 1, 2), (1, 0, 3))).edges, ((0, 1, 5),))
        with self.assertRaises(ValueError):
            WeightedGraph((0, 1), ())
        with self.assertRaises(ValueError):
            WeightedGraph((1, 1), ((0, 0, 1),))


if __name__ == '__main__':
    unittest.main()
