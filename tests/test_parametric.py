"""Parameter-aware observability (OE09).

Oracles are independent of ``parametric``: polynomial arithmetic comes from
``polynomials`` (sparse dictionaries), gcds from ``parameters``, determinants
from the Leibniz formula, experiment rows from explicit word enumeration, and
specialized ranks from ``observability.observable_closure`` or a local
Gaussian elimination.
"""
import random
import unittest
from fractions import Fraction as F
from itertools import combinations, permutations, product

from singularity import parametric as P
from singularity.graph_experiments import BoundaryExperimentSystem
from singularity.observability import observable_closure
from singularity.parameters import gcd as pgcd
from singularity.polynomials import add, evaluate, mul, normalize, scale
from singularity.parametric import (
    PolynomialOperatorSystem, determinantal_divisor, determinantal_divisor_by_minors,
    factor_over_q, generic_closure, generic_rank, observation_module, parametric_observability,
    rank_at_algebraic, rank_at_rational, real_roots, smith_invariant_factors,
    symbolic_boundary_system, to_polynomial,
)


# ---------------------------------------------------------------- oracles
def leibniz_det(m):
    k = len(m)
    total = {}
    for perm in permutations(range(k)):
        sign = 1
        for i in range(k):
            for j in range(i + 1, k):
                if perm[i] > perm[j]:
                    sign = -sign
        term = {0: F(sign)}
        for i in range(k):
            term = mul(term, m[i][perm[i]])
            if not term:
                break
        total = add(total, term)
    return total


def oracle_divisor(matrix, r):
    """Monic gcd of all r x r minors (Leibniz determinants, parameters.gcd)."""
    rows = [[to_polynomial(x) for x in row] for row in matrix]
    g = {}
    for I in combinations(range(len(rows)), r):
        for J in combinations(range(len(rows[0])), r):
            d = leibniz_det([[rows[i][j] for j in J] for i in I])
            if d:
                g = pgcd(g, d) if g else d
    if not g:
        return {}
    lead = g[max(g)]
    return {e: c / lead for e, c in g.items()}


def oracle_generic_rank(matrix):
    rows = [[to_polynomial(x) for x in row] for row in matrix]
    for r in range(min(len(rows), len(rows[0]) if rows else 0), 0, -1):
        if oracle_divisor(rows, r):
            return r
    return 0


def oracle_rows(ops, obs, max_length):
    """All experiment rows L_j M_w with |w| <= max_length, by enumeration.
    The word (i1,...,im) applies i1 first: row = L M_im ... M_i1."""
    n = len(obs[0])
    out = []
    for length in range(max_length + 1):
        for word in product(range(len(ops)), repeat=length):
            for L in obs:
                row = [to_polynomial(x) for x in L]
                for i in reversed(word):
                    M = ops[i]
                    row = [normalize(sum_polys(mul(row[k], to_polynomial(M[k][j])) for k in range(n)))
                           for j in range(n)]
                out.append(row)
    return out


def sum_polys(items):
    total = {}
    for x in items:
        total = add(total, x)
    return total


def rational_rank(rows):
    rows = [list(r) for r in rows]
    rank = 0
    for c in range(len(rows[0]) if rows else 0):
        k = next((i for i in range(rank, len(rows)) if rows[i][c]), None)
        if k is None:
            continue
        rows[rank], rows[k] = rows[k], rows[rank]
        for i in range(len(rows)):
            if i != rank and rows[i][c]:
                f = rows[i][c] / rows[rank][c]
                rows[i] = [a - f * b for a, b in zip(rows[i], rows[rank])]
        rank += 1
    return rank


def random_poly(rng, degree=2, zero=0.3, spread=2):
    if rng.random() < zero:
        return {}
    return {e: rng.randint(-spread, spread) for e in range(degree + 1)}


def random_matrix(rng, rows, columns, degree=2):
    return [[random_poly(rng, degree) for _ in range(columns)] for _ in range(rows)]


