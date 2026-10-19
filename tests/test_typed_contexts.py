"""Typed boundary grammar against actual assembled graphs (NX13-B, NX13-C graph side).

The oracle is weak-composition enumeration on the assembled graph
(``kernel_by_enumeration`` / ``local_coefficients``), not the matrices.
"""
import unittest
from collections import Counter
from dataclasses import replace
from fractions import Fraction as F

from singularity.charges import charge_interface, forget_terminal, kernel_from_charges
from singularity.graph import Graph
from singularity.heights import weak_compositions
from singularity.separator_compiler import introduce_terminal
from singularity.terminal_moves import OrderedContextAttachment
from singularity.typed_contexts import CLOSED, ONE, TWO, TWO_ADJ, BoundaryGrammar
from singularity.typed_observability import (
    TypedOperatorSystem, minimum_typed_distinction, typed_apply_word, typed_closure, typed_experiment,
    verify_typed_certificate)

Q = F(2, 3)
PATH = Graph(3, ((0, 1), (1, 2)))
P4 = Graph(4, ((0, 1), (1, 2), (2, 3)))
TRIANGLE = Graph(3, ((0, 1), (1, 2), (0, 2)))
BASES = [(PATH, ()), (Graph(1), ()), (PATH, (1,)), (PATH, (0,)), (Graph(1), (0,)),
         (PATH, (0, 2)), (PATH, (2, 0)), (Graph(2), (0, 1)), (P4, (0, 2)),
         (PATH, (0, 1)), (PATH, (1, 0)), (Graph(2, ((0, 1),)), (0, 1)), (TRIANGLE, (0, 1))]


def legal_words(system, start, length):
    out, frontier = [()], [((), start)]
    for _ in range(length):
        frontier = [(w + (a.identifier,), a.target) for w, t in frontier for a in system.actions if a.source == t]
        out += [w for w, _ in frontier]
    return out


def mat_vec(m, v):
    return tuple(sum((a * b for a, b in zip(r, v)), F(0)) for r in m)


class AdapterAgainstEnumerationTests(unittest.TestCase):
    def check(self, grammar, bases, length):
        s = grammar.system
        total = 0
        for graph, terminals in bases:
            ty, state = grammar.compile_state(graph, terminals)
            self.assertEqual((ty, state), grammar.direct_state(graph, terminals))
            for word in legal_words(s, ty, length):
                end, image = typed_apply_word(s, ty, state, word)
                assembled, new_terminals = grammar.assemble(graph, terminals, word)
                self.assertEqual(grammar.direct_state(assembled, new_terminals), (end, image),
                                 (graph, terminals, word))
                self.assertEqual(grammar.observe(ty, state, word),
                                 grammar.direct_observations(graph, terminals, word))
                total += 1
        return total

    def test_every_short_legal_word_at_budget_two(self):
        self.assertEqual(self.check(BoundaryGrammar(2, Q), BASES, 3), 4087)

    def test_budget_three_and_another_parameter(self):
        self.assertGreater(self.check(BoundaryGrammar(3, F(1, 2)), BASES[2:11:2], 2), 100)

    def test_matrices_never_reach_above_the_budget(self):
        """Closure of the truncated grammar: output volume v reads inputs of volume <= v only."""
        g = BoundaryGrammar(3, Q)
        for a in g.system.actions:
            src, tgt = g.coordinates[a.source], g.coordinates[a.target]
            for i, row in enumerate(a.matrix):
                for j, x in enumerate(row):
                    if x:
                        self.assertLessEqual(src[j][1], tgt[i][1], a.identifier)


