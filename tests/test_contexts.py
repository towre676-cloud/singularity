import unittest
from collections import Counter
from fractions import Fraction

from singularity.contexts import (boundary_determinant, interpolation_rank, _context_series, finite_difference_budget, finite_difference_probe_set,
                                  recover_by_finite_differences, tau, interface_status, interior_zero_coefficient, lower_degree_condition,
                                  orbit_groups, recover_symmetrized_kernel, symmetric_context, symmetric_interface_rank,
                                  symmetric_interface_rank_mod, symmetric_probe_set, symmetrize, top_block_rank_mod,
                                  top_degree_defect, top_degree_kernel, weighted_probe)
from singularity.heights import weak_compositions
from singularity.polynomials import add, mul
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.terminals import glue_graphs, terminal_kernel

Q0 = Fraction(1, 2)
BLOCK = Graph(5, [(0, 2), (2, 3), (3, 1), (2, 4)])  # asymmetric: the leaf sits next to terminal 0


def at(poly):
    return sum((c * Q0 ** e for e, c in poly.items()), Fraction(0))


class SymmetrizationTests(unittest.TestCase):
    def test_symmetric_context_sees_only_the_symmetrized_kernel(self):
        # SNG-F47: sum over orbits of x^|o| K^+(o) K_C(o) equals the glued series.
        R = 5
        context = Graph(4, [(0, 2), (2, 3), (3, 1)])  # path with terminals at its ends: swap-symmetric
        plus = symmetrize(terminal_kernel(BLOCK, (0, 1), R))
        kc = terminal_kernel(context, (0, 1), R)
        rows = [Counter() for _ in range(R + 1)]
        for o, cells in plus.items():
            for (v1, e1), c1 in cells.items():
                for (v2, e2), c2 in kc.get(o, {}).items():
                    if sum(o) + v1 + v2 <= R:
                        rows[sum(o) + v1 + v2][e1 + e2] += c1 * c2
        glued, _ = glue_graphs(BLOCK, (0, 1), context, (0, 1))
        self.assertEqual([dict(r) for r in rows], local_coefficients(glued, R))

    def test_symmetrization_forgets_the_terminal_order(self):
        K = terminal_kernel(BLOCK, (0, 1), 4)
        self.assertNotEqual(K, terminal_kernel(BLOCK, (1, 0), 4))
        self.assertEqual(symmetrize(K), symmetrize(terminal_kernel(BLOCK, (1, 0), 4)))
        with self.assertRaises(ValueError):
            symmetrize({(0, 0, 0): {(0, 0): 1}})


class TopDegreeObstructionTests(unittest.TestCase):
    def test_orbits_with_equal_square_sum_agree_at_interior_volume_zero(self):
        # SNG-F48(a): without a terminal edge, a swap-symmetric context gives
        # {0,5} and {3,4} the same interior-volume-zero cell.
        contexts = [Graph(4, [(0, 2), (2, 1), (0, 3), (3, 1)]),  # 4-cycle, terminals opposite
                    Graph(4, [(0, 2), (2, 3), (3, 1)]),
                    Graph(5, [(0, 2), (1, 3), (2, 4), (3, 4)])]
        for context in contexts:
            K = terminal_kernel(context, (0, 1), 7)
            zero = lambda b: {k: c for k, c in K[b].items() if k[0] == 0}
            self.assertEqual(zero((0, 5)), zero((3, 4)))
        edged = terminal_kernel(Graph(2, [(0, 1)]), (0, 1), 7)
        self.assertNotEqual(edged[0, 5], edged[3, 4])

    def test_groups(self):
        self.assertEqual(top_degree_defect(6), 0)
        self.assertEqual(orbit_groups(7)[25], [(0, 5), (3, 4)])
        self.assertEqual(top_degree_defect(7), 1)
        self.assertTrue(all(len(g) <= 2 for g in orbit_groups(24).values()))
        self.assertEqual(orbit_groups(25)[325], [(1, 18), (6, 17), (10, 15)])

    def test_small_budget_rank_is_full(self):
        for R in range(5):
            unknowns, rank = symmetric_interface_rank(R, Q0, False)
            self.assertEqual(rank, unknowns)


