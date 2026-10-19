"""An all-budget robust optimum for actual graph experiments.

The theorem is proved in ORDERED_CONTEXTS.md.  These checks compare its
closed form to both search algorithms and to independent graph enumeration.
"""
import unittest
from fractions import Fraction as F
from itertools import product

from singularity.graph import Graph
from singularity.graph_experiments import BoundaryExperimentSystem
from singularity.robust_search import bounded_margin_search, exhaustive_margin_search


PATH = Graph(3, ((0, 1), (1, 2)))


class PathMarginTests(unittest.TestCase):
    def test_all_budget_formula_matches_both_exact_searches(self):
        for q in (F(1, 3), F(1, 2), F(2, 3), F(4, 5)):
            compiler = BoundaryExperimentSystem(1, q)
            system = compiler.operator_system(attachment_costs=(2, 1))
            left, right = (compiler.compile_graph(PATH, terminals)
                           for terminals in ((0, 2), (0, 1)))
            d = tuple(x - y for x, y in zip(left, right))
            a = q * (1 - q)
            self.assertEqual(d, (0, -a, a))
            for numerator in range(15):
                budget = F(numerator, 2)
                k = budget.numerator // budget.denominator
                expected = a * (1 - q ** k)
                for search in (exhaustive_margin_search, bounded_margin_search):
                    result = search(system, d, (1, 1), budget)
                    self.assertEqual(result.margin, expected, (q, budget, search.__name__))
                    if k:
                        self.assertEqual(result.experiment.word, (1,) * k)
                        self.assertEqual(result.experiment.observation, 1)

    def test_every_short_word_has_the_predicted_graph_discrepancy(self):
        # local_coefficients of newly assembled graphs is independent of
        # the compiler's context matrices and the robust search routines.
        for q in (F(1, 3), F(1, 2), F(2, 3)):
            compiler = BoundaryExperimentSystem(1, q)
            a = q * (1 - q)
            for length in range(6):
                for word in product(range(2), repeat=length):
                    readings = [compiler.direct_observations(PATH, terminals, word)
                                for terminals in ((0, 2), (0, 1))]
                    self.assertEqual(tuple(x - y for x, y in zip(*readings)),
                                     (0, -a * (1 - q ** length)), (q, word))

    def test_finite_budget_never_attains_the_unbounded_supremum(self):
        q = F(1, 2)
        supremum = q * (1 - q)
        previous = F(0)
        for k in range(1, 101):
            optimum = supremum * (1 - q ** k)
            self.assertLess(previous, optimum)
            self.assertLess(optimum, supremum)
            self.assertEqual(supremum - optimum, q ** k / 4)
            previous = optimum


if __name__ == "__main__":
    unittest.main()
