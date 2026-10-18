"""Regression suite for the exact observation-closure engine.

Independent oracles enumerate words and multiply matrices directly; they do
not call observable_closure, experiment or _echelon.
"""
import dataclasses
import json
import random
import unittest
from fractions import Fraction as F
from itertools import product

from singularity.observability import (
    ClosureCertificate, Experiment, OperatorSystem, apply_word, certificate_bundle,
    experiment, future_equivalent, minimum_distinguishing_experiment, observable_closure,
    quotient_output, quotient_state, quotient_update, replay_bundle, row_times_matrix,
    verify_certificate,
)


# ---------------------------------------------------------------- oracles
def mat_vec(m, v):
    return tuple(sum((a * b for a, b in zip(row, v)), F(0)) for row in m)


def vec_mat(v, m, n):
    return tuple(sum((v[k] * m[k][j] for k in range(len(v))), F(0)) for j in range(n))


def oracle_row(system, j, word):
    """L_j M_{i_m} ... M_{i_1}: apply the letters right to left on the row."""
    row = system.observations[j]
    for i in reversed(word):
        row = vec_mat(row, system.operators[i], system.dimension)
    return row


def oracle_rank(rows, n):
    a = [list(r) for r in rows]
    rank = 0
    for c in range(n):
        k = next((i for i in range(rank, len(a)) if a[i][c]), None)
        if k is None:
            continue
        a[rank], a[k] = a[k], a[rank]
        for i in range(len(a)):
            if i != rank and a[i][c]:
                f = a[i][c] / a[rank][c]
                a[i] = [u - f * w for u, w in zip(a[i], a[rank])]
        rank += 1
    return rank


def words_up_to(g, length):
    for m in range(length + 1):
        yield from product(range(g), repeat=m)


def all_rows(system, length):
    return [(j, w, oracle_row(system, j, w))
            for w in words_up_to(len(system.operators), length)
            for j in range(len(system.observations))]


def random_system(seed, n, g, o, density=0.6, costs=True):
    rng = random.Random(seed)
    entry = lambda: F(rng.randint(-2, 2), rng.randint(1, 2)) if rng.random() < density else F(0)
    ops = [[[entry() for _ in range(n)] for _ in range(n)] for _ in range(g)]
    obs = [[entry() for _ in range(n)] for _ in range(o)]
    ac = [rng.randint(1, 3) for _ in range(g)] if costs else None
    oc = [rng.randint(0, 2) for _ in range(o)] if costs else None
    return OperatorSystem(n, ops, obs, ac, oc)


NONCOMMUTING = OperatorSystem(2, (((1, 1), (0, 1)), ((1, 0), (1, 1))), ((1, 0),))


class DegenerateClosureTests(unittest.TestCase):
    def check_roundtrip(self, system):
        cert = observable_closure(system)
        self.assertTrue(verify_certificate(system, cert))
        bundle = json.loads(json.dumps(certificate_bundle(system, cert)))
        replayed_system, replayed = replay_bundle(bundle)
        self.assertEqual(replayed_system, system)
        self.assertEqual(replayed, cert)
        return cert

    def test_rank_zero_closure_verifies(self):
        # The confirmed defect: zero observation, one generator, dimension one.
        system = OperatorSystem(1, (((1,),),), ((0,),))
        cert = self.check_roundtrip(system)
        self.assertEqual(cert.rank, 0)
        self.assertEqual(cert.observation_coordinates, ((),))
        self.assertEqual(cert.nullspace, ((F(1),),))
        self.assertEqual(quotient_state(system, cert, (5,)), ())
        self.assertEqual(quotient_update(cert, 0, ()), ())
        self.assertEqual(quotient_output(cert, ()), (F(0),))
        self.assertTrue(future_equivalent(system, (1,), (-7,), cert))
        self.assertIsNone(minimum_distinguishing_experiment(system, (1,), cert))

    def test_dimension_zero(self):
        system = OperatorSystem(0, ((),), ((),))
        cert = self.check_roundtrip(system)
        self.assertEqual((cert.rank, cert.nullspace, cert.observation_coordinates), (0, (), ((),)))
        self.assertEqual(quotient_output(cert, ()), (F(0),))

    def test_empty_observation_family(self):
        system = OperatorSystem(2, (((0, 1), (1, 0)),), ())
        cert = self.check_roundtrip(system)
        self.assertEqual(cert.rank, 0)
        self.assertEqual(cert.nullspace, ((1, 0), (0, 1)))
        self.assertEqual(quotient_output(cert, ()), ())

    def test_empty_generator_family(self):
        system = OperatorSystem(3, (), ((1, 0, 0), (2, 0, 0), (0, 0, 1)), observation_costs=(0, 0, 1))
        cert = self.check_roundtrip(system)
        self.assertEqual(cert.rank, 2)
        self.assertEqual(cert.transition_coordinates, ())
        self.assertEqual([e.word for e in cert.basis], [(), ()])
        self.assertEqual(cert.nullspace, ((0, 1, 0),))

    def test_row_times_empty_matrix_needs_columns(self):
        self.assertEqual(row_times_matrix((), (), 3), (0, 0, 0))
        with self.assertRaises(ValueError):
            row_times_matrix((), ())
        with self.assertRaises(ValueError):
            row_times_matrix((1,), ((1, 2),), 3)


