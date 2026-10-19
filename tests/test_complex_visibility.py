from fractions import Fraction as Q
import unittest
from singularity.complex_visibility import *
from singularity.examples import GRAPHS


class ComplexVisibilityTests(unittest.TestCase):
    def test_geometric_series_and_zero_count(self):
        self.assertEqual(combinatorial_tail(1,3,Q(1,2)),Q(1,8))
        # Roots of 1+z+z²+z³ are -1,+i,-i, independently factored.
        count=factored_polynomial_zero_count((1,1,1,1),(-1,(0,1),(0,-1)),0,Q(1,2))
        self.assertEqual(count['zero_count'],0)
        zero=factored_polynomial_zero_count((-Q(1,4),1),(Q(1,4),),0,Q(1,2))
        self.assertEqual(zero['zero_count'],1);self.assertFalse(zero['zero_free'])

    def test_zero_leading_coefficient_cannot_certify_zero_polynomial(self):
        # A supplied factorization of 0=0*(z-r) carries no root information.
        with self.assertRaises(ValueError):factored_polynomial_zero_count((0,0),(0,),2,Q(1,2))
        with self.assertRaises(ValueError):factored_polynomial_zero_count((0,),(),2,Q(1,2))
        with self.assertRaises(ValueError):factored_polynomial_zero_count((1,0),(0,),2,Q(1,2))
    def test_subdivision_and_strict_boundary(self):
        rectangle=(-Q(9,10),Q(9,10),-Q(1,10),Q(1,10))
        self.assertFalse(polynomial_rectangle_certificate((1,0,1),rectangle,max_depth=0)['zero_free'])
        receipt=polynomial_rectangle_certificate((1,0,1),rectangle,max_depth=4)
        self.assertTrue(receipt['zero_free']);self.assertGreater(len(receipt['leaves']),1)
        with self.assertRaises(ValueError):factored_polynomial_zero_count((-1,1),(1,),0,1)

    def test_directed_transcendentals(self):
        for p in (2,3,5):
            a,b=root_interval(Q(1,p),2)
            self.assertLessEqual(a*a,Q(1,p));self.assertGreaterEqual(b*b,Q(1,p))
            domain=prime_image_disc(p,2,Q(1,25000));self.assertGreater(domain['radius'],0)
            lo,hi=log_interval(p);self.assertLess(lo,hi)

    def test_fourfold_reference_improvement(self):
        receipt=improved_visibility_certificate(GRAPHS['spectral_g'],GRAPHS['spectral_h'],Q(1,2),2,Q(1,25000))
        self.assertEqual(receipt['delta'],Q(3,32))
        self.assertGreater(receipt['local_real_part_lower'],0)
        self.assertEqual(receipt['radius']/Q(1,100000),4)
        with self.assertRaises(ValueError):improved_visibility_certificate(GRAPHS['spectral_g'],GRAPHS['spectral_h'],Q(1,2),3,Q(1,25000))

if __name__=='__main__':unittest.main()
