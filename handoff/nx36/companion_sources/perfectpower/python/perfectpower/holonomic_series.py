"""Theta/Weyl operators to exact coefficient recurrences, with singular seeds.

This is a formal-series compiler. A supplied differential equation is a
definition/premise, not a discovery of an external analytic function.
"""
from copy import deepcopy
from fractions import Fraction as Q
from .observable_machine import _q
from . import polyalg as P
from .core import mul
from .divisor_square import WorkLimit
from .exact_operators import Weyl


def weyl_theta_bridge(operator):
    """Multiply on the left by z^h, then rewrite z^i D^j in z,theta.

    D^j = z^-j theta(theta-1)...(theta-j+1). Multiplication by
    z^h is injective on formal series, so it does not change the kernel.
    """
    if not isinstance(operator, Weyl) or not operator.terms or len(operator.terms) > 256:
        raise ValueError('nonzero bounded Weyl operator required')
    if any(max(i, j) > 32 for i, j in operator.terms):
        raise WorkLimit('Weyl degree budget exceeded')
    h = max(0, max(j-i for i, j in operator.terms))
    rows = [P.ZERO]*(max(i+h-j for i, j in operator.terms)+1)
    for (i, j), c in operator.terms.items():
        falling = P.ONE
        for k in range(j):
            falling = mul(falling, (Q(-k), Q(1)))
        rows[i+h-j] = P.add(rows[i+h-j], P.scale(falling, c))
    return {'schema': 'pp-weyl-theta/1', 'weyl': operator.receipt(),
            'left_power': h, 'theta': [list(map(str, row)) for row in rows],
            'scope': 'same formal-series kernel; theta=zD, polynomial normal-ordering identity',
            'execution_verified': False}


class ThetaSeries:
    def __init__(self, specification):
        if not isinstance(specification, dict) or set(specification)-{'theta', 'initial', 'forcing'} or not {'theta', 'initial'} <= set(specification):
            raise ValueError('theta operator rows and supplied initial coefficients required')
        rows, initial = specification['theta'], specification['initial']
        if not isinstance(rows, (list, tuple)) or not 1 <= len(rows) <= 65 or any(not isinstance(row, (list, tuple)) or not 1 <= len(row) <= 33 for row in rows):
            raise ValueError('bounded theta polynomial rows required')
        if not isinstance(initial, (list, tuple)) or len(initial) > 4096:
            raise ValueError('at most 4096 initial coefficients required')
        self.theta = tuple(P.poly(map(_q, row)) for row in rows)
        if P.is_zero(self.theta[0]):
            raise ValueError('nonzero coefficient of z^0 required; remove a common z factor first')
        forcing = specification.get('forcing', [0])
        if not isinstance(forcing, (list, tuple)) or not 1 <= len(forcing) <= 257:
            raise ValueError('bounded polynomial forcing required')
        self.forcing = P.poly(map(_q, forcing))
        if any(max(abs(c.numerator).bit_length(), c.denominator.bit_length()) > 8192
               for row in self.theta+(self.forcing,) for c in row):
            raise WorkLimit('operator coefficient bit budget exceeded')
        self.singular_indices = P.integer_roots(self.theta[0], 0)
        if self.singular_indices and max(self.singular_indices) >= 4096:
            raise WorkLimit('singular coefficient index exceeds seed budget')
        if any(n >= len(initial) for n in self.singular_indices):
            raise ValueError('supply an initial coefficient at every nonnegative singular index')
        self.specification = deepcopy(specification)
        self.values = []
        for n, supplied in enumerate(initial):
            value = _q(supplied)
            expected, leading = self._equation(n)
            if leading*value != expected:
                raise ValueError('initial coefficient violates the differential equation at index '+str(n))
            self._check(value); self.values.append(value)

    @classmethod
    def from_weyl(cls, operator, initial, forcing=None):
        bridge = weyl_theta_bridge(operator)
        forcing = [0] if forcing is None else forcing
        return cls({'theta': bridge['theta'], 'initial': initial,
                    'forcing': [0]*bridge['left_power']+list(forcing)})

    @staticmethod
    def _check(value):
        if max(abs(value.numerator).bit_length(), value.denominator.bit_length()) > 8192:
            raise WorkLimit('holonomic coefficient bit budget exceeded')

    def _equation(self, n):
        rhs = self.forcing[n] if n < len(self.forcing) else Q(0)
        for j in range(1, min(n+1, len(self.theta))):
            rhs -= P.evaluate(self.theta[j], n-j)*self.values[n-j]
        return rhs, P.evaluate(self.theta[0], n)

    def coefficient(self, index):
        if type(index) is not int or not 0 <= index <= 4095:
            raise ValueError('holonomic sequential index 0 through 4095 required')
        while len(self.values) <= index:
            n = len(self.values); rhs, leading = self._equation(n)
            if not leading:
                raise ValueError('missing singular seed coefficient')
            value = rhs/leading; self._check(value); self.values.append(value)
        return self.values[index]

    def terms(self, start=0, size=12):
        if type(start) is not int or start < 0 or type(size) is not int or not 0 <= size <= 1024 or start+size > 4096:
            raise ValueError('bounded holonomic term window required')
        return [self.coefficient(n) for n in range(start, start+size)]

    def summary(self):
        return {'schema': 'pp-theta-series/1', 'theta': [list(map(str, row)) for row in self.theta],
                'forcing': list(map(str, self.forcing)), 'singular_indices': self.singular_indices,
                'initial': list(map(str, map(_q, self.specification['initial']))),
                'scope': 'unique formal series satisfying the supplied operator and singular seed values',
                'execution_verified': False}

    def evidence(self):
        return dict(self.summary(), coefficient_equation='sum_j q_j(n-j)*a[n-j]=forcing[n], omitting j>n',
                    analytic_convergence_proved=False, external_sequence_definition_proved=False)


def differential_theta_bridge(coefficients):
    """Clear Q(z) denominators of sum_i c_i(z) D^i, then normal-order."""
    from .rational_functions import RationalFunction as RF, AlgebraBudget
    if not isinstance(coefficients, (list, tuple)) or not 1 <= len(coefficients) <= 17:
        raise ValueError('bounded list of constant-first differential coefficients required')
    budget = AlgebraBudget(degree_limit=128)
    coeffs = [RF.parse(c, budget) for c in coefficients]
    denominator = P.ONE
    for c in coeffs:
        denominator = mul(denominator, P.exact_div(c.d, P.gcd_poly(denominator, c.d)))
        budget.check(denominator)
    terms = {}
    for i, c in enumerate(coeffs):
        cleared = mul(c.n, P.exact_div(denominator, c.d))
        for j, v in enumerate(cleared):
            if v:
                terms[j, i] = v
    bridge = weyl_theta_bridge(Weyl(terms))
    bridge['cleared_denominator'] = list(map(str, denominator))
    bridge['scope'] = 'formal kernel identity after exact denominator clearing; analytic domains at poles need separate treatment'
    return bridge
