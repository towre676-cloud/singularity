"""Exact root-of-unity filters for Mellin/polylogarithmic integral periods.

For Re(s)>1 put I_s(z)=Gamma(s)^(-1) integral_0^1
z*(-log(x))^(s-1)/(1-z*x) dx = Li_s(z), for |z|=1.  All
identities below hold on this common absolutely convergent domain.  No
categorical or exceptional-Lie-algebra assertion is needed.

If n|N and gcd(a,n)=1, let P be the primes dividing N but not n.  Then

 sum_{u mod N, u=a mod n, gcd(u,N)=1} I_s(exp(2*pi*i*u/N))
 = sum_{d|prod(P)} mu(d) (N/(n*d))^(1-s)
       I_s(exp(2*pi*i*(a*d^(-1) mod n)/n)).

Proof: apply inclusion-exclusion to d|u, put u=d*v, then apply the
ordinary finite Fourier filter to the complete congruence class of v.
When gcd(a,n)>1 the primitive class is empty.  Fractions encode phases
modulo one; coefficients at integer weights are rational and exact.

This module uses the existing cyclotomic_real.pi_interval enclosure
instead of introducing another numerical pi or cyclotomic-field layer.
These are mathematical Python calculations, not kernel-checked proofs.
"""

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from math import comb, factorial, gcd


