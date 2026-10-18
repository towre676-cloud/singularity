import json
import random
import unittest
from collections import Counter
from fractions import Fraction
from itertools import combinations
from pathlib import Path

from singularity.graph import Graph
from singularity.invariants import binary_cut_profile
from singularity.locality import (connected_supersets, girth_threshold, overlap_correction, regular_cycle_term,
                                  regular_log_prediction, connected_sets, cycle, cycle_log_difference, disjoint_union, exact_support_log, kappa,
                                  moment_series, moment_series_by_enumeration, moments_from_pinnings, pinned_log,
                                  pinned_series, pinned_series_by_enumeration, reconstruct_cycle_type, specialize_moments)
from singularity.polynomials import normalize, polynomial_from_json, power, scale, sub

ROOT = Path(__file__).resolve().parents[1]
CUBE = Graph(8, [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3), (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)])
MOBIUS = Graph(8, [(0, 1), (0, 4), (0, 7), (1, 2), (1, 5), (2, 3), (2, 6), (3, 4), (3, 7), (4, 5), (5, 6), (6, 7)])
K33 = Graph(6, [(u, v) for u in range(3) for v in range(3, 6)])
PRISM = Graph(6, [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (0, 3), (1, 4), (2, 5)])


def difference(a, b):
    return [normalize(sub(x, y)) for x, y in zip(a, b)]


def regular_girth_prediction(cycles, d, g, lam):
    """Delta N_g q^((d + lam - 2) g) (1 - q^2)^g (SNG-F56)."""
    return scale(power(kappa(lam, d), g), cycles)


class ConnectedSupportTests(unittest.TestCase):
    def test_compiler_uses_local_adjacency_after_graph_construction(self):
        # A full-edge scan per support makes a bounded-degree compiler quadratic
        # in graph size. The oracle is evaluated before the instrumented edge
        # container rejects such scans; cyclic supports exercise canonical keys.
        class NoFullEdgeScan(tuple):
            def __iter__(self):
                raise AssertionError("connected-support work scanned all graph edges")

        graph = disjoint_union(cycle(4), cycle(5))
        expected = pinned_series_by_enumeration(graph, 4)
        object.__setattr__(graph, "edges", NoFullEdgeScan(graph.edges))
        self.assertEqual(pinned_series(graph, 4), expected)

    def test_connected_sets_against_brute_force(self):
        rng = random.Random(5)
        for _ in range(25):
            n = rng.randint(1, 7)
            G = Graph(n, [e for e in combinations(range(n), 2) if rng.random() < 0.45])
            k = rng.randint(1, 5)
            expected = set()
            for size in range(1, k + 1):
                for S in combinations(range(n), size):
                    seen, stack = {S[0]}, [S[0]]
                    while stack:
                        v = stack.pop()
                        for w in G.neighbors[v]:
                            if w in S and w not in seen:
                                seen.add(w)
                                stack.append(w)
                    if len(seen) == size:
                        expected.add(frozenset(S))
            found = list(connected_sets(G, k))
            self.assertEqual(len(found), len(set(found)))
            self.assertEqual(set(found), expected)

    def test_compiler_against_enumeration(self):
        rng = random.Random(11)
        graphs = [CUBE, K33, Graph(5, []), Graph(6, [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4)])]
        graphs += [Graph(n, [e for e in combinations(range(n), 2) if rng.random() < 0.5]) for n in (4, 5, 6)]
        for G in graphs:
            for lam in (0, 2):
                self.assertEqual(pinned_series(G, 4, lam), pinned_series_by_enumeration(G, 4, lam))

    def test_exact_support_degree_and_disconnected_sets(self):
        G = Graph(6, [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (1, 4)])
        for S in (frozenset({0, 1, 2}), frozenset({0, 1, 2, 3}), frozenset({1, 4, 5})):
            phi = exact_support_log(G, S, 2, 6)
            self.assertTrue(all(not c for c in phi[: len(S)]))
            self.assertTrue(phi[len(S)])
        self.assertTrue(all(not c for c in exact_support_log(G, frozenset({0, 5}), 2, 6)))


class FirstCycleTests(unittest.TestCase):
    def test_cube_mobius_is_the_square_count(self):
        # Squares: cube 6, Moebius ladder 4.  L: 2 q^4 (1-q^2)^4, the retained fixture.
        L = difference(pinned_series(CUBE, 5, 0), pinned_series(MOBIUS, 5, 0))
        self.assertEqual(L[:4], [{}] * 4)
        self.assertEqual(L[4], regular_girth_prediction(2, 3, 4, 0))
        retained = json.loads((ROOT / "results/exact_examples.json").read_text())["pairs"]["regular_cube_mobius"]
        self.assertEqual(L[4], polynomial_from_json(retained["difference"]))
        A = difference(pinned_series(CUBE, 5, 2), pinned_series(MOBIUS, 5, 2))
        self.assertEqual(A[4], regular_girth_prediction(2, 3, 4, 2))

    def test_prism_against_k33_is_the_triangle_count(self):
        for lam in (0, 2):
            D = difference(pinned_series(PRISM, 4, lam), pinned_series(K33, 4, lam))
            self.assertEqual(D[:3], [{}] * 3)
            self.assertEqual(D[3], regular_girth_prediction(2, 3, 3, lam))

    def test_cycle_family(self):
        # A(C_g + C_g) - A(C_2g) = 2 [q^2 (1 - q^2)]^g x^g + O(x^(g+1)).
        for g in range(3, 7):
            two, one = disjoint_union(cycle(g), cycle(g)), cycle(2 * g)
            D = difference(pinned_series(two, g), pinned_series(one, g))
            self.assertEqual(D[:g], [{}] * g)
            self.assertEqual(D[g], scale(power(kappa(2), g), 2))
            if g <= 5:
                self.assertEqual(D, difference(pinned_series_by_enumeration(two, g), pinned_series_by_enumeration(one, g)))


