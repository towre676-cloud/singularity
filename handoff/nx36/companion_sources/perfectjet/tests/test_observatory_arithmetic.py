"""Exact arithmetic replay, orbit completeness, and history-count crosschecks."""
import itertools
from math import comb
import unittest

from perfectjet.quadratic import fundamental_unit
from perfectjet.observatory.arithmetic import (
    ArithmeticOrbitLimitError, arithmetic_receipt, pell_point, pell_residue_system,
)
from perfectjet.observatory.histories import HistoryPopulation


def mul(left, right, D, modulus=None):
    x = left[0]*right[0] + D*left[1]*right[1]
    y = left[0]*right[1] + left[1]*right[0]
    return (x, y) if modulus is None else (x % modulus, y % modulus)


def matrix_power_action(matrix, vector, exponent, modulus):
    def mm(left, right):
        return [[sum(left[i][k]*right[k][j] for k in range(2)) % modulus for j in range(2)] for i in range(2)]
    result = [[1, 0], [0, 1]]
    while exponent:
        if exponent % 2:
            result = mm(result, matrix)
        matrix = mm(matrix, matrix)
        exponent //= 2
    return tuple(sum(result[i][j]*vector[j] for j in range(2)) % modulus for i in range(2))


class PellArithmeticTests(unittest.TestCase):
    def test_exact_positive_negative_integer_points_and_recurrence(self):
        for D in (2, 3, 5, 6, 7, 13):
            unit = fundamental_unit(D)
            a, b = unit
            for seed in ((1, 0), (2, 1), (-3, 2)):
                norm = seed[0]**2-D*seed[1]**2
                for sign in (1, -1):
                    current = seed
                    points = []
                    step = (a, sign*b)
                    for n in range(26):
                        fast = pell_point(D, unit, seed, sign*n)
                        self.assertEqual(fast, current)
                        self.assertEqual(fast[0]**2-D*fast[1]**2, norm)
                        points.append(fast)
                        current = mul(current, step, D)
                    for n in range(24):
                        self.assertEqual(points[n+2], tuple(2*a*points[n+1][j]-points[n][j] for j in range(2)))

    def test_small_modular_orbits_are_complete_and_have_inverse_transport(self):
        for D in (2, 3, 5, 7, 13):
            unit = fundamental_unit(D)
            for modulus in range(1, 21):
                for seed in ((1, 0), (2, 1), (0, 0)):
                    system, record = pell_residue_system(D, unit, seed, modulus)
                    self.assertLessEqual(system.n, modulus**2)
                    self.assertTrue(all(record["certificate"].values()))
                    self.assertEqual(record["preperiod"], 0)
                    self.assertFalse(record["completeness"]["covers_all_integer_norm_solutions"])
                    residues = {(item["x"], item["y"]) for item in record["orbit_index_classes"]}
                    self.assertEqual(len(residues), system.n)
                    for n in range(-system.n, 2*system.n):
                        point = pell_point(D, unit, seed, n, modulus)
                        item = record["orbit_index_classes"][n % system.n]
                        self.assertEqual(point, (item["x"], item["y"]))
                    for state in range(system.n):
                        self.assertEqual(system.step(system.step(state, "advance"), "retreat"), state)

    def test_huge_index_agrees_with_independent_matrix_powering(self):
        exponent = 10**100
        D, unit, seed, modulus = 2, (3, 2), (7, -4), 1_000_000_007
        self.assertEqual(pell_point(D, unit, seed, exponent, modulus),
                         matrix_power_action([[3, 4], [2, 3]], seed, exponent, modulus))
        self.assertEqual(pell_point(D, unit, seed, -exponent, modulus),
                         matrix_power_action([[3, -4], [-2, 3]], seed, exponent, modulus))

    def test_nonfundamental_generator_is_reported_honestly(self):
        _, record = pell_residue_system(2, (17, 12), (1, 0), 7)
        self.assertFalse(record["unit"]["is_fundamental"])
        self.assertEqual(record["unit"]["fundamental_unit"], [3, 2])
        self.assertIsNotNone(record["completeness"]["generator_warning"])
        self.assertFalse(record["completeness"]["covers_all_integer_norm_solutions"])

    def test_symbolic_transport_and_characteristic_identity(self):
        _, record = pell_residue_system(2, (3, 2), (2, 1), 35)
        self.assertEqual(record["original_norm"], 2)
        self.assertEqual(record["symbolic_norm_coefficients_x2_xy_y2"], [1, 0, -2])
        M, inverse = record["forward_matrix"], record["inverse_matrix"]
        for i, j in itertools.product(range(2), repeat=2):
            self.assertEqual(sum(M[i][k]*inverse[k][j] for k in range(2)), int(i == j))
            self.assertEqual(sum(M[i][k]*M[k][j] for k in range(2))-6*M[i][j]+int(i == j), 0)

    def test_residue_filter_and_history_population_match_binomial_fibers(self):
        system, record = pell_residue_system(2, (3, 2), (1, 0), 35, accepted_x=[36, -34])
        self.assertEqual(record["accepted_x"], [1])
        for horizon in range(31):
            expected = sum(comb(horizon, k) for k in range(horizon+1)
                           if system.accepting[(2*k-horizon) % system.n])
            self.assertEqual(HistoryPopulation(system, horizon).count(), expected)
        empty, _ = pell_residue_system(2, (3, 2), (1, 0), 35, accepted_x=[])
        self.assertEqual(HistoryPopulation(empty, 20).count(), 0)

    def test_receipt_replays_and_contains_no_all_solution_claim(self):
        receipt = arithmetic_receipt()
        self.assertTrue(receipt["integer_replay"]["all_equal"])
        self.assertTrue(receipt["remote_query"]["norm_replayed"])
        self.assertTrue(receipt["remote_query"]["cycle_transport_replayed"])
        self.assertTrue(receipt["history_query"]["independent_count_agrees"])
        self.assertFalse(receipt["transport"]["completeness"]["covers_all_integer_norm_solutions"])

    def test_validation_and_explicit_limits(self):
        invalid = [
            (True, (3, 2), (1, 0), 35), (4, (3, 2), (1, 0), 35),
            (2, (1, 0), (1, 0), 35), (2, (3, 1), (1, 0), 35),
            (2, (3, 2), (True, 0), 35), (2, (3, 2), (1, 0), 0),
        ]
        for args in invalid:
            with self.assertRaises(ValueError):
                pell_residue_system(*args)
        with self.assertRaises(ArithmeticOrbitLimitError):
            pell_residue_system(2, (3, 2), (1, 0), 35, max_states=1)
        with self.assertRaises(ArithmeticOrbitLimitError):
            pell_point(2, (3, 2), (1, 0), 10**100)
        self.assertEqual(pell_point(2, (3, 2), (0, 0), 10**100), (0, 0))
        with self.assertRaises(ValueError):
            pell_residue_system(2, (3, 2), (1, 0), 35, accepted_x=True)


if __name__ == "__main__":
    unittest.main()
