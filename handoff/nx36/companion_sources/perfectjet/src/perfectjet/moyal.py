"""Exact finite Moyal algebra over Q[i][hbar][q_1,...,q_n,p_1,...,p_n].

Adapted from the recovered ``symplectic_moyal_bridge_v4.zip`` packet's
``symplectic_moyal_bridge_v4.py``. This supported layer keeps the exact Gaussian
rational polynomial calculus, not the optional NumPy geometry experiment.
The bidifferential expansion terminates for polynomials; no truncation or
floating-point equality is used. This implements standard Weyl/Moyal identities,
not a universal Dirac quantization or a formal proof assistant certificate.

Ordinary pullback preserves this flat star product for affine symplectic maps.
Nonlinear symplectomorphisms preserve the Poisson bracket but need a transported
star product or corrected quantum pullback. ``covariance_example`` exhibits the
boundary exactly. The affine-quadratic safe sector is a Lie subalgebra under the
scaled commutator, not an associative subalgebra under the star product.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import factorial


def _natural(value, name):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


@dataclass(frozen=True)
class GaussianRational:
    """An exact coefficient re + i*im; use integers or Fraction components."""
    re: Fraction = Fraction(0)
    im: Fraction = Fraction(0)

    def __post_init__(self):
        for name in ("re", "im"):
            value = getattr(self, name)
            if not isinstance(value, (int, Fraction)):
                raise TypeError("Gaussian rational components must be int or Fraction")
            object.__setattr__(self, name, Fraction(value))

    def __add__(self, other):
        other = to_gi(other)
        return GaussianRational(self.re + other.re, self.im + other.im)

    __radd__ = __add__

    def __neg__(self):
        return GaussianRational(-self.re, -self.im)

    def __sub__(self, other):
        return self + -to_gi(other)

    def __rsub__(self, other):
        return to_gi(other) + -self

    def __mul__(self, other):
        other = to_gi(other)
        return GaussianRational(self.re * other.re - self.im * other.im,
                                self.re * other.im + self.im * other.re)

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = to_gi(other)
        den = other.re * other.re + other.im * other.im
        if den == 0:
            raise ZeroDivisionError("Gaussian rational division by zero")
        return GaussianRational((self.re * other.re + self.im * other.im) / den,
                                (self.im * other.re - self.re * other.im) / den)

    def conj(self):
        return GaussianRational(self.re, -self.im)

    def is_zero(self):
        return self.re == 0 and self.im == 0

    def __str__(self):
        if self.im == 0:
            return str(self.re)
        if self.re == 0:
            return f"{self.im}i"
        sign = "+" if self.im >= 0 else "-"
        return f"{self.re} {sign} {abs(self.im)}i"


GI = GaussianRational  # Original packet's coefficient name remains usable.
ZERO, ONE, I = GI(0), GI(1), GI(0, 1)


def to_gi(value):
    if isinstance(value, GaussianRational):
        return value
    if isinstance(value, (int, Fraction)):
        return GaussianRational(value)
    raise TypeError("coefficients must be int, Fraction, or GaussianRational")


class PolyH:
    """Sparse exact polynomial with keys (hbar_power, variable_exponents).

    Exponents use q-first/p-second ordering and have length 2*n. ``*`` is
    ordinary commutative polynomial multiplication; use ``star_product`` for
    the Moyal product. Construction discards zero coefficients.
    """
    def __init__(self, n, terms=None):
        _natural(n, "n")
        if n == 0:
            raise ValueError("n must be positive")
        self.n, self.m = n, 2 * n
        self.terms = {}
        for (hpow, exps), coefficient in (terms or {}).items():
            _natural(hpow, "hbar power")
            exps = tuple(exps)
            if len(exps) != self.m:
                raise ValueError("expected 2*n variable exponents")
            for exp in exps:
                _natural(exp, "variable exponent")
            coefficient = to_gi(coefficient)
            if not coefficient.is_zero():
                self.terms[hpow, exps] = coefficient

    @staticmethod
    def zero(n):
        return PolyH(n)

    @staticmethod
    def one(n):
        return PolyH.monomial(n, (0,) * (2 * n))

    @staticmethod
    def monomial(n, exps, coeff=1, hpow=0):
        return PolyH(n, {(hpow, tuple(exps)): coeff})

    @staticmethod
    def q(n=1, i=0):
        _natural(i, "coordinate index")
        if i >= n:
            raise ValueError("coordinate index must be smaller than n")
        exps = tuple(int(j == i) for j in range(2 * n))
        return PolyH.monomial(n, exps)

    @staticmethod
    def p(n=1, i=0):
        _natural(i, "coordinate index")
        if i >= n:
            raise ValueError("coordinate index must be smaller than n")
        exps = tuple(int(j == n + i) for j in range(2 * n))
        return PolyH.monomial(n, exps)

    @staticmethod
    def hbar(n=1):
        return PolyH.monomial(n, (0,) * (2 * n), hpow=1)

    def _coerce(self, other):
        if isinstance(other, PolyH):
            if self.n != other.n:
                raise ValueError("polynomials have different phase-space dimensions")
            return other
        return PolyH.monomial(self.n, (0,) * self.m, coeff=other)

    def __add__(self, other):
        other = self._coerce(other)
        terms = dict(self.terms)
        for key, value in other.terms.items():
            terms[key] = terms.get(key, ZERO) + value
        return PolyH(self.n, terms)

    __radd__ = __add__

    def __neg__(self):
        return self.scale(-1)

    def __sub__(self, other):
        return self + -self._coerce(other)

    def __rsub__(self, other):
        return self._coerce(other) + -self

    def __mul__(self, other):
        other = self._coerce(other)
        terms = {}
        for (ha, ea), ca in self.terms.items():
            for (hb, eb), cb in other.terms.items():
                key = ha + hb, tuple(a + b for a, b in zip(ea, eb))
                terms[key] = terms.get(key, ZERO) + ca * cb
        return PolyH(self.n, terms)

    __rmul__ = __mul__
    mul = __mul__

    def __pow__(self, exponent):
        _natural(exponent, "polynomial power")
        out, base = PolyH.one(self.n), self
        while exponent:
            if exponent & 1:
                out = out * base
            base = base * base
            exponent //= 2
        return out

    def scale(self, coefficient):
        coefficient = to_gi(coefficient)
        return PolyH(self.n, {key: c * coefficient for key, c in self.terms.items()})

    def derivative(self, orders):
        orders = tuple(orders)
        if len(orders) != self.m:
            raise ValueError("expected 2*n derivative orders")
        for order in orders:
            _natural(order, "derivative order")
        terms = {}
        for (hp, exps), coefficient in self.terms.items():
            if any(order > exp for order, exp in zip(orders, exps)):
                continue
            factor = 1
            for exp, order in zip(exps, orders):
                for offset in range(order):
                    factor *= exp - offset
            key = hp, tuple(exp - order for exp, order in zip(exps, orders))
            terms[key] = coefficient * factor
        return PolyH(self.n, terms)

    def max_var_exp(self):
        return tuple(max((exps[j] for _, exps in self.terms), default=0)
                     for j in range(self.m))

    def coefficient(self, exps, hpow=0):
        exps = tuple(exps)
        if len(exps) != self.m:
            raise ValueError("expected 2*n variable exponents")
        _natural(hpow, "hbar power")
        for exp in exps:
            _natural(exp, "variable exponent")
        return self.terms.get((hpow, exps), ZERO)

    def is_zero(self):
        return not self.terms

    def variable_part_zero(self):
        return all(not any(exps) for _, exps in self.terms)

    def first_hbar_power(self):
        return min((hp for hp, _ in self.terms), default=None)

    def to_data(self):
        """JSON-compatible exact coefficients as rational strings."""
        return {"n": self.n, "terms": [
            {"hbar_power": hp, "exponents": list(exps),
             "real": str(c.re), "imaginary": str(c.im)}
            for (hp, exps), c in sorted(self.terms.items())]}

    def __eq__(self, other):
        if not isinstance(other, PolyH):
            try:
                other = self._coerce(other)
            except (TypeError, ValueError):
                return False
        return self.n == other.n and self.terms == other.terms

    def __str__(self):
        pieces = []
        names = [f"q{j+1}" for j in range(self.n)] + [f"p{j+1}" for j in range(self.n)]
        for (hp, exps), c in sorted(self.terms.items()):
            powers = (["hbar" if hp == 1 else f"hbar^{hp}"] if hp else [])
            powers += [name if exp == 1 else f"{name}^{exp}"
                       for name, exp in zip(names, exps) if exp]
            pieces.append(f"({c})*{'*'.join(powers) or '1'}")
        return " + ".join(pieces) or "0"


def _same_dimension(f, g):
    if not isinstance(f, PolyH) or not isinstance(g, PolyH):
        raise TypeError("expected PolyH arguments")
    if f.n != g.n:
        raise ValueError("polynomials have different phase-space dimensions")


def _multi_indices(bounds):
    return product(*(range(bound + 1) for bound in bounds))


def _i_power(k):
    return (ONE, I, -ONE, -I)[k % 4]


def star_product(f, g):
    """Finite exact Weyl/Moyal product with {q_i,p_j}=delta_ij."""
    _same_dimension(f, g)
    n = f.n
    fm, gm = f.max_var_exp(), g.max_var_exp()
    alpha_bounds = tuple(min(fm[i], gm[n+i]) for i in range(n))
    beta_bounds = tuple(min(fm[n+i], gm[i]) for i in range(n))
    out = PolyH.zero(n)
    for alpha in _multi_indices(alpha_bounds):
        for beta in _multi_indices(beta_bounds):
            k = sum(alpha) + sum(beta)
            df, dg = f.derivative(alpha + beta), g.derivative(beta + alpha)
            if df.is_zero() or dg.is_zero():
                continue
            denominator = 2 ** k
            for value in alpha + beta:
                denominator *= factorial(value)
            c = _i_power(k) * Fraction((-1) ** sum(beta), denominator)
            term = (df * dg).scale(c)
            out += PolyH(n, {(hp+k, exps): value for (hp, exps), value in term.terms.items()})
    return out


def poisson_bracket(f, g):
    """Exact classical bracket in q-first/p-second coordinate order."""
    _same_dimension(f, g)
    out = PolyH.zero(f.n)
    for i in range(f.n):
        dq = tuple(int(j == i) for j in range(f.m))
        dp = tuple(int(j == f.n+i) for j in range(f.m))
        out += f.derivative(dq) * g.derivative(dp) - f.derivative(dp) * g.derivative(dq)
    return out


def scaled_moyal_bracket(f, g):
    """(f star g - g star f)/(i*hbar), with exact formal division."""
    commutator = star_product(f, g) - star_product(g, f)
    if any(hp == 0 for hp, _ in commutator.terms):
        raise ArithmeticError("Moyal commutator unexpectedly has an hbar^0 term")
    return PolyH(f.n, {(hp-1, exps): value * -I
                      for (hp, exps), value in commutator.terms.items()})


def egorov_defect(hamiltonian, observable):
    return scaled_moyal_bracket(hamiltonian, observable) - poisson_bracket(hamiltonian, observable)


def classify_defect(defect):
    if defect.is_zero():
        return "EXACT"
    return "CENTRAL_DEFECT" if defect.variable_part_zero() else "NONCENTRAL_DEFECT"


def pullback(f, coordinates):
    """Ordinary substitution of 2*n polynomial coordinates, preserving hbar."""
    coordinates = tuple(coordinates)
    if len(coordinates) != f.m:
        raise ValueError("expected 2*n polynomial coordinate images")
    for coordinate in coordinates:
        _same_dimension(f, coordinate)
    out = PolyH.zero(f.n)
    for (hp, exps), coefficient in f.terms.items():
        term = PolyH.monomial(f.n, (0,) * f.m, coefficient, hp)
        for coordinate, exponent in zip(coordinates, exps):
            term *= coordinate ** exponent
        out += term
    return out


def covariance_defect(f, g, coordinates):
    """(Phi*f) star (Phi*g) - Phi*(f star g), without assuming covariance."""
    return (star_product(pullback(f, coordinates), pullback(g, coordinates))
            - pullback(star_product(f, g), coordinates))


def monomials_total_degree(n, max_total_degree):
    """List (exponent_tuple, monomial) in the finite total-degree window."""
    _natural(max_total_degree, "maximum total degree")
    PolyH.zero(n)  # validate the phase-space dimension before enumerating
    return [(exps, PolyH.monomial(n, exps))
            for exps in product(range(max_total_degree + 1), repeat=2*n)
            if sum(exps) <= max_total_degree]


def scan_phase_diagram(max_total_degree=5):
    """Exact one-degree-of-freedom census; cost grows with the degree window."""
    symbols = monomials_total_degree(1, max_total_degree)
    counts = {key: 0 for key in ("EXACT", "CENTRAL_DEFECT", "NONCENTRAL_DEFECT")}
    for _, f in symbols:
        for _, g in symbols:
            counts[classify_defect(egorov_defect(f, g))] += 1
    return {"max_total_degree": max_total_degree, "pair_count": len(symbols)**2,
            "counts": counts}


def covariance_example():
    """Computed affine covariance and nonlinear shear counterexample."""
    q, p = PolyH.q(), PolyH.p()
    affine = (q+p+1, p+2)
    symbols = monomials_total_degree(1, 3)
    affine_ok = all(covariance_defect(f, g, affine).is_zero()
                    for _, f in symbols for _, g in symbols)
    nonlinear = (q, p+q*q)
    f, g = p*p, p
    poisson_difference = (poisson_bracket(pullback(f, nonlinear), pullback(g, nonlinear))
                          - pullback(poisson_bracket(f, g), nonlinear))
    defect = covariance_defect(f, g, nonlinear)
    return {"affine_map": "(q+p+1,p+2)", "affine_tested_pairs": len(symbols)**2,
            "affine_covariance_exact": affine_ok,
            "nonlinear_map": "(q,p+q^2)", "test_pair": ["p^2", "p"],
            "nonlinear_poisson_covariance_exact": poisson_difference.is_zero(),
            "nonlinear_star_defect": defect.to_data()}


def receipt():
    """JSON-compatible fresh arithmetic receipt, not a kernel theorem."""
    q, p = PolyH.q(), PolyH.p()
    h = PolyH.hbar()
    cubic = egorov_defect(q**3, p**3)
    quintic = egorov_defect(q**5, p**5)
    quartic_h = p*p*Fraction(1, 2) + q*q*Fraction(1, 2) + q**4*Fraction(1, 4)
    quartic = egorov_defect(quartic_h, p**3)
    safe = monomials_total_degree(2, 2)
    safe_ok = all(egorov_defect(f, g).is_zero() for _, f in safe for _, g in safe)
    return {"schema": "perfectjet/moyal/1", "arithmetic": "exact Q[i][hbar][q,p]",
            "source": "recovered symplectic_moyal_bridge_v4.zip",
            "cubic_defect": cubic.to_data(), "cubic_matches": cubic == h*h*Fraction(-3, 2),
            "quintic_defect": quintic.to_data(),
            "quintic_matches": quintic == h*h*q*q*p*p*(-150) + h**4*Fraction(15, 2),
            "quartic_egorov_defect": quartic.to_data(),
            "quartic_matches": quartic == h*h*q*Fraction(-3, 2),
            "quadratic_2d_tested_pairs": len(safe)**2, "quadratic_2d_exact": safe_ok,
            "degree5_census": scan_phase_diagram(5), "covariance": covariance_example(),
            "scope": "finite exact computations; polynomial algebra; no universal Dirac map"}
