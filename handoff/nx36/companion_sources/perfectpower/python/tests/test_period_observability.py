"""Exact all-future checks for rational periodic Mellin observations."""

from fractions import Fraction as Q
import json
import unittest

from perfectpower.divisor_square import WorkLimit
from perfectpower.e8_periods import PHI30, coxeter_trace
from perfectpower.observable_machine import power_outputs, verify_machine
from perfectpower.period_observability import PeriodObservation, e8_observations, receipt


class PeriodObservabilityTests(unittest.TestCase):
    def test_repeated_blocks_are_the_same_complete_observation(self):
        a = PeriodObservation((1, '-2/3', 0))
        b = PeriodObservation((1, Q(-2, 3), 0) * 4)
        self.assertTrue(a.separating_witness(b)['equal'])
        self.assertEqual(a.generating_function(), b.generating_function())
        self.assertEqual(a.generating_function().dimension, 3)
        zero = PeriodObservation((0, 0))
        self.assertEqual(zero.generating_function().dimension, 0)
        self.assertEqual(zero.machine()['minimal_dimension'], 0)

    def test_first_difference_is_an_exact_separating_witness(self):
        a, b = PeriodObservation((3, 0, 5)), PeriodObservation((3, 0, 5, 3))
        witness = a.separating_witness(b)
        self.assertFalse(witness['equal'])
        self.assertEqual(witness['common_period'], 12)
        self.assertEqual(witness['first_differing_index'], 5)
        self.assertEqual((witness['left'], witness['right'], witness['difference']), ('0', '3', '-3'))
        with self.assertRaises(WorkLimit):
            a.separating_witness(b, period_budget=11)

    def test_shift_compression_preserves_arbitrarily_late_readouts(self):
        observation = PeriodObservation((Q(1, 2), -1, Q(3, 2), 0) * 3)
        machine = observation.machine()
        self.assertTrue(verify_machine(machine))
        self.assertEqual(machine['minimal_dimension'], 4)
        for time in (0, 1, 2, 3, 4, 11, 12, 97, 10 ** 18):
            expected = (observation.coefficient(time + 1),)
            self.assertEqual(power_outputs(machine, time), expected)
            self.assertEqual(power_outputs(machine, time, original=True), expected)
            self.assertEqual(observation.generating_function().nth(time), expected[0])

    def test_rational_kernel_and_dirichlet_engine_agree(self):
        for block in ((1, 0, -1, 0), (2, Q(-3, 5), 4), (0,)):
            observation = PeriodObservation(block)
            kernel, family = observation.generating_function(), observation.dirichlet()
            self.assertEqual(kernel.coefficients(101), tuple(family.coefficient(n) for n in range(1, 102)))
            for x in (Q(0), Q(1, 7), Q(2, 3)):
                numerator = sum((c * x ** j for j, c in enumerate(kernel.numerator)), Q(0))
                denominator = sum((c * x ** j for j, c in enumerate(kernel.denominator)), Q(0))
                self.assertEqual(numerator / denominator, family.kernel(x))
            packet = observation.packet(include_machine=True)
            self.assertTrue(verify_machine(packet['machine']))
            json.dumps(packet, sort_keys=True)

    def test_e8_kernel_and_machine_dimensions_are_output_dimensions(self):
        retained = receipt()
        reflection, adjoint = e8_observations()
        self.assertEqual(reflection.generating_function().denominator, PHI30)
        self.assertEqual(adjoint.generating_function().denominator, (1,) + (0,) * 29 + (-1,))
        for name, observation, dimension in (('reflection', reflection, 8), ('adjoint', adjoint, 30)):
            packet = retained[name]
            self.assertEqual(packet['minimal_dimension'], dimension)
            self.assertEqual(packet['rational_gf']['dimension'], dimension)
            self.assertNotEqual(Q(packet['rational_gf']['hankel_determinant']), 0)
            self.assertTrue(verify_machine(packet['machine']))
            for time in (0, 29, 30, 61, 10 ** 18):
                self.assertEqual(power_outputs(packet['machine'], time), (observation.coefficient(time + 1),))
        self.assertEqual(retained['adjoint']['underlying_representation_dimension'], 248)
        self.assertEqual(adjoint.coefficient(30), 248)
        for n in range(1, 61):
            self.assertEqual(reflection.coefficient(n), coxeter_trace(n))
        self.assertEqual(adjoint.dirichlet().pi_coefficient(2).as_rational(), 0)
        self.assertFalse(adjoint.separating_witness(PeriodObservation((0,)))['equal'])
        json.dumps(retained, sort_keys=True)

    def test_invalid_and_excessive_inputs_are_rejected(self):
        for block in ((), (True,), (0.5,), ('nonsense',)):
            with self.assertRaises((ValueError, ZeroDivisionError)):
                PeriodObservation(block)
        for block in ((1 << 8192,), (Q(1, 1 << 8192),), (0,) * 4097):
            with self.assertRaises(WorkLimit):
                PeriodObservation(block)
        observation = PeriodObservation((1,))
        for index in (0, -1, True, 1.0):
            with self.assertRaises(ValueError):
                observation.coefficient(index)
        for budget in (0, True, 1.0):
            with self.assertRaises(ValueError):
                observation.separating_witness(observation, period_budget=budget)
        with self.assertRaises(ValueError):
            observation.separating_witness((1,))
        with self.assertRaises(ValueError):
            observation.packet(include_machine=1)
        with self.assertRaises(WorkLimit):
            PeriodObservation((1,) * 65).machine()
        self.assertEqual(PeriodObservation((0,) * 4096).generating_function().dimension, 0)


if __name__ == '__main__':
    unittest.main()