def random_system(rng, n=3, g=2, o=1, degree=1):
    ops = []
    for _ in range(g):
        ops.append([[random_poly(rng, degree, zero=0.5) for _ in range(n)] for _ in range(n)])
    obs = [[random_poly(rng, degree, zero=0.4) for _ in range(n)] for _ in range(o)]
    return ops, obs


# ---------------------------------------------------------------- tests
class DeterminantalDivisorTests(unittest.TestCase):
    def test_normal_form_matches_minor_gcd_on_random_matrices(self):
        rng = random.Random(9091)
        checked = 0
        for trial in range(36):
            rows, cols = rng.choice([(2, 3), (3, 3), (3, 4), (4, 3), (3, 2), (4, 4)])
            m = random_matrix(rng, rows, cols)
            if trial % 3 == 0:  # force a common factor, or a dependent row
                m[0] = [mul(x, {0: -1, 1: 2}) for x in m[0]]
            if trial % 4 == 1 and rows >= 2:
                m[-1] = [add(scale(a, 2), mul(b, {1: 1})) for a, b in zip(m[0], m[1])]
            r = oracle_generic_rank(m)
            self.assertEqual(generic_rank(m), r)
            for k in range(0, r + 1):
                expected = oracle_divisor(m, k) if k else {0: F(1)}
                self.assertEqual(determinantal_divisor(m, k), expected)
                self.assertEqual(determinantal_divisor_by_minors(m, k), expected)
            self.assertEqual(determinantal_divisor(m), oracle_divisor(m, r) if r else {0: F(1)})
            if r:  # Smith invariant factors: product of the first r is D_r, and they divide in turn
                inv = smith_invariant_factors([[P._poly(x) for x in row] for row in m])
                self.assertEqual(len(inv), r)
                prod = {0: F(1)}
                for f in inv:
                    prod = mul(prod, P._to_dict(f))
                self.assertEqual(prod, oracle_divisor(m, r))
                for a, b in zip(inv, inv[1:]):
                    self.assertFalse(P._divmod(b, a)[1])
            checked += 1
        self.assertGreaterEqual(checked, 30)

    def test_divisor_above_rank_is_zero(self):
        m = [[{1: 1}, {2: 1}], [{0: 1}, {1: 1}]]  # rank 1 over Q(q)
        self.assertEqual(generic_rank(m), 1)
        self.assertEqual(determinantal_divisor(m, 2), {})
        self.assertEqual(determinantal_divisor(m, 1), {0: F(1)})


class ParametricSystemTests(unittest.TestCase):
    def systems(self):
        rng = random.Random(4242)
        out = []
        while len(out) < 12:
            ops, obs = random_system(rng, n=3, g=2, o=rng.choice([1, 2]))
            if len(out) % 3 == 0:  # plant an exceptional rational parameter
                ops[0] = [[mul(x, {0: F(-1, 2), 1: 1}) for x in row] for row in ops[0]]
            out.append((ops, obs))
        return out

    def test_divisor_of_all_short_words_equals_module_divisor(self):
        for ops, obs in self.systems():
            system = PolynomialOperatorSystem(3, ops, obs)
            W = oracle_rows(ops, obs, 2)  # every row of length <= n-1
            r = oracle_generic_rank(W)
            report = parametric_observability(system)
            self.assertEqual(report['generic_rank'], r)
            module = observation_module(system)
            D = P._to_dict(P._determinantal_divisor_dense(module.at_length_bound, r)) if r else {0: F(1)}
            self.assertEqual(D, oracle_divisor(W, r) if r else {0: F(1)})

    def test_rank_drops_exactly_at_zeros_of_divisor(self):
        for ops, obs in self.systems():
            system = PolynomialOperatorSystem(3, ops, obs)
            W = oracle_rows(ops, obs, 2)
            r = oracle_generic_rank(W)
            D = oracle_divisor(W, r) if r else {0: F(1)}
            candidates = {F(k, 4) for k in range(-8, 9)}
            for root in P._rational_roots(P._from_dict(D)) if len(D) > 1 or 0 not in D else []:
                candidates.add(root)
            for q0 in sorted(candidates):
                rank = observable_closure(system.specialize(q0)).rank
                self.assertLessEqual(rank, r)
                self.assertEqual(rank == r, evaluate(D, q0) != 0, (q0, D))
                self.assertEqual(rank, rational_rank([[evaluate(x, q0) for x in row] for row in W]))

    def test_exceptional_replays(self):
        hit = 0
        for ops, obs in self.systems():
            report = parametric_observability(PolynomialOperatorSystem(3, ops, obs))
            for x in report['exceptional_real']:
                self.assertTrue(x['rank_drop_confirmed'])
                if 'value' in x:
                    self.assertLess(x['closure_rank'], report['generic_rank'])
                    hit += 1
            self.assertEqual(report['rank_equals_generic_on_real_line'], not report['exceptional_real'])
        self.assertGreater(hit, 0)


