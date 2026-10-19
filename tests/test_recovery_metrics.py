import itertools
import unittest
from fractions import Fraction as F
from singularity.recovery_metrics import (reconstruction_map,box_amplification,target_amplification,rational_size,compare_recovery_designs,optimize_target,verify_target_certificate,select_target_design,vandermonde,vandermonde_uniform_bound,interface_reconstruction_data)

class RecoveryMetricsTests(unittest.TestCase):
    def test_sharp_33_32_box_bounds(self):
        R=reconstruction_map([[1,1],[1,F(17,16)]])
        self.assertEqual(box_amplification(R,[1,1]),(33,32))
        extremes=[tuple(sum(a*b for a,b in zip(r,e)) for r in R) for e in itertools.product((-1,1),repeat=2)]
        self.assertEqual(tuple(max(abs(v[i]) for v in extremes) for i in range(2)),(33,32))
        self.assertEqual(target_amplification(R,[0,1],[1,1]),32)
    def test_dependent_physical_sensor_and_rescaling_noise(self):
        physical=optimize_target([[1],[100]],[1],[1,1])
        rescaled=optimize_target([[1],[100]],[1],[1,100])
        self.assertEqual(physical['objective'],F(1,100));self.assertEqual(rescaled['objective'],1)
    def test_primal_dual_and_tamper(self):
        A=[[1,0],[0,1],[1,1]];g=[1,0];e=[1,1,F(1,4)]
        c=optimize_target(A,g,e);self.assertTrue(verify_target_certificate(A,g,e,c))
        bad=dict(c,objective=c['objective']+1);self.assertFalse(verify_target_certificate(A,g,e,bad))
        self.assertEqual(c['objective'],1)
    def test_finite_menu_minimum_and_preprocessing(self):
        menu=[{'name':'cheap','A':[[1]],'noise':[1],'costs':[1]}, {'name':'clear','A':[[100]],'noise':[1],'costs':[3]}, {'name':'costly','A':[[200]],'noise':[1],'costs':[7]}]
        r=select_target_design(menu,[1],F(1,50));self.assertEqual(r['selected']['name'],'clear')
        a=compare_recovery_designs([{'name':'scale','A':[[1]],'preprocessing':[[100]],'noise':[1]}])[0]
        self.assertEqual(a['amplification'],(1,))
    def test_uniform_vandermonde_interval_bound(self):
        # z=(1,1+q), q in [1/4,1/2]: |z|<=3/2, gap>=1/4.
        bound=vandermonde_uniform_bound(2,F(3,2),F(1,4));self.assertEqual(bound,10)
        for q in (F(1,4),F(1,3),F(1,2)):
            amps=box_amplification(reconstruction_map(vandermonde([1,1+q])),[1,1])
            self.assertTrue(all(a<=bound for a in amps))
    def test_generic_interface_wrapper_and_delay_boundary(self):
        d=interface_reconstruction_data('finite_difference',3,F(1,2))
        self.assertEqual(len(d['coordinates']),13)
        for i,row in enumerate(d['R']):
            for j in range(len(d['coordinates'])):
                self.assertEqual(sum(row[k]*d['A'][k][j] for k in range(len(row))),int(i==j))
        with self.assertRaises(ArithmeticError):interface_reconstruction_data('finite_difference',7,F(1,2))
    def test_validation_and_bits(self):
        self.assertEqual(rational_size([F(1,2),0])['total_bits'],7)
        with self.assertRaises(ValueError):reconstruction_map([[1,1]])
        with self.assertRaises(TypeError):reconstruction_map([[0.5]])
        with self.assertRaises(ValueError):box_amplification([[1]],[-1])
        with self.assertRaises(ArithmeticError):optimize_target([[1],[2]],[1],[1,1],max_active_sets=1)
