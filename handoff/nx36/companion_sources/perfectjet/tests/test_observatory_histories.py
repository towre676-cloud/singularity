import itertools
import math
import random
import unittest
from collections import Counter
from dataclasses import replace

from perfectjet.observatory import FiniteSystem, HistoryPopulation, compile_system, replay_compilation
from perfectjet.observatory.histories import PopulationLimitError
from perfectjet.observatory.model import labels_equal, scalar_key
from perfectjet.semantics import PartialMachine


def enumerate_words(system, horizon, budget=None, start=None, trace=None):
    start = system.initial if start is None else start
    trace = [None] * (horizon + 1) if trace is None else trace
    answer = []
    for word in itertools.product(range(system.alphabet), repeat=horizon):
        state, cost = start, 0
        if trace[0] is not None and not labels_equal(trace[0], system.observations[state]):
            continue
        for time, action in enumerate(word, 1):
            cost += system.costs[action]
            state = system.transitions[state][action]
            if state is None or (trace[time] is not None and not labels_equal(trace[time], system.observations[state])):
                break
        else:
            if system.accepting[state] and (budget is None or cost <= budget):
                answer.append((word, cost))
    return answer


class FiniteSystemTests(unittest.TestCase):
    def example(self):
        return {"states": ["cold", "hot"], "actions": [{"name": "heat", "cost": 2},
                                                        {"name": "wait", "cost": 1}],
                "transitions": [[1, 0], [None, 0]], "observations": [False, True]}

    def test_defaults_roundtrip_and_step(self):
        data = self.example()
        model = FiniteSystem.from_dict(data)
        self.assertEqual((model.n, model.alphabet), (2, 2))
        self.assertEqual(model.targets, model.observations)
        self.assertEqual(model.accepting, (True, True))
        self.assertEqual(model.step(0, "heat"), 1)
        self.assertIsNone(model.step(1, 0))
        self.assertEqual(FiniteSystem.from_dict(model.to_dict()), model)
        del data["states"]
        data["actions"], data["costs"] = ["heat", "wait"], [2, 1]
        self.assertEqual(FiniteSystem.from_dict(data).states, ("s0", "s1"))

    def test_invalid_systems(self):
        bad = [dict(initial=True), dict(initial=0.0), dict(initial=2),
               dict(costs=[1.0, 1], actions=["a", "b"]),
               dict(costs=[True, 1], actions=["a", "b"]),
               dict(actions=[{"name": "a", "cost": 0}, {"name": "b", "cost": 1}]),
               dict(transitions=[[True, 0], [None, 0]]),
               dict(transitions=[[1.0, 0], [None, 0]]), dict(transitions=[[2, 0], [None, 0]]),
               dict(transitions=[[1], [None, 0]]), dict(observations=[{}, 0]),
               dict(observations=[float("nan"), 0]), dict(targets=[[1], 0]),
               dict(accepting=[0, 1]), dict(states=["x", "x"]),
               dict(actions=["x", "x"])]
        for override in bad:
            with self.subTest(override=override), self.assertRaises(ValueError):
                FiniteSystem.from_dict(self.example() | override)

    def test_distinct_json_scalar_types(self):
        model = FiniteSystem.from_dict({"actions": ["stay"], "transitions": [[0], [1], [2]],
                                       "observations": [True, 1, 1.0]})
        self.assertEqual(compile_system(model).system.n, 3)
        self.assertEqual(HistoryPopulation(model, 0, start=0, trace=[1]).count(), 0)

    def test_compiler_independent_pair_search_and_population_transport(self):
        rng = random.Random(1729)
        for trial in range(90):
            n, actions = rng.randint(1, 8), rng.randint(0, 4)
            model = FiniteSystem.from_dict({
                "actions": [f"a{i}" for i in range(actions)],
                "costs": [rng.randint(1, 3) for _ in range(actions)],
                "transitions": [[rng.choice([None] + list(range(n))) for _ in range(actions)] for _ in range(n)],
                "observations": [rng.randrange(2) for _ in range(n)],
                "targets": [rng.randrange(2) for _ in range(n)],
                "accepting": [bool(rng.randrange(2)) for _ in range(n)],
                "initial": rng.randrange(n)})
            result = compile_system(model)
            observed = [(scalar_key(model.observations[s]), scalar_key(model.targets[s]), model.accepting[s])
                        for s in range(n)]
            independent, old_mapping, _ = PartialMachine(observed, model.transitions).quotient()
            self.assertEqual(result.system.n, len(independent.observations))
            for left in range(n):
                for right in range(n):
                    self.assertEqual(result.mapping[left] == result.mapping[right],
                                     old_mapping[left] == old_mapping[right])
            self.assertTrue(replay_compilation(model, result))
            for start in range(n):
                population = HistoryPopulation(model, 4, budget=8, start=start)
                reduced = HistoryPopulation(result.system, 4, budget=8, start=result.mapping[start])
                self.assertEqual(population.count(), reduced.count())
                if population.count():
                    rank = rng.randrange(population.count())
                    self.assertEqual(population.unrank(rank), reduced.unrank(rank))

    def test_compiler_large_redundant_model_and_receipt_tampering(self):
        n = 1200
        model = FiniteSystem.from_dict({"actions": ["advance", "reset"],
                                       "transitions": [[(s + 1) % n, 0] for s in range(n)],
                                       "observations": [s % 12 for s in range(n)]})
        result = compile_system(model)
        self.assertEqual(result.system.n, 12)
        self.assertLess(result.metrics["predecessor_visits"], n * 20)
        forged = replace(result, mapping=tuple(0 for _ in range(n)))
        self.assertFalse(replay_compilation(model, forged))

    def test_compiler_long_hidden_distinguishing_chain(self):
        # The only sensor distinction sits at the remote terminal state.
        # Each preceding distance must be split without scanning state pairs.
        n = 1500
        model = FiniteSystem.from_dict({"actions": ["advance", "reset"],
                                       "transitions": [[min(s + 1, n - 1), 0] for s in range(n)],
                                       "observations": [0] * (n - 1) + [1]})
        result = compile_system(model)
        self.assertEqual(result.system.n, n)
        self.assertEqual(result.metrics["splits"], n - 2)
        self.assertLess(result.metrics["predecessor_visits"], 5 * n)
        self.assertTrue(replay_compilation(model, result))