class LengthBoundTests(unittest.TestCase):
    def test_span_growth_stops_once_and_by_n_minus_one(self):
        rng = random.Random(77)
        for _ in range(15):
            n = rng.choice([2, 3, 4])
            ops, obs = random_system(rng, n=n, g=2, o=1)
            system = PolynomialOperatorSystem(n, ops, obs)
            all_rows = oracle_rows(ops, obs, n + 1)  # ordered by word length
            count = [len(obs) * sum(2 ** j for j in range(k + 1)) for k in range(n + 2)]
            for q0 in (F(0), F(1, 3), F(-2), F(1)):
                values = [[evaluate(x, q0) for x in row] for row in all_rows]
                ranks = [rational_rank(values[:count[k]]) for k in range(n + 2)]
                self.assertEqual(ranks, sorted(ranks))
                for k in range(len(ranks) - 1):
                    if ranks[k] == ranks[k + 1]:
                        self.assertTrue(all(v == ranks[k] for v in ranks[k:]))
                self.assertEqual(ranks[n - 1], ranks[-1])
                self.assertEqual(ranks[-1], observable_closure(system.specialize(q0)).rank)
            # over Q(q): the module chain ranks follow the same rule
            chain = observation_module(system).chain
            gr = [len(h) for h in chain]
            self.assertEqual(gr, sorted(gr))
            self.assertEqual(gr[min(n - 1, len(gr) - 1)], generic_closure(system).rank)
            for k in range(min(n, len(gr), 3)):
                self.assertEqual(gr[k], oracle_generic_rank(all_rows[:count[k]]))

    def test_module_is_stable_after_first_stagnation(self):
        rng = random.Random(5)
        for _ in range(10):
            ops, obs = random_system(rng, n=3, g=2, o=1, degree=2)
            module = observation_module(PolynomialOperatorSystem(3, ops, obs))
            k = module.stable_from
            self.assertTrue(all(h == module.chain[k] for h in module.chain[k:]))
            self.assertTrue(all(module.chain[i] != module.chain[i + 1] for i in range(k)))


class GenericBasisTests(unittest.TestCase):
    def test_generic_basis_drops_but_true_rank_does_not(self):
        # L1 = (1,0), L2 = (0,q), M = [[0,1],[0,0]]: B = {L1, L2}, det B = q,
        # but L1 M = (0,1) restores rank two at q = 0.
        system = PolynomialOperatorSystem(2, [[[0, 1], [0, 0]]], [[1, 0], [0, {1: 1}]])
        closure = generic_closure(system)
        self.assertEqual([(e.observation, e.word) for e in closure.basis], [(0, ()), (1, ())])
        B = [[P._to_dict(x) for x in row] for row in closure.matrix]
        self.assertEqual(oracle_divisor(B, 2), {1: F(1)})
        self.assertEqual(rank_at_rational(closure.matrix, 0), 1)
        at0 = observable_closure(system.specialize(0))
        self.assertEqual(at0.rank, 2)
        self.assertEqual([e.word for e in at0.basis], [(), (0,)])
        report = parametric_observability(system)
        self.assertEqual(report['D_r_factors'], [])
        self.assertEqual(report['exceptional_real'], [])
        self.assertEqual(report['generic_basis_spurious_factors'][0]['value'], '0/1')
        W = oracle_rows([[[0, 1], [0, 0]]], [[1, 0], [0, {1: 1}]], 1)  # n - 1 = 1
        self.assertEqual(oracle_divisor(W, 2), {0: F(1)})


