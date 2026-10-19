import copy
import itertools
import unittest
from fractions import Fraction as F
from singularity.arithmetic_automata import QuadraticUnit,ResidueOrbitSystem,replay_arithmetic_receipt
from singularity.observability import apply_word,experiment

class ArithmeticAutomataTests(unittest.TestCase):
    def setUp(self):self.u=QuadraticUnit(2,3,2)
    def test_integer_norm_and_direct_power_oracle(self):
        x,y=1,0
        for i in range(40):
            self.assertEqual(x*x-2*y*y,1)
            s=ResidueOrbitSystem(self.u,12,{'s':(1,0)})
            self.assertEqual(s.remote_residue('s',i),(x%12,y%12))
            x,y=3*x+4*y,2*x+3*y
    def test_exact_cycle_and_original_seed_collisions(self):
        s=ResidueOrbitSystem(self.u,5,{'a':(1,0),'b':(4,0),'original_duplicate_residue':(6,0)})
        self.assertEqual(s.cycle('a')['cycle'],((1,0),(3,2),(2,2),(4,0),(2,3),(3,3)))
        self.assertEqual(s.seed_states['a'],s.seed_states['original_duplicate_residue'])
        self.assertEqual(len(s.seeds),3)
        self.assertEqual(s.cheapest_witness('a','b')['cost'],1)
        self.assertEqual(s.cheapest_witness('a','b')['word'],(0,))
        self.assertIsNone(s.cheapest_witness('a','original_duplicate_residue'))
    def test_partition_refinement_independent_oracle(self):
        s=ResidueOrbitSystem(self.u,7,{'a':(1,0),'b':(6,0)},actions={'u':self.u,'j':'conjugation'},signed_states=True,observations=('x',))
        signatures=[(s.sensor(v,'x'),) for v in s.states]
        while True:
            ids={v:i for i,v in enumerate(sorted(set(signatures)))};parts=[ids[v] for v in signatures]
            new=[(parts[i],tuple(parts[t[i]] for t in s.transitions)) for i in range(len(s.states))]
            newids={v:i for i,v in enumerate(sorted(set(new)))};newparts=[newids[v] for v in new]
            if all((parts[i]==parts[j])==(newparts[i]==newparts[j]) for i in range(len(parts)) for j in range(len(parts))):break
            signatures=new
        actual=s.behavioral_classes()['state_to_class']
        for i,j in itertools.product(range(len(parts)),repeat=2):self.assertEqual(parts[i]==parts[j],actual[i]==actual[j])
    def test_forever_equivalent_and_costs(self):
        s=ResidueOrbitSystem(self.u,5,{'a':(1,0),'b':(4,0)},observations=('norm',),action_costs=[F(3,2)],observation_costs=[2])
        self.assertIsNone(s.cheapest_witness('a','b'))
        self.assertEqual(s.behavioral_classes()['seed_to_class']['a'],s.behavioral_classes()['seed_to_class']['b'])
    def test_huge_decimal_remote_and_conjugation_chronology(self):
        s=ResidueOrbitSystem(self.u,5,{'a':(1,0)},actions={'u':self.u,'j':'conjugation'},signed_states=True)
        digits='9876543210'*600;remainder=0
        for d in digits:remainder=(10*remainder+int(d))%6
        self.assertEqual(s.remote_residue('a',digits),s.cycle('a')['cycle'][remainder])
        self.assertEqual(s.remote_residue('a',-1,allow_negative=True),(3,3))
        sys=s.compile_operator_system();v=[0]*len(s.states);v[s.seed_states['a']]=1
        self.assertNotEqual(apply_word(sys,v,(0,1)),apply_word(sys,v,(1,0)))
        u2=QuadraticUnit(2,17,12)
        for v in ((1,0),(4,-2)):
            self.assertEqual(self.u.apply(u2.apply(v)),u2.apply(self.u.apply(v)))
    def test_norm_congruence_is_not_the_chosen_seed_image(self):
        s=ResidueOrbitSystem(self.u,4,{'s':(1,0)})
        congruence={(x,y) for x in range(4) for y in range(4) if (x*x-2*y*y)%4==1}
        self.assertEqual(len(congruence),4);self.assertEqual(len(s.states),2)
        self.assertNotIn((1,2),s.states)
    def test_receipt_tamper_modulus_one_and_validation(self):
        s=ResidueOrbitSystem(self.u,1,{'s':(-3,-2)})
        self.assertEqual(s.remote_residue('s',100),(0,0));self.assertTrue(replay_arithmetic_receipt(s.receipt()))
        r=copy.deepcopy(s.receipt());r['seed_norms']['s']=0;self.assertFalse(replay_arithmetic_receipt(r))
        with self.assertRaises(ValueError):QuadraticUnit(2,2,1)
        with self.assertRaises(TypeError):QuadraticUnit(True,1,0)
        with self.assertRaises(ValueError):ResidueOrbitSystem(self.u,5,{'s':(1,0)},actions={'j':'conjugation'})
        with self.assertRaises(ValueError):s.remote_residue('s','12x')
        with self.assertRaises(ValueError):s.remote_residue('s',-1)
        with self.assertRaises(ArithmeticError):ResidueOrbitSystem(QuadraticUnit(2,1,0),7,{'a':(0,0),'b':(1,0),'c':(2,0)},max_states=1)
