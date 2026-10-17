"""Exact root-of-unity specialization in Z[t]/Phi_l(t).

The finite numerator is a residue-box computation. It is not an assertion of
modularity of the associated infinite Euler product.
"""
from functools import lru_cache
from itertools import product
from math import comb


def _trim(a):
    a = list(a)
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return tuple(a or [0])


def _monic_divide(a, b):
    a = list(_trim(a)); b = _trim(b)
    if b[-1] != 1:
        raise ValueError("divisor must be monic")
    quotient = [0] * max(1, len(a) - len(b) + 1)
    while len(a) >= len(b) and any(a):
        shift = len(a) - len(b); leading = a[-1]
        quotient[shift] += leading
        for j, value in enumerate(b):
            a[shift + j] -= leading * value
        a = list(_trim(a))
    if any(a):
        raise ArithmeticError("non-exact cyclotomic division")
    return _trim(quotient)


@lru_cache(None)
def cyclotomic_polynomial(order):
    """Return constant-first integer coefficients of Phi_order."""
    if isinstance(order, bool) or not isinstance(order, int) or order < 1:
        raise ValueError("conductor must be a positive integer")
    polynomial = [-1] + [0] * (order - 1) + [1]
    for divisor in range(1, order):
        if order % divisor == 0:
            polynomial = _monic_divide(polynomial, cyclotomic_polynomial(divisor))
    return tuple(polynomial)


class CyclotomicRing:
    """Integer quotient ring with tuple-valued, constant-first elements."""
    def __init__(self, order):
        self.order = order
        self.modulus = cyclotomic_polynomial(order)
        self.degree = len(self.modulus) - 1
        self.zero = (0,) * self.degree
        self.one = (1,) + (0,) * (self.degree - 1)

    def reduce(self, values):
        a = list(values)
        while len(a) > self.degree:
            leading = a[-1]; shift = len(a) - self.degree - 1
            for j, value in enumerate(self.modulus):
                a[shift + j] -= leading * value
            a.pop()
        return tuple(a + [0] * (self.degree - len(a)))

    def add(self, a, b):
        return self.reduce([x + y for x, y in zip(self.reduce(a), self.reduce(b))])

    def scale(self, a, scalar):
        return tuple(scalar * x for x in self.reduce(a))

    def multiply(self, a, b):
        a = self.reduce(a); b = self.reduce(b)
        out = [0] * (2 * self.degree - 1)
        for i, x in enumerate(a):
            for j, y in enumerate(b):
                out[i + j] += x * y
        return self.reduce(out)

    def power(self, a, exponent):
        if isinstance(exponent, bool) or not isinstance(exponent, int) or exponent < 0:
            raise ValueError("exponent must be a nonnegative integer")
        result = self.one; base = self.reduce(a)
        while exponent:
            if exponent & 1:
                result = self.multiply(result, base)
            base = self.multiply(base, base); exponent //= 2
        return result

    def phase(self, exponent):
        exponent %= self.order
        return self.reduce([0] * exponent + [1])


def residue_numerator(graph, order, max_profiles=1_000_000):
    """Return (ring, numerator) for L=N/(1-x^order)^n.

    Work is bounded explicitly by order**n. A refusal is a resource limit,
    not a mathematical claim that no smaller representation exists.
    """
    ring = CyclotomicRing(order)
    profiles = order ** graph.n
    if profiles > max_profiles:
        raise ValueError(f"residue box has {profiles} profiles; budget is {max_profiles}")
    numerator = [ring.zero for _ in range(graph.n * (order - 1) + 1)]
    phases = [ring.phase(j) for j in range(order)]
    for rho in product(range(order), repeat=graph.n):
        volume = sum(rho)
        numerator[volume] = ring.add(numerator[volume], phases[graph.energy(rho) % order])
    return ring, numerator


def remote_coefficient(graph, order, index, max_profiles=1_000_000):
    """Exact coefficient at an arbitrary nonnegative integer index."""
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise ValueError("index must be a nonnegative integer")
    ring, numerator = residue_numerator(graph, order, max_profiles)
    answer = ring.zero
    for j, coefficient in enumerate(numerator):
        if index >= j and (index - j) % order == 0:
            count = comb((index - j) // order + graph.n - 1, graph.n - 1)
            answer = ring.add(answer, ring.scale(coefficient, count))
    return answer
