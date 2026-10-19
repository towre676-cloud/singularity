"""Exact monogenic Q-algebras, adapted from Morphonic finite_extensions.js.

Uses PerfectPower's rational polynomial core. Irreducibility is NOT assumed or
certified: reducible moduli and zero divisors are supported. Norm and trace are
those of the multiplication matrix, not an unproved number-field assertion.
These are proposal computations, with execution_verified=False in receipts.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from . import polyalg as P
from .core import mul, subtract


def determinant(matrix):
    a = [list(map(Q, row)) for row in matrix]
    n, result = len(a), Q(1)
    if any(len(row) != n for row in a):
        raise ValueError('a square matrix is required')
    for c in range(n):
        pivot = next((i for i in range(c, n) if a[i][c]), None)
        if pivot is None:
            return Q(0)
        if pivot != c:
            a[c], a[pivot] = a[pivot], a[c]
            result = -result
        v = a[c][c]
        result *= v
        for i in range(c+1, n):
            ratio = a[i][c]/v
            for j in range(c, n):
                a[i][j] -= ratio*a[c][j]
    return result


@dataclass(frozen=True)
class QuotientAlgebra:
    modulus: tuple

    def __post_init__(self):
        m = P.poly(self.modulus)
        if P.degree(m) < 1:
            raise ValueError('a nonconstant modulus is required')
        object.__setattr__(self, 'modulus', P.monic(m))

    @property
    def degree(self):
        return len(self.modulus)-1

    def element(self, coefficients):
        if isinstance(coefficients, Element):
            if coefficients.algebra != self:
                raise ValueError('elements belong to different quotient algebras')
            return coefficients
        if isinstance(coefficients, (int, Q)):
            coefficients = (coefficients,)
        reduced = P.divmod_poly(P.poly(coefficients), self.modulus)[1]
        return Element(self, reduced)


@dataclass(frozen=True)
class Element:
    algebra: QuotientAlgebra
    coefficients: tuple

    def __post_init__(self):
        object.__setattr__(self, 'coefficients',
                           P.divmod_poly(P.poly(self.coefficients), self.algebra.modulus)[1])

    def __add__(self, other):
        other = self.algebra.element(other)
        return self.algebra.element(P.add(self.coefficients, other.coefficients))

    def __neg__(self):
        return self.algebra.element(P.scale(self.coefficients, -1))

    def __sub__(self, other):
        return self + -self.algebra.element(other)

    def __mul__(self, other):
        other = self.algebra.element(other)
        return self.algebra.element(mul(self.coefficients, other.coefficients))

    def __pow__(self, exponent):
        if type(exponent) is not int:
            raise TypeError('an integer exponent is required')
        if exponent < 0:
            return self.inverse() ** -exponent
        out, base = self.algebra.element(1), self
        while exponent:
            if exponent & 1:
                out = out*base
            base, exponent = base*base, exponent//2
        return out

    def inverse(self):
        a, b = self.algebra.modulus, self.coefficients
        u, v = P.ZERO, P.ONE
        while not P.is_zero(b):
            q, r = P.divmod_poly(a, b)
            a, b, u, v = b, r, v, subtract(u, mul(q, v))
        if P.degree(a) != 0:
            raise ZeroDivisionError('element is not a unit in this quotient algebra')
        return self.algebra.element(P.scale(u, 1/a[0]))

    def matrix(self):
        n = self.algebra.degree
        columns = [(self*self.algebra.element((0,)*j+(1,))).coefficients
                   for j in range(n)]
        return tuple(tuple(col[i] if i < len(col) else Q(0) for col in columns)
                     for i in range(n))

    def trace(self):
        m = self.matrix()
        return sum((m[i][i] for i in range(len(m))), Q(0))

    def norm(self):
        return determinant(self.matrix())

    def characteristic_polynomial(self):
        # Faddeev–LeVerrier, exactly as in the reusable JS source, over Q.
        a = self.matrix()
        n = len(a)
        b = [[Q(i == j) for j in range(n)] for i in range(n)]
        coefficients = [Q(1)]
        for k in range(1, n+1):
            ab = [[sum((a[i][h]*b[h][j] for h in range(n)), Q(0))
                   for j in range(n)] for i in range(n)]
            c = -sum((ab[i][i] for i in range(n)), Q(0))/k
            coefficients.append(c)
            b = [[ab[i][j] + (c if i == j else 0) for j in range(n)] for i in range(n)]
        return tuple(reversed(coefficients))

    def receipt(self):
        return {'modulus': list(map(str, self.algebra.modulus)),
                'element': list(map(str, self.coefficients)),
                'norm': str(self.norm()), 'trace': str(self.trace()),
                'characteristic_polynomial': list(map(str, self.characteristic_polynomial())),
                'execution_verified': False, 'irreducibility_certified': False}
