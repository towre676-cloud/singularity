"""P15: an energy isometry of height quotients that does not preserve the marks (SNG-F46)."""

from itertools import product
import unittest

from singularity.families import pendant_cycle
from singularity.graph import Graph
from singularity.heights import local_coefficients, marked_coefficients, normalize_heights
from singularity.terminals import circuits, twist_lattice_map


def path_block(m, k):
    path = [0] + list(range(2, 2 * m + 1)) + [1]
    edges = [(path[i], path[i + 1]) for i in range(2 * m)]
    edges.append((path[k], 2 * m + 1))
    return Graph(2 * m + 2, edges)


class TwistLatticeMapTests(unittest.TestCase):
    def setUp(self):
        self.block = path_block(2, 1)
        self.straight, self.twisted, self.phi = twist_lattice_map(self.block, (0, 1), self.block, (0, 1))

    def test_energy_shift_and_involution(self):
        n = self.straight.n
        for a in product(range(-1, 2), repeat=n):
            image = self.phi(a)
            self.assertEqual(self.twisted.energy(image), self.straight.energy(a))
            self.assertEqual(self.phi(tuple(x + 2 for x in a)), tuple(x + 2 for x in image))
            # The same formula maps the twisted gluing back (terminals fixed).
            self.assertEqual(self.phi(image), tuple(a))

    def test_volume_is_not_preserved(self):
        n = self.straight.n
        interior = n - 1  # a vertex of the second block's interior
        unit = tuple(int(v == interior) for v in range(n))
        image = normalize_heights(self.phi(unit))
        self.assertEqual(sum(normalize_heights(unit)), 1)
        self.assertEqual(sum(image), n - 1)
        self.assertEqual(self.twisted.energy(image), self.straight.energy(unit))

    def test_matroid_preserved_but_marked_series_differ(self):
        self.assertEqual(len(circuits(self.straight)), len(circuits(self.twisted)))
        self.assertEqual(local_coefficients(self.straight, 4), local_coefficients(pendant_cycle(4, 2), 4))
        self.assertEqual(local_coefficients(self.twisted, 4), local_coefficients(pendant_cycle(4, 4), 4))
        self.assertNotEqual(marked_coefficients(self.straight, 3), marked_coefficients(self.twisted, 3))

    def test_sufficient_condition_with_an_isomorphism(self):
        # A vertex relabeling preserves energy, volume and span; the marked series agree.
        graph = Graph(5, [(0, 1), (1, 2), (2, 3), (1, 4)])
        relabeled = graph.relabel((4, 2, 0, 1, 3))
        self.assertEqual(marked_coefficients(graph, 5), marked_coefficients(relabeled, 5))


if __name__ == "__main__":
    unittest.main()
