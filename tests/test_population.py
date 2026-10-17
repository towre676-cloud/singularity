"""Direct exhaustive oracles for constrained population count/rank/unrank."""

from itertools import combinations, product
import json
import unittest

from singularity.graph import Graph
from singularity.population import HeightPopulation


def brute_population(graph, bound, constraints):
    result = []
    for a in product(range(bound + 1), repeat=graph.n):
        volume = sum(a)
        energy = sum((a[i] - a[j]) ** 2 for i, j in graph.edges)
        span = max(a) - min(a)
        if constraints.get("min_zero", True) and min(a) != 0:
            continue
        if any(constraints.get(name) is not None and value != constraints[name] for name, value in (("volume", volume), ("energy", energy), ("span", span))):
            continue
        if any(constraints.get(name) is not None and value > constraints[name] for name, value in (("max_volume", volume), ("max_energy", energy), ("max_span", span))):
            continue
        result.append(a)
    return result


class PopulationTests(unittest.TestCase):
    def assert_population(self, graph, bound, constraints):
        population = HeightPopulation(graph, max_height=bound, **constraints)
        expected = brute_population(graph, bound, constraints)
        self.assertEqual(population.count(), len(expected), (graph, constraints))
        self.assertEqual(list(population.iter_tuples()), expected)
        for rank, a in enumerate(expected):
            self.assertTrue(population.contains(a))
            self.assertEqual(population.rank(a), rank)
            self.assertEqual(population.unrank(rank), a)
        with self.assertRaises(IndexError):
            population.unrank(len(expected))

    def test_all_graphs_up_to_four_vertices_varied_joint_constraints(self):
        cases = (
            {}, {"min_zero": False}, {"volume": 3}, {"max_volume": 2},
            {"energy": 2}, {"max_energy": 3}, {"span": 2}, {"max_span": 1},
            {"volume": 3, "max_energy": 4, "span": 2},
            {"min_zero": False, "volume": 4, "max_span": 1},
        )
        for n in range(1, 5):
            edges = list(combinations(range(n), 2))
            for mask in range(1 << len(edges)):
                graph = Graph(n, [e for j, e in enumerate(edges) if mask >> j & 1])
                for constraints in cases:
                    self.assert_population(graph, 2, constraints)

    def test_frontier_recursion_on_longer_path_and_relabeling(self):
        graph = Graph(6, [(i, i + 1) for i in range(5)])
        constraints = {"volume": 6, "max_energy": 10, "span": 2}
        self.assert_population(graph, 2, constraints)
        permutation = (5, 2, 0, 4, 1, 3)
        other = graph.relabel(permutation)
        left = HeightPopulation(graph, max_height=2, **constraints)
        right = HeightPopulation(other, max_height=2, **constraints)
        self.assertEqual(left.count(), right.count())
        for a in left.iter_tuples():
            renamed = [0] * graph.n
            for i, label in enumerate(permutation):
                renamed[label] = a[i]
            self.assertTrue(right.contains(renamed))

    def test_derived_volume_span_and_energy_bounds(self):
        graph = Graph(4, [(0, 1), (1, 2), (2, 3)])
        for constraints, brute_bound in (({"volume": 4}, 4), ({"max_volume": 3}, 3), ({"span": 2}, 2), ({"max_span": 2}, 2), ({"energy": 3}, 3), ({"max_energy": 3}, 3)):
            population = HeightPopulation(graph, **constraints)
            self.assertEqual(list(population.iter_tuples()), brute_population(graph, brute_bound, constraints))
            self.assertLessEqual(population.height_bound, brute_bound)
        synchronized = HeightPopulation(graph, energy=0)
        self.assertEqual(list(synchronized.iter_tuples()), [(0, 0, 0, 0)])
        self.assertEqual(HeightPopulation(Graph(1)).count(), 1)

    def test_finiteness_is_not_silently_assumed(self):
        for graph, constraints in ((Graph(2), {"energy": 0}), (Graph(2, [(0, 1)]), {"energy": 2, "min_zero": False}), (Graph(3), {"max_span": 2, "min_zero": False}), (Graph(2), {})):
            with self.assertRaises(ValueError):
                HeightPopulation(graph, **constraints)

    def test_empty_populations_and_invalid_inputs(self):
        graph = Graph(3, [(0, 1), (1, 2)])
        self.assertEqual(HeightPopulation(graph, max_height=1, volume=10).count(), 0)
        self.assertEqual(HeightPopulation(graph, volume=2, max_volume=1).count(), 0)
        self.assertEqual(HeightPopulation(graph, max_height=1, span=2).count(), 0)
        population = HeightPopulation(graph, max_height=2)
        self.assertFalse(population.contains((1, 1, 1)))
        self.assertFalse(population.contains((0, -1, 1)))
        self.assertFalse(population.contains((0, 1)))
        with self.assertRaises(ValueError):
            population.rank((1, 1, 1))
        with self.assertRaises(ValueError):
            population.unrank(-1)
        with self.assertRaises(TypeError):
            population.unrank(True)
        for constraints in ({"max_height": -1}, {"volume": -1}, {"max_energy": 1.5}, {"max_span": True}):
            with self.assertRaises((TypeError, ValueError)):
                HeightPopulation(graph, **constraints)

    def test_original_labeled_multiplicity_large_exact_counts_and_json(self):
        graph = Graph(20)
        population = HeightPopulation(graph, max_height=3, min_zero=False)
        self.assertEqual(population.count(), 4 ** 20)
        self.assertEqual(population.unrank(0), (0,) * 20)
        self.assertEqual(population.unrank(population.count() - 1), (3,) * 20)
        index = 87123456789
        self.assertEqual(population.rank(population.unrank(index)), index)
        normalized = HeightPopulation(graph, max_height=3)
        self.assertEqual(normalized.count(), 4 ** 20 - 3 ** 20)
        source = json.loads(json.dumps(normalized.to_dict(sample=2)))
        self.assertEqual(Graph.from_dict(source["graph"]), graph)
        self.assertEqual(source["count"], normalized.count())
        self.assertEqual(len(source["witnesses"]), 2)
        self.assertEqual(source["witnesses"][1]["rank"], 1)


if __name__ == "__main__":
    unittest.main()
