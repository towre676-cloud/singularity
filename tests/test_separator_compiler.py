"""OE11 separator compiler, checked against independent direct enumeration.

Oracles: ``heights.local_coefficients`` and ``terminals.kernel_by_enumeration``
enumerate weak compositions of the actual graph; ``charges.charge_interface``
enumerates interior compositions.  Cross-checks use the bag-message engine
(``decomposition``), ``terminals.terminal_kernel`` and the connected-support
compiler (``locality.pinned_series`` with lam = 0, which is L_G).
"""

import copy
import itertools
import random
import unittest

from singularity.charges import charge_interface, forget_terminal, kernel_from_charges, parallel_interfaces
from singularity.decomposition import (TreeDecomposition, decomposition_histogram, elimination_decomposition,
                                       forest_decomposition)
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.locality import pinned_series
from singularity.separator_compiler import (apply_step_operator, boundary_block, build_step_operator, cell_bound,
                                            closed_coefficients, compile_decomposition, compile_graph,
                                            compile_interface, count_bit_bound, elimination_schedule,
                                            empty_interface, introduce_terminal, order_width, periodic_compile,
                                            periodic_plan, run_schedule, strip_graph)
from singularity.terminals import kernel_by_enumeration, terminal_kernel
from singularity.transfer import histogram_coefficients


def graphs_on(n):
    edges = list(itertools.combinations(range(n), 2))
    for mask in range(1 << len(edges)):
        yield Graph(n, [e for i, e in enumerate(edges) if mask >> i & 1])


def induced(graph, vertices):
    """G[vertices] relabelled 0..k-1 in the listed order, with the label map."""
    index = {v: i for i, v in enumerate(vertices)}
    return Graph(len(vertices), [(index[u], index[v]) for u, v in graph.edges if u in index and v in index]), index


def without_labels(interface):
    return {k: v for k, v in interface.items() if k != "terminals"}


class IntroduceTests(unittest.TestCase):
    def test_introduce_matches_actual_graphs_every_position_and_neighbour_set(self):
        # G on 4 vertices with terminals T; add vertex 4 joined to S subset of T.
        R, checked = 3, 0
        for terminals in ((3, 1), (2, 0, 1)):
            for graph in graphs_on(4):
                base = charge_interface(graph, terminals, R)
                for size in range(len(terminals) + 1):
                    for S in itertools.combinations(terminals, size):
                        bigger = Graph(5, list(graph.edges) + [(s, 4) for s in S])
                        for p in range(len(terminals) + 1):
                            new_terminals = terminals[:p] + (4,) + terminals[p:]
                            result = introduce_terminal(base, 4, S, position=p)
                            self.assertEqual(result, charge_interface(bigger, new_terminals, R))
                            checked += 1
                        if graph.edges and size == len(terminals):  # full kernels on a subset
                            self.assertEqual(kernel_from_charges(result, R),
                                             kernel_by_enumeration(bigger, new_terminals, R))
        self.assertEqual(checked, 64 * (4 * 3 + 8 * 4))

    def test_boundary_block_is_the_interior_free_graph(self):
        triangle_tail = Graph(4, [(0, 1), (1, 2), (0, 2), (2, 3)])
        block = boundary_block((2, 0, 3, 1), triangle_tail.edges, 4)
        self.assertEqual(block, charge_interface(triangle_tail, (2, 0, 3, 1), 4))
        self.assertEqual(kernel_from_charges(block, 4), terminal_kernel(triangle_tail, (2, 0, 3, 1), 4))

    def test_inputs_are_not_mutated(self):
        interface = charge_interface(Graph(3, [(0, 2), (1, 2)]), (0, 1), 3)
        saved = copy.deepcopy(interface)
        introduce_terminal(interface, 5, (1,), position=0)
        self.assertEqual(interface, saved)


