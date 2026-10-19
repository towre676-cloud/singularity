"""Exact Hahn-coefficient stratification of monomial Moyal brackets.

Recovered from ``hahn_stratification_professional_push_v2.zip`` and the archived
``hahn_stratification_final_form_extracted.txt``. Coefficients are computed by
the finite integer falling-factorial formula, including every active odd layer.
The kappa=4 nonzero-Poisson rays are algebraically classified in that source;
the absence of higher-kappa nonzero-Poisson exact pairs is a conjecture supported
by its targeted degree-80 search, not a theorem or a new search performed here.

This module generates the proved rays and counterexamples and classifies any
supplied finite tuple exactly. It does not label that conjecture as proved.
"""
from fractions import Fraction
from math import comb, factorial


def _natural(value, name):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _exponents(a, b, c, d):
    return tuple(_natural(x, "monomial exponent") for x in (a, b, c, d))


def falling_factorial(n, k):
    """n*(n-1)*...*(n-k+1), with value zero for k>n."""
    _natural(n, "falling-factorial input")
    _natural(k, "falling-factorial order")
    if k > n:
        return 0
    out = 1
    for offset in range(k):
        out *= n-offset
    return out


def S(a, b, c, d, k):
    """Exact integer coefficient of Lambda^k(q^a p^b,q^c p^d)."""
    a, b, c, d = _exponents(a, b, c, d)
    _natural(k, "bracket order")
    ff = falling_factorial
    return sum((-1)**r * comb(k, r) * ff(a, k-r) * ff(b, r)
               * ff(c, r) * ff(d, k-r) for r in range(k+1))


def kappa(a, b, c, d):
    a, b, c, d = _exponents(a, b, c, d)
    return min(a, d) + min(b, c)


def poisson_scalar(a, b, c, d):
    a, b, c, d = _exponents(a, b, c, d)
    return a*d-b*c


def odd_coefficients(a, b, c, d):
    """All active odd correction layers, INCLUDING zero coefficients."""
    return {k: S(a, b, c, d, k) for k in range(3, kappa(a, b, c, d)+1, 2)}


def defect_terms(a, b, c, d):
    """Nonzero correction terms (hbar_power, q_power, p_power, Fraction).

    Their sum is [q^a*p^b,q^c*p^d]_star/(i*hbar) minus the Poisson bracket.
    """
    return [(k-1, a+c-k, b+d-k,
             Fraction((-1)**((k-1)//2) * sk, 2**(k-1) * factorial(k)))
            for k, sk in odd_coefficients(a, b, c, d).items() if sk]


def exact(a, b, c, d):
    return all(value == 0 for value in odd_coefficients(a, b, c, d).values())


def classify(a, b, c, d):
    terms = defect_terms(a, b, c, d)
    if not terms:
        return "EXACT"
    return "CENTRAL_DEFECT" if all(q == p == 0 for _, q, p, _ in terms) else "NONCENTRAL_DEFECT"


def classify_pair(a, b, c, d):
    """JSON-compatible complete finite correction certificate for one pair."""
    coeffs = odd_coefficients(a, b, c, d)
    terms = defect_terms(a, b, c, d)
    return {"exponents": [a, b, c, d], "kappa": kappa(a, b, c, d),
            "poisson_scalar": poisson_scalar(a, b, c, d), "classification": classify(a, b, c, d),
            "odd_coefficients": {str(k): value for k, value in coeffs.items()},
            "defect_terms": [{"hbar_power": h, "q_power": q, "p_power": p,
                              "coefficient": str(value)} for h, q, p, value in terms]}


def kappa4_ray_pairs(max_total_degree=80):
    """Generate proved nonzero-Poisson kappa=4 rays, bounded per monomial.

    Includes q/p duals and ordered reversals; overlap at t=1 is deduplicated.
    This is a family generator, not an exhaustive search outside kappa=4.
    """
    _natural(max_total_degree, "maximum total degree")
    pairs = set()
    for t in range(1, max_total_degree+1):
        for pair in ((1, 3, 3*t+2, t), (3, t, 1, 3*t+2)):
            a, b, c, d = pair
            for transformed in ((a, b, c, d), (b, a, d, c),
                                (c, d, a, b), (d, c, b, a)):
                if max(sum(transformed[:2]), sum(transformed[2:])) <= max_total_degree:
                    pairs.add(transformed)
    return sorted(pairs)


def is_kappa4_ray(a, b, c, d):
    """Recognize the classified kappa=4 nonzero-Poisson locus exactly."""
    if kappa(a, b, c, d) != 4 or poisson_scalar(a, b, c, d) == 0:
        return False
    # Exhaustive first active odd layer; at kappa=4 there is no S5 layer.
    return S(a, b, c, d, 3) == 0


def higher_order_decoy(t=1):
    """Family with S3=0 but a provably positive S5 for every integer t>=1."""
    _natural(t, "decoy parameter")
    if t == 0:
        raise ValueError("decoy parameter must be positive")
    exps = (1, 4, 3*t+2, 2*t)
    report = classify_pair(*exps)
    expected = 720*t*t*(3*t-1)*(3*t+1)*(3*t+2)
    report.update({"t": t, "expected_S5": expected,
                   "S3_zero": S(*exps, 3) == 0,
                   "S5_positive_identity": S(*exps, 5) == expected and expected > 0})
    return report


def receipt():
    """Fresh exact checks and generated rays; no global D=80 search claim."""
    rays = kappa4_ray_pairs(80)
    return {"schema": "perfectjet/hahn/1", "arithmetic": "exact integers and Fractions",
            "source": "recovered hahn_stratification_professional_push_v2.zip",
            "cubic_witness": classify_pair(3, 0, 0, 3),
            "quintic_tower": classify_pair(5, 0, 0, 5),
            "first_accidental_ray": classify_pair(1, 3, 5, 1),
            "degree80_generated_ray_pairs": len(rays),
            "generated_rays_exact": all(exact(*pair) and is_kappa4_ray(*pair) for pair in rays),
            "higher_order_decoys": [higher_order_decoy(t) for t in (1, 2, 3, 10)],
            "scope": "kappa=4 rays classified; global higher-kappa exclusion remains conjectural"}
