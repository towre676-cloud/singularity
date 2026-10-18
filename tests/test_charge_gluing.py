"""Charge composition checked against actual graphs and height enumeration."""

import copy
import itertools
import unittest

from singularity.charges import (charge_chart, charge_interface, forget_terminal,
                                 interface_sizes, kernel_from_charges, parallel_interfaces)
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.terminals import glue_graphs, kernel_by_enumeration


def graphs_on(n):
    edges = list(itertools.combinations(range(n), 2))
    for mask in range(1 << len(edges)):
        yield Graph(n, [e for i, e in enumerate(edges) if mask & (1 << i)])


class ChargeGluingTests(unittest.TestCase):
    def test_parallel_matches_every_three_vertex_pair(self):
        # Labels are deliberately out of order.  Interior vertices in the
        # second graph become independent copies under actual graph gluing.
        terminals, R = (2, 0), 4
        checked = 0
        for first in graphs_on(3):
            for second in graphs_on(3):
                a = charge_interface(first, terminals, R)
                b = charge_interface(second, terminals, R)
                if set(a["terminal_edges"]) & set(b["terminal_edges"]):
                    with self.assertRaises(ValueError):
                        parallel_interfaces(a, b)
                    continue
                graph, _ = glue_graphs(first, terminals, second, terminals)
                composed = parallel_interfaces(a, b)
                self.assertEqual(composed, charge_interface(graph, terminals, R))
                self.assertEqual(kernel_from_charges(composed, R),
                                 kernel_by_enumeration(graph, terminals, R))
                checked += 1
        self.assertEqual(checked, 48)

    def test_forgetting_every_boundary_position_matches_actual_graphs(self):
        terminals, R = (3, 1, 0), 4
        for graph in graphs_on(4):
            original = charge_interface(graph, terminals, R)
            for label in terminals:
                remaining = tuple(v for v in terminals if v != label)
                result = forget_terminal(original, label)
                self.assertEqual(result, charge_interface(graph, remaining, R))
                self.assertEqual(kernel_from_charges(result, R),
                                 kernel_by_enumeration(graph, remaining, R))

    def test_forgetting_last_terminal_closes_the_series(self):
        for graph in graphs_on(4):
            interface = charge_interface(graph, (2,), 4)
            closed = forget_terminal(interface, 2)
            self.assertEqual(closed["terminals"], ())
            self.assertEqual([closed["charges"].get((j, ()), {}) for j in range(5)],
                             local_coefficients(graph, 4))
            self.assertTrue(all(energy >= 0 for row in closed["charges"].values() for energy in row))

    def test_boundary_only_blocks_and_remaining_terminal_edges(self):
        first = Graph(3, [(0, 1)])
        second = Graph(3, [(1, 2), (0, 2)])
        terminals, R = (2, 0, 1), 5
        combined = parallel_interfaces(charge_interface(first, terminals, R),
                                       charge_interface(second, terminals, R))
        triangle = Graph(3, [(0, 1), (1, 2), (0, 2)])
        self.assertEqual(combined, charge_interface(triangle, terminals, R))
        # Both inputs have only the zero-volume charge, despite being complete
        # through R.  The declared bound is essential when a terminal moves in.
        self.assertEqual(len(combined["charges"]), 1)
        reduced = forget_terminal(combined, 0)
        self.assertEqual(reduced, charge_interface(triangle, (2, 1), R))
        self.assertEqual(reduced["terminal_edges"], ((0, 1),))

    def test_parallel_associativity_and_forgetting_order(self):
        terminals, R = (2, 0), 4
        graphs = [Graph(3, [(0, 2), (1, 2)]), Graph(3, [(0, 1)]),
                  Graph(3, [(0, 1), (1, 2)])]
        a, b, c = [charge_interface(g, terminals, R) for g in graphs]
        left = parallel_interfaces(parallel_interfaces(a, b), c)
        right = parallel_interfaces(a, parallel_interfaces(b, c))
        self.assertEqual(left, right)
        graph, _ = glue_graphs(graphs[0], terminals, graphs[1], terminals)
        graph, _ = glue_graphs(graph, terminals, graphs[2], terminals)
        self.assertEqual(left, charge_interface(graph, terminals, R))
        closed1 = forget_terminal(forget_terminal(left, 2), 0)
        closed2 = forget_terminal(forget_terminal(left, 0), 2)
        self.assertEqual(closed1, closed2)
        self.assertEqual([closed1["charges"][j, ()] for j in range(R + 1)],
                         local_coefficients(graph, R))

    def test_closed_parallel_is_disjoint_union(self):
        first = Graph(2, [(0, 1)])
        second = Graph(3, [(0, 1), (1, 2)])
        a = forget_terminal(charge_interface(first, (0,), 4), 0)
        b = forget_terminal(charge_interface(second, (1,), 4), 1)
        combined = parallel_interfaces(a, b)
        union = Graph(5, [(0, 1), (2, 3), (3, 4)])
        self.assertEqual([combined["charges"][j, ()] for j in range(5)],
                         local_coefficients(union, 4))

    def test_depth_metadata_prevents_silent_missing_coefficients(self):
        graph = Graph(3, [(0, 2), (1, 2)])
        small, large = charge_interface(graph, (0, 1), 1), charge_interface(graph, (0, 1), 4)
        self.assertEqual(parallel_interfaces(small, large)["max_volume"], 1)
        self.assertEqual(forget_terminal(large, 0, 2), charge_interface(graph, (1,), 2))
        for operation in (lambda: parallel_interfaces(small, large, 2),
                          lambda: forget_terminal(small, 0, 2),
                          lambda: kernel_from_charges(small, 2),
                          lambda: charge_chart(small, 2),
                          lambda: interface_sizes(small, 2)):
            with self.assertRaises(ValueError):
                operation()
        legacy = copy.deepcopy(large)
        del legacy["max_volume"]
        for operation in (lambda: parallel_interfaces(legacy, large),
                          lambda: forget_terminal(legacy, 0),
                          lambda: kernel_from_charges(legacy, 2)):
            with self.assertRaisesRegex(ValueError, "completeness metadata"):
                operation()

    def test_invalid_labels_and_inputs_are_unchanged(self):
        graph = Graph(4, [(0, 2), (1, 2), (2, 3), (0, 1)])
        original = charge_interface(graph, (1, 0), 3)
        saved = copy.deepcopy(original)
        forget_terminal(original, 1)
        self.assertEqual(original, saved)
        other = charge_interface(Graph(3, [(0, 2)]), (1, 0), 3)
        other_saved = copy.deepcopy(other)
        parallel_interfaces(original, other)
        self.assertEqual((original, other), (saved, other_saved))
        with self.assertRaises(ValueError):
            forget_terminal(original, 3)
        with self.assertRaises(TypeError):
            forget_terminal(original, True)
        with self.assertRaises(ValueError):
            parallel_interfaces(original, charge_interface(graph, (0, 1), 3))
        with self.assertRaises(ValueError):
            parallel_interfaces(original, original)


if __name__ == "__main__":
    unittest.main()
