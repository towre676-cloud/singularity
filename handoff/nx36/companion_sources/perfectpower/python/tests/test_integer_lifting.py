import copy
import itertools
import random
import unittest
from fractions import Fraction
from perfectpower.integer_lifting import (smith_certificate,verify_smith,solve_integer,
    integral_task_section,integral_intertwiners,compare_column_lattices,ReductionLimit)
from perfectpower.integral_lattice import smith_invariants,lattice_membership
from perfectpower.exact_linear import apply,inverse,task_section,multiply,rank
from perfectpower.integer_projection import project_integer_query


class IntegerLiftingTests(unittest.TestCase):
    def test_nonunique_rational_coordinates_do_not_rule_out_integer_lift(self):
        rational=task_section([[1]],[[2,3]])
        self.assertFalse(rational['constructed_lift_integral'])
        result=solve_integer([[2,3]],[1])
        self.assertEqual(result['status'],'INTEGER_AFFINE_FIBRE')
        for t in range(-10,11):
            x=[a+t*b for a,b in zip(result['particular'],result['kernel_basis'][0])]
            self.assertEqual(apply([[2,3]],x),(1,))

    def test_non_saturated_denominator_cleared_rational_kernel(self):
        result=solve_integer([[2,1,1]],[0]);v=(-1,1,1)
        coordinates=apply(inverse(result['certificate']['right']),v)
        self.assertEqual(coordinates[0],0)
        self.assertTrue(all(x.denominator==1 for x in coordinates))
        # Clearing each rational basis vector separately yields (-1,2,0),
        # (-1,0,2), whose Z-span misses this integer solution.
        self.assertEqual(v[1]%2,1);self.assertEqual(result['parameter_count'],2)

    def test_random_smith_against_independent_all_minors(self):
        rng=random.Random(20261004)
        for _ in range(180):
            m,n=rng.randrange(1,5),rng.randrange(1,6)
            a=[[rng.randrange(-15,16) for j in range(n)] for i in range(m)]
            if rng.randrange(3)==0 and m>1:a[-1]=[2*x for x in a[0]]
            cert=smith_certificate(a)
            self.assertTrue(verify_smith(cert))
            self.assertEqual(cert['smith_factors'],smith_invariants(a)['smith_factors'])
            self.assertEqual(multiply(multiply(cert['left'],a),cert['right']),
                             tuple(tuple(Fraction(x) for x in row) for row in cert['diagonal_matrix']))

    def test_random_fibres_against_independent_lattice_indices(self):
        rng=random.Random(27154)
        for _ in range(180):
            m,n=rng.randrange(1,4),rng.randrange(1,5)
            a=[[rng.randrange(-6,7) for j in range(n)] for i in range(m)]
            b=[rng.randrange(-8,9) for i in range(m)]
            result=solve_integer(a,b)
            self.assertEqual(result['status']=='INTEGER_AFFINE_FIBRE',lattice_membership(a,b)['member'])
            if result['status']=='INTEGER_AFFINE_FIBRE':
                self.assertEqual(list(apply(a,result['particular'])),b)
                for w in result['kernel_basis']:self.assertEqual(apply(a,w),(0,)*m)
            else:
                h=result['annihilator'];pairs=[sum(h[i]*a[i][j] for i in range(m)) for j in range(n)]
                self.assertEqual(pairs,result['annihilator_times_matrix'])
                self.assertEqual(sum(x*y for x,y in zip(h,b)),result['pairing'])
                if result['status']=='DIVISIBILITY_OBSTRUCTION':
                    self.assertTrue(all(x%result['modulus']==0 for x in pairs))
                    self.assertNotEqual(result['pairing']%result['modulus'],0)
                else:self.assertFalse(any(pairs));self.assertNotEqual(result['pairing'],0)

    def test_every_small_solution_has_unique_integer_parameters(self):
        rng=random.Random(392)
        for _ in range(25):
            a=[[rng.randrange(-3,4) for j in range(3)] for i in range(2)]
            sample=[rng.randrange(-2,3) for j in range(3)];b=list(apply(a,sample))
            result=solve_integer(a,b);iv=inverse(result['certificate']['right']);r=result['certificate']['rank']
            for x in itertools.product(range(-2,3),repeat=3):
                if list(apply(a,x))!=b:continue
                z=apply(iv,[u-v for u,v in zip(x,result['particular'])])
                self.assertTrue(all(c.denominator==1 for c in z));self.assertFalse(any(z[:r]))
                self.assertEqual(tuple(result['particular'][i]+sum(z[r+j]*w[i] for j,w in enumerate(result['kernel_basis'])) for i in range(3)),x)

    def test_zero_negative_rank_deficient_and_prime_power_obstructions(self):
        for a,b,want in [([[0,0],[0,0]],[0,0],'INTEGER_AFFINE_FIBRE'),
                         ([[0,0],[0,0]],[1,0],'RATIONAL_IMAGE_OBSTRUCTION'),
                         ([[4,0],[0,8]],[0,4],'DIVISIBILITY_OBSTRUCTION'),
                         ([[-2,4]],[6],'INTEGER_AFFINE_FIBRE')]:
            self.assertEqual(solve_integer(a,b)['status'],want)
        r=solve_integer([[4,0],[0,8]],[0,4])
        self.assertEqual((r['modulus'],r['residue']),(8,4))

    def test_equal_abstract_smith_data_is_not_equal_embedded_lattice(self):
        a=[[2,0],[0,1]];b=[[1,0],[0,2]]
        self.assertEqual(smith_certificate(a)['smith_factors'],smith_certificate(b)['smith_factors'])
        r=compare_column_lattices(a,b);self.assertFalse(r['equal'])
        self.assertEqual(r['failed_inclusion'],'right_in_left')
        equivalent=[[2,2,0],[0,1,1]]
        self.assertTrue(compare_column_lattices(a,equivalent)['equal'])

    def test_tube_primitive_inclusion_and_nonunimodular_pairing(self):
        # e2+e3 is primitive. The doubled symplectic pairing is a distinct
        # statement about the map from the invariant lattice into its dual.
        c=[[0]*4 for i in range(5)]
        for j,indices in enumerate(((0,),(1,),(2,3),(4,))):
            for i in indices:c[i][j]=1
        inclusion=[row+[0]*4 for row in c]+[[0]*4+row for row in c]
        self.assertEqual(smith_certificate(inclusion)['smith_factors'],[1]*8)
        ambient=[[int(i<5 and j==i+5)-int(i>=5 and j==i-5) for j in range(10)] for i in range(10)]
        transpose=[list(col) for col in zip(*inclusion)]
        pairing=[[int(x) for x in row] for row in multiply(multiply(transpose,ambient),inclusion)]
        self.assertEqual(smith_certificate(pairing)['smith_factors'],[1]*6+[2,2])
        self.assertEqual(solve_integer(pairing,[0,0,1,0,0,0,0,0])['status'],'DIVISIBILITY_OBSTRUCTION')

    def test_large_unimodular_presentations(self):
        a=[[2,0,0],[0,6,0],[0,0,30]]
        a[0]=[x+10**120*y for x,y in zip(a[0],a[2])]
        for row in a:row[1]+=10**100*row[0]
        cert=smith_certificate(a)
        self.assertEqual(cert['smith_factors'],[2,6,30]);self.assertTrue(verify_smith(cert))

    def test_certificate_corruption_and_invalid_operations_rejected(self):
        cert=smith_certificate([[2,3],[4,7]])
        for key in ('left','right','diagonal_matrix','matrix'):
            bad=copy.deepcopy(cert);bad[key][0][0]+=1;self.assertFalse(verify_smith(bad))
        for op in [['row','add',0,0,1],['row','add',0,1,1.5],['column','scale',0,1,2],
                   ['row','negate',0,0,2],['row','swap',10,0,0]]:
            bad=copy.deepcopy(cert);bad['operations'].append(op);self.assertFalse(verify_smith(bad))
        bad=copy.deepcopy(cert);bad['rank']=True;self.assertFalse(verify_smith(bad))
        self.assertFalse(verify_smith({}));self.assertFalse(verify_smith(cert,operation_limit=1))

    def test_fail_closed_budgets_and_exact_input(self):
        for a in ([[True]],[[1.0]],[[Fraction(1)]],[],[[1],[2,3]]):
            with self.assertRaises(ValueError):smith_certificate(a)
        with self.assertRaises(ReductionLimit):smith_certificate([[2,3]],operation_limit=6)
        with self.assertRaises(ReductionLimit):smith_certificate([[2**100]],entry_bit_limit=20)
        with self.assertRaises(ValueError):smith_certificate([[1]],operation_limit=True)
        with self.assertRaises(ValueError):solve_integer([[1]],[True])

    def test_integral_task_sections_and_complete_parameter_count(self):
        r=integral_task_section([[1,5]],[[2,3]])
        self.assertEqual(r['status'],'INTEGRAL_TASK_SECTION');self.assertEqual(r['parameter_count'],2)
        self.assertEqual(multiply([[2,3]],r['lift']),((Fraction(1),Fraction(5)),))
        self.assertEqual(integral_task_section([[2,1]],[[2,4]])['target_column'],1)
        rng=random.Random(439)
        for _ in range(30):
            g=[[rng.randrange(-4,5) for j in range(4)] for i in range(3)]
            t=[[rng.randrange(-3,4) for j in range(2)] for i in range(4)]
            f=[[int(x) for x in row] for row in multiply(g,t)]
            r=integral_task_section(f,g);self.assertEqual(multiply(g,r['lift']),multiply(g,t))

    def test_integral_intertwiner_module_and_all_contexts(self):
        a=[[0,2],[0,0]];b=[[0,3],[0,0]]
        result=integral_intertwiners([a],[b]);self.assertEqual(result['dimension'],2)
        for t in result['basis']:self.assertEqual(multiply(t,a),multiply(b,t))
        self.assertEqual(integral_intertwiners([[[1]]],[[[2]]])['dimension'],0)
        self.assertEqual(integral_intertwiners([[[1]],[[2]]],[[[1]],[[3]]])['dimension'],0)
        with self.assertRaises(ReductionLimit):integral_intertwiners([a],[b],variable_limit=3)


