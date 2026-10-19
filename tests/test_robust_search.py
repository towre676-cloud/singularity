"""Cost-bounded robust experiment search against an independent brute force.

The oracle below enumerates words with itertools.product, multiplies the
state by explicit matrices in chronological order and shares no code with
either the row-side exhaustive search or the state-side branch-and-bound.
"""
import random
import unittest
from fractions import Fraction as F
from itertools import product

from singularity.graph import Graph
from singularity.graph_experiments import BoundaryExperimentSystem
from singularity.observability import (OperatorSystem, minimum_distinguishing_experiment,
                                       observable_closure)
from singularity.robust_search import (bounded_family_search, bounded_margin_search,
                                       exhaustive_family_search, exhaustive_margin_search,
                                       family_margin, kappa_table, margin, matrix_inf_norm)

HALF = F(1, 2)
PATH = Graph(3, ((0, 1), (1, 2)))
AMPLIFY = OperatorSystem(1, [[[2]]], [[1]])
CREEP = OperatorSystem(2, [[[1, 1], [0, HALF]]], [[1, 0]])
# Two generators: a swap and a stretch of the second coordinate.
SEPARATE = OperatorSystem(2, [[[0, 1], [1, 0]], [[1, 0], [0, 3]]], [[1, 0]])


def mat_vec(m, v):
    return tuple(sum((a * b for a, b in zip(row, v)), F(0)) for row in m)


