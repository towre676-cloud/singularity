"""Shared experiment panels (OE08).

Oracles: exhaustive subset search recomputes separation from readings;
experiment readings are recomputed by direct matrix products; graph
readings by direct height enumeration on the assembled glued graphs.
"""
import random
import unittest
from fractions import Fraction as F
from itertools import product

from singularity.graph import Graph
from singularity.graph_experiments import BoundaryExperimentSystem
from singularity.observability import OperatorSystem
from singularity.panels import (
    ambiguous_reading, candidate_pairs, certifies_identification, consistent_candidates,
    coverage_masks, exhaustive_minimum_panel, experiment_pool, explicit_pool, greedy_panel,
    l2_ambiguous_reading, l2_certifies, l2_consistent_candidates, l2_separates,
    minimum_cost_l2_panel, minimum_cost_panel, pairwise_cheapest_witnesses, panel_cost,
    reading_pool, separates_all,
)


def random_pool(rng, force_infeasible=False):
    k = rng.randint(2, 4)
    size = rng.randint(1, 10)
    costs = [rng.randint(0, 5) for _ in range(size)]
    rows = [[rng.randint(-2, 2) for _ in range(k)] for _ in range(size)]
    if force_infeasible:
        a, b = rng.sample(range(k), 2)
        for r in rows:
            r[b] = r[a]
    return reading_pool(costs, rows)


class BranchAndBoundAgainstExhaustive(unittest.TestCase):
    def check(self, pool, epsilon):
        oracle = exhaustive_minimum_panel(pool, epsilon)
        for packing in (True, False):
            for reduce in (True, False):
                r = minimum_cost_panel(pool, epsilon, packing=packing, reduce=reduce)
                self.assertEqual(r.feasible, oracle.feasible)
                self.assertEqual(r.uncoverable, oracle.uncoverable)
                if r.feasible:
                    self.assertEqual(r.cost, oracle.cost)
                    self.assertTrue(separates_all(pool, r.panel, epsilon))
                    self.assertEqual(panel_cost(pool, r.panel), r.cost)
                    self.assertLessEqual(r.root_lower_bound, r.cost)
        g = greedy_panel(pool, epsilon)
        self.assertEqual(g.feasible, oracle.feasible)
        if g.feasible:
            self.assertGreaterEqual(g.cost, oracle.cost)
            self.assertTrue(separates_all(pool, g.panel, epsilon))
        return oracle.feasible, (g.cost - oracle.cost) if g.feasible else None

    def test_exact_seeded(self):
        rng = random.Random(8080)
        infeasible = gaps = 0
        for n in range(60):
            feasible, gap = self.check(random_pool(rng, force_infeasible=n % 6 == 0), None)
            infeasible += not feasible
            gaps += bool(gap)
        self.assertGreaterEqual(infeasible, 10)

    def test_robust_seeded(self):
        rng = random.Random(1717)
        infeasible = 0
        for n in range(60):
            pool = random_pool(rng, force_infeasible=n % 7 == 0)
            if n % 2:
                eps = F(rng.randint(1, 4), rng.randint(1, 4))
            else:
                eps = [F(rng.randint(1, 3), 2) for _ in range(pool.size)]
            feasible, _ = self.check(pool, eps)
            infeasible += not feasible
        self.assertGreaterEqual(infeasible, 9)

    def test_greedy_is_not_optimal(self):
        # Partitions {01|23} and {02|13} each cost 1 and cover 4 of 6 pairs
        # (ratio 1/4); the all-distinct reading costs 19/10 and covers all six
        # (ratio 19/60 > 1/4).  Greedy pays 2, the optimum is 19/10.
        pool = reading_pool([1, 1, F(19, 10)], [[0, 0, 1, 1], [0, 1, 0, 1], [0, 1, 2, 3]])
        self.assertEqual(greedy_panel(pool).cost, 2)
        self.assertEqual(greedy_panel(pool).panel, (0, 1))
        exact = minimum_cost_panel(pool)
        self.assertEqual((exact.panel, exact.cost), ((2,), F(19, 10)))
        self.assertEqual(exhaustive_minimum_panel(pool).cost, F(19, 10))

    def test_infeasibility_names_pair(self):
        pool = reading_pool([1, 1], [[0, 0, 1], [0, 0, 2]])
        r = minimum_cost_panel(pool)
        self.assertFalse(r.feasible)
        self.assertEqual(r.uncoverable, ((0, 1),))
        self.assertIsNone(r.panel)

    def test_node_budget(self):
        rng = random.Random(3)
        rows = [[rng.randint(0, 3) for _ in range(6)] for _ in range(10)]
        pool = reading_pool([rng.randint(1, 9) for _ in range(10)], rows)
        if minimum_cost_panel(pool).nodes > 1:
            with self.assertRaises(ValueError):
                minimum_cost_panel(pool, max_nodes=1)


