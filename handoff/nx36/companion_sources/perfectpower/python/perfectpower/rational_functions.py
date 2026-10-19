"""Budgeted Q(t) arithmetic; canonical monic denominators, no symbolic eval."""
from fractions import Fraction as Q
from . import polyalg as P
from .core import mul
from .observable_machine import _q
from .divisor_square import WorkLimit


class AlgebraBudget:
    def __init__(self, work_limit=5000000, degree_limit=128, bit_limit=4096):
        if any(type(v) is not int or v < 1 for v in (work_limit, degree_limit, bit_limit)):
            raise ValueError('positive algebra budgets required')
        if work_limit > 20000000 or degree_limit > 256 or bit_limit > 8192:
            raise ValueError('algebra budgets exceed supported limits')
        self.work_limit, self.degree_limit, self.bit_limit = work_limit, degree_limit, bit_limit
        self.work = 0

    def check(self, *polynomials):
        self.work += 1 + sum(len(p) for p in polynomials)
        if self.work > self.work_limit:
            raise WorkLimit('rational-function algebra work budget')
        for p in polynomials:
            if P.degree(p) > self.degree_limit:
                raise WorkLimit('rational-function degree budget')
            if any(max(abs(c.numerator).bit_length(), c.denominator.bit_length()) > self.bit_limit for c in p):
                raise WorkLimit('rational-function coefficient bit budget')


class RationalFunction:
    def __init__(self, numerator=(0,), denominator=(1,), *, budget=None):
        n, d = P.poly(map(_q, numerator)), P.poly(map(_q, denominator))
        if P.is_zero(d):
            raise ValueError('nonzero rational-function denominator required')
        if budget: budget.check(n, d)
        if P.is_zero(n): n, d = P.ZERO, P.ONE
        else:
            g = P.gcd_poly(n, d); n, d = P.exact_div(n, g), P.exact_div(d, g)
            factor = 1 / d[-1]; n, d = P.scale(n, factor), P.scale(d, factor)
        if budget: budget.check(n, d)
        self.n, self.d, self.budget = n, d, budget

    @classmethod
    def parse(cls, value, budget=None):
        if isinstance(value, cls):
            return cls(value.n, value.d, budget=budget)
        if isinstance(value, dict) and set(value) == {'numerator', 'denominator'}:
            return cls(value['numerator'], value['denominator'], budget=budget)
        if isinstance(value, (list, tuple)):
            return cls(value, budget=budget)
        return cls((_q(value),), budget=budget)

    def coerce(self, value):
        return value if isinstance(value, RationalFunction) else self.parse(value, self.budget)

    def __bool__(self): return not P.is_zero(self.n)
    def __eq__(self, value):
        if getattr(value, '_accepts_scalar', lambda _: False)(self):return NotImplemented
        other = self.coerce(value)
        return self.n == other.n and self.d == other.d
    def __neg__(self): return RationalFunction(P.scale(self.n, -1), self.d, budget=self.budget)
    def __add__(self, value):
        if getattr(value, '_accepts_scalar', lambda _: False)(self):return NotImplemented
        b = self.coerce(value); g = P.gcd_poly(self.d, b.d)
        a1, b1 = P.exact_div(self.d, g), P.exact_div(b.d, g)
        return RationalFunction(P.add(mul(self.n, b1), mul(b.n, a1)), mul(self.d, b1), budget=self.budget or b.budget)
    __radd__ = __add__
    def __sub__(self, value):
        if getattr(value, '_accepts_scalar', lambda _: False)(self):return NotImplemented
        return self + -self.coerce(value)
    def __rsub__(self, value): return self.coerce(value) + -self
    def __mul__(self, value):
        if getattr(value, '_accepts_scalar', lambda _: False)(self):return NotImplemented
        b = self.coerce(value)
        g, h = P.gcd_poly(self.n, b.d), P.gcd_poly(b.n, self.d)
        return RationalFunction(mul(P.exact_div(self.n, g), P.exact_div(b.n, h)),
            mul(P.exact_div(self.d, h), P.exact_div(b.d, g)), budget=self.budget or b.budget)
    __rmul__ = __mul__
    def __truediv__(self, value):
        if getattr(value, '_accepts_scalar', lambda _: False)(self):return NotImplemented
        b = self.coerce(value)
        if not b: raise ZeroDivisionError('zero rational function')
        return self * RationalFunction(b.d, b.n, budget=self.budget or b.budget)
    def __rtruediv__(self, value): return self.coerce(value) / self
    def derivative(self):
        return RationalFunction(P.add(mul(P.derivative(self.n), self.d), P.scale(mul(self.n, P.derivative(self.d)), -1)),
            mul(self.d, self.d), budget=self.budget)
    def evaluate(self, value):
        d = P.evaluate(self.d, value)
        if not d: raise ValueError('rational-function pole')
        return P.evaluate(self.n, value) / d
    def packet(self): return dict(numerator=list(map(str, self.n)), denominator=list(map(str, self.d)))


def solve_many(matrix, rhs, *, determinant=False):
    """RREF over Q(t), simultaneous RHS; None for inconsistency."""
    rows, columns, targets = len(matrix), len(matrix[0]), len(rhs[0])
    if len(rhs) != rows or any(len(r) != columns for r in matrix) or any(len(r) != targets for r in rhs):
        raise ValueError('matching rectangular field systems required')
    a = [list(r) + list(v) for r, v in zip(matrix, rhs)]
    one = matrix[0][0].coerce(1); det = one; pivots = []
    for c in range(columns):
        k = len(pivots); pivot = next((i for i in range(k, rows) if a[i][c]), None)
        if pivot is None: continue
        if pivot != k: a[k], a[pivot] = a[pivot], a[k]; det = -det
        factor = a[k][c]; det = det * factor; a[k] = [v / factor for v in a[k]]
        for i in range(rows):
            if i != k and a[i][c]:
                factor = a[i][c]; a[i] = [v - factor*w for v, w in zip(a[i], a[k])]
        pivots.append(c)
    if determinant:
        if rows != columns: raise ValueError('square determinant required')
        return det if len(pivots) == rows else one.coerce(0)
    if any(not any(r[:columns]) and any(r[columns:]) for r in a): return None
    solution = [[one.coerce(0) for _ in range(targets)] for _ in range(columns)]
    for i, c in enumerate(pivots): solution[c] = a[i][columns:]
    return solution


def determinant(matrix):
    return solve_many(matrix, [[] for _ in matrix], determinant=True)
