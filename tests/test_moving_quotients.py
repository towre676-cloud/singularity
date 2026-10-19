from fractions import Fraction as Q
import unittest
from singularity.period_observations import RationalConnection,transport_targets,_rf
from singularity.moving_quotients import (construct_quotient,verify_quotient,gauge_quotient,
    verify_overlap,assert_quotient_path,obstruction_at)


class MovingQuotientTests(unittest.TestCase):
    def test_compatibility_gauge_and_explicit_solution(self):
        a=RationalConnection(((0,-1),(0,0)))
        quotient=construct_quotient(a,((1,(0,1)),),((1,(0,1)),))
        self.assertTrue(verify_quotient(quotient));self.assertFalse(quotient.reduced_connection[0][0])
        changed=gauge_quotient(quotient,(((1,1),),))
        self.assertEqual(changed.reduced_connection[0][0],_rf(1)/_rf((1,1)))
        self.assertTrue(verify_overlap(quotient,changed,(((1,1),),)))
        self.assertFalse(verify_overlap(quotient,changed,((2,),)))
        for path in ((0,Q(1,2)),(0,Q(1,4),Q(1,2))):
            out=transport_targets(a,((1,(0,1)),),path,(2,3))['outputs'][0]
            self.assertLessEqual(out['interval'][0],2);self.assertGreaterEqual(out['interval'][1],2)

    def test_leakage_target_loss_zero_and_rank_strata(self):
        a=RationalConnection(((0,0),(0,1)))
        with self.assertRaises(ValueError):construct_quotient(a,((1,(0,1)),))
        obstruction=obstruction_at(a,((1,(0,1)),),Q(0))
        self.assertEqual(obstruction['hidden'],(0,1));self.assertEqual(obstruction['exposure_rates'],(1,))
        with self.assertRaises(ValueError):construct_quotient(a,((1,0),),((0,1),))
        self.assertTrue(verify_quotient(construct_quotient(a,(),())))
        self.assertEqual(construct_quotient(a,((1,0),(0,1))).rank,2)
        # Observable rank of the source-grounded diagonal family: lambda=0
        # loses the constant component, while lambda!=0 retains both modes.
        from singularity.period_observations import differential_closure
        for parameter,rank in ((-1,2),(0,1),(1,2)):
            self.assertEqual(differential_closure(a,((parameter,1),)).rank,rank)

    def test_chart_refuses_gauge_zero(self):
        a=RationalConnection(((0,0),(0,0)),chart=(-2,2))
        quotient=construct_quotient(a,((1,0),),((1,0),))
        changed=gauge_quotient(quotient,(((1,1),),))
        with self.assertRaises(ValueError):assert_quotient_path(changed,(-Q(3,2),Q(0)))

if __name__=='__main__':unittest.main()