class AlgebraicTests(unittest.TestCase):
    def test_irrational_exceptional_parameter(self):
        entry = mul({0: -1, 1: 2}, {0: -1, 1: 1, 2: 1})
        system = PolynomialOperatorSystem(2, [[[0, entry], [0, 0]]], [[1, 0]])
        report = parametric_observability(system)
        inside = report['exceptional_open_unit']
        self.assertEqual(len(inside), 2)
        golden = next(x for x in inside if 'isolating_interval' in x)
        a, b = (F(v) for v in golden['isolating_interval'])
        f = {0: -1, 1: 1, 2: 1}
        self.assertLess(evaluate(f, a) * evaluate(f, b), 0)  # sign change: a root inside
        self.assertLessEqual(b - a, F(1, 1024))
        self.assertFalse(a <= F(1, 2) <= b)
        self.assertEqual(golden['rank_over_number_field'], 1)
        half = next(x for x in inside if 'value' in x)
        self.assertEqual((half['value'], half['closure_rank']), ('1/2', 1))
        self.assertEqual(len(report['exceptional_real']), 3)
        module = observation_module(system).at_length_bound
        self.assertEqual(rank_at_algebraic(module, f), 1)
        self.assertEqual(rank_at_algebraic(module, {0: -2, 2: 1}), 2)  # sqrt 2 is not exceptional

    def test_factorization(self):
        f = mul(mul({0: -2, 2: 1}, mul({0: 1, 1: 1, 2: 1}, {0: 1, 1: 1, 2: 1})), mul({3: 1}, {0: 3, 1: 2}))
        lead, factors = factor_over_q(f)
        self.assertEqual(lead, 2)
        got = {tuple(sorted(g.items())): i for g, i, _ in factors}
        self.assertEqual(got, {((0, -2), (2, 1)): 1, ((0, 1), (1, 1), (2, 1)): 2,
                               ((1, 1),): 3, ((0, F(3, 2)), (1, 1)): 1})
        # irreducible over Q although reducible modulo every prime
        _, swinnerton = factor_over_q({0: 1, 2: -10, 4: 1})
        self.assertEqual(len(swinnerton), 1)
        self.assertEqual(swinnerton[0][2]['method'], 'Kronecker exhaustive search')
        _, sophie = factor_over_q({0: 4, 4: 1})  # x^4 + 4 = (x^2+2x+2)(x^2-2x+2)
        self.assertEqual(sorted(tuple(sorted(g.items())) for g, _, _ in sophie),
                         [((0, 2), (1, -2), (2, 1)), ((0, 2), (1, 2), (2, 1))])
        _, cyc = factor_over_q({0: -1, 12: 1})
        self.assertEqual(len(cyc), 6)  # Phi_d for d | 12

    def test_real_roots(self):
        roots = real_roots({0: -2, 2: 1, 4: 1})  # (q^2 - 1)(q^2 + 2)
        self.assertEqual([r['rational'] for r in roots], [F(-1), F(1)])
        self.assertEqual(real_roots({0: -2, 2: 1, 4: 1}, 'open_unit'), [])
        self.assertEqual(real_roots({0: 1, 2: 1}), [])