class ScheduleInvariantTests(unittest.TestCase):
    def check_invariant(self, graph, order, R):
        """After every operation the interface is the charge interface of (G[introduced], boundary)."""
        state = {"interface": empty_interface(R), "introduced": [], "boundary": []}
        for op in elimination_schedule(graph, order):
            if op[0] == "introduce":
                # Edges to forgotten vertices never occur: their neighbours were all introduced.
                self.assertEqual(set(op[2]), set(graph.neighbors[op[1]]) & set(state["introduced"]))
                state["introduced"].append(op[1])
                state["boundary"].append(op[1])
            else:
                state["boundary"].remove(op[1])
            state["interface"] = run_schedule(state["interface"], [op])
            self.assertEqual(tuple(state["interface"]["terminals"]), tuple(state["boundary"]))
            if state["boundary"]:
                sub, index = induced(graph, state["introduced"])
                mapped = tuple(index[v] for v in state["boundary"])
                self.assertEqual(without_labels(state["interface"]), without_labels(charge_interface(sub, mapped, R)))
                self.assertEqual(kernel_from_charges(state["interface"], R), kernel_by_enumeration(sub, mapped, R))
        self.assertEqual(state["interface"]["terminals"], ())

    def test_every_intermediate_interface_on_four_vertex_graphs(self):
        for graph in graphs_on(4):
            for order in ((0, 1, 2, 3), (2, 0, 3, 1)):
                self.check_invariant(graph, order, 3)

    def test_sampled_five_vertex_graphs(self):
        rng = random.Random(11)
        graphs = list(graphs_on(5))
        for graph in rng.sample(graphs, 40):
            order = list(range(5))
            rng.shuffle(order)
            self.check_invariant(graph, order, 3)


class JoinTests(unittest.TestCase):
    def test_join_of_compiled_blocks_matches_glued_graph(self):
        # Blocks on boundary (0, 1, 2) built only by introduce/forget, then joined.
        R = 3
        first = Graph(5, [(0, 3), (3, 4), (4, 1), (1, 2)])           # interior 3, 4
        second = Graph(5, [(2, 3), (0, 3), (3, 4), (0, 1)])          # interior 3, 4
        def block(graph):
            interface = run_schedule(empty_interface(R), [("introduce", 0, ()), ("introduce", 1, ()), ("introduce", 2, ())])
            for u, v in graph.edges:  # boundary edges are joined in as interior-free blocks
                if u < 3 and v < 3:
                    interface = parallel_interfaces(interface, boundary_block((0, 1, 2), [(u, v)], R))
            for v in (3, 4):
                interface = introduce_terminal(interface, v, [u for u in graph.neighbors[v] if u in interface["terminals"]])
            return forget_terminal(forget_terminal(interface, 3), 4)
        a, b = block(first), block(second)
        joined = parallel_interfaces(a, b)
        glued = Graph(7, list(first.edges) + [(u if u < 3 else u + 2, v if v < 3 else v + 2) for u, v in second.edges])
        self.assertEqual(joined, charge_interface(glued, (0, 1, 2), R))
        self.assertEqual(kernel_from_charges(joined, R), kernel_by_enumeration(glued, (0, 1, 2), R))
        closed = forget_terminal(forget_terminal(forget_terminal(joined, 1), 0), 2)
        self.assertEqual(closed_coefficients(closed), local_coefficients(glued, R))

    def test_explicit_join_decompositions(self):
        star = Graph(4, [(0, 1), (0, 2), (0, 3)])
        join = TreeDecomposition([[0], [0, 1], [0, 2], [0, 3]], [(0, 1), (0, 2), (0, 3)], root=0)
        stats = {}
        self.assertEqual(compile_decomposition(star, join, 4, stats), local_coefficients(star, 4))
        self.assertEqual(stats["joins"], 3)
        cycle = Graph(6, [(i, (i + 1) % 6) for i in range(6)])
        # Two halves of C_6 joined on the separator {0, 3}.
        dec = TreeDecomposition([[0, 3], [0, 1, 3], [1, 2, 3], [0, 3, 5], [3, 4, 5]],
                                [(0, 1), (1, 2), (0, 3), (3, 4)], root=0)
        stats = {}
        self.assertEqual(compile_decomposition(cycle, dec, 4, stats), local_coefficients(cycle, 4))
        self.assertGreaterEqual(stats["joins"], 2)
        self.assertEqual(stats["width"], 3)

    def test_decompositions_with_branching_on_all_five_vertex_graphs(self):
        rng = random.Random(5)
        joins = 0
        for graph in graphs_on(5):
            order = list(range(5))
            rng.shuffle(order)
            stats = {}
            self.assertEqual(compile_decomposition(graph, elimination_decomposition(graph, order), 3, stats),
                             local_coefficients(graph, 3))
            joins += stats["joins"]
        self.assertGreater(joins, 0)


