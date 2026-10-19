"""Independent small-character and exact period checks for finite transports."""
from copy import deepcopy
from fractions import Fraction as Q
from math import cos, sin, pi
import unittest
from perfectpower.period_transport import (PhaseObject, TransportArrow, even_period_coefficient,
    primitive_phases, ramanujan_trace, root_fiber, transport_closure, verify_transport)


def character(obj, at):
    return sum(float(v) * complex(cos(2*pi*k*at/obj.conductor), sin(2*pi*k*at/obj.conductor)) for k, v in obj.terms)


class PeriodTransportTests(unittest.TestCase):
    def test_tensor_and_sum_against_independent_characters(self):
        a = PhaseObject(4, {0: 1, 1: 2, 3: 1})
        b = PhaseObject(6, {1: 1, 5: 1})
        self.assertEqual(a.tensor(b).dimension, a.dimension*b.dimension)
        for at in range(12):
            self.assertAlmostEqual(abs(character(a.tensor(b), at) - character(a, at)*character(b, at)), 0, places=12)
            self.assertAlmostEqual(abs(character(a.direct_sum(b), at) - character(a, at)-character(b, at)), 0, places=12)
            self.assertAlmostEqual(abs(character(a.dual(), at)-character(a, at).conjugate()), 0, places=12)
        self.assertEqual(a.tensor(b), b.tensor(a))
        self.assertEqual(a.tensor(b).dual(), a.dual().tensor(b.dual()))

    def test_lift_restriction_and_composition(self):
        a = PhaseObject(5, {1: 2, 4: 2})
        first = TransportArrow.rule(a, 'lift', conductor=10)
        second = TransportArrow.rule(first.target, 'lift', conductor=30)
        path = first.then(second)
        self.assertEqual(path.target, a.lift(30))
        self.assertEqual(path.target.phases(), a.phases())
        self.assertTrue(verify_transport(path.receipt()))
        self.assertEqual(a.lift(30).restrict(5), a.power(6))
        self.assertEqual(a.lift(30).restrict(5), a)
        self.assertEqual(PhaseObject(4, {1: 1}).lift(8).restrict(4), PhaseObject(4, {2: 1}))
        for at in range(5):
            self.assertAlmostEqual(abs(character(a.lift(30).restrict(5), at)-character(a.lift(30), 6*at)), 0, places=12)
        forged = deepcopy(path.receipt())
        forged['target']['terms'][0][1] = '3'
        self.assertFalse(verify_transport(forged))
        forged = deepcopy(path.receipt())
        forged['phase_preserving'] = False
        self.assertFalse(verify_transport(forged))
        with self.assertRaises(ValueError):
            first.then(first)

    def test_exact_trace_and_representation_domain(self):
        self.assertEqual(primitive_phases(12).cyclotomic_trace(), (Q(0),))
        self.assertEqual(primitive_phases(5).cyclotomic_trace(), (Q(-1),))
        for n in range(1, 20):
            for at in range(n):
                value = character(primitive_phases(n), at)
                self.assertAlmostEqual(abs(value-ramanujan_trace(n, at)), 0, places=11)
        self.assertFalse(PhaseObject(4, {1: '-1/2'}).is_representation)
        self.assertTrue(primitive_phases(1680).has_real_form)
        self.assertEqual(primitive_phases(1680).dimension, 384)
        with self.assertRaises(ValueError):
            PhaseObject(4, {1: 0.5})
        with self.assertRaises(ValueError):
            primitive_phases(5).lift(6)
        with self.assertRaises(ValueError):
            primitive_phases(5).restrict(2)

    def test_actual_root_fiber_and_primitive_fiber(self):
        full = root_fiber(1680, 264)
        primitive = root_fiber(1680, 264, primitive=True)
        base = PhaseObject(1680, {1: 1})
        self.assertEqual(full.dimension, 264)
        self.assertEqual(primitive.dimension, 240)
        self.assertEqual(full.power(264), base.lift(443520).scale(264))
        self.assertEqual(primitive.power(264), base.lift(443520).scale(240))
        self.assertEqual(even_period_coefficient(primitive), Q(22537, 6773760))

    def test_period_additivity_and_tensor_counterexample(self):
        a = PhaseObject(4, {1: 1})
        b = PhaseObject(6, {1: 2})
        self.assertEqual(even_period_coefficient(a.direct_sum(b)), even_period_coefficient(a)+even_period_coefficient(b))
        self.assertEqual(even_period_coefficient(a.lift(120), 8), even_period_coefficient(a, 8))
        self.assertEqual(even_period_coefficient(PhaseObject(1, {0: 1})), Q(1, 6))
        self.assertEqual(even_period_coefficient(PhaseObject(1, {0: 1}), 4), Q(1, 90))
        # Weight 2 times weight 2 would have weight 4. Even there it fails.
        unit = PhaseObject(1, {0: 1})
        self.assertNotEqual(even_period_coefficient(unit.tensor(unit), 4), even_period_coefficient(unit)**2)
        with self.assertRaises(ValueError):
            even_period_coefficient(a, 3)

    def test_finite_closure_and_invalid_rule_domain(self):
        a = PhaseObject(7, {1: 1})
        orbit = transport_closure([a], [('power', {'exponent': 2}), ('dual', {})])
        self.assertEqual(len(orbit), 6)
        self.assertEqual({x.terms[0][0] for x in orbit}, set(range(1, 7)))
        with self.assertRaises(ValueError):
            transport_closure([a], [('lift', {'conductor': 8})])
        with self.assertRaises(ValueError):
            transport_closure([a], [('power', {'exponent': 2})], max_objects=2)


if __name__ == '__main__':
    unittest.main()
