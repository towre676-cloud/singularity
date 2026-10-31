#!/usr/bin/env python3
"""All-order first and second off-diagonal connected-pattern coefficients.

The formulas use only vertex degrees and connected components after
deleting one or two vertices.  No height enumeration or cumulant table
is used.  Polynomials are returned as q-exponent -> Fraction dictionaries.
"""
from fractions import Fraction as Q
from functools import lru_cache
from itertools import combinations

from vol8_lib import degrees_of, edges_of


def add(a, b, scale=1):
    out = dict(a)
    for i, x in b.items():
        out[i] = out.get(i, Q(0)) + scale * x
    return {i: x for i, x in out.items() if x}


def multiply(a, b):
    out = {}
    for i, x in a.items():
        for j, y in b.items():
            out[i + j] = out.get(i + j, Q(0)) + x * y
    return {i: x for i, x in out.items() if x}


@lru_cache(None)
def _power(items, n):
    a = dict(items)
    out = {0: Q(1)}
    for _ in range(n):
        out = multiply(out, a)
    return tuple(sorted(out.items()))


def power(a, n):
    return dict(_power(tuple(sorted(a.items())), n))


@lru_cache(None)
def components_after_delete(mask, k, deleted):
    """Connected components as sorted tuples, with deleted a sorted tuple."""
    es = edges_of(mask, k)
    remaining = set(range(k)) - set(deleted)
    out = []
    while remaining:
        reached = {min(remaining)}
        todo = list(reached)
        while todo:
            v = todo.pop()
            for a, b in es:
                w = b if a == v else a if b == v else -1
                if w in remaining and w not in reached:
                    reached.add(w)
                    todo.append(w)
        remaining -= reached
        out.append(tuple(sorted(reached)))
    return tuple(out)


F = {0: Q(-1), 1: Q(1)}  # z - 1, z = q^-2
A = {0: Q(1), 1: Q(1)}   # z + 1
B = {0: Q(1), 1: Q(1), 2: Q(1)}


def q_polynomial(z_polynomial, q_shift):
    return {q_shift - 2 * j: c for j, c in z_polynomial.items() if c}


def first_off_diagonal(mask, k, regular_degree=3):
    """[x^(k+1)] B_H for a connected k-vertex pattern in d-regular hosts."""
    es = edges_of(mask, k)
    degrees = degrees_of(mask, k)
    first = {}
    second = Q(0)
    for v in range(k):
        first = add(first, power(A, degrees[v]))
        second += Q(2) ** (len(components_after_delete(mask, k, (v,))) - 1)
    f_power = power(F, len(es))
    return add(
        q_polynomial(multiply(f_power, first), regular_degree * (k + 3)),
        q_polynomial(f_power, regular_degree * (k + 1)),
        -second,
    )


def second_off_diagonal_blocks(mask, k):
    """Return the four z-polynomials U3,U22,M,D before multiplication by f^e.

    beta_(H,k+2) = f^e [q^(3k+24)U3 + q^(3k+18)U22
                           - q^(3k+12)M + q^(3k+6)D].
    """
    es = edges_of(mask, k)
    eset = set(es)
    degrees = degrees_of(mask, k)
    single_components = {v: components_after_delete(mask, k, (v,)) for v in range(k)}
    articulation_weights = {v: Q(2) ** (len(single_components[v]) - 1) for v in range(k)}
    high3, high22, mixed = {}, {}, {}
    binary = {0: sum(Q(3) ** (len(single_components[v]) - 1) for v in range(k))}

    for v in range(k):
        high3 = add(high3, power(B, degrees[v]))
        product = {0: Q(1)}
        for component in single_components[v]:
            boundary = sum((a == v and b in component) or (b == v and a in component) for a, b in es)
            product = multiply(product, add({0: Q(1)}, power(A, boundary)))
        mixed = add(mixed, product)
        for u in range(k):
            if u != v:
                mixed = add(mixed, power(A, degrees[u]), articulation_weights[v])

    for u, v in combinations(range(k), 2):
        adjacent = int((u, v) in eset)
        product = power(A, degrees[u] + degrees[v] - adjacent)
        if adjacent:
            product = multiply(product, {0: Q(1), 2: Q(1)})
        high22 = add(high22, product)

        components = components_after_delete(mask, k, (u, v))
        one_sided = 0
        for component in components:
            touches_u = any(tuple(sorted((u, w))) in eset for w in component)
            touches_v = any(tuple(sorted((v, w))) in eset for w in component)
            one_sided += touches_u != touches_v
        binary = add(binary, {0: Q(2) ** (one_sided + 1)})
        binary = add(binary, power(A, adjacent), -Q(2) ** (len(components) - 1))
    return high3, high22, mixed, binary


def second_off_diagonal(mask, k, regular_degree=3):
    """[x^(k+2)] B_H, proved for every finite connected simple pattern H.

    For regular degree d the four q-shifts are d(k+8), d(k+6),
    d(k+4), d(k+2), respectively.  This function needs only the pattern.
    """
    blocks = second_off_diagonal_blocks(mask, k)
    f_power = power(F, len(edges_of(mask, k)))
    result = {}
    for block, increment, sign in zip(blocks, (8, 6, 4, 2), (1, 1, -1, 1)):
        term = q_polynomial(multiply(f_power, block), regular_degree * (k + increment))
        result = add(result, term, sign)
    return result
