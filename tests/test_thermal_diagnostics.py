"""Independent source, physical-stencil, lift and decision checks for the pilot."""
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path
import unittest

from singularity.observability import apply_word
from singularity.panels import (exhaustive_minimum_panel, minimum_cost_panel,
                                greedy_panel, consistent_candidates, reading_pool)
from singularity.thermal_diagnostics import (
    AffineCandidate, affine_operator_system, build_plate_candidates,
    default_protocols, protocol_pool, simulate_protocol)


class ThermalDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = build_plate_candidates(12)
        cls.small = build_plate_candidates(4)
        cls.protocols = default_protocols((1, 2, 3, 4, 6, 8, 12, 20))
        cls.compiled = protocol_pool(cls.models, cls.protocols, sensor_noise=F(1, 1000))

    def test_nominal_is_pinned_dynacomp_fixture(self):
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / 'applications/thermal_diagnostics/source_fixture.json').read_text())
        fixture, model = data['model'], self.models[0]
        self.assertEqual(model.dimension, fixture['n'])
        self.assertEqual(model.entries, tuple(sorted((i, j, F(value)) for i, j, value in fixture['entries'])))
        self.assertEqual(model.heater, tuple(F(row[0]) for row in fixture['B']))
        self.assertEqual(model.sensors[0], tuple(F(value) for value in fixture['C'][0]))
        self.assertEqual(data['source']['commit'], 'cd788c7ac695728e3f5b22056a0f99a2c1e1463c')

    def test_nonnegative_stability_and_input_budget(self):
        for index, model in enumerate(self.models):
            rows = [F(0)] * model.dimension
            for i, j, value in model.entries:
                self.assertGreaterEqual(value, 0)
                rows[i] += value
            decay = F(49, 50) if index == 3 else F(99, 100)
            self.assertEqual(rows, [decay] * model.dimension)
            self.assertEqual(sum(model.heater), F(1, 2) if index == 2 else F(1))
            self.assertTrue(all(sum(sensor) == 1 for sensor in model.sensors))
        self.assertEqual(len(self.models[4].entries), 670)
        self.assertEqual(len(self.models[5].entries), 670)

    @staticmethod
    def independent_stencil(identifier, state, amplitude, grid=4):
        """Edge flux implementation, independent of sparse matrix assembly."""
        k = F(1, 16) if identifier == 'conductance_half' else F(1, 8)
        loss = F(1, 50) if identifier == 'loss_double' else F(1, 100)
        gain = F(1, 2) if identifier == 'heater_half' else F(1)
        mid = grid // 2 - 1
        blocked = ({(mid * grid + mid - 1, mid * grid + mid)}
                   if identifier == 'blocked_left_center_bond' else
                   {(mid * grid + mid + 1, mid * grid + mid + 2)}
                   if identifier == 'blocked_right_center_bond' else set())
        out = [(1 - loss) * x for x in state]
        for r in range(grid):
            for c in range(grid):
                i = r * grid + c
                for j in ((i + 1,) if c + 1 < grid else ()) + ((i + grid,) if r + 1 < grid else ()):
                    if (i, j) in blocked:
                        continue
                    flux = k * (state[j] - state[i])
                    out[i] += flux
                    out[j] -= flux
                if r in (mid, mid + 1) and c in (mid, mid + 1):
                    out[i] += gain * amplitude / 4
        return tuple(out)

    def test_independent_edge_flux_evolution_all_faults(self):
        for model in self.small:
            initial = tuple(F((i * 7) % 13, 10) for i in range(16))
            for word in ((2, 0, 2, 0), (0, 2, 2, 2), (2,)):
                state = initial
                for amplitude in word:
                    state = self.independent_stencil(model.identifier, state, F(amplitude))
                for sensor in range(4):
                    self.assertEqual(simulate_protocol(model, word, sensor, initial), model.observe(state, sensor))

    def test_homogeneous_lift_preserves_original_candidate_identity(self):
        lift = affine_operator_system(self.small)
        self.assertEqual(lift.system.dimension, 102)
        self.assertEqual(lift.candidate_ids, tuple(c.identifier for c in self.small))
        for length in range(4):
            for word in product((0, 1), repeat=length):
                amplitudes = tuple(lift.amplitudes[i] for i in word)
                for model, candidate in zip(self.small, lift.states):
                    state = apply_word(lift.system, candidate, word)
                    for sensor, row in enumerate(lift.system.observations):
                        reading = sum((a * b for a, b in zip(row, state)), F(0))
                        self.assertEqual(reading, simulate_protocol(model, amplitudes, sensor))
        with self.assertRaises(ValueError):
            affine_operator_system(self.models)

    def test_generic_lift_order_nonzero_initial_and_sparse_duplicate_entries(self):
        a = AffineCandidate('a', 1, ((0, 0, F(1, 4)), (0, 0, F(1, 4))), (1,), ((1,),))
        b = AffineCandidate('b', 1, ((0, 0, F(1, 3)),), (2,), ((1,),))
        lift = affine_operator_system((a, b), initial_states=((3,), (5,)),
                                     observation_costs=(1,))
        for model, candidate, x0 in zip((a, b), lift.states, ((3,), (5,))):
            answers = []
            for word in ((0, 1), (1, 0)):
                state = apply_word(lift.system, candidate, word)
                output = sum((a * b for a, b in zip(lift.system.observations[0], state)), F(0))
                self.assertEqual(output, simulate_protocol(model, tuple(lift.amplitudes[i] for i in word), 0, x0))
                answers.append(output)
            self.assertNotEqual(*answers)
        self.assertEqual(len(a.entries), 1)

    def test_exact_radius_propagation_and_cost(self):
        word = (2, 0, 2, 0)
        result = protocol_pool(self.small, ((word, 2),), initial_radius=F(1, 100),
                               sensor_noise=F(1, 1000), process_radius=F(1, 10000),
                               reduction_error=F(1, 100000))
        expected = []
        for index in range(6):
            decay = F(49, 50) if index == 3 else F(99, 100)
            expected.append(F(1, 100) * decay ** 4 + F(1, 10000) * sum(decay ** j for j in range(4))
                            + F(1, 1000) + F(1, 100000))
        self.assertEqual(result.error_bounds, (tuple(expected),))
        self.assertEqual(result.epsilon, (max(expected),))
        self.assertEqual(result.pool.costs, (F(10),))
        for model, radius in zip(self.small, expected):
            nominal = simulate_protocol(model, word, 2)
            upper = (F(1, 100),) * 16
            for amplitude in word:
                upper = tuple(x + F(1, 10000) for x in model.step(upper, amplitude))
            self.assertEqual(model.observe(upper, 2) - nominal + F(1, 1000) + F(1, 100000), radius)

    def test_reflected_faults_invisible_to_original_mean_sensors(self):
        # Reflection covariance plus invariant initial/heater/sensors proves all words;
        # these checks also exercise the concrete sparse matrices independently.
        left, right = self.small[4:]
        reflect = lambda i: (i // 4) * 4 + 3 - i % 4
        self.assertEqual(tuple(sorted((reflect(i), reflect(j), v) for i, j, v in left.entries)), right.entries)
        self.assertEqual(tuple(left.heater[reflect(i)] for i in range(16)), right.heater)
        for sensor in (0, 1):
            self.assertEqual(tuple(left.sensors[sensor][reflect(i)] for i in range(16)), right.sensors[sensor])
        protocols = tuple(p for p in self.protocols if p[1] in (0, 1))
        result = protocol_pool(self.models[4:], protocols, sensor_noise=0)
        self.assertTrue(all(row[0] == row[1] for row in result.pool.readings))
        failure = minimum_cost_panel(result.pool)
        self.assertFalse(failure.feasible)
        self.assertEqual(failure.uncoverable, ((0, 1),))
        self.assertNotEqual(simulate_protocol(self.models[4], (2, 0), 2),
                            simulate_protocol(self.models[5], (2, 0), 2))

    def test_small_exhaustive_panel_matches_backend_and_full_fixture(self):
        data = self.compiled
        chosen = tuple(range(11)) + (22,)
        pool = reading_pool(tuple(data.pool.costs[i] for i in chosen),
                            tuple(data.pool.readings[i] for i in chosen),
                            tuple(data.pool.labels[i] for i in chosen))
        oracle = exhaustive_minimum_panel(pool, F(1, 1000))
        fast = minimum_cost_panel(pool, F(1, 1000))
        self.assertEqual((fast.feasible, fast.cost), (oracle.feasible, oracle.cost))
        self.assertEqual(fast.cost, 8)
        full = minimum_cost_panel(data.pool, data.panel_epsilon)
        greedy = greedy_panel(data.pool, data.panel_epsilon)
        self.assertEqual(full.cost, 8)
        self.assertEqual(greedy.cost, 13)
        self.assertEqual(data.pool.labels[full.panel[0]], ((F(2), F(0), F(0)), 2))
        self.assertEqual(len(data.candidate_ids), 6)
        for truth in range(6):
            observed = tuple(data.pool.readings[e][truth] + data.epsilon[e] for e in full.panel)
            self.assertEqual(consistent_candidates(data.pool, full.panel, observed, data.panel_epsilon), (truth,))
        noisy = minimum_cost_panel(data.pool, F(1, 100))
        self.assertEqual(noisy.cost, 16)
        self.assertEqual(greedy_panel(data.pool, F(1, 100)).cost, 19)

    def test_negative_operator_bounds_and_empty_pool(self):
        first = AffineCandidate('signed-a', 1, ((0, 0, F(-1, 2)),), (0,), ((-2,),))
        second = AffineCandidate('signed-b', 1, ((0, 0, F(1, 2)),), (0,), ((2,),))
        result = protocol_pool((first, second), (((0, 0), 0),),
                               initial_radius=F(1, 10), sensor_noise=0,
                               sensor_costs=(1,))
        self.assertEqual(result.error_bounds, ((F(1, 20), F(1, 20)),))
        for model in (first, second):
            self.assertEqual(abs(simulate_protocol(model, (0, 0), 0, (F(1, 10),))), F(1, 20))
        empty = protocol_pool(self.small, (), sensor_noise=0)
        self.assertEqual(empty.pool.size, 0)
        self.assertEqual(empty.pool.candidates, 6)
        self.assertIsNone(empty.panel_epsilon)
        # Equal dynamics are not discarded: different original fault identities
        # remain distinct candidates and the backend correctly reports failure.
        clone = AffineCandidate('equal-different-id', 1, first.entries, first.heater, first.sensors)
        same = protocol_pool((first, clone), (((0,), 0),), sensor_noise=0,
                             sensor_costs=(1,))
        self.assertEqual(same.candidate_ids, ('signed-a', 'equal-different-id'))
        self.assertFalse(minimum_cost_panel(same.pool).feasible)

    def test_bound_input_contracts_and_duplicate_ids(self):
        for value in (True, 4.0, '4'):
            with self.assertRaises(TypeError):
                build_plate_candidates(value)
        for value in (2, 3, -4):
            with self.assertRaises(ValueError):
                build_plate_candidates(value)
        for kwargs in ({'sensor_noise': .001}, {'initial_radius': True}, {'elapsed_cost': 0},
                       {'sensor_noise': -1}, {'heating_cost': -1}):
            with self.assertRaises((TypeError, ValueError)):
                protocol_pool(self.small, (((2,), 0),), **kwargs)
        with self.assertRaises(ValueError):
            protocol_pool((self.small[0], self.small[0]), (((2,), 0),))
        with self.assertRaises(ValueError):
            protocol_pool(self.small, (((3,), 0),))
        with self.assertRaises(TypeError):
            simulate_protocol(self.small[0], (2.0,), 0)
        with self.assertRaises(ValueError):
            simulate_protocol(self.small[0], (2,), 4)
        exact = protocol_pool(self.small, (((2,), 0),), sensor_noise=0)
        self.assertIsNone(exact.panel_epsilon)


if __name__ == '__main__':
    unittest.main()