def _positive_integer(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _integer(value, name):
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer")
    return value


def canonical_phase(value):
    """Return an exact rational angle in turns in [0,1); reject floats."""
    if not isinstance(value, (int, Fraction)) or isinstance(value, bool):
        raise ValueError("an integer or Fraction phase is required")
    return Fraction(value) % 1


def prime_divisors(n):
    """Distinct prime divisors, by integer trial division (no CAS dependency)."""
    _positive_integer(n, "n")
    result = []
    p = 2
    while p * p <= n:
        if n % p == 0:
            result.append(p)
            while n % p == 0:
                n //= p
        p = 3 if p == 2 else p + 2
    if n > 1:
        result.append(n)
    return tuple(result)


@lru_cache(maxsize=256)
def bernoulli_number(n):
    """Classical Bernoulli number with B_1=-1/2."""
    if type(n) is not int or n < 0:
        raise ValueError("nonnegative Bernoulli degree required")
    if n == 0:
        return Fraction(1)
    return -sum((comb(n + 1, k) * bernoulli_number(k)
                 for k in range(n)), Fraction(0)) / (n + 1)


def bernoulli_polynomial(n, x):
    """Evaluate B_n(x) at an exact rational x (without reducing x modulo 1)."""
    if type(n) is not int or n < 0:
        raise ValueError("nonnegative Bernoulli degree required")
    if not isinstance(x, (int, Fraction)) or isinstance(x, bool):
        raise ValueError("exact rational argument required")
    x = Fraction(x)
    return sum((comb(n, k) * bernoulli_number(k) * x ** (n - k)
                for k in range(n + 1)), Fraction(0))


def real_li_even_pi_coefficient(weight, phase):
    """Return c exactly such that Re Li_weight(e^(2*pi*i*phase))=c*pi^weight.

    Positive even weight >=2 is required.  This includes phase zero, where
    the value is zeta(weight).  It is the Bernoulli Fourier-series identity.
    """
    if type(weight) is not int or weight < 2 or weight % 2:
        raise ValueError("an even integer weight at least two is required")
    k = weight // 2
    return (Fraction((-1) ** (k + 1) * 2 ** (weight - 1), factorial(weight))
            * bernoulli_polynomial(weight, canonical_phase(phase)))


@dataclass(frozen=True)
class SparsePhaseSum:
    """A normalized exact linear combination of I_s at rational phases.

    This stores a formal expression at a fixed weight; two different
    expressions can have the same period value without identical terms.
    """

    weight: int
    terms: tuple

    def __post_init__(self):
        if type(self.weight) is not int or self.weight < 2:
            raise ValueError("integer weight at least two required")
        merged = {}
        for phase, coefficient in self.terms:
            phase = canonical_phase(phase)
            if not isinstance(coefficient, (int, Fraction)) or isinstance(coefficient, bool):
                raise ValueError("exact rational coefficient required")
            merged[phase] = merged.get(phase, Fraction(0)) + coefficient
        object.__setattr__(self, "terms", tuple(sorted(
            (phase, Fraction(coefficient)) for phase, coefficient in merged.items()
            if coefficient)))

    def __add__(self, other):
        if not isinstance(other, SparsePhaseSum) or self.weight != other.weight:
            raise ValueError("matching integer weights required")
        return SparsePhaseSum(self.weight, self.terms + other.terms)

    def scale(self, scalar):
        if not isinstance(scalar, (int, Fraction)) or isinstance(scalar, bool):
            raise ValueError("exact rational scalar required")
        return SparsePhaseSum(self.weight, tuple((x, scalar*c) for x, c in self.terms))

    def pushforward(self, multiplier):
        """Apply the phase power map z->z^multiplier, retaining multiplicity."""
        _integer(multiplier, "multiplier")
        return SparsePhaseSum(self.weight, tuple((multiplier*x, c) for x, c in self.terms))

    def real_even_pi_coefficient(self):
        return sum((c * real_li_even_pi_coefficient(self.weight, x)
                    for x, c in self.terms), Fraction(0))

    def real_interval(self, bits=64):
        """Rigorous rational enclosure for this even-weight real period sum."""
        from .cyclotomic_real import pi_interval
        coefficient = self.real_even_pi_coefficient()
        lo, hi = pi_interval(bits)
        lo, hi = coefficient * lo ** self.weight, coefficient * hi ** self.weight
        return min(lo, hi), max(lo, hi)

    def as_dict(self):
        return {"weight": self.weight, "terms": [
            {"phase_turns": str(x), "coefficient": str(c)} for x, c in self.terms]}


@dataclass(frozen=True)
class DistributionTerm:
    """multiplicity*dilation^(1-s)*I_s(exp(2*pi*i*phase))."""

    multiplicity: int
    dilation: int
    phase: Fraction

    def __post_init__(self):
        _integer(self.multiplicity, "multiplicity")
        _positive_integer(self.dilation, "dilation")
        object.__setattr__(self, "phase", canonical_phase(self.phase))

    def coefficient(self, weight):
        if type(weight) is not int or weight < 2:
            raise ValueError("integer weight at least two required")
        return Fraction(self.multiplicity, self.dilation ** (weight - 1))


@dataclass(frozen=True)
class PeriodReduction:
    """A root filter and its symbolic sparse distribution formula."""

    n: int
    N: int
    a: int
    primitive: bool
    terms: tuple

    @property
    def phase_count(self):
        """Number of source phases, computed without enumerating them."""
        return sum(t.multiplicity * t.dilation for t in self.terms)

    def source_phases(self):
        return tuple(Fraction(u, self.N) for u in range(self.a, self.N, self.n)
                     if not self.primitive or gcd(u, self.N) == 1)

    def source(self, weight):
        return SparsePhaseSum(weight, tuple((x, 1) for x in self.source_phases()))

    def specialize(self, weight):
        return SparsePhaseSum(weight, tuple((t.phase, t.coefficient(weight)) for t in self.terms))

    def real_even_pi_coefficient(self, weight=2):
        return self.specialize(weight).real_even_pi_coefficient()

    def verify_even_weight(self, weight=2):
        """Independent full-source Bernoulli comparison; no reduction reused."""
        return (self.source(weight).real_even_pi_coefficient()
                == self.real_even_pi_coefficient(weight))

    def as_dict(self, weight=2):
        return {"n": self.n, "N": self.N, "a": self.a,
                "primitive": self.primitive, "phase_count": self.phase_count,
                "domain": "Re(s)>1", "reduced": self.specialize(weight).as_dict(),
                "symbolic_terms": [{"multiplicity": t.multiplicity,
                                    "dilation": t.dilation,
                                    "phase_turns": str(t.phase)} for t in self.terms]}


def period_reduction(n, N, a=1, *, primitive=True):
    """Construct the exact filter for n|N, including empty nonunit classes."""
    _positive_integer(n, "n")
    _positive_integer(N, "N")
    _integer(a, "a")
    if N % n:
        raise ValueError("n must divide N")
    if type(primitive) is not bool:
        raise ValueError("primitive must be bool")
    a %= n
    if primitive and gcd(a, n) != 1:
        return PeriodReduction(n, N, a, primitive, ())
    divisors = [(1, 1)]
    if primitive:
        for p in prime_divisors(N):
            if n % p:
                divisors += [(d*p, -sign) for d, sign in divisors]
    terms = []
    for d, sign in sorted(divisors):
        b = a * pow(d, -1, n) % n if n > 1 else 0
        terms.append(DistributionTerm(sign, N // (n*d), Fraction(b, n)))
    return PeriodReduction(n, N, a, primitive, tuple(terms))


def primitive_conjugate_reduction(n, N, a=1):
    """Primitive N-th roots lying over exp(2*pi*i*a/n)."""
    return period_reduction(n, N, a, primitive=True)


def full_fiber_reduction(n, N, a=1):
    """All N/n branches, without a primitivity restriction."""
    return period_reduction(n, N, a, primitive=False)


def compose_full_fiber(n, middle, N, a=1, *, weight=2):
    """Compose N->middle->n complete root distributions and check coherence.

    Returns the resulting sparse expression. The intermediate fiber is
    explicitly retained until its common outer coefficient is applied.
    """
    _positive_integer(n, "n")
    _positive_integer(middle, "middle")
    _positive_integer(N, "N")
    if middle % n or N % middle:
        raise ValueError("n must divide middle and middle must divide N")
    direct = full_fiber_reduction(n, N, a).specialize(weight)
    intermediate = full_fiber_reduction(n, middle, a).specialize(weight)
    composed = intermediate.scale(Fraction(1, (N // middle) ** (weight - 1)))
    if direct != composed:
        raise ArithmeticError("root-distribution composition failed")
    return composed
