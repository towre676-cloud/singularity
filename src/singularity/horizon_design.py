"""All-horizon stopping certificates for fixed step and repeated-block protocols (NX10).

Scope
-----
One scalar reading per experiment, taken after ``t`` steps (or ``k`` repeated
blocks) of a *fixed* input protocol, each experiment starting from the
declared reset state (independent reset).  Arbitrary, adaptive or switched
inputs, fixed multi-time panels and shared physical histories are outside this
module; a conclusion here says nothing about them.

Dynamics and steady state
-------------------------
An :class:`AffineScalarSystem` is ``x_{k+1} = A x_k + b``, ``y_k = c x_k + e``
with exact rational data and initial state ``x_0``.  For a constant input
``u`` on ``x' = A x + B u`` this is ``b = B u``, ``e = 0``.  For a fixed block
of inputs ``u_0, ..., u_{L-1}`` (chronological) it is the block map
``A^L``, ``b = sum_i A^(L-1-i) B u_i``, observed at phase ``j`` through
``c = C A^j`` and ``e = C sum_{i<j} A^(j-1-i) B u_i``.  When ``I - A`` is
invertible the unique fixed point ``x* = (I-A)^(-1) b`` gives

    y_k = (c x* + e) + c A^k (x_0 - x*).

The affine homogeneous lift ``[[A, b], [0, 1]]`` always has eigenvalue one;
contraction is tested on ``A`` after subtracting ``x*``, never on the lift.

Contraction convention (squared gamma)
--------------------------------------
A :class:`QuadraticMetric` stores a positive definite rational ``P`` and the
*squared* factor ``gamma_squared`` with ``gamma_squared P - A^T P A`` positive
semidefinite.  This is DynaComp's ``gamma`` convention (``x^T P x`` shrinks by
``gamma`` per step); the norm ``||x||_P`` shrinks by ``sqrt(gamma_squared)``.
The metric also stores a rational norm factor ``rho`` with
``rho^2 >= gamma_squared`` and ``rho < 1``, so ``||A^k v||_P <= rho^k ||v||_P``.
DynaComp accepts the strict inequality; this module accepts the semidefinite
one, which is sufficient for the norm bound and admits the exact factor of a
symmetric matrix.  :func:`metric_from_dynacomp` converts the upstream packet
without confusing the two factors.

Tail theorem (proved in docs/research/HORIZON_DESIGN.md)
-------------------------------------------------------
With ``K = ||c||_{P,*} ||x_T - x*||_P`` (rational upper enclosure), for all
``k >= T``: ``|y_k - y_inf| <= K rho^(k-T)``.  For a pair ``a, b`` with
``delta = y_a - y_b`` and ``U = K_a rho_a^(k-T) + K_b rho_b^(k-T)``,
``| |delta_k| - |delta_inf| | <= U``.  Separation at ``k`` is strict:
``|delta_k| > rho_a(k) + rho_b(k)`` for declared radius envelopes.

All arithmetic is exact; inputs of type bool, float or str raise TypeError.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
import hashlib
import json
from math import gcd, isqrt

SCHEMA = "singularity.horizon-design/1"
METRIC_SCHEMA = "singularity.horizon-metric/1"
STATUSES = ("eventually_separating", "never_separating_after", "finite_optimum_certified",
            "supremum_bracket", "inconclusive_tail", "resource_limit")
RESET_CONTRACTS = ("independent_reset",)
THRESHOLD_CONVENTION = "separation iff |delta| > radius_a + radius_b (strict); equality is not separation"
SCOPE = ("one scalar reading after a fixed constant-input step protocol or a fixed repeated input "
         "block, every experiment independently reset; not a multi-time panel, not all legal words, "
         "not an adaptive policy, not a calibrated physical-time statement")


# --------------------------------------------------------------------------
# Exact scalar, vector and matrix helpers
# --------------------------------------------------------------------------

def _q(value, name="value"):
    if isinstance(value, bool) or isinstance(value, (float, str)):
        raise TypeError(f"{name} must be an int or Fraction, not {type(value).__name__}")
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, Fraction):
        return value
    raise TypeError(f"{name} must be an int or Fraction")


def _int(value, name="value"):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int")
    return value


def _seq(value, name):
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise TypeError(f"{name} must be a sequence")
    return tuple(value)


def _vector(values, name="vector", size=None):
    result = tuple(_q(x, name) for x in _seq(values, name))
    if size is not None and len(result) != size:
        raise ValueError(f"{name} has length {len(result)}, expected {size}")
    if not result:
        raise ValueError(f"{name} must be nonempty")
    return result


def _matrix(rows, name="matrix", rows_count=None, cols=None):
    result = tuple(_vector(r, name) for r in _seq(rows, name))
    if not result:
        raise ValueError(f"{name} must be nonempty")
    width = len(result[0])
    if any(len(r) != width for r in result):
        raise ValueError(f"{name} must be rectangular")
    if rows_count is not None and len(result) != rows_count:
        raise ValueError(f"{name} has {len(result)} rows, expected {rows_count}")
    if cols is not None and width != cols:
        raise ValueError(f"{name} has {width} columns, expected {cols}")
    return result


def _identity(n):
    return tuple(tuple(Fraction(int(i == j)) for j in range(n)) for i in range(n))


def _transpose(a):
    return tuple(zip(*a))


def _matmul(a, b):
    bt = _transpose(b)
    return tuple(tuple(sum((x * y for x, y in zip(row, col) if x and y), Fraction(0)) for col in bt)
                 for row in a)


def _matvec(a, v):
    return tuple(sum((x * y for x, y in zip(row, v) if x and y), Fraction(0)) for row in a)


def _dot(u, v):
    return sum((x * y for x, y in zip(u, v) if x and y), Fraction(0))


def _matpow(a, k):
    result, power = _identity(len(a)), a
    while k:
        if k & 1:
            result = _matmul(power, result)
        k >>= 1
        if k:
            power = _matmul(power, power)
    return result


def _solve(m, rhs):
    """Exact Gaussian elimination; ValueError if m is singular."""
    n = len(m)
    aug = [list(row) + [r] for row, r in zip(m, rhs)]
    for col in range(n):
        pivot = next((r for r in range(col, n) if aug[r][col]), None)
        if pivot is None:
            raise ValueError("matrix is singular")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        p = aug[col][col]
        for r in range(n):
            if r != col and aug[r][col]:
                f = aug[r][col] / p
                aug[r] = [x - f * y for x, y in zip(aug[r], aug[col])]
    return tuple(aug[i][n] / aug[i][i] for i in range(n))


def _symmetric(m):
    n = len(m)
    return len(m[0]) == n and all(m[i][j] == m[j][i] for i in range(n) for j in range(i))


def _lcm_den(values):
    d = 1
    for x in values:
        d = d * x.denominator // gcd(d, x.denominator)
    return d


def _integer_matrix(m):
    """Positive integer multiple of a rational matrix (common denominator)."""
    d = _lcm_den(x for r in m for x in r)
    return [[x.numerator * (d // x.denominator) for x in r] for r in m]


def _bareiss_semidefinite(a, strict):
    """Fraction-free symmetric elimination on an integer matrix (destroys ``a``).

    Pivots are leading principal minors (Sylvester).  For the semidefinite
    test a zero pivot requires its whole remaining column to vanish, and that
    index is skipped; the remaining entries are then minors of the matrix with
    the skipped indices deleted, so every division stays exact.
    """
    n = len(a)
    prev = 1
    for k in range(n):
        p = a[k][k]
        if p < 0 or (strict and p == 0):
            return False
        if p == 0:
            if any(a[i][k] for i in range(k + 1, n)):
                return False
            continue
        rk = a[k]
        for i in range(k + 1, n):
            ri = a[i]
            aik = ri[k]
            for j in range(k + 1, n):
                q, rem = divmod(p * ri[j] - aik * rk[j], prev)
                if rem:
                    raise ArithmeticError("Bareiss division was not exact")
                ri[j] = q
        prev = p
    return True


def positive_semidefinite(m):
    """Exact semidefinite test of a symmetric rational matrix (fraction-free LDL^T)."""
    m = _matrix(m, "matrix")
    if not _symmetric(m):
        raise ValueError("expected a symmetric matrix")
    return _bareiss_semidefinite(_integer_matrix(m), strict=False)


def positive_definite(m):
    """Exact Sylvester test: every leading principal minor is positive."""
    m = _matrix(m, "matrix")
    if not _symmetric(m):
        raise ValueError("expected a symmetric matrix")
    return _bareiss_semidefinite(_integer_matrix(m), strict=True)


def sqrt_up(x, bits=64):
    """Rational upper bound of sqrt(x) for rational x >= 0 (ported from DynaComp)."""
    x = _q(x, "x")
    if x < 0:
        raise ValueError("negative argument")
    if not x:
        return Fraction(0)
    n = x.numerator * x.denominator * 4 ** bits
    r = isqrt(n)
    if r * r < n:
        r += 1
    return Fraction(r, x.denominator * 2 ** bits)


# Exact Schur stability (Faddeev-LeVerrier + Schur-Cohn), ported from the pinned
# DynaComp ``stability.py`` (commit cd788c7) with the same recursion.

def charpoly(a):
    """Coefficients of det(zI - A), lowest degree first."""
    a = _matrix(a, "A")
    n = len(a)
    if len(a[0]) != n:
        raise ValueError("expected a square matrix")
    coefficients = [Fraction(1)]
    m = tuple(tuple(Fraction(0) for _ in range(n)) for _ in range(n))
    for k in range(1, n + 1):
        shifted = tuple(tuple(m[i][j] + (coefficients[-1] if i == j else 0) for j in range(n))
                        for i in range(n))
        m = _matmul(a, shifted)
        coefficients.append(-sum(m[i][i] for i in range(n)) / k)
    return tuple(reversed(coefficients))


def _primitive(p):
    den = 1
    for c in p:
        den = den * c.denominator // gcd(den, c.denominator)
    ints = [int(c * den) for c in p]
    g = 0
    for c in ints:
        g = gcd(g, c)
    return [c // g for c in ints] if g else ints


def schur_stable(a):
    """True iff every eigenvalue of A lies in the open unit disk (exact)."""
    p = list(charpoly(a))
    while len(p) > 1:
        p = _primitive(p)
        a0, an = p[0], p[-1]
        if not abs(a0) < abs(an):
            return False
        p = [an * x - a0 * y for x, y in zip(p, reversed(p))][1:]
    return True


def _dyadic(x, bits):
    y = x * (1 << bits)
    return Fraction((y.numerator * 2 + y.denominator) // (2 * y.denominator), 1 << bits)


# --------------------------------------------------------------------------
# Exact JSON encoding (INTERCHANGE_CONTRACT: rational = [num, den])
# --------------------------------------------------------------------------

def encode_rational(x):
    x = _q(x)
    return [x.numerator, x.denominator]


def decode_rational(value, name="rational"):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{name} must be a [numerator, denominator] pair")
    n, d = value
    if isinstance(n, bool) or isinstance(d, bool) or not isinstance(n, int) or not isinstance(d, int):
        raise TypeError(f"{name} entries must be JSON integers")
    if d <= 0 or gcd(n, d) != 1 or (n == 0 and d != 1):
        raise ValueError(f"{name} is not a canonical rational pair")
    return Fraction(n, d)


def _enc(value):
    if isinstance(value, Fraction):
        return encode_rational(value)
    if isinstance(value, dict):
        return {k: _enc(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_enc(v) for v in value]
    return value


def _enc_vec(v):
    return [encode_rational(x) for x in v]


def _enc_mat(m):
    return {"rows": len(m), "cols": len(m[0]), "entries": [_enc_vec(r) for r in m]}


def _dec_vec(v, name):
    if not isinstance(v, list) or not v:
        raise ValueError(f"{name} must be a nonempty list")
    return tuple(decode_rational(x, name) for x in v)


def _dec_mat(m, name):
    if not isinstance(m, dict) or set(m) != {"rows", "cols", "entries"}:
        raise ValueError(f"{name} must record rows, cols and entries")
    rows = tuple(_dec_vec(r, name) for r in m["entries"])
    if len(rows) != m["rows"] or any(len(r) != m["cols"] for r in rows):
        raise ValueError(f"{name} shape does not match its declaration")
    return rows


def _digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Units:
    """Declared units; pairs and error contracts must agree exactly."""
    output: str = "model_output"
    step: str = "model_step"
    input: str = "model_input"

    def __post_init__(self):
        for name in ("output", "step", "input"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"unit {name} must be a nonempty string")


@dataclass(frozen=True)
class LinearCandidate:
    """x' = A x + B u, readings y_j = sensors[j] x, reset state ``initial``."""
    identifier: str
    A: tuple
    B: tuple
    sensors: tuple
    initial: tuple = None
    units: Units = field(default_factory=Units)

    def __post_init__(self):
        if not isinstance(self.identifier, str) or not self.identifier:
            raise ValueError("identifier must be a nonempty string")
        a = _matrix(self.A, "A")
        n = len(a)
        if len(a[0]) != n:
            raise ValueError("A must be square")
        object.__setattr__(self, "A", a)
        object.__setattr__(self, "B", _matrix(self.B, "B", rows_count=n))
        sensors = tuple(_vector(s, "sensor", n) for s in _seq(self.sensors, "sensors"))
        if not sensors:
            raise ValueError("at least one sensor is required")
        object.__setattr__(self, "sensors", sensors)
        object.__setattr__(self, "initial", (Fraction(0),) * n if self.initial is None
                           else _vector(self.initial, "initial", n))
        if not isinstance(self.units, Units):
            raise TypeError("units must be a Units instance")

    @property
    def dimension(self):
        return len(self.A)

    @property
    def inputs(self):
        return len(self.B[0])

    @classmethod
    def from_affine(cls, candidate, units=None, initial=None):
        """Dense adapter for :class:`singularity.thermal_diagnostics.AffineCandidate`."""
        from .thermal_diagnostics import AffineCandidate
        if not isinstance(candidate, AffineCandidate):
            raise TypeError("candidate must be an AffineCandidate")
        n = candidate.dimension
        rows = [[Fraction(0)] * n for _ in range(n)]
        for i, j, v in candidate.entries:
            rows[i][j] = v
        return cls(candidate.identifier, rows, tuple((h,) for h in candidate.heater),
                   candidate.sensors, initial, units or Units())


