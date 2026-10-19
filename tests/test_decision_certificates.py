from fractions import Fraction as Q
from copy import deepcopy
from itertools import product
import json
import unittest
from singularity.decision_certificates import *


def problem():
    return make_problem(('a','b','c'),('a','b','c'),('e1','e2','e3'),(1,1,3),
        (((0,0),(1,1),(1,1)),((0,0),(0,0),(1,1)),((0,0),(1,1),(2,2))),
        model_revision='source-v1',source_bindings=('actual-bound-premise',))


class DecisionCertificateTests(unittest.TestCase):
    def test_optimality_against_direct_set_oracle(self):
        p=problem();c=make_decision_certificate(p,(0,1))
        self.assertTrue(verify_decision_certificate(json.loads(json.dumps(c)),p))
        # Plain interval intersection and every subset, independent of masks/DP.
        feasible=[]
        raw=(((0,0),(1,1),(1,1)),((0,0),(0,0),(1,1)),((0,0),(1,1),(2,2)))
        for flags in product((False,True),repeat=3):
            panel=[e for e,v in enumerate(flags)if v]
            good=all(any(max(raw[e][a][0],raw[e][b][0])>min(raw[e][a][1],raw[e][b][1])for e in panel)
                     for a in range(3)for b in range(a+1,3))
            if good:feasible.append(sum((1,1,3)[e]for e in panel))
        self.assertEqual(min(feasible),2)

    def test_tamper_cost_endpoint_target_domain_and_proof(self):
        p=problem();c=make_decision_certificate(p,(0,1))
        mutations=(lambda x:x['problem']['costs'][0].__setitem__(0,9),
            lambda x:x['problem']['intervals'][0][0][0].__setitem__(0,1),
            lambda x:x['problem']['target_labels'].__setitem__(0,'b'),
            lambda x:x['problem']['semantics'].__setitem__('reset','warm-start'),
            lambda x:x['problem']['semantics'].__setitem__('model_revision','stale'),
            lambda x:x['pair_witnesses'][0]['gap'].__setitem__(0,0),
            lambda x:x['optimality']['tables'][-1][0][1].__setitem__(0,1),
            lambda x:x['optimality'].__setitem__('positive_common_denominator',0))
        for mutation in mutations:
            bad=deepcopy(c);mutation(bad);self.assertFalse(verify_decision_certificate(bad,p))

    def test_closed_endpoint_contact_and_contrast(self):
        p=make_problem(('a','b'),('a','b'),('e',),(2,),
            (((0,Q(1,10)),(Q(1,10),Q(1,5))),),model_revision='m',source_bindings=('s',))
        with self.assertRaises(ValueError):make_decision_certificate(p,(0,))
        self.assertEqual(contrast_gap((0,0),((Q(1,10),0),),(1,1),((0,Q(1,10)),),(1,1)),Q(9,5))
        self.assertEqual(contrast_gap((0,),((Q(1,2),),),(1,),((Q(1,2),),),(1,)),0)
        with self.assertRaises(ValueError):contrast_gap((0,0),(),(1,),(),(1,))

if __name__=='__main__':unittest.main()