class CompileGraphTests(unittest.TestCase):
    def test_all_graphs_through_five_vertices_three_orders(self):
        rng = random.Random(2026)
        checked = 0
        for n in range(1, 6):
            for graph in graphs_on(n):
                expected = local_coefficients(graph, 3)
                shuffled = list(range(n))
                rng.shuffle(shuffled)
                for order in (range(n), range(n - 1, -1, -1), shuffled):
                    self.assertEqual(compile_graph(graph, order, 3), expected)
                    checked += 1
        self.assertEqual(checked, 3 * (1 + 2 + 8 + 64 + 1024))

    def test_every_order_of_selected_graphs(self):
        for graph in (Graph(5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 2)]), Graph(5, [(0, 1), (2, 3)])):
            expected = local_coefficients(graph, 4)
            for order in itertools.permutations(range(5)):
                self.assertEqual(compile_graph(graph, order, 4), expected)

    def test_disconnected_and_isolated(self):
        for graph in (Graph(1), Graph(4), Graph(6, [(0, 1), (3, 4)]), Graph(7, [(0, 6), (6, 3), (2, 5)])):
            for order in (range(graph.n), range(graph.n - 1, -1, -1)):
                self.assertEqual(compile_graph(graph, order, 4), local_coefficients(graph, 4))
        self.assertEqual(compile_graph(Graph(2), (1, 0), 0), [{0: 1}])

    def test_families_against_direct_enumeration(self):
        cases = [strip_graph(1, n) for n in range(1, 9)] + [strip_graph(1, n, cyclic=True) for n in range(3, 9)]
        cases += [strip_graph(2, n) for n in range(1, 5)] + [strip_graph(3, n) for n in range(1, 4)]
        for graph in cases:
            for R in range(5):
                self.assertEqual(compile_graph(graph, range(graph.n), R), local_coefficients(graph, R))

    def test_cross_checks_with_bag_messages_and_connected_support(self):
        for graph in (strip_graph(1, 12), strip_graph(1, 10, cyclic=True), strip_graph(2, 6), strip_graph(3, 4)):
            R = 4
            ours = compile_graph(graph, range(graph.n), R)
            order = list(range(graph.n))
            bags = histogram_coefficients(decomposition_histogram(graph, elimination_decomposition(graph, order), R, R), R)
            self.assertEqual(ours, bags)
            self.assertEqual(ours, pinned_series(graph, R, lam=0))
            self.assertEqual(compile_decomposition(graph, elimination_decomposition(graph, order), R), ours)
        tree = Graph(7, [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)])
        self.assertEqual(compile_decomposition(tree, forest_decomposition(tree), 4), local_coefficients(tree, 4))


class BoundTests(unittest.TestCase):
    def test_cell_charge_energy_and_bit_bounds_along_strips(self):
        for rows, cyclic in ((1, False), (1, True), (2, False), (3, False)):
            for n in (4, 12, 30):
                graph = strip_graph(rows, n, cyclic)
                for R in (3, 4):
                    stats = {}
                    compile_interface(graph, range(graph.n), R, stats)
                    D = max(graph.degrees)
                    self.assertEqual(stats["bound_violations"], 0)
                    self.assertLessEqual(stats["cells_at_widest"], stats["cell_bound_at_widest"])
                    self.assertLessEqual(stats["max_count_bits"], count_bit_bound(graph.n, R))
                    self.assertLessEqual(stats["max_charge"], R)
                    self.assertEqual(stats["min_energy"], 0)
                    self.assertLessEqual(stats["max_energy"], D * R * R)
                    self.assertEqual(stats["width"], order_width(graph, range(graph.n)))

    def test_width_is_one_plus_vertex_separation(self):
        rng = random.Random(3)
        for graph in rng.sample(list(graphs_on(5)), 60):
            order = list(range(5))
            rng.shuffle(order)
            separation = max(len({u for u in order[:t] if any(w in order[t:] for w in graph.neighbors[u])})
                             for t in range(5))
            self.assertEqual(order_width(graph, order), separation + 1)

    def test_bound_formulae(self):
        self.assertEqual(cell_bound(0, 0, 5), 1)
        self.assertEqual(cell_bound(1, 2, 2), 1 + 2 * 3 + 3 * 9)
        self.assertEqual(count_bit_bound(0, 4), 1)
        self.assertEqual(count_bit_bound(3, 2), 6 .bit_length())


