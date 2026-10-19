from fractions import Fraction as Q
import random
import unittest
from perfectpower.period_matrix_balls import (inverse_matrix_ball, multiply_matrix_balls,
    recognize_integral_matrix, marked_legendre_monodromy, exact_inverse, verify_marked_legendre_monodromy)
from perfectpower.certified_period_transport import Gaussian as G, rownorm, certified_transport


class PeriodMatrixBallTests(unittest.TestCase):
    def test_inverse_bound_encloses_rational_complex_perturbations(self):
        rng = random.Random(20261006)
        centre = [[G(2), G(0, Q(1, 3))], [G(Q(1, 4)), G(3)]]
        error = Q(1, 20)
        receipt = inverse_matrix_ball(centre, error)
        inverse = [[G.parse(v) for v in row] for row in receipt['matrix']]
        bound = Q(receipt['row_error_bound'])
        for _ in range(100):
            actual = [[v+G(Q(rng.randrange(-4, 5), 400), Q(rng.randrange(-4, 5), 400))
                       for v in row] for row in centre]
            self.assertLessEqual(rownorm([[v-w for v, w in zip(row, base)]
                                         for row, base in zip(actual, centre)]), error)
            exact = exact_inverse(actual)
            self.assertLessEqual(rownorm([[v-w for v, w in zip(row, base)]
                                         for row, base in zip(exact, inverse)]), bound)

    def test_product_bound_and_pivoting(self):
        inverse = inverse_matrix_ball([[0, 2], [3, 0]], 0)
        self.assertEqual(inverse['matrix'], [[['0', '0'], ['1/3', '0']], [['1/2', '0'], ['0', '0']]])
        product = multiply_matrix_balls([[1, 0], [0, 1]], '1/10', [[2, 0], [0, 2]], '1/20')
        self.assertEqual(Q(product['row_error_bound']), Q(51, 200))
        self.assertTrue(product['certified_under_input_enclosures'])

    def test_inverse_rejects_uncertainty_and_singular_centres(self):
        for matrix, error in [([[1]], 1), ([[0]], 0), ([[1]], -1), ([[1, 2]], 0)]:
            with self.assertRaises(ValueError):
                inverse_matrix_ball(matrix, error)

    def test_recognition_requires_integrality_and_row_bound(self):
        result = recognize_integral_matrix([['101/100', '199/100'], [0, '99/100']], '1/40', symplectic=True)
        self.assertEqual(result['candidate'], [[1, 2], [0, 1]])
        self.assertTrue(result['integrality_premise_required'])
        for matrix, error, symplectic in [([[1]], '1/2', False), ([['3/4']], '1/10', False),
                ([[[1, '1/4']]], '1/10', False), ([[2, 0], [0, 1]], 0, True),
                ([[1]], 0, True), ([['99/100', '1/100'], [0, 1]], '3/200', False)]:
            with self.assertRaises(ValueError):
                recognize_integral_matrix(matrix, error, symplectic=symplectic)

    def test_marked_constant_loop_and_open_path_rejection(self):
        result = marked_legendre_monodromy(['1/2', '1/2'])
        self.assertEqual(result['monodromy'], [[1, 0], [0, 1]])
        self.assertLess(Q(result['enclosure']['row_error_bound']), Q(1, 2))
        with self.assertRaises(ValueError):
            marked_legendre_monodromy(['1/2', '9/16'])

    def test_monodromy_replay_binds_every_field_and_external_path(self):
        import copy
        path=['1/2','1/2']
        receipt=marked_legendre_monodromy(path)
        self.assertTrue(verify_marked_legendre_monodromy(path,receipt))
        for mutate in (lambda r:r['monodromy'][0].__setitem__(0,True),
                       lambda r:r['enclosure'].__setitem__('row_error_bound','0'),
                       lambda r:r.__setitem__('integrality_argument','different marking'),
                       lambda r:r['initial'].__setitem__('seed_terms',47)):
            bad=copy.deepcopy(receipt);mutate(bad)
            self.assertFalse(verify_marked_legendre_monodromy(path,bad))
        self.assertFalse(verify_marked_legendre_monodromy(['1/2','9/16'],receipt))

    def test_outward_rounding_encloses_exponential_series(self):
        for bits in (16,32,128):
            result=certified_transport([[1]],['0','1/8'],order=8,rounding_bits=bits)
            lower=sum((Q(1,8)**k/Q(__import__('math').factorial(k)) for k in range(40)),Q(0))
            upper=lower+Q(1,8)**40/Q(__import__('math').factorial(40))/(1-Q(1,8*41))
            centre=Q(result['matrix'][0][0][0]);error=Q(result['row_error_bound'])
            self.assertLessEqual(centre-error,lower)
            self.assertGreaterEqual(centre+error,upper)
            self.assertLessEqual(centre.denominator,1<<bits)
        for bits in (1,True,5000):
            with self.assertRaises(ValueError):certified_transport([[1]],['0','1/8'],rounding_bits=bits)


if __name__ == '__main__':
    unittest.main()
