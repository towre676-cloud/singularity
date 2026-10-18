"""Quadratic Gauss sums of the Laplacian energy at odd primes (SNG-F30).

For an odd prime p and w = exp(2 pi i / p),

    Gamma_G(p) = sum_{a in F_p^n} w^(E_G(a)) = p^(n-r) chi(D) g_p^r,

where r is the rank of the Laplacian modulo p, D the product of the nonzero
diagonal entries of any congruence diagonalization P^T L P = diag(...) over
F_p (well defined up to squares), chi the Legendre symbol and
g_p = sum_t w^(t^2).  Rank zero gives p^n.  Everything is compared in the
exact ring Z[t]/Phi_p(t) of ``conductor.py``; no square root of p is used.
Characteristic two and prime powers are outside this module: completing the
square needs 2 to be invertible.
"""

from __future__ import annotations

from typing import Sequence

from .conductor import CyclotomicRing, residue_numerator
from .graph import Graph, _integer

Matrix = tuple[tuple[int, ...], ...]


def _odd_prime(p: int) -> int:
    p = _integer(p, "prime", minimum=2)
    if p == 2:
        raise ValueError("characteristic two is not supported: completing the square needs 1/2")
    if any(p % d == 0 for d in range(2, int(p ** 0.5) + 1)):
        raise ValueError(f"{p} is not prime; prime powers and composite moduli are not supported")
    return p


def legendre(value: int, p: int) -> int:
    """Legendre symbol (value/p) for an odd prime p, by Euler's criterion."""
    p = _odd_prime(p)
    value %= p
    if value == 0:
        return 0
    return 1 if pow(value, (p - 1) // 2, p) == 1 else -1


def _transform(m: list[list[int]], p_matrix: list[list[int]], target: int, source: int, factor: int, p: int) -> None:
    """Basis change e_target <- e_target + factor * e_source, applied as a congruence."""
    n = len(m)
    for row in range(n):
        m[row][target] = (m[row][target] + factor * m[row][source]) % p
    for col in range(n):
        m[target][col] = (m[target][col] + factor * m[source][col]) % p
    for row in range(n):
        p_matrix[row][target] = (p_matrix[row][target] + factor * p_matrix[row][source]) % p


def _swap(m: list[list[int]], p_matrix: list[list[int]], i: int, j: int) -> None:
    m[i], m[j] = m[j], m[i]
    for row in m:
        row[i], row[j] = row[j], row[i]
    for row in p_matrix:
        row[i], row[j] = row[j], row[i]


def diagonalize(matrix: Sequence[Sequence[int]], p: int) -> tuple[Matrix, tuple[int, ...]]:
    """Return (P, diagonal) with P^T M P = diag(diagonal) modulo an odd prime p.

    Columns of P are the new basis vectors; P is invertible modulo p.
    """
    p = _odd_prime(p)
    m = [[int(x) % p for x in row] for row in matrix]
    n = len(m)
    if any(len(row) != n for row in m) or any(m[i][j] != m[j][i] for i in range(n) for j in range(n)):
        raise ValueError("a square symmetric matrix is required")
    basis = [[int(i == j) for j in range(n)] for i in range(n)]
    for k in range(n):
        pivot = next((i for i in range(k, n) if m[i][i]), None)
        if pivot is None:
            pair = next(((i, j) for i in range(k, n) for j in range(i + 1, n) if m[i][j]), None)
            if pair is None:
                break  # the remaining block is zero
            i, j = pair
            _transform(m, basis, i, j, 1, p)  # new diagonal 2 m_ij, nonzero as p is odd
            pivot = i
        _swap(m, basis, k, pivot)
        inverse = pow(m[k][k], -1, p)
        for j in range(k + 1, n):
            if m[k][j]:
                _transform(m, basis, j, k, (-m[k][j] * inverse) % p, p)
    return tuple(map(tuple, basis)), tuple(m[i][i] for i in range(n))


def _check_witness(matrix: Sequence[Sequence[int]], basis: Matrix, diagonal: Sequence[int], p: int) -> bool:
    n = len(matrix)
    for i in range(n):
        for j in range(n):
            value = sum(basis[a][i] * matrix[a][b] * basis[b][j] for a in range(n) for b in range(n)) % p
            if value != (diagonal[i] % p if i == j else 0):
                return False
    return _determinant_mod(basis, p) != 0


def _determinant_mod(matrix: Sequence[Sequence[int]], p: int) -> int:
    m = [[x % p for x in row] for row in matrix]
    n, det = len(m), 1
    for k in range(n):
        pivot = next((i for i in range(k, n) if m[i][k]), None)
        if pivot is None:
            return 0
        if pivot != k:
            m[k], m[pivot] = m[pivot], m[k]
            det = -det
        det = det * m[k][k] % p
        inverse = pow(m[k][k], -1, p)
        for i in range(k + 1, n):
            factor = m[i][k] * inverse % p
            m[i] = [(x - factor * y) % p for x, y in zip(m[i], m[k])]
    return det % p


def laplacian_invariants(graph: Graph, p: int) -> dict[str, object]:
    """Rank and discriminant square class of the Laplacian modulo p, with witness."""
    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    p = _odd_prime(p)
    laplacian = graph.laplacian()
    basis, diagonal = diagonalize(laplacian, p)
    if not _check_witness(laplacian, basis, diagonal, p):
        raise ArithmeticError("diagonalization witness failed")
    nonzero = [d for d in diagonal if d % p]
    discriminant = 1
    for d in nonzero:
        discriminant = discriminant * d % p
    return {
        "prime": p, "n": graph.n, "rank": len(nonzero),
        "diagonal": list(diagonal), "basis_columns": [list(row) for row in basis],
        "discriminant": discriminant, "discriminant_character": legendre(discriminant, p),
    }


def gauss_sum_direct(graph: Graph, p: int, max_profiles: int = 1_000_000) -> tuple[int, ...]:
    """sum over F_p^n of w^E(a), as the x=1 value of the residue numerator."""
    p = _odd_prime(p)
    ring, numerator = residue_numerator(graph, p, max_profiles)
    total = ring.zero
    for element in numerator:
        total = ring.add(total, element)
    return total


def gauss_sum_formula(graph: Graph, p: int) -> tuple[int, ...]:
    """p^(n-r) chi(D) g_p^r in Z[t]/Phi_p(t)."""
    invariants = laplacian_invariants(graph, p)
    ring = CyclotomicRing(p)
    g = ring.zero
    for t in range(p):
        g = ring.add(g, ring.phase(t * t))
    rank = invariants["rank"]
    factor = p ** (graph.n - rank) * (invariants["discriminant_character"] if rank else 1)
    return ring.scale(ring.power(g, rank), factor)