@dataclass(frozen=True)
class AffineScalarSystem:
    """x_{k+1} = A x_k + b, y_k = c x_k + e; ``protocol`` names the experiment."""
    identifier: str
    A: tuple
    b: tuple
    c: tuple
    e: Fraction
    x0: tuple
    units: Units
    protocol: tuple

    def __post_init__(self):
        if not isinstance(self.identifier, str) or not self.identifier:
            raise ValueError("identifier must be a nonempty string")
        a = _matrix(self.A, "A")
        n = len(a)
        if len(a[0]) != n:
            raise ValueError("A must be square")
        object.__setattr__(self, "A", a)
        object.__setattr__(self, "b", _vector(self.b, "b", n))
        object.__setattr__(self, "c", _vector(self.c, "c", n))
        object.__setattr__(self, "e", _q(self.e, "e"))
        object.__setattr__(self, "x0", _vector(self.x0, "x0", n))
        if not isinstance(self.units, Units):
            raise TypeError("units must be a Units instance")
        if not isinstance(self.protocol, tuple):
            raise TypeError("protocol must be a tuple description")

    @property
    def dimension(self):
        return len(self.A)

    def spec(self):
        return {"identifier": self.identifier, "A": _enc_mat(self.A), "b": _enc_vec(self.b),
                "c": _enc_vec(self.c), "e": encode_rational(self.e), "x0": _enc_vec(self.x0),
                "units": {"output": self.units.output, "step": self.units.step, "input": self.units.input},
                "protocol": _enc(list(self.protocol))}

    @classmethod
    def from_spec(cls, spec):
        if not isinstance(spec, dict):
            raise ValueError("system spec must be an object")
        u = spec["units"]
        protocol = spec["protocol"]

        def tup(v):
            if isinstance(v, list) and len(v) == 2 and all(type(x) is int for x in v):
                return decode_rational(v)
            return tuple(tup(x) for x in v) if isinstance(v, list) else v
        return cls(spec["identifier"], _dec_mat(spec["A"], "A"), _dec_vec(spec["b"], "b"),
                   _dec_vec(spec["c"], "c"), decode_rational(spec["e"], "e"), _dec_vec(spec["x0"], "x0"),
                   Units(u["output"], u["step"], u["input"]), tup(protocol))

    def steady_state(self):
        """Unique fixed point x* of x -> A x + b; ValueError when I - A is singular."""
        n = self.dimension
        m = tuple(tuple(int(i == j) - self.A[i][j] for j in range(n)) for i in range(n))
        try:
            return _solve(m, self.b)
        except ValueError:
            raise ValueError("I - A is singular: no unique steady state for this protocol") from None

    def states(self, count):
        """Exact states x_0..x_{count-1} using a common-denominator integer recursion."""
        count = _int(count, "count")
        if count < 0:
            raise ValueError("count must be nonnegative")
        n = self.dimension
        d = 1
        for row in self.A:
            for x in row:
                d = d * x.denominator // gcd(d, x.denominator)
        db = 1
        for x in self.b:
            db = db * x.denominator // gcd(db, x.denominator)
        m = [[int(x * d) for x in row] for row in self.A]
        beta = [int(x * db) for x in self.b]
        g = 1
        for x in self.x0:
            g = g * x.denominator // gcd(g, x.denominator)
        y = [int(x * g) for x in self.x0]
        out = []
        for _ in range(count):
            out.append(tuple(Fraction(v, g) for v in y))
            g_next = d * g // gcd(d * g, db) * db
            s1, s2 = g_next // (d * g), g_next // db
            y = [sum(mij * yj for mij, yj in zip(row, y) if mij) * s1 + bi * s2 for row, bi in zip(m, beta)]
            common = g_next
            for v in y:
                common = gcd(common, v)
                if common == 1:
                    break
            g = g_next // common
            y = [v // common for v in y]
        return out

    def output(self, state):
        return _dot(self.c, state) + self.e


def step_system(candidate, input, sensor, *, label=None):
    """Constant-input step experiment: b = B u, c = C_sensor, e = 0."""
    if not isinstance(candidate, LinearCandidate):
        raise TypeError("candidate must be a LinearCandidate")
    u = _vector(input, "input", candidate.inputs)
    j = _int(sensor, "sensor")
    if not 0 <= j < len(candidate.sensors):
        raise ValueError("sensor index out of range")
    b = _matvec(candidate.B, u)
    return AffineScalarSystem(candidate.identifier, candidate.A, b, candidate.sensors[j], 0,
                              candidate.initial, candidate.units,
                              ("constant_input_step", u, label if label is not None else j))


def block_system(candidate, block, phase, sensor, *, label=None):
    """Fixed repeated block in chronological order, observed ``phase`` steps into a block.

    Block index k corresponds to physical step k*L + phase.  The block map is
    A_blk = A^L, b_blk = sum_i A^(L-1-i) B u_i; the phase output is
    c = C A^phase, e = C sum_{i<phase} A^(phase-1-i) B u_i.
    """
    if not isinstance(candidate, LinearCandidate):
        raise TypeError("candidate must be a LinearCandidate")
    block = tuple(_vector(u, "block input", candidate.inputs) for u in _seq(block, "block"))
    if not block:
        raise ValueError("block must contain at least one input")
    phase = _int(phase, "phase")
    if not 0 <= phase < len(block):
        raise ValueError("phase must lie in [0, block length)")
    j = _int(sensor, "sensor")
    if not 0 <= j < len(candidate.sensors):
        raise ValueError("sensor index out of range")
    n = candidate.dimension
    a_blk, b_blk = _identity(n), (Fraction(0),) * n
    c_row, e = candidate.sensors[j], Fraction(0)
    for i, u in enumerate(block):
        bu = _matvec(candidate.B, u)
        a_blk = _matmul(candidate.A, a_blk)
        b_blk = tuple(x + y for x, y in zip(_matvec(candidate.A, b_blk), bu))
        if i + 1 == phase:
            c_row = tuple(_matvec(_transpose(a_blk), candidate.sensors[j]))
            e = _dot(candidate.sensors[j], b_blk)
    units = Units(candidate.units.output, f"block[{len(block)}]x{candidate.units.step}",
                  candidate.units.input)
    return AffineScalarSystem(candidate.identifier, a_blk, b_blk, c_row, e, candidate.initial, units,
                              ("fixed_repeated_block", block, phase, label if label is not None else j))


@dataclass(frozen=True)
class StepFamily:
    """Constant-input step protocols for named candidates and sensors."""
    candidates: tuple
    input: tuple
    sensors: tuple
    reset_contract: str = "independent_reset"
    min_horizon: int = 0

    def __post_init__(self):
        cands = tuple(_seq(self.candidates, "candidates"))
        if len(cands) < 2 or any(not isinstance(c, LinearCandidate) for c in cands):
            raise ValueError("at least two LinearCandidate models are required")
        if len({c.identifier for c in cands}) != len(cands):
            raise ValueError("candidate identifiers must be distinct")
        if len({c.units for c in cands}) != 1:
            raise ValueError("inconsistent units across candidates")
        if len({(c.inputs, len(c.sensors)) for c in cands}) != 1:
            raise ValueError("candidates must share input and sensor channels")
        object.__setattr__(self, "candidates", cands)
        object.__setattr__(self, "input", _vector(self.input, "input", cands[0].inputs))
        sensors = tuple(_int(s, "sensor") for s in _seq(self.sensors, "sensors"))
        if not sensors or any(not 0 <= s < len(cands[0].sensors) for s in sensors):
            raise ValueError("sensor indices out of range")
        object.__setattr__(self, "sensors", sensors)
        if self.reset_contract not in RESET_CONTRACTS:
            raise ValueError("only independent_reset protocols are supported")
        if _int(self.min_horizon, "min_horizon") < 0:
            raise ValueError("min_horizon must be nonnegative")

    def candidate(self, identifier):
        for c in self.candidates:
            if c.identifier == identifier:
                return c
        raise ValueError(f"unknown candidate {identifier!r}")

    def system(self, identifier, sensor):
        if sensor not in self.sensors:
            raise ValueError("sensor not declared in this family")
        return step_system(self.candidate(identifier), self.input, sensor)


# --------------------------------------------------------------------------
# Quadratic metrics
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class QuadraticMetric:
    """P > 0 and gamma_squared P - A^T P A >= 0, with rho^2 >= gamma_squared, rho < 1."""
    A: tuple
    P: tuple
    gamma_squared: Fraction
    rho: Fraction
    source: str = "supplied"

    def __post_init__(self):
        object.__setattr__(self, "A", _matrix(self.A, "A"))
        object.__setattr__(self, "P", _matrix(self.P, "P"))
        object.__setattr__(self, "gamma_squared", _q(self.gamma_squared, "gamma_squared"))
        object.__setattr__(self, "rho", _q(self.rho, "rho"))
        self.check()

    def check(self):
        a, p, g, r = self.A, self.P, self.gamma_squared, self.rho
        n = len(a)
        if len(a[0]) != n or len(p) != n or len(p[0]) != n:
            raise ValueError("A and P must be square of equal size")
        if not 0 <= g < 1:
            raise ValueError("gamma_squared must lie in [0, 1)")
        if not 0 <= r < 1:
            raise ValueError("rho must lie in [0, 1)")
        if r * r < g:
            raise ValueError("rho^2 < gamma_squared: rho is not an upper norm factor")
        if not _symmetric(p) or not positive_definite(p):
            raise ValueError("P is not symmetric positive definite")
        if not contraction_holds(a, p, g):
            raise ValueError("gamma_squared P - A^T P A is not positive semidefinite")
        return True

    def norm_squared(self, v):
        return _dot(v, _matvec(self.P, v))

    def dual_norm_squared(self, row):
        return _dot(row, _solve(self.P, row))

    def spec(self):
        return {"schema": METRIC_SCHEMA, "A": _enc_mat(self.A), "P": _enc_mat(self.P),
                "gamma_squared": encode_rational(self.gamma_squared), "rho": encode_rational(self.rho),
                "convention": "gamma_squared P - A^T P A >= 0 (semidefinite); ||A^k v||_P <= rho^k ||v||_P",
                "source": self.source}

    @classmethod
    def from_spec(cls, spec):
        if not isinstance(spec, dict) or spec.get("schema") != METRIC_SCHEMA:
            raise ValueError("need a singularity.horizon-metric/1 record")
        return cls(_dec_mat(spec["A"], "A"), _dec_mat(spec["P"], "P"),
                   decode_rational(spec["gamma_squared"]), decode_rational(spec["rho"]), spec["source"])


def contraction_holds(a, p, gamma_squared):
    """Exact semidefinite test of gamma_squared P - A^T P A (P symmetric).

    With A = Ai/g, P = Pi/h and gamma_squared = s/t (integers), the matrix
    t h g^2 (gamma_squared P - A^T P A) = s g^2 Pi - t Ai^T Pi Ai is an
    integer matrix with the same inertia, tested fraction-free.
    """
    a, p = _matrix(a, "A"), _matrix(p, "P")
    gamma_squared = _q(gamma_squared, "gamma_squared")
    if not _symmetric(p):
        raise ValueError("P must be symmetric")
    g = _lcm_den(x for r in a for x in r)
    h = _lcm_den(x for r in p for x in r)
    ai = [[x.numerator * (g // x.denominator) for x in r] for r in a]
    pi = [[x.numerator * (h // x.denominator) for x in r] for r in p]
    n = len(a)
    pa = [[sum(pi[i][k] * ai[k][j] for k in range(n) if pi[i][k] and ai[k][j]) for j in range(n)]
          for i in range(n)]
    s, t = gamma_squared.numerator, gamma_squared.denominator
    g2 = g * g
    m = [[s * g2 * pi[i][j] - t * sum(ai[k][i] * pa[k][j] for k in range(n) if ai[k][i] and pa[k][j])
          for j in range(n)] for i in range(n)]
    return _bareiss_semidefinite(m, strict=False)


@dataclass(frozen=True)
class MetricFailure:
    """No metric accepted.  ``schur_stable`` separates instability from proposal failure."""
    status: str
    schur_stable: bool
    reason: str


def _smith(a, scale, bits, max_doublings):
    """Exact dyadic Smith doubling for sum_k (A/s)^T^k (A/s)^k; None if not converged."""
    n = len(a)
    m = tuple(tuple(_dyadic(x / scale, bits) for x in row) for row in a)
    p, power = _identity(n), m
    limit = Fraction(1 << (bits // 2))
    tiny = Fraction(1, 1 << bits)
    for _ in range(max_doublings):
        add = _matmul(_matmul(_transpose(power), p), power)
        p = tuple(tuple(_dyadic((p[i][j] + add[i][j] + p[j][i] + add[j][i]) / 2, bits) for j in range(n))
                  for i in range(n))
        if max(abs(x) for r in p for x in r) > limit:
            return None
        power = tuple(tuple(_dyadic(x, bits) for x in r) for r in _matmul(power, power))
        if max(abs(x) for r in power for x in r) <= tiny:
            return p
    return None


_METRICS = {}


def certify_metric(A, P=None, rho=None, *, bits=48, rho_bits=24, max_scale_exponent=16,
                   max_doublings=40):
    """Return a :class:`QuadraticMetric` or a :class:`MetricFailure`.

    With ``P`` and ``rho`` supplied the pair is checked exactly.  With only
    ``P``, the smallest dyadic ``rho`` (``rho_bits`` bisection steps) is
    found.  Otherwise a positive definite ``P`` is proposed by exact dyadic
    Smith doubling for scales ``s = 1 - 2^-k`` and accepted exactly.  Results
    are cached by the exact source matrix and options.
    """
    a = _matrix(A, "A")
    if len(a[0]) != len(a):
        raise ValueError("A must be square")
    p_in = None if P is None else _matrix(P, "P")
    r_in = None if rho is None else _q(rho, "rho")
    key = (a, p_in, r_in, bits, rho_bits, max_scale_exponent, max_doublings)
    if key in _METRICS:
        return _METRICS[key]
    stable = schur_stable(a)
    result = None
    if p_in is not None:
        if not _symmetric(p_in) or not positive_definite(p_in):
            result = MetricFailure("metric_rejected", stable, "supplied P is not symmetric positive definite")
        elif r_in is not None:
            if 0 <= r_in < 1 and contraction_holds(a, p_in, r_in * r_in):
                result = QuadraticMetric(a, p_in, r_in * r_in, r_in, "supplied")
            else:
                result = MetricFailure("metric_rejected", stable, "supplied rho is not an accepted contraction factor")
        else:
            r = _bisect_rho(a, p_in, rho_bits)
            result = (QuadraticMetric(a, p_in, r * r, r, "supplied P, bisected rho") if r is not None
                      else MetricFailure("metric_rejected", stable, "no rho < 1 accepted for supplied P"))
    elif not stable:
        result = MetricFailure("not_schur_stable", False, "an eigenvalue lies on or outside the unit circle")
    else:
        for k in range(1, max_scale_exponent + 1):
            scale = 1 - Fraction(1, 1 << k)
            proposal = _smith(a, scale, bits, max_doublings)
            if proposal is None or not positive_definite(proposal):
                continue
            r = _bisect_rho(a, proposal, rho_bits)
            if r is not None:
                result = QuadraticMetric(a, proposal, r * r, r, f"dyadic Smith proposal, scale 1-2^-{k}")
                break
        if result is None:
            result = MetricFailure("proposal_failed", True,
                                   "A is Schur stable, but no proposal was accepted within the budget")
    _METRICS[key] = result
    return result


def _bisect_rho(a, p, bits):
    lo, hi = Fraction(0), Fraction(1)
    if contraction_holds(a, p, Fraction(0)):
        return Fraction(0)
    for _ in range(bits):
        mid = (lo + hi) / 2
        if contraction_holds(a, p, mid * mid):
            hi = mid
        else:
            lo = mid
    return hi if hi < 1 else None


def _parse_dynacomp_rational(text):
    if not isinstance(text, str):
        raise TypeError("DynaComp rationals are strings")
    parts = text.split("/")
    if len(parts) > 2 or not all(p.strip().lstrip("-").isdigit() for p in parts):
        raise ValueError(f"not a rational string: {text!r}")
    return Fraction(int(parts[0]), int(parts[1]) if len(parts) == 2 else 1)


def metric_from_dynacomp(packet, bits=64):
    """Adapter for ``dynacomp.quadratic-metric/1``: its ``gamma`` is the squared factor."""
    if not isinstance(packet, dict) or packet.get("schema") != "dynacomp.quadratic-metric/1" \
            or packet.get("status") != "certified":
        raise ValueError("need a certified dynacomp.quadratic-metric/1 packet")
    a = tuple(tuple(_parse_dynacomp_rational(x) for x in r) for r in packet["A"])
    p = tuple(tuple(_parse_dynacomp_rational(x) for x in r) for r in packet["P"])
    gamma_squared = _parse_dynacomp_rational(packet["gamma"])
    return QuadraticMetric(a, p, gamma_squared, sqrt_up(gamma_squared, bits), "dynacomp.quadratic-metric/1")


# --------------------------------------------------------------------------
# Response tails
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ResponseTail:
    """|y_k - y_inf| <= K rho^(k - anchor) for every k >= anchor."""
    system: AffineScalarSystem
    metric: QuadraticMetric
    steady_state: tuple
    steady_output: Fraction
    anchor: int
    K: Fraction

    def bound(self, k):
        k = _int(k, "k")
        if k < self.anchor:
            raise ValueError("tail bound applies only from its anchor")
        return self.K * self.metric.rho ** (k - self.anchor)

    def spec(self):
        return {"system_sha256": _digest(self.system.spec()), "metric": self.metric.spec(),
                "steady_state": _enc_vec(self.steady_state), "steady_output": encode_rational(self.steady_output),
                "anchor": self.anchor, "K": encode_rational(self.K)}


def _check_metric_for(system, metric):
    if not isinstance(metric, QuadraticMetric):
        raise TypeError("metric must be a QuadraticMetric")
    if metric.A != system.A:
        raise ValueError("metric certifies a different source matrix")
    metric.check()


def certify_response_tail(system, metric=None, *, anchor=0, anchor_state=None):
    """Exact response tail for one system; returns ResponseTail or MetricFailure."""
    if not isinstance(system, AffineScalarSystem):
        raise TypeError("system must be an AffineScalarSystem")
    anchor = _int(anchor, "anchor")
    if anchor < 0:
        raise ValueError("anchor must be nonnegative")
    if metric is None:
        metric = certify_metric(system.A)
        if isinstance(metric, MetricFailure):
            return metric
    _check_metric_for(system, metric)
    x_star = system.steady_state()
    if anchor_state is None:
        anchor_state = system.states(anchor + 1)[anchor]
    else:
        anchor_state = _vector(anchor_state, "anchor_state", system.dimension)
    d = tuple(x - y for x, y in zip(anchor_state, x_star))
    k = sqrt_up(metric.dual_norm_squared(system.c) * metric.norm_squared(d))
    return ResponseTail(system, metric, x_star, system.output(x_star), anchor, k)


@dataclass(frozen=True)
class RadiusEnvelope:
    """Declared radius rho(k) = sensor + decay*decay_rate^k + floor*(1 - floor_rate^k).

    ``sensor`` is an attainable constant error box (the only part used for
    indistinguishability).  The decay and floor parts are upper bounds only
    (initial uncertainty and persistent bounded disturbance) and are never
    used as attained lower bounds.
    """
    sensor: Fraction = Fraction(0)
    decay: Fraction = Fraction(0)
    decay_rate: Fraction = Fraction(0)
    floor: Fraction = Fraction(0)
    floor_rate: Fraction = Fraction(0)
    unit: str = "model_output"

    def __post_init__(self):
        for name in ("sensor", "decay", "decay_rate", "floor", "floor_rate"):
            value = _q(getattr(self, name), name)
            if value < 0:
                raise ValueError(f"{name} must be nonnegative")
            object.__setattr__(self, name, value)
        if self.decay_rate > 1 or self.floor_rate > 1:
            raise ValueError("rates must lie in [0, 1]")
        if not isinstance(self.unit, str) or not self.unit:
            raise ValueError("unit must be a nonempty string")

    def value(self, k):
        k = _int(k, "k")
        return self.sensor + self.decay * self.decay_rate ** k + self.floor * (1 - self.floor_rate ** k)

    def lower_after(self, k):
        """inf of value(t) over t >= k."""
        return (self.sensor + (self.decay if self.decay_rate == 1 else 0)
                + self.floor * (1 - self.floor_rate ** k))

    def upper_after(self, k):
        """sup of value(t) over t >= k."""
        return self.sensor + self.decay * self.decay_rate ** k + (self.floor if self.floor_rate < 1 else 0)

    def limit(self):
        return self.sensor + (self.decay if self.decay_rate == 1 else 0) + (self.floor if self.floor_rate < 1 else 0)

    def spec(self):
        return {"sensor_attainable": encode_rational(self.sensor), "decay_upper": encode_rational(self.decay),
                "decay_rate": encode_rational(self.decay_rate), "floor_upper": encode_rational(self.floor),
                "floor_rate": encode_rational(self.floor_rate), "unit": self.unit}

    @classmethod
    def from_spec(cls, s):
        return cls(decode_rational(s["sensor_attainable"]), decode_rational(s["decay_upper"]),
                   decode_rational(s["decay_rate"]), decode_rational(s["floor_upper"]),
                   decode_rational(s["floor_rate"]), s["unit"])


@dataclass(frozen=True)
class PairTail:
    tail_a: ResponseTail
    tail_b: ResponseTail

    def __post_init__(self):
        a, b = self.tail_a.system, self.tail_b.system
        if a.units != b.units:
            raise ValueError("inconsistent units between candidates")
        if a.protocol != b.protocol:
            raise ValueError("candidates must be compared under the same protocol and sensor")
        if a.identifier == b.identifier:
            raise ValueError("a pair needs two distinct candidates")

    @property
    def delta_inf(self):
        return self.tail_a.steady_output - self.tail_b.steady_output

    @property
    def anchor(self):
        return max(self.tail_a.anchor, self.tail_b.anchor)

    def U(self, k):
        return self.tail_a.bound(k) + self.tail_b.bound(k)


def pair_tail(tail_a, tail_b):
    return PairTail(tail_a, tail_b)


def _check_contract(units, envelope_a, envelope_b):
    for env in (envelope_a, envelope_b):
        if not isinstance(env, RadiusEnvelope):
            raise TypeError("error contract entries must be RadiusEnvelope")
        if env.unit != units.output:
            raise ValueError("inconsistent units between radius envelope and output")


def future_separation_status(pair, start, envelope_a, envelope_b):
    """Conclusion for every k >= start (start >= pair anchor).

    eventually_separating:  |delta_inf| - U(start) > sup radii   (every k >= start separates)
    never_separating_after: |delta_inf| + U(start) <= inf radii  (no k >= start separates);
        ``indistinguishable`` is added when even the attainable sensor boxes overlap.
    """
    if not isinstance(pair, PairTail):
        raise TypeError("pair must be a PairTail")
    start = _int(start, "start")
    if start < pair.anchor:
        raise ValueError("start precedes the tail anchor")
    _check_contract(pair.tail_a.system.units, envelope_a, envelope_b)
    u = pair.U(start)
    d = abs(pair.delta_inf)
    r_max = envelope_a.upper_after(start) + envelope_b.upper_after(start)
    r_min = envelope_a.lower_after(start) + envelope_b.lower_after(start)
    sensors = envelope_a.sensor + envelope_b.sensor
    record = {"start": start, "abs_delta_inf": d, "U": u, "radius_upper": r_max, "radius_lower": r_min,
              "attainable_sensor_sum": sensors, "abs_delta_lower": max(Fraction(0), d - u),
              "abs_delta_upper": d + u}
    if d - u > r_max:
        return "eventually_separating", record
    if d + u <= r_min:
        record["indistinguishable"] = d + u <= sensors
        return "never_separating_after", record
    return "inconclusive_tail", record


# --------------------------------------------------------------------------
# Costs and decisions
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class IndexCost:
    """cost(k) = setup + per_index * k with per_index > 0 (strictly increasing)."""
    setup: Fraction
    per_index: Fraction
    unit: str = "accounting_unit"

    def __post_init__(self):
        object.__setattr__(self, "setup", _q(self.setup, "setup"))
        object.__setattr__(self, "per_index", _q(self.per_index, "per_index"))
        if self.setup < 0 or self.per_index <= 0:
            raise ValueError("setup must be nonnegative and per_index positive")

    def __call__(self, k):
        return self.setup + self.per_index * _int(k, "k")

    def spec(self):
        return {"setup": encode_rational(self.setup), "per_index": encode_rational(self.per_index),
                "unit": self.unit}


# --------------------------------------------------------------------------
# Pair-difference minimal realization (the correct pair problem)
# --------------------------------------------------------------------------

def _check_pair(system_a, system_b):
    if not isinstance(system_a, AffineScalarSystem) or not isinstance(system_b, AffineScalarSystem):
        raise TypeError("systems must be AffineScalarSystem")
    if system_a.units != system_b.units:
        raise ValueError("inconsistent units between candidates")
    if system_a.protocol != system_b.protocol:
        raise ValueError("candidates must share protocol and sensor")
    if system_a.identifier == system_b.identifier:
        raise ValueError("a pair needs two distinct candidates")


def berlekamp_massey(sequence):
    """Shortest exact linear recurrence over Q: returns (L, c) with
    s_n + c_1 s_(n-1) + ... + c_L s_(n-L) = 0 for every L <= n < len(sequence)."""
    s = [_q(x, "sequence term") for x in sequence]
    c, b = [Fraction(1)], [Fraction(1)]
    L, m, bb = 0, 1, Fraction(1)
    for n in range(len(s)):
        d = s[n] + sum((c[i] * s[n - i] for i in range(1, L + 1) if i < len(c) and c[i]), Fraction(0))
        if d == 0:
            m += 1
            continue
        t = list(c)
        coef = d / bb
        if len(c) < len(b) + m:
            c = c + [Fraction(0)] * (len(b) + m - len(c))
        for i, x in enumerate(b):
            c[i + m] -= coef * x
        if 2 * L <= n:
            L, b, bb, m = n + 1 - L, t, d, 1
        else:
            m += 1
    c = c + [Fraction(0)] * (L + 1 - len(c))
    return L, tuple(c[1:L + 1])


@dataclass(frozen=True)
class PairQuotientTail:
    """delta_k - delta_inf = eta G^k zeta0 for every k >= 0, with a metric for G.

    G is the minimal (reachable from the initial offset, then observable)
    realization of the stacked pair-difference sequence.  Directions shared
    by both candidates and invisible in the difference -- for example a
    common slow mode that cancels -- are removed, so the decay rate can be
    much faster than either candidate's own rate.  ``metric`` is ``None`` only
    when the realization has order zero (the difference is constant).
    """
    system_a: AffineScalarSystem
    system_b: AffineScalarSystem
    G: tuple
    eta: tuple
    zeta0: tuple
    metric: object
    delta_inf: Fraction

    @property
    def order(self):
        return len(self.eta)

    def spec(self):
        return {"order": self.order,
                "G": _enc_mat(self.G) if self.order else None,
                "eta": _enc_vec(self.eta) if self.order else [],
                "zeta0": _enc_vec(self.zeta0) if self.order else [],
                "metric": self.metric.spec() if isinstance(self.metric, QuadraticMetric) else None,
                "delta_inf": encode_rational(self.delta_inf),
                "identity_terms": self.system_a.dimension + self.system_b.dimension + self.order}


def verify_pair_realization(system_a, system_b, G, eta, zeta0, delta_inf):
    """Exact check that delta_k - delta_inf == eta G^k zeta0 for all k >= 0.

    The stacked difference sequence is annihilated by the characteristic
    polynomial of diag(A_a, A_b) (degree N) and the reduced one by that of G
    (degree r); their difference therefore satisfies a monic recurrence of
    order N + r, and N + r consecutive zero terms force it to vanish
    identically (Cayley-Hamilton).  Raises ValueError on mismatch.
    """
    _check_pair(system_a, system_b)
    xa, xb = system_a.steady_state(), system_b.steady_state()
    if system_a.output(xa) - system_b.output(xb) != delta_inf:
        raise ValueError("stored delta_inf does not match the exact steady states")
    r = len(eta)
    terms = system_a.dimension + system_b.dimension + r
    sa, sb = system_a.states(terms), system_b.states(terms)
    zeta = tuple(zeta0)
    for k in range(terms):
        exact = system_a.output(sa[k]) - system_b.output(sb[k]) - delta_inf
        reduced = _dot(eta, zeta) if r else Fraction(0)
        if exact != reduced:
            raise ValueError(f"pair realization fails at index {k}")
        if r:
            zeta = _matvec(G, zeta)
    return True


_QUOTIENTS = {}


def certify_pair_quotient_tail(system_a, system_b, metric=None):
    """Minimal pair-difference realization plus an exact metric for it.

    Returns :class:`PairQuotientTail`, or :class:`MetricFailure` when the
    realization exists but no metric is accepted (certificate failure, not
    instability unless ``schur_stable`` is False).  Cached by the exact pair.
    """
    _check_pair(system_a, system_b)
    key = (system_a, system_b, metric)
    if key in _QUOTIENTS:
        return _QUOTIENTS[key]
    na, nb = system_a.dimension, system_b.dimension
    xa, xb = system_a.steady_state(), system_b.steady_state()
    delta_inf = system_a.output(xa) - system_b.output(xb)
    # Exact difference sequence s_k = delta_k - delta_inf for 2N terms (N = na + nb
    # bounds the order), its minimal recurrence, and the observer-form realization
    # zeta_k = (s_k, ..., s_(k+r-1)), zeta_(k+1) = G zeta_k, s_k = eta . zeta_k.
    terms = 2 * (na + nb)
    sa, sb = system_a.states(terms), system_b.states(terms)
    seq = [system_a.output(x) - system_b.output(y) - delta_inf for x, y in zip(sa, sb)]
    r, conn = berlekamp_massey(seq)
    result = None
    if r:
        G = tuple(tuple(Fraction(int(j == i + 1)) for j in range(r)) for i in range(r - 1)) + \
            (tuple(-conn[r - 1 - j] for j in range(r)),)
        eta = (Fraction(1),) + (Fraction(0),) * (r - 1)
        zeta0 = tuple(seq[:r])
        verify_pair_realization(system_a, system_b, G, eta, zeta0, delta_inf)
        if metric is None:
            metric = certify_metric(G)
        elif isinstance(metric, QuadraticMetric):
            if metric.A != G:
                raise ValueError("pair metric certifies a different reduced matrix")
            metric.check()
        if isinstance(metric, MetricFailure):
            result = metric
        else:
            result = PairQuotientTail(system_a, system_b, G, eta, zeta0, metric, delta_inf)
    if result is None:
        verify_pair_realization(system_a, system_b, (), (), (), delta_inf)
        result = PairQuotientTail(system_a, system_b, (), (), (), None, delta_inf)
    _QUOTIENTS[key] = result
    return result


class _TailEngine:
    """Bounds U_after(k) on |delta_t - delta_inf| for every t >= k+1, from exact states at k."""

    def __init__(self, system_a, system_b, metric_a, metric_b, quotient, mode):
        if mode not in ("separate", "pair_quotient", "best"):
            raise ValueError("tail_mode must be separate, pair_quotient or best")
        self.mode = mode
        self.sep = None
        if mode in ("separate", "best") and all(isinstance(m, QuadraticMetric) for m in (metric_a, metric_b)):
            xa, xb = system_a.steady_state(), system_b.steady_state()
            self.sep = (metric_a, metric_b, xa, xb, metric_a.dual_norm_squared(system_a.c),
                        metric_b.dual_norm_squared(system_b.c))
        self.quo = quotient if mode in ("pair_quotient", "best") and isinstance(quotient, PairQuotientTail) else None
        if self.quo is not None:
            self._k, self._zeta = 0, self.quo.zeta0
            self._eta_dual = (self.quo.metric.dual_norm_squared(self.quo.eta) if self.quo.order else None)
        xa, xb = system_a.steady_state(), system_b.steady_state()
        self.delta_inf = system_a.output(xa) - system_b.output(xb)

    @property
    def available(self):
        return self.sep is not None or self.quo is not None

    def after(self, k, state_a, state_b):
        bounds = {}
        if self.sep is not None:
            ma, mb, xa, xb, ca, cb = self.sep
            ka = _anchored_K(ma, ca, state_a, xa)
            kb = _anchored_K(mb, cb, state_b, xb)
            bounds["separate"] = ka * ma.rho + kb * mb.rho
        if self.quo is not None:
            if k < self._k:
                raise ValueError("tail engine indices must be nondecreasing")
            while self._k < k:
                self._zeta = _matvec(self.quo.G, self._zeta) if self.quo.order else ()
                self._k += 1
            if self.quo.order:
                kq = sqrt_up(self._eta_dual * self.quo.metric.norm_squared(self._zeta))
                bounds["pair_quotient"] = kq * self.quo.metric.rho
            else:
                bounds["pair_quotient"] = Fraction(0)
        if not bounds:
            return None, None
        source = min(bounds, key=lambda name: (bounds[name], name))
        return bounds[source], source


def _anchored_K(metric, c_dual_sq, state, x_star):
    d = tuple(x - y for x, y in zip(state, x_star))
    return sqrt_up(c_dual_sq * metric.norm_squared(d))


def _metric_summary(m):
    if isinstance(m, QuadraticMetric):
        return m.spec()
    if isinstance(m, MetricFailure):
        return {"status": m.status, "schur_stable": m.schur_stable, "reason": m.reason}
    return None


def _setup(system_a, system_b, envelope_a, envelope_b, metric_a, metric_b, pair_metric, tail_mode):
    _check_pair(system_a, system_b)
    _check_contract(system_a.units, envelope_a, envelope_b)
    metrics = []
    for system, metric in ((system_a, metric_a), (system_b, metric_b)):
        if tail_mode == "pair_quotient":
            metrics.append(None)
            continue
        if metric is None:
            metric = certify_metric(system.A)
        if isinstance(metric, QuadraticMetric):
            _check_metric_for(system, metric)
        metrics.append(metric)
    quotient = None
    if tail_mode in ("pair_quotient", "best"):
        quotient = certify_pair_quotient_tail(system_a, system_b, pair_metric)
    engine = _TailEngine(system_a, system_b, metrics[0], metrics[1], quotient, tail_mode)
    return metrics, quotient, engine


def _base_record(kind, system_a, system_b, envelope_a, envelope_b, metrics, quotient, engine, params):
    qspec = None
    if isinstance(quotient, PairQuotientTail):
        qspec = quotient.spec()
    elif isinstance(quotient, MetricFailure):
        qspec = {"metric": _metric_summary(quotient)}
    return {"schema": SCHEMA, "kind": kind, "scope": SCOPE, "reset_contract": "independent_reset",
            "threshold": THRESHOLD_CONVENTION,
            "systems": [system_a.spec(), system_b.spec()],
            "system_sha256": [_digest(system_a.spec()), _digest(system_b.spec())],
            "radius_envelopes": [envelope_a.spec(), envelope_b.spec()],
            "metrics": [_metric_summary(m) for m in metrics],
            "pair_quotient": qspec,
            "steady_outputs": _enc([system_a.output(system_a.steady_state()),
                                    system_b.output(system_b.steady_state())]),
            "delta_inf": encode_rational(engine.delta_inf),
            "parameters": params}


@dataclass(frozen=True)
class HorizonResult:
    status: str
    record: dict


def _validate_common(max_prefix, min_index, tail_mode):
    max_prefix, min_index = _int(max_prefix, "max_prefix"), _int(min_index, "min_index")
    if min_index < 0 or max_prefix < min_index:
        raise ValueError("need 0 <= min_index <= max_prefix")
    if tail_mode not in ("separate", "pair_quotient", "best"):
        raise ValueError("tail_mode must be separate, pair_quotient or best")
    return max_prefix, min_index


def minimum_step_horizon(system_a, system_b, envelope_a, envelope_b, cost, *, max_prefix,
                         min_index=0, metric_a=None, metric_b=None, pair_metric=None,
                         tail_mode="best", incumbent_cost=None):
    """Cheapest certified separating index for one pair under one fixed protocol.

    Indices ``min_index..T`` are evaluated exactly.  Because cost is strictly
    increasing, the first separating index is the minimum-cost experiment of
    this family.  After each non-separating index T a tail anchored at the
    exact state at T bounds every later index; when it proves no later
    separation the family is certified never to separate (status
    ``never_separating_after``).  ``incumbent_cost`` (cost of a separating
    experiment known elsewhere) stops the search once cost(k) >= incumbent.
    """
    if not isinstance(cost, IndexCost):
        raise TypeError("cost must be an IndexCost")
    max_prefix, min_index = _validate_common(max_prefix, min_index, tail_mode)
    incumbent = None if incumbent_cost is None else _q(incumbent_cost, "incumbent_cost")
    metrics, quotient, engine = _setup(system_a, system_b, envelope_a, envelope_b, metric_a, metric_b,
                                       pair_metric, tail_mode)
    params = {"max_prefix": max_prefix, "min_index": min_index, "cost": cost.spec(), "tail_mode": tail_mode,
              "incumbent_cost": None if incumbent is None else encode_rational(incumbent)}
    rec = _base_record("minimum_horizon", system_a, system_b, envelope_a, envelope_b, metrics, quotient,
                       engine, params)
    delta_inf = engine.delta_inf
    states_a, states_b = system_a.states(max_prefix + 1), system_b.states(max_prefix + 1)
    prefix_digest = hashlib.sha256()
    indistinguishable_prefix = True
    sensors = envelope_a.sensor + envelope_b.sensor
    u = source = None

    def finish(**fields):
        rec.update(fields)
        rec["prefix_sha256"] = prefix_digest.hexdigest()
        return HorizonResult(rec["status"], _enc(rec))
    for k in range(min_index, max_prefix + 1):
        if incumbent is not None and cost(k) >= incumbent:
            return finish(status="finite_optimum_certified", witness="incumbent",
                          optimum_cost=encode_rational(incumbent), checked_through=k - 1,
                          claim="accounting cutoff: every index with cost below the incumbent was "
                                "checked exactly and none separates, so the incumbent is cheapest")
        ya, yb = system_a.output(states_a[k]), system_b.output(states_b[k])
        delta = ya - yb
        prefix_digest.update(json.dumps([k, encode_rational(ya), encode_rational(yb)]).encode())
        radius = envelope_a.value(k) + envelope_b.value(k)
        if abs(delta) > sensors:
            indistinguishable_prefix = False
        if abs(delta) > radius:
            return finish(status="finite_optimum_certified", witness="prefix", horizon=k,
                          cost_value=encode_rational(cost(k)), delta=encode_rational(delta),
                          radius=encode_rational(radius), checked_through=k,
                          claim="minimum-cost certified separating index of this protocol family: every "
                                "earlier index was evaluated exactly and does not separate")
        u, source = engine.after(k, states_a[k], states_b[k])
        if u is None:
            continue
        r_min = envelope_a.lower_after(k + 1) + envelope_b.lower_after(k + 1)
        if abs(delta_inf) + u <= r_min:
            indist = indistinguishable_prefix and abs(delta_inf) + u <= sensors
            return finish(status="never_separating_after", after=k + 1, checked_through=k,
                          tail={"anchor": k, "source": source, "U_after": encode_rational(u),
                                "radius_lower_after": encode_rational(r_min)},
                          indistinguishable_all_indices=indist,
                          claim=f"no index >= min_index certifies separation: indices through {k} were "
                                "checked exactly and |delta_inf| + U <= inf radii for every later index"
                                + ("; the attainable sensor boxes overlap at every index" if indist else ""))
    if engine.available:
        return finish(status="inconclusive_tail", checked_through=max_prefix,
                      tail={"anchor": max_prefix, "source": source, "U_after": encode_rational(u)},
                      claim="no separation through the prefix; the tail bound is still loose, which is "
                            "not evidence of impossibility")
    return finish(status="resource_limit", checked_through=max_prefix,
                  claim="no tail metric accepted; only the finite prefix is decided")


def maximum_margin_horizon(system_a, system_b, envelope_a, envelope_b, *, max_prefix, epsilon,
                           min_index=0, metric_a=None, metric_b=None, pair_metric=None, tail_mode="best"):
    """Maximum certified margin m(k) = |delta_k| - (rho_a(k) + rho_b(k)) over all k >= min_index.

    For each prefix end T, F(T) = |delta_inf| + U_after(T) - inf_{k>T} radii
    bounds every later margin.  F < best certifies a global finite optimum;
    F == best certifies the optimal value (later ties not excluded).
    Otherwise sup m lies in [max(best, L), F] with L = |delta_inf| - lim radii
    (approached, not necessarily attained); once F - best <= epsilon the best
    prefix index is an epsilon-optimal finite experiment.  Attainment of the
    supremum is never claimed in that case.
    """
    max_prefix, min_index = _validate_common(max_prefix, min_index, tail_mode)
    epsilon = _q(epsilon, "epsilon")
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    metrics, quotient, engine = _setup(system_a, system_b, envelope_a, envelope_b, metric_a, metric_b,
                                       pair_metric, tail_mode)
    params = {"max_prefix": max_prefix, "min_index": min_index, "epsilon": encode_rational(epsilon),
              "tail_mode": tail_mode}
    rec = _base_record("maximum_margin", system_a, system_b, envelope_a, envelope_b, metrics, quotient,
                       engine, params)
    delta_inf = engine.delta_inf
    limit = abs(delta_inf) - envelope_a.limit() - envelope_b.limit()
    rec["limit_margin"] = encode_rational(limit)
    states_a, states_b = system_a.states(max_prefix + 1), system_b.states(max_prefix + 1)
    best, argmax, upper = None, [], None
    prefix_digest = hashlib.sha256()
    for k in range(min_index, max_prefix + 1):
        ya, yb = system_a.output(states_a[k]), system_b.output(states_b[k])
        prefix_digest.update(json.dumps([k, encode_rational(ya), encode_rational(yb)]).encode())
        m = abs(ya - yb) - envelope_a.value(k) - envelope_b.value(k)
        if best is None or m > best:
            best, argmax = m, [k]
        elif m == best:
            argmax.append(k)
        u, source = engine.after(k, states_a[k], states_b[k])
        if u is None:
            continue
        upper = abs(delta_inf) + u - envelope_a.lower_after(k + 1) - envelope_b.lower_after(k + 1)
        common = {"checked_through": k, "best_margin": encode_rational(best), "argmax": argmax,
                  "future_upper": encode_rational(upper), "tail_source": source,
                  "prefix_sha256": prefix_digest.hexdigest()}
        if upper <= best:
            rec.update(status="finite_optimum_certified", optimum=encode_rational(best), **common,
                       later_ties_excluded=upper < best,
                       claim="global maximum certified margin over every index >= min_index, attained at "
                             "the recorded prefix indices" + ("" if upper < best else
                                                              "; a later index may tie but cannot exceed it"))
            return HorizonResult(rec["status"], _enc(rec))
        if upper - best <= epsilon:
            rec.update(status="supremum_bracket", **common,
                       bracket=_enc([max(best, limit), upper]), epsilon_optimal_index=argmax[0],
                       attainment="not_certified",
                       claim="the supremum over all indices lies in the bracket and the recorded index is "
                             "epsilon-optimal; no claim that the supremum is attained")
            return HorizonResult(rec["status"], _enc(rec))
    rec.update(status="resource_limit", checked_through=max_prefix, best_margin=encode_rational(best),
               argmax=argmax, prefix_sha256=prefix_digest.hexdigest(),
               claim="prefix budget exhausted before the bracket closed to epsilon")
    if upper is not None:
        rec["bracket"] = _enc([max(best, limit), max(best, upper)])
    return HorizonResult(rec["status"], _enc(rec))


# --------------------------------------------------------------------------
# Replay
# --------------------------------------------------------------------------

def replay_horizon_result(record):
    """Validate every stored exact object, then recompute the decision.

    Checks: schema, scope and reset contract; canonical rationals; system
    digests; each metric is positive definite with semidefinite squared
    contraction, gamma_squared < 1, rho^2 >= gamma_squared, and certifies the
    stored matrix; stored steady outputs satisfy (I - A) x* = b; the stored
    pair realization reproduces the difference sequence (finite exact
    Cayley-Hamilton check); units and protocols agree.  The decision is then
    recomputed with the stored metrics and must match field for field.
    """
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        raise ValueError("need a singularity.horizon-design/1 record")
    if record.get("scope") != SCOPE or record.get("reset_contract") != "independent_reset" \
            or record.get("threshold") != THRESHOLD_CONVENTION:
        raise ValueError("record scope, threshold or reset contract was altered")
    systems = [AffineScalarSystem.from_spec(s) for s in record["systems"]]
    if [_digest(s.spec()) for s in systems] != record["system_sha256"]:
        raise ValueError("system digest mismatch")
    _check_pair(*systems)
    envelopes = [RadiusEnvelope.from_spec(e) for e in record["radius_envelopes"]]
    _check_contract(systems[0].units, *envelopes)
    stored = [decode_rational(x) for x in record["steady_outputs"]]
    for system, value in zip(systems, stored):
        if system.output(system.steady_state()) != value:
            raise ValueError("stored steady state does not satisfy (I - A) x* = b")
    metrics = []
    for system, spec in zip(systems, record["metrics"]):
        if spec is not None and "schema" in spec:
            metric = QuadraticMetric.from_spec(spec)
            _check_metric_for(system, metric)
            metrics.append(metric)
        else:
            metrics.append(None)
    pair_metric = None
    q = record["pair_quotient"]
    if q is not None and q.get("G") is not None:
        G = _dec_mat(q["G"], "G")
        verify_pair_realization(systems[0], systems[1], G, _dec_vec(q["eta"], "eta"),
                                _dec_vec(q["zeta0"], "zeta0"), decode_rational(q["delta_inf"]))
        if q["metric"] is not None:
            pair_metric = QuadraticMetric.from_spec(q["metric"])
            if pair_metric.A != G:
                raise ValueError("pair metric certifies a different reduced matrix")
    p = record["parameters"]
    if record["kind"] == "minimum_horizon":
        c = p["cost"]
        cost = IndexCost(decode_rational(c["setup"]), decode_rational(c["per_index"]), c["unit"])
        fresh = minimum_step_horizon(systems[0], systems[1], envelopes[0], envelopes[1], cost,
                                     max_prefix=p["max_prefix"], min_index=p["min_index"],
                                     metric_a=metrics[0], metric_b=metrics[1], pair_metric=pair_metric,
                                     tail_mode=p["tail_mode"],
                                     incumbent_cost=None if p["incumbent_cost"] is None
                                     else decode_rational(p["incumbent_cost"]))
    elif record["kind"] == "maximum_margin":
        fresh = maximum_margin_horizon(systems[0], systems[1], envelopes[0], envelopes[1],
                                       max_prefix=p["max_prefix"], epsilon=decode_rational(p["epsilon"]),
                                       min_index=p["min_index"], metric_a=metrics[0], metric_b=metrics[1],
                                       pair_metric=pair_metric, tail_mode=p["tail_mode"])
    else:
        raise ValueError("unknown record kind")
    if fresh.record != record:
        diff = sorted(k for k in set(fresh.record) | set(record) if fresh.record.get(k) != record.get(k))
        raise ValueError(f"stored decision differs from recomputation in {diff}")
    return True


__all__ = [
    "SCHEMA", "STATUSES", "SCOPE", "Units", "LinearCandidate", "AffineScalarSystem", "StepFamily",
    "step_system", "block_system", "QuadraticMetric", "MetricFailure", "certify_metric",
    "metric_from_dynacomp", "contraction_holds", "positive_definite", "positive_semidefinite",
    "schur_stable", "charpoly", "sqrt_up", "ResponseTail", "certify_response_tail", "RadiusEnvelope",
    "PairTail", "pair_tail", "future_separation_status", "PairQuotientTail", "certify_pair_quotient_tail",
    "verify_pair_realization", "IndexCost", "HorizonResult", "minimum_step_horizon",
    "maximum_margin_horizon", "replay_horizon_result", "encode_rational", "decode_rational",
]