class RecoveryTests(unittest.TestCase):
    def probes(self, graph, R):
        values = {}
        for d, e in symmetric_probe_set(R):
            context, terminals = symmetric_context(d, bool(e))
            glued, _ = glue_graphs(graph, (0, 1), context, terminals)
            values[d, e] = [at(row) for row in local_coefficients(glued, R)]
        return values

    def test_recovers_the_symmetrized_kernel(self):
        R = 3
        Y = recover_symmetrized_kernel(self.probes(BLOCK, R), R, Q0)
        plus = symmetrize(terminal_kernel(BLOCK, (0, 1), R))
        for o, series in Y.items():
            self.assertEqual(series[: sum(o)], [0] * sum(o))
            for interior in range(R + 1 - sum(o)):
                expected = sum((c * Q0 ** en for (v, en), c in plus.get(o, {}).items() if v == interior), Fraction(0))
                self.assertEqual(series[sum(o) + interior], expected)

    def test_malformed_and_inconsistent_probes(self):
        R = 2
        values = self.probes(BLOCK, R)
        with self.assertRaises(ValueError):
            recover_symmetrized_kernel({k: v for k, v in values.items() if k != (0, 1)}, R, Q0)
        with self.assertRaises(ValueError):
            recover_symmetrized_kernel(values, R, Fraction(1))
        broken = dict(values)
        broken[0, 0] = [v + (1 if i == 2 else 0) for i, v in enumerate(values[0, 0])]
        with self.assertRaises(ArithmeticError):
            recover_symmetrized_kernel(broken, R, Q0)
        with self.assertRaises(ArithmeticError):
            recover_symmetrized_kernel(values, 25, Q0)


class ObservableQuotientTests(unittest.TestCase):
    def test_blind_direction_at_budget_25(self):
        # SNG-F49(a): the triple 325 = 1+324 = 36+289 = 100+225 with (s-t)^2 = 289, 121, 25.
        (v,) = top_degree_kernel(25, 2)
        self.assertEqual(set(v), {(1, 18), (6, 17), (10, 15)})
        self.assertEqual(v[1, 18], {25: 1, 121: -1})
        self.assertEqual(v[6, 17], {289: 1, 25: -1})
        self.assertEqual(v[10, 15], {121: 1, 289: -1})
        for e in (0, 1):
            total = {}
            for (s, t), poly in v.items():
                total = add(total, mul(poly, {e * (s - t) ** 2: 1}))
            self.assertEqual(total, {})
        # (10, 15) has |o| = 25: interior volume zero, fixed by terminal degrees.
        self.assertEqual(top_degree_kernel(25, 2, realizable=True), [])
        self.assertEqual(top_degree_kernel(26, 2, realizable=True), [v])
        self.assertEqual(top_block_rank_mod(25, 2), (182, 181))
        self.assertEqual(top_block_rank_mod(25, 2, realizable=True), (169, 169))
        self.assertEqual(top_block_rank_mod(25, 3), (182, 182))

    def test_interface_dimensions(self):
        self.assertEqual(interface_status(7, 1)["invisible_dimension"], 1)
        self.assertEqual(interface_status(7, 1, realizable=True)["invisible_dimension"], 0)
        self.assertEqual(interface_status(8, 1, realizable=True)["invisible_dimension"], 1)
        self.assertEqual(interface_status(24, 2)["invisible_dimension"], 0)
        self.assertEqual(interface_status(25, 2)["invisible_dimension"], 1)
        self.assertEqual(interface_status(25, 2, realizable=True)["invisible_dimension"], 0)
        self.assertEqual(interface_status(26, 2, realizable=True)["invisible_dimension"], 1)
        self.assertIsNone(interface_status(26, 2)["invisible_dimension"])

    def test_interior_volume_zero_is_fixed_by_terminal_degrees(self):
        for graph in (BLOCK, Graph(6, [(0, 2), (0, 3), (1, 4), (2, 5), (4, 5), (3, 4)])):
            K = terminal_kernel(graph, (0, 1), 6)
            plus = symmetrize(K)
            degrees = (graph.degrees[0], graph.degrees[1])
            for o in [(0, 1), (1, 2), (0, 3), (2, 2), (1, 5), (3, 3)]:
                cells = {e: c for (v, e), c in plus[o].items() if v == 0}
                self.assertEqual(cells, interior_zero_coefficient(degrees, o))

    def test_second_functional(self):
        # The x^1 coefficient of d leaves per terminal and c shared neighbours is
        # q^((d+c) m) (d sigma + c pi): trading a leaf for a shared neighbour gives tau = sigma - pi.
        R = 3
        for s, t in [(0, 2), (1, 1), (1, 2)]:
            m = s * s + t * t
            sigma = Q0 ** (1 - 2 * s) + Q0 ** (1 - 2 * t)
            pi = Q0 ** (2 - 2 * (s + t))
            for d, c in [(1, 0), (0, 1), (2, 1), (1, 3)]:
                series = _context_series((s, t), d, 0, c, R, Q0)
                self.assertEqual(series[0], Q0 ** ((d + c) * m))
                self.assertEqual(series[1], Q0 ** ((d + c) * m) * (d * sigma + c * pi))

    def test_lower_degree_condition(self):
        self.assertEqual(lower_degree_condition(40, 1), 25)
        self.assertEqual(lower_degree_condition(40, 1, realizable=True), 26)
        self.assertIsNone(lower_degree_condition(60, 2))

    def test_modular_rank_meets_the_proved_dimension(self):
        for R in (7, 9):
            status = interface_status(R, 1)
            self.assertEqual(symmetric_interface_rank_mod(R, False), (status["unknowns"], status["unknowns"] - status["top_defect"]))


