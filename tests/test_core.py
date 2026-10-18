"""Independent finite oracles for graph-height identities and the discoveries."""

from collections import Counter
from dataclasses import FrozenInstanceError
from fractions import Fraction
from itertools import combinations, permutations, product
import json
from math import comb
from pathlib import Path
import tempfile
import unittest

from singularity.examples import GRAPHS
from singularity.graph import Graph
from singularity.heights import (
    componentwise_normalized_coefficients, local_coefficients, marked_coefficients,
    nested_energy, normalize_heights, normalized_coefficients, threshold_sets,
    weak_compositions,
)
from singularity.polynomials import series_mul
from singularity.invariants import (
    binary_cut_profile, first_difference, laplacian_characteristic_polynomial,
    minimum_cut_profile,
)


def small_graphs(max_n=4):
    for n in range(1, max_n + 1):
        possible = list(combinations(range(n), 2))
        for mask in range(1 << len(possible)):
            yield Graph(n, [edge for j, edge in enumerate(possible) if mask >> j & 1])


def direct_energy(graph, a):
    return sum((a[i] - a[j]) * (a[i] - a[j]) for i, j in graph.edges)


def determinant(matrix):
    """Leibniz determinant is deliberately independent of Newton identities."""
    n = len(matrix)
    result = 0
    for permutation in permutations(range(n)):
        inversions = sum(permutation[i] > permutation[j] for i in range(n) for j in range(i + 1, n))
        term = (-1) ** inversions
        for i, j in enumerate(permutation):
            term *= matrix[i][j]
        result += term
    return result


class GraphTests(unittest.TestCase):
    def test_canonical_immutable_and_source_roundtrip(self):
        source = [[2, 0], [1, 0]]
        graph = Graph(4, source)
        source[0][0] = 3
        self.assertEqual(graph.edges, ((0, 1), (0, 2)))
        self.assertEqual(graph.degrees, (2, 1, 1, 0))
        self.assertEqual(graph.components(), ((0, 1, 2), (3,)))
        self.assertEqual(Graph.from_dict(graph.to_dict()), graph)
        with self.assertRaises(FrozenInstanceError):
            graph.n = 3

    def test_reject_invalid_graph_data(self):
        for n, edges in ((0, []), (-1, []), (3, [(0, 0)]), (3, [(0, 1), (1, 0)]), (3, [(-1, 2)]), (3, [(0, 3)]), (3, [(0, 1, 2)])):
            with self.subTest(n=n, edges=edges), self.assertRaises(ValueError):
                Graph(n, edges)
        for n, edges in ((True, []), (3.0, []), (3, [(False, 2)]), (3, [(0, 1.5)])):
            with self.subTest(n=n, edges=edges), self.assertRaises(TypeError):
                Graph(n, edges)

    def test_signed_energy_and_validation(self):
        graph = Graph(2, [(0, 1)])
        self.assertEqual(graph.energy((-2, 3)), 25)
        with self.assertRaises(ValueError):
            graph.energy((0,))
        with self.assertRaises(TypeError):
            graph.energy((False, 1))
        with self.assertRaises(ValueError):
            graph.relabel((0, 0))

    def test_laplacian_and_characteristic_polynomial_all_small_graphs(self):
        for graph in small_graphs():
            lap = graph.laplacian()
            self.assertTrue(all(sum(row) == 0 for row in lap))
            polynomial = laplacian_characteristic_polynomial(graph)
            self.assertEqual(len(polynomial), graph.n + 1)
            self.assertEqual(polynomial[0], 1)
            for t in range(graph.n + 1):
                actual = sum(c * t ** (graph.n - j) for j, c in enumerate(polynomial))
                expected = determinant([
                    [(t if i == j else 0) - lap[i][j] for j in range(graph.n)]
                    for i in range(graph.n)
                ])
                self.assertEqual(actual, expected, (graph, t))


