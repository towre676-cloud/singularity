"""Independent history enumeration and exact algebra replay for Observatory."""

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import json
import random
import unittest

from perfectjet.observatory.series import compile_observable_closure, compile_series


@dataclass(frozen=True)
class System:
    transitions: tuple
    accepting: tuple
    initial: int = 0

    @property
    def n(self):
        return len(self.transitions)

    @property
    def alphabet(self):
        return len(self.transitions[0])


def count_words(system, length, start=0):
    """Enumeration has no recurrence or matrix dependence on the implementation."""
    total = 0
    for word in product(range(system.alphabet), repeat=length):
        state = start
        for action in word:
            state = system.transitions[state][action]
            if state is None:
                break
        total += state is not None and system.accepting[state]
    return total


def iterative_counts(system, length, start=0):
    counts = [0] * system.n
    counts[start] = 1
    out = []
    for _ in range(length):
        out.append(sum(v for v, accepted in zip(counts, system.accepting) if accepted))
        next_counts = [0] * system.n
        for state, count in enumerate(counts):
            for target in system.transitions[state]:
                if target is not None:
                    next_counts[target] += count
        counts = next_counts
    return out


def fibonacci_mod(index, modulus):
    """Independent fast-doubling identity for the remote-index test."""
    if not index:
        return 0, 1
    a, b = fibonacci_mod(index // 2, modulus)
    c = a * (2 * b - a) % modulus
    d = (a * a + b * b) % modulus
    return (d, (c + d) % modulus) if index % 2 else (c, d)


class SeriesTests(unittest.TestCase):
    def test_fibonacci_remote_composite_modulus(self):
        system = System(((0, 1), (0, None)), (True, False))
        series = compile_series(system)
        self.assertEqual(series.recurrence, (1, 1))
        self.assertEqual(series.initial_values, (1, 1))
        self.assertEqual(series.numerator, (1,))
        self.assertEqual(series.denominator, (1, -1, -1))
        self.assertTrue(series.identity_verified)
        index = 10 ** 100 + 12345
        for modulus in (2, 10 ** 9 + 7, 2 ** 32, 360):
            self.assertEqual(series.coefficient(index, modulus), fibonacci_mod(index + 1, modulus)[0])
        self.assertEqual(series.coefficient(100), 573147844013817084101)

    def test_repeated_eigenvalue_is_not_squarefree(self):
        system = System(((0, 1), (1, None)), (True, True))
        series = compile_series(system)
        self.assertEqual(series.recurrence, (2, -1))
        self.assertEqual(series.numerator, (1,))
        self.assertEqual(series.denominator, (1, -2, 1))
        self.assertEqual(series.coefficient(10 ** 100, 10 ** 9 + 7), (10 ** 100 + 1) % (10 ** 9 + 7))
        self.assertEqual(series.coefficients(100), tuple(range(1, 101)))

    def test_nilpotent_and_trailing_zero_denominator(self):
        system = System(((1,), (2,), (None,)), (False, False, True))
        series = compile_series(system)
        self.assertEqual(series.order, 3)
        self.assertEqual(series.recurrence, (0, 0, 0))
        self.assertEqual(series.numerator, (0, 0, 1))
        self.assertEqual(series.denominator, (1,))
        self.assertEqual(series.coefficients(7), (0, 0, 1, 0, 0, 0, 0))
        self.assertEqual(series.coefficient(10 ** 100, 100), 0)

    def test_zero_sequence_and_empty_alphabet(self):
        empty_output = System(((0, 1), (1, 0)), (False, False))
        series = compile_series(empty_output)
        self.assertEqual(series.order, 0)
        self.assertEqual(series.numerator, (0,))
        self.assertEqual(series.denominator, (1,))
        self.assertEqual(series.coefficient(10 ** 100), 0)
        self.assertEqual(series.coefficients(10), (0,) * 10)
        no_actions = compile_series(System(((),), (True,)))
        self.assertEqual(no_actions.coefficients(4), (1, 0, 0, 0))

    def test_actions_to_same_target_keep_multiplicity(self):
        series = compile_series(System(((0, 0, 0),), (True,)))
        self.assertEqual(series.recurrence, (3,))
        self.assertEqual(series.coefficient(80), 3 ** 80)
        self.assertEqual(series.coefficient(10 ** 100, 123456), pow(3, 10 ** 100, 123456))

    def test_every_start_and_random_system_matches_independent_counts(self):
        rng = random.Random(928131)
        for _ in range(36):
            n, alphabet = rng.randrange(1, 7), rng.randrange(1, 4)
            system = System(tuple(tuple(rng.choice([None] + list(range(n))) for _ in range(alphabet))
                                  for _ in range(n)), tuple(bool(rng.randrange(2)) for _ in range(n)))
            for start in range(n):
                series = compile_series(system, start=start)
                self.assertLessEqual(series.order, n)
                self.assertTrue(series.identity_verified)
                expected = iterative_counts(system, 30, start)
                self.assertEqual(series.coefficients(30), tuple(expected))
                for index in range(30):
                    self.assertEqual(series.coefficient(index), expected[index])
                    self.assertEqual(series.coefficient(index, 12), expected[index] % 12)
                for index in range(6):
                    self.assertEqual(series.coefficient(index), count_words(system, index, start))
                # P(z)=Q(z)S(z), including well beyond the compilation prefix.
                for k in range(30):
                    convolution = sum(c * expected[k - j] for j, c in enumerate(series.denominator) if j <= k)
                    self.assertEqual(convolution, series.numerator[k] if k < len(series.numerator) else 0)

    def test_default_modulus_and_json_receipt(self):
        series = compile_series(System(((0, 0),), (True,)), modulus=6)
        self.assertEqual(series.coefficient(50), pow(2, 50, 6))
        self.assertEqual(series.coefficient(50, 7), pow(2, 50, 7))
        self.assertEqual(series.coefficients(5), (1, 2, 4, 2, 4))
        self.assertEqual(json.loads(json.dumps(series.record()))["identity_residual"], [0])

    def test_global_vector_dimension_can_exceed_scalar_denominator_degree(self):
        # A third state contributes a zero eigenmode invisible from start 0.
        system = System(((0, 1), (0, None), (None, None)), (True, False, True))
        series = compile_series(system)
        self.assertEqual(series.order, 3)
        self.assertEqual(len(series.denominator) - 1, 2)
        self.assertEqual(series.numerator, (1,))
        self.assertEqual(series.record()["global_krylov_dimension"], 3)
        self.assertFalse(series.record()["scalar_minimality_claimed"])

    def test_invalid_indices_moduli_and_guard_rejected(self):
        system = System(((0,),), (True,))
        series = compile_series(system)
        for value in (-1, True, 1.0, "2", Fraction(2)):
            with self.assertRaises(ValueError):
                series.coefficient(value)
        for value in (0, 1, -1, True, 2.0):
            with self.assertRaises(ValueError):
                series.coefficient(5, value)
        with self.assertRaises(ValueError):
            compile_series(system, start=1)
        with self.assertRaises(ValueError):
            compile_series(System(((0,), (1,)), (True, False)), max_dimension=1)


class ObservableClosureTests(unittest.TestCase):
    def test_action_closure_is_stronger_than_aggregated_length_closure(self):
        system = System(((0, 1), (0, 2), (1, 0)), (True, False, False))
        series = compile_series(system)
        closure = compile_observable_closure(system)
        self.assertEqual(series.closure_dimension, 2)
        self.assertEqual(closure.dimension, 3)
        self.assertTrue(closure.identity_verified)
        for state in range(system.n):
            for word in product(range(system.alphabet), repeat=5):
                coordinates = closure.state_coordinates(state)
                direct = state
                for action in word:
                    coordinates = closure.step(coordinates, action)
                    direct = system.transitions[direct][action] if direct is not None else None
                self.assertEqual(closure.acceptance(coordinates), int(direct is not None and system.accepting[direct]))

    def test_random_reduced_actions_and_source_words_replay(self):
        rng = random.Random(391)
        for _ in range(24):
            n = rng.randrange(1, 8)
            system = System(tuple(tuple(rng.choice([None] + list(range(n))) for _ in range(2)) for _ in range(n)),
                            tuple(bool(rng.randrange(2)) for _ in range(n)))
            extra = tuple(Fraction(s - 1, 3) for s in range(n))
            closure = compile_observable_closure(system, observations=[extra])
            seeds = [system.accepting, extra]
            self.assertLessEqual(closure.dimension, n)
            for row, (seed, word) in zip(closure.basis, closure.basis_sources):
                for state in range(n):
                    direct = state
                    for action in word:
                        direct = system.transitions[direct][action] if direct is not None else None
                    self.assertEqual(row[state], 0 if direct is None else seeds[seed][direct])
            for state in range(n):
                coordinate = closure.state_coordinates(state)
                self.assertEqual(closure.acceptance(coordinate), int(system.accepting[state]))
                for action in range(2):
                    target = system.transitions[state][action]
                    expected = closure.state_coordinates(target) if target is not None else (0,) * closure.dimension
                    self.assertEqual(closure.step(coordinate, action), expected)
            for row in seeds:
                coordinates = closure.coordinates(row)
                self.assertEqual(tuple(sum(c * basis[s] for c, basis in zip(coordinates, closure.basis)) for s in range(n)), row)
            self.assertEqual(closure.observation_coordinates, tuple(closure.coordinates(row) for row in seeds))
            self.assertEqual(closure.record()["identity_residual_nonzero_entries"], 0)
            json.dumps(closure.record())

    def test_zero_closure_and_coordinate_rejection(self):
        closure = compile_observable_closure(System(((0,), (1,)), (False, False)))
        self.assertEqual(closure.dimension, 0)
        self.assertEqual(closure.state_coordinates(1), ())
        self.assertEqual(closure.step((), 0), ())
        self.assertEqual(closure.acceptance(()), 0)
        with self.assertRaises(ValueError):
            closure.coordinates((1, 0))
        with self.assertRaises(ValueError):
            closure.state_coordinates(-1)
        with self.assertRaises(ValueError):
            closure.step((), 1)


if __name__ == "__main__":
    unittest.main()