class NoncommutationTests(unittest.TestCase):
    def setUp(self):
        self.g = BoundaryGrammar(2, Q)

    def differ(self, graph, terminals, w1, w2):
        ty, state = self.g.compile_state(graph, terminals)
        self.assertNotEqual(self.g.observe(ty, state, w1), self.g.observe(ty, state, w2))
        self.assertNotEqual(self.g.direct_observations(graph, terminals, w1),
                            self.g.direct_observations(graph, terminals, w2))

    def test_noncommuting_pairs(self):
        self.differ(PATH, (0, 2), ("extend_a", "shared"), ("shared", "extend_a"))
        self.differ(P4, (0, 2), ("swap", "leaf_a"), ("leaf_a", "swap"))
        # P3 endpoints are automorphic, so this word pair is equal on that base
        # even though the matrices do not commute: readings depend on the base.
        ty, state = self.g.compile_state(PATH, (0, 2))
        self.assertEqual(self.g.observe(ty, state, ("swap", "leaf_a")), self.g.observe(ty, state, ("leaf_a", "swap")))
        s = self.g.system
        sw, lf = s.action("swap").matrix, s.action("leaf_a").matrix
        self.assertNotEqual(tuple(mat_vec(sw, mat_vec(lf, col)) for col in zip(*[[F(i == j) for j in range(10)] for i in range(10)])),
                            tuple(mat_vec(lf, mat_vec(sw, col)) for col in zip(*[[F(i == j) for j in range(10)] for i in range(10)])))
        self.differ(PATH, (0, 2), ("join", "extend_a@adj"), ("extend_a", "join"))
        self.differ(PATH, (1,), ("intro", "forget_a"), ("pendant", "intro", "forget_a"))
        self.differ(PATH, (0, 1), ("forget_a@adj", "pendant"), ("forget_b@adj", "pendant"))


class DuplicateEdgeTests(unittest.TestCase):
    def test_join_twice_is_ill_typed_and_matrices_would_build_a_multigraph(self):
        g = BoundaryGrammar(2, Q)
        s = g.system
        with self.assertRaises(ValueError):
            s.path(("join", "join"), TWO)
        with self.assertRaises(ValueError):
            g.assemble(PATH, (0, 2), ("join", "join"))
        with self.assertRaises(ValueError):
            g.assemble(PATH, (0, 1), ("join",))           # start type is two_adj
        with self.assertRaises(ValueError):
            typed_experiment(s, "L1@two_adj", ("join", "join"))
        with self.assertRaises(ValueError):
            Graph(3, PATH.edges + ((0, 1),))
        # Untyped algebra would happily square the join matrix: that is the
        # doubled-edge multigraph population, not the simple graph's.
        join = s.action("join").matrix
        _, state = g.compile_state(PATH, (0, 2))
        squared = mat_vec(join, mat_vec(join, state))
        simple = g.direct_state(Graph(3, PATH.edges + ((0, 2),)), (0, 2))[1]
        self.assertNotEqual(squared, simple)
        # independent multigraph enumeration with the edge 02 counted twice
        multi = []
        for (s_, t), v in g.coordinates[TWO]:
            total = F(0)
            for a in weak_compositions(v, 3):
                if (a[0], a[2]) == (s_, t):
                    energy = (a[0] - a[1]) ** 2 + (a[1] - a[2]) ** 2 + 2 * (a[0] - a[2]) ** 2
                    total += Q ** energy
            multi.append(total)
        self.assertEqual(squared, tuple(multi))

    def test_cut_then_join_returns(self):
        g = BoundaryGrammar(2, Q)
        _, state = g.compile_state(TRIANGLE, (0, 1))
        self.assertEqual(typed_apply_word(g.system, TWO_ADJ, state, ("cut", "join")), (TWO_ADJ, state))
        self.assertEqual(g.assemble(TRIANGLE, (0, 1), ("cut", "join"))[0], TRIANGLE)


class ExistingMachineryCrossChecks(unittest.TestCase):
    """The fixed-q forget/introduce matrices agree with the charge-interface operations."""

    def evaluate(self, g, ty, kernel):
        return tuple(sum((c * Q ** e for (j, e), c in kernel.get(b, {}).items() if j == v - sum(b)), F(0))
                     for b, v in g.coordinates[ty])

    def test_forget_and_introduce(self):
        g = BoundaryGrammar(2, Q)
        for graph, terminals in ((P4, (0, 2)), (PATH, (0, 1)), (PATH, (2, 0))):
            ty, state = g.compile_state(graph, terminals)
            for k, op in ((0, "forget_a"), (1, "forget_b")):
                ident = op if ty == TWO else op + "@adj"
                interface = forget_terminal(charge_interface(graph, terminals, 2), terminals[k])
                self.assertEqual(typed_apply_word(g.system, ty, state, (ident,))[1],
                                 self.evaluate(g, ONE, kernel_from_charges(interface, 2)))
        for graph, terminal in ((PATH, 0), (PATH, 1), (P4, 1)):
            ty, state = g.compile_state(graph, (terminal,))
            for op, neighbours, target in (("intro", (), TWO), ("intro_adj", (terminal,), TWO_ADJ)):
                interface = introduce_terminal(charge_interface(graph, (terminal,), 2), graph.n, neighbours)
                self.assertEqual(typed_apply_word(g.system, ONE, state, (op,)),
                                 (target, self.evaluate(g, target, kernel_from_charges(interface, 2))))


