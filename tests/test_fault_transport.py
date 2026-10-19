from fractions import Fraction as Q
from itertools import combinations
import unittest
from singularity.fault_transport import *
from singularity.thermal_diagnostics import AffineCandidate,build_plate_candidates,simulate_protocol

class FaultTransportTests(unittest.TestCase):
    def test_two_node_sign_and_protocol(self):
        a=AffineCandidate('two',2,((0,0,Q(1,2)),(1,1,Q(1,2)),(0,1,Q(1,4)),(1,0,Q(1,4))),(1,0),((0,1),))
        cache=NominalTransferCache(a,8)
        for d in (0,Q(1,8),Q(1,4)):
            f=BondFault(0,1,d);direct=apply_faults(a,(f,));imp=bond_transfer(cache,f)[0]
            self.assertEqual(imp,bond_transfer(cache,BondFault(1,0,d))[0])
            x=a.heater
            for t,y in enumerate(imp):
                self.assertEqual(y,direct.observe(x,0));x=direct.step(x,0)
            for word in ((1,1),(1,0,2),(-1,2,0,1)):
                self.assertEqual(protocol_from_impulse(imp,word),simulate_protocol(direct,word,0))
            initial=(Q(2),Q(-1));response=bond_transfer(cache,f,initial)[0]
            self.assertEqual(protocol_from_impulse(imp,(1,2),response[2]),simulate_protocol(direct,(1,2),0,initial))
        self.assertEqual(bond_transfer(cache,BondFault(0,1,Q(1,4)))[0],(0,)*9)
        with self.assertRaises(ValueError):bond_transfer(cache,BondFault(0,1,Q(1,3)))
        with self.assertRaises(TypeError):BondFault(0,1,0.1)

    def test_small_multi_faults_independent_flux(self):
        a=build_plate_candidates(4)[0];cache=NominalTransferCache(a,5)
        bonds=[(i,j) for i,j,v in a.entries if i<j and v>0][:6]
        for pair in combinations(bonds,2):
            for severity in (Q(1,16),Q(1,8)):
                fs=tuple(BondFault(u,v,severity) for u,v in pair);out=fault_set_transfer(cache,fs)
                direct=apply_faults(a,fs);x=a.heater
                entries={(i,j):v for i,j,v in direct.entries}
                for i in range(a.dimension):
                    self.assertEqual(sum(entries.get((i,j),0) for j in range(a.dimension)),Q(99,100))
                    for j in range(a.dimension):self.assertEqual(entries.get((i,j),0),entries.get((j,i),0))
                for t in range(6):
                    for s in range(4):self.assertEqual(out[s][t],direct.observe(x,s))
                    # Independent neighbor flux, preserving the source-derived stencil.
                    new=[Q(99,100)*z for z in x]
                    for i,j in [(i,j) for i,j,v in a.entries if i<j and v>0]:
                        k=Q(1,8)-sum(f.removed_conductance for f in fs if (f.u,f.v)==(i,j))
                        flow=k*(x[j]-x[i]);new[i]+=flow;new[j]-=flow
                    x=tuple(new)
        self.assertEqual(fault_set_transfer(cache,()),cache.nominal[1])

if __name__=='__main__':unittest.main()
