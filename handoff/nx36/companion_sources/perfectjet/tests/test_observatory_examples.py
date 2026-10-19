"""Independent arithmetic and information-flow checks for the laboratories."""
import importlib.util
import itertools
import json
from pathlib import Path
import unittest

from perfectjet.observatory.examples import (
    arithmetic_interferometer, example_catalog, interferometer_spec,
    irreversible_machine, protocol_machine,
)
from perfectjet.observatory.experiments import adaptive_experiment, pair_experiment
from perfectjet.observatory.histories import HistoryPopulation
from perfectjet.observatory.model import compile_system

ROOT = Path(__file__).resolve().parents[1]


class ObservatoryExampleTests(unittest.TestCase):
    def test_prime_input_is_checked(self):
        for bad in (True, 2, 4, 9, 1, -7, 5.0):
            with self.assertRaises(ValueError):
                arithmetic_interferometer(bad)

    def test_fixture_sources_match_generated_models(self):
        for name, example in example_catalog().items():
            actual = json.loads((ROOT / "examples/observatory" / f"{name}.json").read_text())
            self.assertEqual(actual, example["model"])

    def test_absolute_lift_partition_is_exact_translation_and_sign_relation(self):
        p = 13
        original = arithmetic_interferometer(p, lifted=True)
        result = compile_system(original)
        self.assertEqual((original.n, result.system.n), (2197, 85))
        by_formula = {}
        by_compiler = {}
        for i, name in enumerate(original.states):
            x, y, z = map(int, name.split(","))
            u, v = (x-z) % p, (y-z) % p
            key = min((u, v), ((-u) % p, (-v) % p))
            block = result.mapping[i]
            self.assertEqual(by_formula.setdefault(key, block), block)
            self.assertEqual(by_compiler.setdefault(block, key), key)
        self.assertEqual(sorted(map(len, result.blocks)), [13] + [26] * 84)

    def test_action_order_has_observable_effect(self):
        model = arithmetic_interferometer(13)
        first_a = model.step(model.initial, "A")
        first_b = model.step(model.initial, "B")
        ab = model.step(first_a, "B")
        ba = model.step(first_b, "A")
        self.assertEqual((model.observations[ab], model.observations[ba]), (2, 5))

    def test_safe_history_population_matches_independent_word_enumeration(self):
        p = 5
        model = arithmetic_interferometer(p)
        for length in range(9):
            accepted = []
            for word in itertools.product((0, 1), repeat=length):
                u, v = 1, 0
                for action in word:
                    u, v = (((u+v) % p, v) if action == 0 else (u, (u+v) % p))
                    if (u*u+v*v) % p == 0:
                        break
                else:
                    accepted.append(word)
            population = HistoryPopulation(model, length)
            self.assertEqual(population.count(), len(accepted))
            self.assertEqual([population.unrank(i) for i in range(len(accepted))], accepted)

    def test_recorded_p13_counts_are_not_raw_binary_word_counts(self):
        model = compile_system(arithmetic_interferometer(13)).system
        for horizon, expected in ((10, 162), (20, 20010), (40, 311989738), (80, 76712911076419434)):
            self.assertEqual(HistoryPopulation(model, horizon).count(), expected)
            self.assertLess(expected, 2**horizon)

    def test_adaptive_lab_requires_a_contingent_second_action(self):
        model = protocol_machine()
        result = adaptive_experiment(model, belief=[0, 1, 2, 3])
        self.assertEqual((result["status"], result["worst_cost"]), ("finite", 2))
        actions = {node.get("action") for node in result["nodes"] if node["kind"] == "action"}
        self.assertEqual(actions, {"route", "inspect alpha", "inspect beta"})
        # The standalone benchmark's exhaustive monitor search preserves
        # observation history, including branches that become undefined.
        path = ROOT / "scripts/benchmark_observatory.py"
        spec = importlib.util.spec_from_file_location("observatory_benchmark", path)
        benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(benchmark)
        preset = benchmark.preset_identification_search(model, [0, 1, 2, 3])
        self.assertEqual(preset["status"], "infinite")
        self.assertLess(preset["explored_monitors"], 50)

    def test_irreversible_button_really_coalesces_distinct_hidden_targets(self):
        model = irreversible_machine()
        best = pair_experiment(model, 0, 1)
        self.assertEqual((best["status"], best["cost"], best["word"]), ("finite", 3, ["inspect"]))
        self.assertNotEqual(model.targets[0], model.targets[1])
        self.assertEqual(model.step(0, "reset"), model.step(1, "reset"))
        # Determinism then makes every continuation identical for both origins.
        for word in itertools.product(range(model.alphabet), repeat=6):
            left, right = model.step(0, "reset"), model.step(1, "reset")
            for action in word:
                left, right = model.step(left, action), model.step(right, action)
                self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
