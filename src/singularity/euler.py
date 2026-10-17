"""Exact finite Euler transforms and first-discrepancy signatures.

For a formal unit series L, unique polynomials b_n in Q[q] satisfy
L(x)=prod_n (1-x**n)**(-b_n). These are formal exponents. Their existence
does not assert global meromorphic continuation of a prime Euler product.
"""

from fractions import Fraction
from typing import Mapping, Sequence

from .polynomials import (
    Polynomial, Series, add, constant, evaluate, mul, normalize,
    normalized_series, scale, series_log, series_mul, sub,
)


def log_coefficients(series: Sequence[Mapping[int, int | Fraction]], max_degree: int | None = None) -> Series:
    return series_log(series, max_degree)


def euler_exponents(series: Sequence[Mapping[int, int | Fraction]], max_degree: int | None = None) -> Series:
    """Return b_0=0,b_1,...,b_N for ``L=prod(1-x**n)**-b_n``.

    If ell_n=[x**n]log(L), then n*ell_n=sum_{d|n}d*b_d.
    Lower indices alone determine the recursion; every coefficient is exact.
    """
    logarithm = series_log(series, max_degree)
    result: Series = [{} for _ in logarithm]
    for n in range(1, len(result)):
        value = logarithm[n]
        for d in range(1, n):
            if n % d == 0:
                value = sub(value, scale(result[d], Fraction(d, n)))
        result[n] = value
    return result


def _mobius(n: int) -> int:
    value = 1
    prime = 2
    while prime * prime <= n:
        if n % prime == 0:
            n //= prime
            value = -value
            if n % prime == 0:
                return 0
            while n % prime == 0:
                n //= prime
        prime += 1
    return -value if n > 1 else value


def euler_exponents_mobius(series: Sequence[Mapping[int, int | Fraction]], max_degree: int | None = None) -> Series:
    """Independent divisor-inversion formula, useful for replay cross-checks."""
    logarithm = series_log(series, max_degree)
    result: Series = [{} for _ in logarithm]
    for n in range(1, len(result)):
        for divisor in range(1, n + 1):
            if n % divisor == 0:
                result[n] = add(result[n], scale(logarithm[n // divisor], Fraction(_mobius(divisor), divisor)))
    return result


def recompose_euler(exponents: Sequence[Mapping[int, int | Fraction]], max_degree: int | None = None) -> Series:
    """Multiply generalized-binomial factors, independently of log recursion.

    The coefficient of y**j in (1-y)**(-b) is
    b(b+1)...(b+j-1)/j!, evaluated in Q[q].
    """
    b = normalized_series(exponents, max_degree)
    if b[0]:
        raise ValueError("Euler exponent at index zero must be zero")
    degree = len(b) - 1
    result = [constant(1)] + [{} for _ in range(degree)]
    for n in range(1, degree + 1):
        factor: Series = [{} for _ in range(degree + 1)]
        factor[0] = constant(1)
        coefficient = constant(1)
        for j in range(1, degree // n + 1):
            coefficient = scale(mul(coefficient, add(b[n], constant(j - 1))), Fraction(1, j))
            factor[n * j] = coefficient
        result = series_mul(result, factor, degree)
    return result


def first_difference(left: Sequence[Mapping[int, int | Fraction]], right: Sequence[Mapping[int, int | Fraction]]) -> tuple[int, Polynomial] | None:
    """First symbolic difference within the shared truncation, or None.

    None means agreement only through the available shared degree. It never
    asserts equality of infinite series, even if one supplied list is longer.
    """
    for n in range(min(len(left), len(right))):
        delta = sub(left[n], right[n])
        if delta:
            return n, delta
    return None


def first_difference_at_q(left: Sequence[Mapping[int, int | Fraction]], right: Sequence[Mapping[int, int | Fraction]], q: int | Fraction) -> tuple[int, Fraction] | None:
    """Scan after specialization: the first symbolic delta can vanish at q."""
    for n in range(min(len(left), len(right))):
        delta = evaluate(left[n], q) - evaluate(right[n], q)
        if delta:
            return n, delta
    return None


def finite_signature(left: Sequence[Mapping[int, int | Fraction]], right: Sequence[Mapping[int, int | Fraction]], q: int | Fraction) -> dict:
    """JSON-safe statement of a detected first-discrepancy exponent.

    This function records exact finite algebra, not a claimed analytic
    continuation certificate. The transfer theorem applies to graph local
    series with its separately stated positivity and convergence hypotheses.
    """
    found = first_difference_at_q(left, right, q)
    if found is None:
        return {"status": "agreement_through_truncation", "through_volume": min(len(left), len(right)) - 1}
    r, delta = found
    return {
        "status": "first_difference", "volume": r,
        "delta_numerator": delta.numerator, "delta_denominator": delta.denominator,
        "candidate_real_location": None if r == 0 else f"1/{r}",
        "analytic_hypotheses_checked": False,
    }
