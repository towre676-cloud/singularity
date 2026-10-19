import unittest
from fractions import Fraction as F
from itertools import product
from singularity.thermal_parameters import (Polynomial as P,ThermalParameterDomain,
    ParametricFaultFamily, parametric_fault_sample,panel_parameter_map,
    certify_family_separation,verify_family_certificate,severity_frontier)
from singularity.fault_population import plate_nominal,fault_candidate,plate_bonds
from singularity.thermal_diagnostics import simulate_protocol


class ParameterTests(unittest.TestCase):
    def test_severity_endpoints_and_flux(self):
        source=plate_nominal(4);bond=(4,5)
        nominal=parametric_fault_sample(4,bond,(F(1,8),F(1,100),1,0))
        blocked=parametric_fault_sample(4,bond,(F(1,8),F(1,100),1,1))
        self.assertEqual((nominal.entries,nominal.heater,nominal.sensors),
                         (source.entries,source.heater,source.sensors))
        oracle=fault_candidate(source,(1,),(bond,))
        self.assertEqual(blocked.entries,oracle.entries)
        state=tuple(F(i-3,20) for i in range(16)); alpha=F(2,5)
        model=parametric_fault_sample(4,bond,(F(1,8),F(1,100),F(3,2),alpha))
        expected=[F(99,100)*x+F(3,2)*source.heater[i] for i,x in enumerate(state)]
        for a,b in plate_bonds(4):
            k=F(1,8)*(1-alpha) if (a,b)==bond else F(1,8)
            flux=k*(state[b]-state[a]);expected[a]+=flux;expected[b]-=flux
        self.assertEqual(model.step(state,1),tuple(expected))

    def test_polynomial_map_and_manual_two_updates(self):
        protocols=(((2,0),2),((2,2,0),3))
        maps=panel_parameter_map(4,(4,5),protocols)
        for alpha,gain in product((0,F(1,3),1),(F(1,2),1)):
            parameters=(F(1,8),F(1,100),gain,alpha)
            model=parametric_fault_sample(4,(4,5),parameters)
            self.assertEqual(tuple(p.evaluate(parameters) for p in maps),
                             tuple(simulate_protocol(model,*protocol) for protocol in protocols))
        # Independent two-step expansion: x2=2*g*((1-loss)b-k L b+k alpha vv'b).
        k,loss,g,a=(P.variable(4,i) for i in range(4)); source=plate_nominal(4)
        b=source.heater; c=source.sensors[2]
        cb=sum(x*y for x,y in zip(c,b));clb=F(0)
        for u,v in plate_bonds(4): clb+=(c[u]-c[v])*(b[u]-b[v])
        cvvb=(c[4]-c[5])*(b[4]-b[5])
        manual=2*g*((1-loss)*cb-k*clb+k*a*cvvb)
        self.assertEqual(maps[0],manual)

    def scalar(self, band):
        g,a=P.variable(2,0),P.variable(2,1)
        return ParametricFaultFamily('scalar',((1,2),band),(g,(F(1,2)-a*F(1,4))*g))

    def test_full_domain_separation_overlap_touch_and_refusal(self):
        nominal=self.scalar((0,0));fault=self.scalar((F(1,2),1))
        cert=certify_family_separation(nominal,fault,noise=F(1,100),contrasts=((F(1,2),-1),))
        self.assertEqual(cert['status'],'separated');self.assertTrue(verify_family_certificate(nominal,fault,cert))
        final_nom=ParametricFaultFamily('n',nominal.domain,(nominal.observations[1],))
        final_fault=ParametricFaultFamily('f',fault.domain,(fault.observations[1],))
        overlap=certify_family_separation(final_nom,final_fault,max_cells=31,
            overlap_witnesses=(((1,0),(F(4,3),F(1,2))),))
        self.assertEqual(overlap['status'],'overlap');self.assertTrue(verify_family_certificate(final_nom,final_fault,overlap))
        left=ParametricFaultFamily('a',((0,0),),(P.constant(1,0),))
        right=ParametricFaultFamily('b',((0,0),),(P.constant(1,2),))
        touching=certify_family_separation(left,right,noise=1)
        self.assertEqual(touching['status'],'overlap');self.assertTrue(verify_family_certificate(left,right,touching))
        # Deliberately supply an uninformative contrast and a tiny budget.
        unresolved=certify_family_separation(nominal,fault,contrasts=((0,0),),max_cells=1)
        self.assertEqual(unresolved['status'],'unresolved')
        with self.assertRaises(ValueError): ThermalParameterDomain(((0,1),(F(1,10),F(1,10)),(1,1),(0,1)))
        with self.assertRaises(ValueError): ThermalParameterDomain(((F(1,8),F(1,8)),(F(1,100),F(1,100)),(1,1),(0,1)),severity_convention='reversed')

    def test_complete_subdivision_cover_and_tampering(self):
        x=P.variable(1,0)
        left=ParametricFaultFamily('curved',((0,1),),(x-x*x,))
        right=ParametricFaultFamily('constant',((0,0),),(P.constant(1,1),))
        cert=certify_family_separation(left,right,max_cells=7)
        self.assertEqual(cert['status'],'separated')
        self.assertEqual(cert['nodes'][0]['kind'],'split')
        self.assertTrue(verify_family_certificate(left,right,cert))
        bad=dict(cert);nodes=[dict(n) for n in cert['nodes']]
        nodes[1]['left_box']=((F(1,10),F(1,2)),)
        bad['nodes']=tuple(nodes)
        self.assertFalse(verify_family_certificate(left,right,bad))