class ClosureAgainstOracleTests(unittest.TestCase):
    def test_rank_equals_span_of_all_short_words(self):
        # Words of length < n already span the closure (the length filtration
        # strictly increases until it stabilizes), so length n is a safe oracle.
        for seed in range(40):
            n = 1 + seed % 4
            system = random_system(seed, n, 1 + seed % 3, 1 + seed % 2)
            cert = observable_closure(system)
            self.assertTrue(verify_certificate(system, cert))
            rows = [r for _, _, r in all_rows(system, n)]
            self.assertEqual(cert.rank, oracle_rank(rows, n), seed)
            self.assertEqual(oracle_rank(rows + list(cert.rows), n), cert.rank)
            for e in cert.basis:
                self.assertEqual(e.row, oracle_row(system, e.observation, e.word))

    def test_nullspace_is_invisible_and_invariant(self):
        for seed in range(25):
            n = 2 + seed % 3
            system = random_system(100 + seed, n, 2, 1)
            cert = observable_closure(system)
            self.assertEqual(len(cert.nullspace), n - cert.rank)
            for v in cert.nullspace:
                for _, _, row in all_rows(system, n):
                    self.assertEqual(sum(a * b for a, b in zip(row, v)), 0)
                for m in system.operators:
                    image = mat_vec(m, v)
                    self.assertFalse(any(mat_vec(cert.rows, image)))

    def test_quotient_transport(self):
        rng = random.Random(7)
        for seed in range(20):
            n = 2 + seed % 3
            system = random_system(200 + seed, n, 2, 2)
            cert = observable_closure(system)
            for _ in range(3):
                v = tuple(F(rng.randint(-3, 3)) for _ in range(n))
                for word in words_up_to(2, 3):
                    y = quotient_state(system, cert, v)
                    for i in word:
                        y = quotient_update(cert, i, y)
                    moved = apply_word(system, v, word)
                    self.assertEqual(y, quotient_state(system, cert, moved))
                    self.assertEqual(quotient_output(cert, y), mat_vec(system.observations, moved))

    def test_future_equivalence_matches_oracle(self):
        rng = random.Random(11)
        for seed in range(25):
            n = 2 + seed % 3
            system = random_system(300 + seed, n, 2, 1, density=0.4)
            cert = observable_closure(system)
            rows = [r for _, _, r in all_rows(system, n)]
            for _ in range(4):
                v = tuple(F(rng.randint(-2, 2)) for _ in range(n))
                w = list(v)
                if cert.nullspace and rng.random() < 0.5:
                    w = [a + b for a, b in zip(w, rng.choice(cert.nullspace))]
                elif rng.random() < 0.5:
                    w[rng.randrange(n)] += 1
                same = all(sum(a * (b - c) for a, b, c in zip(r, v, w)) == 0 for r in rows)
                self.assertEqual(future_equivalent(system, v, tuple(w), cert), same)


