import unittest
from fractions import Fraction

from singularity.charges import (chart_observations, chart_transport, charge_chart, recover_from_chart, _at, apply, charge_interface, closure_operator, dominating_block, dominating_sequence,
                                 kernel_from_charges, pattern_dimension, recover_sequence, transport)
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.terminals import glue_graphs, terminal_kernel

Q0 = Fraction(1, 2)
PATH = Graph(3, [(0, 1), (1, 2)])
SHARED = Graph(3, [(0, 2), (1, 2)])
ASYMMETRIC = Graph(5, [(0, 2), (2, 3), (1, 3), (0, 4), (0, 1)])


class ChargeCompilerTests(unittest.TestCase):
    def test_charge_table_rebuilds_kernels(self):
        # SNG-F53(a): the kernel depends on the interior only through (j, Q, energy).
        cases = [(Graph(5, [(0, 2), (2, 3), (3, 1), (2, 4)]), (0, 1)),
                 (Graph(6, [(0, 2), (0, 3), (1, 3), (1, 4), (2, 5), (4, 5), (0, 1)]), (0, 1)),
                 (Graph(6, [(0, 3), (1, 3), (2, 4), (3, 4), (4, 5), (1, 2)]), (0, 1, 2))]
        for graph, terminals in cases:
            R = 5 if len(terminals) == 2 else 4
            self.assertEqual(kernel_from_charges(charge_interface(graph, terminals, R), R),
                             terminal_kernel(graph, terminals, R))

    def test_pattern_dimensions(self):
        dominating, _ = dominating_block(PATH)
        twins = Graph(6, [(0, 2), (1, 2), (0, 3), (1, 3), (2, 4), (3, 5), (4, 5)])
        general = Graph(6, [(0, 2), (0, 3), (1, 3), (1, 4), (2, 5), (4, 5)])
        dims = [pattern_dimension(charge_interface(g, (0, 1), 2)) for g in (dominating, twins, general)]
        self.assertEqual(dims, [0, 1, 2])
        self.assertEqual(len(charge_interface(twins, (0, 1), 6)["charges"]), sum(j + 1 for j in range(7)))

    def test_dominating_closed_form(self):
        # K(s,t) = q^(m(s^2+t^2)) sum_j A_j x^j q^(-2j(s+t)).
        R, m = 6, PATH.n
        G, T = dominating_block(PATH)
        A = dominating_sequence(PATH, R)
        for (s, t), cells in terminal_kernel(G, T, R).items():
            expected = {(j, e + m * (s * s + t * t) - 2 * j * (s + t)): c
                        for j in range(R + 1 - s - t) for e, c in A[j].items()}
            self.assertEqual(cells, expected)


class TransportTests(unittest.TestCase):
    def test_closure_is_triangular_and_matches_gluing(self):
        R = 5
        G, T = dominating_block(PATH)
        A = [_at(a, Q0) for a in dominating_sequence(PATH, R)]
        for C in (SHARED, ASYMMETRIC):
            Tc = closure_operator(C, (0, 1), PATH.n, R, Q0)
            self.assertTrue(all(Tc[v][v] == 1 and not any(Tc[v][v + 1:]) for v in range(R + 1)))
            glued, _ = glue_graphs(G, T, C, (0, 1))
            Z = [_at(row, Q0) for row in local_coefficients(glued, R)]
            self.assertEqual(apply(Tc, A), Z)
            self.assertEqual(recover_sequence(Z, Tc), A)

    def test_one_closure_predicts_every_other(self):
        # SNG-F54: Z_D = T_D T_C^(-1) Z_C, with an operator independent of the interior.
        R = 4
        Tc = closure_operator(SHARED, (0, 1), 3, R, Q0)
        Td = closure_operator(ASYMMETRIC, (0, 1), 3, R, Q0)
        U = transport(Td, Tc)
        for H in (PATH, Graph(3, []), Graph(3, [(0, 1), (1, 2), (0, 2)])):
            G, T = dominating_block(H)
            series = {}
            for name, C in (("C", SHARED), ("D", ASYMMETRIC)):
                glued, _ = glue_graphs(G, T, C, (0, 1))
                series[name] = [_at(row, Q0) for row in local_coefficients(glued, R)]
            self.assertEqual(apply(U, series["C"]), series["D"])

    def test_composition_law(self):
        R = 4
        Ts = [closure_operator(C, (0, 1), 2, R, Q0) for C in (SHARED, Graph(4, [(0, 2), (1, 3)]), ASYMMETRIC)]
        U10, U21, U20 = transport(Ts[1], Ts[0]), transport(Ts[2], Ts[1]), transport(Ts[2], Ts[0])
        self.assertEqual([[sum(U21[i][k] * U10[k][j] for k in range(R + 1)) for j in range(R + 1)] for i in range(R + 1)], U20)

    def test_k23_denominators(self):
        # A_j = sum_{|h|=j} 2^(-2 sum h_i^2): denominator exactly 2^(2 j^2), odd numerator.
        A = [_at(a, Q0) for a in dominating_sequence(Graph(3, []), 8)]
        for j, a in enumerate(A):
            self.assertEqual(a.denominator, 2 ** (2 * j * j))
            self.assertEqual(a.numerator % 2, 1)

    def test_rejects_bad_input(self):
        with self.assertRaises(TypeError):
            dominating_block("not a graph")
        with self.assertRaises(ValueError):
            charge_interface(PATH, (0, 0), 2)


class ChartTests(unittest.TestCase):
    def test_false_twin_chart(self):
        G = Graph(6, [(0, 2), (1, 2), (0, 3), (1, 3), (2, 4), (3, 5), (4, 5)])
        iface = charge_interface(G, (0, 1), 4)
        chart = charge_chart(iface, 4)
        self.assertEqual(len(chart["coordinates"]), pattern_dimension(iface))
        self.assertLessEqual(chart["budget"], 2 * 4)
        K = terminal_kernel(G, (0, 1), chart["budget"])
        truth = {key: _at(cells, Q0) for key, cells in iface["charges"].items()}
        self.assertEqual(recover_from_chart(iface, chart, chart_observations(K, chart, Q0), Q0), truth)

    def test_three_terminal_chart_and_transport(self):
        G = Graph(6, [(0, 3), (1, 3), (2, 4), (3, 4), (4, 5), (1, 2)])
        iface = charge_interface(G, (0, 1, 2), 3)
        first = charge_chart(iface, 3)
        second = charge_chart(iface, 3, (1, 2))
        K = terminal_kernel(G, (0, 1, 2), max(first["budget"], second["budget"]))
        truth = {key: _at(cells, Q0) for key, cells in iface["charges"].items()}
        self.assertEqual(recover_from_chart(iface, first, chart_observations(K, first, Q0), Q0), truth)
        o1, o2 = chart_observations(K, first, Q0), chart_observations(K, second, Q0)
        for j in first["states"]:
            U = chart_transport(iface, first, second, j, Q0)
            self.assertEqual([sum(u * v for u, v in zip(row, o1[j])) for row in U], o2[j])


if __name__ == "__main__":
    unittest.main()
