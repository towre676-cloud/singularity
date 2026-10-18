"""Tests for the periodic sector: residue numerators, palindromes, cutoff.

Declared finite population (exhaustive, no sampling): every graph on
n in {1, 2, 3} labeled vertices (every edge subset of K_n), every modulus
M in {1, 2, 3, 4}, and every assignment of phase exponents from
{-1, 0, 1, 2} to the edges.  Counts per M: 1 (n=1) + 5 (n=2) + 125 (n=3)
= 131 models, 524 models in total.  Direct oracle coefficients are compared
through volume K + 2M + 1 for each model.
"""
import unittest
from collections import defaultdict
from itertools import combinations, product
from math import comb

from singularity.graph import Graph
from singularity.periodic import (
    PeriodicComparison,
    PeriodicModel,
    compare_models,
    direct_coefficients,
    is_palindromic,
    periodic_cutoff,
    residue_numerator,
    series_from_numerator,
)

EXPONENTS = (-1, 0, 1, 2)
MODULI = (1, 2, 3, 4)


def population():
    models = []
    for n in (1, 2, 3):
        all_edges = list(combinations(range(n), 2))
        for size in range(len(all_edges) + 1):
            for edges in combinations(all_edges, size):
                graph = Graph(n, edges)
                for M in MODULI:
                    for exps in product(EXPONENTS, repeat=len(edges)):
                        models.append(PeriodicModel(graph, M, dict(zip(edges, exps))))
    return models


def bound(model):
    return model.K + 2 * model.modulus + 1


class PopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = population()
        cls.numerators = {}
        cls.direct = {}
        for model in cls.models:
            cls.numerators[model] = residue_numerator(model)
            cls.direct[model] = direct_coefficients(model, bound(model))

    def test_population_size(self):
        self.assertEqual(len(self.models), 4 * (1 + 5 + 125))
        self.assertEqual(len(set(self.models)), len(self.models))

    def test_residue_split_identity(self):
        for model in self.models:
            series = series_from_numerator(model, self.numerators[model], bound(model))
            self.assertEqual(series, self.direct[model], model)

    def test_palindrome(self):
        for model in self.models:
            numerator = self.numerators[model]
            self.assertEqual(len(numerator), model.K + 1)
            self.assertTrue(is_palindromic(numerator), model)

    def test_cutoff_theorem_exhaustive(self):
        groups = defaultdict(list)
        for model in self.models:
            cutoff = periodic_cutoff(model.n, model.modulus)
            key = (model.n, model.modulus, tuple(self.direct[model][: cutoff + 1]))
            groups[key].append(model)
        nontrivial = 0
        for members in groups.values():
            reference = self.direct[members[0]]
            for other in members[1:]:
                self.assertEqual(self.direct[other], reference)
                if other.graph != members[0].graph:
                    nontrivial += 1
        # Agreement through the cutoff between genuinely different graphs occurs.
        self.assertGreater(nontrivial, 0)

    def test_compare_models_matches_oracle_on_sample(self):
        # All pairs among n=2 models for each M (25 pairs per M).
        for M in MODULI:
            members = [m for m in self.models if m.n == 2 and m.modulus == M]
            for a, b in product(members, repeat=2):
                result = compare_models(a, b)
                self.assertEqual(result.equal, self.direct[a] == self.direct[b])
                if not result.equal:
                    k = result.first_difference
                    self.assertLessEqual(k, result.cutoff)
                    self.assertEqual(self.direct[a][k], result.first_coefficient)
                    self.assertEqual(self.direct[b][k], result.second_coefficient)
                    self.assertEqual(self.direct[a][:k], self.direct[b][:k])


