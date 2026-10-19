import unittest
from fractions import Fraction as F
from itertools import product, combinations
from math import comb
from singularity.fault_population import (FaultPopulation, fault_candidate, plate_bonds,
                                           plate_nominal, pilot_fault_candidates)


def flux_step(grid, state, amplitude, mask, bonds, k=F(1,8),loss=F(1,100),gain=1,alpha=1):
    n=grid*grid
    middle=(grid//2-1,grid//2)
    heat={r*grid+c for r in middle for c in middle}
    output=[(1-loss)*x+gain*amplitude*F(int(i in heat),len(heat)) for i,x in enumerate(state)]
    removed={tuple(sorted(b)) for b,t in zip(bonds,mask) if t}
    for r in range(grid):
        for c in range(grid):
            a=r*grid+c
            for rr,cc in ((r+1,c),(r,c+1)):
                if rr<grid and cc<grid:
                    b=rr*grid+cc
                    conductance=k*(1-alpha) if (a,b) in removed else k
                    transfer=conductance*(state[b]-state[a])
                    output[a]+=transfer;output[b]-=transfer
    return tuple(output)


class FaultTests(unittest.TestCase):
    def test_general_constraints_and_every_rank(self):
        rows=(((1,1,0,0),1),((0,-1,1,1),0))
        p=FaultPopulation(('a','b','c','d'),rows,max_faults=2)
        oracle=tuple(m for m in product((0,1),repeat=4) if sum(m)<=2 and all(
            sum(a*x for a,x in zip(row,m))<=b for row,b in rows))
        self.assertEqual(tuple(p.iterate_masks()),oracle)
        for i,m in enumerate(oracle):
            self.assertEqual((p.rank(m),p.unrank(i)),(i,m))
        for depth in range(5):
            self.assertEqual(sum(p.count(prefix) for prefix in product((0,1),repeat=depth)),len(oracle))
        conditioned=p.condition(lambda m:m[0]==0)
        self.assertEqual(conditioned.count()+p.condition(lambda m:m[0]==1).count(),p.count())
        self.assertEqual(FaultPopulation(('x',),(((1,),-1),)).count(),0)

    def test_exact79_and34981(self):
        p,c=pilot_fault_candidates()
        self.assertEqual(p.count(),79);self.assertEqual(len(c),79)
        self.assertEqual(len({x.identifier for x in c}),79)
        self.assertEqual(sum(p.count(prefix) for prefix in product((0,1),repeat=3)),79)
        full=FaultPopulation(plate_bonds(12),max_faults=2)
        self.assertEqual((len(full.bond_ids),full.count()),(264,34981))

    def test_all_eleven_tiny_physical_models(self):
        bonds=plate_bonds(2); p=FaultPopulation(bonds,max_faults=2); source=plate_nominal(2)
        self.assertEqual(p.count(),11)
        state=tuple(F(i-2,7) for i in range(4))
        for mask in p.iterate_masks():
            candidate=fault_candidate(source,mask,bonds)
            self.assertEqual(candidate.step(state,F(3,2)),flux_step(2,state,F(3,2),mask,bonds))
            matrix={(i,j):v for i,j,v in candidate.entries}
            self.assertEqual(candidate.heater,source.heater);self.assertEqual(candidate.sensors,source.sensors)
            for i in range(4):
                self.assertEqual(sum(v for (a,b),v in matrix.items() if a==i),F(99,100))
                for j in range(4):
                    self.assertEqual(matrix.get((i,j),0),matrix.get((j,i),0))
            self.assertTrue(all(v>=0 for v in matrix.values()))
        # First two bonds share endpoint zero; simultaneous removal is additive.
        self.assertEqual(fault_candidate(source,(1,1,0,0),bonds).step(state,0),
                         flux_step(2,state,0,(1,1,0,0),bonds))

    def test_validation_and_budget(self):
        with self.assertRaises(ValueError): FaultPopulation(('a','a'))
        with self.assertRaises(TypeError): FaultPopulation(('a',),(((0.5,),1),))
        with self.assertRaises(ValueError): FaultPopulation(('a',),max_states=1).count()
        with self.assertRaises(ValueError): FaultPopulation(('a',)).rank((2,))
        with self.assertRaises(ValueError): fault_candidate(plate_nominal(2),(1,1),((0,1),(1,0)))
