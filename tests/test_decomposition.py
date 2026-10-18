"""P12: supplied tree decompositions, checker and bag-conditioned exact engine."""

from itertools import combinations
import unittest

from singularity.chains import chain_marked_coefficients
from singularity.decomposition import (
    SCHEMA, TreeDecomposition, charge_owners, check_decomposition,
    decomposition_histogram, decomposition_statistics, elimination_decomposition,
    forest_decomposition, marked_decomposition_coefficients,
)
from singularity.graph import Graph
from singularity.heights import marked_coefficients
from singularity.transfer import bounded_height_histogram, brute_bounded_height_histogram


def cycle(n):
    return Graph(n, [(i, (i + 1) % n) for i in range(n)])


def ladder(rungs):
    edges = [(i, i + rungs) for i in range(rungs)]
    edges += [(i, i + 1) for i in range(rungs - 1)] + [(i + rungs, i + rungs + 1) for i in range(rungs - 1)]
    return Graph(2 * rungs, edges)


def decompositions():
    """Several valid decompositions per graph, including redundant bags."""
    c5, c6, lad, k4 = cycle(5), cycle(6), ladder(4), Graph(4, combinations(range(4), 2))
    two_triangles = Graph(6, [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)])
    return [
        ("C5 fan", c5, TreeDecomposition([(0, 1, 2), (0, 2, 3), (0, 3, 4)], [(0, 1), (1, 2)], 0)),
        ("C5 fan rooted at end", c5, TreeDecomposition([(0, 1, 2), (0, 2, 3), (0, 3, 4)], [(0, 1), (1, 2)], 2)),
        ("C5 elimination", c5, elimination_decomposition(c5, [2, 4, 0, 1, 3])),
        ("C6 elimination identity", c6, elimination_decomposition(c6, range(6))),
        ("C6 elimination alternating", c6, elimination_decomposition(c6, [0, 3, 1, 4, 2, 5])),
        ("C6 star of bags", c6, TreeDecomposition([(0, 2, 4), (0, 1, 2), (2, 3, 4), (4, 5, 0)], [(0, 1), (0, 2), (0, 3)], 0)),
        ("ladder path", lad, TreeDecomposition([(0, 4, 1), (1, 4, 5), (1, 5, 2), (2, 5, 6), (2, 6, 3), (3, 6, 7)], [(i, i + 1) for i in range(5)], 3)),
        ("ladder elimination", lad, elimination_decomposition(lad, [0, 4, 1, 5, 2, 6, 3, 7])),
        ("K4 single bag", k4, TreeDecomposition([(0, 1, 2, 3)])),
        ("K4 with redundant bags", k4, TreeDecomposition([(0, 1, 2, 3), (0, 1, 2, 3), (1, 2), (3,)], [(0, 1), (1, 2), (0, 3)], 2)),
        ("two triangles", two_triangles, TreeDecomposition([(0, 1, 2), (3, 4, 5)], [(0, 1)], 1)),
        ("two triangles via empty bag", two_triangles, TreeDecomposition([(0, 1, 2), (), (3, 4, 5)], [(0, 1), (1, 2)], 1)),
    ]


