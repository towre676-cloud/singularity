"""Independent small exhaustive checks for active experiment synthesis."""
import itertools
import random
import unittest
from functools import lru_cache

from perfectjet.observatory.experiments import adaptive_experiment, pair_experiment
from perfectjet.observatory.model import FiniteSystem, scalar_key


def make_system(rows, observations, targets=None, costs=None):
    return FiniteSystem(
        states=tuple(f"s{i}" for i in range(len(rows))),
        actions=tuple(f"a{i}" for i in range(len(rows[0]))),
        costs=tuple(costs or [1] * len(rows[0])),
        transitions=tuple(tuple(row) for row in rows),
        observations=tuple(observations),
        targets=tuple(observations if targets is None else targets),
        accepting=(True,) * len(rows),
    )


def bounded_tree_possible(system, initial, budget, prefix=()):
    """Brute-force the finite budget game, independently of retrograde solving."""
    def observed(current):
        return ("terminal",) if current is None else ("live", scalar_key(system.observations[current]))

    def partition(candidates):
        groups = {}
        for origin, current in candidates:
            groups.setdefault(observed(current), []).append((origin, current))
        return tuple(tuple(group) for group in groups.values())

    @lru_cache(None)
    def possible(candidates, available):
        if len({scalar_key(system.targets[origin]) for origin, _ in candidates}) == 1:
            return True
        for action, cost in enumerate(system.costs):
            if cost > available:
                continue
            moved = tuple((origin, None if current is None else system.transitions[current][action])
                          for origin, current in candidates)
            if all(possible(group, available - cost) for group in partition(moved)):
                return True
        return False

    groups = partition(tuple((i, i) for i in initial))
    for action in prefix:
        groups = tuple(nxt for group in groups for nxt in partition(tuple(
            (origin, None if current is None else system.transitions[current][action])
            for origin, current in group)))
    return all(possible(group, budget) for group in groups)


class PairExperimentTests(unittest.TestCase):
    def test_minimum_cost_can_use_more_actions(self):
        system = make_system([(2, 4), (3, 3), (4, 4), (3, 3), (4, 4)],
                             [0, 0, 0, 0, 1], ["x", "y", "z", "z", "z"], [1, 5])
        result = pair_experiment(system, "s0", "s1")
        self.assertEqual(result["status"], "finite")
        self.assertEqual(result["cost"], 2)
        self.assertEqual(result["word"], ["a0", "a0"])

    def test_undefined_is_distinct_from_live_null(self):
        system = make_system([(None,), (1,)], [None, None], [0, 1])
        result = pair_experiment(system, 0, 1)
        self.assertEqual(result["cost"], 1)
        self.assertEqual(result["terminal_observations"], [
            {"kind": "undefined"}, {"kind": "live", "value": None}])

    def test_free_sensor_keeps_scalar_types_distinct(self):
        system = make_system([(0,), (1,)], [True, 1], ["A", "B"])
        self.assertEqual(pair_experiment(system, 0, 1)["cost"], 0)