class IntegerProjectionTests(unittest.TestCase):
    @staticmethod
    def script(body,names=('x','y')):
        return '(set-logic QF_NIA)\n'+''.join(f'(declare-const {n} Int)\n' for n in names)+body+'\n(check-sat)\n'

    def test_projection_keeps_nonlinear_residual_and_lifts_models(self):
        source=self.script('(assert (and (= (+ (* 2 x) (* 3 y)) 1) (= (* x x) 1)))')
        r=project_integer_query(source);self.assertFalse(r.linear);self.assertEqual(len(r.parameters),1)
        self.assertEqual(r.lift({r.parameters[0]:0}),{'x':-1,'y':1})
        with self.assertRaises(ValueError):r.lift({r.parameters[0]:0.0})

    def test_unsat_reduction_and_parameter_name_collision(self):
        r=project_integer_query(self.script('(assert (= (+ (* 4 x) (* 8 y)) 2))'))
        self.assertIn('(assert false)',r.smt);self.assertTrue(r.linear)
        with self.assertRaises(ValueError):r.lift({})
        r=project_integer_query(self.script('(assert (= (+ (* 2 x) (* 3 _pp_integer_0)) 1))',('x','_pp_integer_0')))
        self.assertEqual(r.parameters,('_pp_integer_0_',))

    def test_invalid_scope_sort_and_commands_rejected(self):
        bodies=['(assert (= (+ x missing) 1))','(assert (= (+ x true) 1))',
                '(assert (forall ((z Int)) (= z x)))','(assert (or (= x 1) (= y 2)))',
                '(assert (= (* x y) 1))']
        for body in bodies:
            with self.assertRaises(ValueError):project_integer_query(self.script(body))
        with self.assertRaises(ValueError):project_integer_query(self.script('(assert (= x 1))')+'(check-sat)')

    def test_z3_exhaustive_source_fibres_and_residual_semantics(self):
        try:import z3
        except ImportError:self.skipTest('optional z3 unavailable')
        cases=[('(assert (= (+ (* 2 x) (* 3 y)) 1))(assert (= (* x x) 1))','sat'),
               ('(assert (= (+ (* 4 x) (* 8 y)) 2))(assert (> (* x x) 0))','unsat'),
               ('(assert (= (+ (* 2 x) (* 3 y)) 1))(assert (= x 2))(assert (= y 0))','unsat'),
               ('(assert (= (+ x y) 4))(assert (= (mod x 3) 1))(assert (> y 0))','sat')]
        for body,expected in cases:
            source=self.script(body);r=project_integer_query(source)
            a,b=z3.Solver(),z3.Solver();a.add(z3.parse_smt2_string(source));b.add(z3.parse_smt2_string(r.smt))
            self.assertEqual(str(a.check()),expected);self.assertEqual(str(b.check()),expected)
            if expected=='sat':
                model=b.model();lift=r.lift({p:model.eval(z3.Int(p),model_completion=True).as_long() for p in r.parameters})
                a.push();a.add(*[z3.Int(k)==v for k,v in lift.items()]);self.assertEqual(a.check(),z3.sat);a.pop()
        # For every small original point, the projected fibre parameters are
        # integral and evaluating the reduced formula gives identical truth.
        source=self.script('(assert (= (+ (* 2 x) y) 3))(assert (or (= (* x x) y) (> x y)))')
        r=project_integer_query(source);iv=inverse(r.solution['certificate']['right']);rank=r.solution['certificate']['rank']
        original=z3.And(*z3.parse_smt2_string(source));reduced=z3.And(*z3.parse_smt2_string(r.smt))
        for x,y in itertools.product(range(-5,6),repeat=2):
            if 2*x+y!=3:continue
            diff=[x-r.solution['particular'][0],y-r.solution['particular'][1]];coords=apply(iv,diff)
            values={p:int(coords[rank+j]) for j,p in enumerate(r.parameters)}
            old=z3.simplify(z3.substitute(original,(z3.Int('x'),z3.IntVal(x)),(z3.Int('y'),z3.IntVal(y))))
            new=z3.simplify(z3.substitute(reduced,*[(z3.Int(p),z3.IntVal(v)) for p,v in values.items()]))
            self.assertEqual(str(old),str(new))

if __name__=='__main__':unittest.main()