class BoxDecoder(unittest.TestCase):
    def test_theorem_exhaustive(self):
        """Robust panel => unique consistent candidate, for every truth and
        every noise vector on a grid inside the box; non-robust => the
        midpoint reading is admissible and ambiguous."""
        rng = random.Random(42)
        certified = ambiguous = 0
        for _ in range(40):
            k, size = rng.randint(2, 3), rng.randint(1, 3)
            pool = reading_pool([1] * size, [[rng.randint(-3, 3) for _ in range(k)] for _ in range(size)])
            eps = [F(rng.randint(1, 3), 2) for _ in range(size)]
            panel = tuple(range(size))
            if certifies_identification(pool, panel, eps):
                certified += 1
                for t in range(k):
                    for eta in product(*[(-e, -e / 2, 0, e / 3, e) for e in eps]):
                        y = [pool.readings[e][t] + eta[e] for e in panel]
                        self.assertEqual(consistent_candidates(pool, panel, y, eps), (t,))
                self.assertIsNone(ambiguous_reading(pool, panel, eps))
            else:
                ambiguous += 1
                a, b, y = ambiguous_reading(pool, panel, eps)
                for e, ye in zip(panel, y):  # admissible noise for truth a
                    self.assertLessEqual(abs(ye - pool.readings[e][a]), eps[e])
                found = consistent_candidates(pool, panel, y, eps)
                self.assertIn(a, found)
                self.assertIn(b, found)
        self.assertGreater(certified, 5)
        self.assertGreater(ambiguous, 5)

    def test_equality_does_not_certify(self):
        eps = F(1, 2)
        pool = reading_pool([1], [[0, 1]])           # |difference| = 1 = 2*eps
        self.assertFalse(certifies_identification(pool, (0,), eps))
        self.assertEqual(consistent_candidates(pool, (0,), [F(1, 2)], eps), (0, 1))
        self.assertEqual(ambiguous_reading(pool, (0,), eps), (0, 1, (F(1, 2),)))
        self.assertFalse(minimum_cost_panel(pool, eps).feasible)
        self.assertTrue(certifies_identification(pool, (0,), F(1, 2) - F(1, 10**9)))


class EuclideanVersusBox(unittest.TestCase):
    def test_joint_beats_single(self):
        pool = reading_pool([1, 1], [[0, 1], [0, 1]])
        eps = F(3, 5)
        # box model with eps_e = eps: no single experiment robustly separates
        self.assertEqual(coverage_masks(pool, eps), (0, 0))
        self.assertFalse(minimum_cost_panel(pool, eps).feasible)
        # ball model: 1 + 1 = 2 > 4 * 9/25 = 36/25
        self.assertTrue(l2_separates(pool, (0, 1), eps, (0, 1)))
        self.assertTrue(l2_certifies(pool, (0, 1), eps))
        self.assertFalse(l2_certifies(pool, (0,), eps))
        r = minimum_cost_l2_panel(pool, eps)
        self.assertEqual((r.panel, r.cost), ((0, 1), 2))
        # exhaustive over a noise grid inside the l2 ball
        grid = [F(i, 10) for i in range(-6, 7)]
        for t in range(2):
            for e1 in grid:
                for e2 in grid:
                    if e1 * e1 + e2 * e2 <= eps * eps:
                        y = [pool.readings[0][t] + e1, pool.readings[1][t] + e2]
                        self.assertEqual(l2_consistent_candidates(pool, (0, 1), y, eps), (t,))
        a, b, y = l2_ambiguous_reading(pool, (0,), eps)
        self.assertEqual(l2_consistent_candidates(pool, (0,), y, eps), (0, 1))

    def test_l2_equality_does_not_certify(self):
        pool = reading_pool([1, 1], [[0, 3], [0, 4]])  # distance 5 = 2 * 5/2
        self.assertFalse(l2_certifies(pool, (0, 1), F(5, 2)))
        a, b, y = l2_ambiguous_reading(pool, (0, 1), F(5, 2))
        self.assertEqual(l2_consistent_candidates(pool, (0, 1), y, F(5, 2)), (0, 1))


