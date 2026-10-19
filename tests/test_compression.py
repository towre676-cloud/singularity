"""Family compression: typed transitions, cyclicity and the star-family bound."""
import unittest
from fractions import Fraction as F

from singularity.compression import (compression_report, cyclicity_certificate, independent_star,
                                     observable_dimension, reachable_subspace, star_coordinates,
                                     star_function_dimension, star_reconstruction, star_transition)
from singularity.graph_experiments import BoundaryExperimentSystem
from singularity.observability import observable_closure

HALF = F(1, 2)


def rank(rows, n):
    a = [list(r) for r in rows]
    k = 0
    for c in range(n):
        p = next((i for i in range(k, len(a)) if a[i][c]), None)
        if p is None:
            continue
        a[k], a[p] = a[p], a[k]
        for i in range(len(a)):
            if i != k and a[i][c]:
                f = a[i][c] / a[k][c]
                a[i] = [u - f * w for u, w in zip(a[i], a[k])]
        k += 1
    return k


class TypedTransitionTests(unittest.TestCase):
    def test_star_family_is_closed_under_the_standard_contexts(self):
        system = BoundaryExperimentSystem(3, HALF)
        names = [a.name for a in system.attachments]
        for params in [(0, 0, 0, 0, False), (2, 0, 1, 1, False), (1, 3, 0, 0, True), (0, 1, 2, 2, True)]:
            state = system.compile_graph(independent_star(*params), (0, 1))
            for i, name in enumerate(names):
                after = star_transition(params, name)
                moved = system.apply_word(state, (i,))
                self.assertEqual(moved, system.compile_graph(independent_star(*after), (0, 1)))
                # Independent: direct enumeration of the actual glued graph.
                self.assertEqual(system.observe(state, (i,)),
                                 system.direct_observations(independent_star(*params), (0, 1), (i,)))
        with self.assertRaises(ValueError):
            star_transition((0, 0, 0, 0, False), "other")

    def test_star_validation(self):
        with self.assertRaises(TypeError):
            independent_star(True)
        with self.assertRaises(ValueError):
            independent_star(-1)
        with self.assertRaises(TypeError):
            independent_star(1, terminal_edge=1)
        self.assertEqual(independent_star(1, 1, 1, 1, True).edges, ((0, 1), (0, 2), (0, 4), (1, 3), (1, 4)))


class CyclicityTests(unittest.TestCase):
    def test_certificate_holds_exactly_through_budget_six(self):
        for R in range(1, 9):
            certificate = cyclicity_certificate(BoundaryExperimentSystem(R, HALF))
            self.assertEqual(certificate["full_block_algebra"], R <= 6, R)
            self.assertTrue(certificate["linear_terms_nonzero"])

    def test_every_seed_reaches_the_whole_space(self):
        # SNG-O13 predicts this for R <= 6; Krylov closure confirms it for R <= 4.
        seeds = [(0, 0, 0, 0, False), (1, 0, 0, 0, False), (0, 2, 1, 0, True), (0, 0, 0, 3, False)]
        for R in range(1, 5):
            system = BoundaryExperimentSystem(R, HALF)
            operators = system.operator_system()
            for seed in seeds:
                state = system.compile_graph(independent_star(*seed), (0, 1))
                self.assertEqual(len(reachable_subspace(operators, (state,))), system.dimension)

    def test_reachable_dimension_is_seed_independent(self):
        # Reach = A v with v a unit in every block, so dim Reach = dim A.
        system = BoundaryExperimentSystem(3, HALF)
        operators = system.operator_system()
        from singularity.graph import Graph
        bases = [(Graph(3, ((0, 1), (1, 2))), (0, 2)), (Graph(4, ((0, 2), (2, 3), (3, 1))), (0, 1)),
                 (Graph(2, ()), (0, 1))]
        dims = {len(reachable_subspace(operators, (system.compile_graph(g, t),))) for g, t in bases}
        self.assertEqual(dims, {system.dimension})

    def test_reachable_subspace_is_invariant(self):
        system = BoundaryExperimentSystem(2, HALF)
        operators = system.operator_system()
        state = system.compile_graph(independent_star(1), (0, 1))
        basis = reachable_subspace(operators, (state,))
        n = system.dimension
        for m in operators.operators:
            images = [tuple(sum(m[r][k] * v[k] for k in range(n)) for r in range(n)) for v in basis]
            self.assertEqual(rank(list(basis) + images, n), len(basis))


class StarFamilyTests(unittest.TestCase):
    def test_span_meets_the_function_space_bound(self):
        for R in range(1, 6):
            system = BoundaryExperimentSystem(R, HALF)
            d = star_function_dimension(R)
            states = [system.compile_graph(independent_star(a), (0, 1)) for a in range(d + 3)]
            self.assertEqual(rank(states, system.dimension), d)
            if R >= 2:
                self.assertLess(d, system.dimension)

    def test_reconstruction_is_exact_on_held_out_alpha(self):
        for R in range(1, 6):
            system = BoundaryExperimentSystem(R, HALF)
            C = star_reconstruction(system, verify_through=star_function_dimension(R) + 6)
            self.assertEqual(len(C), system.dimension)
            self.assertEqual(len(C[0]), star_function_dimension(R))
        # A different q works too.
        star_reconstruction(BoundaryExperimentSystem(3, F(2, 5)))

    def test_star_coordinates(self):
        self.assertEqual(star_coordinates(1, HALF, 3), (1, 3, F(1, 8)))
        with self.assertRaises(TypeError):
            star_coordinates(1, 0.5, 3)

    def test_compression_report(self):
        system = BoundaryExperimentSystem(3, HALF)
        report = compression_report(system, [(independent_star(a), (0, 1)) for a in range(6)])
        self.assertEqual(report["formal_dimension"], 13)
        self.assertEqual(report["formal_quotient"], 13)
        self.assertEqual(report["family_span"], 6)
        self.assertEqual(report["family_observable"], 6)
        self.assertEqual(report["reachable"], 13)
        rows = observable_closure(system.operator_system()).rows
        self.assertEqual(observable_dimension(rows, ()), 0)


if __name__ == "__main__":
    unittest.main()