class ExampleTests(unittest.TestCase):
    def setUp(self):
        self.path = Graph(3, [(0, 1), (1, 2)])
        self.edge_iso = Graph(3, [(0, 1)])

    def test_m2_pair_certified_equal(self):
        a = PeriodicModel(self.path, 2)
        b = PeriodicModel(self.edge_iso, 2)
        expected = [(1,), (-1,), (-1,), (1,)]
        self.assertEqual(residue_numerator(a), expected)
        self.assertEqual(residue_numerator(b), expected)
        result = compare_models(a, b)
        self.assertEqual(result, PeriodicComparison(1, True))
        self.assertNotEqual(a, b)
        self.assertEqual(direct_coefficients(a, 14), direct_coefficients(b, 14))

    def test_m3_pair_separates_at_volume_one(self):
        a = PeriodicModel(self.path, 3)
        b = PeriodicModel(self.edge_iso, 3)
        ring = a.ring
        zeta, zeta2 = ring.phase(1), ring.phase(2)
        path_f1 = ring.add(ring.scale(zeta, 2), zeta2)
        iso_f1 = ring.add(ring.scale(zeta, 2), ring.one)
        self.assertEqual(path_f1, (-1, 1))
        self.assertEqual(iso_f1, (1, 2))
        result = compare_models(a, b)
        self.assertFalse(result.equal)
        self.assertEqual(result.cutoff, 3)
        self.assertEqual(result.first_difference, 1)
        self.assertEqual(result.first_coefficient, path_f1)
        self.assertEqual(result.second_coefficient, iso_f1)
        self.assertEqual(direct_coefficients(a, 1)[1], path_f1)
        self.assertEqual(direct_coefficients(b, 1)[1], iso_f1)

    def test_modulus_one(self):
        for graph in (Graph(1), self.path, Graph(4, [(0, 1), (2, 3)])):
            model = PeriodicModel(graph, 1)
            self.assertEqual(residue_numerator(model), [(1,)])
            expected = [(comb(k + graph.n - 1, graph.n - 1),) for k in range(10)]
            self.assertEqual(series_from_numerator(model, [(1,)], 9), expected)
            self.assertEqual(direct_coefficients(model, 9), expected)

    def test_disconnected_and_isolated(self):
        graph = Graph(4, [(0, 1), (2, 3)])
        model = PeriodicModel(graph, 3, {(0, 1): 1, (2, 3): -1})
        numerator = residue_numerator(model)
        self.assertTrue(is_palindromic(numerator))
        self.assertEqual(series_from_numerator(model, numerator, 12),
                         direct_coefficients(model, 12))
        empty = PeriodicModel(Graph(3), 4)
        # No edges: every residue profile has weight one.
        expected = [(sum(1 for r in product(range(4), repeat=3) if sum(r) == k),) + (0,)
                    for k in range(10)]
        self.assertEqual(residue_numerator(empty), expected)

    def test_exponent_equivalences(self):
        for M in (2, 3, 4, 5):
            neg = PeriodicModel(self.path, M, {(0, 1): -1, (1, 2): -1})
            top = PeriodicModel(self.path, M, {(0, 1): M - 1, (1, 2): M - 1})
            self.assertEqual(residue_numerator(neg), residue_numerator(top))
            self.assertTrue(compare_models(neg, top).equal)
            zero = PeriodicModel(self.path, M, {(0, 1): 0, (1, 2): 1})
            mult = PeriodicModel(self.path, M, {(0, 1): 3 * M, (1, 2): 1 - 2 * M})
            self.assertEqual(residue_numerator(zero), residue_numerator(mult))
            self.assertEqual(direct_coefficients(zero, 2 * M), direct_coefficients(mult, 2 * M))
        # Exponent zero on every edge is the edgeless count.
        flat = PeriodicModel(self.path, 3, {(0, 1): 0, (1, 2): 0})
        self.assertEqual(residue_numerator(flat), residue_numerator(PeriodicModel(Graph(3), 3)))

    def test_model_attributes(self):
        model = PeriodicModel(self.path, 4, {(1, 2): -3})
        self.assertEqual(model.n, 3)
        self.assertEqual(model.K, 9)
        self.assertEqual(model.ring.order, 4)
        self.assertEqual(model.phases, (((0, 1), 1), ((1, 2), -3)))
        self.assertEqual(periodic_cutoff(3, 4), 4)
        self.assertEqual(periodic_cutoff(1, 1), 0)
        with self.assertRaises(Exception):
            model.modulus = 5


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.graph = Graph(3, [(0, 1), (1, 2)])

    def test_modulus(self):
        for bad in (True, 2.0):
            with self.assertRaises(TypeError):
                PeriodicModel(self.graph, bad)
        for bad in (0, -3):
            with self.assertRaises(ValueError):
                PeriodicModel(self.graph, bad)
        with self.assertRaises(TypeError):
            periodic_cutoff(3, 2.0)
        with self.assertRaises(ValueError):
            periodic_cutoff(3, 0)

    def test_phases(self):
        with self.assertRaises(ValueError):
            PeriodicModel(self.graph, 3, {(0, 2): 1})
        with self.assertRaises(ValueError):
            PeriodicModel(self.graph, 3, {(1, 0): 1})
        for bad in (True, 1.0):
            with self.assertRaises(TypeError):
                PeriodicModel(self.graph, 3, {(0, 1): bad})
        with self.assertRaises(TypeError):
            PeriodicModel(self.graph, 3, [((0, 1), 1)])
        with self.assertRaises(TypeError):
            PeriodicModel((3, [(0, 1)]), 3)

    def test_budgets_and_volumes(self):
        model = PeriodicModel(self.graph, 5)
        with self.assertRaises(ValueError):
            residue_numerator(model, max_profiles=124)
        self.assertEqual(len(residue_numerator(model, max_profiles=125)), 13)
        with self.assertRaises(ValueError):
            direct_coefficients(model, 10, max_profiles=comb(13, 3) - 1)
        with self.assertRaises(TypeError):
            direct_coefficients(model, 2.0)
        with self.assertRaises(ValueError):
            series_from_numerator(model, residue_numerator(model), -1)
        with self.assertRaises(ValueError):
            series_from_numerator(model, [(1,)], 3)

    def test_compare_requires_same_shape(self):
        with self.assertRaises(ValueError):
            compare_models(PeriodicModel(self.graph, 3), PeriodicModel(self.graph, 2))
        with self.assertRaises(ValueError):
            compare_models(PeriodicModel(self.graph, 3), PeriodicModel(Graph(2, [(0, 1)]), 3))
        with self.assertRaises(TypeError):
            compare_models(PeriodicModel(self.graph, 3), self.graph)


if __name__ == "__main__":
    unittest.main()