class OperatorPools(unittest.TestCase):
    def test_pool_and_cheapest_witnesses(self):
        rng = random.Random(5)
        for _ in range(15):
            n = rng.randint(1, 3)
            mats = [[[F(rng.randint(-1, 1)) for _ in range(n)] for _ in range(n)] for _ in range(2)]
            obs = [[F(rng.randint(-1, 1)) for _ in range(n)]]
            system = OperatorSystem(n, mats, obs, [1, 2], [rng.randint(0, 1)])
            states = [[F(rng.randint(-1, 1)) for _ in range(n)] for _ in range(3)]
            C = 3
            pool = experiment_pool(system, states, C)
            # oracle: words by brute force over length <= 3
            expected = 0
            for length in range(4):
                for w in product(range(2), repeat=length):
                    if system.observation_costs[0] + sum(system.attachment_costs[i] for i in w) <= C:
                        expected += 1
                        row = list(obs[0])
                        for i in reversed(w):
                            row = [sum(row[a] * mats[i][a][b] for a in range(n)) for b in range(n)]
                        idx = pool.labels.index((0, w))
                        self.assertEqual(pool.readings[idx],
                                         tuple(sum(r * s for r, s in zip(row, v)) for v in states))
            self.assertEqual(pool.size, expected)
            masks = coverage_masks(pool)
            for p, (a, b, status, cost, _) in enumerate(pairwise_cheapest_witnesses(system, states, C)):
                coverers = [pool.costs[e] for e in range(pool.size) if masks[e] >> p & 1]
                if status == "within_budget":
                    self.assertEqual(min(coverers), cost)
                else:
                    self.assertEqual(coverers, [])

    def test_explicit_pool(self):
        system = OperatorSystem(2, [[[0, 1], [1, 0]]], [[1, 0]])
        pool = explicit_pool(system, [[1, 2], [2, 1]], [(0, ()), (0, (0,))])
        self.assertEqual(pool.readings, ((1, 2), (2, 1)))
        self.assertEqual(pool.costs, (0, 1))


HALF = F(1, 2)
P3 = Graph(3, ((0, 1), (1, 2)))
K3 = Graph(3, ((0, 1), (0, 2), (1, 2)))
EI = Graph(3, ((0, 1),))
FAMILY = [(P3, (0, 2)), (P3, (0, 1)), (P3, (1, 2)), (K3, (0, 1)), (EI, (0, 1)), (EI, (0, 2))]


