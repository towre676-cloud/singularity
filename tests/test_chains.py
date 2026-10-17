"""P02: level-chain enumeration against weak compositions and direct products."""

from collections import Counter
from itertools import combinations, product
from math import comb
import unittest

from singularity.chains import (
    chain_census, chain_energy, chain_heights, chain_local_coefficients,
    chain_marked_coefficients, chain_normalized_coefficients, heights_chain,
    level_chains, strict_chain_marked_coefficients, validate_chain,
)
from singularity.graph import Graph
from singularity.heights import local_coefficients, marked_coefficients, normalized_coefficients


def all_graphs(max_n):
    for n in range(1, max_n + 1):
        pairs = list(combinations(range(n), 2))
        for mask in range(1 << len(pairs)):
            yield Graph(n, [edge for j, edge in enumerate(pairs) if mask >> j & 1])


class ChainPopulationTests(unittest.TestCase):
    # Declared population: every labeled simple graph on 1..4 vertices
    # (1 + 2 + 8 + 64 = 75 graphs) and every volume 0..6.
    MAX_N, MAX_VOLUME = 4, 6

    def test_complete_marked_histograms_match_weak_compositions(self):
        graphs = cells = profiles = 0
        for graph in all_graphs(self.MAX_N):
            chains = chain_marked_coefficients(graph, self.MAX_VOLUME)
            self.assertEqual(chains, marked_coefficients(graph, self.MAX_VOLUME), graph)
            graphs += 1
            cells += len(chains)
            profiles += sum(chains.values())
        # The receipt is the exact size of what was compared, not a Boolean.
        self.assertEqual((graphs, cells, profiles), (75, 4713, 13019))

    def test_unmarked_and_local_projections(self):
        for graph in all_graphs(3):
            self.assertEqual(chain_normalized_coefficients(graph, 7), normalized_coefficients(graph, 7))
            self.assertEqual(chain_local_coefficients(graph, 7), local_coefficients(graph, 7))

    def test_chain_count_equals_stars_and_bars(self):
        for n in range(1, 6):
            for bound in range(0, 7):
                chains = list(level_chains(n, bound))
                expected = comb(bound + n, n) - comb(bound, n)
                self.assertEqual(len(chains), expected)
                self.assertEqual(len(set(chains)), expected)
        census = chain_census(Graph(4, [(0, 1), (1, 2)]), 6)
        self.assertTrue(census["agrees"])
        self.assertEqual(census["chains_visited"], comb(10, 4) - comb(6, 4))

    def test_chain_profile_bijection_volume_and_energy(self):
        graph = Graph(4, [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2)])
        profiles = set()
        for chain in level_chains(4, 6):
            a = chain_heights(4, chain)
            self.assertEqual(min(a), 0)
            self.assertEqual(max(a), len(chain))
            self.assertEqual(sum(a), sum(level.bit_count() for level in chain))
            self.assertEqual(heights_chain(a), chain)
            direct = sum((a[u] - a[v]) ** 2 for u, v in graph.edges)
            self.assertEqual(chain_energy(graph, chain), direct)
            profiles.add(a)
        expected = {a for a in product(range(7), repeat=4) if sum(a) <= 6 and min(a) == 0}
        self.assertEqual(profiles, expected)


class ChainBoundaryTests(unittest.TestCase):
    def test_height_gaps_need_repeated_levels(self):
        path = Graph(3, [(0, 1), (1, 2)])
        # (0,1,3): S1={1,2}, S2=S3={2}; the repeated pair contributes 2.
        chain = heights_chain((0, 1, 3))
        self.assertEqual(chain, (0b110, 0b100, 0b100))
        self.assertEqual(chain_energy(path, chain), 5)
        # (0,2,2): S1=S2={1,2}; cut sum 2, cross term 2.
        self.assertEqual(chain_energy(path, heights_chain((0, 2, 2))), 4)
        full = chain_marked_coefficients(path, 4)
        strict = strict_chain_marked_coefficients(path, 4)
        lost = Counter(full)
        lost.subtract(strict)
        lost = {key: count for key, count in lost.items() if count}
        # Exactly the profiles with a gap between consecutive used heights are lost.
        expected = Counter()
        for a in product(range(5), repeat=3):
            if sum(a) <= 4 and min(a) == 0:
                used = set(a)
                if any(h not in used for h in range(max(a) + 1)):
                    expected[sum(a), sum((a[u] - a[v]) ** 2 for u, v in path.edges), max(a)] += 1
        self.assertEqual(lost, dict(expected))
        self.assertIn((2, 4, 2), lost)

    def test_absolute_difference_energy_is_not_the_chain_energy(self):
        path = Graph(3, [(0, 1), (1, 2)])
        chain = heights_chain((0, 2, 2))
        cut_sum = sum(sum(bool(level >> u & 1) != bool(level >> v & 1) for u, v in path.edges) for level in chain)
        self.assertEqual(cut_sum, 2)
        self.assertEqual(chain_energy(path, chain), 4)

    def test_singleton_empty_chain_and_zero_volume(self):
        self.assertEqual(list(level_chains(1, 5)), [()])
        self.assertEqual(chain_marked_coefficients(Graph(1), 5), {(0, 0, 0): 1})
        self.assertEqual(chain_local_coefficients(Graph(1), 3), [{0: 1}] * 4)
        for graph in (Graph(1), Graph(3, [(0, 1)])):
            self.assertEqual(chain_marked_coefficients(graph, 0), {(0, 0, 0): 1})
        self.assertEqual(chain_heights(3, ()), (0, 0, 0))
        self.assertEqual(chain_energy(Graph(2, [(0, 1)]), ()), 0)

    def test_disconnected_graph_keeps_positive_component(self):
        graph = Graph(3, [(0, 1)])
        marked = chain_marked_coefficients(graph, 2)
        # Volume 2: (1,1,0) has energy 0 although component {0,1} is positive.
        self.assertEqual(marked[2, 0, 1], 1)
        self.assertEqual(marked[2, 0, 2], 1)  # (0,0,2)

    def test_malformed_chains_and_bounds(self):
        for chain in ((0b111,), (0b1000,), (0b010, 0b101), (0,), (True,)):
            with self.subTest(chain=chain), self.assertRaises((TypeError, ValueError)):
                validate_chain(3, chain)
        for bad in (-1, 1.5, True):
            with self.assertRaises((TypeError, ValueError)):
                list(level_chains(2, bad))
        with self.assertRaises((TypeError, ValueError)):
            list(level_chains(0, 2))
        with self.assertRaises(TypeError):
            chain_marked_coefficients({"n": 2, "edges": []}, 2)
        with self.assertRaises(ValueError):
            heights_chain((1, 2))


if __name__ == "__main__":
    unittest.main()