class WordOrderTests(unittest.TestCase):
    def test_chronological_action_on_noncommuting_generators(self):
        system = NONCOMMUTING
        m0, m1 = system.operators
        self.assertNotEqual(mat_vec(m1, mat_vec(m0, (0, 1))), mat_vec(m0, mat_vec(m1, (0, 1))))
        # Word (0, 1): attach 0 first, then 1, so the state becomes M1 M0 v.
        self.assertEqual(apply_word(system, (0, 1), (0, 1)), mat_vec(m1, mat_vec(m0, (0, 1))))
        e = experiment(system, 0, (0, 1))
        self.assertEqual(e.row, vec_mat(vec_mat(system.observations[0], m1, 2), m0, 2))
        self.assertNotEqual(e.row, experiment(system, 0, (1, 0)).row)
        for v in ((0, 1), (1, 0), (2, -3)):
            for word in words_up_to(2, 3):
                reading = sum(a * b for a, b in zip(experiment(system, 0, word).row, v))
                self.assertEqual(reading, mat_vec(system.observations, apply_word(system, v, word))[0])

    def test_closure_prepends_letters(self):
        cert = observable_closure(NONCOMMUTING)
        self.assertEqual(cert.rank, 2)
        self.assertEqual([e.word for e in cert.basis], [(), (0,)])
        # (1,0)·M0 = (1,1): the row of word (0,) must be L M0, not L M1 = (1,0).
        self.assertEqual(cert.basis[1].row, (1, 1))

    def test_reversed_witness_word_is_rejected(self):
        system = OperatorSystem(2, (((1, 1), (0, 1)), ((2, 0), (0, 1))), ((1, 0),),
                                attachment_costs=(1, 1))
        cert = observable_closure(system)
        self.assertTrue(verify_certificate(system, cert))
        word = (0, 1)
        e = experiment(system, 0, word)
        self.assertNotEqual(e.row, experiment(system, 0, word[::-1]).row)
        forged = dataclasses.replace(e, word=word[::-1])
        fake = dataclasses.replace(cert, basis=(cert.basis[0], forged))
        self.assertFalse(verify_certificate(system, fake))


class MinimumCostTests(unittest.TestCase):
    def oracle_minimum(self, system, d, cost_limit):
        best = None
        g = len(system.operators)
        length = int(cost_limit / min(system.attachment_costs)) if g else 0
        for j, w, row in all_rows(system, length):
            cost = system.observation_costs[j] + sum((system.attachment_costs[i] for i in w), F(0))
            if cost <= cost_limit and sum(a * b for a, b in zip(row, d)) and (best is None or cost < best):
                best = cost
        return best

    def test_cheapest_witness_is_global_minimum(self):
        rng = random.Random(5)
        checked = 0
        for seed in range(60):
            n = 2 + seed % 3
            system = random_system(400 + seed, n, 2, 2)
            cert = observable_closure(system)
            limit = max((e.cost for e in cert.basis), default=F(0))
            for _ in range(3):
                d = tuple(F(rng.randint(-2, 2)) for _ in range(n))
                found = minimum_distinguishing_experiment(system, d, cert)
                expected = self.oracle_minimum(system, d, limit)
                if found is None:
                    self.assertIsNone(expected)
                    self.assertTrue(future_equivalent(system, d, (0,) * n, cert))
                else:
                    checked += 1
                    self.assertEqual(found.cost, expected, seed)
                    self.assertEqual(found, experiment(system, found.observation, found.word))
                    self.assertNotEqual(sum(a * b for a, b in zip(found.row, d)), 0)
        self.assertGreater(checked, 50)

    def test_basis_costs_count_cost_filtered_rank(self):
        # The theorem behind pruning: #basis rows of cost <= C is the rank of
        # all experiments of cost <= C, for every threshold C.
        for seed in range(30):
            n = 2 + seed % 3
            system = random_system(500 + seed, n, 2, 2)
            cert = observable_closure(system)
            limit = max((e.cost for e in cert.basis), default=F(0))
            length = int(limit / min(system.attachment_costs)) + 1
            rows = all_rows(system, length)
            for c in sorted({e.cost for e in cert.basis}):
                cheap = [r for j, w, r in rows if system.observation_costs[j]
                         + sum((system.attachment_costs[i] for i in w), F(0)) <= c]
                self.assertEqual(sum(e.cost <= c for e in cert.basis), oracle_rank(cheap, n), (seed, c))

    def test_zero_observation_cost_and_positive_attachment_cost(self):
        system = OperatorSystem(2, (((0, 1), (1, 0)),), ((1, 0),), attachment_costs=(F(1, 2),),
                                observation_costs=(0,))
        cert = observable_closure(system)
        self.assertEqual([e.cost for e in cert.basis], [0, F(1, 2)])
        for bad in ((0,), (-1,), (F(-1, 3),)):
            with self.assertRaises(ValueError):
                OperatorSystem(2, (((0, 1), (1, 0)),), ((1, 0),), attachment_costs=bad)
        with self.assertRaises(ValueError):
            OperatorSystem(2, (((0, 1), (1, 0)),), ((1, 0),), observation_costs=(-1,))

    def test_cheapest_is_not_strongest(self):
        # Observation 1 and generator 2: the direct reading (cost 0, signal 1)
        # is the cheapest witness, and dependence pruning discards the
        # extensions, whose signals 2^k are larger.  Minimum cost is not
        # maximum margin.
        system = OperatorSystem(1, (((2,),),), ((1,),))
        cert = observable_closure(system)
        self.assertEqual(cert.rank, 1)
        witness = minimum_distinguishing_experiment(system, (1,), cert)
        self.assertEqual((witness.word, witness.cost, witness.row), ((), 0, (1,)))
        self.assertEqual(experiment(system, 0, (0, 0, 0)).row, (8,))


