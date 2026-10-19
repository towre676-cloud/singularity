from fractions import Fraction as Q
import unittest
from dataclasses import replace
from singularity.period_observations import (RationalConnection,differential_closure,
    verify_differential_closure,transport_targets,legendre_connection,legendre_series,
    legendre_quadrature)


class PeriodObservationTests(unittest.TestCase):
    def test_nilpotent_outputs_against_explicit_polynomial(self):
        a=RationalConnection(((0,1,0),(0,0,0),(0,0,2)))
        c=differential_closure(a,((1,0,0),))
        self.assertEqual(c.rank,2);self.assertTrue(verify_differential_closure(a,c))
        self.assertEqual(c.scalar_equations[0]['order'],2)
        for initial in ((2,3,5),(-1,2,0),(0,0,7)):
            for t in (Q(0),Q(1,8),Q(1,4)):
                out=transport_targets(a,((1,0,0),),(0,t),initial)['outputs'][0]
                self.assertLessEqual(out['interval'][0],initial[0]+t*initial[1])
                self.assertGreaterEqual(out['interval'][1],initial[0]+t*initial[1])

    def test_zero_full_and_pivot_chart(self):
        a=RationalConnection(((0,1),(0,0)))
        self.assertEqual(differential_closure(a,((0,0),)).rank,0)
        self.assertEqual(differential_closure(a,((1,0),(0,1))).rank,2)
        pivot=differential_closure(RationalConnection(((0,0),(0,0))),(((0,1),0),))
        self.assertIn((Q(0),Q(1)),pivot.excluded_polynomials)
        with self.assertRaises(TypeError):RationalConnection(((0.1,),))
        pole=RationalConnection((({'numerator':(1,), 'denominator':(0,1)},),))
        with self.assertRaises(ValueError):transport_targets(pole,((1,),),(-Q(1,2),Q(1,2)),(1,))

    def test_initial_derivative_uncertainty_is_not_dropped(self):
        a=RationalConnection(((0,1),(0,0)))
        out=transport_targets(a,((1,0),),(0,Q(1,2)),(1,2),(Q(1,10),Q(1,5)))['outputs'][0]
        self.assertGreaterEqual(out['initial_error'],Q(1,5))
        self.assertLessEqual(out['interval'][0],Q(9,5))
        self.assertGreaterEqual(out['interval'][1],Q(11,5))

    def test_verifier_rejects_closed_but_ungenerated_or_dependent_basis(self):
        from singularity.period_observations import _rf
        a=RationalConnection(((0,0),(0,0)))
        valid=differential_closure(a,((1,0),))
        z,o=_rf(0),_rf(1)
        forged=replace(valid,basis=((o,z),(z,o)),reduced_connection=((z,z),(z,z)),
                       target_coordinates=((o,z),))
        self.assertFalse(verify_differential_closure(a,forged))
        dependent=replace(forged,basis=((o,z),(o,z)))
        self.assertFalse(verify_differential_closure(a,dependent))

    def test_source_legendre_independent_series_and_quadrature(self):
        a=legendre_connection();seed,radii=legendre_series(Q(1,2),48)
        c=differential_closure(a,((1,0),));self.assertEqual(c.rank,2)
        out=transport_targets(a,((1,0),),(Q(1,2),Q(9,16)),seed,radii)['outputs'][0]
        exact,error=legendre_series(Q(9,16),80)
        self.assertLessEqual(out['interval'][0],exact[0])
        self.assertGreaterEqual(out['interval'][1],exact[0]+error[0])
        qlo,qhi=legendre_quadrature(Q(9,16),64)
        self.assertLessEqual(qlo,out['interval'][0]);self.assertGreaterEqual(qhi,out['interval'][1])

if __name__=='__main__':unittest.main()