def brute_force(system, differences, noise, budget):
    """Best margin over every affordable experiment; words by length."""
    costs, gammas = system.attachment_costs, system.observation_costs
    cmin = min(costs, default=None)
    max_length = 0 if cmin is None else int(budget // cmin)
    best = None
    for length in range(max_length + 1):
        for word in product(range(len(system.operators)), repeat=length):
            wc = sum((costs[i] for i in word), F(0))
            states = list(differences)
            for i in word:
                states = [mat_vec(system.operators[i], v) for v in states]
            for j, row in enumerate(system.observations):
                if wc + gammas[j] > budget:
                    continue
                value = min(abs(sum((a * b for a, b in zip(row, v)), F(0))) for v in states) / noise[j]
                if best is None or value > best:
                    best = value
    return best


def subtree_margins(system, prefix, differences, noise, budget):
    """Margins of every affordable experiment whose word extends ``prefix``."""
    costs, gammas = system.attachment_costs, system.observation_costs
    base = sum((costs[i] for i in prefix), F(0))
    remaining = budget - base
    if remaining < 0:
        return []
    max_length = int(remaining // min(costs))
    out = []
    for length in range(max_length + 1):
        for suffix in product(range(len(system.operators)), repeat=length):
            word = tuple(prefix) + suffix
            wc = sum((costs[i] for i in word), F(0))
            states = list(differences)
            for i in word:
                states = [mat_vec(system.operators[i], v) for v in states]
            for j, row in enumerate(system.observations):
                if wc + gammas[j] <= budget:
                    out.append(min(abs(sum((a * b for a, b in zip(row, v)), F(0)))
                                   for v in states) / noise[j])
    return out


def random_system(rng):
    n, g, o = rng.randint(1, 3), rng.randint(1, 2), rng.randint(1, 2)
    entry = lambda: F(rng.randint(-4, 4), rng.choice((1, 2)))
    ops = [[[entry() for _ in range(n)] for _ in range(n)] for _ in range(g)]
    obs = [[entry() for _ in range(n)] for _ in range(o)]
    system = OperatorSystem(n, ops, obs, [rng.randint(1, 3) for _ in range(g)],
                            [rng.randint(0, 2) for _ in range(o)])
    noise = [rng.choice((HALF, 1, 2)) for _ in range(o)]
    return system, noise, rng.randint(0, 6)


def pairwise(states):
    return [tuple(x - y for x, y in zip(states[a], states[b]))
            for a in range(len(states)) for b in range(a + 1, len(states))]


class RandomAgreementTests(unittest.TestCase):
    def test_pair_margin_agrees_on_seeded_systems(self):
        for seed in range(50):
            rng = random.Random(seed)
            system, noise, budget = random_system(rng)
            d = tuple(F(rng.randint(-3, 3), rng.choice((1, 2))) for _ in range(system.dimension))
            bb = bounded_margin_search(system, d, noise, budget)
            ex = exhaustive_margin_search(system, d, noise, budget)
            oracle = brute_force(system, [d], noise, budget)
            self.assertEqual(bb.margin, oracle, seed)
            self.assertEqual(ex.margin, oracle, seed)
            if oracle is not None:
                e = bb.experiment
                self.assertLessEqual(e.cost, budget)
                self.assertEqual(margin(system, e.observation, e.word, d, noise), oracle)
                self.assertLessEqual(bb.nodes, ex.nodes)

    def test_family_margin_agrees_on_seeded_systems(self):
        for seed in range(100, 150):
            rng = random.Random(seed)
            system, noise, budget = random_system(rng)
            states = [tuple(F(rng.randint(-3, 3)) for _ in range(system.dimension)) for _ in range(3)]
            bb = bounded_family_search(system, states, noise, budget)
            ex = exhaustive_family_search(system, states, noise, budget)
            oracle = brute_force(system, pairwise(states), noise, budget)
            self.assertEqual(bb.margin, oracle, seed)
            self.assertEqual(ex.margin, oracle, seed)
            if oracle is not None:
                e = bb.experiment
                self.assertEqual(family_margin(system, e.observation, e.word, states, noise), oracle)

    def test_no_pruned_subtree_beats_the_optimum(self):
        checked = 0
        for seed in range(200, 260):
            rng = random.Random(seed)
            system, noise, budget = random_system(rng)
            states = [tuple(F(rng.randint(-3, 3)) for _ in range(system.dimension)) for _ in range(2 + seed % 2)]
            diffs = pairwise(states)
            result = bounded_family_search(system, states, noise, budget, record_pruned=True)
            self.assertEqual(result.pruned, len(result.pruned_nodes))
            for node in result.pruned_nodes:
                checked += 1
                values = subtree_margins(system, node.word, diffs, noise, budget)
                self.assertTrue(all(v <= node.bound for v in values), (seed, node))
                self.assertTrue(all(v <= result.margin for v in values), (seed, node))
        self.assertGreater(checked, 20)

    def test_pruning_occurs_with_contracting_generators(self):
        system = OperatorSystem(2, [[[HALF, 0], [0, HALF]], [[0, HALF], [HALF, 0]]], [[1, 1], [1, -1]])
        result = bounded_margin_search(system, (1, 0), (1, 1), 6, record_pruned=True)
        self.assertEqual(result.margin, 1)
        self.assertGreater(result.pruned, 0)
        self.assertEqual(result.nodes, 1)

    def test_kappa_dynamic_programme(self):
        system = OperatorSystem(1, [[[2]], [[3]]], [[1]], [2, 3])
        table = kappa_table(system, 7)
        # words: cost 2 -> 2, 3 -> 3, 4 -> 4, 5 -> 6, 6 -> 9, 7 -> 12
        self.assertEqual(table, {0: 1, 2: 2, 3: 3, 4: 4, 5: 6, 6: 9, 7: 12})
        self.assertEqual(matrix_inf_norm([[1, -2], [HALF, 0]]), 3)


class CounterexampleTests(unittest.TestCase):
    def test_amplification(self):
        cert = observable_closure(AMPLIFY)
        self.assertEqual([e.word for e in cert.basis], [()])
        witness = minimum_distinguishing_experiment(AMPLIFY, (1,), cert)
        self.assertEqual((witness.word, margin(AMPLIFY, 0, witness.word, (1,), (1,))), ((), 1))
        for budget in range(11):
            result = bounded_margin_search(AMPLIFY, (1,), (1,), budget)
            self.assertEqual(result.margin, 2 ** budget)
            self.assertEqual(result.experiment.word, (0,) * budget)
        self.assertEqual(bounded_margin_search(AMPLIFY, (1,), (1,), F(7, 2)).margin, 8)

    def test_supremum_not_attained(self):
        for k in range(21):
            value = margin(CREEP, 0, (0,) * k, (0, 1), (1,))
            self.assertEqual(value, 2 - F(2) ** (1 - k))
            self.assertLess(value, 2)
        values = [bounded_margin_search(CREEP, (0, 1), (1,), c).margin for c in range(9)]
        self.assertEqual(values, [2 - F(2) ** (1 - c) for c in range(9)])
        self.assertEqual(matrix_inf_norm(CREEP.operators[0]), 2)  # the bound is loose here

    def test_dependence_pruning_discards_the_best_row(self):
        cert = observable_closure(SEPARATE)
        self.assertEqual([e.word for e in cert.basis], [(), (0,)])
        witness = minimum_distinguishing_experiment(SEPARATE, (0, 1), cert)
        self.assertEqual(witness.word, (0,))
        best = bounded_margin_search(SEPARATE, (0, 1), (1,), 2)
        self.assertEqual((best.experiment.word, best.margin), ((1, 0), 3))
        self.assertNotIn(best.experiment.word, [e.word for e in cert.basis])
        self.assertGreater(best.margin, margin(SEPARATE, 0, witness.word, (0, 1), (1,)))
        self.assertEqual(best.experiment.row, (0, 3))  # 3 * (L M_0), dependent on a cheaper row
        self.assertEqual(margin(SEPARATE, 0, (0, 1), (0, 1), (1,)), 1)  # order matters

    def test_two_problems_separate(self):
        witness = minimum_distinguishing_experiment(SEPARATE, (0, 1))
        best = bounded_margin_search(SEPARATE, (0, 1), (1,), 2)
        self.assertNotEqual(witness.word, best.experiment.word)
        self.assertEqual(exhaustive_margin_search(SEPARATE, (0, 1), (1,), 2).margin, 3)


class GraphFixtureTests(unittest.TestCase):
    def test_path_fixture_budgets(self):
        system = BoundaryExperimentSystem(1, HALF)
        ops = system.operator_system(attachment_costs=(2, 1))
        d = tuple(a - b for a, b in zip(system.compile_graph(PATH, (0, 2)), system.compile_graph(PATH, (0, 1))))
        for budget in range(1, 7):
            bb = bounded_margin_search(ops, d, (1, 1), budget)
            ex = exhaustive_margin_search(ops, d, (1, 1), budget)
            self.assertEqual(bb.margin, ex.margin)
            self.assertEqual(bb.margin, brute_force(ops, [d], (1, 1), budget))
            self.assertEqual(bb.margin, F(1, 4) - F(1, 2 ** (budget + 2)))
        self.assertEqual(minimum_distinguishing_experiment(ops, d).word, (1,))


class ValidationTests(unittest.TestCase):
    def test_bad_inputs(self):
        for noise in ((0,), (-1,)):
            with self.assertRaises(ValueError):
                bounded_margin_search(AMPLIFY, (1,), noise, 1)
        for noise in ((0.5,), (True,), ("1",), "1", 1):
            with self.assertRaises(TypeError):
                bounded_margin_search(AMPLIFY, (1,), noise, 1)
        with self.assertRaises(ValueError):
            bounded_margin_search(AMPLIFY, (1,), (1, 1), 1)
        with self.assertRaises(ValueError):
            bounded_margin_search(AMPLIFY, (1,), (1,), -1)
        with self.assertRaises(ValueError):
            exhaustive_margin_search(AMPLIFY, (1,), (1,), F(-1, 2))
        for budget in (1.0, True, "1"):
            with self.assertRaises(TypeError):
                bounded_margin_search(AMPLIFY, (1,), (1,), budget)
        with self.assertRaises(TypeError):
            bounded_margin_search(AMPLIFY, (1.0,), (1,), 1)
        with self.assertRaises(ValueError):
            bounded_margin_search(AMPLIFY, (1, 2), (1,), 1)
        with self.assertRaises(ValueError):
            bounded_family_search(AMPLIFY, [(1,)], (1,), 1)
        with self.assertRaises(TypeError):
            bounded_margin_search("system", (1,), (1,), 1)
        with self.assertRaises(ValueError):
            bounded_margin_search(AMPLIFY, (1,), (1,), 1, max_nodes=0)
        with self.assertRaises(TypeError):
            bounded_margin_search(AMPLIFY, (1,), (1,), 1, max_nodes=True)
        with self.assertRaises(ValueError):
            bounded_margin_search(AMPLIFY, (1,), (1,), 30, max_nodes=5)
        with self.assertRaises(ValueError):
            margin(AMPLIFY, 1, (), (1,), (1,))

    def test_unaffordable_and_zero(self):
        system = OperatorSystem(1, [[[2]]], [[1]], observation_costs=[3])
        for search in (bounded_margin_search, exhaustive_margin_search):
            result = search(system, (1,), (1,), 2)
            self.assertIsNone(result.experiment)
            self.assertIsNone(result.margin)
        result = bounded_margin_search(AMPLIFY, (0,), (1,), 4)
        self.assertEqual(result.margin, 0)
        self.assertEqual(bounded_family_search(AMPLIFY, [(1,), (1,)], (1,), 2).margin, 0)


if __name__ == "__main__":
    unittest.main()