class StrictCertificateTests(unittest.TestCase):
    def setUp(self):
        self.system = OperatorSystem(2, (((1, 1), (0, 1)), ((2, 0), (0, 1))), ((1, 0), (0, 0)),
                                     attachment_costs=(1, 2), observation_costs=(0, 1))
        self.cert = observable_closure(self.system)
        self.assertTrue(verify_certificate(self.system, self.cert))

    def reject(self, **changes):
        self.assertFalse(verify_certificate(self.system, dataclasses.replace(self.cert, **changes)))

    def test_inexact_costs_are_rejected(self):
        e = self.cert.basis[0]
        for value in (0.0, False, 0, F(1)):
            self.reject(basis=(dataclasses.replace(e, cost=value),) + self.cert.basis[1:])

    def test_malformed_indices_words_rows(self):
        e = self.cert.basis[0]
        for change in ({'observation': True}, {'observation': 5}, {'observation': -1},
                       {'word': [0]}, {'word': (2,)}, {'word': (True,)},
                       {'row': (1, 0)}, {'row': (F(1), F(0), F(0))}, {'row': [F(1), F(0)]}):
            self.reject(basis=(dataclasses.replace(e, **change),) + self.cert.basis[1:])
        self.reject(basis=list(self.cert.basis))
        self.reject(basis=self.cert.basis + self.cert.basis[:1])

    def test_malformed_pivots_nullspace_coordinates(self):
        c = self.cert
        self.reject(pivots=tuple(True if p == 1 else p for p in c.pivots) if 1 in c.pivots else (True,))
        self.reject(pivots=c.pivots[::-1] if len(c.pivots) > 1 else (1,))
        self.reject(pivots=list(c.pivots))
        self.reject(nullspace=tuple(tuple(2 * x for x in row) for row in c.nullspace) or ((F(1), F(0)),))
        self.reject(nullspace=tuple(tuple(int(x) for x in row) for row in c.nullspace) or ((1, 0),))
        self.reject(observation_coordinates=tuple(tuple(float(x) for x in row)
                                                  for row in c.observation_coordinates))
        bumped = tuple(tuple(tuple(x + 1 for x in row) for row in m) for m in c.transition_coordinates)
        self.reject(transition_coordinates=bumped)
        self.reject(transition_coordinates=c.transition_coordinates[:1])

    def test_cost_filtration_violation_is_rejected(self):
        # A row of cost 2 used to reconstruct an observation of cost 1.
        system = OperatorSystem(1, (((1,),),), ((1,), (2,)), attachment_costs=(1,),
                                observation_costs=(2, 1))
        cert = observable_closure(system)
        self.assertEqual(cert.basis[0].observation, 1)
        costly = experiment(system, 0)
        forged = ClosureCertificate((costly,), ((F(1),), (F(2),)), (((F(1),),),), (), (0,))
        self.assertFalse(verify_certificate(system, forged))
        # Same rows with the cheap observation as witness pass the filtration.
        cheap = experiment(system, 1)
        honest = ClosureCertificate((cheap,), ((F(1, 2),), (F(1),)), (((F(1),),),), (), (0,))
        self.assertTrue(verify_certificate(system, honest))

    def test_nullspace_must_be_the_rref_kernel(self):
        system = OperatorSystem(2, (((1, 0), (0, 2)),), ((1, 0),))
        cert = observable_closure(system)
        self.assertEqual((cert.rank, cert.nullspace), (1, ((F(0), F(1)),)))
        for bad in (((F(0), F(2)),), ((0, 1),), ((F(1), F(0)),), (), ((F(0), F(1)), (F(0), F(1)))):
            self.assertFalse(verify_certificate(system, dataclasses.replace(cert, nullspace=bad)))

    def test_non_certificate_objects(self):
        self.assertFalse(verify_certificate(self.system, None))
        self.assertFalse(verify_certificate(None, self.cert))
        with self.assertRaises(ValueError):
            quotient_state(self.system, dataclasses.replace(self.cert, pivots=()), (1, 1))
        with self.assertRaises(ValueError):
            minimum_distinguishing_experiment(self.system, (1, 0), dataclasses.replace(self.cert, pivots=()))


