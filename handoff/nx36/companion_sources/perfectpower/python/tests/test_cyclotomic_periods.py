"""Independent checks of root filters, multiplicities and Bernoulli periods."""
import cmath
from fractions import Fraction as Q
from math import gcd
import unittest

from perfectpower.cyclotomic_periods import (
    SparsePhaseSum, bernoulli_number, bernoulli_polynomial, canonical_phase,
    compose_full_fiber, full_fiber_reduction, period_reduction,
    primitive_conjugate_reduction, real_li_even_pi_coefficient,
)


class CyclotomicPeriodTests(unittest.TestCase):
    def test_reference_240_phases_two_terms(self):
        r = primitive_conjugate_reduction(1680, 443520)
        self.assertEqual(r.phase_count, 240)
        self.assertEqual(len(r.source_phases()), 240)
        self.assertEqual([(t.multiplicity, t.dilation, t.phase) for t in r.terms],
                         [(1, 264, Q(1, 1680)), (-1, 24, Q(611, 1680))])
        self.assertEqual(r.real_even_pi_coefficient(2), Q(22537, 6773760))
        self.assertTrue(r.verify_even_weight(2))
        self.assertTrue(r.verify_even_weight(4))

    def test_every_small_conductor_and_residue(self):
        checks = 0
        for N in range(1, 49):
            for n in range(1, N + 1):
                if N % n:
                    continue
                for a in range(n):
                    r = primitive_conjugate_reduction(n, N, a)
                    expected = tuple(Q(u, N) for u in range(N)
                                     if u % n == a and gcd(u, N) == 1)
                    self.assertEqual(r.source_phases(), expected)
                    self.assertEqual(r.phase_count, len(expected))
                    for weight in (2, 4, 6):
                        self.assertTrue(r.verify_even_weight(weight), (N, n, a, weight))
                    checks += 1
        self.assertGreater(checks, 1000)

    def test_multiple_new_primes_and_multiplicities(self):
        r = primitive_conjugate_reduction(4, 420, 3)
        self.assertEqual(len(r.terms), 8)
        self.assertEqual(r.phase_count, 48)
        for s in (2, 4, 8):
            self.assertTrue(r.verify_even_weight(s))
        # At n=1 all reduced phases coincide; canonical addition must retain
        # signed rational multiplicities, rather than treating terms as a set.
        r = primitive_conjugate_reduction(1, 30)
        self.assertEqual(r.phase_count, 8)
        self.assertEqual(len(r.specialize(2).terms), 1)
        self.assertEqual(r.real_even_pi_coefficient(), -Q(2, 45))

    def test_fourier_filter_direct_complex_modes(self):
        # Independent exponential sums verify the actual Fourier selection
        # rule, not only its even real special values.
        for n, N, a in ((1, 30, 0), (4, 60, 3), (6, 126, 5), (7, 210, 2)):
            r = primitive_conjugate_reduction(n, N, a)
            for k in range(1, 40):
                lhs = sum(cmath.exp(2j*cmath.pi*float(x)*k) for x in r.source_phases())
                rhs = sum(t.multiplicity*t.dilation *
                          cmath.exp(2j*cmath.pi*float(t.phase)*(k//t.dilation))
                          for t in r.terms if k % t.dilation == 0)
                self.assertLess(abs(lhs-rhs), 1e-10, (n, N, a, k))

    def test_known_even_values(self):
        self.assertEqual(bernoulli_number(1), -Q(1, 2))
        self.assertEqual(bernoulli_number(12), -Q(691, 2730))
        self.assertEqual(bernoulli_polynomial(2, Q(1, 2)), -Q(1, 12))
        self.assertEqual(real_li_even_pi_coefficient(2, 0), Q(1, 6))
        self.assertEqual(real_li_even_pi_coefficient(4, 0), Q(1, 90))
        self.assertEqual(real_li_even_pi_coefficient(6, 0), Q(1, 945))
        self.assertEqual(real_li_even_pi_coefficient(2, Q(1, 2)), -Q(1, 12))
        self.assertEqual(real_li_even_pi_coefficient(2, Q(1, 4)), -Q(1, 48))

    def test_complete_fibers_and_composition(self):
        for n, middle, N, a in ((1, 4, 48, 0), (3, 12, 120, -2),
                                 (1680, 6720, 443520, 1)):
            for weight in (2, 3, 4, 8):
                self.assertEqual(compose_full_fiber(n, middle, N, a, weight=weight),
                                 full_fiber_reduction(n, N, a).specialize(weight))
            r = full_fiber_reduction(n, N, a)
            self.assertEqual(r.phase_count, N//n)
            self.assertTrue(r.verify_even_weight())

    def test_exact_phase_maps_canonicalization_and_composition(self):
        p = SparsePhaseSum(2, ((Q(1, 3), 2), (Q(4, 3), 1), (Q(-1, 3), -2)))
        self.assertEqual(p.terms, ((Q(1, 3), Q(3)), (Q(2, 3), Q(-2))))
        self.assertEqual(p.pushforward(2).pushforward(-3), p.pushforward(-6))
        self.assertEqual(p.pushforward(3).terms, ((Q(0), Q(1)),))
        self.assertEqual(canonical_phase(Q(-5, 3)), Q(1, 3))
        self.assertEqual(p + p.scale(-1), SparsePhaseSum(2, ()))

    def test_existing_rational_pi_enclosure(self):
        s = primitive_conjugate_reduction(1680, 443520).specialize(2)
        lo, hi = s.real_interval(64)
        self.assertLess(lo, hi)
        self.assertLess(hi-lo, Q(1, 2**60))
        neg = s.scale(-1).real_interval(64)
        self.assertEqual(neg, (-hi, -lo))

    def test_empty_and_invalid_domains(self):
        self.assertEqual(primitive_conjugate_reduction(6, 30, 2).phase_count, 0)
        self.assertEqual(primitive_conjugate_reduction(6, 30, 2).specialize(2).terms, ())
        for args in ((0, 10), (3, 10), (True, 10), (2, 0), (2, 10, 1.5)):
            with self.assertRaises(ValueError):
                period_reduction(*args)
        for weight in (0, 1, 3, 2.0, True):
            with self.assertRaises(ValueError):
                real_li_even_pi_coefficient(weight, 0)
        with self.assertRaises(ValueError):
            canonical_phase(0.25)
        with self.assertRaises(ValueError):
            SparsePhaseSum(2, ((Q(1, 3), 0.1),))
        with self.assertRaises(ValueError):
            compose_full_fiber(3, 5, 30)


if __name__ == '__main__':
    unittest.main()
