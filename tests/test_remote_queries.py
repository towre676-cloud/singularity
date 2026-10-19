import unittest
from fractions import Fraction as Q
from dataclasses import replace
from singularity.dynacomp_adapter import bundled_adapter
from singularity.remote_queries import *
from singularity.thermal_diagnostics import AffineCandidate,simulate_protocol,build_plate_candidates

class RemoteQueryTests(unittest.TestCase):
    def setUp(self):self.adapter=bundled_adapter()
    def compile(self,A,x,C,name='m'):return compile_response(SequenceQuery(name,name),A,x,C,self.adapter)
    def test_two_modes_closed_form_and_strict_inputs(self):
        a=self.compile(((Q(1,2),0),(0,Q(1,3))),(1,1),(1,-1))
        self.assertEqual(a.dimension,2)
        self.assertEqual(a.sequence_packet['hankel_determinant'],'-1/36')
        for n in range(33):self.assertEqual(query_index(a,n,10000,self.adapter).value,Q(1,2)**n-Q(1,3)**n)
        for bad in (True,1.0,'1/2'):
            with self.assertRaises(TypeError):self.compile(((bad,),),(1,),(1,))
        with self.assertRaises(ValueError):query_index(a,True,adapter=self.adapter)
        with self.assertRaises(ValueError):query_index(a,10**100,adapter=self.adapter)
        residue=query_index(a,10**100,adapter=self.adapter,modulus=101)
        self.assertEqual(residue.value,(pow(pow(2,-1,101),10**100,101)-pow(pow(3,-1,101),10**100,101))%101)
    def test_zero_invisible_and_polynomial_transient(self):
        a=self.compile(((Q(1,2),0,0),(0,Q(1,3),0),(0,0,Q(1,5))),(1,1,1),(1,-1,0))
        self.assertEqual(a.dimension,2)
        zero=self.compile(((Q(1,2),),),(1,),(0,));self.assertEqual(zero.dimension,0)
        self.assertEqual(query_index(zero,12,adapter=self.adapter).value,0)
        transient=self.compile(((0,1),(0,0)),(0,1),(1,0))
        self.assertEqual(transient.dimension,2)
        self.assertEqual(tuple(query_index(transient,n,adapter=self.adapter).value for n in range(4)),(0,1,0,0))
    def test_pair_cancel_progression_and_tampering(self):
        a=self.compile(((Q(1,2),0),(0,Q(1,3))),(1,1),(1,1),'a')
        b=self.compile(((Q(1,2),0),(0,Q(1,5))),(1,1),(1,1),'b')
        d=compile_pair_difference(a,b,self.adapter)
        self.assertEqual(d.dimension,2)
        for n in range(12):self.assertEqual(query_index(d,n,adapter=self.adapter).value,Q(1,3)**n-Q(1,5)**n)
        z=compile_pair_difference(a,a,self.adapter);self.assertEqual(z.dimension,0)
        p=query_progression(a,3,2,self.adapter)
        for n in range(6):self.assertEqual(query_index(p,n,adapter=self.adapter).value,Q(1,2)**(3*n+2)+Q(1,3)**(3*n+2))
        changed=dict(a.source);changed['C']=(Q(0),Q(1))
        with self.assertRaises(ValueError):replay_compiled(replace(a,source=changed),self.adapter)
    def test_physical_indexing_blocks_and_impulse(self):
        c=AffineCandidate('scalar',1,((0,0,Q(1,2)),),(Q(1),),((Q(1),),))
        step=compile_constant_input(c,0,adapter=self.adapter)
        for n in range(33):self.assertEqual(query_index(step,n,10000,self.adapter).value,simulate_protocol(c,(1,)*n,0))
        for block in ((1,0),(0,1,1)):
            for phase in range(len(block)):
                r=compile_repeated_block(c,block,0,phase,self.adapter)
                for k in range(33):self.assertEqual(query_index(r,k,10000,self.adapter).value,simulate_protocol(c,block*k+block[:phase],0))
        # Impulse convention has the explicit one-step delay.
        impulse=self.compile(((Q(1,2),0),(1,0)),(1,0),(0,1))
        self.assertEqual(tuple(query_index(impulse,n,adapter=self.adapter).value for n in range(4)),(0,1,Q(1,2),Q(1,4)))

    def test_remote_panel_binds_physical_indices_and_costs(self):
        a=self.compile(((Q(1,2),),),(1,),(1,),'a')
        b=self.compile(((Q(1,3),),),(1,),(1,),'b')
        ap=query_progression(a,3,2,self.adapter);bp=query_progression(b,3,2,self.adapter)
        pool=remote_panel_pool((ap,bp),(0,2),cost_per_index=2,reset_cost=1,adapter=self.adapter)
        self.assertEqual(pool.costs,(5,17))
        self.assertEqual(pool.readings,((Q(1,2)**2,Q(1,3)**2),(Q(1,2)**8,Q(1,3)**8)))
        with self.assertRaises(ValueError):remote_panel_pool((a,bp),(0,1),adapter=self.adapter)
        c=AffineCandidate('block',1,((0,0,Q(1,2)),),(1,),((1,),))
        block=compile_repeated_block(c,(1,0,1),0,phase=2,adapter=self.adapter)
        self.assertEqual((block.index_map['offset'],block.index_map['stride']),(2,3))


    def test_portable_receipts_and_index_tampering(self):
        import json,copy
        a=self.compile(((Q(1,2),),),(1,),(1,),'a')
        p=query_progression(a,3,2,self.adapter)
        receipt=response_receipt(p,query_index(p,5,adapter=self.adapter))
        self.assertTrue(replay_remote_receipt(json.loads(json.dumps(receipt)),self.adapter))
        altered=copy.deepcopy(receipt);altered['compiled']['index_map']['stride']=4
        with self.assertRaises(ValueError):replay_remote_receipt(altered,self.adapter)
        altered=copy.deepcopy(receipt);altered['value']=[2,4]
        with self.assertRaises(ValueError):replay_remote_receipt(altered,self.adapter)
        altered=copy.deepcopy(receipt);altered['extra']=1
        with self.assertRaises(ValueError):replay_remote_receipt(altered,self.adapter)
