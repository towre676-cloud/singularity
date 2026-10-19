"""Exact periodic Dirichlet series, Mellin kernels, and finite characters.

``PeriodicDirichlet((c1,...,cN))`` represents sum c_n/n**s, with the
coefficients extended periodically from indices 1 through N.  Exact rational
arithmetic is used throughout.  Cyclotomic coefficients reuse the repository's
QuotientAlgebra and cyclotomic polynomial implementation.  Binary64 values are
available only through the explicitly numerical ``approximate`` method.

Matching parity at positive integer weights gives an algebraic multiple of
pi**weight.  Opposite parity remains a formal special value; in particular the
module never reduces Catalan's constant to an invented rational multiple of pi.
These are exact Python calculations and mathematical identities, not Lean proofs.
"""

from dataclasses import dataclass
from fractions import Fraction as Q
from functools import lru_cache
from math import factorial, gcd, lcm

from .cyclotomic_periods import bernoulli_polynomial, prime_divisors
from .period_transport import _cyclotomic
from .quotient_algebra import QuotientAlgebra


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(name + ' must be an integer >= ' + str(minimum))
    return value


def _rational(value):
    if type(value) not in (int, Q, str):
        raise ValueError('exact integer, Fraction, or rational string required')
    return Q(value)


@lru_cache(maxsize=256)
def _field(order):
    return QuotientAlgebra(_cyclotomic(order))


@lru_cache(maxsize=32768)
def _root_coefficients(order, exponent):
    return _field(order).element((0,) * exponent + (1,)).coefficients


@dataclass(frozen=True, eq=False)
class CyclotomicNumber:
    """A specified complex embedding of Q[zeta_order], reduced exactly.

    A conductor records an ambient field, not a claim of minimal conductor.
    Arithmetic between different fields uses their least common multiple.
    """

    order: int
    coefficients: tuple

    def __post_init__(self):
        _integer(self.order, 'cyclotomic order', 1)
        values = self.coefficients
        if isinstance(values, (int, Q, str)):
            values = (_rational(values),)
        else:
            values = tuple(_rational(x) for x in values)
        object.__setattr__(self, 'coefficients', _field(self.order).element(values).coefficients)

    @classmethod
    def root(cls, order, exponent=1):
        _integer(order, 'cyclotomic order', 1)
        if type(exponent) is not int:
            raise ValueError('root exponent must be an integer')
        exponent %= order
        return cls(order, _root_coefficients(order, exponent))

    def lift(self, order):
        _integer(order, 'target cyclotomic order', 1)
        if order % self.order:
            raise ValueError('target order must be a multiple of source order')
        if order == self.order:
            return self
        step = order // self.order
        values = [Q(0)] * ((len(self.coefficients) - 1) * step + 1)
        for j, value in enumerate(self.coefficients):
            values[j * step] = value
        return CyclotomicNumber(order, tuple(values))

    def _pair(self, other):
        if not isinstance(other, CyclotomicNumber):
            other = CyclotomicNumber(self.order, _rational(other))
        order = lcm(self.order, other.order)
        return self.lift(order), other.lift(order)

    def __add__(self, other):
        a, b = self._pair(other)
        value = _field(a.order).element(a.coefficients) + _field(a.order).element(b.coefficients)
        return CyclotomicNumber(a.order, value.coefficients)

    __radd__ = __add__

    def __neg__(self):
        return CyclotomicNumber(self.order, tuple(-x for x in self.coefficients))

    def __sub__(self, other):
        return self + -self._pair(other)[1]

    def __rsub__(self, other):
        return -self + other

    def __mul__(self, other):
        a, b = self._pair(other)
        value = _field(a.order).element(a.coefficients) * _field(a.order).element(b.coefficients)
        return CyclotomicNumber(a.order, value.coefficients)

    __rmul__ = __mul__

    def __pow__(self, exponent):
        if type(exponent) is not int:
            raise ValueError('an integer exponent is required')
        value = _field(self.order).element(self.coefficients) ** exponent
        return CyclotomicNumber(self.order, value.coefficients)

    def __truediv__(self, other):
        a, b = self._pair(other)
        return a * (b ** -1)

    def conjugate(self):
        return sum((value * CyclotomicNumber.root(self.order, -j)
                    for j, value in enumerate(self.coefficients)), CyclotomicNumber(self.order, 0))

    def __eq__(self, other):
        try:
            a, b = self._pair(other)
        except (ValueError, TypeError):
            return False
        return a.coefficients == b.coefficients

    # Equality can compare elements represented in different ambient fields.
    __hash__ = None

    @property
    def is_zero(self):
        return not any(self.coefficients)

    @property
    def is_rational(self):
        return len(self.coefficients) == 1

    def as_rational(self):
        if not self.is_rational:
            raise ValueError('this element is not rational in the power basis')
        return self.coefficients[0]

    def approximate(self):
        """Binary64 evaluation, deliberately separate from exact arithmetic."""
        import cmath
        z = cmath.exp(2j * cmath.pi / self.order)
        return sum(float(c) * z ** j for j, c in enumerate(self.coefficients))

    def packet(self):
        return {'order': self.order, 'embedding': 'zeta=exp(2*pi*i/order)',
                'modulus_low_to_high': list(map(str, _field(self.order).modulus)),
                'coefficients_low_to_high': list(map(str, self.coefficients))}


