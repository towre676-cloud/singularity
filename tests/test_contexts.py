import unittest
from collections import Counter
from fractions import Fraction

from singularity.contexts import (orbit_groups, recover_symmetrized_kernel, symmetric_context,
                                  symmetric_interface_rank, symmetric_probe_set, symmetrize, top_degree_defect)
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


if __name__ == "__main__":
    unittest.main()
