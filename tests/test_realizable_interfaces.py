import copy
import itertools
import unittest
from fractions import Fraction as F
from singularity.graph import Graph
from singularity.charges import charge_interface
from singularity.realizable_interfaces import (frontier_vectors,charge_relaxation_contains,tree_family,dominating_family,block_isomorphism_key,complete_bounded_exclusion,threshold_dominating_exclusion)

class RealizableInterfaceTests(unittest.TestCase):
    def test_formal_frontiers_are_not_graphs(self):
        f=frontier_vectors();self.assertEqual(f['terminal_edge']['annihilator'],(0,0))
        self.assertEqual(f['edge_free']['annihilator'],(0,))
        self.assertEqual(f['terminal_edge']['interior_volumes'],(19,15,13))
        self.assertEqual(f['edge_free']['interior_volumes'],(6,4))
    def test_charge_relaxations_never_reject_tiny_graphs(self):
        edges=tuple(itertools.combinations(range(4),2))
        for mask in range(64):
            g=Graph(4,[e for i,e in enumerate(edges) if mask>>i&1]);c=charge_interface(g,(0,1),3)
            self.assertTrue(charge_relaxation_contains(c,2))
        bad=copy.deepcopy(c);first=next(iter(bad['charges']));e=next(iter(bad['charges'][first]));bad['charges'][first][e]+=1
        self.assertFalse(charge_relaxation_contains(bad,2))
        bad=copy.deepcopy(c);poly=bad['charges'].pop((0,(0,0)));bad['charges'][0,(2,0)]=poly
        self.assertFalse(charge_relaxation_contains(bad,2))
    def test_tree_constructor_completeness_independent_edge_subsets(self):
        for n in range(2,6):
            expected=set();possible=tuple(itertools.combinations(range(n),2))
            for edges in itertools.combinations(possible,n-1):
                g=Graph(n,edges)
                if g.connected:expected.add(g.edges)
            actual={g.edges for g in tree_family(n) if g.n==n}
            self.assertEqual(actual,expected);self.assertEqual(len(actual),n**(n-2))
    def test_two_complete_bounded_exclusions(self):
        trees=complete_bounded_exclusion(tree_family(5));dom=complete_bounded_exclusion(dominating_family(4))
        self.assertEqual(trees['constructor_count'],145);self.assertEqual(dom['constructor_count'],76)
        self.assertEqual(trees['state'],'complete_bounded_exclusion');self.assertEqual(dom['state'],'complete_bounded_exclusion')
        self.assertEqual(trees['surviving_nonisomorphic_groups'],0);self.assertEqual(dom['surviving_nonisomorphic_groups'],0)
    def test_structural_threshold_exclusion(self):
        a=threshold_dominating_exclusion(11);b=threshold_dominating_exclusion(38)
        self.assertEqual(a['maximum_interior_order'],2**20-1);self.assertEqual(b['maximum_interior_order'],2**74-1)
    def test_preflight_and_canonical_terminal_swap(self):
        g=Graph(4,[(0,2),(2,3),(3,1)]);h=Graph(4,[(1,2),(2,3),(3,0)])
        self.assertEqual(block_isomorphism_key(g),block_isomorphism_key(h))
        with self.assertRaises(ArithmeticError):complete_bounded_exclusion(tree_family(4),max_profiles=1)
