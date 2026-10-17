"""Small exact polynomial and formal-series operations over ``Q[q]``.

A q-polynomial is a sparse ``{nonnegative exponent: Fraction}`` dictionary.
An x-series is a list of q-polynomials, with list index equal to x-degree.
Every operation returns fresh normalized dictionaries. No floating-point
arithmetic is used; this module is intentionally independent of computer
algebra packages so that the released coefficient certificates can be replayed.
"""

from fractions import Fraction
from typing import Iterable, Mapping, Sequence

Polynomial = dict[int, Fraction]
Series = list[Polynomial]


def _nonnegative_integer(value: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def normalize(poly: Mapping[int, int | Fraction]) -> Polynomial:
    """Coerce coefficients to exact rationals and discard zeros."""
    result: Polynomial = {}
    for exponent, coefficient in poly.items():
        _nonnegative_integer(exponent, "polynomial exponent")
        if not isinstance(coefficient, (int, Fraction)) or isinstance(coefficient, bool):
            raise TypeError("coefficients must be integers or Fractions")
        value = Fraction(coefficient)
        if value:
            result[exponent] = value
    return dict(sorted(result.items()))


def constant(value: int | Fraction) -> Polynomial:
    return normalize({0: value})


def add(left: Mapping[int, int | Fraction], right: Mapping[int, int | Fraction]) -> Polynomial:
    result = normalize(left)
    for exponent, coefficient in normalize(right).items():
        result[exponent] = result.get(exponent, Fraction(0)) + coefficient
    return normalize(result)


def scale(poly: Mapping[int, int | Fraction], coefficient: int | Fraction) -> Polynomial:
    scalar = constant(coefficient).get(0, Fraction(0))
    return normalize({e: scalar * c for e, c in normalize(poly).items()})


def sub(left: Mapping[int, int | Fraction], right: Mapping[int, int | Fraction]) -> Polynomial:
    return add(left, scale(right, -1))


def mul(left: Mapping[int, int | Fraction], right: Mapping[int, int | Fraction]) -> Polynomial:
    result: Polynomial = {}
    for i, a in normalize(left).items():
        for j, b in normalize(right).items():
            result[i + j] = result.get(i + j, Fraction(0)) + a * b
    return normalize(result)


def power(poly: Mapping[int, int | Fraction], exponent: int) -> Polynomial:
    _nonnegative_integer(exponent, "power")
    result = constant(1)
    base = normalize(poly)
    while exponent:
        if exponent & 1:
            result = mul(result, base)
        base = mul(base, base)
        exponent //= 2
    return result


def evaluate(poly: Mapping[int, int | Fraction], q: int | Fraction) -> Fraction:
    """Evaluate exactly. Floats are rejected to avoid silent approximation."""
    if not isinstance(q, (int, Fraction)) or isinstance(q, bool):
        raise TypeError("q must be an integer or Fraction")
    return sum((c * Fraction(q) ** e for e, c in normalize(poly).items()), Fraction(0))


def derivative(poly: Mapping[int, int | Fraction]) -> Polynomial:
    return normalize({e - 1: e * c for e, c in normalize(poly).items() if e})


def from_factors(
    coefficient: int | Fraction = 1,
    monomial: int = 0,
    factors: Iterable[tuple[int, int]] = (),
) -> Polynomial:
    """Expand ``coefficient*q**monomial*prod((1-q**d)**m)`` exactly.

    This verifies a supplied factorization; it is not a factorization solver.
    Degrees must be positive and multiplicities nonnegative.
    """
    _nonnegative_integer(monomial, "monomial exponent")
    result = normalize({monomial: coefficient})
    for degree, multiplicity in factors:
        _nonnegative_integer(degree, "factor degree")
        _nonnegative_integer(multiplicity, "factor multiplicity")
        if degree == 0:
            raise ValueError("factor degree must be positive")
        result = mul(result, power({0: 1, degree: -1}, multiplicity))
    return result


def verify_factorization(
    poly: Mapping[int, int | Fraction],
    coefficient: int | Fraction = 1,
    monomial: int = 0,
    factors: Iterable[tuple[int, int]] = (),
) -> bool:
    return normalize(poly) == from_factors(coefficient, monomial, factors)


def normalized_series(series: Sequence[Mapping[int, int | Fraction]], max_degree: int | None = None) -> Series:
    if max_degree is None:
        max_degree = len(series) - 1
    _nonnegative_integer(max_degree, "series degree")
    return [normalize(series[i]) if i < len(series) else {} for i in range(max_degree + 1)]


def series_add(left: Sequence[Mapping[int, int | Fraction]], right: Sequence[Mapping[int, int | Fraction]], max_degree: int | None = None) -> Series:
    if max_degree is None:
        max_degree = max(len(left), len(right)) - 1
    a, b = normalized_series(left, max_degree), normalized_series(right, max_degree)
    return [add(x, y) for x, y in zip(a, b)]


def series_mul(left: Sequence[Mapping[int, int | Fraction]], right: Sequence[Mapping[int, int | Fraction]], max_degree: int | None = None) -> Series:
    if max_degree is None:
        max_degree = min(len(left), len(right)) - 1
    a, b = normalized_series(left, max_degree), normalized_series(right, max_degree)
    result: Series = [{} for _ in range(max_degree + 1)]
    for i in range(max_degree + 1):
        for j in range(max_degree + 1 - i):
            if a[i] and b[j]:
                result[i + j] = add(result[i + j], mul(a[i], b[j]))
    return result


def series_inverse(series: Sequence[Mapping[int, int | Fraction]], max_degree: int | None = None) -> Series:
    """Invert a series whose constant coefficient is a nonzero rational."""
    a = normalized_series(series, max_degree)
    if set(a[0]) != {0}:
        raise ValueError("inverse requires a nonzero rational constant term")
    inv = 1 / a[0][0]
    result = [constant(inv)] + [{} for _ in range(len(a) - 1)]
    for n in range(1, len(a)):
        total: Polynomial = {}
        for i in range(1, n + 1):
            total = add(total, mul(a[i], result[n - i]))
        result[n] = scale(total, -inv)
    return result


def series_log(series: Sequence[Mapping[int, int | Fraction]], max_degree: int | None = None) -> Series:
    """Formal logarithm of a unit series, using ``L' = L*(log L)'``."""
    a = normalized_series(series, max_degree)
    if a[0] != constant(1):
        raise ValueError("formal logarithm requires constant term 1")
    result: Series = [{} for _ in a]
    for n in range(1, len(a)):
        total = scale(a[n], n)
        for i in range(1, n):
            total = sub(total, scale(mul(result[i], a[n - i]), i))
        result[n] = scale(total, Fraction(1, n))
    return result


def series_exp(series: Sequence[Mapping[int, int | Fraction]], max_degree: int | None = None) -> Series:
    """Formal exponential of a series with zero constant coefficient."""
    a = normalized_series(series, max_degree)
    if a[0]:
        raise ValueError("formal exponential requires constant term 0")
    result = [constant(1)] + [{} for _ in range(len(a) - 1)]
    for n in range(1, len(a)):
        total: Polynomial = {}
        for i in range(1, n + 1):
            total = add(total, scale(mul(a[i], result[n - i]), i))
        result[n] = scale(total, Fraction(1, n))
    return result


def polynomial_to_json(poly: Mapping[int, int | Fraction]) -> list[list[int]]:
    return [[e, c.numerator, c.denominator] for e, c in normalize(poly).items()]


def polynomial_from_json(entries: Sequence[Sequence[int]]) -> Polynomial:
    result: Polynomial = {}
    for item in entries:
        if len(item) != 3:
            raise ValueError("polynomial entries must be [degree, numerator, denominator]")
        exponent, numerator, denominator = item
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in item):
            raise ValueError("polynomial JSON entries must contain integers")
        _nonnegative_integer(exponent, "polynomial exponent")
        if exponent in result or denominator <= 0 or numerator == 0:
            raise ValueError("polynomial entries must be unique and nonzero with positive denominators")
        result[exponent] = Fraction(numerator, denominator)
    return normalize(result)
