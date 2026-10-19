import random
import unittest
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations
from singularity.reset_policies import (ResetExperimentFamily,observation_cells,
    minimum_reset_policy,verify_reset_policy,replay_policy,reset_family_from_diagnostics)


def independent_tree_value(family, belief, depth):
    """Finite-depth exhaustive tree recursion, direct inequalities only."""
    if len({family.targets[c] for c in belief})<=1:return F(0)
    if not depth:return None
    best=None
    for e in range(len(family.costs)):
        ends=sorted({z for c in belief for z in family.intervals[e][c]})
        samples=ends+[(a+b)/2 for a,b in zip(ends,ends[1:])]
        children={tuple(c for c in belief if family.intervals[e][c][0]<=y<=family.intervals[e][c][1]) for y in samples}
        values=[independent_tree_value(family,c,depth-1) for c in children if c]
        if values and all(v is not None for v in values):
            value=family.costs[e]+max(values)
            best=value if best is None else min(best,value)
    return best


class ResetTests(unittest.TestCase):
    def fixture(self):
        return ResetExperimentFamily(('A','B','C','D'),('base','left','right'),(1,1,1),
            (((0,0),(0,0),(1,1),(1,1)),((0,0),(1,1),(0,0),(0,0)),((0,0),(0,0),(0,0),(1,1))))

    def test_endpoint_cell_semantics(self):
        f=ResetExperimentFamily(('a','b','c','d'),('x',),(1,),(((0,1),(1,2),(1,1),(0,2)),))
        cells=observation_cells(f,0)
        for cell in cells:
            y=cell['representative']
            self.assertEqual(cell['candidates'],tuple(c for c in range(4) if f.intervals[0][c][0]<=y<=f.intervals[0][c][1]))
        shared=next(c for c in cells if c['lower']==c['upper']==1)
        self.assertEqual(shared['candidates'],(0,1,2,3))
        self.assertTrue(shared['lower_closed']);self.assertTrue(shared['upper_closed'])
        self.assertEqual(cells[0]['candidates'],())
        self.assertEqual(cells[-1]['candidates'],())

    def test_adaptive_two_static_three(self):
        f=self.fixture();p=minimum_reset_policy(f)
        self.assertEqual(p['cost'],2);self.assertTrue(verify_reset_policy(f,p))
        for subset in combinations(range(3),2):
            readings=[tuple(f.intervals[e][c][0] for e in subset) for c in range(4)]
            self.assertLess(len(set(readings)),4)
        self.assertEqual(len({tuple(f.intervals[e][c][0] for e in range(3)) for c in range(4)}),4)
        for c in range(4):
            node=p['root']; observations=[]
            while node['experiment'] is not None:
                e=node['experiment'];y=f.intervals[e][c][0];observations.append(y)
                node=next(b['child'] for b in node['branches'] if c in b['candidates'])
            result=replay_policy(f,p,observations)
            self.assertEqual(result['target'],f.targets[c]);self.assertLessEqual(result['cost'],p['cost'])
        self.assertEqual(replay_policy(f,p,(99,))['status'],'model_rejected')

    def test_random_independent_tree_oracle(self):
        rng=random.Random(501)
        for _ in range(25):
            k=3;e=3
            intervals=[]
            for i in range(e):
                row=[]
                for c in range(k):
                    center=F(rng.randrange(5),2);radius=F(rng.randrange(2),2)
                    row.append((center-radius,center+radius))
                intervals.append(tuple(row))
            f=ResetExperimentFamily(tuple(range(k)),tuple(range(e)),(1,2,3),tuple(intervals))
            result=minimum_reset_policy(f)
            self.assertEqual(result['cost'],independent_tree_value(f,tuple(range(k)),k-1))
            self.assertTrue(verify_reset_policy(f,result))

    def test_targets_touching_impossible_and_invalid(self):
        f=ResetExperimentFamily(('a','b'),('x',),(1,),(((0,1),(1,2)),))
        self.assertEqual(minimum_reset_policy(f)['status'],'impossible')
        coarse=ResetExperimentFamily(('a','b'),('x',),(1,),(((0,1),(1,2)),),('same','same'))
        self.assertEqual(minimum_reset_policy(coarse)['cost'],0)
        with self.assertRaises(ValueError): ResetExperimentFamily(('a',),('e',),(0,),(((0,0),),))
        with self.assertRaises(ValueError): minimum_reset_policy(self.fixture(),max_beliefs=1)

    def test_certificate_binds_schema_status_and_semantics(self):
        f=self.fixture();valid=minimum_reset_policy(f)
        for key,value in (('schema','other'),('status','unknown'),('uncertainty_semantics','persistent')):
            self.assertFalse(verify_reset_policy(f,dict(valid,**{key:value})))
        self.assertFalse(verify_reset_policy(f,dict(valid,status='impossible')))
        impossible=ResetExperimentFamily(('a','b'),('x',),(1,),(((0,1),(1,2)),))
        cert=minimum_reset_policy(impossible)
        self.assertTrue(verify_reset_policy(impossible,cert))
        self.assertFalse(verify_reset_policy(impossible,dict(cert,status='optimal')))
