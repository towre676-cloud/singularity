from itertools import combinations
import unittest
from singularity.graph import Graph
from singularity.heights import marked_coefficients
from singularity.primitive import primitive_marked_coefficients, direct_primitive_marked_coefficients, recompose_primitive_counts


class PrimitiveTests(unittest.TestCase):
    def test_scaling_and_inversion_on_all_small_graphs(self):
        for n in range(1,5):
            edges=list(combinations(range(n),2))
            for mask in range(1<<len(edges)):
                graph=Graph(n,[edge for i,edge in enumerate(edges) if mask&(1<<i)])
                primitive=primitive_marked_coefficients(graph,6)
                self.assertEqual(primitive,direct_primitive_marked_coefficients(graph,6))
                self.assertEqual(recompose_primitive_counts(primitive,6),marked_coefficients(graph,6))


if __name__=='__main__':
    unittest.main()
