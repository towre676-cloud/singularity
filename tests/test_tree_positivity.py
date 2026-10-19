import itertools
import unittest
from fractions import Fraction

from singularity.graph import Graph
from singularity.tree_positivity import (
    boxed_tree_kernel, consecutive_minor_lead, distance_minor_lead, exact_determinant, terminal_path,
)


def brute_box(tree, terminals, rows, columns, bound, x, q):
    interior = [v for v in range(tree.n) if v not in terminals]
    output = []
    for s in rows:
        row = []
        for t in columns:
            total = Fraction()
            for values in itertools.product(range(bound + 1), repeat=len(interior)):
                heights = [0] * tree.n
                heights[terminals[0]], heights[terminals[1]] = s, t
                for v, h in zip(interior, values):
                    heights[v] = h
                total += x ** sum(values) * q ** tree.energy(heights)
            row.append(total)
        output.append(tuple(row))
    return tuple(output)


def compositions(total, length):
    if length == 0:
        if total == 0:
            yield ()
    elif length == 1:
        yield (total,)
    else:
        for head in range(total + 1):
            for tail in compositions(total - head, length - 1):
                yield (head,) + tail


def direct_determinant_coefficients(tree, terminals, budget, q):
    """Independent fixed-pin weak-composition enumeration, no tree messages."""
    interior = [v for v in range(tree.n) if v not in terminals]
    coefficients = {}
    for s, t in itertools.product((0, 1), repeat=2):
        values = []
        for volume in range(budget + 1):
            value = Fraction()
            for profile in compositions(volume, len(interior)):
                heights = [0] * tree.n
                heights[terminals[0]], heights[terminals[1]] = s, t
                for v, height in zip(interior, profile):
                    heights[v] = height
                value += q ** tree.energy(heights)
            values.append(value)
        coefficients[s, t] = values
    return tuple(sum((coefficients[0, 0][j] * coefficients[1, 1][r - j]
                      - coefficients[0, 1][j] * coefficients[1, 0][r - j]
                      for j in range(r + 1)), Fraction()) for r in range(budget + 1))


def prufer_tree(n, code):
    degrees = [1] * n
    for vertex in code:
        degrees[vertex] += 1
    edges = []
    for vertex in code:
        leaf = next(i for i, degree in enumerate(degrees) if degree == 1)
        edges.append((leaf, vertex))
        degrees[leaf] -= 1
        degrees[vertex] -= 1
    leaves = [i for i, degree in enumerate(degrees) if degree == 1]
    edges.append(tuple(leaves))
    return Graph(n, edges)


