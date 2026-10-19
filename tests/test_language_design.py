import itertools,unittest
from fractions import Fraction as Q
from dataclasses import replace
from singularity.language_design import *
from singularity.thermal_diagnostics import build_plate_candidates,simulate_protocol

def tiny(n=1):
    caps=tuple(Capability(s,c) for s,c in (('s1',2),('s2',2),('s3',5)))
    exp=(RequiredExperiment('e1',('s1',),(0,1,0),(Q(1,10),)*3,1),RequiredExperiment('e2',('s2',),(0,0,1),(Q(1,10),)*3,1),RequiredExperiment('e3',('s3',),(0,1,2),(Q(1,10),)*3,1))
    return LanguageDesignProblem(caps,exp,('v1','v2','v3'),('v1','v2','v3'),n)

class LanguageTests(unittest.TestCase):
    def test_tiny_ties_and_independent_oracle(self):
        for n,expected in ((1,6),(2,7),(10,15),(100,105)):
            p=tiny(n);r=minimum_installation_panel(p);self.assertEqual(r['total_cost'],expected);self.assertTrue(verify_installation_result(p,r))
            oracle=[]
            for bits in itertools.product((0,1),repeat=3):
                installed={c.identifier for c,b in zip(p.capabilities,bits) if b}
                for chosen in itertools.product((0,1),repeat=3):
                    panel=[e for e,b in zip(p.experiments,chosen) if b]
                    if any(not set(e.requires)<=installed for e in panel):continue
                    if all(any(abs(e.readings[i]-e.readings[j])>e.radii[i]+e.radii[j] for e in panel) for i in range(3) for j in range(i+1,3)):
                        oracle.append(sum(c.install_cost for c,b in zip(p.capabilities,bits) if b)+n*sum(e.run_cost for e in panel))
            self.assertEqual(r['total_cost'],min(oracle))
            if n==1:self.assertEqual(len(r['optima']),2)
    def test_targets_validation_and_resource(self):
        p=tiny();self.assertEqual(minimum_installation_panel(replace(p,target_labels=('same',)*3))['total_cost'],0)
        with self.assertRaises(ValueError):replace(p,capabilities=p.capabilities+(p.capabilities[0],))
        with self.assertRaises(ValueError):replace(p,experiments=(replace(p.experiments[0],requires=('unknown',)),))
        self.assertNotEqual(minimum_installation_panel(p,max_panel_nodes=1)['status'],'optimal')
    def test_thermal_catalogue_independent_flux_and_blindness(self):
        candidates=build_plate_candidates(4);p=thermal_capability_catalogue(candidates,horizons=(1,2,3))
        # Reflection swaps blocked candidates; symmetric heater/sensors stay invariant.
        for horizon in range(1,7):
            for sensor in (0,1):self.assertEqual(simulate_protocol(candidates[4],(1,)*horizon,sensor),simulate_protocol(candidates[5],(1,)*horizon,sensor))
        self.assertTrue(any(e.readings[4]!=e.readings[5] for e in p.experiments if 'sensor:2' in e.requires))
        r=minimum_installation_panel(p,max_panel_nodes=2000000);self.assertEqual(r['status'],'optimal');self.assertTrue(verify_installation_result(p,r,max_panel_nodes=2000000))


    def test_tie_budget_and_constant_sensor_guard(self):
        p=tiny()
        for bad in (0,True,1.0):
            with self.assertRaises(ValueError):minimum_installation_panel(p,max_ties=bad)
        constant=RequiredExperiment('constant',(),(7,7,7),(0,0,0),1)
        self.assertEqual(minimum_installation_panel(replace(p,experiments=p.experiments+(constant,)))['total_cost'],6)
