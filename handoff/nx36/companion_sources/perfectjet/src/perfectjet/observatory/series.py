"""Exact future observations and rational counting series of finite systems.

A state is a column of observable values.  For an action ``a``, ``T_a f``
is the function ``s -> f(transition(s, a))``, with value zero at an undefined
transition.  Thus every distinct action contributes one history, even when
two actions have the same target.  With ``A = sum_a T_a`` and acceptance
indicator ``f``, ``(A**k f)[s]`` counts the accepted length-k action words.

The recurrence below comes from an identity between whole state vectors,
not from fitting a finite prefix of one sequence.  That identity proves the
recurrence at every length and every starting state.  All arithmetic is exact;
remote modular queries use polynomial binary powering, without iterating to
the requested length.
"""

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Iterable, Sequence


Number = int | Fraction


def _integer(value: Any, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _number(value: Number) -> Number:
    value = Fraction(value)
    return value.numerator if value.denominator == 1 else value


def _json_number(value: Number) -> int | str:
    value = _number(value)
    return value if isinstance(value, int) else str(value)


def _trim(poly: Sequence[Number]) -> tuple[Number, ...]:
    out = [_number(x) for x in poly]
    while len(out) > 1 and not out[-1]:
        out.pop()
    return tuple(out) if out else (0,)


def _system_data(system: Any, max_dimension: int) -> tuple:
    """Accept the Observatory FiniteSystem protocol without importing its core."""
    max_dimension = _integer(max_dimension, "max_dimension", 1)
    n = _integer(system.n, "number of states", 1)
    if n > max_dimension:
        raise ValueError(
            f"exact linear closure is limited to {max_dimension} states; "
            "compile the behavioral quotient first or explicitly raise max_dimension"
        )
    alphabet = system.alphabet
    m = alphabet if isinstance(alphabet, int) else len(alphabet)
    m = _integer(m, "alphabet size")
    transitions = tuple(tuple(row) for row in system.transitions)
    if len(transitions) != n or any(len(row) != m for row in transitions):
        raise ValueError("transition table must have one row per state and column per action")
    for row in transitions:
        for target in row:
            if target is not None:
                _integer(target, "transition target")
                if target >= n:
                    raise ValueError("transition target is outside the state space")
    accepting = tuple(system.accepting)
    if len(accepting) != n or any(x not in (False, True) for x in accepting):
        raise ValueError("accepting must contain one Boolean value per state")
    initial = _integer(system.initial, "initial state")
    if initial >= n:
        raise ValueError("initial state is outside the state space")
    return n, m, transitions, tuple(int(x) for x in accepting), initial


class _Echelon:
    """Incremental exact span with coordinates in the original input basis.

    Keeping each normalized echelon row's expression in the input vectors
    avoids rebuilding an augmented system for every closure or coordinate
    query.  The original basis stays integral when its inputs are integral.
    """

    def __init__(self, n: int):
        self.n = n
        self.originals: list[tuple[Number, ...]] = []
        self.rows: list[list[Fraction]] = []
        self.pivots: list[int] = []
        self.expressions: list[list[Fraction]] = []

    def reduce(self, vector: Sequence[Number]) -> tuple[list[Fraction], list[Fraction]]:
        if len(vector) != self.n:
            raise ValueError("observable has the wrong number of state values")
        work = [Fraction(x) for x in vector]
        coordinates = [Fraction(0)] * len(self.originals)
        for row, pivot, expression in zip(self.rows, self.pivots, self.expressions):
            factor = work[pivot]
            if factor:
                work = [x - factor * y for x, y in zip(work, row)]
                coordinates = [x + factor * y for x, y in zip(coordinates, expression)]
        return work, coordinates

    def add(self, vector: Sequence[Number]) -> tuple[bool, tuple[Number, ...]]:
        residual, coordinates = self.reduce(vector)
        pivot = next((i for i, x in enumerate(residual) if x), None)
        if pivot is None:
            return False, tuple(_number(x) for x in coordinates)
        divisor = residual[pivot]
        for expression in self.expressions:
            expression.append(Fraction(0))
        self.originals.append(tuple(_number(x) for x in vector))
        self.rows.append([x / divisor for x in residual])
        self.pivots.append(pivot)
        self.expressions.append([-x / divisor for x in coordinates] + [1 / divisor])
        return True, ()

    def coordinates(self, vector: Sequence[Number]) -> tuple[Number, ...]:
        residual, coordinates = self.reduce(vector)
        if any(residual):
            raise ValueError("observable is outside the compiled observable space")
        return tuple(_number(x) for x in coordinates)


def _image(vector: Sequence[Number], action: int, transitions: tuple) -> tuple[Number, ...]:
    return tuple(0 if row[action] is None else vector[row[action]] for row in transitions)


def _sum_image(vector: Sequence[Number], transitions: tuple) -> tuple[Number, ...]:
    return tuple(sum(vector[target] for target in row if target is not None) for row in transitions)


def _mod(value: Number, modulus: int) -> int:
    value = Fraction(value)
    if value.denominator == 1:
        return value.numerator % modulus
    try:
        return value.numerator * pow(value.denominator, -1, modulus) % modulus
    except ValueError as error:
        raise ValueError("a recurrence denominator is not invertible modulo the requested modulus") from error


def _multiply_mod_polynomial(
    left: Sequence[Number], right: Sequence[Number], dependency: Sequence[Number], modulus: int | None
) -> list[Number]:
    """Multiply modulo x^r - sum(dependency[j] x^j)."""
    r = len(dependency)
    product: list[Number] = [0] * (2 * r - 1)
    for i, x in enumerate(left):
        if x:
            for j, y in enumerate(right):
                if y:
                    product[i + j] += x * y
                    if modulus is not None:
                        product[i + j] %= modulus
    for k in range(len(product) - 1, r - 1, -1):
        factor = product[k]
        if factor:
            for j, c in enumerate(dependency):
                if c:
                    product[k - r + j] += factor * c
                    if modulus is not None:
                        product[k - r + j] %= modulus
    return product[:r]


@dataclass(frozen=True)
class RationalSeries:
    """An exact counting series with a globally checked recurrence.

    ``recurrence`` is in lag order: a[k] = recurrence[0]*a[k-1] + ...
    + recurrence[r-1]*a[k-r], for k >= r.  Polynomial coefficients in
    ``numerator`` and ``denominator`` are in ascending powers of z.  The
    closure dimension is for the whole vector sequence; a particular start
    may admit a shorter recurrence through additional cancellation.
    """

    start: int
    state_count: int
    action_count: int
    closure_dimension: int
    initial_values: tuple[Number, ...]
    recurrence: tuple[Number, ...]
    numerator: tuple[Number, ...]
    denominator: tuple[Number, ...]
    identity_residual: tuple[Number, ...]
    default_modulus: int | None = None
    _krylov_vectors: tuple[tuple[Number, ...], ...] = field(default=(), repr=False)

    @property
    def identity_verified(self) -> bool:
        return not any(self.identity_residual)

    @property
    def order(self) -> int:
        return self.closure_dimension

    @property
    def rational_gf(self) -> dict:
        return {
            "numerator": [_json_number(x) for x in self.numerator],
            "denominator": [_json_number(x) for x in self.denominator],
            "coefficient_order": "ascending powers of z",
        }

    def coefficient(self, index: int, modulus: int | None = None) -> Number:
        """Count accepted words at an arbitrary length in O(r^2 log index).

        Supplying a modulus keeps intermediate integers bounded.  Without
        one, the exact answer itself can require exponentially many bits.
        """
        index = _integer(index, "index")
        modulus = self.default_modulus if modulus is None else modulus
        if modulus is not None:
            modulus = _integer(modulus, "modulus", 2)
        r = self.order
        if not r:
            return 0
        if index < r:
            return self.initial_values[index] if modulus is None else _mod(self.initial_values[index], modulus)
        dependency = list(reversed(self.recurrence))
        initials = self.initial_values
        if modulus is not None:
            dependency = [_mod(x, modulus) for x in dependency]
            initials = tuple(_mod(x, modulus) for x in initials)
        result: list[Number] = [1] + [0] * (r - 1)
        power: list[Number] = ([0, 1] + [0] * (r - 2)) if r > 1 else [dependency[0]]
        exponent = index
        while exponent:
            if exponent & 1:
                result = _multiply_mod_polynomial(result, power, dependency, modulus)
            exponent >>= 1
            if exponent:
                power = _multiply_mod_polynomial(power, power, dependency, modulus)
        answer = sum(x * y for x, y in zip(result, initials))
        return _number(answer) if modulus is None else int(answer % modulus)

    def coefficients(self, length: int, modulus: int | None = None) -> tuple[Number, ...]:
        """Return a short prefix, using sequential recurrence evaluation."""
        length = _integer(length, "length")
        modulus = self.default_modulus if modulus is None else modulus
        if modulus is not None:
            modulus = _integer(modulus, "modulus", 2)
        if not self.order:
            return (0,) * length
        values = list(self.initial_values[:length])
        recurrence = self.recurrence
        if modulus is not None:
            values = [_mod(x, modulus) for x in values]
            recurrence = tuple(_mod(x, modulus) for x in recurrence)
        while len(values) < length:
            value = sum(c * values[-j - 1] for j, c in enumerate(recurrence))
            values.append(_number(value) if modulus is None else int(value % modulus))
        return tuple(values)

    def record(self) -> dict:
        return {
            "schema": "perfectjet-observatory-series/1",
            "start": self.start,
            "state_count": self.state_count,
            "action_count": self.action_count,
            "closure_dimension": self.closure_dimension,
            "global_krylov_dimension": self.closure_dimension,
            "recurrence_order": self.order,
            "recurrence_valid_from": self.order,
            "recurrence": [_json_number(x) for x in self.recurrence],
            "recurrence_convention": "a[k] = sum(recurrence[j-1] * a[k-j], j=1..r), k>=r",
            "initial_values": [_json_number(x) for x in self.initial_values],
            "rational_gf": self.rational_gf,
            "numerator": [_json_number(x) for x in self.numerator],
            "denominator": [_json_number(x) for x in self.denominator],
            "denominator_degree": len(self.denominator) - 1,
            "scalar_minimality_claimed": False,
            "dimension_scope": "whole-state vector sequence; the selected start can have a shorter scalar recurrence",
            "identity_verified": self.identity_verified,
            "identity_scope": "all states, all subsequent lengths",
            "identity_residual_nonzero_entries": sum(bool(x) for x in self.identity_residual),
            "identity_residual": [_json_number(x) for x in self.identity_residual],
            "default_modulus": self.default_modulus,
            "query_method": "binary polynomial powering modulo the exact recurrence",
        }


def compile_series(
    system: Any, start: int | None = None, modulus: int | None = None, *, max_dimension: int = 128
) -> RationalSeries:
    """Compile a rational accepted-history series by exact Krylov dependence."""
    n, m, transitions, accepting, initial = _system_data(system, max_dimension)
    start = initial if start is None else _integer(start, "start")
    if start >= n:
        raise ValueError("start is outside the state space")
    if modulus is not None:
        modulus = _integer(modulus, "modulus", 2)
    span = _Echelon(n)
    vector: tuple[Number, ...] = accepting
    while True:
        independent, dependency = span.add(vector)
        if not independent:
            break
        vector = _sum_image(vector, transitions)
    vectors = tuple(span.originals)
    r = len(vectors)
    residual = tuple(
        _number(vector[s] - sum(c * v[s] for c, v in zip(dependency, vectors))) for s in range(n)
    )
    if any(residual):  # A failed algebraic identity must never become a receipt.
        raise ArithmeticError("exact global Krylov identity did not replay")
    recurrence = tuple(reversed(dependency))
    # A rational monic divisor of an integer matrix's characteristic polynomial
    # has integer coefficients.  Keep Fraction support for explicit replay and
    # modular denominator diagnostics, but expose integers whenever possible.
    initials = tuple(v[start] for v in vectors)
    denominator = _trim((1,) + tuple(-x for x in recurrence))
    numerator = _trim(tuple(
        initials[k] - sum(recurrence[j - 1] * initials[k - j] for j in range(1, k + 1))
        for k in range(r)
    ))
    return RationalSeries(
        start=start, state_count=n, action_count=m, closure_dimension=r,
        initial_values=initials, recurrence=recurrence, numerator=numerator,
        denominator=denominator, identity_residual=residual, default_modulus=modulus,
        _krylov_vectors=vectors,
    )


@dataclass(frozen=True)
class ObservableClosure:
    """Smallest exact function space containing outputs and closed under actions.

    If C has ``basis`` as rows, ``operators[a]`` is B_a with
    C[:, transition(s,a)] = B_a C[:,s].  Undefined transitions use the zero
    vector.  This is a linear representation of all future acceptance
    observations, and can be smaller than the number of behavioral states.
    """

    state_count: int
    action_count: int
    basis: tuple[tuple[Number, ...], ...]
    operators: tuple[tuple[tuple[Number, ...], ...], ...]
    output_coordinates: tuple[Number, ...]
    observation_coordinates: tuple[tuple[Number, ...], ...]
    basis_sources: tuple[tuple[int, tuple[int, ...]], ...]
    identity_verified: bool
    _span: _Echelon = field(repr=False, compare=False)

    @property
    def dimension(self) -> int:
        return len(self.basis)

    @property
    def closure_dimension(self) -> int:
        return self.dimension

    def coordinates(self, observable: Sequence[Number]) -> tuple[Number, ...]:
        return self._span.coordinates(observable)

    def state_coordinates(self, state: int) -> tuple[Number, ...]:
        state = _integer(state, "state")
        if state >= self.state_count:
            raise ValueError("state is outside the state space")
        return tuple(row[state] for row in self.basis)

    def step(self, coordinates: Sequence[Number], action: int) -> tuple[Number, ...]:
        """Transport a state coordinate vector using one reduced action."""
        action = _integer(action, "action")
        if action >= self.action_count:
            raise ValueError("action is outside the alphabet")
        if len(coordinates) != self.dimension:
            raise ValueError("coordinate vector has the wrong dimension")
        return tuple(_number(sum(x * y for x, y in zip(row, coordinates))) for row in self.operators[action])

    def acceptance(self, coordinates: Sequence[Number]) -> Number:
        if len(coordinates) != self.dimension:
            raise ValueError("coordinate vector has the wrong dimension")
        return _number(sum(x * y for x, y in zip(self.output_coordinates, coordinates)))

    def record(self, *, include_basis: bool = True) -> dict:
        out = {
            "schema": "perfectjet-observatory-observable-closure/1",
            "state_count": self.state_count,
            "action_count": self.action_count,
            "dimension": self.dimension,
            "identity_verified": self.identity_verified,
            "identity_scope": "all states and every action; acceptance and every explicitly supplied observable",
            "identity_residual_nonzero_entries": 0 if self.identity_verified else None,
            "identity_convention": "C[:, next(s,a)] = operators[a] * C[:,s]; undefined next uses zero",
            "output_coordinates": [_json_number(x) for x in self.output_coordinates],
            "observation_coordinates": [[_json_number(x) for x in row] for row in self.observation_coordinates],
            "observation_convention": "observation 0 is acceptance; later observations follow the explicitly supplied order",
            "operators": [[[_json_number(x) for x in row] for row in operator] for operator in self.operators],
            "basis_sources": [{"observation": seed, "word": list(word)} for seed, word in self.basis_sources],
        }
        if include_basis:
            out["basis"] = [[_json_number(x) for x in row] for row in self.basis]
        return out


def compile_observable_closure(
    system: Any, observations: Iterable[Sequence[Number]] | None = None, *, max_dimension: int = 128
) -> ObservableClosure:
    """Close acceptance and any additional observable functions under each action.

    Basis-source words are replayable: a basis element marked observation i,
    word w is that original observation evaluated after w.  This closure
    preserves ordered words, rather than only their aggregated length counts.
    """
    n, m, transitions, accepting, _ = _system_data(system, max_dimension)
    span = _Echelon(n)
    seeds = [accepting]
    if observations is not None:
        seeds.extend(tuple(Fraction(x) for x in row) for row in observations)
    sources: list[tuple[int, tuple[int, ...]]] = []
    for i, seed in enumerate(seeds):
        independent, _ = span.add(seed)
        if independent:
            sources.append((i, ()))
    cursor = 0
    while cursor < len(span.originals):
        vector = span.originals[cursor]
        seed, word = sources[cursor]
        for action in range(m):
            independent, _ = span.add(_image(vector, action, transitions))
            if independent:
                sources.append((seed, (action,) + word))
        cursor += 1
    basis = tuple(span.originals)
    operators = tuple(tuple(span.coordinates(_image(row, action, transitions)) for row in basis) for action in range(m))
    verified = all(
        sum(operator[i][j] * basis[j][s] for j in range(len(basis)))
        == (0 if transitions[s][action] is None else basis[i][transitions[s][action]])
        for action, operator in enumerate(operators) for i in range(len(basis)) for s in range(n)
    )
    if not verified:
        raise ArithmeticError("exact action-closure identity did not replay")
    return ObservableClosure(
        state_count=n, action_count=m, basis=basis, operators=operators,
        output_coordinates=span.coordinates(accepting),
        observation_coordinates=tuple(span.coordinates(seed) for seed in seeds), basis_sources=tuple(sources),
        identity_verified=verified, _span=span,
    )


# A short discoverable synonym for callers presenting this as a math bridge.
observable_closure = compile_observable_closure
