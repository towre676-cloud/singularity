"""Exact metric identities and declared finite-pool selection contracts."""
from fractions import Fraction as F
import unittest
from singularity.experiment_design import (
    Experiment, RationalMetric, integral_inner_product, integral_distance_squared,
    minimum_separation, monomial_gram, nearest_candidate,
    orthogonal_polynomial_basis, rank_experiments,
)


class ExactPolynomialMetricTests(unittest.TestCase):
    def test_gram_integrates_monomials(self):
        gram = monomial_gram(4,F(-1),F(2))
        for i in range(5):
            for j in range(5):
                self.assertEqual(gram[i][j],(F(2)**(i+j+1)-F(-1)**(i+j+1))/(i+j+1))
        # Coefficient dot product is zero, but integral of 1*q is 1/2.
        self.assertEqual(integral_inner_product((1,0),(0,1)),F(1,2))
        difference = (0,-1,2,-1)
        self.assertEqual(integral_inner_product(difference,difference),F(1,105))
        basis = orthogonal_polynomial_basis(3)
        self.assertEqual(basis.coordinates(difference),(F(-1,12),F(1,10),F(1,2),F(-1)))
        self.assertEqual(basis.norms_squared,(F(1),F(1,12),F(1,180),F(1,2800)))
        self.assertEqual(basis.polynomial(basis.coordinates(difference)),difference)

    def test_polynomial_quadrature_identity(self):
        # Simpson quadrature is exact on the cubic product (1+2q)(3-q+q^2).
        p,q = (1,2),(3,-1,1)
        value = lambda c,x: sum(a*x**i for i,a in enumerate(c))
        quadrature = (value(p,F(0))*value(q,F(0))+4*value(p,F(1,2))*value(q,F(1,2))
                      +value(p,F(1))*value(q,F(1)))/6
        self.assertEqual(integral_inner_product(p,q),quadrature)
        self.assertEqual(integral_inner_product({0:1,1:2},{0:3,1:-1,2:1}),quadrature)

    def test_ldl_reconstruction_and_positive_definiteness(self):
        metric = RationalMetric(monomial_gram(4))
        lower,diagonal = metric.ldl
        for i in range(5):
            for j in range(5):
                self.assertEqual(sum(lower[i][k]*diagonal[k]*lower[j][k] for k in range(5)),metric.gram[i][j])
        for bad in (((1,2),(0,1)),((1,1),(1,1)),((1,0),(0,-1)),()):
            with self.assertRaises(ValueError): RationalMetric(bad)

    def test_coordinate_pullback_preserves_geometry(self):
        metric = RationalMetric(monomial_gram(2))
        transform = ((1,2),(0,1),(1,-1))
        pulled = metric.pullback(transform)
        u,v = (F(2),F(-3)),(F(4),F(1))
        apply = lambda x: tuple(sum(row[j]*x[j] for j in range(2)) for row in transform)
        self.assertEqual(pulled.inner(u,v),metric.inner(apply(u),apply(v)))
        self.assertEqual(pulled.distance_squared(u,v),metric.distance_squared(apply(u),apply(v)))
        with self.assertRaises(ValueError): metric.pullback(((1,1),(2,2),(3,3)))

    def test_monic_shifted_legendre_basis(self):
        result = orthogonal_polynomial_basis(4)
        basis = tuple(p[:i+1] for i,p in enumerate(result.polynomials))
        self.assertEqual(basis[:3],((F(1),),(F(-1,2),F(1)),(F(1,6),F(-1),F(1))))
        for i,p in enumerate(basis):
            self.assertEqual(p[-1],1)
            for j,q in enumerate(basis):
                if i != j: self.assertEqual(integral_inner_product(p,q),0)

    def test_whole_curve_does_not_imply_fixed_q_separation(self):
        self.assertEqual(integral_distance_squared((F(-1,2),1),(0,)),F(1,12))
        self.assertEqual(F(-1,2)+F(1,2),0)

    def test_exact_input_contract(self):
        for bad in (True,0.5):
            with self.assertRaises(TypeError): integral_inner_product((bad,),(1,))
            with self.assertRaises(TypeError): RationalMetric(((bad,),))
        with self.assertRaises(ValueError): monomial_gram(True)
        with self.assertRaises(ValueError): monomial_gram(1,1,0)


class ExperimentSelectionTests(unittest.TestCase):
    def setUp(self): self.metric = RationalMetric(((1,0),(0,1)))

    def test_separation_and_strict_noise_guarantee(self):
        separation = minimum_separation({'a':(0,0),'b':(3,0),'c':(0,4)},self.metric)
        self.assertEqual((separation.delta_squared,separation.closest_pairs),(9,(('a','b'),)))
        self.assertTrue(separation.guarantees_identification(F(7,5)))
        self.assertFalse(separation.guarantees_identification(F(3,2)))
        self.assertFalse(minimum_separation(((1,2),(1,2)),self.metric).guarantees_identification(0))

    def test_nearest_candidate_ties_and_error_bound(self):
        candidates = {'a':(0,0),'b':(3,0)}
        result = nearest_candidate((1,0),candidates,self.metric,error_bound_squared=1)
        self.assertEqual(result.nearest_labels,('a',))
        self.assertTrue(result.certified_unique)
        result = nearest_candidate((F(3,2),0),candidates,self.metric,error_bound_squared=F(9,4))
        self.assertEqual(result.nearest_labels,('a','b'))
        self.assertFalse(result.certified_unique)
        result = nearest_candidate((1,0),candidates,self.metric,error_bound_squared=F(1,4))
        self.assertTrue(result.margin_guarantee)
        self.assertFalse(result.within_declared_error)
        self.assertFalse(result.certified_unique)
        result = nearest_candidate((0,0),candidates,self.metric,error_bound_squared=0)
        self.assertTrue(result.certified_unique)

    def test_finite_pool_cost_and_noise_scores(self):
        a = Experiment('a',{'left':(0,0),'right':(4,0)},self.metric,cost=2,noise_squared=1)
        b = Experiment('b',{'left':(0,0),'right':(3,0)},self.metric,cost=1,noise_squared=F(1,4))
        scores = rank_experiments((a,b))
        self.assertEqual([r.name for r in scores],['b','a'])
        self.assertEqual([r.score for r in scores],[36,8])
        self.assertTrue(all(r.robust for r in scores))
        self.assertEqual(rank_experiments(()),())
        with self.assertRaises(ValueError): rank_experiments((a,a))
        with self.assertRaises(ValueError): rank_experiments((a,Experiment('c',{'a':(0,0),'b':(4,0)},self.metric)))

    def test_invalid_costs_noise_and_candidate_counts(self):
        for kwargs in ({'cost':0},{'cost':-1},{'noise_squared':0},{'noise_squared':-1}):
            with self.assertRaises(ValueError): Experiment('x',((0,0),(1,0)),self.metric,**kwargs)
        with self.assertRaises(TypeError): Experiment('x',((0,0),(1,0)),self.metric,cost=1.0)
        with self.assertRaises(ValueError): minimum_separation(((0,0),),self.metric)


if __name__ == '__main__': unittest.main()