class GraphTests(unittest.TestCase):
    def test_specialization_matches_boundary_system(self):
        for R in (1, 2, 3):
            _, system = symbolic_boundary_system(R)
            for q0 in (F(1, 2), F(1, 3)):
                reference = BoundaryExperimentSystem(R, q0).operator_system()
                special = system.specialize(q0)
                self.assertEqual(special.operators, reference.operators)
                self.assertEqual(special.observations, reference.observations)
            self.assertEqual(observable_closure(system.specialize(F(1, 2))).rank,
                             generic_closure(system).rank)

    def test_graph_budget_two(self):
        _, system = symbolic_boundary_system(2)
        report = parametric_observability(system)
        self.assertEqual((report['dimension'], report['generic_rank'], report['D_r_degree']), (7, 7, 18))
        self.assertEqual({(f['factor'], f['multiplicity']) for f in report['D_r_factors']},
                         {('q - 1', 7), ('q + 1', 3), ('q', 4), ('q^2 + q + 1', 1), ('q^2 + 1', 1)})
        self.assertEqual(report['exceptional_open_unit'], [])
        self.assertEqual([(x['value'], x['closure_rank']) for x in report['exceptional_real']],
                         [('-1/1', 5), ('0/1', 5), ('1/1', 3)])
        # direct oracle: rank at q0 from all words of length <= n-1 would be
        # exponential; instead compare with the closure at sampled points
        D = P._determinantal_divisor_dense(observation_module(system).at_length_bound, 7)
        for q0 in (F(-1), F(0), F(1), F(1, 2), F(2), F(-3, 5)):
            rank = observable_closure(system.specialize(q0)).rank
            self.assertEqual(rank == 7, P._eval(D, q0) != 0)


class ValidationTests(unittest.TestCase):
    def test_types_and_shapes(self):
        ok = ([[[0, 1], [0, 0]]], [[1, 0]])
        PolynomialOperatorSystem(2, *ok)
        for bad in (True, 1.0, '1'):
            with self.assertRaises(TypeError):
                PolynomialOperatorSystem(2, [[[0, bad], [0, 0]]], [[1, 0]])
            with self.assertRaises(TypeError):
                PolynomialOperatorSystem(2, [[[0, {0: bad}], [0, 0]]], [[1, 0]])
            with self.assertRaises(TypeError):
                PolynomialOperatorSystem(2, *ok).specialize(bad)
        with self.assertRaises(TypeError):
            PolynomialOperatorSystem(True, *ok)
        with self.assertRaises(TypeError):
            PolynomialOperatorSystem(2, [[[0, {True: 1}], [0, 0]]], [[1, 0]])
        with self.assertRaises(TypeError):
            PolynomialOperatorSystem(2, 'ab', [[1, 0]])
        with self.assertRaises(ValueError):
            PolynomialOperatorSystem(2, [[[0, {-1: 1}], [0, 0]]], [[1, 0]])
        with self.assertRaises(ValueError):
            PolynomialOperatorSystem(2, [[[0, 1]]], [[1, 0]])
        with self.assertRaises(ValueError):
            PolynomialOperatorSystem(2, *ok, attachment_costs=[0])
        with self.assertRaises(ValueError):
            PolynomialOperatorSystem(2, [[[0, 1], [0, 0]]], [[1, 0, 0]])
        with self.assertRaises(ValueError):
            PolynomialOperatorSystem(-1, [], [])
        with self.assertRaises(TypeError):
            parametric_observability('system')
        with self.assertRaises(ValueError):
            real_roots({})
        with self.assertRaises(ValueError):
            real_roots({1: 1}, 'complex')
        with self.assertRaises(ValueError):
            factor_over_q({})
        with self.assertRaises(TypeError):
            determinantal_divisor([[1, 0.5]])
        with self.assertRaises(ValueError):
            determinantal_divisor([[1, 0], [1]])
        with self.assertRaises(TypeError):
            symbolic_boundary_system(1.0)
        with self.assertRaises(ValueError):
            symbolic_boundary_system(-1)

    def test_degenerate_systems(self):
        empty = PolynomialOperatorSystem(0, [], [])
        report = parametric_observability(empty)
        self.assertEqual((report['generic_rank'], report['D_r_degree']), (0, 0))
        zero = PolynomialOperatorSystem(2, [[[1, 0], [0, 1]]], [[0, 0]])
        self.assertEqual(parametric_observability(zero)['generic_rank'], 0)


if __name__ == '__main__':
    unittest.main()
