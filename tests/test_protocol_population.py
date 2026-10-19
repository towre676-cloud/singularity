import unittest,itertools,random
from fractions import Fraction as Q
from singularity.protocol_population import *

def tiny(budget=100):
    alphabet=ProtocolAlphabet(('0','2'),(0,2),(1,2),((0,),(2,)))
    grammar=DeterministicProtocolGrammar(('q',),'q',('q',),(('q','0','q'),('q','2','q')))
    return ProtocolPopulation(alphabet,grammar,ProtocolResources(budget,(4,),3,1,1), (TerminalSensor('a',1),TerminalSensor('b',1)))

class ProtocolTests(unittest.TestCase):
    def test_22_6_and_independent_products(self):
        for budget,expected in ((100,22),(4,6)):
            p=tiny(budget);oracle=[]
            for length in range(1,4):
                for word in itertools.product(('0','2'),repeat=length):
                    heat=sum(map(int,word));switch=sum(a!=b for a,b in zip(word,word[1:]))
                    cost=2+length+Q(heat,2)
                    if heat<=4 and switch<=1 and cost<=budget:
                        for s in ('a','b'):oracle.append((word,s))
            self.assertEqual(p.count(),expected);self.assertEqual(set((r.word,r.sensor) for r in p.iter_protocols()),set(oracle))
            for i in range(p.count()):self.assertEqual(p.rank(p.unrank(i)),i)
            for prefix in ((),('0',),('2','0')):
                self.assertEqual(p.count(prefix),sum(w[:len(prefix)]==prefix for w,s in oracle))
                self.assertEqual(p.conditional_count(prefix,'a'),sum(w[:len(prefix)]==prefix and s=='a' for w,s in oracle))
            self.assertTrue(verify_completion_certificate(p,p.completion_certificate()))
    def test_random_tiny_dfas_independent_enumeration(self):
        rng=random.Random(27)
        for _ in range(20):
            transitions=tuple((q,a,rng.choice(('a','b'))) for q in ('a','b') for a in ('x','y') if rng.randrange(4))
            g=DeterministicProtocolGrammar(('a','b'),'a',('b',),transitions)
            p=ProtocolPopulation(ProtocolAlphabet(('x','y'),(0,1),(Q(1,2),1),((0,),(1,))),g,ProtocolResources(3,(2,),4,2), (TerminalSensor('s'),))
            oracle=[];delta={(q,a):r for q,a,r in transitions}
            for n in range(1,5):
                for w in itertools.product(('x','y'),repeat=n):
                    q='a'
                    for a in w:q=delta.get((q,a))
                    if q=='b' and sum(a=='y' for a in w)<=2 and sum(a!=b for a,b in zip(w,w[1:]))<=2 and sum(Q(1,2) if a=='x' else 1 for a in w)<=3:oracle.append(w)
            self.assertEqual(p.count(),len(oracle));self.assertEqual({x.word for x in p.iter_protocols()},set(oracle))
    def test_invalid_zero_cost_empty_unreachable_and_capabilities(self):
        with self.assertRaises(ValueError):ProtocolAlphabet(('a',),(0,),(0,),((),))
        a=ProtocolAlphabet(('a',),(0,),(1,),((),))
        with self.assertRaises(ValueError):ProtocolPopulation(a,DeterministicProtocolGrammar(('q',),'q',('q',),(('q','a','q'),('q','a','q'))),ProtocolResources(2,(),2),(TerminalSensor('s'),))
        p=ProtocolPopulation(a,DeterministicProtocolGrammar(('q','u'),'q',('u',),(('q','a','q'),)),ProtocolResources(2,(),2),(TerminalSensor('s'),))
        self.assertEqual(p.count(),0)
        with self.assertRaises(ValueError):p.unrank(0)
        p=ProtocolPopulation(a,DeterministicProtocolGrammar(('q',),'q',('q',),(('q','a','q'),)),ProtocolResources(2,(),2,nonempty=False),(TerminalSensor('s',requires=('cap',)),))
        self.assertEqual(p.count(),0)
    def test_complete_cheapest_search(self):
        p=tiny();result=cheapest_robust_protocol(p,lambda protocol:(0,sum(p.amplitudes(protocol))),('a','b'))
        self.assertEqual(result['status'],'optimal');self.assertEqual(result['cost'],4)
        self.assertEqual(result['population_count'],22)
        for row in result['excluded_no_more_expensive']:self.assertEqual(row['failing_pair'],('a','b'))


    def test_population_resource_and_sensor_mapping_contracts(self):
        p=tiny()
        with self.assertRaises(ValueError):cheapest_robust_protocol(p,lambda x:(0,1),('same','same'))
        from singularity.thermal_diagnostics import build_plate_candidates
        a=ProtocolAlphabet(('on',),(1,),(1,),((),));g=DeterministicProtocolGrammar(('q',),'q',('q',),(('q','on','q'),))
        small=ProtocolPopulation(a,g,ProtocolResources(2,(),1),(TerminalSensor('center'),))
        with self.assertRaises(ValueError):small.compile_pool(build_plate_candidates(4)[:2])
        pool=small.compile_pool(build_plate_candidates(4)[:2],sensor_indices={'center':1})
        self.assertEqual(pool.size,1)
        with self.assertRaises(ValueError):ProtocolPopulation(a,g,ProtocolResources(2,(),1),(TerminalSensor('s'),),max_states=0)
