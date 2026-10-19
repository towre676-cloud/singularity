from fractions import Fraction as Q
from itertools import product
import unittest
from singularity.monodromy_experiments import MonodromyLanguage,bounded_robust_experiments,_mul


class MonodromyTests(unittest.TestCase):
    def setUp(self):self.language=MonodromyLanguage((((1,1),(0,1)),((1,0),(1,1))),((1,0),))
    def test_chronology_and_all_word_closure(self):
        l=self.language
        self.assertEqual(l.reading((1,0),0,(0,1)),1)
        self.assertEqual(l.reading((1,0),0,(1,0)),2)
        self.assertEqual(l.closure().rank,2)
        for d in ((1,0),(0,1),(1,-1)):
            e=l.cheapest(d)
            brute=min((len(w),w)for n in range(7)for w in product(range(2),repeat=n)if l.reading(d,0,w))
            self.assertEqual(e.cost,brute[0])

    def test_gauge_and_inverse_readings_exhaustively(self):
        for s in (((1,1),(0,1)),((2,0),(0,3)),((0,1),(1,0))):
            transformed=self.language.gauge(s,'changed')
            v=(Q(2),Q(-3));sv=tuple(sum((x*y for x,y in zip(row,v)),Q(0))for row in s)
            for n in range(7):
                for word in product(range(2),repeat=n):
                    self.assertEqual(self.language.reading(v,0,word),transformed.reading(sv,0,word))
        inverses=self.language.with_inverses((2,3))
        self.assertEqual(inverses.reading((2,3),0,(0,2)),2)
        with self.assertRaises(ValueError):self.language.with_inverses((0,1))
        with self.assertRaises(ValueError):self.language.gauge(((1,0),(0,0)),'singular')

    def test_more_expensive_witness_is_robust(self):
        l=self.language;d=(0,Q(1,100))
        self.assertEqual(l.cheapest(d).cost,1)
        rows=bounded_robust_experiments(l,d,4,Q(1,100))
        robust=next(row for row in rows if row[-1])
        self.assertEqual(robust[0],3)
        self.assertTrue(all(abs(row[3])<=Q(1,50)for row in rows if row[0]<3))

    def test_singular_loop_is_not_monodromy(self):
        for geometric in (False,True):
            with self.assertRaises(ValueError):
                MonodromyLanguage((((1,0),(0,0)),),((1,0),),geometric=geometric)

if __name__=='__main__':unittest.main()