class WeightedRestorationTests(unittest.TestCase):
    def test_weighted_terminal_edge_recovers(self):
        # SNG-F50 on a real weighted gluing, glued series by weak compositions.
        R, W = 2, 2
        values = {}
        for d, e in symmetric_probe_set(R, W):
            probe = weighted_probe(BLOCK, d, e)
            values[d, e] = [sum((Q0 ** probe.energy(a) for a in weak_compositions(v, probe.n)), Fraction(0)) for v in range(R + 1)]
        Y = recover_symmetrized_kernel(values, R, Q0, max_edge_weight=W)
        plus = symmetrize(terminal_kernel(BLOCK, (0, 1), R))
        for o, series in Y.items():
            for interior in range(R + 1 - sum(o)):
                self.assertEqual(series[sum(o) + interior],
                                 sum((c * Q0 ** en for (v, en), c in plus.get(o, {}).items() if v == interior), Fraction(0)))

    def test_multiplicity_check(self):
        with self.assertRaises(ArithmeticError):
            recover_symmetrized_kernel({}, 25, Q0, max_edge_weight=1)
        with self.assertRaises(ValueError):  # weights 0..2 pass the multiplicity check; probes are missing
            recover_symmetrized_kernel({}, 25, Q0, max_edge_weight=2)
        with self.assertRaises(ValueError):
            weighted_probe(Graph(2, [(0, 1)]), 0, 1)


class AllOrderRecoveryTests(unittest.TestCase):
    def test_closed_form_context_series_matches_actual_contexts(self):
        R = 5
        for d, c in [(0, 2), (2, 1), (1, 0)]:
            context, terminals = symmetric_context(d, False, c)
            K = terminal_kernel(context, terminals, R)
            for o in [(0, 0), (0, 2), (1, 1), (1, 3)]:
                actual = [Fraction(0)] * (R + 1)
                for (v, e), count in K.get(o, {}).items():
                    actual[v] += count * Q0 ** e
                self.assertEqual(actual[: R + 1 - sum(o)], _context_series(o, d, 0, c, R, Q0)[: R + 1 - sum(o)])

    def test_finite_differences_vanish_below_order_j(self):
        # SNG-F51: sum_c (-1)^(j-c) C(j,c) P^(k-c) S^c = P^(k-j) (S-P)^j.
        from math import comb
        R, q = 6, Fraction(1, 3)
        for o in [(0, 2), (1, 3), (2, 2)]:
            m = o[0] ** 2 + o[1] ** 2
            for k in range(4):
                for j in range(k + 1):
                    D = [Fraction(0)] * (R + 1)
                    for c in range(j + 1):
                        D = [a + (-1) ** (j - c) * comb(j, c) * b for a, b in zip(D, _context_series(o, k - c, 0, c, R, q))]
                    self.assertEqual(D[:j], [0] * j)
                    self.assertEqual(D[j], q ** (k * m) * (-tau(o, q)) ** j)

    def test_tau_orders_each_circle(self):
        # tau = 1 - (q^(1-2s) - 1)(q^(1-2t) - 1) strictly decreases toward balance.
        for q in (Fraction(1, 10), Fraction(1, 2), Fraction(9, 10)):
            for group in orbit_groups(60).values():
                values = [tau(o, q) for o in sorted(group, key=lambda o: o[1] - o[0])]
                self.assertTrue(all(a < b for a, b in zip(values, values[1:])))
                for o in group:  # tau > 1 exactly for {0, t}, t >= 1
                    self.assertEqual(tau(o, q) > 1, o[0] == 0 and o[1] > 0)

    def test_recovery_past_the_top_degree_obstruction(self):
        # R = 7 has a top-degree defect without the edge; one extra volume recovers it.
        R = 7
        self.assertEqual(top_degree_defect(R), 1)
        B = finite_difference_budget(R)
        self.assertEqual(B, 8)
        block = Graph(6, [(0, 2), (2, 3), (3, 1), (2, 4), (4, 5)])
        plus = symmetrize(terminal_kernel(block, (0, 1), B))
        values = {}
        for d, c in finite_difference_probe_set(R):
            series = [Fraction(0)] * (B + 1)
            for o, cells in plus.items():
                ctx = _context_series(o, d, 0, c, B, Q0)
                for (v, en), count in cells.items():
                    for w in range(B + 1 - sum(o) - v):
                        series[sum(o) + v + w] += count * Q0 ** en * ctx[w]
            values[d, c] = series
        Y = recover_by_finite_differences(values, R, Q0)
        for o, series in Y.items():
            for interior in range(R + 1 - sum(o)):
                self.assertEqual(series[sum(o) + interior],
                                 sum((c * Q0 ** en for (v, en), c in plus.get(o, {}).items() if v == interior), Fraction(0)))
        with self.assertRaises(ValueError):
            recover_by_finite_differences({k: v[:B] for k, v in values.items()}, R, Q0)


