"""P19: odd-prime Laplacian Gauss sums, diagonalization witnesses, exceptional primes."""

from itertools import combinations, product
import unittest

from singularity.conductor import CyclotomicRing
from singularity.examples import GRAPHS
from singularity.gauss import (
    diagonalize, gauss_sum_direct, gauss_sum_formula, laplacian_invariants, legendre,
)
from singularity.graph import Graph


def all_graphs(max_n):
    for n in range(1, max_n + 1):
        pairs = list(combinations(range(n), 2))
        for mask in range(1 << len(pairs)):
            yield Graph(n, [edge for j, edge in enumerate(pairs) if mask >> j & 1])


def matrix_rank_mod(matrix, p):
    """Independent row-reduction rank, no congruence transformations."""
    m = [[x % p for x in row] for row in matrix]
    rank, col, n = 0, 0, len(m)
    while rank < n and col < n:
        pivot = next((i for i in range(rank, n) if m[i][col]), None)
        if pivot is None:
            col += 1
            continue
        m[rank], m[pivot] = m[pivot], m[rank]
        inverse = pow(m[rank][col], -1, p)
        for i in range(n):
            if i != rank and m[i][col]:
                factor = m[i][col] * inverse % p
                m[i] = [(x - factor * y) % p for x, y in zip(m[i], m[rank])]
        rank += 1
        col += 1
    return rank


class GaussSumTests(unittest.TestCase):
    def test_formula_equals_direct_residue_sum(self):
        checks = 0
        for graph in all_graphs(4):
            for p in (3, 5, 7):
                with self.subTest(graph=graph, p=p):
                    self.assertEqual(gauss_sum_formula(graph, p), gauss_sum_direct(graph, p))
                checks += 1
        for graph in all_graphs(5):
            if graph.n == 5:
                self.assertEqual(gauss_sum_formula(graph, 3), gauss_sum_direct(graph, 3))
                checks += 1
        self.assertEqual(checks, 75 * 3 + 1024)

    def test_witness_rank_and_invertibility(self):
        for graph in (GRAPHS["spectral_g"], GRAPHS["binary_h"], Graph(4, combinations(range(4), 2)), Graph(3)):
            for p in (3, 5, 7, 11):
                info = laplacian_invariants(graph, p)
                basis, diagonal = info["basis_columns"], info["diagonal"]
                lap = graph.laplacian()
                for i, j in product(range(graph.n), repeat=2):
                    value = sum(basis[a][i] * lap[a][b] * basis[b][j] for a in range(graph.n) for b in range(graph.n)) % p
                    self.assertEqual(value, diagonal[i] if i == j else 0)
                self.assertEqual(info["rank"], matrix_rank_mod(lap, p))

    def test_exceptional_prime_triangle_mod_three(self):
        triangle = Graph(3, [(0, 1), (1, 2), (0, 2)])  # spanning trees: 3
        ring = CyclotomicRing(3)
        info = laplacian_invariants(triangle, 3)
        self.assertEqual(info["rank"], 1)              # L = 2 J (mod 3)
        self.assertEqual(info["discriminant_character"], -1)
        g3 = ring.add(ring.one, ring.scale(ring.phase(1), 2))
        self.assertEqual(gauss_sum_direct(triangle, 3), ring.scale(g3, -9))
        self.assertEqual(laplacian_invariants(triangle, 5)["rank"], 2)
        # Nondegenerate formula p * chi(tau) * g^(n-1) holds when p does not divide tau.
        g5 = CyclotomicRing(5).zero
        r5 = CyclotomicRing(5)
        for t in range(5):
            g5 = r5.add(g5, r5.phase(t * t))
        self.assertEqual(gauss_sum_direct(triangle, 5), r5.scale(r5.power(g5, 2), 5 * legendre(3, 5)))

    def test_singular_directions_include_components(self):
        graph = Graph(5, [(0, 1), (2, 3)])  # three components: rank n - 3
        for p in (3, 5):
            info = laplacian_invariants(graph, p)
            self.assertEqual(info["rank"], 2)
            self.assertEqual(gauss_sum_formula(graph, p), gauss_sum_direct(graph, p))
        self.assertEqual(gauss_sum_formula(Graph(2), 3), (9, 0))  # rank zero: p^n

    def test_diagonalizer_handles_zero_diagonal_and_rejects_bad_input(self):
        basis, diagonal = diagonalize([[0, 1], [1, 0]], 3)
        self.assertEqual(sorted(d != 0 for d in diagonal), [True, True])
        for p in (2, 4, 9, 1, True):
            with self.assertRaises((TypeError, ValueError)):
                gauss_sum_formula(Graph(2, [(0, 1)]), p)
        with self.assertRaises(ValueError):
            diagonalize([[1, 2], [0, 1]], 3)
        self.assertEqual([legendre(a, 7) for a in range(7)], [0, 1, 1, -1, 1, -1, -1])


if __name__ == "__main__":
    unittest.main()