class HeightTests(unittest.TestCase):
    def test_weak_compositions_against_direct_product(self):
        for n in range(0, 5):
            for total in range(5):
                expected = [a for a in product(range(total + 1), repeat=n) if sum(a) == total]
                actual = list(weak_compositions(total, n))
                self.assertEqual(actual, expected)
                if n:
                    self.assertEqual(len(actual), comb(total + n - 1, n - 1))
        with self.assertRaises(ValueError):
            list(weak_compositions(-1, 2))

    def test_energy_shift_nested_decomposition_all_small_graphs(self):
        for graph in small_graphs():
            lap = graph.laplacian()
            for a in product(range(3), repeat=graph.n):
                energy = direct_energy(graph, a)
                self.assertEqual(graph.energy(a), energy)
                self.assertEqual(nested_energy(graph, a), energy)
                self.assertEqual(graph.energy(tuple(x + 5 for x in a)), energy)
                self.assertEqual(graph.energy(normalize_heights(a)), energy)
                self.assertEqual(sum(map(len, threshold_sets(a))), sum(a))
                self.assertEqual(sum(a[i] * lap[i][j] * a[j] for i in range(graph.n) for j in range(graph.n)), energy)

    def test_local_normalized_and_marked_against_direct_products(self):
        for graph in small_graphs():
            bound = 3
            expected = [Counter() for _ in range(bound + 1)]
            normalized = [Counter() for _ in range(bound + 1)]
            marked = Counter()
            for a in product(range(bound + 1), repeat=graph.n):
                total = sum(a)
                if total <= bound:
                    energy = direct_energy(graph, a)
                    expected[total][energy] += 1
                    if min(a) == 0:
                        normalized[total][energy] += 1
                        marked[total, energy, max(a)] += 1
            self.assertEqual(local_coefficients(graph, bound), expected)
            self.assertEqual(normalized_coefficients(graph, bound), normalized)
            self.assertEqual(marked_coefficients(graph, bound), marked)

    def test_binary_sector_and_complement_all_small_graphs(self):
        for graph in small_graphs():
            profile = binary_cut_profile(graph)
            brute = Counter((sum(a), direct_energy(graph, a)) for a in product((0, 1), repeat=graph.n))
            self.assertEqual(profile, brute)
            self.assertEqual(sum(profile.values()), 2 ** graph.n)
            for (size, cut), count in profile.items():
                self.assertEqual(profile[graph.n - size, cut], count)
            # Only volumes <= n-1 are needed for nonconstant binary assignments.
            marked = marked_coefficients(graph, graph.n - 1)
            binary_marked = {(v, e): c for (v, e, span), c in marked.items() if span == 1}
            interior = {key: c for key, c in profile.items() if 0 < key[0] < graph.n}
            self.assertEqual(binary_marked, interior)

    def test_minimum_cut_is_minimum_nonzero_normalized_energy(self):
        for graph in small_graphs():
            if graph.n == 1 or not graph.connected:
                with self.assertRaises(ValueError):
                    minimum_cut_profile(graph)
                continue
            minimum, sizes = minimum_cut_profile(graph)
            energies = []
            minimizers = Counter()
            for a in product(range(3), repeat=graph.n):
                if min(a) == 0 and max(a) > 0:
                    energy = direct_energy(graph, a)
                    energies.append(energy)
                    self.assertGreaterEqual(energy, minimum * max(a))
                    if energy == minimum:
                        self.assertEqual(max(a), 1)
                        minimizers[sum(a)] += 1
            self.assertEqual(min(energies), minimum)
            self.assertEqual(sizes, minimizers)

    def test_minimum_cut_shell_needs_connectedness_and_is_symmetric(self):
        # P13 edge cases: K2 + K1 has a nonzero normalized profile of energy zero, and its
        # smallest positive energy is attained by a profile that is not a minimum-cut side.
        graph = Graph(3, [(0, 1)])
        self.assertEqual(direct_energy(graph, (1, 1, 0)), 0)
        self.assertEqual(direct_energy(graph, (1, 0, 0)), 1)
        with self.assertRaises(ValueError):
            minimum_cut_profile(graph)
        # Both sides of every minimum cut are counted: sizes are symmetric under r -> n - r.
        for g in small_graphs():
            if g.n >= 2 and g.connected:
                _, sizes = minimum_cut_profile(g)
                self.assertEqual(dict(sizes), {g.n - r: c for r, c in sizes.items()})

    def test_relabel_invariance_all_small_graphs(self):
        for graph in small_graphs():
            relabeled = graph.relabel(tuple(reversed(range(graph.n))))
            self.assertEqual(binary_cut_profile(graph), binary_cut_profile(relabeled))
            self.assertEqual(local_coefficients(graph, 3), local_coefficients(relabeled, 3))
            self.assertEqual(marked_coefficients(graph, 3), marked_coefficients(relabeled, 3))


