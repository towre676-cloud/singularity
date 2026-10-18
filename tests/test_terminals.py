"""SNG-F41/F42: terminal kernels, gluing and the Whitney twist."""

import random
import unittest

from singularity.families import first_discrepancy, pendant_cycle
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.polynomials import sub
from singularity.terminals import (
    antisymmetric_part, glue, glue_graphs, kernel_by_enumeration, terminal_kernel, twist_difference,
)


def path_block(m, k):
    """Path s=0 ... t=1 of length 2m, with a leaf at distance k from s."""
    path = [0] + list(range(2, 2 * m + 1)) + [1]
    edges = [(path[i], path[i + 1]) for i in range(2 * m)]
    edges.append((path[k], 2 * m + 1))
    return Graph(2 * m + 2, edges)


def twist_depth(kernel):
    a = antisymmetric_part(kernel)
    return min((s + t + 2 * min(v for v, _ in cells) for (s, t), cells in a.items()), default=None)


class KernelTests(unittest.TestCase):
    def test_kernels_match_enumeration(self):
        rng = random.Random(41)
        for _ in range(25):
            n = rng.randrange(2, 7)
            graph = Graph(n, [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < 0.45])
            terminals = tuple(rng.sample(range(n), rng.choice([1, 2, min(3, n)])))
            with self.subTest(graph=graph.to_dict(), terminals=terminals):
                self.assertEqual(terminal_kernel(graph, terminals, 5), kernel_by_enumeration(graph, terminals, 5))

    def test_gluing_and_twisting_reproduce_the_glued_graphs(self):
        first = Graph(5, [(0, 1), (1, 2), (2, 3), (1, 4)])
        second = Graph(4, [(0, 1), (1, 2), (2, 3), (0, 2)])
        bound = 6
        k1, k2 = terminal_kernel(first, (0, 3), bound), terminal_kernel(second, (0, 3), bound)
        glued, _ = glue_graphs(first, (0, 3), second, (0, 3))
        twisted, _ = glue_graphs(first, (0, 3), second, (3, 0))
        self.assertEqual(glue(k1, k2, bound), local_coefficients(glued, bound))
        self.assertEqual(glue(k1, k2, bound, permutation=(1, 0)), local_coefficients(twisted, bound))
        difference = [sub(a, b) for a, b in zip(local_coefficients(glued, bound), local_coefficients(twisted, bound))]
        self.assertEqual(difference, twist_difference(k1, k2, bound))

    def test_three_terminal_gluing(self):
        first = Graph(4, [(0, 3), (1, 3), (2, 3)])
        second = Graph(4, [(0, 1), (1, 2), (2, 3)])
        k1, k2 = terminal_kernel(first, (0, 1, 2), 5), terminal_kernel(second, (0, 1, 2), 5)
        glued, _ = glue_graphs(first, (0, 1, 2), second, (0, 1, 2))
        self.assertEqual(glue(k1, k2, 5), local_coefficients(glued, 5))

    def test_symmetric_block_makes_the_twist_invisible(self):
        symmetric = Graph(4, [(0, 2), (2, 3), (3, 1)])  # path s-a-b-t: swap automorphism
        other = Graph(5, [(0, 2), (2, 1), (2, 3), (3, 4)])
        bound = 6
        ks, ko = terminal_kernel(symmetric, (0, 1), bound), terminal_kernel(other, (0, 1), bound)
        self.assertEqual(antisymmetric_part(ks), {})
        self.assertEqual(twist_difference(ks, ko, bound), [{}] * (bound + 1))
        self.assertEqual(glue(ks, ko, bound), glue(ks, ko, bound, permutation=(1, 0)))

    def test_identical_blocks_depth_formula_and_pendant_cycles(self):
        for m, k in ((2, 1), (3, 1), (3, 2), (4, 2)):
            block = path_block(m, k)
            bound = 2 * k + 2
            kernel = terminal_kernel(block, (0, 1), bound)
            difference = twist_difference(kernel, kernel, bound)
            first = next(v for v, row in enumerate(difference) if row)
            with self.subTest(m=m, k=k):
                self.assertEqual(first, twist_depth(kernel))
                self.assertEqual(first, 2 * k + 1)
                self.assertEqual(difference[first], first_discrepancy(2 * k))
                # The straight and twisted gluings are the SNG-F36 pair G(2m, 2k), G(2m, 2m).
                glued, _ = glue_graphs(block, (0, 1), block, (0, 1))
                twisted, _ = glue_graphs(block, (0, 1), block, (1, 0))
                self.assertEqual(local_coefficients(glued, bound), local_coefficients(pendant_cycle(2 * m, 2 * k), bound))
                self.assertEqual(local_coefficients(twisted, bound), local_coefficients(pendant_cycle(2 * m, 2 * m), bound))

    def test_marked_gluing_recovers_global_span(self):
        from singularity.heights import marked_coefficients
        from singularity.terminals import marked_glue
        first = Graph(5, [(0, 1), (1, 2), (2, 3), (1, 4)])
        second = Graph(4, [(0, 1), (1, 2), (2, 3), (0, 2)])
        for terminals in ((0, 3), (3, 0)):
            glued, _ = glue_graphs(first, (0, 3), second, terminals)
            self.assertEqual(marked_glue(first, (0, 3), second, terminals, 6), marked_coefficients(glued, 6))
        # A disconnected first block keeps one global translation (SNG-F25).
        loose = Graph(4, [(0, 2), (1, 3)])
        glued, _ = glue_graphs(loose, (0, 1), second, (0, 3))
        self.assertEqual(marked_glue(loose, (0, 1), second, (0, 3), 5), marked_coefficients(glued, 5))
        box = terminal_kernel(first, (0, 3), 4, height=1)
        self.assertTrue(all(max(b) <= 1 for b in box))

    def test_invalid_terminals_and_shared_edges(self):
        graph = Graph(3, [(0, 1), (1, 2)])
        for terminals in ((), (0, 0), (0, 3), (True,)):
            with self.assertRaises((TypeError, ValueError)):
                terminal_kernel(graph, terminals, 2)
        with self.assertRaises(ValueError):
            glue_graphs(graph, (0, 1), Graph(2, [(0, 1)]), (0, 1))


if __name__ == "__main__":
    unittest.main()
