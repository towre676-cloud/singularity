"""Independent height-box and weighted-energy checks of the polynomial family."""
from collections import Counter
from fractions import Fraction as F
from itertools import product
import unittest

from singularity.edge_factors import (
    edge_factor_coefficients, edge_factor_moments, evaluate_factors, factor_gradient,
)
from singularity.graph import Graph
from singularity.heights import local_coefficients


class EdgeFactorTests(unittest.TestCase):
    def test_independent_boxes_and_scalar_specialization(self):
        for graph in (Graph(1), Graph(3), Graph(3, [(0,1),(1,2)]),
                      Graph(3, [(0,1),(0,2),(1,2)]), Graph(4, [(0,1),(1,2),(2,3),(0,3)])):
            rows = edge_factor_coefficients(graph, 3)
            scalar = local_coefficients(graph, 3)
            factors = tuple(F(i+1, i+3) for i in range(len(graph.edges)))
            for r, row in enumerate(rows):
                expected = F(0)
                histogram = Counter()
                for h in product(range(r+1), repeat=graph.n):
                    if sum(h) != r:
                        continue
                    term = F(1)
                    for (u,v), factor in zip(graph.edges, factors):
                        term *= factor**((h[u]-h[v])**2)
                    expected += term
                self.assertEqual(evaluate_factors(row, factors), expected)
                for exponents, count in row.items():
                    histogram[sum(exponents)] += count
                self.assertEqual(dict(histogram), scalar[r])

    def test_triangle_extreme_moments_and_quadratic_response(self):
        graph = Graph(3, [(0,1),(0,2),(1,2)])
        marked = edge_factor_moments(graph, 5)
        for k in range(1,6):
            k2 = k*k
            self.assertEqual(marked[k,k2], {(k2,k2,0):1,(k2,0,k2):1,(0,k2,k2):1})
        c1 = edge_factor_coefficients(graph, 1)[1]
        t, e = F(1,2), F(1,10)
        self.assertEqual(evaluate_factors(c1, (t+e,t-e,t)), 3*t*t-e*e)
        self.assertEqual(factor_gradient(c1, (t,t,t)), (2*t,)*3)

    def test_derivatives_at_zero_and_input_budget(self):
        self.assertEqual(factor_gradient({(1,0):2,(0,2):3}, (0,0)), (2,0))
        self.assertEqual(evaluate_factors({():5}, ()), 5)
        with self.assertRaises(TypeError):
            evaluate_factors({(1,):1}, (0.5,))
        with self.assertRaises(ValueError):
            factor_gradient({(1,0):1}, (1,))
        with self.assertRaises(ValueError):
            edge_factor_coefficients(Graph(10), 10, profile_budget=100)


if __name__ == '__main__':
    unittest.main()