class CycleReconstructionTests(unittest.TestCase):
    @staticmethod
    def partitions(n, smallest=3):
        if n == 0:
            yield []
            return
        for k in range(smallest, n + 1):
            for rest in CycleReconstructionTests.partitions(n - k, k):
                yield [k] + rest

    def test_every_two_regular_graph_at_half_its_order(self):
        for n in range(3, 13):
            R = n // 2
            tables = cycle_log_difference(R)
            for parts in self.partitions(n):
                H = disjoint_union(*[cycle(l) for l in parts])
                self.assertEqual(reconstruct_cycle_type(pinned_log(H, R), n, R, tables=tables), dict(sorted(Counter(parts).items())))

    def test_threshold_is_sharp(self):
        for n in range(6, 13):
            g = n // 2
            a = cycle(n)
            b = disjoint_union(cycle(g), cycle(n - g))
            D = difference(pinned_series(a, g), pinned_series(b, g))
            self.assertEqual(D[: g], [{}] * g)
            self.assertTrue(D[g])
            with self.assertRaises(ArithmeticError):
                reconstruct_cycle_type(pinned_log(a, g - 1), n, g - 1)


class MomentTests(unittest.TestCase):
    GRAPH = Graph(6, [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (1, 4)])

    def test_moment_compiler_and_specializations(self):
        M = moment_series(self.GRAPH, 5)
        self.assertEqual(M, moment_series_by_enumeration(self.GRAPH, 5))
        for lam in (0, 1, 2, 5):
            self.assertEqual(specialize_moments(M, lam), pinned_series(self.GRAPH, 5, lam))

    def test_extremal_strata(self):
        # S = j: zero-one profiles, cuts by size.  S = j^2: one vertex, degrees.
        M = moment_series(self.GRAPH, 5)
        cuts = binary_cut_profile(self.GRAPH)
        for j in range(1, 6):
            self.assertEqual({E: int(c) for (S, E), c in M[j].items() if S == j},
                             {c: k for (size, c), k in cuts.items() if size == j})
            self.assertEqual({E: int(c) for (S, E), c in M[j].items() if S == j * j},
                             dict(Counter(d * j * j for d in self.GRAPH.degrees)))

    def test_pinnings_determine_moments(self):
        # C(R,2) + 1 pinnings suffice (Vandermonde in q^(2 lam)); fewer are refused.
        R, q = 4, Fraction(1, 3)
        M = moment_series(self.GRAPH, R)
        values = {lam: [sum(c * q ** e for e, c in row.items()) for row in pinned_series(self.GRAPH, R, lam)] for lam in range(7)}
        expected = []
        for row in M:
            d = Counter()
            for (S, E), c in row.items():
                d[S] += c * q ** E
            expected.append({S: v for S, v in d.items() if v})
        self.assertEqual(moments_from_pinnings(values, R, q), expected)
        with self.assertRaises(ValueError):
            moments_from_pinnings({lam: values[lam] for lam in range(6)}, R, q)


class LoopDecompositionTests(unittest.TestCase):
    PETERSEN = Graph(10, [(i, (i + 1) % 5) for i in range(5)] + [(i, 5 + i) for i in range(5)]
                     + [(5 + i, 5 + (i + 2) % 5) for i in range(5)])

    def test_connected_supersets(self):
        G = Graph(7, [(0, 1), (1, 2), (2, 3), (3, 0), (2, 4), (4, 5), (5, 6), (1, 5)])
        base = {0, 1}
        found = list(connected_supersets(G, base, 5, forbidden=[6]))
        expected = {S for S in connected_sets(G, 5) if base <= S and 6 not in S}
        self.assertEqual(len(found), len(set(found)))
        self.assertEqual(set(found), expected)

    def test_threshold(self):
        self.assertEqual([girth_threshold(g) for g in (3, 4, 5, 6, 7)], [4, 5, 7, 8, 10])

    def test_below_first_overlap(self):
        # SNG-F60: log F = n b + sum N_l W_l below b_g, as absolute series.
        for lam in (0, 2):
            self.assertEqual(pinned_log(CUBE, 4, lam), regular_log_prediction(8, 3, {4: 6}, 4, lam))
            self.assertEqual(pinned_log(self.PETERSEN, 6, lam), regular_log_prediction(10, 3, {5: 12, 6: 10}, 6, lam))
            self.assertEqual(pinned_log(cycle(6), 6, lam), regular_log_prediction(6, 2, {6: 1}, 6, lam))

    def test_first_overlap(self):
        # SNG-F61: K33 has nine K_{2,3}; the cycle-only prediction fails at b_4 = 5, the corrected one holds.
        for lam in (0, 2):
            actual = pinned_log(K33, 5, lam)
            self.assertNotEqual(actual, regular_log_prediction(6, 3, {4: 9}, 5, lam))
            self.assertEqual(actual, regular_log_prediction(6, 3, {4: 9}, 5, lam, overlap=overlap_correction(K33, 5, lam)))
            self.assertEqual(overlap_correction(CUBE, 5, lam), {})

    def test_cycle_term_coefficients(self):
        for d, lam, g in [(2, 0, 4), (3, 2, 3), (3, 0, 5), (4, 2, 4)]:
            W = regular_cycle_term(d, g, g + 1, lam)
            self.assertEqual(W[:g], [{}] * g)
            self.assertEqual(W[g], power(kappa(lam, d), g))


if __name__ == "__main__":
    unittest.main()
