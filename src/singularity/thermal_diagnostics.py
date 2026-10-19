"""Exact finite-candidate diagnostics for source-derived discrete thermal models.

The nominal stencil follows DynaComp's ``thermal.plate_model`` at the pinned
source revision recorded in ``applications/thermal_diagnostics/source_fixture.json``.
This adapter does not interpret a graph-height kernel as thermal physics.  Its
state is an excess-temperature vector in declared per-step model units.

Every panel member is a separate experiment reset to the declared initial box.
The exact optimizer is the existing :mod:`singularity.panels` backend.  Bounds
combine initial uncertainty, an optional bounded additive per-step disturbance,
optional certified reduction error, and sensor error.  Disturbance bounds are
assumptions, not measurements or physical calibration.  Full exact simulation
has zero reduction error.  Cost units are declared laboratory accounting units,
not measured money or energy.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .observability import OperatorSystem
from .panels import PanelPool, reading_pool

SENSOR_LABELS = ("corner_mean", "center_mean", "left_center_mean", "right_center_mean")
CANDIDATE_IDS = ("nominal", "conductance_half", "heater_half", "loss_double",
                 "blocked_left_center_bond", "blocked_right_center_bond")


def _q(value, name="value"):
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(f"{name} must be an int or Fraction")
    return Fraction(value)


def _index(value, size, name="index"):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int")
    if not 0 <= value < size:
        raise ValueError(f"{name} is out of range")
    return value


def _vector(values, size, name="vector"):
    result = tuple(_q(x, name) for x in values)
    if len(result) != size:
        raise ValueError(f"{name} has the wrong dimension")
    return result


@dataclass(frozen=True)
class AffineCandidate:
    """Sparse x' = A x + b u, y_j = C_j x; arbitrary exact rational data."""
    identifier: str
    dimension: int
    entries: tuple
    heater: tuple
    sensors: tuple

    def __post_init__(self):
        if not isinstance(self.identifier, str) or not self.identifier:
            raise ValueError("candidate identifier must be a nonempty string")
        if isinstance(self.dimension, bool) or not isinstance(self.dimension, int):
            raise TypeError("dimension must be an int")
        if self.dimension < 1:
            raise ValueError("dimension must be positive")
        combined = {}
        for item in self.entries:
            if len(item) != 3:
                raise ValueError("sparse entry must have row, column and value")
            i = _index(item[0], self.dimension, "row")
            j = _index(item[1], self.dimension, "column")
            combined[i, j] = combined.get((i, j), Fraction(0)) + _q(item[2])
        object.__setattr__(self, "entries", tuple((i, j, x) for (i, j), x in sorted(combined.items()) if x))
        object.__setattr__(self, "heater", _vector(self.heater, self.dimension, "heater"))
        sensors = tuple(_vector(s, self.dimension, "sensor") for s in self.sensors)
        if not sensors:
            raise ValueError("at least one sensor is required")
        object.__setattr__(self, "sensors", sensors)

    def step(self, state, amplitude):
        state = _vector(state, self.dimension, "state")
        amplitude = _q(amplitude, "amplitude")
        result = [b * amplitude for b in self.heater]
        for i, j, value in self.entries:
            result[i] += value * state[j]
        return tuple(result)

    def observe(self, state, sensor):
        state = _vector(state, self.dimension, "state")
        sensor = _index(sensor, len(self.sensors), "sensor")
        return sum((c * x for c, x in zip(self.sensors[sensor], state)), Fraction(0))


def _candidates(candidates):
    result = tuple(candidates)
    if len(result) < 2 or any(not isinstance(c, AffineCandidate) for c in result):
        raise ValueError("at least two AffineCandidate models are required")
    if len({c.identifier for c in result}) != len(result):
        raise ValueError("candidate identifiers must be distinct; candidates are never deduplicated")
    if len({len(c.sensors) for c in result}) != 1:
        raise ValueError("models must expose the same sensor channels")
    return result


