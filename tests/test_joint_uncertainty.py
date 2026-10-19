import random
import unittest
from fractions import Fraction as F
from itertools import combinations, product
from singularity.joint_uncertainty import (JointObservationFamily, GeometryBudgetExceeded,
    rational_feasibility, support_radius, project_panel, joint_pair_certificate,
    verify_joint_certificate, minimum_joint_panel, joint_consistent_candidates,
    affine_protocol_family)
from singularity.thermal_diagnostics import build_plate_candidates, simulate_protocol


def vertex_feasible(matrix, rhs, variables):
    """Independent active-vertex enumeration, not production elimination."""
    rows = list(zip(matrix, rhs))
    for i in range(variables):
        row = tuple(F(int(i == j)) for j in range(variables))
        rows.extend(((row, F(1)), (tuple(-x for x in row), F(1))))
    for selected in combinations(rows, variables):
        a = [list(row)+[b] for row, b in selected]
        for col in range(variables):
            pivot = next((j for j in range(col, variables) if a[j][col]), None)
            if pivot is None:
                break
            a[col], a[pivot] = a[pivot], a[col]
            scale = a[col][col]; a[col] = [x/scale for x in a[col]]
            for j in range(variables):
                if j != col:
                    c = a[j][col]; a[j] = [x-c*y for x, y in zip(a[j], a[col])]
        else:
            point = tuple(row[-1] for row in a)
            if all(abs(x) <= 1 for x in point) and all(sum(x*y for x, y in zip(row, point)) == b
                                                         for row, b in zip(matrix, rhs)):
                return True
    return False