class StepOperatorTests(unittest.TestCase):
    def test_periodic_operator_matches_direct_compilation(self):
        for rows, cyclic, anchors in ((1, False, ()), (1, True, (0,)), (2, False, ()), (3, False, ())):
            for n in (3, 5, 9, 20):
                graph = strip_graph(rows, n, cyclic)
                for R in (3, 4):
                    coefficients, info = periodic_compile(graph, range(graph.n), rows, R, anchors)
                    self.assertEqual(coefficients, compile_graph(graph, range(graph.n), R))
                    if n >= 9:
                        self.assertGreaterEqual(info["steps"], n - 4)
                    if n <= 5 and graph.n <= 10:
                        self.assertEqual(coefficients, local_coefficients(graph, R))

    def test_operator_rejects_nonstationary_or_mismatched_use(self):
        graph = strip_graph(1, 6)
        plan = periodic_plan(graph, range(6), 1)
        template = run_schedule(empty_interface(3), plan["prefix"])
        operator = build_step_operator(template, plan["segment"])
        early = run_schedule(empty_interface(3), [("introduce", 0, ())])  # terminal degree 0, not 1
        with self.assertRaises(ValueError):
            build_step_operator(early, [("introduce", 1, (0,)), ("forget", 0)])
        with self.assertRaises(ValueError):
            apply_step_operator(operator, early, (1,))
        with self.assertRaises(ValueError):
            apply_step_operator(operator, template, (7, 8))
        # Rows reachable from the zero charge: charge never exceeds interior volume.
        sparse = build_step_operator(template, plan["segment"], seeds=[(0, (0,))])
        self.assertTrue(all(Q[0] <= j <= 3 for j, Q in sparse["rows"]))
        foreign = dict(template, charges={(1, (2,)): {0: 1}})  # not a realizable key, so no row
        with self.assertRaisesRegex(ValueError, "no row"):
            apply_step_operator(sparse, foreign, plan["labels"][1])


class ContractTests(unittest.TestCase):
    def test_type_errors(self):
        graph = Graph(3, [(0, 1)])
        interface = charge_interface(graph, (0,), 2)
        for bad in (True, 2.0, "2"):
            with self.assertRaises(TypeError):
                compile_graph(graph, range(3), bad)
            with self.assertRaises(TypeError):
                introduce_terminal(interface, bad)
            with self.assertRaises(TypeError):
                compile_graph(graph, (0, 1, bad), 2)
            with self.assertRaises(TypeError):
                introduce_terminal(interface, 5, (bad,))
            with self.assertRaises(TypeError):
                introduce_terminal(interface, 5, (), position=bad)
            with self.assertRaises(TypeError):
                empty_interface(bad)
        with self.assertRaises(TypeError):
            compile_graph(graph, "012", 2)
        with self.assertRaises(TypeError):
            compile_graph("graph", range(3), 2)
        with self.assertRaises(TypeError):
            compile_decomposition(graph, {"bags": [[0, 1, 2]]}, 2)
        with self.assertRaises(TypeError):
            introduce_terminal("interface", 1)

    def test_value_errors(self):
        graph = Graph(3, [(0, 1)])
        interface = charge_interface(graph, (0,), 2)
        for call in (lambda: compile_graph(graph, (0, 1), 2),
                     lambda: compile_graph(graph, (0, 1, 1), 2),
                     lambda: compile_graph(graph, range(3), -1),
                     lambda: introduce_terminal(interface, 0),
                     lambda: introduce_terminal(interface, 5, (2,)),
                     lambda: introduce_terminal(interface, 5, (0, 0)),
                     lambda: introduce_terminal(interface, 5, (), position=2),
                     lambda: introduce_terminal({"terminals": ()}, 5),
                     lambda: closed_coefficients(interface),
                     lambda: closed_coefficients(forget_terminal(interface, 0), 3),
                     lambda: boundary_block((0, 1), [(0, 2)], 2),
                     lambda: boundary_block((0, 1), [(0, 1), (1, 0)], 2),
                     lambda: boundary_block((0, 0), [], 2),
                     lambda: compile_decomposition(graph, TreeDecomposition([[0, 2], [1]], [(0, 1)]), 2),
                     lambda: strip_graph(1, 2, cyclic=True),
                     lambda: periodic_plan(graph, range(3), 2)):
            with self.assertRaises(ValueError):
                call()


if __name__ == "__main__":
    unittest.main()
