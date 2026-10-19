"""FR05 promised-class inverse tests with independent assignment populations."""

from collections import Counter
from fractions import Fraction
from itertools import combinations, product
import unittest

from singularity.denominator_recovery import recovery_volume
from singularity.graph import Graph
from singularity.threshold_reconstruction import (
    attach_universal, graph_from_creation_word, isolated_factor,
    reconstruct_threshold, remove_isolated, remove_universal,
)


def direct_prefix(graph, q, volume, shift=0):
    result = []
    for r in range(volume + 1):
        counts = Counter()
        for separators in combinations(range(r + graph.n - 1), graph.n - 1):
            stops = (-1,) + separators + (r + graph.n - 1,)
            h = tuple(stops[i + 1] - stops[i] - 1 for i in range(graph.n))
            energy = sum((h[u] - h[v]) ** 2 for u, v in graph.edges) + shift * sum(t * t for t in h)
            counts[energy] += 1
        result.append(sum((count * q ** energy for energy, count in counts.items()), Fraction()))
    return tuple(result)


class ThresholdReconstructionTests(unittest.TestCase):
    def test_every_creation_word_through_order_six(self):
        checks = 0
        for n in range(1, 7):
            for tail in product((0, 1), repeat=n - 1):
                word = (0,) + tail
                graph = graph_from_creation_word(word)
                for q in (Fraction(1, 2), Fraction(2, 3), Fraction(5, 6)):
                    volume = recovery_volume(n, q)
                    for shift in (0, 2):
                        actual = reconstruct_threshold(n, q, direct_prefix(graph, q, volume, shift), diagonal_shift=shift)
                        self.assertEqual(actual.creation_word, word)
                        self.assertEqual(actual.graph, graph)
                        checks += 1
        self.assertEqual(checks, 378)

    def test_universal_transform_against_direct_join(self):
        inner = graph_from_creation_word((0, 1, 0, 1))
        for m in (1, 2, 3):
            graph = graph_from_creation_word((0, 1, 0, 1) + (1,) * m)
            for q in (Fraction(1, 2), Fraction(5, 6)):
                for shift in (0, 2):
                    a = direct_prefix(graph, q, 4, shift)
                    b = direct_prefix(inner, q, 4, shift + m)
                    self.assertEqual(attach_universal(b, graph.n, m, q, shift), a)
                    self.assertEqual(remove_universal(a, graph.n, m, q, shift), b)

    def test_isolate_factor_and_division(self):
        q = Fraction(2, 3)
        inner = graph_from_creation_word((0, 1, 1))
        graph = graph_from_creation_word((0, 1, 1, 0, 0))
        for shift in (0, 2):
            expected = direct_prefix(inner, q, 4, shift)
            self.assertEqual(remove_isolated(direct_prefix(graph, q, 4, shift), 2, q, shift), expected)
            self.assertEqual(isolated_factor(5, q, 4, shift), direct_prefix(Graph(5), q, 4, shift))

    def test_first_coefficient_collision_is_not_class_completeness(self):
        words = ((0, 1, 0, 0, 0, 0, 1, 1), (0, 1, 1, 0, 1, 1, 1, 0))
        q = Fraction(1, 2)
        prefixes = [direct_prefix(graph_from_creation_word(word), q, 3) for word in words]
        self.assertEqual(prefixes[0][1], Fraction(81, 64))
        self.assertEqual(prefixes[0][1], prefixes[1][1])
        self.assertNotEqual(prefixes[0][2], prefixes[1][2])
        for word, values in zip(words, prefixes):
            self.assertEqual(reconstruct_threshold(8, q, values).creation_word, word)

    def test_complete_edgeless_and_empty_residual_conventions(self):
        for n in (1, 2, 7):
            for word in ((0,) * n, (0,) + (1,) * (n - 1)):
                q = Fraction(1, 2)
                graph = graph_from_creation_word(word)
                r = recovery_volume(n, q)
                for shift in (0, 2):
                    actual = reconstruct_threshold(n, q, direct_prefix(graph, q, r, shift), diagonal_shift=shift)
                    self.assertEqual(actual.creation_word, word)
                    self.assertGreaterEqual(actual.graph.n, 1)

    def test_larger_prefix_reuses_the_same_budget(self):
        word = (0, 1, 0, 1, 0, 1, 0)
        q = Fraction(2, 3)
        actual = reconstruct_threshold(7, q, direct_prefix(graph_from_creation_word(word), q, 5))
        self.assertEqual(actual.creation_word, word)
        self.assertEqual(actual.volume, 5)
        self.assertEqual([step['operation'] for step in actual.steps], ['isolated', 'universal', 'isolated', 'universal', 'isolated', 'universal'])

    def test_raw_closures_reconstruct_the_two_collision_interiors(self):
        from singularity.charges import closure_operator, dominating_block, recover_sequence
        from singularity.terminals import glue_graphs

        q, volume = Fraction(1, 2), 3
        words = ((0, 1, 0, 0, 0, 0, 1, 1), (0, 1, 1, 0, 1, 1, 1, 0))
        contexts = (Graph(2, [(0, 1)]), Graph(3, [(0, 2), (1, 2)]))
        for word in words:
            interior = graph_from_creation_word(word)
            block, terminals = dominating_block(interior)
            expected = direct_prefix(interior, q, volume, 2)
            for context in contexts:
                closed, _ = glue_graphs(block, terminals, context, (0, 1))
                # The observation is counted directly on the actual glued
                # graph, without applying the closure operator to its input.
                observed = direct_prefix(closed, q, volume)
                operator = closure_operator(context, (0, 1), interior.n, volume, q)
                recovered = tuple(recover_sequence(observed, operator))
                self.assertEqual(recovered, expected)
                self.assertEqual(reconstruct_threshold(8, q, recovered, diagonal_shift=2).creation_word, word)

    def test_validation_and_explicit_class_hypothesis(self):
        for bad in (True, 2.0, '2'):
            with self.assertRaises(TypeError):
                reconstruct_threshold(bad, Fraction(1, 2), [1, 1, 1])
        for bad in (0.5, True, '1/2'):
            with self.assertRaises(TypeError):
                reconstruct_threshold(2, bad, [1, 1, 1])
        for prefix in ([1], [1, 1], [0, 1, 1], [1, -1, 1]):
            with self.assertRaises(ValueError):
                reconstruct_threshold(2, Fraction(1, 2), prefix)
        with self.assertRaises(TypeError):
            reconstruct_threshold(2, Fraction(1, 2), [1, 0.5, 1])
        with self.assertRaises(ValueError):
            graph_from_creation_word((0, 2))
        actual = reconstruct_threshold(2, Fraction(1, 2), direct_prefix(Graph(2), Fraction(1, 2), 2))
        self.assertEqual(actual.to_dict()['class_hypothesis'], 'threshold graph')


if __name__ == '__main__':
    unittest.main()
