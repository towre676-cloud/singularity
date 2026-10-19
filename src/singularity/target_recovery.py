"""Exact target-specific recovery conditioning on affine admissible sets (NX08).

Problem.  A hidden state ``x`` in Q^d lies in the affine admissible set
``x = x_c + Q z`` with ``Q`` a rational d x k matrix of full column rank and
``z`` unrestricted.  Observations are ``y = H x + eta`` and the requested
target is ``t = G x``.  After subtracting the known centres, ``H0 = H Q`` and
``G0 = G Q``.  Noise lies in the declared ellipsoid ``eta^T R^-1 eta <= eps^2``
(``R`` is the positive-definite *shape* matrix, default identity), and target
error is measured by ``||e||_P^2 = e^T P e`` (``P`` positive definite, default
identity).  Write ``W = R^-1``.

Sharp amplification.  The squared target amplification is

    kappa_*^2 = min { alpha >= 0 : G0^T P G0 <= alpha H0^T W H0 }   (PSD order)

and is +infinity when no such alpha exists.  When some ``H0 z != 0`` this is
``sup ||G0 z||_P^2 / ||H0 z||_W^2``; when ``H0 = 0`` and ``G0 = 0`` it is 0.
``docs/research/TARGET_RECOVERY.md`` proves: (i) kappa_* is finite exactly when
``ker H0`` is contained in ``ker G0``; (ii) no decoder, linear or not, has worst
target error below ``eps * kappa_*``; (iii) the minimum-norm decoder returned by
:func:`minimum_norm_decoder` attains ``eps * kappa_*``.  The constant depends on
the admissible subspace, the target metric and the noise metric only; it does
not depend on the basis ``Q`` or on any state norm.

Exact evidence.  ``kappa_*^2`` is usually algebraic, so results are rational
brackets: a *lower witness* ``z`` (its exact ratio is <= kappa_*^2) and an
*upper certificate* ``alpha`` with an exact factorization
``alpha H0^T W H0 - G0^T P G0 = L D L^T``, ``L`` unit lower triangular and
``D >= 0`` (zero pivots allowed).  A failed factorization returns an exact
vector ``v`` with ``v^T S v < 0``.  Statuses are ``unobservable`` (with a
hidden-target witness), ``exact_sharp_constant``, ``bracketed_sharp_constant``
and ``resource_limit`` (a valid but wider bracket).  Floating point is never
used.  Public exact numbers are ``int`` or ``Fraction``; ``bool``, ``float``
and ``str`` raise ``TypeError`` and wrong values or shapes raise ``ValueError``.

Sensor layouts (NX08-B) choose a subset of a bounded catalogue; adding a
sensor never increases kappa_* (block-diagonal noise shapes), which justifies
the pruned search.  Forecast and thermal adapters (NX08-C) build ``G F^tau``
and ``C A^t`` rows for a fixed known linear transition; uncertainty in the
transition itself is outside this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Mapping

SCHEMA = "singularity.target-recovery/1"
LAYOUT_SCHEMA = "singularity.target-sensor-layout/1"
MAX_CATALOGUE = 12
MAX_ADMISSIBLE_DIMENSION = 16

__all__ = [
    "SCHEMA", "LAYOUT_SCHEMA", "TargetRecoveryProblem", "PSDCertificate", "NegativeWitness",
    "psd_certificate", "verify_psd_certificate", "Identifiability", "target_identifiability",
    "amplification_form", "amplification_ratio", "AmplificationCertificate",
    "certify_target_amplification", "AmplificationBracket", "bracket_target_amplification",
    "minimum_norm_decoder", "DecoderCertificate", "certify_decoder_norm", "bracket_decoder_norm",
    "decoder_ratio", "TargetEstimate", "recover_target", "AdversarialWitness",
    "adversarial_witness", "target_recovery_receipt", "verify_target_recovery_receipt",
    "SensorOption", "layout_problem", "LayoutResult", "cheapest_identifying_layout",
    "cheapest_conditioned_layout", "conditioning_frontier", "layout_table",
    "linear_forecast_problem", "matrix_power", "thermal_target_problem",
]


# ---------------------------------------------------------------------------
# Exact validation and elementary linear algebra
# ---------------------------------------------------------------------------

def _q(value, name="value"):
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(f"{name} must be an int or Fraction, not {type(value).__name__}")
    return Fraction(value)


def _count(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _seq(value, name):
    if isinstance(value, (str, bytes)) or isinstance(value, Mapping):
        raise TypeError(f"{name} must be a sequence")
    try:
        return tuple(value)
    except TypeError:
        raise TypeError(f"{name} must be a sequence") from None


def _vector(values, size, name="vector"):
    result = tuple(_q(x, name) for x in _seq(values, name))
    if size is not None and len(result) != size:
        raise ValueError(f"{name} must have length {size}")
    return result


def _matrix(values, rows, columns, name="matrix"):
    result = tuple(_vector(r, columns, name) for r in _seq(values, name))
    if rows is not None and len(result) != rows:
        raise ValueError(f"{name} must have {rows} rows")
    return result


def _zeros(rows, columns):
    return tuple((Fraction(0),) * columns for _ in range(rows))


def _identity(n):
    return tuple(tuple(Fraction(int(i == j)) for j in range(n)) for i in range(n))


def _transpose(a, columns):
    return tuple(tuple(row[j] for row in a) for j in range(columns))


def _matmul(a, b, columns):
    """a (r x s) times b (s x columns); columns is explicit for empty shapes."""
    return tuple(tuple(sum((row[k] * b[k][j] for k in range(len(row))), Fraction(0))
                       for j in range(columns)) for row in a)


def _matvec(a, v):
    return tuple(sum((x * y for x, y in zip(row, v)), Fraction(0)) for row in a)


def _dot(a, b):
    return sum((x * y for x, y in zip(a, b)), Fraction(0))


def _quad(a, v):
    return _dot(v, _matvec(a, v))


def _sub(a, b):
    return tuple(tuple(x - y for x, y in zip(r, s)) for r, s in zip(a, b))


def _scale(c, a):
    return tuple(tuple(c * x for x in row) for row in a)


def _symmetric(a, name):
    n = len(a)
    if any(len(row) != n for row in a):
        raise ValueError(f"{name} must be square")
    if any(a[i][j] != a[j][i] for i in range(n) for j in range(i)):
        raise ValueError(f"{name} must be symmetric")
    return a


def _rref(rows, columns):
    a = [list(r) for r in rows]
    pivots = []
    r = 0
    for c in range(columns):
        p = next((i for i in range(r, len(a)) if a[i][c] != 0), None)
        if p is None:
            continue
        a[r], a[p] = a[p], a[r]
        inv = 1 / a[r][c]
        a[r] = [x * inv for x in a[r]]
        for i in range(len(a)):
            if i != r and a[i][c] != 0:
                f = a[i][c]
                a[i] = [x - f * y for x, y in zip(a[i], a[r])]
        pivots.append(c)
        r += 1
        if r == len(a):
            break
    return [tuple(x) for x in a[:r]], pivots


def _rank(rows, columns):
    return len(_rref(rows, columns)[1])


def _primitive(v):
    """Scale a nonzero rational vector to a primitive integer vector."""
    from math import gcd
    lcm = 1
    for x in v:
        lcm = lcm * x.denominator // gcd(lcm, x.denominator)
    ints = [int(x * lcm) for x in v]
    g = 0
    for x in ints:
        g = gcd(g, abs(x))
    g = g or 1
    first = next((x for x in ints if x), 1)
    sign = -1 if first < 0 else 1
    return tuple(Fraction(sign * x // g) for x in ints)


def _nullspace(rows, columns):
    reduced, pivots = _rref(rows, columns)
    free = [c for c in range(columns) if c not in pivots]
    basis = []
    for f in free:
        v = [Fraction(0)] * columns
        v[f] = Fraction(1)
        for row, p in zip(reduced, pivots):
            v[p] = -row[f]
        basis.append(_primitive(tuple(v)))
    return tuple(basis)


def _independent_rows(rows, columns):
    """Indices of the first maximal linearly independent subset, in order."""
    chosen, echelon = [], []
    for index, row in enumerate(rows):
        candidate = echelon + [row]
        if _rank(candidate, columns) > len(echelon):
            chosen.append(index)
            echelon = candidate
    return tuple(chosen)


def _inverse(a):
    n = len(a)
    aug = [list(row) + [Fraction(int(i == j)) for j in range(n)] for i, row in enumerate(a)]
    for c in range(n):
        p = next((i for i in range(c, n) if aug[i][c] != 0), None)
        if p is None:
            raise ValueError("matrix is singular")
        aug[c], aug[p] = aug[p], aug[c]
        inv = 1 / aug[c][c]
        aug[c] = [x * inv for x in aug[c]]
        for i in range(n):
            if i != c and aug[i][c] != 0:
                f = aug[i][c]
                aug[i] = [x - f * y for x, y in zip(aug[i], aug[c])]
    return tuple(tuple(row[n:]) for row in aug)


def _solve(a, b):
    """Solve a x = b for invertible square a."""
    return _matvec(_inverse(a), b)


# ---------------------------------------------------------------------------
# Exact PSD certificates with zero pivots
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PSDCertificate:
    """S = L diag(D) L^T with L unit lower triangular and every D entry >= 0."""
    lower: tuple
    diagonal: tuple

    @property
    def zero_pivots(self):
        return tuple(i for i, d in enumerate(self.diagonal) if d == 0)


@dataclass(frozen=True)
class NegativeWitness:
    """An exact vector with vector^T S vector = value < 0."""
    vector: tuple
    value: Fraction


def psd_certificate(matrix):
    """Return a :class:`PSDCertificate` or a :class:`NegativeWitness`.

    Symmetric elimination in the given order.  A positive pivot is eliminated;
    a zero pivot is accepted only if its whole remaining column is zero (for a
    PSD matrix a zero diagonal entry forces this) and then contributes a zero
    diagonal entry with an identity column of L; a negative pivot, or a zero
    pivot with a nonzero remaining entry, yields an exact negative direction.
    """
    s = _symmetric(_matrix(matrix, None, None, "symmetric matrix"), "symmetric matrix")
    n = len(s)
    if any(len(row) != n for row in s):
        raise ValueError("symmetric matrix must be square")
    a = [list(row) for row in s]
    lower = [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]
    diagonal = []
    positive = []
    for k in range(n):
        p = a[k][k]
        if p > 0:
            for i in range(k + 1, n):
                lower[i][k] = a[i][k] / p
            for i in range(k + 1, n):
                if lower[i][k]:
                    f = lower[i][k]
                    for j in range(k + 1, n):
                        a[i][j] -= f * a[k][j]
            for i in range(k + 1, n):
                a[i][k] = a[k][i] = Fraction(0)
            diagonal.append(p)
            positive.append(k)
            continue
        if p == 0:
            off = next((i for i in range(k + 1, n) if a[i][k] != 0), None)
            if off is None:
                diagonal.append(Fraction(0))
                continue
            t = -(abs(a[off][off]) + 1) / (2 * a[off][k])
            v = {k: t, off: Fraction(1)}
        else:
            v = {k: Fraction(1)}
        return _lift_witness(s, positive, v)
    return PSDCertificate(tuple(tuple(r) for r in lower), tuple(diagonal))


def _lift_witness(s, positive, v):
    n = len(s)
    z = [Fraction(0)] * n
    for i, x in v.items():
        z[i] = x
    if positive:
        sii = tuple(tuple(s[i][j] for j in positive) for i in positive)
        rhs = tuple(-sum((s[i][j] * x for j, x in v.items()), Fraction(0)) for i in positive)
        for i, x in zip(positive, _solve(sii, rhs)):
            z[i] = x
    z = _primitive(tuple(z))
    value = _quad(s, z)
    if value >= 0:  # pragma: no cover - would indicate an elimination bug
        raise RuntimeError("internal error: negative witness failed")
    return NegativeWitness(z, value)


def verify_psd_certificate(matrix, certificate):
    """Independent identity check; never re-runs the elimination."""
    if not isinstance(certificate, PSDCertificate):
        return False
    try:
        s = _matrix(matrix, None, None)
        n = len(s)
        lower = _matrix(certificate.lower, n, n)
        diagonal = _vector(certificate.diagonal, n)
    except (TypeError, ValueError):
        return False
    if any(len(r) != n for r in s):
        return False
    for i in range(n):
        if lower[i][i] != 1 or any(lower[i][j] != 0 for j in range(i + 1, n)):
            return False
    if any(d < 0 for d in diagonal):
        return False
    for i in range(n):
        for j in range(n):
            if sum((lower[i][k] * diagonal[k] * lower[j][k] for k in range(n)), Fraction(0)) != s[i][j]:
                return False
    return True


def _positive_definite(a, name):
    a = _symmetric(a, name)
    cert = psd_certificate(a)
    if not isinstance(cert, PSDCertificate) or cert.zero_pivots:
        raise ValueError(f"{name} must be positive definite")
    return a


# ---------------------------------------------------------------------------
# Problem
# ---------------------------------------------------------------------------

def _units(units, d, m, p):
    if units is None:
        return ()
    if not isinstance(units, Mapping):
        raise TypeError("units must be a mapping")
    sizes = {"state": d, "observations": m, "target": p}
    result = []
    for key in sorted(units):
        if not isinstance(key, str):
            raise TypeError("unit keys must be strings")
        value = units[key]
        if key in sizes:
            if isinstance(value, str):
                value = (value,) * sizes[key]
            value = _seq(value, f"units[{key}]")
            if len(value) != sizes[key]:
                raise ValueError(f"units[{key}] must have length {sizes[key]}")
            if any(not isinstance(u, str) or not u for u in value):
                raise TypeError(f"units[{key}] entries must be nonempty strings")
        elif not isinstance(value, str):
            raise TypeError(f"units[{key}] must be a string")
        result.append((key, value))
    return tuple(result)


@dataclass(frozen=True)
class TargetRecoveryProblem:
    """Validated exact problem; inputs are stored in their original order.

    ``observations`` H is m x d, ``target`` G is p x d, ``admissible_basis`` Q
    is d x k with full column rank (default identity), ``centre`` x_c has
    length d (default zero), ``observation_metric`` R (m x m) is the noise
    ellipsoid shape, ``target_metric`` P (p x p) the target error metric.
    ``state_dimension`` is needed only when no row determines d.
    ``units`` may give ``state``/``observations``/``target`` (a string or one
    string per coordinate) and further free-text string fields.
    """
    observations: tuple
    target: tuple
    admissible_basis: tuple
    centre: tuple
    observation_metric: tuple
    target_metric: tuple
    units: tuple
    state_dimension: int
    admissible_dimension: int

    def __init__(self, observations, target, admissible_basis=None, observation_metric=None,
                 units=None, *, centre=None, target_metric=None, state_dimension=None,
                 admissible_dimension=None):
        raw_h = _seq(observations, "observations")
        raw_g = _seq(target, "target")
        d = None
        if state_dimension is not None:
            d = _count(state_dimension, "state_dimension")
        for rows in (raw_h, raw_g):
            if rows:
                width = len(_seq(rows[0], "row"))
                if d is None:
                    d = width
        if d is None and admissible_basis is not None:
            d = len(_seq(admissible_basis, "admissible_basis"))
        if d is None and centre is not None:
            d = len(_seq(centre, "centre"))
        if d is None:
            raise ValueError("state_dimension is required when no row determines it")
        h = _matrix(raw_h, None, d, "observations")
        g = _matrix(raw_g, None, d, "target")
        m, p = len(h), len(g)
        if admissible_basis is None:
            q = _identity(d)
            k = d
        else:
            raw_q = _seq(admissible_basis, "admissible_basis")
            if len(raw_q) != d:
                raise ValueError("admissible_basis must have one row per state coordinate")
            if admissible_dimension is not None:
                k = _count(admissible_dimension, "admissible_dimension")
            elif d:
                k = len(_seq(raw_q[0], "admissible_basis row"))
            else:
                raise ValueError("admissible_dimension is required when the state dimension is zero")
            q = _matrix(raw_q, d, k, "admissible_basis")
        if admissible_dimension is not None and k != admissible_dimension:
            raise ValueError("admissible_dimension disagrees with the basis")
        if k > MAX_ADMISSIBLE_DIMENSION:
            raise ValueError(f"admissible dimension exceeds the declared limit {MAX_ADMISSIBLE_DIMENSION}")
        if _rank(_transpose(q, k), d) != k:
            raise ValueError("admissible_basis must have full column rank")
        x_c = (Fraction(0),) * d if centre is None else _vector(centre, d, "centre")
        r = _identity(m) if observation_metric is None else _positive_definite(
            _matrix(observation_metric, m, m, "observation_metric"), "observation_metric")
        pm = _identity(p) if target_metric is None else _positive_definite(
            _matrix(target_metric, p, p, "target_metric"), "target_metric")
        for name, value in (("observations", h), ("target", g), ("admissible_basis", q),
                            ("centre", x_c), ("observation_metric", r), ("target_metric", pm),
                            ("units", _units(units, d, m, p)), ("state_dimension", d),
                            ("admissible_dimension", k)):
            object.__setattr__(self, name, value)

    @property
    def observation_count(self):
        return len(self.observations)

    @property
    def target_count(self):
        return len(self.target)

    @property
    def reduced_observations(self):
        """H0 = H Q (m x k)."""
        return _matmul(self.observations, self.admissible_basis, self.admissible_dimension)

    @property
    def reduced_target(self):
        """G0 = G Q (p x k)."""
        return _matmul(self.target, self.admissible_basis, self.admissible_dimension)

    @property
    def observation_weight(self):
        """W = R^-1, the whitened observation weighting."""
        return _inverse(self.observation_metric) if self.observation_metric else ()

    def information_form(self):
        """A = H0^T W H0 and B = G0^T P G0 (both k x k)."""
        k = self.admissible_dimension
        h0, g0 = self.reduced_observations, self.reduced_target
        a = _matmul(_transpose(h0, k), _matmul(self.observation_weight, h0, k), k)
        b = _matmul(_transpose(g0, k), _matmul(self.target_metric, g0, k), k)
        return a, b

    def unit_map(self):
        return dict(self.units)


def _require(problem):
    if not isinstance(problem, TargetRecoveryProblem):
        raise TypeError("problem must be a TargetRecoveryProblem")
    return problem


# ---------------------------------------------------------------------------
# NX08-A: identifiability, certificates and brackets
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Identifiability:
    """``identifiable`` carries a row-space decoder L with G0 = L H0;
    ``unobservable`` carries z with H0 z = 0 and G0 z != 0."""
    status: str
    rank: int
    pivot_rows: tuple
    kernel_basis: tuple
    hidden_witness: tuple | None
    hidden_state_direction: tuple | None
    decoder: tuple | None


def target_identifiability(problem):
    problem = _require(problem)
    k = problem.admissible_dimension
    h0, g0 = problem.reduced_observations, problem.reduced_target
    pivots = _independent_rows(h0, k)
    kernel = _nullspace(h0, k)
    for z in kernel:
        if any(_matvec(g0, z)):
            return Identifiability("unobservable", len(pivots), pivots, kernel, z,
                                   _matvec(problem.admissible_basis, z), None)
    # Row-space coordinates: g = c Hp with Hp of full row rank.
    hp = tuple(h0[i] for i in pivots)
    gram = _matmul(hp, _transpose(hp, k), len(hp))
    decoder = []
    for g in g0:
        c = _solve(gram, _matvec(hp, g)) if hp else ()
        full = [Fraction(0)] * problem.observation_count
        for i, x in zip(pivots, c):
            full[i] = x
        decoder.append(tuple(full))
    decoder = tuple(decoder)
    if _matmul(decoder, h0, k) != g0:  # pragma: no cover
        raise RuntimeError("internal error: row-space decoder identity failed")
    return Identifiability("identifiable", len(pivots), pivots, kernel, None, None, decoder)


def amplification_form(problem, alpha_squared):
    """S(alpha) = alpha H0^T W H0 - G0^T P G0."""
    problem = _require(problem)
    alpha = _q(alpha_squared, "alpha_squared")
    if alpha < 0:
        raise ValueError("alpha_squared must be nonnegative")
    a, b = problem.information_form()
    return _sub(_scale(alpha, a), b)


def amplification_ratio(problem, z):
    """||G0 z||_P^2 / ||H0 z||_W^2, or None when H0 z = 0."""
    problem = _require(problem)
    z = _vector(z, problem.admissible_dimension, "z")
    a, b = problem.information_form()
    den = _quad(a, z)
    return None if den == 0 else _quad(b, z) / den


@dataclass(frozen=True)
class AmplificationCertificate:
    """``certified_upper_bound`` (kappa_*^2 <= alpha) or ``refuted``
    (witness z with ratio > alpha, or a hidden-target witness)."""
    status: str
    alpha_squared: Fraction
    certificate: PSDCertificate | None
    witness: tuple | None
    witness_ratio: Fraction | None


def certify_target_amplification(problem, alpha_squared):
    problem = _require(problem)
    alpha = _q(alpha_squared, "alpha_squared")
    s = amplification_form(problem, alpha)
    cert = psd_certificate(s)
    if isinstance(cert, PSDCertificate):
        return AmplificationCertificate("certified_upper_bound", alpha, cert, None, None)
    return AmplificationCertificate("refuted", alpha, None, cert.vector,
                                    amplification_ratio(problem, cert.vector))


@dataclass(frozen=True)
class PencilBracket:
    status: str
    lower: Fraction
    upper: Fraction
    lower_witness: tuple | None
    upper_certificate: PSDCertificate
    steps: int


def _simplest_between(lo, hi):
    """The rational of least denominator in the closed interval [lo, hi], lo <= hi."""
    if lo <= 0 <= hi:
        return Fraction(0)
    from math import floor
    a = floor(lo)
    if Fraction(a) == lo:
        return Fraction(a)
    if a + 1 <= hi:
        return Fraction(a + 1)
    inner = _simplest_between(1 / (hi - a), 1 / (lo - a))
    return a + 1 / inner


def _bracket_pencil(a, b, tolerance, max_steps, seeds=()):
    """Bracket max v^T B v / v^T A v given ker A in ker B (both PSD)."""
    n = len(a)
    pivots = _independent_rows(a, n)
    z = _transpose(tuple(a[i] for i in pivots), n) if pivots else ()  # n x r basis of range A
    r = len(pivots)

    def form(alpha):
        return _sub(_scale(alpha, a), b)

    def ratio(v):
        den = _quad(a, v)
        return None if den == 0 else _quad(b, v) / den

    if r == 0:
        cert = psd_certificate(form(Fraction(0)))
        if not isinstance(cert, PSDCertificate):  # pragma: no cover
            raise RuntimeError("internal error: kernel condition was not checked")
        return PencilBracket("exact_sharp_constant", Fraction(0), Fraction(0), None, cert, 0)
    ar = _matmul(_transpose(z, r), _matmul(a, z, r), r)
    br = _matmul(_transpose(z, r), _matmul(b, z, r), r)
    m = _matmul(_inverse(ar), br, r)
    upper = sum((m[i][i] for i in range(r)), Fraction(0))
    upper_cert = psd_certificate(form(upper))
    if not isinstance(upper_cert, PSDCertificate):  # pragma: no cover
        raise RuntimeError("internal error: trace bound failed")
    # Lower witnesses: coordinate directions, seeds and a few rounded power steps.
    candidates = [tuple(z[i][j] for i in range(n)) for j in range(r)]
    candidates.extend(seeds)
    # Exact columns of M = Ar^-1 Br: for a single target row (rank-one Br) any
    # nonzero column is the exact maximizer, so scalar targets close exactly.
    candidates.extend(_matvec(z, tuple(m[i][j] for i in range(r))) for j in range(r))
    w = tuple(Fraction(1) for _ in range(r))
    for _ in range(12):
        w = _matvec(m, w)
        scale = max((abs(x) for x in w), default=Fraction(0))
        if scale == 0:
            break
        w = tuple((x / scale).limit_denominator(10 ** 6) for x in w)
        candidates.append(_matvec(z, w))
    best, best_v = None, None
    for v in candidates:
        value = ratio(v)
        if value is not None and (best is None or value > best):
            best, best_v = value, _primitive(v)
    lower, lower_v = best, best_v
    steps = 0
    if lower == upper:
        return PencilBracket("exact_sharp_constant", lower, upper, lower_v, upper_cert, 0)
    cert = psd_certificate(form(lower))
    if isinstance(cert, PSDCertificate):
        return PencilBracket("exact_sharp_constant", lower, lower, lower_v, cert, 0)

    def snap():
        # If the simplest rational c in the bracket is the sharp value, S(c) is
        # PSD and singular on the range of A; a null vector v with v^T A v > 0
        # then has ratio exactly c.  Both facts are checked exactly.
        c = _simplest_between(lower, upper)
        if c in (lower, upper):
            return None
        c_cert = psd_certificate(form(c))
        if not isinstance(c_cert, PSDCertificate):
            return None
        for v in _nullspace(form(c), n):
            if ratio(v) == c:
                return PencilBracket("exact_sharp_constant", c, c, v, c_cert, steps)
        return None

    while upper - lower > tolerance and steps < max_steps:
        if steps % 8 == 4:
            snapped = snap()
            if snapped is not None:
                return snapped
        third = (upper - lower) / 3
        mid = _simplest_between(lower + third, upper - third)
        steps += 1
        cert = psd_certificate(form(mid))
        if isinstance(cert, PSDCertificate):
            upper, upper_cert = mid, cert
        else:
            value = ratio(cert.vector)
            if value is None or value <= mid:  # pragma: no cover
                raise RuntimeError("internal error: negative witness has no ratio")
            lower, lower_v = value, cert.vector
            if lower >= upper:  # pragma: no cover
                raise RuntimeError("internal error: bracket crossed")
    if upper != lower:
        snapped = snap()
        if snapped is not None:
            return snapped
    status = "bracketed_sharp_constant" if upper - lower <= tolerance else "resource_limit"
    return PencilBracket(status, lower, upper, lower_v, upper_cert, steps)


def _tolerance(tolerance, max_steps):
    tolerance = _q(tolerance, "tolerance")
    if tolerance < 0:
        raise ValueError("tolerance must be nonnegative")
    return tolerance, _count(max_steps, "max_steps")


@dataclass(frozen=True)
class AmplificationBracket:
    """lower <= kappa_*^2 <= upper; for ``unobservable`` both are None."""
    status: str
    lower: Fraction | None
    upper: Fraction | None
    lower_witness: tuple | None
    upper_certificate: PSDCertificate | None
    hidden_witness: tuple | None
    steps: int

    @property
    def exact(self):
        return self.status == "exact_sharp_constant"


def bracket_target_amplification(problem, tolerance=Fraction(1, 10 ** 6), max_steps=200):
    """Rational bracket on kappa_*^2 with a PSD upper certificate and a lower witness."""
    problem = _require(problem)
    tolerance, max_steps = _tolerance(tolerance, max_steps)
    ident = target_identifiability(problem)
    if ident.status == "unobservable":
        return AmplificationBracket("unobservable", None, None, None, None, ident.hidden_witness, 0)
    a, b = problem.information_form()
    result = _bracket_pencil(a, b, tolerance, max_steps)
    return AmplificationBracket(result.status, result.lower, result.upper, result.lower_witness,
                                result.upper_certificate, None, result.steps)


def minimum_norm_decoder(problem):
    """L* = G0 Z (Z^T A Z)^-1 Z^T H0^T W, Z a basis of the row space of H0.

    L* H0 = G0 and ||L*||_{W->P} = kappa_*: it acts as the target map on the
    observation image and annihilates its W-orthogonal complement.
    """
    problem = _require(problem)
    ident = target_identifiability(problem)
    if ident.status != "identifiable":
        raise ValueError("target is unobservable on the admissible set")
    k, m = problem.admissible_dimension, problem.observation_count
    h0, g0 = problem.reduced_observations, problem.reduced_target
    if not ident.pivot_rows:
        return _zeros(problem.target_count, m)
    r = len(ident.pivot_rows)
    z = _transpose(tuple(h0[i] for i in ident.pivot_rows), k)
    hz = _matmul(h0, z, r)  # m x r
    w = problem.observation_weight
    ar = _matmul(_transpose(hz, r), _matmul(w, hz, r), r)
    right = _matmul(_inverse(ar), _matmul(_transpose(hz, r), w, m), m)  # r x m
    decoder = _matmul(_matmul(g0, z, r), right, m)
    if _matmul(decoder, h0, k) != g0:  # pragma: no cover
        raise RuntimeError("internal error: minimum-norm decoder identity failed")
    return decoder


def _decoder(problem, decoder):
    decoder = _matrix(decoder, problem.target_count, problem.observation_count, "decoder")
    if _matmul(decoder, problem.reduced_observations, problem.admissible_dimension) != problem.reduced_target:
        raise ValueError("decoder does not satisfy G0 = L H0")
    return decoder


def _decoder_forms(problem, decoder):
    m = problem.observation_count
    b = _matmul(_transpose(decoder, m), _matmul(problem.target_metric, decoder, m), m)
    return problem.observation_weight, b


def decoder_ratio(problem, decoder, noise):
    """||L eta||_P^2 / ||eta||_W^2 for a nonzero noise vector."""
    problem = _require(problem)
    decoder = _decoder(problem, decoder)
    noise = _vector(noise, problem.observation_count, "noise")
    w, b = _decoder_forms(problem, decoder)
    den = _quad(w, noise)
    if den == 0:
        raise ValueError("noise must be nonzero")
    return _quad(b, noise) / den


@dataclass(frozen=True)
class DecoderCertificate:
    """beta_squared W - L^T P L = lower diag(D) lower^T: ||L||^2_{W->P} <= beta^2."""
    decoder: tuple
    beta_squared: Fraction
    certificate: PSDCertificate


def certify_decoder_norm(problem, decoder, beta_squared):
    """Return a :class:`DecoderCertificate` or a :class:`NegativeWitness` noise vector."""
    problem = _require(problem)
    decoder = _decoder(problem, decoder)
    beta = _q(beta_squared, "beta_squared")
    if beta < 0:
        raise ValueError("beta_squared must be nonnegative")
    w, b = _decoder_forms(problem, decoder)
    cert = psd_certificate(_sub(_scale(beta, w), b))
    if isinstance(cert, PSDCertificate):
        return DecoderCertificate(decoder, beta, cert)
    return cert


def bracket_decoder_norm(problem, decoder, tolerance=Fraction(1, 10 ** 6), max_steps=200):
    """Bracket the actual worst-case squared gain of a chosen decoder."""
    problem = _require(problem)
    decoder = _decoder(problem, decoder)
    tolerance, max_steps = _tolerance(tolerance, max_steps)
    w, b = _decoder_forms(problem, decoder)
    return _bracket_pencil(w, b, tolerance, max_steps)


@dataclass(frozen=True)
class TargetEstimate:
    """estimate = G x_c + L (y - H x_c); ||estimate - t||_P^2 <= beta^2 eps^2."""
    estimate: tuple
    error_squared_per_noise_squared: Fraction
    error_squared_bound: Fraction | None


def recover_target(problem, observed, certificate, noise_radius_squared=None):
    problem = _require(problem)
    if not isinstance(certificate, DecoderCertificate):
        raise TypeError("certificate must be a DecoderCertificate")
    decoder = _decoder(problem, certificate.decoder)
    w, b = _decoder_forms(problem, decoder)
    if not verify_psd_certificate(_sub(_scale(certificate.beta_squared, w), b), certificate.certificate):
        raise ValueError("decoder norm certificate does not verify")
    y = _vector(observed, problem.observation_count, "observed")
    centre_y = _matvec(problem.observations, problem.centre)
    centre_t = _matvec(problem.target, problem.centre)
    innovation = tuple(a - c for a, c in zip(y, centre_y))
    estimate = tuple(c + x for c, x in zip(centre_t, _matvec(decoder, innovation)))
    bound = None
    if noise_radius_squared is not None:
        eps2 = _q(noise_radius_squared, "noise_radius_squared")
        if eps2 < 0:
            raise ValueError("noise_radius_squared must be nonnegative")
        bound = certificate.beta_squared * eps2
    return TargetEstimate(estimate, certificate.beta_squared, bound)


@dataclass(frozen=True)
class AdversarialWitness:
    """Two admissible states with identical noisy observations.

    ``state_plus = x_c + Q z`` with noise ``-H0 z`` and ``state_minus = x_c - Q z``
    with noise ``+H0 z`` both produce ``observed = H x_c``.  Their targets differ by
    ``2 G0 z``, so every decoder errs by at least ``||G0 z||_P`` on one of them,
    with ``noise_squared = ||H0 z||_W^2``.  ``decoder_errors_squared`` are the
    attained errors of the supplied decoder on the two states.
    """
    z: tuple
    state_plus: tuple
    state_minus: tuple
    noise_plus: tuple
    noise_minus: tuple
    observed: tuple
    noise_squared: Fraction
    target_gap_squared: Fraction
    ratio: Fraction
    decoder_errors_squared: tuple | None


def adversarial_witness(problem, z, decoder=None):
    problem = _require(problem)
    k = problem.admissible_dimension
    z = _vector(z, k, "z")
    h0z = _matvec(problem.reduced_observations, z)
    g0z = _matvec(problem.reduced_target, z)
    w = problem.observation_weight
    noise2 = _quad(w, h0z)
    if noise2 == 0:
        raise ValueError("z must be visible (H0 z != 0); invisible targets use the hidden witness")
    qz = _matvec(problem.admissible_basis, z)
    plus = tuple(c + x for c, x in zip(problem.centre, qz))
    minus = tuple(c - x for c, x in zip(problem.centre, qz))
    observed = _matvec(problem.observations, problem.centre)
    gap2 = _quad(problem.target_metric, g0z)
    errors = None
    if decoder is not None:
        decoder = _decoder(problem, decoder)
        centre_t = _matvec(problem.target, problem.centre)
        errs = []
        for state, noise in ((plus, tuple(-x for x in h0z)), (minus, h0z)):
            y = tuple(a + e for a, e in zip(_matvec(problem.observations, state), noise))
            innov = tuple(a - c for a, c in zip(y, observed))
            est = tuple(c + x for c, x in zip(centre_t, _matvec(decoder, innov)))
            true = _matvec(problem.target, state)
            errs.append(_quad(problem.target_metric, tuple(e - t for e, t in zip(est, true))))
        errors = tuple(errs)
    return AdversarialWitness(z, plus, minus, tuple(-x for x in h0z), h0z, observed,
                              noise2, gap2, gap2 / noise2, errors)


# ---------------------------------------------------------------------------
# Receipt: singularity.target-recovery/1
# ---------------------------------------------------------------------------

def _enc_q(x):
    return [x.numerator, x.denominator]


def _enc_v(v):
    return [_enc_q(x) for x in v]


def _enc_m(a, rows, columns):
    return {"rows": rows, "columns": columns, "entries": [_enc_v(r) for r in a]}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _problem_json(problem):
    d, k = problem.state_dimension, problem.admissible_dimension
    m, p = problem.observation_count, problem.target_count
    return {
        "observations": _enc_m(problem.observations, m, d),
        "target": _enc_m(problem.target, p, d),
        "admissible_basis": _enc_m(problem.admissible_basis, d, k),
        "centre": _enc_v(problem.centre),
        "observation_metric": _enc_m(problem.observation_metric, m, m),
        "observation_metric_semantics": "ellipsoid shape R: eta^T R^-1 eta <= eps^2",
        "target_metric": _enc_m(problem.target_metric, p, p),
        "target_metric_semantics": "target error norm ||e||_P^2 = e^T P e",
        "units": {key: (list(v) if isinstance(v, tuple) else v) for key, v in problem.units},
    }


def target_recovery_receipt(problem, bracket=None, decoder_certificate=None, source=None):
    """Portable exact receipt with rationals as [numerator, denominator]."""
    problem = _require(problem)
    if bracket is None:
        bracket = bracket_target_amplification(problem)
    if not isinstance(bracket, AmplificationBracket):
        raise TypeError("bracket must be an AmplificationBracket")
    if source is not None and not isinstance(source, Mapping):
        raise TypeError("source must be a mapping")
    k, m = problem.admissible_dimension, problem.observation_count
    pj = _problem_json(problem)
    receipt = {
        "schema": SCHEMA,
        "problem": pj,
        "problem_sha256": _digest(pj),
        "admissible_basis_sha256": _digest(pj["admissible_basis"]),
        "status": bracket.status,
        "source": dict(source) if source else {},
    }
    if bracket.status == "unobservable":
        receipt["hidden_witness"] = _enc_v(bracket.hidden_witness)
        return receipt
    ident = target_identifiability(problem)
    receipt["identifiability"] = {"rank": ident.rank, "pivot_rows": list(ident.pivot_rows),
                                  "kernel_basis": [_enc_v(v) for v in ident.kernel_basis],
                                  "row_space_decoder": _enc_m(ident.decoder, problem.target_count, m)}
    receipt["amplification_squared"] = {
        "lower": _enc_q(bracket.lower), "upper": _enc_q(bracket.upper),
        "lower_witness": None if bracket.lower_witness is None else _enc_v(bracket.lower_witness),
        "upper_ldl": {"lower": _enc_m(bracket.upper_certificate.lower, k, k),
                      "diagonal": _enc_v(bracket.upper_certificate.diagonal)},
        "steps": bracket.steps,
    }
    if decoder_certificate is not None:
        if not isinstance(decoder_certificate, DecoderCertificate):
            raise TypeError("decoder_certificate must be a DecoderCertificate")
        receipt["decoder"] = {"matrix": _enc_m(decoder_certificate.decoder, problem.target_count, m),
                              "beta_squared": _enc_q(decoder_certificate.beta_squared),
                              "ldl": {"lower": _enc_m(decoder_certificate.certificate.lower, m, m),
                                      "diagonal": _enc_v(decoder_certificate.certificate.diagonal)}}
    return receipt


class _ReceiptError(ValueError):
    pass


def _dec_q(x):
    if (not isinstance(x, list) or len(x) != 2 or any(isinstance(v, bool) or not isinstance(v, int) for v in x)
            or x[1] <= 0):
        raise _ReceiptError("bad rational")
    value = Fraction(x[0], x[1])
    if value.numerator != x[0] or value.denominator != x[1]:
        raise _ReceiptError("noncanonical rational")
    return value


def _dec_v(v, n):
    if not isinstance(v, list) or len(v) != n:
        raise _ReceiptError("bad vector")
    return tuple(_dec_q(x) for x in v)


def _dec_m(obj, rows=None, columns=None):
    if not isinstance(obj, dict) or set(obj) != {"rows", "columns", "entries"}:
        raise _ReceiptError("bad matrix")
    r, c = obj["rows"], obj["columns"]
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in (r, c)):
        raise _ReceiptError("bad shape")
    if (rows is not None and r != rows) or (columns is not None and c != columns):
        raise _ReceiptError("shape mismatch")
    if not isinstance(obj["entries"], list) or len(obj["entries"]) != r:
        raise _ReceiptError("bad matrix")
    return tuple(_dec_v(row, c) for row in obj["entries"]), r, c


def _ldl_ok(s, lower, diagonal):
    n = len(s)
    for i in range(n):
        if lower[i][i] != 1 or any(lower[i][j] for j in range(i + 1, n)):
            return False
    if any(x < 0 for x in diagonal):
        return False
    return all(sum((lower[i][t] * diagonal[t] * lower[j][t] for t in range(n)), Fraction(0)) == s[i][j]
               for i in range(n) for j in range(n))


def verify_target_recovery_receipt(receipt):
    """Replay every exact claim from the receipt alone, by direct matrix
    products.  It does not call the elimination, decoder or bracketing code."""
    try:
        return _verify_receipt(receipt)
    except (_ReceiptError, KeyError, TypeError, ZeroDivisionError):
        return False


def _verify_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        return False
    pj = receipt["problem"]
    if receipt.get("problem_sha256") != _digest(pj):
        return False
    if receipt.get("admissible_basis_sha256") != _digest(pj["admissible_basis"]):
        return False
    h, m, d = _dec_m(pj["observations"])
    g, p, _ = _dec_m(pj["target"], None, d)
    q, _, k = _dec_m(pj["admissible_basis"], d)
    r, _, _ = _dec_m(pj["observation_metric"], m, m)
    pm, _, _ = _dec_m(pj["target_metric"], p, p)
    _dec_v(pj["centre"], d)
    # Full column rank of Q by a fresh fraction-free determinant of Q^T Q.
    if _bareiss_det(_matmul(_transpose(q, k), q, k)) == 0 and k:
        return False
    for metric in (r, pm):
        if any(metric[i][j] != metric[j][i] for i in range(len(metric)) for j in range(i)):
            return False
        if any(_bareiss_det(tuple(tuple(row[:t]) for row in metric[:t])) <= 0
               for t in range(1, len(metric) + 1)):
            return False
    h0, g0 = _matmul(h, q, k), _matmul(g, q, k)
    adj, det_r = _adjugate(r)  # W = adj / det
    if receipt["status"] == "unobservable":
        z = _dec_v(receipt["hidden_witness"], k)
        return not any(_matvec(h0, z)) and any(_matvec(g0, z))
    if receipt["status"] not in ("exact_sharp_constant", "bracketed_sharp_constant", "resource_limit"):
        return False
    ident = receipt["identifiability"]
    lrs, _, _ = _dec_m(ident["row_space_decoder"], p, m)
    if _matmul(lrs, h0, k) != g0:
        return False
    for v in ident["kernel_basis"]:
        if any(_matvec(h0, _dec_v(v, k))):
            return False
    w = tuple(tuple(x / det_r for x in row) for row in adj)
    a = _matmul(_transpose(h0, k), _matmul(w, h0, k), k)
    b = _matmul(_transpose(g0, k), _matmul(pm, g0, k), k)
    amp = receipt["amplification_squared"]
    lower, upper = _dec_q(amp["lower"]), _dec_q(amp["upper"])
    if lower > upper or lower < 0:
        return False
    if receipt["status"] == "exact_sharp_constant" and lower != upper:
        return False
    s = _sub(_scale(upper, a), b)
    ll, _, _ = _dec_m(amp["upper_ldl"]["lower"], k, k)
    if not _ldl_ok(s, ll, _dec_v(amp["upper_ldl"]["diagonal"], k)):
        return False
    if amp["lower_witness"] is None:
        if lower != 0 or any(any(row) for row in a):
            return False
    else:
        z = _dec_v(amp["lower_witness"], k)
        den = _quad(a, z)
        if den == 0 or _quad(b, z) / den != lower:
            return False
    if "decoder" in receipt:
        dec = receipt["decoder"]
        lmat, _, _ = _dec_m(dec["matrix"], p, m)
        if _matmul(lmat, h0, k) != g0:
            return False
        beta = _dec_q(dec["beta_squared"])
        bl = _matmul(_transpose(lmat, m), _matmul(pm, lmat, m), m)
        ldl, _, _ = _dec_m(dec["ldl"]["lower"], m, m)
        if not _ldl_ok(_sub(_scale(beta, w), bl), ldl, _dec_v(dec["ldl"]["diagonal"], m)):
            return False
    return True


def _bareiss_det(a):
    """Fraction-free determinant after clearing denominators (separate code path)."""
    n = len(a)
    if n == 0:
        return Fraction(1)
    from math import lcm
    den = 1
    for row in a:
        for x in row:
            den = lcm(den, x.denominator)
    m = [[int(x * den) for x in row] for row in a]
    sign, prev = 1, 1
    for k in range(n - 1):
        if m[k][k] == 0:
            swap = next((i for i in range(k + 1, n) if m[i][k] != 0), None)
            if swap is None:
                return Fraction(0)
            m[k], m[swap] = m[swap], m[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                m[i][j] = (m[i][j] * m[k][k] - m[i][k] * m[k][j]) // prev
        prev = m[k][k]
    return Fraction(sign * m[n - 1][n - 1], den ** n)


def _adjugate(a):
    n = len(a)
    if n == 0:
        return (), Fraction(1)
    det = _bareiss_det(a)
    adj = tuple(tuple((-1) ** (i + j) * _bareiss_det(tuple(tuple(row[:i] + row[i + 1:])
                                                      for t, row in enumerate(a) if t != j))
                      for j in range(n)) for i in range(n))
    return adj, det


# ---------------------------------------------------------------------------
# NX08-B: bounded sensor catalogues
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SensorOption:
    """One installable sensor: one or more rows over the state, a positive
    installation cost, and its noise-shape block (default identity)."""
    identifier: str
    rows: tuple
    cost: Fraction
    noise_shape: tuple | None = None
    unit: str | None = None

    def __post_init__(self):
        if not isinstance(self.identifier, str) or not self.identifier:
            raise ValueError("sensor identifier must be a nonempty string")
        rows = _matrix(self.rows, None, None, "sensor rows")
        if not rows:
            raise ValueError("a sensor must have at least one row")
        width = len(rows[0])
        if any(len(r) != width for r in rows):
            raise ValueError("sensor rows must have equal length")
        cost = _q(self.cost, "cost")
        if cost <= 0:
            raise ValueError("installation cost must be positive")
        shape = None if self.noise_shape is None else _positive_definite(
            _matrix(self.noise_shape, len(rows), len(rows), "noise_shape"), "noise_shape")
        if self.unit is not None and (not isinstance(self.unit, str) or not self.unit):
            raise TypeError("unit must be a nonempty string")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "cost", cost)
        object.__setattr__(self, "noise_shape", shape)


def _catalogue(catalogue, d):
    options = _seq(catalogue, "catalogue")
    if any(not isinstance(o, SensorOption) for o in options):
        raise TypeError("catalogue entries must be SensorOption")
    if len(options) > MAX_CATALOGUE:
        raise ValueError(f"catalogue exceeds the declared limit of {MAX_CATALOGUE} options")
    if len({o.identifier for o in options}) != len(options):
        raise ValueError("sensor identifiers must be distinct")
    if any(len(o.rows[0]) != d for o in options):
        raise ValueError("sensor rows must match the state dimension")
    return options


def layout_problem(catalogue, layout, target, admissible_basis=None, *, centre=None,
                   target_metric=None, units=None, state_dimension=None):
    """The :class:`TargetRecoveryProblem` of a chosen subset (indices, any order;
    rows are stacked in increasing index order with a block-diagonal R)."""
    target_rows = _matrix(target, None, None, "target")
    d = state_dimension
    if d is None:
        if target_rows:
            d = len(target_rows[0])
        else:
            opts = _seq(catalogue, "catalogue")
            if not opts:
                raise ValueError("state_dimension is required")
            d = len(opts[0].rows[0])
    options = _catalogue(catalogue, d)
    chosen = sorted(set(layout))
    if any(isinstance(i, bool) or not isinstance(i, int) for i in chosen):
        raise TypeError("layout entries must be ints")
    if any(not 0 <= i < len(options) for i in chosen):
        raise ValueError("layout index out of range")
    rows, blocks = [], []
    for i in chosen:
        rows.extend(options[i].rows)
        blocks.append(options[i].noise_shape or _identity(len(options[i].rows)))
    m = len(rows)
    r = [[Fraction(0)] * m for _ in range(m)]
    offset = 0
    for block in blocks:
        for i, row in enumerate(block):
            for j, x in enumerate(row):
                r[offset + i][offset + j] = x
        offset += len(block)
    obs_units = []
    for i in chosen:
        obs_units.extend([options[i].unit or "unspecified"] * len(options[i].rows))
    merged = dict(units or {})
    merged.setdefault("observations", obs_units)
    return TargetRecoveryProblem(tuple(rows), target_rows, admissible_basis, tuple(map(tuple, r)),
                                 merged, centre=centre, target_metric=target_metric,
                                 state_dimension=d)


@dataclass(frozen=True)
class LayoutResult:
    """``feasible`` with the chosen indices, ids, cost and an exact PSD
    certificate of S(kappa_max^2), or ``infeasible`` for the whole catalogue."""
    status: str
    layout: tuple
    identifiers: tuple
    cost: Fraction | None
    certificate: PSDCertificate | None
    tests: int


def _key(options, layout):
    return (sum((options[i].cost for i in layout), Fraction(0)), len(layout), tuple(layout))


def _feasible(catalogue, layout, target, kappa2, kw):
    problem = layout_problem(catalogue, layout, target, **kw)
    if kappa2 is None:
        return target_identifiability(problem).status == "identifiable", None
    cert = psd_certificate(amplification_form(problem, kappa2))
    return isinstance(cert, PSDCertificate), (cert if isinstance(cert, PSDCertificate) else None)


def _search(catalogue, target, kappa2, method, kw):
    options = _catalogue(catalogue, kw.get("state_dimension") or len(_matrix(target, None, None)[0]))
    n = len(options)
    tests = 0
    if method == "exhaustive":
        best = None
        for mask in range(1 << n):
            layout = tuple(i for i in range(n) if mask >> i & 1)
            tests += 1
            ok, cert = _feasible(catalogue, layout, target, kappa2, kw)
            if ok and (best is None or _key(options, layout) < _key(options, best[0])):
                best = (layout, cert)
    elif method == "pruned":
        best = None
        memo = {}

        def feasible(layout):
            nonlocal tests
            if layout not in memo:
                tests += 1
                memo[layout] = _feasible(catalogue, layout, target, kappa2, kw)
            return memo[layout]

        def visit(i, chosen):
            nonlocal best
            cost = sum((options[j].cost for j in chosen), Fraction(0))
            if best is not None and cost > _key(options, best[0])[0]:
                return
            ok, cert = feasible(chosen)
            if ok:
                # Positive costs: every extension costs more, so stop here.
                if best is None or _key(options, chosen) < _key(options, best[0]):
                    best = (chosen, cert)
                return
            if i == n:
                return
            # Monotonicity: if even all remaining options fail, so does every subset.
            if not feasible(tuple(chosen) + tuple(range(i, n)))[0]:
                return
            visit(i + 1, chosen + (i,))
            visit(i + 1, chosen)

        visit(0, ())
    else:
        raise ValueError("method must be 'pruned' or 'exhaustive'")
    if best is None:
        return LayoutResult("infeasible", (), (), None, None, tests)
    layout, cert = best
    return LayoutResult("feasible", layout, tuple(options[i].identifier for i in layout),
                        _key(options, layout)[0], cert, tests)


def cheapest_identifying_layout(catalogue, target, admissible_basis=None, *, method="pruned", **kw):
    """Minimum-cost layout meeting the kernel condition only (rank objective).
    Ties: fewer sensors, then lexicographically smaller indices."""
    kw["admissible_basis"] = admissible_basis
    return _search(catalogue, target, None, method, kw)


def cheapest_conditioned_layout(catalogue, target, kappa_max_squared, admissible_basis=None, *,
                                method="pruned", **kw):
    """Minimum-cost layout with kappa_*^2 <= kappa_max_squared, decided exactly
    by an LDL test of S(kappa_max^2) per layout.  Same tie rule."""
    kappa2 = _q(kappa_max_squared, "kappa_max_squared")
    if kappa2 < 0:
        raise ValueError("kappa_max_squared must be nonnegative")
    kw["admissible_basis"] = admissible_basis
    return _search(catalogue, target, kappa2, method, kw)


def conditioning_frontier(catalogue, target, thresholds, admissible_basis=None, *,
                          tolerance=Fraction(1, 10 ** 6), max_steps=200, **kw):
    """Cost-versus-conditioning staircase over declared kappa_max^2 thresholds,
    with the exact sharp-constant bracket of each optimal layout."""
    thresholds = tuple(_q(t, "threshold") for t in _seq(thresholds, "thresholds"))
    method = kw.pop("method", "pruned")
    rows = []
    for t in sorted(set(thresholds)):
        result = cheapest_conditioned_layout(catalogue, target, t, admissible_basis,
                                             method=method, **kw)
        entry = {"kappa_max_squared": t, "status": result.status, "layout": result.layout,
                 "identifiers": result.identifiers, "cost": result.cost}
        if result.status == "feasible":
            br = bracket_target_amplification(
                layout_problem(catalogue, result.layout, target, admissible_basis, **kw),
                tolerance, max_steps)
            entry.update(bracket_status=br.status, lower=br.lower, upper=br.upper)
        rows.append(entry)
    return tuple(rows)


def layout_table(catalogue, target, admissible_basis=None, *, tolerance=Fraction(1, 10 ** 6),
                 max_steps=200, **kw):
    """Every subset of a tiny catalogue: cost, rank, status and kappa_*^2 bracket."""
    target_rows = _matrix(target, None, None, "target")
    d = kw.get("state_dimension") or len(target_rows[0])
    options = _catalogue(catalogue, d)
    table = []
    for mask in range(1 << len(options)):
        layout = tuple(i for i in range(len(options)) if mask >> i & 1)
        problem = layout_problem(catalogue, layout, target_rows, admissible_basis, **kw)
        br = bracket_target_amplification(problem, tolerance, max_steps)
        ident = target_identifiability(problem)
        table.append({"layout": layout, "identifiers": tuple(options[i].identifier for i in layout),
                      "cost": _key(options, layout)[0], "rank": ident.rank, "status": br.status,
                      "lower": br.lower, "upper": br.upper})
    return tuple(table)


# ---------------------------------------------------------------------------
# NX08-C: forecast and thermal adapters
# ---------------------------------------------------------------------------

def matrix_power(transition, exponent):
    a = _matrix(transition, None, None, "transition")
    n = len(a)
    if any(len(r) != n for r in a):
        raise ValueError("transition must be square")
    e = _count(exponent, "exponent")
    result = _identity(n)
    for _ in range(e):
        result = _matmul(result, a, n)
    return result


def linear_forecast_problem(transition, sensor_rows, observation_times, target_rows, horizon,
                            admissible_basis=None, **kw):
    """Observations C_j F^t (t in observation_times, sensors inner) of the
    initial state; target G F^horizon.  F is a fixed, known transition; any
    known input contribution must already be subtracted (it is a centre)."""
    f = _matrix(transition, None, None, "transition")
    n = len(f)
    if any(len(r) != n for r in f):
        raise ValueError("transition must be square")
    sensors = _matrix(sensor_rows, None, n, "sensor_rows")
    times = tuple(_count(t, "observation time") for t in _seq(observation_times, "observation_times"))
    if len(set(times)) != len(times):
        raise ValueError("observation times must be distinct")
    target_rows = _matrix(target_rows, None, n, "target_rows")
    horizon = _count(horizon, "horizon")
    rows = []
    for t in times:
        ft = matrix_power(f, t)
        rows.extend(_matmul((c,), ft, n)[0] for c in sensors)
    g = _matmul(target_rows, matrix_power(f, horizon), n)
    return TargetRecoveryProblem(tuple(rows), g, admissible_basis, state_dimension=n, **kw)


def thermal_target_problem(candidate, sensor_indices, observation_times, target_rows, horizon,
                           admissible_basis=None, **kw):
    """Forecast problem for a :class:`thermal_diagnostics.AffineCandidate` with
    zero (or already subtracted) heater input: x' = A x."""
    from .thermal_diagnostics import AffineCandidate
    if not isinstance(candidate, AffineCandidate):
        raise TypeError("candidate must be an AffineCandidate")
    n = candidate.dimension
    a = [[Fraction(0)] * n for _ in range(n)]
    for i, j, v in candidate.entries:
        a[i][j] = v
    sensors = []
    for s in _seq(sensor_indices, "sensor_indices"):
        if isinstance(s, bool) or not isinstance(s, int):
            raise TypeError("sensor indices must be ints")
        if not 0 <= s < len(candidate.sensors):
            raise ValueError("sensor index out of range")
        sensors.append(candidate.sensors[s])
    return linear_forecast_problem(tuple(map(tuple, a)), tuple(sensors), observation_times,
                                   target_rows, horizon, admissible_basis, **kw)
