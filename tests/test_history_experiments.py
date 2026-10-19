import unittest
from fractions import Fraction as F
from itertools import product
from singularity.history_experiments import (HistoryWorld,HistoryBelief,HistoryModel,
    InfeasibleHistoryAction,advance_belief,condition_belief,history_policy_search,
    verify_history_policy,latent_box_world,affine_advance,affine_condition,affine_reset)
from singularity.thermal_diagnostics import AffineCandidate


class HistoryTests(unittest.TestCase):
    def erase(self):
        worlds=(HistoryWorld('zero',0,0),HistoryWorld('one',1,1))
        transitions={(identifier,state,action):((0,) if action=='erase' else (state,))
                     for identifier in ('zero','one') for state in (0,1) for action in ('erase','wait')}
        measurements={'read':{(identifier,state):state for identifier in ('zero','one') for state in (0,1)}}
        return HistoryModel(worlds,('erase','wait'),transitions,measurements,(1,1),(1,))

    def test_destructive_original_identity_and_policy(self):
        model=self.erase();belief=HistoryBelief(model.initial_worlds)
        erased=advance_belief(model,belief,'erase')
        self.assertEqual(erased.targets,(0,1));self.assertEqual({w.state for w in erased.worlds},{0})
        self.assertEqual(condition_belief(model,erased,'read',0).targets,(0,1))
        original=condition_belief(model,belief,'read',1)
        self.assertEqual(original.targets,(1,))
        policy=history_policy_search(model,horizon=3)
        self.assertEqual(policy['cost'],1);self.assertTrue(verify_history_policy(model,policy))
        erased_model=HistoryModel(erased.worlds,model.actions,model.transitions,model.measurements,(1,1),(1,))
        self.assertEqual(history_policy_search(erased_model,horizon=4)['status'],'impossible-within-horizon')

    def test_exhaustive_updates_and_illegal(self):
        model=self.erase()
        for actions in product(model.actions,repeat=4):
            belief=HistoryBelief(model.initial_worlds)
            direct=[(w.original_id,w.target,w.state) for w in model.initial_worlds]
            for action in actions:
                belief=advance_belief(model,belief,action)
                direct=[(i,t,0 if action=='erase' else s) for i,t,s in direct]
            self.assertEqual({(w.original_id,w.target,w.state) for w in belief.worlds},set(direct))
        bad=HistoryModel(model.initial_worlds,model.actions,{},model.measurements,(1,1),(1,))
        with self.assertRaises(InfeasibleHistoryAction):advance_belief(bad,HistoryBelief(bad.initial_worlds),'erase')

    def test_shared_gain_two_slope_conditioning(self):
        worlds=[]
        for a in (F(1,2),F(3,4)):
            candidate=AffineCandidate(str(a),1,((0,0,a),),(F(3,2),),((1,),))
            world=latent_box_world(str(a),a,(0,),((0,),),('persistent:gain',))
            heated=affine_advance(world,candidate,1,heater_generators=((F(1,2),),))
            self.assertEqual((heated.center,heated.generators),((F(3,2),),((F(1,2),),)))
            first,certificate=affine_condition(heated,(1,),F(6,5))
            self.assertTrue(certificate['feasible'])
            cooled=affine_advance(first,candidate,0,heater_generators=((F(1,2),),))
            final,cert=affine_condition(cooled,(1,),F(3,5))
            worlds.append(final)
            self.assertEqual(final is not None,a==F(1,2))
            # Final-only 9/10 is compatible with both slopes at different gains.
            unconditioned=affine_advance(heated,candidate,0)
            self.assertIsNotNone(affine_condition(unconditioned,(1,),F(9,10))[0])
        self.assertEqual(sum(w is not None for w in worlds),1)

    def test_action_order_and_reset_local_latents(self):
        model=AffineCandidate('a',1,((0,0,F(1,2)),),(1,),((1,),))
        w=latent_box_world('original','target',(0,),((0,),),('persistent:g',))
        pulse_then_wait=affine_advance(affine_advance(w,model,1),model,0)
        wait_then_pulse=affine_advance(affine_advance(w,model,0),model,1)
        self.assertEqual((pulse_then_wait.center,wait_then_pulse.center),((F(1,2),),(F(1),)))
        reset=affine_reset(pulse_then_wait,(0,),((0,F(1,10)),),fresh_labels=('reset:1:initial',))
        self.assertEqual((reset.original_id,reset.target),('original','target'))
        self.assertEqual(reset.latent_labels,('persistent:g','reset:1:initial'))
        self.assertEqual(len(reset.inequalities),4)
        self.assertIsNotNone(affine_condition(reset,(1,),F(1,10))[0])
        self.assertIsNone(affine_condition(reset,(1,),F(1,5))[0])

    def test_certificate_binds_schema_status_and_semantics(self):
        model=self.erase();valid=history_policy_search(model,horizon=2)
        for key,value in (('schema','other'),('status','unknown'),('semantics','current-state-only')):
            self.assertFalse(verify_history_policy(model,dict(valid,**{key:value})))
        self.assertFalse(verify_history_policy(model,dict(valid,status='impossible-within-horizon')))
        impossible=history_policy_search(model,horizon=0)
        self.assertTrue(verify_history_policy(model,impossible))
        self.assertFalse(verify_history_policy(model,dict(impossible,status='optimal-within-horizon')))

    def test_duplicate_action_costs_rejected_before_policy_search(self):
        worlds=(HistoryWorld('a','A',0),HistoryWorld('b','B',0))
        transitions={('a',0,'go'):(1,),('b',0,'go'):(2,)}
        readings={'read':{('a',0):0,('b',0):0,('a',1):1,('b',2):2}}
        # A duplicate once let production choose cost one while replay used
        # the first occurrence's cost ten. Stable action IDs must be unique.
        with self.assertRaisesRegex(ValueError,'action identifiers must be distinct'):
            HistoryModel(worlds,('go','go'),transitions,readings,(10,1),(1,))
        valid=HistoryModel(worlds,('go',),transitions,readings,(1,),(1,))
        policy=history_policy_search(valid,horizon=2)
        self.assertEqual(policy['cost'],2)
        self.assertTrue(verify_history_policy(valid,policy))
