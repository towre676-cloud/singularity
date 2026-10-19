"""Noncommuting terminal moves on ordered states, against direct enumeration."""
import unittest
from fractions import Fraction as F
from itertools import product

from singularity.graph import Graph
from singularity.graph_experiments import BoundaryExperimentSystem
from singularity.observability import (minimum_distinguishing_experiment, observable_closure,
                                       verify_certificate)
from singularity.terminal_moves import EXTEND_A, OrderedMoveSystem

HALF = F(1, 2)
PATH = Graph(3, ((0, 1), (1, 2)))
BASES = [(PATH, (0, 2)), (PATH, (0, 1)), (PATH, (1, 0)), (Graph(3, ((0, 2),)), (0, 1)),
         (Graph(2, ((0, 1),)), (0, 1)), (Graph(4, ((0, 2), (2, 3), (3, 1))), (0, 1))]


def mul(a, b):
    n = len(a)
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(n)) for j in range(n)) for i in range(n))


class OrderedMoveTests(unittest.TestCase):
    def test_all_short_words_match_enumeration(self):
        for R in (2, 3):
            system = OrderedMoveSystem(R, HALF)
            words = [w for m in range(4) for w in product(range(len(system.moves)), repeat=m)]
            self.assertEqual(len(words), 85)
            for graph, terminals in BASES:
                state = system.compile_graph(graph, terminals)
                for word in words:
                    self.assertEqual(system.observe(state, word),
                                     system.direct_observations(graph, terminals, word), (graph, terminals, word))

    def test_assembled_graph_semantics(self):
        system = OrderedMoveSystem(2, HALF)
        graph, terminals = system.assemble(PATH, (0, 2), (2,))  # extend terminal a
        self.assertEqual((graph.edges, terminals), (((0, 1), (0, 3), (1, 2)), (3, 2)))
        graph, terminals = system.assemble(PATH, (0, 2), (2, 1))  # then a shared neighbour
        self.assertIn((3, 4), graph.edges)
        self.assertIn((2, 4), graph.edges)

    def test_extension_does_not_commute_with_the_shared_neighbour(self):
        system = OrderedMoveSystem(3, HALF)
        shared, extend_a = system.operators[1], system.operators[2]
        self.assertNotEqual(mul(extend_a, shared), mul(shared, extend_a))
        state = system.compile_graph(PATH, (0, 2))
        self.assertNotEqual(system.observe(state, (1, 2)), system.observe(state, (2, 1)))
        # The two orders give non-isomorphic graphs with different readings.
        self.assertNotEqual(system.direct_observations(PATH, (0, 2), (1, 2)),
                            system.direct_observations(PATH, (0, 2), (2, 1)))

    def test_ordered_closure_and_a_symmetric_blind_pair(self):
        # path(0,1) and path(1,2) have equal symmetric states (the path
        # automorphism swaps them up to terminal order); one terminal move
        # separates their ordered states.
        R = 2
        symmetric = BoundaryExperimentSystem(R, HALF)
        self.assertEqual(symmetric.compile_graph(PATH, (0, 1)), symmetric.compile_graph(PATH, (1, 2)))
        system = OrderedMoveSystem(R, HALF)
        operators = system.operator_system(attachment_costs=(2, 1, 1, 1))
        cert = observable_closure(operators)
        self.assertTrue(verify_certificate(operators, cert))
        self.assertEqual(cert.rank, system.dimension)
        d = tuple(a - b for a, b in zip(system.compile_graph(PATH, (0, 1)), system.compile_graph(PATH, (1, 2))))
        witness = minimum_distinguishing_experiment(operators, d, cert)
        self.assertEqual(witness.cost, 1)
        self.assertIn(system.moves[witness.word[0]], (EXTEND_A, "extend_b"))
        reading = [system.direct_observations(PATH, t, witness.word)[witness.observation] for t in ((0, 1), (1, 2))]
        self.assertNotEqual(reading[0], reading[1])

    def test_validation(self):
        with self.assertRaises(TypeError):
            OrderedMoveSystem(2, 0.5)
        with self.assertRaises(TypeError):
            OrderedMoveSystem(2, HALF, moves=("rotate",))
        system = OrderedMoveSystem(1, HALF)
        with self.assertRaises(ValueError):
            system.apply_word(system.compile_graph(PATH, (0, 2)), (9,))


if __name__ == "__main__":
    unittest.main()
