from fractions import Fraction as Q
import unittest
from singularity.symmetry_channels import *

class SymmetryChannelsTests(unittest.TestCase):
    def test_reflection_and_corrupted_commutation(self):
        P=((0,1),(1,0));A=((Q(1,2),Q(1,4)),(Q(1,4),Q(1,2)));Ps=reflection_channels(P)
        self.assertTrue(verify_channel_decomposition(Ps,(A,),(P,)))
        result=channel_observability((A,),((Q(1,2),Q(1,2)),),Ps)
        self.assertEqual(result['channel_ranks'],(1,0));self.assertEqual(result['blind_channels'],(1,))
        with self.assertRaises(ValueError):verify_channel_decomposition(Ps,(((Q(1,3),0),(0,Q(1,2))),))
        self.assertTrue(conjugate_model_blindness(A,A,P,(1,1),(1,1),((1,1),),((1,1),),(1,0),(0,1)))
        # Commutation alone does not allow splitting an arbitrary mixed sensor.
        bad=channel_observability((((1,0),(0,1)),),((1,0),),Ps)
        self.assertFalse(bad['observations_decompose'])

    def test_klein_repeated_rational_irreducibles(self):
        mats=[]
        for g in range(4):mats.append(tuple(tuple(Q(j==(i^g)) for j in range(4)) for i in range(4)))
        rep=FiniteRepresentation(tuple(range(4)),tuple(tuple(a^b for b in range(4)) for a in range(4)),tuple(mats))
        self.assertTrue(verify_representation(rep))
        Ps=[]
        for mask in range(4):
            Ps.append(tuple(tuple(sum(((-1)**((g&mask).bit_count())*mats[g][i][j] for g in range(4)),Q())/4 for j in range(4)) for i in range(4)))
        self.assertTrue(verify_channel_decomposition(Ps,mats,rep.matrices))
        result=channel_observability(mats,((1,0,0,0),),Ps)
        self.assertEqual(result['full_rank'],4);self.assertEqual(result['channel_ranks'],(1,1,1,1))
        # Two identical regular copies: four irreps, each multiplicity two,
        # but one copy-sum sensor observes one direction per repeated irrep.
        big=lambda A:tuple(tuple(A[i%4][j%4] if i//4==j//4 else Q() for j in range(8)) for i in range(8))
        result=channel_observability(tuple(map(big,mats)),((1,0,0,0,1,0,0,0),),tuple(map(big,Ps)))
        self.assertEqual(result['full_rank'],4);self.assertEqual(sum(result['channel_ranks']),4)

    def test_transformed_noise_keeps_correlations(self):
        T=((1,1),(0,1))
        box=transformed_noise_set(T,(1,1),'box')
        self.assertEqual(box['factor'],((1,1),(0,1)))
        self.assertEqual(box['coordinate_bounds'],(2,1))
        ellipsoid=transformed_noise_set(T,(1,1),'ellipsoid')
        self.assertEqual(ellipsoid['gram'],((2,1),(1,1)))
        with self.assertRaises(ValueError):transformed_noise_set(T,(1,-1))

    def test_costed_repair_and_insufficient_symmetry_break(self):
        opts=(RepairOption('break_but_fail',1,(0,1,1),(0,0,0)),
              RepairOption('complete',3,(0,1,2),(Q(1,10),)*3),
              RepairOption('a',2,(0,0,1),(0,0,0)),RepairOption('b',2,(0,1,0),(0,0,0)))
        out=minimum_channel_repair(('a','b','c'),(0,1,2),opts)
        self.assertEqual(out['cost'],3);self.assertIn(out['panel'],(('complete',),('break_but_fail','a')))

if __name__=='__main__':unittest.main()
