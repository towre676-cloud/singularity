"""Exact r-robust coverage: oracle agreement, erasure lemma and witnesses."""
from fractions import Fraction
from itertools import combinations
import random
import unittest

from singularity.robust_coverage import (
    check_robust_witness, coverage_problem, erasure_tolerance, exhaustive_robust_panel,
    fixed_panel, greedy_robust_panel, is_robust, minimum_robust_panel, random_panels,
    robust_witness, survives_erasures,
)


def table(rows):
    return [[bool(v) for v in row] for row in rows]


class RobustCoverageTests(unittest.TestCase):
    def test_single_cover_is_not_robust_and_double_cover_survives_one_loss(self):
        # Probe 0 alone detects both faults, but losing it loses both.
        problem = coverage_problem([1, 1, 1, 1], table([[1, 1], [1, 0], [0, 1], [1, 1]]))
        single = minimum_robust_panel(problem, 1)
        self.assertEqual((single.panel, single.cost), ((0,), 1))
        self.assertFalse(survives_erasures(problem, single.panel, 1))
        double = minimum_robust_panel(problem, 2)
        self.assertEqual((double.panel, double.cost), ((0, 3), 2))
        self.assertTrue(survives_erasures(problem, double.panel, 1))
        self.assertEqual(erasure_tolerance(problem, double.panel), 1)

    def test_greedy_can_be_strictly_worse_under_the_same_requirement(self):
        # Greedy first takes the cheap narrow probe 4, which the optimum never needs.
        costs = [4, 2, 4, 2, 1]
        rows = table([[1, 1, 1], [1, 0, 0], [1, 0, 0], [1, 1, 1], [0, 1, 0]])
        problem = coverage_problem(costs, rows)
        exact, greedy = minimum_robust_panel(problem, 2), greedy_robust_panel(problem, 2)
        self.assertEqual((exact.panel, exact.cost, greedy.cost), ((0, 3), 6, 7))
        self.assertGreater(greedy.cost, exact.cost)
        self.assertTrue(is_robust(problem, greedy.panel, 2))

    def test_infeasible_requirement_names_deficient_distinctions(self):
        problem = coverage_problem([1, 1], table([[1, 0], [1, 1]]))
        result = minimum_robust_panel(problem, 2)
        self.assertFalse(result.feasible)
        self.assertEqual(result.deficient, (1,))
        self.assertFalse(exhaustive_robust_panel(problem, 2).feasible)

    def test_branch_and_bound_matches_independent_exhaustive_oracle(self):
        rng = random.Random(8080)
        for _ in range(150):
            m, k = rng.randint(1, 8), rng.randint(1, 5)
            rows = [[rng.random() < .45 for _ in range(k)] for _ in range(m)]
            costs = [Fraction(rng.randint(0, 6), rng.randint(1, 3)) for _ in range(m)]
            problem = coverage_problem(costs, rows)
            for r in (1, 2, 3):
                exact = minimum_robust_panel(problem, r)
                oracle = exhaustive_robust_panel(problem, r)
                self.assertEqual(exact.feasible, oracle.feasible)
                if exact.feasible:
                    self.assertEqual(exact.cost, oracle.cost)
                    self.assertTrue(is_robust(problem, exact.panel, r))
                    self.assertLessEqual(exact.root_lower_bound, exact.cost)
                    self.assertTrue(survives_erasures(problem, exact.panel, r - 1))
                    greedy = greedy_robust_panel(problem, r)
                    self.assertGreaterEqual(greedy.cost, exact.cost)

    def test_erasure_lemma_against_direct_enumeration(self):
        rng = random.Random(77)
        for _ in range(100):
            m, k = rng.randint(1, 7), rng.randint(1, 4)
            problem = coverage_problem([1] * m, [[rng.random() < .5 for _ in range(k)] for _ in range(m)])
            panel = [e for e in range(m) if rng.random() < .6]
            tolerance = erasure_tolerance(problem, panel)
            for f in range(len(panel) + 1):
                self.assertEqual(survives_erasures(problem, panel, f), f <= tolerance)

    def test_witness_recheck_uses_caller_separation_and_rejects_forgery(self):
        readings = {"a": (0, 5), "b": (3, 0), "c": (4, 4)}
        reference, tolerance = 0, 1
        probes, faults = ["a", "b", "c"], ["f0", "f1"]

        def separates(probe, fault):
            return abs(readings[probe][faults.index(fault)] - reference) > tolerance

        rows = [[separates(p, f) for f in faults] for p in probes]
        problem = coverage_problem([1, 1, 1], rows, probes, faults)
        result = minimum_robust_panel(problem, 2)
        witness = robust_witness(problem, result.panel, 2)
        labels = [probes[e] for e in result.panel]
        self.assertTrue(check_robust_witness(witness, labels, 2, faults, separates))
        forged = [dict(witness[0], separating_probes=["a", "a"]), witness[1]]
        self.assertFalse(check_robust_witness(forged, labels, 2, faults, separates))
        self.assertFalse(check_robust_witness(witness[:1], labels, 2, faults, separates))
        with self.assertRaises(ValueError):
            robust_witness(problem, [2], 2)

    def test_comparators_and_input_validation(self):
        problem = coverage_problem([1, 2, 3], table([[1, 0], [0, 1], [1, 1]]))
        report = fixed_panel(problem, [0, 1], 2)
        self.assertFalse(report["satisfies_requirement"])
        self.assertEqual(report["distinctions_detected"], 2)
        draws = random_panels(problem, 2, 5, 1, seed=3)
        self.assertEqual(len(draws), 5)
        self.assertEqual(draws, random_panels(problem, 2, 5, 1, seed=3))
        with self.assertRaises(TypeError):
            coverage_problem([1.5], [[True]])
        with self.assertRaises(TypeError):
            coverage_problem([1], [[1]])
        with self.assertRaises(ValueError):
            fixed_panel(problem, [0, 0], 1)
        big = coverage_problem([1] * 20, [[True] * 3 for _ in range(20)])
        with self.assertRaises(ValueError):
            exhaustive_robust_panel(big, 1)
        with self.assertRaises(ValueError):
            rows = table([[1, 0, 1, 0], [1, 1, 0, 0], [1, 0, 1, 0], [0, 1, 1, 1], [0, 1, 0, 0],
                          [0, 1, 0, 0], [0, 0, 1, 1], [1, 0, 1, 1], [1, 0, 1, 1], [1, 0, 0, 1]])
            minimum_robust_panel(coverage_problem([4, 6, 3, 6, 7, 4, 5, 2, 7, 9], rows), 2, max_nodes=3)


if __name__ == "__main__":
    unittest.main()