class TreePositivityTests(unittest.TestCase):
    def test_box_messages_agree_with_direct_height_assignments(self):
        cases = [
            (Graph(2, [(0, 1)]), (0, 1)),
            (Graph(5, [(0, 1), (1, 2), (2, 3), (1, 4)]), (0, 3)),
            (Graph(6, [(0, 1), (1, 2), (2, 3), (1, 4), (4, 5)]), (2, 5)),
            (Graph(6, [(0, 1), (0, 2), (0, 3), (1, 4), (4, 5)]), (0, 1)),
        ]
        for tree, terminals in cases:
            for q in (Fraction(1, 2), Fraction(2, 3)):
                args = (tree, terminals, (0, 2, 4), (0, 1, 3), 2, Fraction(1, 3), q)
                self.assertEqual(boxed_tree_kernel(*args), brute_box(*args))

    def test_all_ordered_box_minors_within_rank_bound_are_positive(self):
        cases = [
            (Graph(5, [(0, 1), (1, 2), (2, 3), (1, 4)]), (0, 3)),
            (Graph(6, [(0, 1), (0, 2), (0, 3), (1, 4), (4, 5)]), (0, 1)),
        ]
        for tree, terminals in cases:
            matrix = boxed_tree_kernel(tree, terminals, (0, 1, 3, 4), (0, 2, 3, 5), 2,
                                       Fraction(2, 5), Fraction(1, 2))
            for size in (1, 2, 3):
                for rows in itertools.combinations(range(4), size):
                    for columns in itertools.combinations(range(4), size):
                        self.assertGreater(exact_determinant([[matrix[i][j] for j in columns]
                                                             for i in rows]), 0)

    def test_box_rank_boundary_and_adjacent_terminal_exception(self):
        path = Graph(3, [(0, 1), (1, 2)])
        matrix = boxed_tree_kernel(path, (0, 2), (0, 1, 2), (0, 1, 2), 1,
                                   Fraction(1, 2), Fraction(1, 2))
        self.assertEqual(exact_determinant(matrix), 0)
        star = Graph(4, [(0, 1), (0, 2), (0, 3)])
        matrix = boxed_tree_kernel(star, (0, 1), (0, 1, 2), (0, 1, 2), 0,
                                   Fraction(1, 2), Fraction(1, 2))
        self.assertGreater(exact_determinant(matrix), 0)

    def test_leading_distance_coefficient_on_all_small_labeled_trees(self):
        for n in range(2, 5):
            for code in itertools.product(range(n), repeat=n - 2):
                tree = prufer_tree(n, code)
                for terminals in itertools.combinations(range(n), 2):
                    predicted = distance_minor_lead(tree, terminals, Fraction(1, 2))
                    coefficients = direct_determinant_coefficients(
                        tree, terminals, predicted['first_volume'], Fraction(1, 2))
                    self.assertEqual(coefficients[:-1], (Fraction(),) * predicted['first_volume'])
                    self.assertEqual(coefficients[-1], predicted['coefficient'])

    def test_branched_path_degree_factor_and_orientation(self):
        tree = Graph(8, [(0, 1), (1, 2), (2, 3), (0, 4), (1, 5), (2, 6), (3, 7)])
        predicted = distance_minor_lead(tree, (0, 3), Fraction(2, 3))
        self.assertEqual(predicted['off_path_edges'], 4)
        self.assertEqual(predicted['distance'], 3)
        self.assertEqual(direct_determinant_coefficients(tree, (0, 3), 2, Fraction(2, 3)),
                         (0, 0, predicted['coefficient']))
        self.assertEqual(terminal_path(tree, (3, 0)), tuple(reversed(predicted['path'])))

    def test_global_volume_truncation_can_have_a_negative_minor(self):
        # An actual tree.  This evaluates only interior volume <= 1, rather
        # than an independent height box: positivity is deliberately false.
        x, q = Fraction(1, 3), Fraction(1, 2)
        matrix = [[q ** (s * s + t * t) *
                   (1 + x * q * q * (q ** (-2 * s) + q ** (-2 * t)))
                   for t in (0, 1)] for s in (0, 1)]
        self.assertEqual(exact_determinant(matrix), -x*x*q*q*(1-q*q)**2)
        self.assertLess(exact_determinant(matrix), 0)
        tree = Graph(4, [(0, 1), (1, 2), (2, 3)])
        self.assertEqual(direct_determinant_coefficients(tree, (0, 3), 2, q),
                         (0, 0, (1-q*q)**3))

    def test_higher_consecutive_pin_minor_leading_terms(self):
        # A three-vertex path has one interior height.  Coefficients of every
        # pinned entry are a single independent assignment at each volume.
        for order in (3, 4):
            tree = Graph(3, [(0, 1), (1, 2)])
            q = Fraction(2, 3)
            predicted = consecutive_minor_lead(tree, (0, 2), q, order)
            budget = predicted['first_volume']
            entries = [[tuple(q ** ((s-h)**2 + (h-t)**2) for h in range(budget+1))
                        for t in range(order)] for s in range(order)]
            determinant = [Fraction()] * (budget + 1)
            for permutation in itertools.permutations(range(order)):
                inversions = sum(permutation[i] > permutation[j]
                                 for i in range(order) for j in range(i+1, order))
                product = [Fraction(1)] + [Fraction()] * budget
                for i, j in enumerate(permutation):
                    product = [sum((product[a] * entries[i][j][r-a] for a in range(r+1)),
                                   Fraction()) for r in range(budget+1)]
                determinant = [a + (-1)**inversions * b for a, b in zip(determinant, product)]
            self.assertEqual(determinant[:-1], [Fraction()] * budget)
            self.assertEqual(determinant[-1], predicted['coefficient'])

    def test_validation_and_work_budget(self):
        tree = Graph(3, [(0, 1), (1, 2)])
        with self.assertRaises(ValueError):
            terminal_path(Graph(3, [(0, 1), (1, 2), (0, 2)]), (0, 1))
        with self.assertRaises(ValueError):
            terminal_path(Graph(3, [(0, 1)]), (0, 1))
        with self.assertRaises(ValueError):
            terminal_path(tree, (0, 0))
        with self.assertRaises(TypeError):
            boxed_tree_kernel(tree, (0, 2), (0, 1), (0, 1), 2, 0.5, Fraction(1, 2))
        with self.assertRaises(ValueError):
            boxed_tree_kernel(tree, (0, 2), (0, 1), (0, 1), 20,
                              Fraction(1, 2), Fraction(1, 2), max_work=10)
        with self.assertRaises(ValueError):
            distance_minor_lead(tree, (0, 2), Fraction(1))
        with self.assertRaises(ValueError):
            boxed_tree_kernel(tree, (0, 2), (), (0, 1), 2, Fraction(1, 2), Fraction(1, 2))
        with self.assertRaises(ValueError):
            exact_determinant([[1, 2]])


if __name__ == '__main__':
    unittest.main()