class GraphInstance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.system = BoundaryExperimentSystem(3, HALF)
        cls.ops = cls.system.operator_system([2, 1])
        cls.states = [cls.system.compile_graph(g, t) for g, t in FAMILY]
        cls.pool = experiment_pool(cls.ops, cls.states, 4)

    def test_pool_readings_by_direct_enumeration(self):
        self.assertEqual(self.pool.size, 48)
        direct = {}
        for e, (j, w) in enumerate(self.pool.labels):
            for c, (g, t) in enumerate(FAMILY):
                if (c, w) not in direct:
                    direct[c, w] = self.system.direct_observations(g, t, w)
                self.assertEqual(self.pool.readings[e][c], direct[c, w][j])

    def test_panels(self):
        full = minimum_cost_panel(self.pool)
        self.assertFalse(full.feasible)
        self.assertEqual(full.uncoverable, ((1, 2),))
        witnesses = pairwise_cheapest_witnesses(self.ops, self.states, 4)
        self.assertEqual([w[2] for w in witnesses].count("future_equivalent"), 1)
        self.assertEqual(witnesses[5][:3], (1, 2, "future_equivalent"))
        keep = [0, 1, 3, 4, 5]
        pool = experiment_pool(self.ops, [self.states[i] for i in keep], 4)
        r = minimum_cost_panel(pool)
        self.assertEqual(r.cost, 1)
        self.assertEqual([pool.labels[i] for i in r.panel], [(1, ()), (1, (1,))])
        robust = minimum_cost_panel(pool, F(1, 8))
        self.assertEqual(robust.cost, 4)
        self.assertEqual(greedy_panel(pool, F(1, 8)).cost, 5)
        self.assertTrue(certifies_identification(pool, robust.panel, F(1, 8)))
        # threshold: the largest pairwise single-experiment margin of pair (0,1)
        star = max(abs(r_[0] - r_[1]) for r_ in pool.readings) / 2
        self.assertEqual(star, F(278513, 2097152))
        self.assertFalse(minimum_cost_panel(pool, star).feasible)
        self.assertIsNotNone(ambiguous_reading(pool, range(pool.size), star))


class Validation(unittest.TestCase):
    def test_types_and_values(self):
        pool = reading_pool([1, 2], [[0, 1], [1, 0]])
        for bad in (True, 1.0, "1"):
            with self.assertRaises(TypeError):
                reading_pool([bad], [[0, 1]])
            with self.assertRaises(TypeError):
                reading_pool([1], [[0, bad]])
            with self.assertRaises(TypeError):
                minimum_cost_panel(pool, bad)
            with self.assertRaises(TypeError):
                l2_certifies(pool, (0,), bad)
        with self.assertRaises(TypeError):
            minimum_cost_panel(pool, [F(1), 0.5])
        with self.assertRaises(ValueError):
            reading_pool([-1], [[0, 1]])
        with self.assertRaises(ValueError):
            reading_pool([1], [[0]])
        with self.assertRaises(ValueError):
            reading_pool([1, 1], [[0, 1], [0, 1, 2]])
        with self.assertRaises(ValueError):
            reading_pool([1, 1], [[0, 1]])
        with self.assertRaises(ValueError):
            reading_pool([], [])
        with self.assertRaises(ValueError):
            minimum_cost_panel(pool, 0)
        with self.assertRaises(ValueError):
            minimum_cost_panel(pool, [1])
        with self.assertRaises(ValueError):
            consistent_candidates(pool, (0,), [0], None)
        with self.assertRaises(ValueError):
            consistent_candidates(pool, (0,), [0, 1], 1)
        with self.assertRaises(ValueError):
            panel_cost(pool, (5,))
        with self.assertRaises(TypeError):
            panel_cost(pool, (True,))
        with self.assertRaises(ValueError):
            l2_separates(pool, (0,), 1, (0, 0))
        with self.assertRaises(ValueError):
            exhaustive_minimum_panel(reading_pool([1] * 17, [[0, 1]] * 17))
        system = OperatorSystem(1, [[[1]]], [[1]])
        with self.assertRaises(ValueError):
            experiment_pool(system, [[1]], 3)          # one state only
        with self.assertRaises(ValueError):
            experiment_pool(system, [[1], [2]], -1)
        with self.assertRaises(ValueError):
            experiment_pool(system, [[1], [2]], 100, max_experiments=10)
        with self.assertRaises(TypeError):
            experiment_pool(system, [[1], [2.0]], 1)
        with self.assertRaises(ValueError):
            experiment_pool(system, [[1], [2, 3]], 1)
        self.assertEqual(candidate_pairs(3), ((0, 1), (0, 2), (1, 2)))


if __name__ == "__main__":
    unittest.main()
