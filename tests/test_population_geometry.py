from fractions import Fraction as Q
from itertools import product
import unittest
from singularity.population_geometry import *

class PopulationGeometryTests(unittest.TestCase):
    def test_binary_multiplicities_moments_and_targets(self):
        pop=WeightedPopulation(tuple(PopulationObject(str(x),(sum(x),),x[0]) for x in product((0,1),repeat=2)))
        self.assertEqual(pushforward_mass(pop),{(0,):1,(1,):2,(2,):1})
        moments=tilted_moments(pop,(2,));self.assertEqual(moments['normalization'],9)
        self.assertEqual(moments['mean'],(Q(4,3),));self.assertEqual(moments['covariance'],((Q(4,9),),))
        self.assertEqual(len(joint_target_mass(pop)),4)
        for i in range(4):self.assertEqual(pop.rank(pop.unrank(i).identifier),i)
        ch=FiniteObservationChannel('second',(0,1),tuple((o.identifier,tuple(int(y==int(o.identifier[-2])) for y in (0,1))) for o in pop.objects))
        with self.assertRaises(ValueError):verify_channel_compression(pop,ch)
        self.assertEqual(sum(pushforward_mass(pop).values()),4)
        signed=WeightedPopulation((PopulationObject('a',(-1,),0,Q(2)),PopulationObject('b',(2,),1,0)))
        self.assertEqual(tilted_moments(signed,(2,))['normalization'],1)
        self.assertEqual(tilted_moments(signed,(2,))['covariance'],((0,),))

    def test_posteriors_and_rejections(self):
        p=WeightedPopulation((PopulationObject('a',(0,),0,3),PopulationObject('b',(0,),1,1)))
        ch=FiniteObservationChannel('noisy',(0,1,2),(('a',(Q(3,4),Q(1,4),0)),('b',(Q(1,4),Q(3,4),0))))
        post=posterior_target(p,ch,0)
        self.assertEqual(post['observation_probability'],Q(5,8));self.assertEqual(post['target_probabilities'],{0:Q(9,10),1:Q(1,10)})
        self.assertEqual(target_risk(p,ch),Q(1,4))
        with self.assertRaises(UnsupportedObservation):posterior_target(p,ch,2)
        with self.assertRaises(ValueError):FiniteObservationChannel('bad',(0,1),(('a',(1,1)),))
        with self.assertRaises(ValueError):WeightedPopulation((PopulationObject('zero',(0,),0,0),))
        with self.assertRaises(TypeError):PopulationObject('float',(0,),0,0.5)

    def test_bayes_and_worst_case_disagree(self):
        pop=WeightedPopulation((PopulationObject('a',(0,),'a',9),PopulationObject('b',(1,),'b',9),PopulationObject('c',(2,),'c',2)))
        cheap=FiniteObservationChannel('majority',(0,1),(('a',(1,0)),('b',(0,1)),('c',(1,0))))
        noise=Q(3,40);balanced=FiniteObservationChannel('balanced',('a','b','c'),tuple((o.identifier,tuple(Q(17,20) if t==o.target else noise for t in ('a','b','c'))) for o in pop.objects))
        result=minimum_expected_target_risk(pop,(cheap,balanced),1)
        self.assertEqual(result['panel'],('majority',));self.assertEqual(result['risk'],Q(1,10))
        self.assertEqual(deterministic_minimax_risk(pop,cheap)['risk'],1)
        self.assertEqual(deterministic_minimax_risk(pop,balanced)['risk'],Q(3,20))
        # Integer quotient fibres supply original tuples; masses survive projection.
        from singularity.integer_quotients import integer_image_certificate,bounded_fibre_population
        cert=integer_image_certificate(((1,1),))
        fibre=bounded_fibre_population(cert,(2,),((0,2),(0,2)))
        original=tuple(fibre.unrank(i) for i in range(fibre.count()))
        p=WeightedPopulation(tuple(PopulationObject(str(x),(sum(x),),x[0]) for x in original))
        self.assertEqual(pushforward_mass(p),{(2,):3});self.assertEqual(len(joint_target_mass(p)),3)

if __name__=='__main__':unittest.main()
