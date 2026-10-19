"""Typed exact observation closure: finite type graphs with rectangular maps (NX13).

The single-space engine in ``observability`` has one ambient column space.
Here a finite set of state types ``b`` carries spaces ``V_b = Q^{d_b}``; an
action ``a : s(a) -> t(a)`` has an exact ``d_t x d_s`` matrix ``M_a``; an
observation at type ``b`` is a row of length ``d_b``.  Zero-dimensional
types are legal: their dimension is declared by the type, never inferred
from an empty tuple.

Words are chronological.  A word ``(a1, ..., am)`` is legal exactly when
``t(a_i) = s(a_{i+1})``; it starts at ``s(a1)`` and its final observation
must live at ``t(am)``.  It sends a state ``v`` to ``M_am ... M_a1 v`` and
its reading is ``L M_am ... M_a1``: the latest matrix acts on the left.
Backward row exploration therefore PREPENDS an action whose target is the
current start type.

``typed_closure`` returns retained, actually realizable witness rows
``B_b`` at each type and coordinates with

    L_b = A_b B_b,        B_{t(a)} M_a = T_a B_{s(a)},

``T_a`` of shape ``r_t x r_s``.  Proofs of closure, quotient invariance,
per-type minimality and the cheapest-witness property are in
docs/research/TYPED_OBSERVABILITY.md.  ``verify_typed_certificate`` and
``replay_typed_bundle`` recheck every identity and never call the closure.

Numbers are exact: int or Fraction.  bool, float and str raise TypeError;
bad values or shapes raise ValueError.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import heapq
from itertools import count
import json
from typing import Sequence

from .observability import _coordinates, _echelon, _kernel

Row = tuple[Fraction, ...]
Matrix = tuple[Row, ...]
SCHEMA = "singularity.typed-operator-closure/1"

_LIMITS = {"types": 64, "dimension": 256, "total_dimension": 1024, "actions": 512,
           "observations": 2048, "word": 256, "bits": 4096}


# ---------------------------------------------------------------------------
# exact scalar and shape validation


def _q(value) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(f"exact rational values must be int or Fraction, not {type(value).__name__}")
    return Fraction(value)


def _identifier(value, name="identifier") -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a str")
    if not value:
        raise ValueError(f"{name} must be nonempty")
    return value


def _dimension(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("dimension must be an int")
    if value < 0:
        raise ValueError("dimension must be nonnegative")
    return value


def _sequence(value, name):
    if isinstance(value, (str, bytes)) or isinstance(value, bool) or not hasattr(value, "__iter__"):
        raise TypeError(f"{name} must be a sequence")
    return tuple(value)


def _row(values, dimension: int) -> Row:
    result = tuple(_q(x) for x in _sequence(values, "row"))
    if len(result) != dimension:
        raise ValueError("row dimension mismatch")
    return result


def _matrix(values, rows: int, columns: int) -> Matrix:
    result = tuple(_row(r, columns) for r in _sequence(values, "matrix"))
    if len(result) != rows:
        raise ValueError("matrix dimension mismatch")
    return result


def _row_times(row: Row, matrix: Matrix, columns: int) -> Row:
    """Row times matrix with an explicit column count (zero rows are legal)."""
    if len(row) != len(matrix) or any(len(r) != columns for r in matrix):
        raise ValueError("matrix dimension mismatch")
    out = [Fraction(0)] * columns
    for c, r in zip(row, matrix):
        if c:
            for j, m in enumerate(r):
                if m:
                    out[j] += c * m
    return tuple(out)


def _matrix_vector(matrix: Matrix, vector: Row) -> Row:
    if any(len(r) != len(vector) for r in matrix):
        raise ValueError("matrix dimension mismatch")
    return tuple(sum((a * b for a, b in zip(r, vector) if a), Fraction(0)) for r in matrix)


def _dot(a: Row, b: Row) -> Fraction:
    return sum((x * y for x, y in zip(a, b)), Fraction(0))


# ---------------------------------------------------------------------------
# declared objects


@dataclass(frozen=True)
class StateType:
    identifier: str
    dimension: int

    def __post_init__(self):
        _identifier(self.identifier, "type identifier")
        _dimension(self.dimension)


@dataclass(frozen=True)
class TypedAction:
    """An action ``source -> target``; ``matrix`` has d_target rows of length d_source."""

    identifier: str
    source: str
    target: str
    matrix: tuple
    cost: Fraction = Fraction(1)

    def __post_init__(self):
        _identifier(self.identifier, "action identifier")
        _identifier(self.source, "action source")
        _identifier(self.target, "action target")
        object.__setattr__(self, "matrix", tuple(tuple(_q(x) for x in _sequence(r, "matrix row"))
                                                 for r in _sequence(self.matrix, "matrix")))
        cost = _q(self.cost)
        if cost <= 0:
            raise ValueError("action costs must be positive")
        object.__setattr__(self, "cost", cost)


@dataclass(frozen=True)
class TypedObservation:
    identifier: str
    type_id: str
    row: tuple
    cost: Fraction = Fraction(0)

    def __post_init__(self):
        _identifier(self.identifier, "observation identifier")
        _identifier(self.type_id, "observation type")
        object.__setattr__(self, "row", tuple(_q(x) for x in _sequence(self.row, "observation row")))
        cost = _q(self.cost)
        if cost < 0:
            raise ValueError("observation costs must be nonnegative")
        object.__setattr__(self, "cost", cost)


class TypedOperatorSystem:
    """A finite typed action graph with exact matrices; immutable after checks."""

    def __init__(self, types: Sequence[StateType], actions: Sequence[TypedAction],
                 observations: Sequence[TypedObservation]):
        types = _sequence(types, "types")
        actions = _sequence(actions, "actions")
        observations = _sequence(observations, "observations")
        for kind, items, cls in (("type", types, StateType), ("action", actions, TypedAction),
                                 ("observation", observations, TypedObservation)):
            if any(not isinstance(x, cls) for x in items):
                raise TypeError(f"every {kind} must be a {cls.__name__}")
            ids = [x.identifier for x in items]
            if len(set(ids)) != len(ids):
                raise ValueError(f"duplicate {kind} identifier")
        self.types = types
        self.actions = actions
        self.observations = observations
        self.dimension = {t.identifier: t.dimension for t in types}
        self.type_index = {t.identifier: i for i, t in enumerate(types)}
        self.action_index = {a.identifier: i for i, a in enumerate(actions)}
        self.observation_index = {o.identifier: i for i, o in enumerate(observations)}
        for a in actions:
            if a.source not in self.dimension or a.target not in self.dimension:
                raise ValueError(f"action {a.identifier} uses an undeclared type")
            _matrix(a.matrix, self.dimension[a.target], self.dimension[a.source])
        for o in observations:
            if o.type_id not in self.dimension:
                raise ValueError(f"observation {o.identifier} uses an undeclared type")
            _row(o.row, self.dimension[o.type_id])
        self.observations_at = {t.identifier: tuple(o for o in observations if o.type_id == t.identifier)
                                for t in types}
        self.actions_into = {t.identifier: tuple(a for a in actions if a.target == t.identifier)
                             for t in types}

    def action(self, identifier) -> TypedAction:
        identifier = _identifier(identifier, "action identifier")
        if identifier not in self.action_index:
            raise ValueError(f"undeclared action {identifier!r}")
        return self.actions[self.action_index[identifier]]

    def observation(self, identifier) -> TypedObservation:
        identifier = _identifier(identifier, "observation identifier")
        if identifier not in self.observation_index:
            raise ValueError(f"undeclared observation {identifier!r}")
        return self.observations[self.observation_index[identifier]]

    def check_type(self, identifier) -> str:
        identifier = _identifier(identifier, "type identifier")
        if identifier not in self.dimension:
            raise ValueError(f"undeclared type {identifier!r}")
        return identifier

    def path(self, word, start_type=None) -> tuple[str, str]:
        """Check a chronological word; return (start type, end type)."""
        word = tuple(_identifier(a, "action identifier") for a in _sequence(word, "word"))
        acts = [self.action(a) for a in word]
        if start_type is not None:
            start_type = self.check_type(start_type)
        if not acts:
            if start_type is None:
                raise ValueError("an empty word needs a start type")
            return start_type, start_type
        if start_type is not None and acts[0].source != start_type:
            raise ValueError(f"illegal path: {acts[0].identifier} does not start at {start_type}")
        for first, second in zip(acts, acts[1:]):
            if first.target != second.source:
                raise ValueError(f"illegal path: {first.identifier} ends at {first.target}, "
                                 f"{second.identifier} starts at {second.source}")
        return acts[0].source, acts[-1].target


@dataclass(frozen=True)
class TypedExperiment:
    observation: str
    start_type: str
    word: tuple[str, ...]
    row: Row
    cost: Fraction


@dataclass(frozen=True)
class TypeBlock:
    type_id: str
    basis: tuple[TypedExperiment, ...]
    observation_coordinates: Matrix
    nullspace: Matrix
    pivots: tuple[int, ...]

    @property
    def rank(self):
        return len(self.basis)

    @property
    def rows(self) -> Matrix:
        return tuple(e.row for e in self.basis)


@dataclass(frozen=True)
class TypedClosureCertificate:
    blocks: tuple[TypeBlock, ...]          # one per declared type, system order
    transition_coordinates: tuple[Matrix, ...]  # T_a, one per action, r_t x r_s

    def block(self, type_id) -> TypeBlock:
        for b in self.blocks:
            if b.type_id == type_id:
                return b
        raise ValueError(f"no block for type {type_id!r}")

    @property
    def ranks(self):
        return {b.type_id: b.rank for b in self.blocks}


# ---------------------------------------------------------------------------
# experiments and words


def typed_experiment(system: TypedOperatorSystem, observation, word=(), start_type=None) -> TypedExperiment:
    """The actual experiment: run the chronological word, then read ``observation``."""
    obs = system.observation(observation)
    word = tuple(_identifier(a, "action identifier") for a in _sequence(word, "word"))
    if not word and start_type is None:
        start_type = obs.type_id
    start, end = system.path(word, start_type)
    if end != obs.type_id:
        raise ValueError(f"illegal experiment: observation {obs.identifier} is read at "
                         f"{obs.type_id}, the word ends at {end}")
    row = obs.row
    cost = obs.cost
    for a in reversed(word):
        act = system.action(a)
        row = _row_times(row, act.matrix, system.dimension[act.source])
        cost += act.cost
    return TypedExperiment(obs.identifier, start, word, row, cost)


def typed_apply_word(system: TypedOperatorSystem, start_type, state, word=()) -> tuple[str, Row]:
    """Chronological action on a column state; returns (end type, state)."""
    start, end = system.path(word, start_type)
    state = _row(state, system.dimension[start])
    for a in word:
        state = _matrix_vector(system.action(a).matrix, state)
    return end, state


# ---------------------------------------------------------------------------
# closure


def typed_closure(system: TypedOperatorSystem) -> TypedClosureCertificate:
    """Least family of invariant observation spaces, in increasing cost.

    Retained rows are actual experiments; only retained rows are extended,
    each by every action entering its start type.  Pops are nondecreasing
    in cost because every child costs strictly more than its parent.
    """
    if not isinstance(system, TypedOperatorSystem):
        raise TypeError("system must be a TypedOperatorSystem")
    heap = []
    serial = count()
    for o in system.observations:
        e = typed_experiment(system, o.identifier)
        heapq.heappush(heap, (e.cost, next(serial), e))
    basis = {t.identifier: [] for t in system.types}
    echelon = {t.identifier: ((), (), ()) for t in system.types}
    while heap:
        _, _, e = heapq.heappop(heap)
        b = e.start_type
        reduced, operations, pivots = echelon[b]
        if _coordinates(e.row, reduced, operations, pivots, len(basis[b])) is not None:
            continue
        basis[b].append(e)
        echelon[b] = _echelon(tuple(x.row for x in basis[b]), system.dimension[b])
        for act in system.actions_into[b]:
            child = TypedExperiment(e.observation, act.source, (act.identifier,) + e.word,
                                    _row_times(e.row, act.matrix, system.dimension[act.source]),
                                    e.cost + act.cost)
            heapq.heappush(heap, (child.cost, next(serial), child))

    def coords(type_id, row):
        reduced, operations, pivots = echelon[type_id]
        value = _coordinates(row, reduced, operations, pivots, len(basis[type_id]))
        if value is None:
            raise ArithmeticError("typed observation closure failed")
        return value

    blocks = []
    for t in system.types:
        b = t.identifier
        reduced, _, pivots = echelon[b]
        blocks.append(TypeBlock(b, tuple(basis[b]),
                                tuple(coords(b, o.row) for o in system.observations_at[b]),
                                _kernel(reduced, pivots, system.dimension[b]), tuple(pivots)))
    transitions = tuple(
        tuple(coords(a.source, _row_times(e.row, a.matrix, system.dimension[a.source]))
              for e in basis[a.target])
        for a in system.actions)
    return TypedClosureCertificate(tuple(blocks), transitions)


# ---------------------------------------------------------------------------
# verification (never calls the closure)


def _exact_row(value, size) -> bool:
    return type(value) is tuple and len(value) == size and all(type(x) is Fraction for x in value)


def _exact_matrix(value, rows, columns) -> bool:
    return type(value) is tuple and len(value) == rows and all(_exact_row(r, columns) for r in value)


def _well_typed(system, certificate) -> bool:
    if not isinstance(system, TypedOperatorSystem) or type(certificate) is not TypedClosureCertificate:
        return False
    blocks = certificate.blocks
    if type(blocks) is not tuple or len(blocks) != len(system.types):
        return False
    ranks = {}
    for t, block in zip(system.types, blocks):
        if type(block) is not TypeBlock or block.type_id != t.identifier:
            return False
        d = t.dimension
        if type(block.basis) is not tuple or len(block.basis) > d:
            return False
        r = len(block.basis)
        for e in block.basis:
            if type(e) is not TypedExperiment or type(e.cost) is not Fraction:
                return False
            if type(e.observation) is not str or type(e.start_type) is not str:
                return False
            if type(e.word) is not tuple or not all(type(a) is str for a in e.word):
                return False
            if not _exact_row(e.row, d):
                return False
        if not _exact_matrix(block.observation_coordinates, len(system.observations_at[t.identifier]), r):
            return False
        if not _exact_matrix(block.nullspace, d - r, d):
            return False
        p = block.pivots
        if type(p) is not tuple or len(p) != r or not all(type(i) is int and 0 <= i < d for i in p):
            return False
        ranks[t.identifier] = r
    trans = certificate.transition_coordinates
    if type(trans) is not tuple or len(trans) != len(system.actions):
        return False
    return all(_exact_matrix(m, ranks[a.target], ranks[a.source]) for a, m in zip(system.actions, trans))


def verify_typed_certificate(system: TypedOperatorSystem, certificate: TypedClosureCertificate) -> bool:
    """Replay every claim exactly; return False on any defect.

    Checks: each witness is the legal experiment its word names, with its
    start type and exact cost; costs nondecrease within each type; rows are
    independent with the stated RREF pivots and kernel N_b; L_b = A_b B_b;
    B_t M_a = T_a B_s; M_a N_s lies in N_t; nonzero coordinates respect the
    cost filtration (this is what makes the first witness cheapest).
    """
    try:
        if not _well_typed(system, certificate):
            return False
        rows = {}
        costs = {}
        for t, block in zip(system.types, certificate.blocks):
            d = t.dimension
            for e in block.basis:
                if e.start_type != t.identifier:
                    return False
                actual = typed_experiment(system, e.observation, e.word, e.start_type)
                if actual != e:
                    return False
            c = [e.cost for e in block.basis]
            if any(c[i] > c[i + 1] for i in range(len(c) - 1)):
                return False
            reduced, _, pivots = _echelon(block.rows, d)
            if len(pivots) != block.rank or pivots != block.pivots:
                return False
            if block.nullspace != _kernel(reduced, pivots, d):
                return False
            for o, coordinates in zip(system.observations_at[t.identifier], block.observation_coordinates):
                if _row_times(coordinates, block.rows, d) != o.row:
                    return False
                if any(x and c[k] > o.cost for k, x in enumerate(coordinates)):
                    return False
            rows[t.identifier] = block.rows
            costs[t.identifier] = c
        for a, transition in zip(system.actions, certificate.transition_coordinates):
            ds = system.dimension[a.source]
            for k, coordinates in enumerate(transition):
                lhs = _row_times(rows[a.target][k], a.matrix, ds)
                if _row_times(coordinates, rows[a.source], ds) != lhs:
                    return False
                if any(x and costs[a.source][m] > costs[a.target][k] + a.cost
                       for m, x in enumerate(coordinates)):
                    return False
            for n in certificate.block(a.source).nullspace:
                if any(_matrix_vector(rows[a.target], _matrix_vector(a.matrix, n))):
                    return False
        return True
    except (ValueError, TypeError, AttributeError, IndexError, ZeroDivisionError, KeyError):
        return False


def _checked(system, certificate):
    if not verify_typed_certificate(system, certificate):
        raise ValueError("invalid typed closure certificate")
    return certificate


def typed_quotient_state(system, certificate, type_id, state) -> Row:
    """z_b = B_b x, the complete future-observable content of x at type b."""
    _checked(system, certificate)
    type_id = system.check_type(type_id)
    return _matrix_vector(certificate.block(type_id).rows, _row(state, system.dimension[type_id]))


def typed_quotient_update(certificate, system, action, quotient) -> Row:
    """z_t = T_a z_s."""
    act = system.action(action)
    t = certificate.transition_coordinates[system.action_index[act.identifier]]
    return _matrix_vector(t, _row(quotient, certificate.block(act.source).rank))


def typed_future_equivalent(system, type_id, first, second, certificate=None) -> bool:
    cert = typed_closure(system) if certificate is None else certificate
    return typed_quotient_state(system, cert, type_id, first) == typed_quotient_state(system, cert, type_id, second)


def minimum_typed_distinction(system, type_id, difference, certificate=None):
    """A cheapest legal experiment separating states whose difference is given, or None."""
    cert = typed_closure(system) if certificate is None else certificate
    _checked(system, cert)
    type_id = system.check_type(type_id)
    difference = _row(difference, system.dimension[type_id])
    return next((e for e in cert.block(type_id).basis if _dot(e.row, difference)), None)


# ---------------------------------------------------------------------------
# portable bundle


def _enc_q(x: Fraction):
    return [x.numerator, x.denominator]


def _enc_matrix(m: Matrix, rows: int, columns: int):
    return {"rows": rows, "columns": columns, "entries": [[_enc_q(x) for x in r] for r in m]}


def typed_certificate_bundle(system: TypedOperatorSystem, certificate=None, provenance=None) -> dict:
    cert = typed_closure(system) if certificate is None else certificate
    _checked(system, cert)
    d = system.dimension
    out = {"schema": SCHEMA, "system": {
        "types": [{"id": t.identifier, "dimension": t.dimension} for t in system.types],
        "actions": [{"id": a.identifier, "source": a.source, "target": a.target,
                     "matrix": _enc_matrix(a.matrix, d[a.target], d[a.source]), "cost": _enc_q(a.cost)}
                    for a in system.actions],
        "observations": [{"id": o.identifier, "type": o.type_id, "row": [_enc_q(x) for x in o.row],
                          "cost": _enc_q(o.cost)} for o in system.observations]},
        "certificate": {
            "types": [{"id": b.type_id, "rank": b.rank,
                       "basis": [{"observation": e.observation, "start_type": e.start_type,
                                  "word": list(e.word), "row": [_enc_q(x) for x in e.row],
                                  "cost": _enc_q(e.cost)} for e in b.basis],
                       "observation_coordinates": _enc_matrix(b.observation_coordinates,
                                                              len(system.observations_at[b.type_id]), b.rank),
                       "nullspace": _enc_matrix(b.nullspace, d[b.type_id] - b.rank, d[b.type_id]),
                       "pivots": list(b.pivots)} for b in cert.blocks],
            "actions": [{"id": a.identifier,
                         "coordinates": _enc_matrix(m, cert.block(a.target).rank, cert.block(a.source).rank)}
                        for a, m in zip(system.actions, cert.transition_coordinates)]}}
    if provenance is not None:
        out["provenance"] = provenance
    return out


def _keys(value, expected, optional=()):
    if not isinstance(value, dict) or not set(expected) <= set(value) <= set(expected) | set(optional):
        raise ValueError("unexpected or missing bundle fields")


def _int(value, lo=0, hi=None):
    if isinstance(value, bool) or not isinstance(value, int) or value.bit_length() > _LIMITS["bits"]:
        raise ValueError("invalid or oversized integer")
    if value < lo or (hi is not None and value > hi):
        raise ValueError("integer out of range")
    return value


def _str(value):
    if not isinstance(value, str) or not value:
        raise ValueError("identifiers must be nonempty strings")
    return value


def _dec_q(value) -> Fraction:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("rational must be [numerator, denominator]")
    a, b = value
    if isinstance(a, bool) or not isinstance(a, int) or a.bit_length() > _LIMITS["bits"]:
        raise ValueError("invalid numerator")
    b = _int(b, 1)
    q = Fraction(a, b)
    if q.numerator != a or q.denominator != b:
        raise ValueError("rational must be canonical")
    return q


def _dec_row(values, size) -> Row:
    if not isinstance(values, list) or len(values) != size:
        raise ValueError("row dimension mismatch")
    return tuple(_dec_q(v) for v in values)


def _dec_matrix(value, rows, columns) -> Matrix:
    _keys(value, ("rows", "columns", "entries"))
    if _int(value["rows"]) != rows or _int(value["columns"]) != columns:
        raise ValueError("declared matrix shape disagrees with the types")
    entries = value["entries"]
    if not isinstance(entries, list) or len(entries) != rows:
        raise ValueError("matrix dimension mismatch")
    return tuple(_dec_row(r, columns) for r in entries)


def replay_typed_bundle(bundle):
    """Strict portable replay; returns (system, certificate) or raises ValueError.

    Decodes and verifies only.  It never calls ``typed_closure``.
    """
    try:
        return _replay(bundle)
    except (TypeError, KeyError, AttributeError) as error:
        raise ValueError(f"malformed typed certificate: {error}") from None


def _replay(bundle):
    _keys(bundle, ("schema", "system", "certificate"), ("provenance",))
    if bundle["schema"] != SCHEMA:
        raise ValueError("unsupported typed certificate schema")
    s = bundle["system"]
    _keys(s, ("types", "actions", "observations"))
    if not isinstance(s["types"], list) or len(s["types"]) > _LIMITS["types"]:
        raise ValueError("type limit exceeded")
    types = []
    for t in s["types"]:
        _keys(t, ("id", "dimension"))
        types.append(StateType(_str(t["id"]), _int(t["dimension"], 0, _LIMITS["dimension"])))
    if sum(t.dimension for t in types) > _LIMITS["total_dimension"]:
        raise ValueError("total dimension limit exceeded")
    dims = {t.identifier: t.dimension for t in types}
    if len(dims) != len(types):
        raise ValueError("duplicate type identifier")
    if not isinstance(s["actions"], list) or len(s["actions"]) > _LIMITS["actions"]:
        raise ValueError("action limit exceeded")
    actions = []
    for a in s["actions"]:
        _keys(a, ("id", "source", "target", "matrix", "cost"))
        src, tgt = _str(a["source"]), _str(a["target"])
        if src not in dims or tgt not in dims:
            raise ValueError("action uses an undeclared type")
        actions.append(TypedAction(_str(a["id"]), src, tgt, _dec_matrix(a["matrix"], dims[tgt], dims[src]),
                                   _dec_q(a["cost"])))
    if not isinstance(s["observations"], list) or len(s["observations"]) > _LIMITS["observations"]:
        raise ValueError("observation limit exceeded")
    observations = []
    for o in s["observations"]:
        _keys(o, ("id", "type", "row", "cost"))
        ty = _str(o["type"])
        if ty not in dims:
            raise ValueError("observation uses an undeclared type")
        observations.append(TypedObservation(_str(o["id"]), ty, _dec_row(o["row"], dims[ty]), _dec_q(o["cost"])))
    system = TypedOperatorSystem(types, actions, observations)
    c = bundle["certificate"]
    _keys(c, ("types", "actions"))
    if not isinstance(c["types"], list) or len(c["types"]) != len(types):
        raise ValueError("certificate type count mismatch")
    blocks = []
    ranks = {}
    for t, b in zip(types, c["types"]):
        _keys(b, ("id", "rank", "basis", "observation_coordinates", "nullspace", "pivots"))
        if b["id"] != t.identifier:
            raise ValueError("certificate type order mismatch")
        r = _int(b["rank"], 0, t.dimension)
        if not isinstance(b["basis"], list) or len(b["basis"]) != r:
            raise ValueError("basis size disagrees with rank")
        basis = []
        for e in b["basis"]:
            _keys(e, ("observation", "start_type", "word", "row", "cost"))
            if not isinstance(e["word"], list) or len(e["word"]) > _LIMITS["word"]:
                raise ValueError("witness word limit exceeded")
            basis.append(TypedExperiment(_str(e["observation"]), _str(e["start_type"]),
                                         tuple(_str(a) for a in e["word"]),
                                         _dec_row(e["row"], t.dimension), _dec_q(e["cost"])))
        if not isinstance(b["pivots"], list) or len(b["pivots"]) != r:
            raise ValueError("pivot count mismatch")
        blocks.append(TypeBlock(t.identifier, tuple(basis),
                                _dec_matrix(b["observation_coordinates"],
                                            len(system.observations_at[t.identifier]), r),
                                _dec_matrix(b["nullspace"], t.dimension - r, t.dimension),
                                tuple(_int(p, 0, max(t.dimension - 1, 0)) for p in b["pivots"])))
        ranks[t.identifier] = r
    if not isinstance(c["actions"], list) or len(c["actions"]) != len(actions):
        raise ValueError("certificate action count mismatch")
    transitions = []
    for a, entry in zip(actions, c["actions"]):
        _keys(entry, ("id", "coordinates"))
        if entry["id"] != a.identifier:
            raise ValueError("certificate action order mismatch")
        transitions.append(_dec_matrix(entry["coordinates"], ranks[a.target], ranks[a.source]))
    cert = TypedClosureCertificate(tuple(blocks), tuple(transitions))
    if not verify_typed_certificate(system, cert):
        raise ValueError("typed closure certificate failed replay")
    return system, cert


def _no_duplicates(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate JSON key {k!r}")
        out[k] = v
    return out


def _no_constant(name):
    raise ValueError(f"nonfinite JSON constant {name}")


def load_typed_bundle(text: str):
    """Parse JSON text strictly (duplicate keys, NaN/Infinity rejected), then replay."""
    if not isinstance(text, str):
        raise TypeError("bundle text must be a str")
    try:
        data = json.loads(text, object_pairs_hook=_no_duplicates, parse_constant=_no_constant)
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON: {error}") from None
    return replay_typed_bundle(data)