def build_plate_candidates(grid=12):
    """Six finite single-fault hypotheses on the exact DynaComp plate stencil.

    At grid 12, blocked bonds are 64--65 and 66--67, reflected in the vertical
    center line.  Removing a bond moves its conductance onto the two diagonal
    entries, preserving the row sum 1-loss and nonnegative stability stencil.
    """
    if isinstance(grid, bool) or not isinstance(grid, int):
        raise TypeError("grid must be an int")
    if grid < 4 or grid % 2:
        raise ValueError("a positive even grid size at least four is required")
    n = grid * grid
    middle = (grid // 2 - 1, grid // 2)

    def mean(indices):
        indices = set(indices)
        return tuple(Fraction(int(i in indices), len(indices)) for i in range(n))

    sensors = (mean((0, grid - 1, n - grid, n - 1)),
               mean(r * grid + c for r in middle for c in middle),
               mean(r * grid + middle[0] for r in middle),
               mean(r * grid + middle[1] for r in middle))
    base_heater = mean(r * grid + c for r in middle for c in middle)
    result = []
    for identifier in CANDIDATE_IDS:
        k = Fraction(1, 16) if identifier == "conductance_half" else Fraction(1, 8)
        loss = Fraction(1, 50) if identifier == "loss_double" else Fraction(1, 100)
        gain = Fraction(1, 2) if identifier == "heater_half" else Fraction(1)
        entries = {}
        for r in range(grid):
            for c in range(grid):
                i = r * grid + c
                neighbors = tuple(rr * grid + cc for rr, cc in
                                  ((r-1, c), (r+1, c), (r, c-1), (r, c+1))
                                  if 0 <= rr < grid and 0 <= cc < grid)
                entries[i, i] = 1 - k * len(neighbors) - loss
                for j in neighbors:
                    entries[i, j] = k
        if identifier.startswith("blocked_"):
            r = middle[0]
            a, b = ((r * grid + middle[0] - 1, r * grid + middle[0])
                    if identifier == "blocked_left_center_bond" else
                    (r * grid + middle[1], r * grid + middle[1] + 1))
            del entries[a, b]
            del entries[b, a]
            entries[a, a] += k
            entries[b, b] += k
        result.append(AffineCandidate(identifier, n,
                      tuple((i, j, v) for (i, j), v in entries.items()),
                      tuple(gain * b for b in base_heater), sensors))
    return tuple(result)


def simulate_protocol(candidate, word, sensor, initial=None):
    """Full sparse exact simulation; words contain heater amplitudes, not indices."""
    if not isinstance(candidate, AffineCandidate):
        raise TypeError("candidate must be an AffineCandidate")
    state = ((Fraction(0),) * candidate.dimension if initial is None else
             _vector(initial, candidate.dimension, "initial state"))
    for amplitude in word:
        state = candidate.step(state, amplitude)
    return candidate.observe(state, sensor)


def default_protocols(horizons=(1, 2, 3, 4, 6, 8, 12, 20), sensors=4):
    """Declared finite pool: step, first pulse, last pulse and alternating heat."""
    if isinstance(sensors, bool) or not isinstance(sensors, int):
        raise TypeError("sensors must be an int")
    if sensors < 1:
        raise ValueError("sensors must be positive")
    words = set()
    for horizon in horizons:
        if isinstance(horizon, bool) or not isinstance(horizon, int):
            raise TypeError("horizons must be integers")
        if horizon < 1:
            raise ValueError("horizons must be positive")
        words.update(((2,) * horizon, (2,) + (0,) * (horizon - 1),
                      (0,) * (horizon - 1) + (2,),
                      tuple(2 if t % 2 == 0 else 0 for t in range(horizon))))
    return tuple((word, j) for word in sorted(words, key=lambda w: (len(w), w))
                 for j in range(sensors))


@dataclass(frozen=True)
class DiagnosticPool:
    pool: PanelPool
    epsilon: tuple
    error_bounds: tuple
    candidate_ids: tuple

    @property
    def panel_epsilon(self):
        """None denotes exact separation when every error bound is zero."""
        if not any(self.epsilon):
            return None
        if any(e <= 0 for e in self.epsilon):
            raise ValueError("the current panel backend requires strictly positive noisy bounds")
        return self.epsilon


def protocol_pool(candidates, protocols, *, initial_radius=0, sensor_noise=Fraction(1, 1000),
                  process_radius=0, reduction_error=0, reset_cost=2, elapsed_cost=1,
                  heating_cost=Fraction(1, 2), sensor_costs=(1, 1, 2, 2)):
    """Compile candidate readings and a conservative common box-noise envelope.

    b_0 = initial_radius*1, b' = |A|b + process_radius*1,
    rho_e,c = |C_j| b + sensor_noise + reduction_error,
    epsilon_e = max_c rho_e,c.  Existing panel optimization is exact for the
    common envelope; it need not be optimal for the sharper heterogeneous
    candidate boxes.  Each protocol independently resets to a zero-centered
    initial box.  ``reduction_error`` must be a caller-supplied certified bound.
    """
    candidates = _candidates(candidates)
    radii = tuple(_q(x, name) for x, name in
                  ((initial_radius, "initial_radius"), (sensor_noise, "sensor_noise"),
                   (process_radius, "process_radius"), (reduction_error, "reduction_error")))
    if any(x < 0 for x in radii):
        raise ValueError("error bounds must be nonnegative")
    initial_radius, sensor_noise, process_radius, reduction_error = radii
    reset_cost, elapsed_cost, heating_cost = (_q(reset_cost, "reset_cost"),
                                             _q(elapsed_cost, "elapsed_cost"),
                                             _q(heating_cost, "heating_cost"))
    sensor_costs = tuple(_q(x, "sensor_cost") for x in sensor_costs)
    if len(sensor_costs) != len(candidates[0].sensors):
        raise ValueError("one sensor cost is required per channel")
    if reset_cost < 0 or elapsed_cost <= 0 or heating_cost < 0 or any(x <= 0 for x in sensor_costs):
        raise ValueError("elapsed and sensor costs must be positive; reset and heating nonnegative")
    validated = []
    for word, sensor in protocols:
        word = tuple(_q(a, "heater amplitude") for a in word)
        if any(a < 0 or a > 2 for a in word):
            raise ValueError("heater amplitudes must lie in [0,2]")
        validated.append((word, _index(sensor, len(sensor_costs), "sensor")))
    caches = [{(): ((Fraction(0),) * c.dimension,
                    (initial_radius,) * c.dimension)} for c in candidates]

    def evolve(c, cache, word):
        if word in cache:
            return cache[word]
        # Iteration avoids a recursion-depth dependency on experiment horizon.
        prefix = len(word)
        while word[:prefix] not in cache:
            prefix -= 1
        state, bound = cache[word[:prefix]]
        for index in range(prefix, len(word)):
            state = c.step(state, word[index])
            next_bound = [process_radius] * c.dimension
            for i, j, value in c.entries:
                next_bound[i] += abs(value) * bound[j]
            bound = tuple(next_bound)
            cache[word[:index + 1]] = state, bound
        return state, bound

    readings, errors, costs = [], [], []
    for word, sensor in validated:
        row, error = [], []
        for c, cache in zip(candidates, caches):
            state, bound = evolve(c, cache, word)
            row.append(c.observe(state, sensor))
            error.append(sum((abs(a) * b for a, b in zip(c.sensors[sensor], bound)), Fraction(0))
                         + sensor_noise + reduction_error)
        readings.append(tuple(row))
        errors.append(tuple(error))
        costs.append(reset_cost + elapsed_cost * len(word) + heating_cost * sum(word) + sensor_costs[sensor])
    pool = reading_pool(costs, readings, validated, candidates=len(candidates))
    return DiagnosticPool(pool, tuple(max(row) for row in errors), tuple(errors),
                          tuple(c.identifier for c in candidates))


@dataclass(frozen=True)
class AffineOperatorCompilation:
    system: OperatorSystem
    states: tuple
    candidate_ids: tuple
    amplitudes: tuple


def affine_operator_system(candidates, amplitudes=(0, 2), *, initial_states=None,
                           attachment_costs=(1, 2), observation_costs=(3, 3, 4, 4),
                           max_dimension=256):
    """Small-model exact block-diagonal homogeneous lift to the existing engine.

    H_c,u=[[A_c,b_c*u],[0,1]], M_u=diag_c H_c,u.  Candidate c's initial
    vector has (x_c,1) in its own block and zero in all other blocks.  A
    common sensor row concatenates (C_c,j,0).  This retains candidate identity.
    Dense materialization is deliberately budgeted; use protocol_pool for the
    144-state sparse models rather than expanding a mostly zero giant matrix.
    """
    candidates = _candidates(candidates)
    amplitudes = tuple(_q(a, "amplitude") for a in amplitudes)
    dimension = sum(c.dimension + 1 for c in candidates)
    if isinstance(max_dimension, bool) or not isinstance(max_dimension, int):
        raise TypeError("max_dimension must be an int")
    if max_dimension < 1 or dimension > max_dimension:
        raise ValueError("dense affine lift exceeds max_dimension")
    if initial_states is None:
        initial_states = tuple((Fraction(0),) * c.dimension for c in candidates)
    else:
        initial_states = tuple(initial_states)
        if len(initial_states) != len(candidates):
            raise ValueError("one initial state per candidate is required")
        initial_states = tuple(_vector(x, c.dimension, "initial state")
                               for c, x in zip(candidates, initial_states))
    operators = []
    for amplitude in amplitudes:
        rows = [[Fraction(0)] * dimension for _ in range(dimension)]
        offset = 0
        for c in candidates:
            for i, j, value in c.entries:
                rows[offset + i][offset + j] = value
            for i, value in enumerate(c.heater):
                rows[offset + i][offset + c.dimension] = value * amplitude
            rows[offset + c.dimension][offset + c.dimension] = Fraction(1)
            offset += c.dimension + 1
        operators.append(tuple(tuple(row) for row in rows))
    observations = []
    for sensor in range(len(candidates[0].sensors)):
        observations.append(tuple(x for c in candidates for x in (*c.sensors[sensor], Fraction(0))))
    states = []
    offset = 0
    for c, initial in zip(candidates, initial_states):
        vector = [Fraction(0)] * dimension
        vector[offset:offset + c.dimension] = initial
        vector[offset + c.dimension] = Fraction(1)
        states.append(tuple(vector))
        offset += c.dimension + 1
    system = OperatorSystem(dimension, operators, observations, attachment_costs, observation_costs)
    return AffineOperatorCompilation(system, tuple(states), tuple(c.identifier for c in candidates), amplitudes)
