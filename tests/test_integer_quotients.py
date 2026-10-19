import copy
import itertools
import unittest
from fractions import Fraction as F
from singularity.integer_quotients import (integer_image_certificate,verify_integer_image_certificate,image_contains,integer_fibre,bounded_fibre_population,pushforward_population,operator_lattice_certificate,apply_lattice_update)

class IntegerQuotientTests(unittest.TestCase):
    def test_smith_exhaustive_rectangular_corpus(self):
        count=0
        for m,n in ((1,3),(2,2),(3,2)):
            for entries in itertools.product((-1,0,1),repeat=m*n):
                A=[entries[i*n:(i+1)*n] for i in range(m)];c=integer_image_certificate(A)
                self.assertTrue(verify_integer_image_certificate(c))
                for x in itertools.product((-1,0,1),repeat=n):
                    y=tuple(sum(a*b for a,b in zip(r,x)) for r in A)
                    self.assertTrue(image_contains(c,y))
                    f=integer_fibre(c,y);p=f['particular']
                    self.assertEqual(y,tuple(sum(a*b for a,b in zip(r,p)) for r in A))
                count+=1
        self.assertEqual(count,837)
    def test_binary_original_fibres(self):
        c=integer_image_certificate([[2,2]])
        self.assertFalse(image_contains(c,[1]))
        p=bounded_fibre_population(c,[2],[(0,1)]*2)
        self.assertEqual(p.count(),2);self.assertEqual([p.unrank(i) for i in range(2)],[(0,1),(1,0)])
        for i in range(2):self.assertEqual(p.rank(p.unrank(i)),i)
        self.assertEqual(pushforward_population(c,[(0,1)]*2),{(0,):1,(2,):2,(4,):1})
    def test_fibres_exhaustive_lexicographic_oracle(self):
        for A in ([[2,1,1]],[[2,0],[0,3]],[[0,0,0]],[[1,1,0],[0,1,1]]):
            c=integer_image_certificate(A);bounds=[(-1,1)]*len(A[0]);states=list(itertools.product(range(-1,2),repeat=len(bounds)))
            groups={}
            for x in states:groups.setdefault(tuple(sum(a*b for a,b in zip(r,x)) for r in A),[]).append(x)
            self.assertEqual(sum(pushforward_population(c,bounds).values()),len(states))
            for y,xs in groups.items():
                p=bounded_fibre_population(c,y,bounds);self.assertEqual(p.count(),len(xs))
                self.assertEqual([p.unrank(k) for k in range(p.count())],xs)
                self.assertEqual([p.rank(x) for x in xs],list(range(len(xs))))
    def test_saturated_kernel_regression(self):
        c=integer_image_certificate([[2,1,1]]);f=integer_fibre(c,[0]);p=bounded_fibre_population(c,[0],[(-2,2)]*3)
        self.assertTrue(p.contains((-1,1,1)))
        self.assertEqual(len(f['kernel_basis']),2)
        self.assertFalse(all(v%2==0 for v in (-1,1,1)[1:]))
    def test_row_clearing_and_operator_words(self):
        c=integer_image_certificate([[F(1,2),F(1,2)]])
        self.assertEqual(c['row_scales'],[2]);self.assertEqual(c['A'],[[1,1]])
        swap=operator_lattice_certificate(c,[[0,1],[1,0]])
        for x in itertools.product(range(-2,3),repeat=2):
            y=(sum(x),)
            for _ in range(4):y=apply_lattice_update(c,swap,y)
            self.assertEqual(y,(sum(x),))
        with self.assertRaises(ValueError):operator_lattice_certificate(c,[[F(1,2),0],[0,1]])
        with self.assertRaises(ValueError):operator_lattice_certificate(c,[[1,0],[0,2]])
        fractional=integer_image_certificate([[2,0],[0,1]])
        induced=operator_lattice_certificate(fractional,[[0,1],[1,0]])
        self.assertEqual(apply_lattice_update(fractional,induced,[2,3]),(6,1))
        with self.assertRaises(ValueError):apply_lattice_update(fractional,induced,[1,3])
    def test_tamper_rankzero_and_limits(self):
        c=integer_image_certificate([[2,4],[0,0]])
        for key in ('U','V'):
            d=copy.deepcopy(c);d[key][0][0]*=2;self.assertFalse(verify_integer_image_certificate(d))
        d=copy.deepcopy(c);d['diagonal'][0]=3;self.assertFalse(verify_integer_image_certificate(d))
        d=integer_image_certificate([[F(1,2),F(1,2)]]);d['row_scales'][0]=4;self.assertFalse(verify_integer_image_certificate(d))
        z=integer_image_certificate([[0,0]])
        self.assertTrue(image_contains(z,[0]));self.assertFalse(image_contains(z,[1]))
        self.assertEqual(len(integer_fibre(z,[0])['kernel_basis']),2)
        with self.assertRaises(TypeError):integer_image_certificate([[True]])
        with self.assertRaises(ArithmeticError):integer_image_certificate([[2,3]],max_operations=1)
        with self.assertRaises(ValueError):bounded_fibre_population(c,[0,0],[])
