"""Sparse multivariate polynomials with rational coefficients and exact replay."""
from fractions import Fraction as Q
from math import factorial


class Poly:
    def __init__(self, terms=None, variables=2):
        self.variables = variables
        self.terms = {tuple(k): Q(v) for k, v in (terms or {}).items() if v}
        if any(len(k) != variables or any(e < 0 or not isinstance(e, int) for e in k)
               for k in self.terms):
            raise ValueError("invalid polynomial exponents")

    @classmethod
    def constant(cls, value, variables=2):
        return cls({(0,)*variables: value}, variables)

    @classmethod
    def variable(cls, index, variables=2):
        if not 0 <= index < variables:
            raise ValueError("variable index out of range")
        e = [0]*variables
        e[index] = 1
        return cls({tuple(e): 1}, variables)

    def _coerce(self, other):
        if not isinstance(other, Poly):
            return Poly.constant(other, self.variables)
        if other.variables != self.variables:
            raise ValueError("polynomial variable counts differ")
        return other

    def __add__(self, other):
        other = self._coerce(other)
        d = self.terms.copy()
        for e, c in other.terms.items():
            d[e] = d.get(e, Q(0)) + c
        return Poly(d, self.variables)

    __radd__ = __add__

    def __neg__(self):
        return Poly({e: -c for e, c in self.terms.items()}, self.variables)

    def __sub__(self, other):
        return self + -self._coerce(other)

    def __rsub__(self, other):
        return self._coerce(other) - self

    def __mul__(self, other):
        other = self._coerce(other)
        d = {}
        for a, c in self.terms.items():
            for b, v in other.terms.items():
                e = tuple(x+y for x, y in zip(a, b))
                d[e] = d.get(e, Q(0)) + c*v
        return Poly(d, self.variables)

    __rmul__ = __mul__

    def __pow__(self, n):
        if not isinstance(n, int) or n < 0:
            raise ValueError("nonnegative integer exponent required")
        out, base = Poly.constant(1, self.variables), self
        while n:
            if n & 1:
                out = out*base
            base = base*base
            n //= 2
        return out

    def __eq__(self, other):
        return self.terms == self._coerce(other).terms

    def derivative(self, orders):
        if len(orders) != self.variables or any(i < 0 for i in orders):
            raise ValueError("invalid derivative orders")
        d = {}
        for e, c in self.terms.items():
            if all(a >= k for a, k in zip(e, orders)):
                factor = 1
                for a, k in zip(e, orders):
                    factor *= factorial(a)//factorial(a-k)
                d[tuple(a-k for a, k in zip(e, orders))] = c*factor
        return Poly(d, self.variables)

    def compose(self, substitutions):
        if len(substitutions) != self.variables or not substitutions:
            raise ValueError("one substitution per variable required")
        nv = substitutions[0].variables
        out = Poly.constant(0, nv)
        for e, c in self.terms.items():
            term = Poly.constant(c, nv)
            for p, k in zip(substitutions, e):
                term = term*(p**k)
            out = out + term
        return out

    def evaluate(self, values):
        if len(values) != self.variables:
            raise ValueError("wrong number of coordinates")
        return sum((c * product(Q(v)**k for v, k in zip(values, e))
                    for e, c in self.terms.items()), Q(0))

    def record(self):
        return [{"exponents": list(e), "coefficient": str(c)}
                for e, c in sorted(self.terms.items())]


def product(values):
    out = 1
    for v in values:
        out *= v
    return out


def feature_closure(features, evolution):
    """Find exact pullback coefficients or return a missing coefficient witness."""
    from .exact import rref
    pulls = [p.compose(evolution) for p in features]
    monomials = sorted(set().union(*(p.terms.keys() for p in features + pulls)))
    rows = [[p.terms.get(m, Q(0)) for p in features] for m in monomials]
    result = []
    for pull in pulls:
        augmented = [row + [pull.terms.get(m, Q(0))] for row, m in zip(rows, monomials)]
        rr, piv = rref(augmented, len(features)+1)
        if len(features) in piv:
            return {"closed": False, "pullback": pull.record(),
                    "reason": "pullback is outside the supplied rational feature span"}
        coeff = [Q(0)]*len(features)
        for i, p in enumerate(piv):
            coeff[p] = rr[i][-1]
        replay = sum((a*p for a, p in zip(coeff, features)), Poly.constant(0, pull.variables))
        if replay != pull:
            raise ArithmeticError("feature replay failed")
        result.append(coeff)
    return {"closed": True, "transition": result}