class CheckerTests(unittest.TestCase):
    def test_valid_decompositions_pass(self):
        for name, graph, decomposition in decompositions():
            with self.subTest(name):
                self.assertEqual(check_decomposition(graph, decomposition), [])

    def test_malformed_decompositions_are_rejected(self):
        c4 = cycle(4)
        cases = [
            (TreeDecomposition([(0, 1, 2)]), "vertex 3 is in no bag"),
            (TreeDecomposition([(0, 1, 2), (0, 2, 3)], [(0, 1)]), None),
            (TreeDecomposition([(0, 1), (1, 2), (2, 3)], [(0, 1), (1, 2)]), "edge [0, 3] is in no bag"),
            (TreeDecomposition([(0, 1, 3), (1, 2), (2, 3, 0)], [(0, 1), (1, 2)]), "vertex 0 are not connected"),
            (TreeDecomposition([(0, 1, 2), (0, 2, 3), (0, 2)], [(0, 1), (1, 2), (2, 0)]), "not a tree"),
            (TreeDecomposition([(0, 1, 2), (0, 2, 3)]), "disconnected"),
            (TreeDecomposition([(0, 1, 2), (0, 2, 3)], [(0, 1)], root=2), "root"),
            (TreeDecomposition([(0, 1, 1, 2), (0, 2, 3)], [(0, 1)]), "repeats a vertex"),
            (TreeDecomposition([(0, 1, 2), (0, 2, 4)], [(0, 1)]), "outside"),
            (TreeDecomposition([(0, True, 2), (0, 2, 3)], [(0, 1)]), "non-integer"),
            (TreeDecomposition([(0, 1, 2), (0, 2, 3)], [(0, 0)]), "invalid"),
            (TreeDecomposition([(0, 1, 2), (0, 2, 3)], [(0, 5)]), "invalid"),
            (TreeDecomposition([]), "at least one bag"),
        ]
        for decomposition, fragment in cases:
            errors = check_decomposition(c4, decomposition)
            if fragment is None:
                self.assertEqual(errors, [])
                continue
            with self.subTest(decomposition=decomposition.to_dict()):
                self.assertTrue(any(fragment in e for e in errors), errors)
                with self.assertRaises(ValueError):
                    decomposition_histogram(c4, decomposition, 1)

    def test_json_roundtrip_and_schema(self):
        decomposition = TreeDecomposition([(0, 1, 2), (0, 2, 3)], [(0, 1)], 1)
        self.assertEqual(TreeDecomposition.from_dict(decomposition.to_dict()).to_dict(), decomposition.to_dict())
        self.assertEqual(TreeDecomposition.from_dict({**decomposition.to_dict(), "schema": SCHEMA}).root, 1)
        for bad in ({"bags": [], "edges": []}, {**decomposition.to_dict(), "schema": "other/1"}, []):
            with self.assertRaises(ValueError):
                TreeDecomposition.from_dict(bad)

    def test_every_charge_has_exactly_one_owner(self):
        for name, graph, decomposition in decompositions():
            vertices, edges = charge_owners(graph, decomposition)
            with self.subTest(name):
                self.assertEqual(sorted(vertices), list(range(graph.n)))
                self.assertEqual(sorted(edges), list(graph.edges))
                for v, owner in vertices.items():
                    self.assertIn(v, decomposition.bags[owner])
                for (u, v), owner in edges.items():
                    self.assertTrue({u, v} <= set(decomposition.bags[owner]))


class EngineTests(unittest.TestCase):
    def test_every_decomposition_matches_cartesian_enumeration(self):
        for name, graph, decomposition in decompositions():
            for height in (0, 1, 2):
                for min_zero in (False, True):
                    with self.subTest(name, height=height, normalized=min_zero):
                        self.assertEqual(
                            decomposition_histogram(graph, decomposition, height, min_zero=min_zero),
                            brute_bounded_height_histogram(graph, height, min_zero=min_zero),
                        )

    def test_marked_coefficients_match_both_enumerators(self):
        for name, graph, decomposition in decompositions():
            with self.subTest(name):
                marked = marked_decomposition_coefficients(graph, decomposition, 5)
                self.assertEqual(marked, marked_coefficients(graph, 5))
                self.assertEqual(marked, chain_marked_coefficients(graph, 5))
        k5 = Graph(5, combinations(range(5), 2))
        self.assertEqual(marked_decomposition_coefficients(k5, TreeDecomposition([tuple(range(5))]), 4), marked_coefficients(k5, 4))

    def test_width_one_matches_forest_transfer_including_disconnected(self):
        forests = [
            Graph(7, [(0, 1), (1, 2), (3, 4), (3, 5)]),
            Graph(8, [(0, 1), (1, 2), (1, 3), (3, 4), (3, 5), (5, 6), (0, 7)]),
            Graph(4),
            Graph(1),
        ]
        for graph in forests:
            decomposition = forest_decomposition(graph)
            self.assertLessEqual(decomposition.width, 1)
            for height in (0, 2, 3):
                with self.subTest(graph=graph.to_dict(), height=height):
                    self.assertEqual(
                        decomposition_histogram(graph, decomposition, height, max_volume=7, min_zero=True),
                        bounded_height_histogram(graph, height, max_volume=7, min_zero=True),
                    )
        with self.assertRaises(ValueError):
            forest_decomposition(cycle(4))

    def test_volume_pruning_and_bounds(self):
        graph, decomposition = cycle(6), elimination_decomposition(cycle(6), range(6))
        full = decomposition_histogram(graph, decomposition, 3)
        for budget in (0, 4, 6, 7, 18):
            expected = {k: c for k, c in full.items() if k[0] <= budget}
            self.assertEqual(decomposition_histogram(graph, decomposition, 3, max_volume=budget), expected)
        for bad in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                decomposition_histogram(graph, decomposition, bad)
        with self.assertRaises(TypeError):
            decomposition_histogram(graph, decomposition.to_dict(), 1)

    def test_cost_measures(self):
        graph = ladder(4)
        decomposition = decompositions()[6][2]
        stats = decomposition_statistics(graph, decomposition, 2, max_volume=6)
        self.assertEqual(stats["width"], 2)
        self.assertEqual(stats["bag_assignments"], sum(3 ** len(b) for b in decomposition.bags))
        self.assertGreater(stats["message_support_cells"], 0)


if __name__ == "__main__":
    unittest.main()