class GraphCertificateTests(unittest.TestCase):
    def test_closure_certificate_and_sublanguage(self):
        g = BoundaryGrammar(2, Q)
        c = typed_closure(g.system)
        self.assertTrue(verify_typed_certificate(g.system, c))
        self.assertEqual(c.ranks, {CLOSED: 3, ONE: 6, TWO: 10, TWO_ADJ: 10})
        # A symmetric sublanguage cannot see terminal order at type two.
        keep = {"shared", "shared@adj", "join", "cut", "forget_a", "forget_a@adj", "close", "open"}
        sub = TypedOperatorSystem(g.system.types, [a for a in g.system.actions if a.identifier in keep],
                                  g.system.observations)
        cs = typed_closure(sub)
        self.assertTrue(verify_typed_certificate(sub, cs))
        self.assertLess(cs.ranks[TWO], 10)

    def test_chronology_tampering_on_a_graph_witness(self):
        g = BoundaryGrammar(2, Q)
        c = typed_closure(g.system)
        for bi, block in enumerate(c.blocks):
            for k, e in enumerate(block.basis):
                rev = tuple(reversed(e.word))
                if rev == e.word:
                    continue
                try:
                    other = typed_experiment(g.system, e.observation, rev, e.start_type)
                except ValueError:
                    continue
                if other.row == e.row:
                    continue
                basis = list(block.basis)
                basis[k] = replace(e, word=rev)
                blocks = list(c.blocks)
                blocks[bi] = replace(block, basis=tuple(basis))
                self.assertFalse(verify_typed_certificate(g.system, replace(c, blocks=tuple(blocks))))
                return
        self.fail("no graph witness with a legal, different reversal")

    def test_cheapest_witness_reads_differently_on_actual_graphs(self):
        g = BoundaryGrammar(2, Q)
        c = typed_closure(g.system)
        for (g1, t1), (g2, t2) in (((P4, (0, 2)), (P4, (2, 0))), ((PATH, (0, 1)), (PATH, (1, 0))),
                                   ((PATH, (0,)), (PATH, (1,)))):
            ty, x1 = g.compile_state(g1, t1)
            _, x2 = g.compile_state(g2, t2)
            w = minimum_typed_distinction(g.system, ty, tuple(a - b for a, b in zip(x1, x2)), c)
            self.assertIsNotNone(w)
            v = int(w.observation[1:w.observation.index("@")])
            self.assertNotEqual(g.direct_observations(g1, t1, w.word)[v], g.direct_observations(g2, t2, w.word)[v])
        _, x1 = g.compile_state(PATH, (0, 2))
        _, x2 = g.compile_state(PATH, (2, 0))  # automorphic placements
        self.assertIsNone(minimum_typed_distinction(g.system, TWO, tuple(a - b for a, b in zip(x1, x2)), c))


class ValidationTests(unittest.TestCase):
    def test_inputs(self):
        with self.assertRaises(TypeError):
            BoundaryGrammar(2, 0.5)
        with self.assertRaises(TypeError):
            BoundaryGrammar(True, Q)
        with self.assertRaises(ValueError):
            BoundaryGrammar(2, 1)
        with self.assertRaises(TypeError):
            BoundaryGrammar(2, Q, contexts=("leaf",))
        with self.assertRaises(ValueError):
            BoundaryGrammar(2, Q, costs={"teleport": 1})
        with self.assertRaises(ValueError):
            BoundaryGrammar(2, Q, contexts=(OrderedContextAttachment("swap", Graph(3, ((0, 2),))),))
        g = BoundaryGrammar(1, Q)
        with self.assertRaises(ValueError):
            g.type_of(P4, (0, 1, 2))
        with self.assertRaises(TypeError):
            g.compile_state("graph", ())
        with self.assertRaises(ValueError):
            g.assemble(PATH, (0,), ("join",))


if __name__ == "__main__":
    unittest.main()