class HistoryPopulationTests(unittest.TestCase):
    def test_random_exhaustive_populations(self):
        rng = random.Random(9871)
        for trial in range(150):
            n, actions, horizon = rng.randint(1, 6), rng.randint(0, 3), rng.randint(0, 5)
            model = FiniteSystem.from_dict({
                "actions": [{"name": f"move{i}", "cost": rng.randint(1, 4)} for i in range(actions)],
                "transitions": [[rng.choice([None] + list(range(n))) for _ in range(actions)] for _ in range(n)],
                "observations": [rng.randrange(3) for _ in range(n)],
                "accepting": [bool(rng.randrange(2)) for _ in range(n)]})
            trace = [rng.choice([None, None, 0, 1, 2]) for _ in range(horizon + 1)]
            budget, start = rng.choice([None, 0, 2, 5, 9, 20]), rng.randrange(n)
            population = HistoryPopulation(model, horizon, budget, start, trace)
            expected = enumerate_words(model, horizon, budget, start, trace)
            with self.subTest(trial=trial):
                self.assertEqual(population.count(), len(expected))
                self.assertEqual(population.cost_histogram(), dict(sorted(Counter(cost for _, cost in expected).items())))
                self.assertEqual(population.minimum_cost(), min((cost for _, cost in expected), default=None))
                self.assertEqual(population.cost_histogram(), population.cost_histogram())
                for rank, (word, _) in enumerate(expected):
                    self.assertEqual(population.rank(word), rank)
                    self.assertEqual(population.rank([model.actions[a] for a in word]), rank)
                    self.assertEqual(population.unrank(rank), word)
                if expected:
                    self.assertIn(population.sample(rng), [word for word, _ in expected])
                else:
                    with self.assertRaises(ValueError):
                        population.sample(rng)

    def test_huge_population_costs_and_full_horizon_without_recursion(self):
        model = FiniteSystem.from_dict({"actions": [{"name": "left", "cost": 1},
                                                    {"name": "right", "cost": 2}],
                                       "transitions": [[0, 0]], "observations": ["quiet"]})
        population = HistoryPopulation(model, 200, budget=250)
        expected = sum(math.comb(200, k) for k in range(51))
        self.assertEqual(population.count(), expected)
        self.assertEqual(population.minimum_cost(), 200)
        self.assertEqual(population.cost_histogram(), {200+k: math.comb(200, k) for k in range(51)})
        rank = expected // 2 + 12345
        self.assertEqual(population.rank(population.unrank(rank)), rank)
        self.assertLess(population.metrics["dynamic_states"], 11000)
        full = HistoryPopulation(model, 512)
        self.assertEqual(full.count(), 2 ** 512)
        self.assertEqual(full.unrank(2 ** 512 - 1), (1,) * 512)
        self.assertLess(full.metrics["dynamic_states"], 520)

    def test_partial_trace_and_terminal_acceptance(self):
        model = FiniteSystem.from_dict({"actions": ["flip", "stay"],
                                       "transitions": [[1, 0], [0, None]],
                                       "observations": ["off", "on"], "accepting": [True, False]})
        population = HistoryPopulation(model, 2, trace=["off", "on", "off"])
        self.assertEqual(population.count(), 1)
        self.assertEqual(population.unrank(0), (0, 0))
        with self.assertRaises(ValueError):
            population.rank((1, 1))
        self.assertEqual(HistoryPopulation(model, 0).unrank(0), ())
        self.assertEqual(HistoryPopulation(model, 0).rank(()), 0)
        self.assertEqual(HistoryPopulation(model, 0, start=1).count(), 0)

    def test_bad_queries_and_resource_limit(self):
        model = FiniteSystem.from_dict({"actions": ["a", "b"], "costs": [1, 2],
                                       "transitions": [[0, 0]], "observations": ["x"]})
        for args in (dict(horizon=True), dict(horizon=1.0), dict(horizon=-1), dict(horizon=513),
                     dict(horizon=2, budget=True), dict(horizon=2, budget=2.0), dict(horizon=2, budget=-1),
                     dict(horizon=2, start=True), dict(horizon=2, start=1), dict(horizon=2, trace=[None])):
            with self.subTest(args=args), self.assertRaises(ValueError):
                HistoryPopulation(model, **args)
        population = HistoryPopulation(model, 1)
        for word in ([True], [0.0], [2], [], "a"):
            with self.assertRaises(ValueError):
                population.rank(word)
        for rank in (True, 0.0, -1, 2):
            with self.assertRaises(ValueError):
                population.unrank(rank)
        population = HistoryPopulation(model, 10, budget=15)
        population.MAX_DP_STATES = 3
        with self.assertRaises(PopulationLimitError):
            population.count()


if __name__ == "__main__":
    unittest.main()
