from dataclasses import replace
from fractions import Fraction as Q
from itertools import product
from copy import deepcopy
import unittest
from singularity.refinement_planner import *
from singularity.fidelity_design import BoundedReading


def example():
    ids=('e1','e2','e3');pairs=((0,1),(0,2),(1,2));truth=((1,1,0),(0,1,1),(1,2,1))
    rows=[]
    for e,row in enumerate(truth):
        rows.append(tuple(MarginEnclosure(ids[e],p,v,v,binding=('fixed',))for p,v in zip(pairs,row)))
    rows[0]=rows[0][:2]+(MarginEnclosure('e1',(1,2),0,1,binding=('fixed',)),)
    return RefinementProblem(ids,(1,1,3),('a','b','c'),rows),truth


class RefinementTests(unittest.TestCase):
    def test_bounds_and_one_refinement(self):
        p,truth=example();b=decision_bounds(p)
        self.assertEqual((b['lower'],b['upper']),(1,2))
        result=refine_decision(p,lambda e,i,m:replace(m,lower=truth[e][i],upper=truth[e][i],fidelity=1))
        self.assertEqual(result['status'],'optimal');self.assertEqual(result['lower'],2)
        self.assertEqual(result['refinement_calls'],1);self.assertTrue(replay_refinement(p,result))
        self.assertEqual(result['certain_panel'],(0,1))

    def test_every_tiny_panel_obeys_bounds(self):
        p,truth=example();b=decision_bounds(p)
        costs=[]
        for flags in product((0,1),repeat=3):
            mask=0;price=0
            for e,on in enumerate(flags):
                if on:
                    price+=p.costs[e]
                    mask|=sum(1<<i for i,v in enumerate(truth[e])if v>0)
            if mask==7:costs.append(price)
        self.assertLessEqual(b['lower'],min(costs));self.assertGreaterEqual(b['upper'],min(costs))

    def test_equality_budget_and_stale_oracle(self):
        p,_=example()
        result=refine_decision(p,lambda e,i,m:m,max_refinements=2)
        self.assertEqual(result['status'],'optimality_unresolved')
        with self.assertRaises(ValueError):refine_decision(p,lambda e,i,m:replace(m,binding=('stale',)))
        with self.assertRaises(ValueError):MarginEnclosure('e',(0,1),1,0)
        left=BoundedReading(0,Q(1,10),Q(1,20),('s',),horizon=1)
        right=BoundedReading(Q(1,5),Q(1,10),Q(1,20),('s',),horizon=1)
        bound=margin_from_readings('e',(0,1),left,right)
        self.assertEqual((bound.lower,bound.upper),(-Q(1,10),Q(1,10)))
        exact=margin_from_readings('e',(0,1),replace(left,computational_radius=0),replace(right,computational_radius=0))
        self.assertEqual(exact.lower,0);self.assertEqual(exact.upper,0)
        with self.assertRaises(ValueError):margin_from_readings('e',(0,1),left,replace(right,domain_id='different-reset'))

    def test_replay_rejects_status_and_fidelity_forgery(self):
        p,truth=example()
        result=refine_decision(p,lambda e,i,m:replace(m,lower=truth[e][i],upper=truth[e][i],fidelity=1))
        for status in ('proved_unseparable','anything'):
            forged=dict(result,status=status)
            with self.assertRaises(ValueError):replay_refinement(p,forged)
        first=result['history'][0]
        # A valid problem may start at a nonzero fidelity; a forged transcript
        # cannot quietly relabel the next certificate as lower fidelity.
        rows=[list(row)for row in p.margins]
        e,i,old,new=first;rows[e][i]=replace(old,fidelity=2)
        p2=RefinementProblem(p.experiment_ids,p.costs,p.candidate_ids,rows)
        forged=dict(result,history=((e,i,rows[e][i],new),))
        with self.assertRaises(ValueError):replay_refinement(p2,forged)

if __name__=='__main__':unittest.main()
