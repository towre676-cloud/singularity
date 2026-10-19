from copy import deepcopy
from fractions import Fraction as Q
from itertools import combinations
import unittest
from singularity.phase_probes import *
from singularity.heights import local_coefficients

class PhaseProbesTests(unittest.TestCase):
    def test_exact_routes_census(self):
        count=0
        for n in range(1,4):
            edges=tuple(combinations(range(n),2))
            for mask in range(1<<len(edges)):
                g=Graph(n,tuple(e for i,e in enumerate(edges) if mask>>i&1));R=2
                M=energy_degree_bound(g,R)+1
                a=phase_table(g,R,M,'direct');b=phase_table(g,R,M,'residue')
                self.assertEqual(a['samples'],b['samples'])
                self.assertEqual(recover_energy_histograms(a),tuple(local_coefficients(g,R)));count+=1
        self.assertEqual(count,11)
        g=Graph(3,((0,1),))
        a=phase_table(g,2,6);b=phase_table(g,2,6,'residue')
        self.assertEqual(a['samples'],b['samples'])
        self.assertEqual(verify_phase_reconstruction(a),tuple(local_coefficients(g,2)))

    def test_aliasing_and_forgery(self):
        g=Graph(2,((0,1),));a=phase_table(g,2,5)
        self.assertEqual(recover_energy_histograms(a)[2],{0:1,4:2})
        b=phase_table(g,2,4)
        with self.assertRaises(ValueError):recover_energy_histograms(b)
        self.assertEqual(recover_energy_histograms(b,allow_aliasing=True)[2],{0:3})
        forged=deepcopy(a);forged['bound']=0
        with self.assertRaises(ValueError):recover_energy_histograms(forged)
        forged=deepcopy(a);forged['samples']=forged['samples'][:-1]
        with self.assertRaises(ValueError):recover_energy_histograms(forged)
        forged=deepcopy(a);forged['samples']=tuple([(0,a['samples'][0][1])]*5)
        with self.assertRaises(ValueError):recover_energy_histograms(forged)

    def test_rational_interpolation_alternative(self):
        samples=tuple((Q(1,i),1+2*Q(1,i)**4) for i in range(2,7))
        self.assertEqual(rational_histogram_interpolation(samples,4),{0:1,4:2})
        with self.assertRaises(ValueError):rational_histogram_interpolation(samples[:4]+samples[:1],4)

    def test_panel_and_conditional_support(self):
        graphs=(Graph(3),Graph(3,((0,1),)),Graph(3,((0,1),(1,2))),Graph(3,((0,1),(1,2),(0,2))))
        tables=tuple(phase_table(g,1,5) for g in graphs)
        result=phase_subset_identification(tuple(map(str,range(4))),tables,(1,2,3,4,5))
        self.assertTrue(result['feasible']);self.assertEqual(result['cost'],2);self.assertEqual(result['panel'],(1,))
        ring=CyclotomicRing(5);sample=ring.add(ring.one,ring.scale(ring.phase(4),2))
        self.assertEqual(sparse_histogram_recovery(5,(0,4),((1,sample),))['histogram'],{0:1,4:2})
        with self.assertRaises(ValueError):sparse_histogram_recovery(4,(0,4),((1,CyclotomicRing(4).scale(CyclotomicRing(4).one,3)),))

if __name__=='__main__':unittest.main()