class SliceRigidityTests(unittest.TestCase):
    def test_first_interior_slice_has_four_coefficients(self):
        # SNG-F52(a): [x] K(s,t) = q^Q0 sum_v q^deg(v) U^A_sv V^A_tv, U = q^(-2s), V = q^(-2t).
        for graph in (Graph(6, [(0, 2), (0, 3), (1, 4), (2, 5), (4, 5), (3, 4), (2, 3)]),
                      Graph(5, [(0, 2), (2, 3), (3, 1), (2, 4), (0, 1)])):
            K = terminal_kernel(graph, (0, 1), 7)
            a, b, e = graph.degrees[0], graph.degrees[1], int((0, 1) in graph.edges)
            for (s, t), cells in K.items():
                if s + t + 1 > 7:
                    continue
                expected = Counter()
                for v in range(2, graph.n):
                    A_s, A_t = int((0, v) in graph.edges), int((1, v) in graph.edges)
                    expected[a * s * s + b * t * t - 2 * e * s * t + graph.degrees[v] - 2 * s * A_s - 2 * t * A_t] += 1
                self.assertEqual({en: c for (v, en), c in cells.items() if v == 1}, dict(expected))

    def test_realizable_separation_bounds(self):
        first = lambda kappa, mode: next(R for R in range(60) if interface_status(R, kappa, mode)["top_defect"])
        self.assertEqual((first(2, True), first(2, "slice"), first(2, "balanced")), (26, 27, 38))
        self.assertEqual((first(1, True), first(1, "slice"), first(1, "balanced")), (8, 9, 11))
        (v,) = top_degree_kernel(25, 2)
        self.assertEqual(top_degree_kernel(26, 2, "slice"), [])
        self.assertEqual(top_degree_kernel(27, 2, "slice"), [v])
        self.assertEqual(interface_status(27, 2, "slice")["invisible_dimension"], 1)
        with self.assertRaises(ValueError):
            interface_status(5, 1, "unknown")


class UnequalDegreeInterpolationTests(unittest.TestCase):
    def test_extreme_coefficients_are_units(self):
        for j, d, ell in [(1, 1, 0), (2, 1, 0), (2, 3, 2), (3, 2, 1)]:
            D = boundary_determinant(j, d, ell)
            self.assertEqual({abs(D[min(D)]), abs(D[max(D)])}, {1})

    def test_injective_at_rational_q(self):
        for j in range(1, 4):
            for d in (1, 2):
                cols, rank = interpolation_rank(j, d, 0, Fraction(1, 2))
                self.assertEqual(rank, cols)

    def test_exceptional_factor(self):
        # D_{3,1,0}(z) = z^-43 (z-1)^11 H(z), deg H = 68, H(1) = 3870720, H(0) = lead H = -1.
        D = boundary_determinant(3, 1, 0)
        self.assertEqual(min(D), -43)
        P = [D.get(e, 0) for e in range(min(D), max(D) + 1)]
        for _ in range(11):
            out, r = [0] * (len(P) - 1), 0
            for i in range(len(P) - 1, 0, -1):
                r += P[i]
                out[i - 1] = r
            self.assertEqual(P[0] + r, 0)
            P = out
        self.assertEqual((len(P) - 1, sum(P), P[0], P[-1]), (68, 3870720, -1, -1))

    def test_interpolated_bounds(self):
        first = lambda kappa: next(R for R in range(60) if interface_status(R, kappa, "interpolated")["top_defect"])
        self.assertEqual((first(2), first(1)), (38, 11))


if __name__ == "__main__":
    unittest.main()
