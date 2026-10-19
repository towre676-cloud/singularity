"""NX31 exact differential observations and source-pinned validated transport.

The Q(t) scalar-equation and Taylor transport engines are the archived,
Apache-2.0 PerfectPower implementations.  This adapter validates Singularity's
strict exact inputs, retains chart exclusions, and separates initial from
arithmetic enclosure errors.  No graph/period identification is assumed.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from pathlib import Path
from itertools import combinations
import importlib
import sys


def _backend(name):
    root = Path(__file__).resolve().parents[2]
    path = root / "handoff/nx36/companion_sources/perfectpower/python"
    if not (path / "perfectpower/rational_functions.py").is_file():
        raise ValueError("the licensed pinned PerfectPower source archive is required")
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
    return importlib.import_module("perfectpower." + name)


def _q(value):
    if isinstance(value, bool) or not isinstance(value, (int, Q)):
        raise TypeError("exact entries require int or Fraction")
    return Q(value)


def _rf(value):
    rf = _backend("rational_functions").RationalFunction
    if isinstance(value, rf):
        return value
    if isinstance(value, dict):
        if set(value) != {"numerator", "denominator"}:
            raise ValueError("rational functions require numerator and denominator")
        n, d = value["numerator"], value["denominator"]
    elif isinstance(value, (tuple, list)):
        n, d = value, (1,)
    else:
        n, d = (_q(value),), (1,)
    if not n or not d or max(len(n), len(d)) > 7:
        raise ValueError("input polynomial degree must be at most six")
    return rf(tuple(map(_q, n)), tuple(map(_q, d)))


def _matrix(matrix, columns=None):
    out = tuple(tuple(_rf(v) for v in row) for row in matrix)
    if columns is None:
        columns = len(out)
    if any(len(row) != columns for row in out):
        raise ValueError("matrix dimension mismatch")
    return out


def _product(a, b):
    if not a:
        return ()
    return tuple(tuple(sum((x * y for x, y in zip(row, col)), _rf(0))
                       for col in zip(*b)) for row in a)


def _coordinates(row, basis):
    if not basis:
        return () if not any(row) else None
    solved = _backend("rational_functions").solve_many(
        list(map(list, zip(*basis))), [[v] for v in row])
    return None if solved is None else tuple(v[0] for v in solved)


def _derivative_row(row, matrix):
    product = _product((row,), matrix)[0]
    return tuple(v.derivative() + w for v, w in zip(row, product))


def _excluded(matrices):
    polys = set()
    for matrix in matrices:
        for row in matrix:
            for value in row:
                if len(value.d) > 1:
                    polys.add(tuple(value.d))
    return polys


@dataclass(frozen=True)
class RationalConnection:
    matrix: tuple
    chart: tuple
    source_revision: str
    interpretation: str = "supplied rational differential system"

    def __init__(self, matrix, chart=(-1, 1), source_revision="explicit-input",
                 interpretation="supplied rational differential system"):
        a = _matrix(matrix)
        if not 1 <= len(a) <= 4:
            raise ValueError("supported connection dimension is one through four")
        if any(max(len(v.n),len(v.d))>7 for row in a for v in row):
            raise ValueError("input coefficient degree must be at most six")
        lo, hi = map(_q, chart)
        if lo >= hi or not isinstance(source_revision, str) or not source_revision:
            raise ValueError("an ordered chart and source revision are required")
        object.__setattr__(self, "matrix", a)
        object.__setattr__(self, "chart", (lo, hi))
        object.__setattr__(self, "source_revision", source_revision)
        object.__setattr__(self, "interpretation", interpretation)

    @property
    def dimension(self):
        return len(self.matrix)


@dataclass(frozen=True)
class DifferentialClosure:
    basis: tuple
    reduced_connection: tuple
    target_coordinates: tuple
    targets: tuple
    excluded_polynomials: tuple
    scalar_equations: tuple

    @property
    def rank(self):
        return len(self.basis)


def differential_closure(connection, targets):
    """Small exact observable submodule; scalar engines are reused, not copied."""
    if not isinstance(connection, RationalConnection):
        raise TypeError("RationalConnection required")
    targets = _matrix(targets, connection.dimension)
    module = _backend("differential_modules").DifferentialModule({
        "matrix": [[v.packet() for v in row] for row in connection.matrix]})
    scalar = tuple(module.observable(list(row)) for row in targets)
    basis, queue = [], list(targets)
    while queue:
        row = queue.pop(0)
        if _coordinates(row, basis) is not None:
            continue
        if len(basis) >= connection.dimension:
            raise ArithmeticError("field row closure exceeded ambient dimension")
        basis.append(row)
        queue.append(_derivative_row(row, connection.matrix))
    reduced = tuple(_coordinates(_derivative_row(row, connection.matrix), basis)
                    for row in basis)
    coords = tuple(_coordinates(row, basis) for row in targets)
    excluded = _excluded((connection.matrix, basis, reduced, coords))
    if basis:
        # A nonzero pivot minor specifies the actual constant-rank chart.
        for columns in combinations(range(connection.dimension), len(basis)):
            minor = [[row[j] for j in columns] for row in basis]
            determinant = _backend("rational_functions").determinant(minor)
            if determinant:
                if len(determinant.n) > 1:
                    excluded.add(tuple(determinant.n))
                break
    result = DifferentialClosure(tuple(basis), reduced, coords, targets,
                                 tuple(sorted(excluded)), scalar)
    if not verify_differential_closure(connection, result):
        raise ArithmeticError("differential closure identities did not replay")
    return result


def verify_differential_closure(connection, result):
    try:
        if len(result.reduced_connection) != result.rank:
            return False
        if len(result.targets)!=len(result.target_coordinates):
            return False
        independent=[]
        for row in result.basis:
            if len(row)!=connection.dimension or _coordinates(row,independent)is not None:
                return False
            independent.append(row)
        # Closedness and target containment alone would permit a forged larger
        # invariant subspace. For each seed the first ambient n derivatives
        # span its cyclic differential submodule: a first dependence at r<=n
        # remains a dependence after differentiation, including coefficient
        # derivatives. Their union therefore generates the observable module.
        generated=[]
        for seed in result.targets:
            row=seed
            for _ in range(connection.dimension):
                if _coordinates(row,generated)is None:generated.append(row)
                row=_derivative_row(row,connection.matrix)
        if len(generated)!=result.rank or any(_coordinates(row,generated)is None for row in result.basis):
            return False
        if not result.rank:
            return (not any(any(row) for row in result.targets)
                    and all(not row for row in result.target_coordinates))
        lhs = tuple(_derivative_row(row, connection.matrix) for row in result.basis)
        return (lhs == _product(result.reduced_connection, result.basis)
                and _product(result.target_coordinates, result.basis) == result.targets)
    except (ValueError, TypeError, IndexError):
        return False


def _poly_interval(poly, lo, hi):
    a = b = Q(0)
    for value in reversed(poly):
        products = (a * lo, a * hi, b * lo, b * hi)
        a, b = min(products) + value, max(products) + value
    return a, b


def assert_regular_segment(connection, start, end, excluded=()):
    start, end = _q(start), _q(end)
    lo, hi = sorted((start, end))
    if lo < connection.chart[0] or hi > connection.chart[1]:
        raise ValueError("transport path leaves the declared chart")
    polys = _excluded((connection.matrix,)) | set(excluded)
    for p in polys:
        a, b = _poly_interval(p, lo, hi)
        if a <= 0 <= b:
            raise ValueError("path may cross an excluded connection or pivot zero")


def transport_targets(connection, targets, path, initial, initial_radii=None,
                      *, order=16, rounding_bits=96):
    """Real polygon transport with separate source-initial and numerical radii.

    A conservative polynomial interval check may refuse a safe chart.  It never
    licenses division across an unverified pole.  Errors are L-infinity state
    radii and absolute scalar output radii.
    """
    path = tuple(map(_q, path))
    if len(path) < 2:
        raise ValueError("at least two path vertices required")
    for a, b in zip(path, path[1:]):
        assert_regular_segment(connection, a, b)
    initial = tuple(map(_q, initial))
    if len(initial) != connection.dimension:
        raise ValueError("initial dimension mismatch")
    radii = ((Q(0),) * connection.dimension if initial_radii is None else
             tuple(map(_q, initial_radii)))
    if len(radii) != connection.dimension or any(v < 0 for v in radii):
        raise ValueError("one nonnegative initial radius per state required")
    backend = _backend("certified_period_transport")
    receipt = backend.certified_transport(
        [[v.packet() for v in row] for row in connection.matrix],
        list(path), order=order, rounding_bits=rounding_bits)
    s = tuple(tuple(Q(v[0]) for v in row) for row in receipt["matrix"])
    error = Q(receipt["row_error_bound"])
    norms = tuple(sum(map(abs, row), Q(0)) for row in s)
    numerical = error * max(map(abs, initial), default=Q(0))
    initial_error = tuple(sum((abs(v) * e for v, e in zip(row, radii)), Q(0))
                          + error * max(radii, default=Q(0)) for row in s)
    state = tuple(sum((v * x for v, x in zip(row, initial)), Q(0)) for row in s)
    outputs = []
    for row in _matrix(targets, connection.dimension):
        c = tuple(v.evaluate(path[-1]) for v in row)
        centre = sum((v * x for v, x in zip(c, state)), Q(0))
        source = sum((abs(v) * e for v, e in zip(c, initial_error)), Q(0))
        arithmetic = sum(map(abs, c), Q(0)) * numerical
        outputs.append({"centre": centre, "initial_error": source,
                        "numerical_error": arithmetic,
                        "interval": (centre-source-arithmetic, centre+source+arithmetic)})
    return {"schema": "singularity.period-target-transport/1", "outputs": tuple(outputs),
            "transport": receipt, "source_revision": connection.source_revision,
            "scope": "declared regular real chart and supplied initial enclosure"}


def legendre_connection(chart=(Q(1, 8), Q(7, 8))):
    t = _rf((0, 1)); one = _rf(1)
    return RationalConnection(((0, 1), (one/(4*t*(1-t)), (2*t-1)/(t*(1-t)))),
        chart, "pinned-PerfectPower-certified_period_transport.py:Legendre",
        "normalized Legendre period F(t)=2K(t)/pi")


def legendre_series(t, terms=64):
    """Independent hypergeometric seed enclosure; no transport engine used."""
    from math import comb
    t = _q(t)
    if not 0 <= t < 1 or type(terms) is not int or terms < 1:
        raise ValueError("0<=t<1 and positive terms required")
    centre = sum((Q(comb(2*k, k)**2, 16**k) * t**k for k in range(terms+1)), Q(0))
    derivative = sum((Q(comb(2*k, k)**2, 16**k) * k * t**(k-1)
                      for k in range(1, terms+1)), Q(0))
    return (centre, derivative), (t**(terms+1)/(1-t),
                                 t**terms*((terms+1)-terms*t)/(1-t)**2)


def legendre_quadrature(t,steps=128,bits=48):
    """Independent rational interval quadrature of a smooth Euler integral.

    F(t)=4/pi * integral_0^1 [1+(2-4t)v^2+v^4]^-1/2 dv.  It is obtained
    from the usual complete elliptic integral by v=tan(theta/2). Bounds use
    interval ranges on each subinterval; no differential equation or series
    coefficients are used. Machin's alternating arctangent formula bounds pi.
    """
    from .complex_visibility import root_interval
    t=_q(t)
    if not 0<=t<1 or type(steps)is not int or not 1<=steps<=4096:
        raise ValueError("0<=t<1 and one through4096 quadrature cells required")
    def atan_bounds(x,terms=48):
        value=sum(((-1)**k*x**(2*k+1)/(2*k+1)for k in range(terms)),Q(0))
        following=value+(-1)**terms*x**(2*terms+1)/(2*terms+1)
        return min(value,following),max(value,following)
    a,b=atan_bounds(Q(1,5));c,d=atan_bounds(Q(1,239))
    pi_lo,pi_hi=16*a-4*d,16*b-4*c
    integral_lo=integral_hi=Q(0);coefficient=2-4*t
    for j in range(steps):
        a,b=Q(j,steps),Q(j+1,steps)
        p0=1+min(coefficient*a*a,coefficient*b*b)+a**4
        p1=1+max(coefficient*a*a,coefficient*b*b)+b**4
        if p0<=0:raise ValueError("quadrature range is too coarse")
        lo,_=root_interval(p0,2,bits);_,hi=root_interval(p1,2,bits)
        integral_lo+=1/(steps*hi);integral_hi+=1/(steps*lo)
    return 4*integral_lo/pi_hi,4*integral_hi/pi_lo
