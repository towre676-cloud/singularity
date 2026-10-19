import copy
import unittest
from fractions import Fraction as F
from singularity.parametric import PolynomialOperatorSystem, symbolic_boundary_system
from singularity.parameter_receipts import parameter_module_receipt,replay_parameter_module_receipt,guarded_specialization
from singularity.observability import observable_closure


def _add(a,b):
    out=dict(a)
    for e,c in b.items():out[e]=out.get(e,0)+c
    return {e:c for e,c in out.items() if c}

def _mul(a,b):
    out={}
    for i,c in a.items():
        for j,d in b.items():out[i+j]=out.get(i+j,0)+c*d
    return {e:c for e,c in out.items() if c}

class ParameterReceiptTests(unittest.TestCase):
    def fixtures(self):
        a={0:-F(1,2),1:1}
        return (PolynomialOperatorSystem(2,[[[0,1],[0,0]]],[[1,0],[0,a]]),PolynomialOperatorSystem(2,[[[1,0],[0,2]]],[[1,a]]))
    def test_false_and_true_exception_independent_minors(self):
        false,true=self.fixtures();a=parameter_module_receipt(false);b=parameter_module_receipt(true)
        self.assertEqual(a['divisor'],[[1,1]]);self.assertEqual(a['exceptions'],[])
        self.assertEqual(b['divisor'],[[-1,2],[1,1]])
        self.assertEqual(b['exceptions'],[{'rational':[1,2],'rank':1}])
        # Independent sparse polynomial 2x2 Leibniz determinant.
        p={0:-F(1,2),1:1};det=_add(_mul({0:1},{e:2*c for e,c in p.items()}),{e:-c for e,c in p.items()})
        self.assertEqual(det,p)
        self.assertTrue(a['atlas']['charts_cover_regular_locus']);self.assertTrue(b['atlas']['charts_cover_regular_locus'])
        for x in (F(1,4),F(1,2),F(3,4)):
            self.assertEqual(observable_closure(false.specialize(x)).rank,2)
            self.assertEqual(observable_closure(true.specialize(x)).rank,1 if x==F(1,2) else 2)
    def test_certificate_tampering(self):
        r=parameter_module_receipt(self.fixtures()[0]);self.assertTrue(replay_parameter_module_receipt(r))
        for change in ('generator','factor','word'):
            c=copy.deepcopy(r)
            if change=='generator':c['chain'][0]['basis'][0][0]=[[2,1]]
            elif change=='factor':c['factors']=[{'factor':[[-1,2],[1,1]],'multiplicity':1,'evidence':'forged'}]
            else:c['charts'][0]['words'][1][1]=[]
            self.assertFalse(replay_parameter_module_receipt(c))
    def test_R5_bounded_attempt_and_specialization(self):
        coords,system=symbolic_boundary_system(5)
        r=parameter_module_receipt(system,limits={'max_dimension':22})
        self.assertEqual(r['state'],'budget_refusal');self.assertGreater(len(coords),22)
        self.assertIn('dimension',r['reason']);self.assertNotIn('generic_rank',r)
        # Finite specialization evidence, never an interval theorem.
        self.assertEqual(observable_closure(system.specialize(F(1,2))).rank,len(coords))
    def test_guarded_rational_function(self):
        s=PolynomialOperatorSystem(2,[[[1,0],[0,2]]],[[1,1]])
        r=parameter_module_receipt(s,denominator={0:-1,1:2})
        for x in (F(1,4),F(3,4)):
            specialized=guarded_specialization(r,x);h=2*x-1
            self.assertEqual(specialized.operators[0],((1/h,0),(0,2/h)))
            self.assertEqual(observable_closure(specialized).rank,2)
        with self.assertRaises(ValueError):guarded_specialization(r,F(1,2))
    def test_algebraic_domain_boundary_and_pole_guard(self):
        g={0:-F(1,2),2:1};s=PolynomialOperatorSystem(1,[[[1]]],[[g]])
        r=parameter_module_receipt(s,domain=(F(2895,4096),F(1)))
        self.assertEqual(r['state'],'complete');self.assertEqual(len(r['exceptions']),1)
        self.assertEqual(r['exceptions'][0]['rank'],0)
        lo,hi=(F(*v) for v in r['exceptions'][0]['interval'])
        self.assertLess(F(2895,4096),lo);self.assertLess(hi,1)
        guarded=parameter_module_receipt(s,denominator=g)
        self.assertEqual(guarded['exceptions'],[])
        self.assertTrue(replay_parameter_module_receipt(guarded))
        for x in (True,0.5,'1/2'):
            with self.assertRaises(TypeError):guarded_specialization(guarded,x)
        with self.assertRaises(ValueError):guarded_specialization(guarded,F(2))
    def test_rank_zero_and_resource_validation(self):
        r=parameter_module_receipt(PolynomialOperatorSystem(2,[],[]))
        self.assertEqual(r['generic_rank'],0);self.assertTrue(replay_parameter_module_receipt(r))
        with self.assertRaises(ValueError):parameter_module_receipt(self.fixtures()[0],limits={'max_steps':True})
