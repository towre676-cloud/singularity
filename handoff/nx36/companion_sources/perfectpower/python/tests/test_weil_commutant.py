import copy,json,unittest
from pathlib import Path
from perfectpower.weil_commutant import certify_commutant,verify_commutant,certify_product
from perfectpower.finite_weil import commutant
from perfectpower.divisor_square import WorkLimit

class WeilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.packet=certify_commutant(16)
    def test_exact_prime_powers(self):
        for n,d in [(2,1),(3,2),(4,3),(8,5),(9,3),(16,7),(25,3),(27,4),(32,9),(49,3),(64,11)]:
            p=certify_commutant(n);self.assertEqual(p['dimension'],d);self.assertTrue(verify_commutant(p))
    def test_old_elimination_agrees(self):
        for n in range(2,10):self.assertEqual(certify_commutant(n)['dimension'],commutant(n)['dimension'])
    def test_coprime_products(self):
        for a,b in [(3,4),(3,16),(5,9),(7,8)]:
            p=certify_product(a,b);self.assertTrue(p['exact_finite_multiplicativity'])
            for key in ['left','right','product']:self.assertTrue(verify_commutant(p[key]))
    def test_roundtrip(self):self.assertTrue(verify_commutant(json.loads(json.dumps(self.packet))))
    def test_chirp_corruption(self):
        p=copy.deepcopy(self.packet);p['basis'][0][0][1]=1;self.assertFalse(verify_commutant(p))
    def test_fourier_corruption(self):
        p=copy.deepcopy(self.packet);p['basis'][0][0][0]+=1;self.assertFalse(verify_commutant(p))
    def test_duplicate_basis(self):
        p=copy.deepcopy(self.packet);p['basis'][1]=p['basis'][0];self.assertFalse(verify_commutant(p))
    def test_missing_basis(self):
        p=copy.deepcopy(self.packet);p['basis'].pop();self.assertFalse(verify_commutant(p))
    def test_bad_minor_row(self):
        p=copy.deepcopy(self.packet);p['minor_rows'][1]=p['minor_rows'][0];self.assertFalse(verify_commutant(p))
    def test_bad_minor_column(self):
        p=copy.deepcopy(self.packet);p['minor_columns'][1]=p['minor_columns'][0];self.assertFalse(verify_commutant(p))
    def test_missing_minor(self):
        p=copy.deepcopy(self.packet);p['minor_rows'].pop();self.assertFalse(verify_commutant(p))
    def test_false_dimension(self):
        p=copy.deepcopy(self.packet);p['dimension']+=1;self.assertFalse(verify_commutant(p))
    def test_composite_prime(self):
        p=copy.deepcopy(self.packet);p['prime']=49;self.assertFalse(verify_commutant(p))
    def test_nonprimitive_root(self):
        p=copy.deepcopy(self.packet);p['root']=pow(p['root'],2,p['prime']);self.assertFalse(verify_commutant(p))
    def test_claim_flags(self):
        for key in ['complete_over_cyclotomic_field','execution_verified']:
            p=copy.deepcopy(self.packet);p[key]=not p[key];self.assertFalse(verify_commutant(p))
    def test_field_types(self):
        for key,value in [('level',True),('prime',1.0),('root',True),('dimension',True)]:
            p=copy.deepcopy(self.packet);p[key]=value;self.assertFalse(verify_commutant(p))
    def test_malformed(self):
        for p in [None,{},[],{'schema':'pp-weil-commutant/1'}]:self.assertFalse(verify_commutant(p))
    def test_input_scope(self):
        for n in [True,1,129,-1]:
            with self.assertRaises(ValueError):certify_commutant(n)
        with self.assertRaises(ValueError):certify_product(4,8)
    def test_work_budget(self):
        with self.assertRaises(WorkLimit):certify_commutant(32,work_limit=1)
    def test_frontier_reconciliation(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
        from reconcile_mordell_frontier import reconcile
        p=reconcile()
        # The rank-witness frontier remains historical evidence; subsequent
        # retained backend completions close its lists without creating Lean
        # integral-list proofs. Protect both distinctions in this regression.
        historical=p['rank_witness_frontier']
        self.assertEqual((len(historical),sum(not r['x_coordinates'] for r in historical),
                          sum(bool(r['x_coordinates']) for r in historical)),(457,323,134))
        self.assertEqual(len(p['descent_closures']),28)
        self.assertEqual(len({r['k'] for r in historical}),457)
        self.assertEqual((p['remaining_count'],p['empty_computed_lists'],p['nonempty_computed_lists']),(0,0,0))
        self.assertEqual(p['external_computation_list_closure_count'],457)
        self.assertEqual({r['k'] for r in p['external_computation_list_closures']},{r['k'] for r in historical})
        self.assertTrue(all(r['lean_integral_list_proved'] is False for r in p['external_computation_list_closures']))

    def test_query_operations(self):
        from perfectpower.query_service import dispatch
        p=dispatch(None,{'op':'certified_weil_commutant','args':{'level':16}})
        self.assertEqual(p['dimension'],7)
        self.assertTrue(dispatch(None,{'op':'verify_weil_commutant','args':{'packet':p}})['valid'])
        self.assertEqual(dispatch(None,{'op':'weil_crt_commutant','args':{'a':3,'b':4}})['dimension'],6)
