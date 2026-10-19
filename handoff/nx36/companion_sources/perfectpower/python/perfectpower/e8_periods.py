"""Exact E8 Coxeter geometry and its cyclotomic integral trace.

Coordinates are doubled: norm-squared 8 here means norm-squared 2 for a
root.  The integral identities concern Re(s)>1.  The root permutation
representation (dimension 240) is distinct from the reflection
representation (dimension 8); matching dimensions alone is never used to
identify them with an unrelated cyclotomic Galois orbit.

References: M. Reeder, *Cyclotomic structures on root lattices*, sections
3.1--3.2, https://www.math.utah.edu/~ptrapa/math-library/reeder/
reeder-cyclotomic-root-lattices-2008.pdf ; D. A. Richter, *Triacontagonal
coordinates for the E(8) root system*, https://arxiv.org/abs/0704.3091 .
"""

from fractions import Fraction
from functools import lru_cache
from itertools import combinations, product
from math import comb, factorial, gcd, log, pi


EXPONENTS = (1, 7, 11, 13, 17, 19, 23, 29)
COXETER_NUMBER = 30
# Coefficients run from constant coefficient to leading coefficient.
PHI30 = (1, 1, 0, -1, -1, -1, 0, 1, 1)
SIMPLE_ROOTS = (
    (1, -1, -1, -1, -1, -1, -1, 1),
    (2, 2, 0, 0, 0, 0, 0, 0),
    (-2, 2, 0, 0, 0, 0, 0, 0),
    (0, -2, 2, 0, 0, 0, 0, 0),
    (0, 0, -2, 2, 0, 0, 0, 0),
    (0, 0, 0, -2, 2, 0, 0, 0),
    (0, 0, 0, 0, -2, 2, 0, 0),
    (0, 0, 0, 0, 0, -2, 2, 0),
)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


@lru_cache(maxsize=1)
def roots():
    """The actual 112+128 roots of E8, in doubled Euclidean coordinates."""
    out = []
    for i, j in combinations(range(8), 2):
        for a, b in product((-2, 2), repeat=2):
            v = [0] * 8
            v[i], v[j] = a, b
            out.append(tuple(v))
    out.extend(v for v in product((-1, 1), repeat=8) if sum(x < 0 for x in v) % 2 == 0)
    return tuple(sorted(out))