class PortableReplayTests(unittest.TestCase):
    def setUp(self):
        self.system = OperatorSystem(2, (((1, 1), (0, 1)),), ((1, 0),), attachment_costs=(F(3, 2),))
        self.bundle = json.loads(json.dumps(certificate_bundle(self.system)))

    def mutate(self, path, value):
        bundle = json.loads(json.dumps(self.bundle))
        target = bundle
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        with self.assertRaises(ValueError):
            replay_bundle(bundle)

    def test_valid_bundle_replays(self):
        system, cert = replay_bundle(self.bundle)
        self.assertEqual(system, self.system)
        self.assertEqual(cert.rank, 2)

    def test_rational_encodings(self):
        for bad in ([3, 2.0], [6, 4], [3, -2], [3, 0], [True, 1], [1], "3/2", [3, 2, 1]):
            self.mutate(("system", "attachment_costs", 0), bad)
        self.mutate(("certificate", "basis", 1, "cost"), [1, 1])

    def test_structure_and_limits(self):
        self.mutate(("schema",), "singularity.operator-closure/0")
        self.mutate(("system", "dimension"), 3)
        self.mutate(("system", "dimension"), True)
        self.mutate(("certificate", "pivots"), [0])
        self.mutate(("certificate", "pivots"), [1, 0])
        self.mutate(("certificate", "basis", 1, "word"), [1])
        self.mutate(("certificate", "basis", 1, "word"), [0, 0])
        self.mutate(("certificate", "basis", 0, "observation"), 1)
        self.mutate(("certificate", "nullspace"), [[[1, 1], [0, 1]]])
        bundle = json.loads(json.dumps(self.bundle))
        bundle["extra"] = 1
        with self.assertRaises(ValueError):
            replay_bundle(bundle)
        big = {"schema": "singularity.operator-closure/1", "system": {
            "dimension": 129, "operators": [], "observations": [], "attachment_costs": [],
            "observation_costs": []}, "certificate": {}}
        with self.assertRaises(ValueError):
            replay_bundle(big)


class InputContractTests(unittest.TestCase):
    def test_exact_inputs_only(self):
        for bad in (True, 1.5, -1, "2"):
            with self.assertRaises((ValueError, TypeError)):
                OperatorSystem(bad, (), ())
        with self.assertRaises(ValueError):
            OperatorSystem(1, (((0.5,),),), ((1,),))
        with self.assertRaises(ValueError):
            OperatorSystem(1, (((1,),),), ((True,),))
        with self.assertRaises(ValueError):
            OperatorSystem(2, (((1,),),), ((1, 0),))
        with self.assertRaises(ValueError):
            apply_word(NONCOMMUTING, (0.5, 1), ())
        with self.assertRaises(ValueError):
            apply_word(NONCOMMUTING, (0, 1), (2,))
        with self.assertRaises(ValueError):
            experiment(NONCOMMUTING, 0, (True,))
        with self.assertRaises(ValueError):
            minimum_distinguishing_experiment(NONCOMMUTING, (1,))


if __name__ == "__main__":
    unittest.main()
