import unittest
from dataclasses import replace
from fractions import Fraction as Q
from singularity.fidelity_design import *
from singularity.thermal_diagnostics import build_plate_candidates,simulate_protocol

def option(candidate,label,center,error,cost=1,setup=0,key=None):
    source=f'source-{candidate}';domain='fixed';key=key or label+'-'+candidate
    reading=compose_reading_contract(center,Q(1,20),reduction_error=error,source_ids=(source,),horizon=1,domain_id=domain)
    receipt={'source_id':source,'candidate_id':candidate,'sensor_ids':('s',),'domain_id':domain,'horizon':1,'units':'model_output','arithmetic_protocol':'exact_rational','rank':1,'setup_binding':key}
    return EvaluatorOption(label+'-'+candidate,candidate,('s',),domain,'exact_rational',1,key,setup,cost,receipt,reading)

class FidelityTests(unittest.TestCase):
    def test_tiny_menu_and_independent_panel_oracle(self):
        a=FidelityExperiment('close',1,((option('a','cheap',0,Q(1,4)),option('a','accurate',0,Q(1,20),3)),(option('b','cheap',Q(1,2),Q(1,4)),option('b','accurate',Q(1,2),Q(1,20),3))))
        b=FidelityExperiment('wide',2,((option('a','cheap2',0,Q(1,4)),),(option('b','cheap2',1,Q(1,4)),)))
        result=minimum_fidelity_panel((a,b),('a','b'))
        self.assertEqual(result.status,'optimal');self.assertEqual(result.total_cost,4)
        self.assertEqual(result.selected[0][0],'wide')
        # Independent plain loops enumerate every selected experiment/menu assignment.
        feasible=[]
        from itertools import product
        for chosen in product((None,)+tuple(product(*a.options)),(None,)+tuple(product(*b.options))):
            keys={};run=Q(0);covered=False
            for e,assignment in zip((a,b),chosen):
                if assignment is None:continue
                run+=e.physical_cost+sum(o.run_cost for o in assignment)
                for o in assignment:keys[o.setup_key]=o.setup_cost
                covered|=abs(assignment[0].reading.center-assignment[1].reading.center)>sum(o.reading.radius for o in assignment)
            if covered:feasible.append(run+sum(keys.values()))
        self.assertEqual(result.total_cost,min(feasible));self.assertTrue(replay_fidelity_result((a,b),('a','b'),result))
    def test_strict_threshold_units_setup_and_resource(self):
        x=option('a','x',0,Q(1,5));y=option('b','y',Q(1,2),Q(1,5))
        e=FidelityExperiment('equal',1,((x,),(y,)))
        self.assertEqual(minimum_fidelity_panel((e,),('a','b')).status,'unseparable')
        self.assertEqual(minimum_fidelity_panel((e,),('a','b'),target_labels=('same','same')).total_cost,0)
        with self.assertRaises(ValueError):replace(x,domain_id='different')
        with self.assertRaises(ValueError):replace(x,arithmetic_protocol='numpy_blas')
        p=dict(x.bound_receipt);p['horizon']=2
        with self.assertRaises(ValueError):replace(x,bound_receipt=p)
        self.assertEqual(minimum_fidelity_panel((e,),('a','b'),max_nodes=1).status,'resource_limit')
    def test_actual_ranks_exact_and_binary64_source_replay(self):
        candidate=build_plate_candidates(4)[0]
        for rank in (1,2):
            for protocol in ('exact_rational','binary64_exact_dot'):
                o=certify_dynacomp_option(candidate,0,(1,0,1),rank,arithmetic_protocol=protocol)
                true=simulate_protocol(candidate,(1,0,1),0)
                self.assertLessEqual(abs(o.reading.center-true),o.reading.computational_radius)
                self.assertEqual(o.rank,rank)
                self.assertTrue(replay_dynacomp_option(o))
                p=dict(o.bound_receipt);p['source_id']='tampered'
                with self.assertRaises(ValueError):replace(o,bound_receipt=p)


    def test_physical_sensor_binding_and_full_state_reference(self):
        x=option('a','x',0,0);y=option('b','y',1,0)
        p=dict(y.bound_receipt);p['sensor_ids']=('other',)
        other=replace(y,sensor_ids=('other',),bound_receipt=p)
        with self.assertRaises(ValueError):minimum_fidelity_panel((FidelityExperiment('bad',1,((x,),(other,))),),('a','b'))
        c=build_plate_candidates(4)[0]
        full=certify_dynacomp_option(c,2,(1,1),16,force_full=True)
        self.assertEqual(full.rank,16);self.assertEqual(full.reading.computational_radius,0)
        self.assertTrue(replay_dynacomp_option(full))


    def test_optimizer_replays_actual_certificate_not_just_labels(self):
        candidates=build_plate_candidates(4)
        a=certify_dynacomp_option(candidates[0],2,(1,1,1),1)
        b=certify_dynacomp_option(candidates[2],2,(1,1,1),1)
        self.assertGreater(a.reading.computational_radius,0)
        forged=replace(a,reading=replace(a.reading,computational_radius=0))
        with self.assertRaises(ValueError):minimum_fidelity_panel((FidelityExperiment('forged',1,((forged,),(b,))),),(a.candidate_id,b.candidate_id))