def reflect(root, simple):
    """Reflect a doubled root in a doubled simple root, with integer checks."""
    if len(root) != 8 or simple not in SIMPLE_ROOTS:
        raise ValueError("an eight-coordinate root and one supplied simple root are required")
    inner = _dot(root, simple)
    if inner % 4:
        raise ValueError("coordinates do not have an integral root pairing")
    return tuple(x - (inner // 4) * a for x, a in zip(root, simple))


def coxeter_action(root):
    """Apply s_8 ... s_1 to a root (s_1 acts first)."""
    for simple in SIMPLE_ROOTS:
        root = reflect(root, simple)
    return root


def cartan_matrix():
    return tuple(tuple(_dot(a, b) // 4 for b in SIMPLE_ROOTS) for a in SIMPLE_ROOTS)


def identity(n=8):
    return tuple(tuple(int(i == j) for j in range(n)) for i in range(n))


def matmul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(len(b)))
                       for j in range(len(b[0]))) for i in range(len(a)))


def matrix_power(a, n):
    if type(n) is not int or n < 0:
        raise ValueError("a nonnegative integer exponent is required")
    out = identity(len(a))
    while n:
        if n & 1:
            out = matmul(out, a)
        a = matmul(a, a)
        n //= 2
    return out


def matvec(a, v):
    return tuple(_dot(row, v) for row in a)


@lru_cache(maxsize=1)
def _simple_basis_inverse():
    augmented = [[Fraction(SIMPLE_ROOTS[j][i]) for j in range(8)]
                 + [Fraction(int(i == j)) for j in range(8)] for i in range(8)]
    for j in range(8):
        pivot = next(i for i in range(j, 8) if augmented[i][j])
        augmented[j], augmented[pivot] = augmented[pivot], augmented[j]
        scale = augmented[j][j]
        augmented[j] = [a / scale for a in augmented[j]]
        for i in range(8):
            if i != j:
                scale = augmented[i][j]
                augmented[i] = [a - scale * b for a, b in zip(augmented[i], augmented[j])]
    return tuple(tuple(row[8:]) for row in augmented)


def simple_root_coordinates(root):
    """Integral coefficients in the displayed base; rejects nonlattice input."""
    if len(root) != 8:
        raise ValueError("eight doubled coordinates are required")
    coefficients = matvec(_simple_basis_inverse(), root)
    if any(c.denominator != 1 for c in coefficients):
        raise ValueError("the vector is not in the root lattice")
    return tuple(int(c) for c in coefficients)


@lru_cache(maxsize=1)
def coxeter_matrix():
    """Coxeter operator in the simple-root basis, with integer entries."""
    cartan = cartan_matrix()
    out = identity()
    for i in range(8):
        reflection = [list(row) for row in identity()]
        reflection[i] = [int(i == j) - cartan[i][j] for j in range(8)]
        out = matmul(tuple(map(tuple, reflection)), out)
    return out


def characteristic_polynomial(matrix):
    """Exact coefficients, low to high, using Newton identities."""
    n = len(matrix)
    power = identity(n)
    traces = [n]
    for _ in range(n):
        power = matmul(power, matrix)
        traces.append(sum(power[i][i] for i in range(n)))
    high = [1]
    for k in range(1, n + 1):
        total = sum(high[k - j] * traces[j] for j in range(1, k + 1))
        if total % k:
            raise ArithmeticError("Newton identity failed integrality")
        high.append(-total // k)
    return tuple(reversed(high))


@lru_cache(maxsize=1)
def root_orbits():
    """Deterministic, actual Coxeter root orbits; no phase/root relabeling."""
    remaining = set(roots())
    result = []
    while remaining:
        first = min(remaining)
        orbit, point = [], first
        while point not in orbit:
            if point not in remaining:
                raise ArithmeticError("Coxeter action failed to partition roots")
            orbit.append(point)
            point = coxeter_action(point)
        if point != first:
            raise ArithmeticError("Coxeter orbit did not return to its seed")
        remaining.difference_update(orbit)
        result.append(tuple(orbit))
    return tuple(result)


def coxeter_trace(power):
    if type(power) is not int:
        raise ValueError("an integer power is required")
    matrix = matrix_power(coxeter_matrix(), power % 30)
    return sum(matrix[i][i] for i in range(8))


def ramanujan_sum_30(power):
    """c_30(n) by its integer divisor formula, independently of matrices."""
    if type(power) is not int:
        raise ValueError("an integer power is required")
    mobius = {1: 1, 2: -1, 3: -1, 5: -1, 6: 1, 10: 1, 15: 1, 30: -1}
    return sum(d * mobius[30 // d] for d in mobius if power % d == 0)


def spectral_zeta_factor(s):
    """Rational A_s with sum_m Li_s(zeta_30^m)=A_s*zeta(s), integer s>1.

    For complex Re(s)>1 the same identity has A_s equal to
    (2**(1-s)-1)*(3**(1-s)-1)*(5**(1-s)-1).
    """
    if type(s) is not int or s < 2:
        raise ValueError("an integer s >= 2 is required")
    result = Fraction(1)
    for p in (2, 3, 5):
        result *= Fraction(1, p ** (s - 1)) - 1
    return result


def bernoulli_number(n):
    """B_n with B_1=-1/2, from its exact triangular recurrence."""
    if type(n) is not int or n < 0:
        raise ValueError("a nonnegative integer is required")
    numbers = [Fraction(1)]
    for k in range(1, n + 1):
        numbers.append(-sum(Fraction(comb(k + 1, j)) * numbers[j]
                            for j in range(k)) / (k + 1))
    return numbers[n]


def bernoulli_polynomial(n, x):
    x = Fraction(x)
    return sum(Fraction(comb(n, k)) * bernoulli_number(k) * x ** (n - k)
               for k in range(n + 1))


def spectral_pi_coefficient(even_s):
    """Coefficient of pi**s in the E8 reflection-spectrum polylog trace."""
    if type(even_s) is not int or even_s < 2 or even_s % 2:
        raise ValueError("a positive even s >= 2 is required")
    k = even_s // 2
    zeta_coefficient = Fraction((-1) ** (k + 1) * 2 ** even_s, 2 * factorial(even_s))
    zeta_coefficient *= bernoulli_number(even_s)
    return spectral_zeta_factor(even_s) * zeta_coefficient


def bernoulli_spectral_pi_coefficient(even_s):
    """Independent sum of Bernoulli evaluations at all eight eigenphases."""
    if type(even_s) is not int or even_s < 2 or even_s % 2:
        raise ValueError("a positive even s >= 2 is required")
    k = even_s // 2
    scale = Fraction((-1) ** (k + 1) * 2 ** even_s, 2 * factorial(even_s))
    return scale * sum(bernoulli_polynomial(even_s, Fraction(m, 30)) for m in EXPONENTS)


def root_permutation_zeta_factor(s):
    """240-root permutation spectrum, distinct from the reflection spectrum."""
    if type(s) is not int or s < 2:
        raise ValueError("an integer s >= 2 is required")
    return Fraction(8, 30 ** (s - 1))


def combined_zeta_factor(s):
    """The E8-derived root-permutation-plus-Cartan model, dimension 248.

    This direct sum is a verified representation of the cyclic Coxeter
    action.  Identification with a Lie-group adjoint lift, including signs
    on root spaces, is not asserted by this construction.
    """
    return root_permutation_zeta_factor(s) + spectral_zeta_factor(s)


def combined_pi_coefficient(even_s):
    """The rational pi**s coefficient in the combined model, even s>=2."""
    if type(even_s) is not int or even_s < 2 or even_s % 2:
        raise ValueError("a positive even s >= 2 is required")
    k = even_s // 2
    zeta_coefficient = Fraction((-1) ** (k + 1) * 2 ** even_s, 2 * factorial(even_s))
    zeta_coefficient *= bernoulli_number(even_s)
    return combined_zeta_factor(even_s) * zeta_coefficient


def combined_log_mellin_coefficients():
    """Coefficients of pi**2*log(p) in the derivative at s=2.

    The derivative equals the integral of
    (-log(x))*log(-log(x))*combined_kernel(x) over (0,1), since
    the undifferentiated normalized Mellin integral vanishes at s=2.
    """
    return {2: Fraction(-4, 45), 3: Fraction(-1, 15), 5: Fraction(-1, 18)}


def spectral_kernel(x):
    """Tr[C(I-xC)^-1] = -Phi_30'(x)/Phi_30(x), exactly for rational x."""
    x = Fraction(x)
    denominator = sum(Fraction(a) * x ** i for i, a in enumerate(PHI30))
    derivative = sum(Fraction(i * a) * x ** (i - 1) for i, a in enumerate(PHI30) if i)
    return -derivative / denominator


def combined_kernel(x):
    """Rational kernel for the 248-dimensional direct-sum model, x!=1."""
    x = Fraction(x)
    return 240 * x ** 29 / (1 - x ** 30) + spectral_kernel(x)


def restricted_cyclotomic_multiplicities(base_order=1680, target_order=30):
    """Spectrum of zeta_base**(base/target) under all base embeddings.

    In particular the 384-dimensional rational cyclotomic representation
    restricts to 48 copies of the actual eight-dimensional Coxeter module.
    The multiplicities are enumerated rather than inferred by matching
    dimensions.
    """
    if (type(base_order) is not int or type(target_order) is not int
            or base_order < 2 or target_order < 2 or base_order % target_order):
        raise ValueError("integer orders >=2 with target dividing base are required")
    out = {}
    for exponent in range(base_order):
        if gcd(exponent, base_order) == 1:
            residue = exponent % target_order
            out[residue] = out.get(residue, 0) + 1
    return dict(sorted(out.items()))


def receipt():
    """A deterministic, JSON-safe computation receipt, not a Lean proof."""
    root_set = set(roots())
    c = coxeter_matrix()
    cp = characteristic_polynomial(c)
    orbits = root_orbits()
    coefficients = [simple_root_coordinates(r) for r in root_set]
    traces = [coxeter_trace(k) for k in range(30)]
    multiplicities = restricted_cyclotomic_multiplicities()
    verified = (
        len(root_set) == 240
        and all(_dot(r, r) == 8 for r in root_set)
        and all(reflect(r, a) in root_set for r in root_set for a in SIMPLE_ROOTS)
        and all(all(x >= 0 for x in v) or all(x <= 0 for x in v) for v in coefficients)
        and cp == PHI30
        and matrix_power(c, 30) == identity()
        and all(matrix_power(c, k) != identity() for k in (1, 2, 3, 5, 6, 10, 15))
        and tuple(map(len, orbits)) == (30,) * 8
        and traces == [ramanujan_sum_30(k) for k in range(30)]
        and multiplicities == dict.fromkeys(EXPONENTS, 48)
    )
    if not verified:
        raise ArithmeticError("E8 construction did not pass exact checks")
    return {
        "kind": "exact_e8_coxeter_integral_bridge_v1",
        "verified_by": "integer and rational Python computation; not Lean",
        "roots": 240,
        "root_coordinate_scale": 2,
        "integer_roots": sum(all(x % 2 == 0 for x in r) for r in root_set),
        "half_integer_roots": sum(all(x % 2 for x in r) for r in root_set),
        "positive_roots_in_displayed_base": sum(all(x >= 0 for x in v) for v in coefficients),
        "reflection_dimension": 8,
        "lie_algebra_dimension": 248,
        "simple_roots_doubled": [list(r) for r in SIMPLE_ROOTS],
        "cartan_matrix": [list(row) for row in cartan_matrix()],
        "coxeter_matrix_simple_basis": [list(row) for row in c],
        "coxeter_order": 30,
        "characteristic_polynomial_low_to_high": list(cp),
        "exponents": list(EXPONENTS),
        "root_orbit_lengths": list(map(len, orbits)),
        "power_traces_0_to_29": traces,
        "spectral_kernel": "-Phi30'(x)/Phi30(x)",
        "reflection_spectral_integral": "zeta(s)*(2^(1-s)-1)*(3^(1-s)-1)*(5^(1-s)-1)",
        "integral_domain": "Re(s)>1; normalized by Gamma(s)",
        "root_permutation_spectral_integral": "8*30^(1-s)*zeta(s)",
        "pi_coefficients": {str(s): str(spectral_pi_coefficient(s)) for s in range(2, 14, 2)},
        "combined_model": {
            "name": "root-permutation-plus-Cartan spectral model",
            "dimension": 248,
            "scope": "verified cyclic direct sum; adjoint-lift identification is not claimed",
            "kernel": "240*x^29/(1-x^30)-Phi30'(x)/Phi30(x)",
            "normalized_mellin_integral": "zeta(s)*30^(1-s)*(8-(2^(s-1)-1)*(3^(s-1)-1)*(5^(s-1)-1))",
            "unique_real_zero_for_s_gt_1": "s=2",
            "sign": "positive for 1<s<2; negative for s>2",
            "zero_proof": "product of the three positive strictly increasing factors is strictly increasing; its value at s=2 is 1*2*4=8",
            "pi_coefficients": {str(s): str(combined_pi_coefficient(s)) for s in range(2, 14, 2)},
            "log_weighted_integral": "-pi^2*(16*log(2)+12*log(3)+10*log(5))/180",
            "log_weighted_pi_squared_coefficients": {str(p): str(c) for p, c in combined_log_mellin_coefficients().items()},
            "log_weighted_integral_numeric": pi**2 * sum(float(c) * log(p) for p, c in combined_log_mellin_coefficients().items()),
        },
        "cyclotomic_bridge": {
            "base_order": 1680,
            "power_to_coxeter_phase": 56,
            "identity": "(exp(2*pi*i/1680))^56=exp(2*pi*i/30)",
            "rational_cyclotomic_dimension": 384,
            "restriction_to_order_30": "48 copies of the 8-dimensional rational Coxeter module",
            "enumerated_restriction_multiplicities": {str(m): n for m, n in multiplicities.items()},
            "extension_degree_to_order_443520": 240,
            "limitation": "240 field conjugates are not thereby E8 roots; no categorical colimit is established",
        },
        "sources": [
            "https://www.math.utah.edu/~ptrapa/math-library/reeder/reeder-cyclotomic-root-lattices-2008.pdf",
            "https://arxiv.org/abs/0704.3091",
            "https://math.ucr.edu/home/baez/octonions/integers/integers_3.html",
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(receipt(), indent=2, sort_keys=True))