class SemanticsTests(unittest.TestCase):
    """P01: the published examples of docs/specifications/COEFFICIENTS-v1.md."""

    def test_disconnected_global_versus_componentwise_translation(self):
        graph = Graph(3, [(0, 1)])  # K2 on {0,1} plus the isolated vertex 2
        # Global min(a)=0 keeps (1,1,0): the component {0,1} stays positive.
        self.assertEqual(normalized_coefficients(graph, 4), [
            {0: 1}, {0: 1, 1: 2}, {0: 2, 1: 2, 4: 2}, {0: 1, 1: 4, 4: 2, 9: 2},
            {0: 2, 1: 2, 4: 4, 9: 2, 16: 2}])
        # One translation per component: min zero on {0,1} and a_2=0.
        self.assertEqual(componentwise_normalized_coefficients(graph, 4),
                         [{0: 1}, {1: 2}, {4: 2}, {9: 2}, {16: 2}])
        # Componentwise quotient is the product of component B series.
        edge, point = normalized_coefficients(Graph(2, [(0, 1)]), 4), normalized_coefficients(Graph(1), 4)
        self.assertEqual(componentwise_normalized_coefficients(graph, 4), series_mul(edge, point))
        # Global quotient: B = (1-x^3)/((1-x^2)(1-x)) B_K2 B_K1 (SNG-F19).
        geometric2 = [{0: 1} if m % 2 == 0 else {} for m in range(5)]
        geometric1 = [{0: 1}] * 5
        cubic = [{0: 1}, {}, {}, {0: -1}, {}]
        global_series = series_mul(series_mul(series_mul(cubic, geometric2), geometric1), series_mul(edge, point))
        self.assertEqual(normalized_coefficients(graph, 4), global_series)

    def test_quotients_agree_exactly_for_connected_graphs(self):
        for graph in small_graphs():
            # Disconnected: lifting a smallest component by one is globally
            # normalized at volume <= 3 when n <= 4, but not componentwise.
            same = componentwise_normalized_coefficients(graph, 3) == normalized_coefficients(graph, 3)
            self.assertEqual(same, graph.connected, graph)

    def test_zero_volume_singleton_and_inclusive_truncation(self):
        self.assertEqual(local_coefficients(Graph(1), 3), [{0: 1}] * 4)
        self.assertEqual(normalized_coefficients(Graph(1), 3), [{0: 1}, {}, {}, {}])
        self.assertEqual(marked_coefficients(Graph(1), 3), {(0, 0, 0): 1})
        self.assertEqual(marked_coefficients(Graph(2, [(0, 1)]), 3),
                         {(0, 0, 0): 1, (1, 1, 1): 2, (2, 4, 2): 2, (3, 9, 3): 2})
        for graph in (Graph(1), Graph(3, [(0, 1)]), GRAPHS["spectral_g"]):
            self.assertEqual(local_coefficients(graph, 0), [{0: 1}])
            self.assertEqual(normalized_coefficients(graph, 0), [{0: 1}])
            self.assertEqual(marked_coefficients(graph, 0), {(0, 0, 0): 1})
        # A truncation at M returns rows 0..M; enlarging M never changes them.
        graph = Graph(4, [(0, 1), (1, 2)])
        longer = marked_coefficients(graph, 5)
        self.assertEqual(marked_coefficients(graph, 3), {k: c for k, c in longer.items() if k[0] <= 3})
        self.assertEqual(local_coefficients(graph, 5)[:4], local_coefficients(graph, 3))

    def test_automorphisms_do_not_divide_multiplicities(self):
        # K2's swap symmetry leaves both (h,0) and (0,h) in the population.
        self.assertEqual(normalized_coefficients(Graph(2, [(0, 1)]), 2), [{0: 1}, {1: 2}, {4: 2}])