class JointTests(unittest.TestCase):
    def fixture(self):
        g = ((1, F(1,10), 0), (1, 0, F(1,10)))
        return JointObservationFamily(('a','b'),('e0','e1'),((0,0),(1,-1)),(g,g),(1,1))

    def test_persistent_contrast_and_joint_optimum(self):
        family = self.fixture()
        self.assertEqual(support_radius(family.generators[0], (1,-1)), F(1,5))
        for i in range(2):
            self.assertEqual(joint_pair_certificate(project_panel(family,(i,)),0,1)['kind'], 'overlap')
        cert = joint_pair_certificate(family,0,1)
        self.assertTrue(verify_joint_certificate(family,cert))
        result = minimum_joint_panel(family)
        self.assertEqual((result['panel'], result['cost']), ((0,1),2))
        # Replace shared calibration by independent columns: fake correlation fails.
        independent = ((1,0,F(1,10),0),(0,1,0,F(1,10)))
        f = JointObservationFamily(('a','b'),('x','y'),((0,0),(1,-1)),(independent,independent),(1,1))
        self.assertEqual(joint_pair_certificate(f,0,1)['kind'],'overlap')
        self.assertFalse(verify_joint_certificate(f,cert))

    def test_tiny_vertex_oracle(self):
        rng = random.Random(121)
        for _ in range(24):
            ga = tuple((F(rng.randrange(-2,3)),) for i in range(2))
            gb = tuple((F(rng.randrange(-2,3)),) for i in range(2))
            rhs = tuple(F(rng.randrange(-4,5),2) for i in range(2))
            family = JointObservationFamily(('a','b'),('x','y'),((0,0),rhs),(ga,gb),(1,1))
            cert = joint_pair_certificate(family,0,1)
            self.assertTrue(verify_joint_certificate(family,cert))
            self.assertEqual(cert['kind']=='overlap',vertex_feasible(
                tuple((ga[i][0],-gb[i][0]) for i in range(2)),rhs,2))

    def test_every_subset_optimizer_independent_oracle(self):
        rng=random.Random(202)
        for trial in range(12):
            centers=tuple(tuple(F(rng.randrange(7),2) for _ in range(2)) for c in range(3))
            generators=tuple(tuple((F(rng.randrange(3),4),) for _ in range(2)) for c in range(3))
            family=JointObservationFamily(('a','b','c'),('x','y'),centers,generators,(1,2))
            feasible=[]
            for mask in range(4):
                panel=tuple(i for i in range(2) if mask>>i&1)
                good=True
                for a,b in combinations(range(3),2):
                    matrix=tuple((generators[a][i][0],-generators[b][i][0]) for i in panel)
                    rhs=tuple(centers[b][i]-centers[a][i] for i in panel)
                    if vertex_feasible(matrix,rhs,2):good=False
                if good:feasible.append((sum(family.costs[i] for i in panel),panel))
            result=minimum_joint_panel(family)
            self.assertEqual(result.get('cost'),min(feasible)[0] if feasible else None)

    def test_touching_rank_zero_and_malformed(self):
        f = JointObservationFamily(('a','b'),('x',),((0,),(2,)),(((1,),),((1,),)),(1,))
        cert = joint_pair_certificate(f,0,1)
        self.assertEqual(cert['kind'],'overlap'); self.assertTrue(verify_joint_certificate(f,cert))
        self.assertEqual(joint_consistent_candidates(f,(1,)),('a','b'))
        z = JointObservationFamily(('a','b'),('x',),((0,),(1,)),(((),),((),)),(1,))
        self.assertEqual(joint_pair_certificate(z,0,1)['kind'],'separating_contrast')
        bad = {'pair':(0,1),'kind':'separating_contrast','contrast':(0,),'gap':0}
        self.assertFalse(verify_joint_certificate(f,bad))
        with self.assertRaises(ValueError):
            JointObservationFamily(('a','b'),('x',),((0,),(1,)),(((1,),(2,)),((1,),)),(1,))
        with self.assertRaises(TypeError):
            support_radius(((1,),),(0.2,))
        with self.assertRaises(GeometryBudgetExceeded):
            minimum_joint_panel(self.fixture(), max_subsets=2)

    def test_farkas_direct_replay_and_refusal(self):
        rows = (((1,),0),((-1,),-1))
        result = rational_feasibility(rows,1)
        self.assertFalse(result['feasible'])
        lam = result['multipliers']
        self.assertTrue(all(x>=0 for x in lam))
        self.assertEqual(sum(x*a[0] for x,(a,b) in zip(lam,rows)),0)
        self.assertLess(sum(x*b for x,(a,b) in zip(lam,rows)),0)
        with self.assertRaises(GeometryBudgetExceeded):
            rational_feasibility(rows,1,max_rows=1)

    def test_outer_enclosure_does_not_claim_physical_impossibility(self):
        family=JointObservationFamily(('a','b'),('x',),((0,),(1,)),(((1,),),((1,),)),(1,),exact_set=False)
        result=minimum_joint_panel(family)
        self.assertEqual(result['status'],'not_certified')
        self.assertEqual(result['scope'],'declared-outer-enclosures')
        cert=joint_pair_certificate(family,0,1)
        self.assertTrue(verify_joint_certificate(family,cert))
        with self.assertRaises(ValueError):joint_pair_certificate(family,False,1)
        bad=dict(cert,pair=(False,1))
        self.assertFalse(verify_joint_certificate(family,bad))
        separated=JointObservationFamily(('a','b'),('x',),((0,),(3,)),(((1,),),((1,),)),(1,),exact_set=False)
        self.assertEqual(minimum_joint_panel(separated)['status'],'optimal_for_outer_enclosure')

    def test_thermal_affine_map_independent_substitution(self):
        candidates = build_plate_candidates(4)[:2]
        protocols = (((2,0),2),((2,2,0),3))
        family = affine_protocol_family(candidates, protocols, persistent_offset=F(1,5),
                                       sensor_noise=F(1,100), initial_radius=F(1,10))
        # Set one independently reset initial cell and calibration/noise by hand.
        for c, candidate in enumerate(candidates):
            for e,(word,sensor) in enumerate(protocols):
                initial = (F(1,10),)+(F(0),)*(candidate.dimension-1)
                direct = simulate_protocol(candidate,word,sensor,initial)+F(1,5)-F(1,100)
                row = family.generators[c][e]
                latent = [F(0)]*len(row); latent[0]=1; latent[1+e]=-1
                latent[1+len(protocols)+e*candidate.dimension]=1
                self.assertEqual(direct,family.centers[c][e]+sum(a*b for a,b in zip(row,latent)))
