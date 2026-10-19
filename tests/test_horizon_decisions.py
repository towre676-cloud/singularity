"""NX10-B/C independent decision and physical chronology regression checks."""
import copy,unittest
from fractions import Fraction as Q
from singularity.horizon_design import *
from singularity.thermal_diagnostics import build_plate_candidates,simulate_protocol

def scalar(name,a,b):return step_system(LinearCandidate(name,((a,),),((b,),),((1,),)),(1,),0)

class HorizonDecisions(unittest.TestCase):
    def test_global_finite_maximum_and_late_impossibility(self):
        a,b=scalar('a',Q(1,2),Q(1,2)),scalar('b',Q(1,3),Q(2,3))
        e=RadiusEnvelope(sensor=Q(1,100))
        r=maximum_margin_horizon(a,b,e,e,max_prefix=32,epsilon=Q(1,100000))
        self.assertEqual(r.status,'finite_optimum_certified');self.assertEqual(r.record['argmax'],[1])
        # Independent exact calculus: d_k=2^-k-3^-k; d_(k+1)-d_k
        # = -(1/2)2^-k +(2/3)3^-k <0 for k>=1.
        self.assertTrue(all((Q(1,2)**k-Q(1,3)**k)<=Q(1,6) for k in range(1,200)))
        self.assertTrue(replay_horizon_result(r.record))
        late=minimum_step_horizon(a,b,e,e,IndexCost(1,1),max_prefix=32,min_index=6)
        self.assertEqual(late.status,'never_separating_after')
        self.assertTrue(all(Q(1,2)**k+Q(1,3)**k<Q(1,50) for k in range(6,80)))
        self.assertTrue(replay_horizon_result(late.record))
    def test_unattained_epsilon_and_strict_threshold(self):
        a,b=scalar('a',Q(1,2),1),scalar('b',Q(1,3),Q(2,3))
        e=RadiusEnvelope(sensor=Q(1,100))
        r=maximum_margin_horizon(a,b,e,e,max_prefix=64,epsilon=Q(1,1000))
        self.assertEqual(r.status,'supremum_bracket');self.assertEqual(r.record['attainment'],'not_certified')
        self.assertTrue(replay_horizon_result(r.record))
        # delta_k=1-2*2^-k+3^-k<1 at every finite k, increasing from k=1.
        for k in range(1,80):self.assertLess(1-2*Q(1,2)**k+Q(1,3)**k,1)
        a,b=scalar('a',0,1),scalar('b',0,0)
        e=RadiusEnvelope(sensor=Q(1,2))
        r=minimum_step_horizon(a,b,e,e,IndexCost(0,1),max_prefix=4)
        self.assertEqual(r.status,'never_separating_after')
        changed=copy.deepcopy(r.record);changed['steady_outputs'][0]=[2,1]
        with self.assertRaises(ValueError):replay_horizon_result(changed)
    def test_thermal_and_repeated_block_chronology(self):
        candidates=build_plate_candidates(4)
        for c in (candidates[0],candidates[2],candidates[4],candidates[5]):
            linear=LinearCandidate.from_affine(c)
            for block in ((1,0),(1,1,0)):
                for phase in range(len(block)):
                    system=block_system(linear,tuple((u,) for u in block),phase,2)
                    for k,state in enumerate(system.states(10)):
                        self.assertEqual(system.output(state),simulate_protocol(c,block*k+block[:phase],2))
        # Exact all-block equality under the symmetric sensor is retained as a
        # verified zero-order pair quotient, not inferred from a long prefix.
        a,b=(step_system(LinearCandidate.from_affine(c),(1,),0) for c in candidates[4:6])
        tail=certify_pair_quotient_tail(a,b)
        self.assertEqual(tail.order,0)
        r=minimum_step_horizon(a,b,RadiusEnvelope(sensor=Q(1,1000)),RadiusEnvelope(sensor=Q(1,1000)),IndexCost(1,1),max_prefix=16,tail_mode='pair_quotient')
        self.assertEqual(r.status,'never_separating_after');self.assertTrue(replay_horizon_result(r.record))
