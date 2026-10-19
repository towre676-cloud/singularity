"""Exact analytic sufficient statistics recovered from the archived notes.

The circular logarithm integral depends on its representative and radius.  The
arithmetic layer proves finite Dirichlet-coefficient identities, not equality
between ratios of truncated numerical L-series.  No irrational phase twist or
unproved analytic continuation is inferred from a finite computation.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from math import gcd


def _rational(value: Fraction | int | str) -> Fraction:
    if isinstance(value, (float, bool)):
        raise TypeError("use an exact Fraction, integer, or rational string")
    return Fraction(value)


def _point(value: tuple) -> tuple[Fraction, Fraction]:
    if len(value) != 2:
        raise ValueError("points have two rational coordinates")
    return _rational(value[0]), _rational(value[1])


def _positive_integer(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


@dataclass(frozen=True)
class LogDivisor:
    name: str
    point: tuple[Fraction | int | str, Fraction | int | str]
    charge: int

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("divisors need a nonempty name")
        object.__setattr__(self, "point", _point(self.point))
        if isinstance(self.charge, bool) or not isinstance(self.charge, int) or not self.charge:
            raise ValueError("charge must be a nonzero integer")


@dataclass(frozen=True)
class CircularLogPeriod:
    """The branch-tracked integral is coefficient_of_two_pi_i * (2*pi*i)."""

    divisor: str
    charge: int
    center: tuple[Fraction, Fraction]
    radius: Fraction
    orientation: int
    coefficient_of_two_pi_i: Fraction
    other_divisor_clearance_squared: Fraction | None

    def receipt(self) -> dict:
        return {"divisor": self.divisor, "charge": self.charge,
                "center": [str(x) for x in self.center], "radius": str(self.radius),
                "orientation": self.orientation,
                "coefficient_of_two_pi_i": str(self.coefficient_of_two_pi_i),
                "other_divisor_clearance_squared": (None if self.other_divisor_clearance_squared is None
                                                       else str(self.other_divisor_clearance_squared)),
                "isolation_scope": "supplied complete divisor list",
                "representative": "circle based at center + positive real radius",
                "branch": "continuous along the loop; not principal-log resetting"}


def isolated_circle_period(divisors: tuple[LogDivisor, ...] | list[LogDivisor],
                           center: tuple, radius: Fraction | int | str,
                           orientation: int = 1) -> CircularLogPeriod:
    """Integrate a sum of charged logarithms on an isolated circular loop.

    Exactly one supplied divisor must be at the center; every other divisor
    must be strictly outside the closed disk.  The caller must supply the
    complete divisor list and ensure any omitted analytic remainder is
    single-valued and holomorphic in the disk.  Their geometry cannot be
    inferred from a charge list.  CCW is +1 and CW is -1.
    """
    center = _point(center)
    radius = _rational(radius)
    if radius <= 0:
        raise ValueError("radius must be positive")
    if isinstance(orientation, bool) or not isinstance(orientation, int) or orientation not in (-1, 1):
        raise ValueError("orientation must be +1 or -1")
    divisors = tuple(divisors)
    if any(not isinstance(d, LogDivisor) for d in divisors):
        raise TypeError("divisors must be LogDivisor instances")
    if len({d.name for d in divisors}) != len(divisors):
        raise ValueError("divisor names must be distinct")
    centered = [d for d in divisors if d.point == center]
    if len(centered) != 1:
        raise ValueError("exactly one divisor must lie at the circle center")
    distances = []
    for divisor in divisors:
        if divisor is centered[0]:
            continue
        distance_squared = sum(((x - y) ** 2 for x, y in zip(divisor.point, center)), Fraction())
        if distance_squared <= radius ** 2:
            raise ValueError(f"circle fails to isolate {centered[0].name}: {divisor.name} is inside or on it")
        distances.append(distance_squared - radius ** 2)
    target = centered[0]
    return CircularLogPeriod(target.name, target.charge, center, radius, orientation,
                             orientation * target.charge * radius,
                             min(distances) if distances else None)


def divisors(n: int) -> tuple[int, ...]:
    _positive_integer(n, "n")
    small, large = [], []
    candidate = 1
    while candidate * candidate <= n:
        if n % candidate == 0:
            small.append(candidate)
            if candidate * candidate != n:
                large.append(n // candidate)
        candidate += 1
    return tuple(small + large[::-1])


def distinct_prime_factors(n: int) -> tuple[int, ...]:
    _positive_integer(n, "n")
    factors = []
    candidate = 2
    while candidate * candidate <= n:
        if n % candidate == 0:
            factors.append(candidate)
            while n % candidate == 0:
                n //= candidate
        candidate += 1
    if n > 1:
        factors.append(n)
    return tuple(factors)


def totient(n: int) -> int:
    _positive_integer(n, "n")
    result = n
    for prime in distinct_prime_factors(n):
        result = result // prime * (prime - 1)
    return result


def _trim(poly: list) -> list:
    while len(poly) > 1 and poly[-1] == 0:
        poly.pop()
    return poly


def _divide_monic_exact(numerator: list[int], denominator: tuple[int, ...]) -> list[int]:
    remainder = list(numerator)
    quotient = [0] * max(1, len(remainder) - len(denominator) + 1)
    while len(remainder) >= len(denominator) and any(remainder):
        degree = len(remainder) - len(denominator)
        coefficient = remainder[-1]
        quotient[degree] = coefficient
        for index, value in enumerate(denominator):
            remainder[index + degree] -= coefficient * value
        _trim(remainder)
    if any(remainder):
        raise ArithmeticError("nonexact polynomial division")
    return _trim(quotient)


@lru_cache(maxsize=None)
def cyclotomic_polynomial(order: int) -> tuple[int, ...]:
    """Ascending coefficients of Phi_order; computed over the integers."""
    _positive_integer(order, "root order")
    polynomial = [-1] + [0] * (order - 1) + [1]
    for proper in divisors(order)[:-1]:
        polynomial = _divide_monic_exact(polynomial, cyclotomic_polynomial(proper))
    return tuple(polynomial)


@dataclass(frozen=True)
class Cyclotomic:
    """An exact rational element of Q[zeta_order] in a canonical power basis."""

    order: int
    coefficients: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        _positive_integer(self.order, "root order")
        poly = list(map(_rational, self.coefficients)) or [Fraction()]
        modulus = cyclotomic_polynomial(self.order)
        while len(poly) >= len(modulus):
            shift = len(poly) - len(modulus)
            lead = poly[-1]
            for index, value in enumerate(modulus):
                poly[index + shift] -= lead * value
            _trim(poly)
        poly += [Fraction()] * (len(modulus) - 1 - len(poly))
        object.__setattr__(self, "coefficients", tuple(poly))

    @classmethod
    def scalar(cls, order: int, value: Fraction | int | str) -> "Cyclotomic":
        return cls(order, (_rational(value),))

    @classmethod
    def root(cls, order: int, exponent: int) -> "Cyclotomic":
        _positive_integer(order, "root order")
        if isinstance(exponent, bool) or not isinstance(exponent, int):
            raise ValueError("root exponent must be an integer")
        exponent %= order
        return cls(order, (Fraction(),) * exponent + (Fraction(1),))

    def _coerce(self, other) -> "Cyclotomic":
        if isinstance(other, Cyclotomic):
            if self.order != other.order:
                raise ValueError("cyclotomic operands must use the same root order")
            return other
        return self.scalar(self.order, other)

    def __add__(self, other) -> "Cyclotomic":
        other = self._coerce(other)
        return Cyclotomic(self.order, tuple(a + b for a, b in zip(self.coefficients, other.coefficients)))

    __radd__ = __add__

    def __neg__(self) -> "Cyclotomic":
        return Cyclotomic(self.order, tuple(-a for a in self.coefficients))

    def __sub__(self, other) -> "Cyclotomic":
        return self + -self._coerce(other)

    def __mul__(self, other) -> "Cyclotomic":
        other = self._coerce(other)
        product = [Fraction()] * (len(self.coefficients) + len(other.coefficients) - 1)
        for i, a in enumerate(self.coefficients):
            for j, b in enumerate(other.coefficients):
                product[i + j] += a * b
        return Cyclotomic(self.order, tuple(product))

    __rmul__ = __mul__

    def conjugate(self) -> "Cyclotomic":
        return sum((a * Cyclotomic.root(self.order, -j) for j, a in enumerate(self.coefficients)),
                   Cyclotomic.scalar(self.order, 0))

    def is_zero(self) -> bool:
        return not any(self.coefficients)

    def rational(self) -> Fraction:
        if any(self.coefficients[1:]):
            raise ValueError("element is not rational")
        return self.coefficients[0]

    def receipt(self) -> dict:
        return {"root_order": self.order, "power_basis_coefficients": [str(x) for x in self.coefficients]}


@dataclass(frozen=True)
class DirichletCharacter:
    """A validated character table, with exact roots-of-unity values.

    ``exponents[r]`` is the exponent of zeta_root_order for residue r; None
    denotes zero.  Nonunits must have value zero.  Modulus one is supported.
    """

    modulus: int
    exponents: tuple[int | None, ...]
    root_order: int = 2

    def __post_init__(self) -> None:
        _positive_integer(self.modulus, "modulus")
        _positive_integer(self.root_order, "root order")
        if len(self.exponents) != self.modulus:
            raise ValueError("character table length must equal modulus")
        normalized = []
        for residue, exponent in enumerate(self.exponents):
            if gcd(residue, self.modulus) != 1:
                if exponent is not None:
                    raise ValueError("nonunits must have character value zero")
                normalized.append(None)
            else:
                if isinstance(exponent, bool) or not isinstance(exponent, int):
                    raise ValueError("units need integer root exponents")
                normalized.append(exponent % self.root_order)
        object.__setattr__(self, "exponents", tuple(normalized))
        if self.exponents[1 % self.modulus] != 0:
            raise ValueError("character value at the identity must be 1")
        units = [r for r in range(self.modulus) if gcd(r, self.modulus) == 1]
        for a in units:
            for b in units:
                if self.exponents[(a * b) % self.modulus] != (self.exponents[a] + self.exponents[b]) % self.root_order:
                    raise ValueError("table is not a multiplicative Dirichlet character")

    @classmethod
    def principal(cls, modulus: int, root_order: int = 2) -> "DirichletCharacter":
        _positive_integer(modulus, "modulus")
        return cls(modulus, tuple(0 if gcd(r, modulus) == 1 else None for r in range(modulus)), root_order)

    def __call__(self, n: int) -> Cyclotomic:
        if isinstance(n, bool) or not isinstance(n, int):
            raise ValueError("character input must be an integer")
        exponent = self.exponents[n % self.modulus]
        return Cyclotomic.scalar(self.root_order, 0) if exponent is None else Cyclotomic.root(self.root_order, exponent)


def twisted_visible_coefficients(character: DirichletCharacter, limit: int) -> tuple[Cyclotomic, ...]:
    """Coefficients a_n = phi(n)*chi(n), indexed by n-1 for 1 <= n <= limit."""
    _positive_integer(limit, "limit")
    return tuple(totient(n) * character(n) for n in range(1, limit + 1))


def dirichlet_l_ratio_coefficients(character: DirichletCharacter, limit: int) -> tuple[Cyclotomic, ...]:
    """Independently divide L(s-1,chi) by L(s,chi) as Dirichlet series.

    Uses divisor convolution and the denominator's unit coefficient, rather
    than assuming phi(n).  The infinite analytic identity converges absolutely
    for Re(s)>2.  This function only computes exact finite coefficients.
    """
    _positive_integer(limit, "limit")
    quotient = [Cyclotomic.scalar(character.root_order, 0)]
    for n in range(1, limit + 1):
        value = n * character(n)
        for d in divisors(n)[:-1]:
            value -= quotient[d] * character(n // d)
        quotient.append(value)
    return tuple(quotient[1:])


def progression_visible_coefficients(modulus: int, residue: int, limit: int) -> tuple[int, ...]:
    _positive_integer(modulus, "modulus")
    _positive_integer(limit, "limit")
    if isinstance(residue, bool) or not isinstance(residue, int) or gcd(residue, modulus) != 1:
        raise ValueError("residue must be a reduced integer residue class")
    return tuple(totient(n) if n % modulus == residue % modulus else 0 for n in range(1, limit + 1))


def progression_via_characters(characters: tuple[DirichletCharacter, ...] | list[DirichletCharacter],
                               residue: int, limit: int) -> tuple[Cyclotomic, ...]:
    """Apply exact character orthogonality to a reduced progression.

    Requires a complete distinct character table expressed in one common root
    order, and verifies orthogonality at every unit before using it.
    """
    characters = tuple(characters)
    if not characters:
        raise ValueError("supply a complete character table")
    modulus, root_order = characters[0].modulus, characters[0].root_order
    expected = totient(modulus)
    if len(characters) != expected or len(set(characters)) != expected:
        raise ValueError("character table must be complete and distinct")
    if any(c.modulus != modulus or c.root_order != root_order for c in characters):
        raise ValueError("characters must share modulus and root order")
    progression_visible_coefficients(modulus, residue, limit)  # validate
    for unit in range(modulus):
        if gcd(unit, modulus) == 1:
            check = sum((c(unit) for c in characters), Cyclotomic.scalar(root_order, 0))
            target = expected if unit == 1 % modulus else 0
            if check != Cyclotomic.scalar(root_order, target):
                raise ValueError("character table fails orthogonality")
    scale = Fraction(1, expected)
    return tuple(scale * totient(n) * sum((c(residue).conjugate() * c(n) for c in characters),
                                         Cyclotomic.scalar(root_order, 0))
                 for n in range(1, limit + 1))


def progression_residue_factor(modulus: int, residue: int) -> Fraction:
    """Residue at s=2, expressed as this rational factor times 1/zeta(2).

    Factor = (1/phi(M))*product_{p|M} p/(p+1).  It includes both the
    orthogonality factor and principal-character local Euler corrections.
    """
    _positive_integer(modulus, "modulus")
    if isinstance(residue, bool) or not isinstance(residue, int) or gcd(residue, modulus) != 1:
        raise ValueError("residue must be a reduced integer residue class")
    factor = Fraction(1, totient(modulus))
    for prime in distinct_prime_factors(modulus):
        factor *= Fraction(prime, prime + 1)
    return factor


def principal_local_factor(modulus: int, integer_s: int) -> Fraction:
    """Exact product (1-p**(1-s))/(1-p**(-s)), for integer s >= 2."""
    _positive_integer(modulus, "modulus")
    if isinstance(integer_s, bool) or not isinstance(integer_s, int) or integer_s < 2:
        raise ValueError("integer_s must be an integer >= 2")
    factor = Fraction(1)
    for prime in distinct_prime_factors(modulus):
        factor *= (1 - Fraction(1, prime ** (integer_s - 1))) / (1 - Fraction(1, prime ** integer_s))
    return factor


def receipt() -> dict:
    geometry = (LogDivisor("t", (0, 0), 3), LogDivisor("t+s", (1, 0), -1),
                LogDivisor("t-s", (-1, 0), -1))
    character = DirichletCharacter(5, (None, 0, 1, 3, 2), 4)
    direct = twisted_visible_coefficients(character, 40)
    quotient = dirichlet_l_ratio_coefficients(character, 40)
    characters = tuple(DirichletCharacter(5, tuple(None if e is None else k * e for e in character.exponents), 4)
                       for k in range(4))
    decomposed = progression_via_characters(characters, 2, 40)
    progression = progression_visible_coefficients(5, 2, 40)
    return {"mechanism": "isolated circular log monodromy and exact twisted visible-ray arithmetic",
            "status": "new executable implementation of recovered formulas; finite exact arithmetic checks",
            "monodromy": [isolated_circle_period(geometry, d.point, "1/10").receipt() for d in geometry],
            "character_modulus": 5, "character_root_order": 4,
            "coefficient_count": len(direct), "ratio_coefficient_identity": direct == quotient,
            "progression_character_identity": all(a.rational() == b for a, b in zip(decomposed, progression)),
            "modulus_3_residue_factor_times_inverse_zeta2": str(progression_residue_factor(3, 1)),
            "caveats": ["circle integral depends on radius and base representative",
                        "divisor completeness and analytic remainder are caller obligations",
                        "finite coefficient identity does not identify ratios of truncated L sums",
                        "irrational phase twists are outside this implementation"]}
