from fractions import Fraction as Q
from math import comb
from copy import deepcopy
import unittest
from singularity.prefix_certificates import *
from singularity.heights import local_coefficients

class PrefixCertificatesTests(unittest.TestCase):
    def test_edge_ideal_original_oracle_and_generation(self):
        for isolates in range(4):
            graph=Graph(2+isolates,((0,1),));hist=local_coefficients(graph,8)
            for q in (Q(0),Q(1,3),Q(1,2),Q(1)):
                cert=IdealClosurePrefixCertificate(q,isolates)
                direct=tuple(sum((count*q**energy for energy,count in h.items()),Q()) for h in hist)
                self.assertEqual(cert.coefficients(8),direct)
                self.assertEqual(parse_certificate(certificate_to_dict(cert)),cert)
                for eta in (Q(0),Q(2,3),q,Q(1)):
                    other=IdealClosurePrefixCertificate(eta,isolates)
                    for r,(a,b) in enumerate(zip(cert.coefficients(8),other.coefficients(8))):
                        self.assertEqual(a-b,2*(q-eta)*ideal_difference_quotient(r,q,eta,isolates))
                    self.assertEqual(compare_prefix(cert,other)['equal'],q==eta)
        self.assertEqual(IdealClosurePrefixCertificate(0).exceptional_stratum,'zero-edge-weight')
        self.assertEqual(IdealClosurePrefixCertificate(1).exceptional_stratum,'unit-weight-rational')

    def test_common_recurrence_parameter_census(self):
        parameters=(Q(-2),Q(-1,2),Q(0),Q(1,3),Q(1),Q(2))
        for a in parameters:
            ca=RecurrencePrefixCertificate(a)
            # Independent rising-factorial oracle rather than recurrence replay.
            for n,f in enumerate(ca.coefficients(12)):
                num=Q(1);den=1
                for j in range(n):num*=a+j;den*=j+1
                self.assertEqual(f,num/den)
            for b in parameters:
                cb=RecurrencePrefixCertificate(b);y=tuple(x-z for x,z in zip(ca.coefficients(12),cb.coefficients(12)))
                for n in range(11):self.assertEqual(sum(c*v for c,v in zip(comparison_recurrence(a,b,n),y[n:n+3])),0)
                self.assertEqual(compare_prefix(ca,cb)['equal'],a==b)

    def test_finite_state_periodic_and_strict_rejections(self):
        a=FiniteStatePrefixCertificate(((Q(1,2),),),(1,),(1,));b=FiniteStatePrefixCertificate(((Q(1,3),),),(1,),(1,))
        self.assertFalse(compare_prefix(a,b)['equal']);self.assertEqual(a.coefficients(8),tuple(Q(1,2)**r for r in range(9)))
        g=Graph(3,((0,1),(1,2)))
        p=PeriodicPrefixCertificate(PeriodicModel(g,2));self.assertTrue(compare_prefix(p,p)['equal'])
        self.assertEqual(parse_certificate(certificate_to_dict(p)),p)
        for delayed in ({'samples':[0]*100,'suggested_cutoff':99},{'ideals':['a-a_prime']*100}, {'parameter_count':1}):
            with self.assertRaises(ValueError):verify_certificate(delayed)
        forged=certificate_to_dict(a);forged['guessed_recurrence']=[1,-1]
        with self.assertRaises(ValueError):parse_certificate(forged)
        with self.assertRaises(ValueError):RecurrencePrefixCertificate(1,'guessed')
        with self.assertRaises(ValueError):parse_certificate({'schema':'singularity.prefix-certificate/1','kind':'edge-ideal','parameter':[1,0],'isolates':0})
        with self.assertRaises(ValueError):compare_prefix(IdealClosurePrefixCertificate(Q(1,2),0),IdealClosurePrefixCertificate(Q(1,2),1))

if __name__=='__main__':unittest.main()