class AdaptiveExperimentTests(unittest.TestCase):
    def test_noninjective_action_does_not_erase_initial_target(self):
        system = make_system([(2,), (2,), (2,)], [0, 0, 1], ["A", "B", "C"])
        result = adaptive_experiment(system, [0, 1])
        self.assertEqual(result["status"], "infinite")
        self.assertEqual(result["impossible_witness"]["kind"], "closed_ambiguity_region")
        self.assertFalse(bounded_tree_possible(system, (0, 1), 5))

    def test_partial_action_preserves_unresolved_terminal_candidates(self):
        system = make_system([(None,), (None,), (2,)], [0, 0, 0], ["A", "B", "C"])
        self.assertEqual(adaptive_experiment(system, [0, 1])["status"], "infinite")
        system = make_system([(None,), (1,)], [0, 0], ["A", "B"])
        self.assertEqual(adaptive_experiment(system)["worst_cost"], 1)

    def test_contingent_probe_survives_destructive_wrong_branch(self):
        rows = [
            (4, 10, 10), (5, 10, 10), (6, 10, 10), (7, 10, 10),
            (4, 8, 10), (5, 9, 10), (6, 10, 8), (7, 10, 9),
            (8, 8, 8), (9, 9, 9), (10, 10, 10),
        ]
        system = make_system(rows, [0, 0, 0, 0, "left", "left", "right", "right", "A", "B", "lost"],
                             ["A", "B", "A", "B"] + ["irrelevant"] * 7)
        result = adaptive_experiment(system, [0, 1, 2, 3])
        self.assertEqual(result["status"], "finite")
        self.assertEqual(result["worst_cost"], 2)
        nodes = {node["id"]: node for node in result["nodes"]}
        root = nodes[result["tree"]["branches"][0]["next"]]
        self.assertEqual(root["action"], "a0")
        self.assertEqual({nodes[branch["next"]]["action"] for branch in root["branches"]}, {"a1", "a2"})
        for node in result["nodes"]:
            if node["kind"] == "action":
                self.assertEqual(node["worst_cost"], node["cost"] + max(nodes[b["next"]]["worst_cost"] for b in node["branches"]))

    def test_prefix_reset_destroys_information_and_inspection_retains_it(self):
        system = FiniteSystem(
            states=("A", "B", "blank", "read_B"), actions=("reset", "inspect"),
            costs=(1, 3), transitions=((2, 2), (2, 3), (2, 2), (2, 3)),
            observations=("unread", "unread", "blank", "B"),
            targets=("A", "B", "irrelevant", "irrelevant"), accepting=(True,) * 4,
        )
        baseline = adaptive_experiment(system, [0, 1])
        self.assertEqual(baseline["worst_cost"], 3)
        self.assertEqual(baseline["prefix"], [])
        self.assertEqual(baseline["worst_remaining_cost"], 3)
        reset = adaptive_experiment(system, [0, 1], prefix=["reset"])
        self.assertEqual(reset["status"], "infinite")
        self.assertEqual(reset["prefix_cost"], 1)
        inspected = adaptive_experiment(system, [0, 1], prefix=["inspect"])
        self.assertEqual(inspected["status"], "finite")
        self.assertEqual(inspected["worst_remaining_cost"], 0)
        self.assertEqual(inspected["worst_cost"], 3)
        self.assertEqual(inspected["prefix"], ["inspect"])
        # A later reset cannot erase an observation already recorded.
        inspected_reset = adaptive_experiment(system, [0, 1], prefix=["inspect", "reset"])
        self.assertEqual(inspected_reset["worst_remaining_cost"], 0)
        self.assertEqual(inspected_reset["worst_cost"], 4)
        histories = [branch["observations"] for branch in inspected_reset["tree"]["branches"]]
        self.assertEqual(len(histories), 2)
        self.assertNotEqual(histories[0][1], histories[1][1])
        self.assertEqual(histories[0][-1], histories[1][-1])

    def test_prefix_preserves_distinct_initial_sensor_readings(self):
        system = make_system([(2,), (2,), (2,)], [0, 1, 2], ["A", "B", "C"])
        result = adaptive_experiment(system, [0, 1], prefix=[0])
        self.assertEqual(result["status"], "finite")
        self.assertEqual(result["worst_remaining_cost"], 0)
        self.assertEqual(result["worst_cost"], 1)
        self.assertEqual(len(result["tree"]["branches"]), 2)
        self.assertNotIn("observations", adaptive_experiment(system, [0, 1])["tree"]["branches"][0])
        self.assertEqual(adaptive_experiment(system, [0, 1], max_beliefs=1, prefix=[0])["status"], "limit")
        with self.assertRaises(ValueError):
            adaptive_experiment(system, prefix="a0")
        with self.assertRaises(ValueError):
            adaptive_experiment(system, prefix=[0] * 513)

    def test_random_prefix_games_against_independent_budget_tree(self):
        rng = random.Random(91482)
        for _ in range(120):
            system = make_system(
                [tuple(rng.choice((None, 0, 1, 2)) for _ in range(2)) for _ in range(3)],
                [rng.randrange(2) for _ in range(3)], ["A", "B", "C"], [1, 2])
            prefix = tuple(rng.randrange(2) for _ in range(rng.randrange(4)))
            result = adaptive_experiment(system, prefix=prefix)
            if result["status"] == "finite":
                remaining = result["worst_remaining_cost"]
                self.assertEqual(result["worst_cost"], sum(system.costs[a] for a in prefix) + remaining)
                self.assertTrue(bounded_tree_possible(system, (0, 1, 2), remaining, prefix))
                if remaining:
                    self.assertFalse(bounded_tree_possible(system, (0, 1, 2), remaining - 1, prefix))
            else:
                self.assertFalse(bounded_tree_possible(system, (0, 1, 2), 2*result["explored_beliefs"], prefix))

    def test_resource_limit_never_claims_impossibility(self):
        system = make_system([(1,), (0,)], [0, 0], ["A", "B"])
        result = adaptive_experiment(system, max_beliefs=1)
        self.assertEqual(result["status"], "limit")
        self.assertIsNone(result["worst_cost"])
        with self.assertRaises(ValueError):
            adaptive_experiment(system, [])

    def test_all_two_state_partial_machines_against_pair_search(self):
        # Every transition table for two actions and two states, including
        # undefined transitions; every binary sensor assignment and both costs.
        for flat in itertools.product((None, 0, 1), repeat=4):
            rows = [flat[:2], flat[2:]]
            for observations in itertools.product((0, 1), repeat=2):
                for costs in ((1, 1), (1, 2)):
                    system = make_system(rows, observations, ["A", "B"], costs)
                    pair = pair_experiment(system, 0, 1)
                    adaptive = adaptive_experiment(system)
                    self.assertEqual(adaptive["status"], pair["status"], (rows, observations, costs))
                    self.assertEqual(adaptive["worst_cost"], pair["cost"], (rows, observations, costs))

    def test_three_state_random_games_against_budget_tree_enumeration(self):
        rng = random.Random(18473)
        for _ in range(120):
            system = make_system(
                [tuple(rng.choice((None, 0, 1, 2)) for _ in range(2)) for _ in range(3)],
                [rng.randrange(2) for _ in range(3)],
                ["A", "B", "C"], [1, 2],
            )
            result = adaptive_experiment(system)
            # A finite optimal policy visits no belief twice along a branch.
            bound = 2 * result["explored_beliefs"]
            if result["status"] == "finite":
                value = result["worst_cost"]
                self.assertTrue(bounded_tree_possible(system, (0, 1, 2), value))
                if value:
                    self.assertFalse(bounded_tree_possible(system, (0, 1, 2), value - 1))
            else:
                self.assertFalse(bounded_tree_possible(system, (0, 1, 2), bound))


if __name__ == "__main__":
    unittest.main()