class DiscoveryTests(unittest.TestCase):
    def test_spectral_pair(self):
        graph, other = GRAPHS["spectral_g"], GRAPHS["spectral_h"]
        expected = (1, -14, 73, -178, 209, -112, 21, 0)
        self.assertEqual(laplacian_characteristic_polynomial(graph), expected)
        self.assertEqual(laplacian_characteristic_polynomial(other), expected)
        self.assertNotEqual(binary_cut_profile(graph), binary_cut_profile(other))
        depth, polynomial = first_difference(graph, other, 3)
        self.assertEqual(depth, 2)
        self.assertEqual(polynomial, {2: 2, 3: -4, 5: 4, 6: -2})
        self.assertEqual(sum(c * Fraction(1, 2) ** e for e, c in polynomial.items()), Fraction(3, 32))

    def test_binary_pair_all_128_assignments_and_first_nested_difference(self):
        graph, other = GRAPHS["binary_g"], GRAPHS["binary_h"]
        profile = binary_cut_profile(graph)
        self.assertEqual(profile, binary_cut_profile(other))
        self.assertEqual(sum(profile.values()), 128)
        self.assertNotEqual(laplacian_characteristic_polynomial(graph), laplacian_characteristic_polynomial(other))
        expected = {3: 1, 4: -1, 6: -2, 8: 2, 9: 1, 10: 3, 11: -3, 12: -1, 13: -2, 15: 2, 17: 1, 18: -1}
        self.assertEqual(first_difference(graph, other, 2), None)
        self.assertEqual(first_difference(graph, other, 3), (3, expected))
        self.assertEqual(sum(c * Fraction(1, 2) ** e for e, c in expected.items()), Fraction(11025, 262144))
        left, right = marked_coefficients(graph, 3), marked_coefficients(other, 3)
        observed = {}
        for key in left.keys() | right.keys():
            difference = left.get(key, 0) - right.get(key, 0)
            if difference:
                self.assertEqual((key[0], key[2]), (3, 2))
                observed[key[1]] = difference
        self.assertEqual(observed, expected)
        self.assertEqual(sum(c for (v, e, h), c in left.items() if v == 3 and h == 2), 42)


class CliIntegrationTests(unittest.TestCase):
    def invoke(self, *arguments):
        from singularity.cli import build_parser, run
        result = run(build_parser().parse_args(arguments))
        # User-facing command results must survive ordinary JSON serialization.
        return json.loads(json.dumps(result))

    def test_profile_comparison_and_population(self):
        profile = self.invoke("profile", "--example", "binary_g", "--max-volume", "3")
        self.assertEqual(sum(row["multiplicity"] for row in profile["binary_cut_profile"]), 128)
        result = self.invoke("compare", "binary_g", "binary_h", "--max-volume", "3")
        self.assertTrue(result["same_binary_cut_profile"])
        self.assertEqual(result["first_formal_difference"]["volume"], 3)
        self.assertEqual(result["first_formal_difference"]["specialization"]["value"], "11025/262144")
        population = self.invoke("population", "--graph-json", '{"n":2,"edges":[[0,1]]}', "--max-height", "2", "--span", "2", "--unrank", "1")
        self.assertEqual(population["count"], 2)
        self.assertEqual(population["unrank_request"]["heights"], [2, 0])

    def test_euler_transfer_and_conductor(self):
        result = self.invoke("euler", "--example", "binary_g", "--max-volume", "3")
        self.assertTrue(result["recomposition_matches"])
        transfer = self.invoke("transfer", "--path", "6", "--max-height", "2")
        self.assertEqual(transfer["count"], 3 ** 6)
        conductor = self.invoke("conductor", "--path", "2", "--order", "2", "--index", "3")
        # At q=-1, all four total-volume-three assignments have odd energy.
        self.assertEqual(conductor["coefficient_constant_first"], [-4])

    def test_certificate_build_and_replay(self):
        certificate = self.invoke("certificate", "build", "--example", "binary_g", "--comparison", "binary_h", "--max-volume", "3", "--claim-known-factorization")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "certificate.json"
            source.write_text(json.dumps(certificate), encoding="utf-8")
            self.assertTrue(self.invoke("certificate", "replay", str(source))["valid"])
            certificate["local_coefficients"][0][0][1] = 2
            source.write_text(json.dumps(certificate), encoding="utf-8")
            self.assertFalse(self.invoke("certificate", "replay", str(source))["valid"])


if __name__ == "__main__":
    unittest.main()