def _dft(values, period, coefficient_order=1):
    order = lcm(period, coefficient_order)
    lifted = tuple(v.lift(order) if isinstance(v, CyclotomicNumber)
                   else CyclotomicNumber(order, v) for v in values)
    return _cached_dft(order, period, tuple(v.coefficients for v in lifted))


@lru_cache(maxsize=256)
def _cached_dft(order, period, coefficients):
    lifted = tuple(CyclotomicNumber(order, values) for values in coefficients)
    # values[0] is c_1, hence Fourier phase a=j+1.
    return tuple(sum((v * CyclotomicNumber.root(order, -(j + 1) * h * (order // period))
                      for j, v in enumerate(lifted)), CyclotomicNumber(order, 0)) / period
                 for h in range(period))


def _parity_pi_coefficient(values, weight, coefficient_order=1):
    _integer(weight, 'integer weight', 1)
    period = len(values)
    sign = (-1) ** weight
    if any(values[(-a - 1) % period] != sign * values[a - 1] for a in range(1, period + 1)):
        raise ValueError('coefficient parity does not match the weight; retain the formal period')
    order = lcm(period, coefficient_order, 4)
    dft = _dft(values, period, coefficient_order)
    total = sum((v.lift(order) * bernoulli_polynomial(weight, Q(h, period))
                 for h, v in enumerate(dft)), CyclotomicNumber(order, 0))
    i = CyclotomicNumber.root(order, order // 4)
    return -(i ** weight) * Q(2 ** (weight - 1), factorial(weight)) * total


@dataclass(frozen=True)
class PeriodicDirichlet:
    """Rational c_1,...,c_N for a periodic Dirichlet/Mellin family."""

    coefficients: tuple

    def __post_init__(self):
        values = tuple(_rational(x) for x in self.coefficients)
        if not values:
            raise ValueError('at least one coefficient is required')
        object.__setattr__(self, 'coefficients', values)

    @classmethod
    def residue_pair(cls, period, residue, parity=-1):
        _integer(period, 'period', 1)
        if type(residue) is not int or parity not in (-1, 1):
            raise ValueError('an integer residue and parity +/-1 are required')
        values = [Q(0)] * period
        values[(residue - 1) % period] += 1
        values[(-residue - 1) % period] += parity
        return cls(tuple(values))

    @property
    def period(self):
        return len(self.coefficients)

    @property
    def minimal_period(self):
        return next(d for d in range(1, self.period + 1) if self.period % d == 0
                    and all(v == self.coefficients[j % d] for j, v in enumerate(self.coefficients)))

    @property
    def mean(self):
        return sum(self.coefficients, Q(0)) / self.period

    @property
    def mean_zero(self):
        return not self.mean

    def coefficient(self, n):
        if type(n) is not int:
            raise ValueError('an integer coefficient index is required')
        return self.coefficients[(n - 1) % self.period]

    def domain(self):
        return {'ordinary_series_and_mellin': 'Re(s)>0' if self.mean_zero else 'Re(s)>1',
                'absolute_series': 'all s' if not any(self.coefficients) else 'Re(s)>1',
                'mean_zero': self.mean_zero, 'pole_at_one_residue': str(self.mean),
                'continuation': 'entire' if self.mean_zero else 'meromorphic, at most a simple pole at s=1'}

    def kernel(self, x):
        """Exact K(x)=sum c_a*x**(a-1)/(1-x**N), 0<=x<1.

        At x=1 the removable limit is returned only for a mean-zero table.
        The Gamma-normalized Mellin integral uses (-log x)**(s-1) K(x) dx.
        """
        x = _rational(x)
        if not 0 <= x <= 1:
            raise ValueError('the real Mellin kernel requires 0<=x<=1')
        if x == 1:
            if not self.mean_zero:
                raise ValueError('the kernel has a pole at x=1')
            return -sum((j * c for j, c in enumerate(self.coefficients)), Q(0)) / self.period
        return sum((c * x ** j for j, c in enumerate(self.coefficients)), Q(0)) / (1 - x ** self.period)

    mellin_kernel = kernel

    def kernel_receipt(self):
        return {'numerator_low_to_high': list(map(str, self.coefficients)),
                'denominator_low_to_high': ['1'] + ['0'] * (self.period - 1) + ['-1'],
                'normalization': 'D(s)=integral_0^1 (-log x)^(s-1) K(x) dx/Gamma(s)',
                'domain': self.domain(),
                'endpoint_one_limit': str(self.kernel(1)) if self.mean_zero else None}

    def hurwitz_reduction(self):
        return {'factor': f'{self.period}^(-s)',
                'terms': [{'coefficient': str(c), 'a': str(Q(a, self.period))}
                          for a, c in enumerate(self.coefficients, 1) if c],
                'identity': 'D(s)=N^(-s)*sum_a c_a*zeta(s,a/N)',
                'domain': self.domain()}

    def lerch_reduction(self):
        return {'identity': 'sum_n c_n*z^n/n^s=N^(-s)*sum_a c_a*z^a*Phi(z^N,s,a/N)',
                'terms': [{'coefficient': str(c), 'z_power': a, 'a': str(Q(a, self.period))}
                          for a, c in enumerate(self.coefficients, 1) if c],
                'initial_domain': '|z|<1, all s; at z=1 use the ordinary convergence domain'}

    def dft(self):
        """b_h=N^-1 sum_a c_a exp(-2*pi*i*h*a/N), h=0,...,N-1."""
        return _dft(self.coefficients, self.period)

    def inverse_dft(self):
        values = self.dft()
        return tuple(sum((v * CyclotomicNumber.root(self.period, h * a)
                          for h, v in enumerate(values)), CyclotomicNumber(self.period, 0))
                     for a in range(1, self.period + 1))

    def polylog_reduction(self):
        return {'identity': 'D(s)=sum_h b_h*Li_s(exp(2*pi*i*h/N))',
                'common_domain': 'Re(s)>1',
                'terms': [{'phase_turns': str(Q(h, self.period)), 'coefficient': value.packet()}
                          for h, value in enumerate(self.dft()) if not value.is_zero]}

    def partial_sum(self, weight, terms):
        _integer(weight, 'integer weight', 1)
        _integer(terms, 'number of terms')
        return sum((self.coefficient(n) / n ** weight for n in range(1, terms + 1)), Q(0))

    def tail_bound(self, weight, terms):
        """Rigorous absolute remainder bound for the ordinary real series.

        In the mean-zero case summation by parts uses the maximum absolute
        partial sum over one complete period beginning after the cutoff.
        This handles weight one without pretending the series is absolute.
        """
        _integer(weight, 'integer weight', 1)
        _integer(terms, 'number of terms')
        bounds = []
        if self.mean_zero:
            running, bound = Q(0), Q(0)
            for j in range(1, self.period + 1):
                running += self.coefficient(terms + j)
                bound = max(bound, abs(running))
            bounds.append(bound / (terms + 1) ** weight)
        if weight > 1:
            amplitude = max(map(abs, self.coefficients))
            bounds.append(amplitude * (Q(1, (terms + 1) ** weight)
                          + Q(1, (weight - 1) * (terms + 1) ** (weight - 1))))
        if not bounds:
            raise ValueError('weight one requires a mean-zero table')
        return min(bounds)

    def enclosure(self, weight, terms):
        partial, tail = self.partial_sum(weight, terms), self.tail_bound(weight, terms)
        return partial - tail, partial + tail

    def pi_coefficient(self, weight):
        """Exact algebraic c in D(weight)=c*pi**weight when parities match."""
        return _parity_pi_coefficient(self.coefficients, weight)

    def special_value(self, weight):
        _integer(weight, 'integer weight', 1)
        try:
            coefficient = self.pi_coefficient(weight)
        except ValueError:
            return {'status': 'formal', 'weight': weight,
                    'reason': 'opposite parity: no algebraic pi reduction is claimed',
                    'periodic_coefficients': list(map(str, self.coefficients))}
        return {'status': 'exact_algebraic_pi_power', 'weight': weight,
                'pi_coefficient': coefficient.packet(), 'verified_by': 'exact Python arithmetic, not Lean'}


@dataclass(frozen=True)
class DirichletCharacter:
    """Full root-of-unity character table indexed 0,...,q-1.

    ``None`` means zero, and an integer e means exp(2*pi*i*e/order).
    Constructor checks support, identity, and every multiplicativity pair.
    Redundant common roots of unity are removed from ``order``.
    """

    modulus: int
    order: int
    exponents: tuple

    def __post_init__(self):
        q = _integer(self.modulus, 'character modulus', 1)
        order = _integer(self.order, 'root-of-unity order', 1)
        if len(self.exponents) != q:
            raise ValueError('a full table indexed 0 through modulus-1 is required')
        table = []
        for a, value in enumerate(self.exponents):
            if gcd(a, q) != 1:
                if value is not None:
                    raise ValueError('nonunits must have character value zero (None)')
                table.append(None)
            else:
                if type(value) is not int:
                    raise ValueError('units require integer root-of-unity exponents')
                table.append(value % order)
        if table[1 % q] != 0:
            raise ValueError('the identity must have character value one')
        units = tuple(a for a in range(q) if gcd(a, q) == 1)
        if any((table[a] + table[b] - table[a * b % q]) % order for a in units for b in units):
            raise ValueError('the supplied table is not multiplicative')
        common = order
        for value in table:
            if value is not None:
                common = gcd(common, value)
        object.__setattr__(self, 'order', order // common)
        object.__setattr__(self, 'exponents', tuple(None if x is None else x // common for x in table))

    @classmethod
    def principal(cls, modulus):
        _integer(modulus, 'character modulus', 1)
        return cls(modulus, 1, tuple(0 if gcd(a, modulus) == 1 else None for a in range(modulus)))

    @classmethod
    def beta(cls):
        return cls(4, 2, (None, 0, None, 1))

    @property
    def is_principal(self):
        return all(x in (0, None) for x in self.exponents)

    @property
    def parity(self):
        exponent = self.exponents[-1]
        if exponent == 0:
            return 1
        if 2 * exponent == self.order:
            return -1
        raise ArithmeticError('a valid character must take +/-1 at -1')

    def value(self, n):
        if type(n) is not int:
            raise ValueError('an integer character argument is required')
        exponent = self.exponents[n % self.modulus]
        return CyclotomicNumber(self.order, 0) if exponent is None else CyclotomicNumber.root(self.order, exponent)

    def conjugate(self):
        return DirichletCharacter(self.modulus, self.order,
                                  tuple(None if e is None else -e for e in self.exponents))

    @property
    def conductor(self):
        q = self.modulus
        units = tuple(a for a in range(q) if gcd(a, q) == 1)
        for d in range(1, q + 1):
            if q % d:
                continue
            seen = {}
            for a in units:
                key = a % d
                if key in seen and seen[key] != self.exponents[a]:
                    break
                seen[key] = self.exponents[a]
            else:
                return d
        raise ArithmeticError('the original modulus always supplies a conductor candidate')

    @property
    def is_primitive(self):
        return self.conductor == self.modulus

    def primitive_character(self):
        d = self.conductor
        table = [None] * d
        for a, exponent in enumerate(self.exponents):
            if exponent is not None:
                table[a % d] = exponent
        return DirichletCharacter(d, self.order, tuple(table))

    def induce(self, modulus):
        _integer(modulus, 'induced modulus', 1)
        if modulus % self.modulus:
            raise ValueError('induced modulus must be a multiple of the source modulus')
        return DirichletCharacter(modulus, self.order,
                                  tuple(self.exponents[a % self.modulus] if gcd(a, modulus) == 1 else None
                                        for a in range(modulus)))

    def rational_period(self):
        values = tuple(self.value(a) for a in range(1, self.modulus + 1))
        if any(not v.is_rational for v in values):
            raise ValueError('this character has nonrational values; use its exact DFT')
        return PeriodicDirichlet(tuple(v.as_rational() for v in values))

    def domain(self):
        return {'ordinary_series_and_mellin': 'Re(s)>1' if self.is_principal else 'Re(s)>0',
                'absolute_series': 'Re(s)>1',
                'continuation': 'meromorphic, simple pole at s=1' if self.is_principal else 'entire',
                'mean_zero': not self.is_principal}

    def kernel(self, x):
        x = _rational(x)
        if not 0 <= x <= 1:
            raise ValueError('the real Mellin parameter requires 0<=x<=1')
        if x == 1:
            if self.is_principal:
                raise ValueError('the principal-character Mellin kernel has a pole at x=1')
            return -sum(((a - 1) * self.value(a) for a in range(1, self.modulus + 1)),
                        CyclotomicNumber(self.order, 0)) / self.modulus
        return sum((self.value(a) * x ** (a - 1) for a in range(1, self.modulus + 1)),
                   CyclotomicNumber(self.order, 0)) / (1 - x ** self.modulus)

    mellin_kernel = kernel

    def hurwitz_reduction(self):
        return {'factor': f'{self.modulus}^(-s)',
                'terms': [{'coefficient': self.value(a).packet(), 'a': str(Q(a, self.modulus))}
                          for a in range(1, self.modulus + 1) if not self.value(a).is_zero],
                'identity': 'L(s,chi)=q^(-s)*sum_a chi(a)*zeta(s,a/q)', 'domain': self.domain()}

    def partial_sum(self, weight, terms):
        _integer(weight, 'integer weight', 1)
        _integer(terms, 'number of terms')
        return sum((self.value(n) / n ** weight for n in range(1, terms + 1)),
                   CyclotomicNumber(self.order, 0))

    def tail_bound(self, weight, terms):
        """A rational radius for the complex remainder, also at weight one.

        Nonprincipal character sums vanish over a period.  Prefix magnitudes
        are bounded by both the number of unit values already encountered and
        the number still remaining.  This triangle bound avoids approximating
        a square root or asserting order on a complex cyclotomic field.
        """
        _integer(weight, 'integer weight', 1)
        _integer(terms, 'number of terms')
        bounds = []
        if not self.is_principal:
            units = sum(e is not None for e in self.exponents)
            seen, bound = 0, 0
            for j in range(1, self.modulus + 1):
                seen += self.exponents[(terms + j) % self.modulus] is not None
                bound = max(bound, min(seen, units - seen))
            bounds.append(Q(bound, (terms + 1) ** weight))
        if weight > 1:
            bounds.append(Q(1, (terms + 1) ** weight)
                          + Q(1, (weight - 1) * (terms + 1) ** (weight - 1)))
        if not bounds:
            raise ValueError('weight one requires a nonprincipal character')
        return min(bounds)

    def bounded_partial(self, weight, terms):
        return {'center': self.partial_sum(weight, terms).packet(),
                'absolute_error_radius': str(self.tail_bound(weight, terms)),
                'weight': weight, 'terms': terms,
                'meaning': 'closed complex disk containing the ordinary Dirichlet-series value'}

    def dft(self):
        return _dft(tuple(self.value(a) for a in range(1, self.modulus + 1)), self.modulus, self.order)

    def gauss_sum(self, multiplier=1):
        if type(multiplier) is not int:
            raise ValueError('an integer Gauss multiplier is required')
        order = lcm(self.modulus, self.order)
        return sum((self.value(a).lift(order)
                    * CyclotomicNumber.root(order, multiplier * a * (order // self.modulus))
                    for a in range(self.modulus)), CyclotomicNumber(order, 0))

    def gauss_relation(self, multiplier=1):
        actual = self.gauss_sum(multiplier)
        applicable = self.is_primitive or gcd(multiplier, self.modulus) == 1
        expected = self.value(multiplier).conjugate() * self.gauss_sum() if applicable else None
        return {'multiplier': multiplier, 'primitive': self.is_primitive,
                'applicable': applicable, 'actual': actual.packet(),
                'expected': expected.packet() if expected is not None else None,
                'exact_equality': actual == expected if applicable else None,
                'scope': 'all multipliers for primitive characters; unit multipliers for every character'}

    def generalized_bernoulli(self, n):
        _integer(n, 'Bernoulli degree', 1)
        return self.modulus ** (n - 1) * sum(
            (self.value(a) * bernoulli_polynomial(n, Q(a, self.modulus))
             for a in range(1, self.modulus + 1)), CyclotomicNumber(self.order, 0))

    def negative_integer_value(self, nonnegative):
        """Analytically continued L(-m,chi), not an ordinary divergent sum."""
        _integer(nonnegative, 'nonnegative negative-weight index')
        return -self.generalized_bernoulli(nonnegative + 1) / (nonnegative + 1)

    def pi_coefficient(self, weight):
        return _parity_pi_coefficient(tuple(self.value(a) for a in range(1, self.modulus + 1)),
                                      weight, self.order)

    def gauss_pi_coefficient(self, weight):
        """Independent primitive-character Bernoulli/Gauss formula."""
        _integer(weight, 'integer weight', 1)
        if not self.is_primitive:
            raise ValueError('the primitive Gauss formula requires a primitive character')
        if self.parity != (-1) ** weight:
            raise ValueError('coefficient parity does not match the weight')
        odd = (1 - self.parity) // 2
        order = lcm(self.modulus, self.order, 4)
        i = CyclotomicNumber.root(order, order // 4)
        return (Q((-1) ** (1 + (weight - odd) // 2) * 2 ** (weight - 1),
                  self.modulus ** weight * factorial(weight))
                * self.gauss_sum().lift(order) / (i ** odd)
                * self.conjugate().generalized_bernoulli(weight).lift(order))

    def euler_factors(self, weight):
        _integer(weight, 'integer weight', 1)
        primitive = self.primitive_character()
        return tuple((p, 1 - primitive.value(p) / p ** weight)
                     for p in prime_divisors(self.modulus) if primitive.modulus % p)

    def primitive_euler_pi_coefficient(self, weight):
        result = self.primitive_character().gauss_pi_coefficient(weight)
        for _, factor in self.euler_factors(weight):
            result = result * factor
        return result

    def special_value(self, weight):
        _integer(weight, 'integer weight', 1)
        if self.parity != (-1) ** weight:
            return {'status': 'formal', 'weight': weight, 'character': self.packet(),
                    'reason': 'opposite parity: no algebraic pi reduction is claimed'}
        result = self.pi_coefficient(weight)
        independent = self.primitive_euler_pi_coefficient(weight)
        return {'status': 'exact_algebraic_pi_power', 'weight': weight,
                'pi_coefficient': result.packet(), 'primitive_euler_crosscheck': result == independent,
                'verified_by': 'exact Python arithmetic, not Lean'}

    def packet(self):
        return {'modulus': self.modulus, 'root_order': self.order,
                'root_exponents_indexed_from_zero': list(self.exponents),
                'conductor': self.conductor, 'primitive': self.is_primitive,
                'parity': self.parity, 'principal': self.is_principal}


def all_characters(modulus, max_modulus=128):
    """Enumerate every character by exact finite-group extension, without CAS.

    A finite explicit modulus budget prevents accidental exponential allocation.
    At each step a character on H is extended to <H,g>.  If g^t is first in H,
    the possible exponents x solve t*x=chi(g^t) modulo the group exponent.
    """
    q = _integer(modulus, 'character modulus', 1)
    _integer(max_modulus, 'enumeration modulus budget', 1)
    if q > max_modulus:
        raise ValueError('character enumeration exceeds its explicit modulus budget')
    units = tuple(a for a in range(q) if gcd(a, q) == 1)
    identity = 1 % q
    exponent = 1
    for a in units:
        power, order = a, 1
        while power != identity:
            power, order = power * a % q, order + 1
        exponent = lcm(exponent, order)
    tables = [{identity: 0}]
    subgroup = {identity}
    while len(subgroup) < len(units):
        g = next(a for a in units if a not in subgroup)
        powers = [identity]
        while powers[-1] * g % q not in subgroup:
            powers.append(powers[-1] * g % q)
        t, linked = len(powers), powers[-1] * g % q
        enlarged = []
        for table in tables:
            for x in range(exponent):
                if (t * x - table[linked]) % exponent:
                    continue
                enlarged.append({h * power % q: (value + j * x) % exponent
                                 for h, value in table.items() for j, power in enumerate(powers)})
        tables = enlarged
        subgroup = set(tables[0])
    return tuple(DirichletCharacter(q, exponent, tuple(table.get(a) for a in range(q))) for table in tables)
