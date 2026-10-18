"""Exact finite observation closure with realizable, minimum-cost witnesses.

States are columns.  A word (i1,...,im) applies i1 first, so its
measurement is L_j M_im ... M_i1.  Row expansion therefore PREPENDS a
letter.  The certificate proves L=A B and B M_i=T_i B, retaining original
experiment rows B rather than elimination residuals as witnesses.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import heapq
from itertools import count
from typing import Sequence

Row = tuple[Fraction, ...]
Matrix = tuple[Row, ...]
_SCHEMA = "singularity.operator-closure/1"


def _q(value) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise ValueError("exact rational values must be integers or Fractions")
    return Fraction(value)


def _row(values, dimension: int) -> Row:
    result = tuple(_q(x) for x in values)
    if len(result) != dimension:
        raise ValueError("row dimension mismatch")
    return result


def _matrix(values, rows: int, columns: int) -> Matrix:
    result = tuple(_row(row, columns) for row in values)
    if len(result) != rows:
        raise ValueError("matrix dimension mismatch")
    return result


def _dot(a, b):
    return sum((x*y for x, y in zip(a, b)), Fraction(0))


def row_times_matrix(row: Row, matrix: Matrix, columns: int | None = None) -> Row:
    """Row vector times matrix.  ``columns`` is required when ``matrix`` has no
    rows: a combination of zero basis rows is the zero vector of the ambient
    dimension, which an empty matrix cannot report by itself."""
    if len(row) != len(matrix):
        raise ValueError("matrix dimension mismatch")
    if columns is None:
        if not matrix:
            raise ValueError("an empty matrix needs an explicit column count")
        columns = len(matrix[0])
    if any(len(r) != columns for r in matrix):
        raise ValueError("matrix dimension mismatch")
    return tuple(sum((row[k]*matrix[k][j] for k in range(len(row))), Fraction(0))
                 for j in range(columns))


def matrix_times_vector(matrix: Matrix, vector: Row) -> Row:
    if any(len(row) != len(vector) for row in matrix):
        raise ValueError("matrix dimension mismatch")
    return tuple(_dot(row, vector) for row in matrix)


@dataclass(frozen=True)
class OperatorSystem:
    dimension: int
    operators: tuple[Matrix, ...]
    observations: Matrix
    attachment_costs: tuple[Fraction, ...]
    observation_costs: tuple[Fraction, ...]

    def __init__(self, dimension: int, operators: Sequence[Matrix],
                 observations: Sequence[Row], attachment_costs=None,
                 observation_costs=None):
        if isinstance(dimension, bool) or not isinstance(dimension, int) or dimension < 0:
            raise ValueError("dimension must be a nonnegative integer")
        ops = tuple(_matrix(m, dimension, dimension) for m in operators)
        obs = tuple(_row(row, dimension) for row in observations)
        ac = tuple(_q(c) for c in (attachment_costs if attachment_costs is not None
                                   else [1]*len(ops)))
        oc = tuple(_q(c) for c in (observation_costs if observation_costs is not None
                                   else [0]*len(obs)))
        if len(ac) != len(ops) or any(c <= 0 for c in ac):
            raise ValueError("attachment costs must be positive, one per operator")
        if len(oc) != len(obs) or any(c < 0 for c in oc):
            raise ValueError("observation costs must be nonnegative, one per row")
        object.__setattr__(self, "dimension", dimension)
        object.__setattr__(self, "operators", ops)
        object.__setattr__(self, "observations", obs)
        object.__setattr__(self, "attachment_costs", ac)
        object.__setattr__(self, "observation_costs", oc)


@dataclass(frozen=True)
class Experiment:
    observation: int
    word: tuple[int, ...]
    row: Row
    cost: Fraction


@dataclass(frozen=True)
class ClosureCertificate:
    basis: tuple[Experiment, ...]
    observation_coordinates: Matrix
    transition_coordinates: tuple[Matrix, ...]
    nullspace: Matrix
    pivots: tuple[int, ...]

    @property
    def rank(self):
        return len(self.basis)

    @property
    def invisible_subspace(self):
        """Rows spanning N = ker B, the states no permitted experiment can see."""
        return self.nullspace

    @property
    def rows(self):
        return tuple(e.row for e in self.basis)

    @property
    def quotient_operators(self):
        return self.transition_coordinates

    @property
    def quotient_observations(self):
        return self.observation_coordinates


def _index(value, size):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < size:
        raise ValueError("invalid observation or operator index")
    return value


def _exact(value) -> bool:
    return type(value) is Fraction


def _exact_row(value, size) -> bool:
    return type(value) is tuple and len(value) == size and all(_exact(x) for x in value)


def _exact_matrix(value, rows, columns) -> bool:
    return type(value) is tuple and len(value) == rows and all(_exact_row(r, columns) for r in value)


def _exact_index(value, size) -> bool:
    return type(value) is int and 0 <= value < size


def _well_typed(system: OperatorSystem, certificate) -> bool:
    """The in-memory analogue of portable replay's strict decoding.

    Ordinary equality identifies Fraction(0), 0, 0.0 and False; a certificate
    is accepted only when every stored number is a Fraction, every index and
    pivot an int (not bool), and every container a tuple of the stated size.
    """
    if not isinstance(system, OperatorSystem) or type(certificate) is not ClosureCertificate:
        return False
    n, o, g = system.dimension, len(system.observations), len(system.operators)
    basis = certificate.basis
    if type(basis) is not tuple or len(basis) > n:
        return False
    r = len(basis)
    for e in basis:
        if type(e) is not Experiment or not _exact_index(e.observation, o) or not _exact(e.cost):
            return False
        if type(e.word) is not tuple or not all(_exact_index(i, g) for i in e.word):
            return False
        if not _exact_row(e.row, n):
            return False
    if not _exact_matrix(certificate.observation_coordinates, o, r):
        return False
    t = certificate.transition_coordinates
    if type(t) is not tuple or len(t) != g or not all(_exact_matrix(m, r, r) for m in t):
        return False
    if not _exact_matrix(certificate.nullspace, n - r, n):
        return False
    p = certificate.pivots
    return type(p) is tuple and len(p) == r and all(_exact_index(i, n) for i in p)


def experiment(system: OperatorSystem, observation: int, word=()) -> Experiment:
    observation = _index(observation, len(system.observations))
    word = tuple(_index(i, len(system.operators)) for i in word)
    row = system.observations[observation]
    for i in reversed(word):
        row = row_times_matrix(row, system.operators[i])
    cost = system.observation_costs[observation] + sum(
        (system.attachment_costs[i] for i in word), Fraction(0))
    return Experiment(observation, word, row, cost)


def apply_word(system: OperatorSystem, state, word=()) -> Row:
    state = _row(state, system.dimension)
    for i in word:
        state = matrix_times_vector(system.operators[_index(i, len(system.operators))], state)
    return state


def _echelon(rows: Matrix, dimension: int):
    """RREF and its row-operation matrix, both exact over Q."""
    n = len(rows)
    a = [list(row) for row in rows]
    coefficients = [[Fraction(i == j) for j in range(n)] for i in range(n)]
    pivots = []
    for col in range(dimension):
        k = next((i for i in range(len(pivots), n) if a[i][col]), None)
        if k is None:
            continue
        r = len(pivots)
        a[r], a[k] = a[k], a[r]
        coefficients[r], coefficients[k] = coefficients[k], coefficients[r]
        divisor = a[r][col]
        a[r] = [v/divisor for v in a[r]]
        coefficients[r] = [v/divisor for v in coefficients[r]]
        for i in range(n):
            if i != r and a[i][col]:
                factor = a[i][col]
                a[i] = [u-factor*v for u, v in zip(a[i], a[r])]
                coefficients[i] = [u-factor*v for u, v in zip(coefficients[i], coefficients[r])]
        pivots.append(col)
        if len(pivots) == n:
            break
    return tuple(tuple(r) for r in a[:len(pivots)]), tuple(
        tuple(r) for r in coefficients[:len(pivots)]), tuple(pivots)


def _coordinates(row, reduced, operations, pivots, rank):
    residual = list(row)
    answer = [Fraction(0)]*rank
    for rr, cc, pivot in zip(reduced, operations, pivots):
        factor = residual[pivot]
        if factor:
            residual = [u-factor*v for u, v in zip(residual, rr)]
            answer = [u+factor*v for u, v in zip(answer, cc)]
    return tuple(answer) if not any(residual) else None


def _kernel(reduced, pivots, dimension):
    result = []
    for free in range(dimension):
        if free not in pivots:
            row = [Fraction(0)]*dimension
            row[free] = Fraction(1)
            for rr, pivot in zip(reduced, pivots):
                row[pivot] = -rr[free]
            result.append(tuple(row))
    return tuple(result)


def observable_closure(system: OperatorSystem) -> ClosureCertificate:
    """Compute the least invariant observation space, in increasing cost.

    Only independent REAL experiment rows are expanded.  A discarded row
    lies in the span of rows costing no more; right multiplication preserves
    that relation and adds the same positive cost to every replacement.
    """
    heap = []
    serial = count()
    for j in range(len(system.observations)):
        e = experiment(system, j)
        heapq.heappush(heap, (e.cost, next(serial), e))
    basis = []
    reduced, operations, pivots = (), (), ()
    while heap:
        _, _, e = heapq.heappop(heap)
        if _coordinates(e.row, reduced, operations, pivots, len(basis)) is not None:
            continue
        basis.append(e)
        reduced, operations, pivots = _echelon(tuple(b.row for b in basis), system.dimension)
        for i, operator in enumerate(system.operators):
            child = Experiment(e.observation, (i,)+e.word,
                               row_times_matrix(e.row, operator, system.dimension),
                               e.cost+system.attachment_costs[i])
            heapq.heappush(heap, (child.cost, next(serial), child))
    rank = len(basis)
    def coords(row):
        value = _coordinates(row, reduced, operations, pivots, rank)
        if value is None:
            raise ArithmeticError("observation closure failed")
        return value
    return ClosureCertificate(tuple(basis), tuple(coords(row) for row in system.observations),
        tuple(tuple(coords(row_times_matrix(e.row, op, system.dimension)) for e in basis)
              for op in system.operators), _kernel(reduced, pivots, system.dimension), pivots)


def verify_certificate(system: OperatorSystem, certificate: ClosureCertificate) -> bool:
    """Replay realizability, invariance, nullspace and cost-filtration claims.

    Checks, all exactly: every basis row is the actual experiment its word
    names, with its exact cost; costs are nondecreasing; the rows are
    independent with the stated RREF pivots and kernel N; L = A B and
    B M_i = T_i B; every M_i maps N into N; nonzero entries of A and T_i
    respect the cost filtration.
    """
    try:
        if not _well_typed(system, certificate):
            return False
        n, r = system.dimension, certificate.rank
        for e in certificate.basis:
            actual = experiment(system, e.observation, e.word)
            if actual.row != e.row or actual.cost != e.cost:
                return False
        if any(certificate.basis[i].cost > certificate.basis[i+1].cost for i in range(r-1)):
            return False
        rows = _matrix(certificate.rows, r, n)
        reduced, operations, pivots = _echelon(rows, n)
        if len(pivots) != r or certificate.pivots != pivots:
            return False
        if certificate.nullspace != _kernel(reduced, pivots, n):
            return False
        observation_coordinates = _matrix(certificate.observation_coordinates, len(system.observations), r)
        transitions = tuple(_matrix(t, r, r) for t in certificate.transition_coordinates)
        if len(transitions) != len(system.operators):
            return False
        for j, coordinates in enumerate(observation_coordinates):
            if row_times_matrix(coordinates, rows, n) != system.observations[j]:
                return False
            if any(c and certificate.basis[b].cost > system.observation_costs[j]
                   for b, c in enumerate(coordinates)):
                return False
        for i, transition in enumerate(transitions):
            for a, coordinates in enumerate(transition):
                if row_times_matrix(coordinates, rows, n) != row_times_matrix(rows[a], system.operators[i], n):
                    return False
                if any(c and certificate.basis[b].cost > certificate.basis[a].cost+system.attachment_costs[i]
                       for b, c in enumerate(coordinates)):
                    return False
        for operator in system.operators:
            for kernel_row in certificate.nullspace:
                image = matrix_times_vector(operator, kernel_row)
                if any(matrix_times_vector(rows, image)):
                    return False
        return True
    except (ValueError, TypeError, AttributeError, IndexError, ZeroDivisionError):
        return False


def quotient_state(system: OperatorSystem, certificate: ClosureCertificate, state) -> Row:
    if not verify_certificate(system, certificate):
        raise ValueError("invalid closure certificate")
    return matrix_times_vector(certificate.rows, _row(state, system.dimension))


def quotient_update(certificate: ClosureCertificate, operator: int, quotient) -> Row:
    """y -> T_i y, the descended action of generator ``operator`` on y = B v."""
    t = certificate.transition_coordinates
    operator = _index(operator, len(t))
    return matrix_times_vector(t[operator], _row(quotient, certificate.rank))


def quotient_output(certificate: ClosureCertificate, quotient) -> Row:
    """The direct observations L v = A y, read from the quotient state y = B v."""
    return matrix_times_vector(certificate.observation_coordinates, _row(quotient, certificate.rank))


def future_equivalent(system: OperatorSystem, first, second, certificate=None) -> bool:
    cert = observable_closure(system) if certificate is None else certificate
    return quotient_state(system, cert, first) == quotient_state(system, cert, second)


def minimum_distinguishing_experiment(system: OperatorSystem, difference, certificate=None):
    difference = _row(difference, system.dimension)
    cert = observable_closure(system) if certificate is None else certificate
    if not verify_certificate(system, cert):
        raise ValueError("invalid closure certificate")
    return next((e for e in cert.basis if _dot(e.row, difference)), None)


def _encode_q(value):
    return [value.numerator, value.denominator]


def _encode_row(row):
    return [_encode_q(q) for q in row]


def _encode_matrix(matrix):
    return [_encode_row(row) for row in matrix]


def certificate_bundle(system: OperatorSystem, certificate=None):
    cert = observable_closure(system) if certificate is None else certificate
    if not verify_certificate(system, cert):
        raise ValueError("invalid closure certificate")
    return {"schema": _SCHEMA, "system": {
        "dimension": system.dimension,
        "operators": [_encode_matrix(m) for m in system.operators],
        "observations": _encode_matrix(system.observations),
        "attachment_costs": _encode_row(system.attachment_costs),
        "observation_costs": _encode_row(system.observation_costs)},
        "certificate": {
            "basis": [{"observation": e.observation, "word": list(e.word),
                       "row": _encode_row(e.row), "cost": _encode_q(e.cost)} for e in cert.basis],
            "observation_coordinates": _encode_matrix(cert.observation_coordinates),
            "transition_coordinates": [_encode_matrix(m) for m in cert.transition_coordinates],
            "nullspace": _encode_matrix(cert.nullspace), "pivots": list(cert.pivots)}}


def _keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError("unexpected or missing certificate fields")


def _integer(value):
    if isinstance(value, bool) or not isinstance(value, int) or value.bit_length() > 4096:
        raise ValueError("invalid or oversized integer")
    return value


def _decode_q(value):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("rational must be [numerator, denominator]")
    a, b = map(_integer, value)
    if b <= 0:
        raise ValueError("rational denominator must be positive")
    q = Fraction(a, b)
    if q.numerator != a or q.denominator != b:
        raise ValueError("rational must be in reduced canonical form")
    return q


def _decode_row(values, size):
    if not isinstance(values, list) or len(values) != size:
        raise ValueError("row dimension mismatch")
    return tuple(_decode_q(v) for v in values)


def _decode_matrix(values, rows, columns):
    if not isinstance(values, list) or len(values) != rows:
        raise ValueError("matrix dimension mismatch")
    return tuple(_decode_row(row, columns) for row in values)


def replay_bundle(bundle):
    """Strict, resource-bounded portable replay; returns (system, certificate)."""
    _keys(bundle, ("schema", "system", "certificate"))
    if bundle["schema"] != _SCHEMA:
        raise ValueError("unsupported operator certificate schema")
    s = bundle["system"]
    _keys(s, ("dimension", "operators", "observations", "attachment_costs", "observation_costs"))
    n = _integer(s["dimension"])
    if not 0 <= n <= 128 or not isinstance(s["operators"], list) or len(s["operators"]) > 16:
        raise ValueError("portable system exceeds dimension/operator limit")
    if not isinstance(s["observations"], list) or len(s["observations"]) > 128:
        raise ValueError("portable observation limit exceeded")
    g, o = len(s["operators"]), len(s["observations"])
    system = OperatorSystem(n, tuple(_decode_matrix(m, n, n) for m in s["operators"]),
                            _decode_matrix(s["observations"], o, n),
                            _decode_row(s["attachment_costs"], g), _decode_row(s["observation_costs"], o))
    c = bundle["certificate"]
    _keys(c, ("basis", "observation_coordinates", "transition_coordinates", "nullspace", "pivots"))
    if not isinstance(c["basis"], list) or len(c["basis"]) > n:
        raise ValueError("basis exceeds ambient dimension")
    basis = []
    for e in c["basis"]:
        _keys(e, ("observation", "word", "row", "cost"))
        if not isinstance(e["word"], list) or len(e["word"]) > 256:
            raise ValueError("portable witness length exceeded")
        basis.append(Experiment(_index(e["observation"], o),
            tuple(_index(i, g) for i in e["word"]), _decode_row(e["row"], n), _decode_q(e["cost"])))
    r = len(basis)
    if not isinstance(c["transition_coordinates"], list) or len(c["transition_coordinates"]) != g:
        raise ValueError("transition count mismatch")
    if not isinstance(c["pivots"], list) or len(c["pivots"]) != r:
        raise ValueError("pivot count mismatch")
    cert = ClosureCertificate(tuple(basis), _decode_matrix(c["observation_coordinates"], o, r),
        tuple(_decode_matrix(m, r, r) for m in c["transition_coordinates"]),
        _decode_matrix(c["nullspace"], n-r, n), tuple(_integer(i) for i in c["pivots"]))
    if not verify_certificate(system, cert):
        raise ValueError("operator closure certificate failed replay")
    return system, cert


LinearExperimentSystem = OperatorSystem
