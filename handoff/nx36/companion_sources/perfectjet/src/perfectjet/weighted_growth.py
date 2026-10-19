"""Finite type partitions, exact sensitivities, and scoped growth certificates.

Histograms are sufficient statistics only for products of constant type
weights.  Graph paths retain their state and time before aggregation.  Use
``weighted_paths`` with position_weights for time/order-sensitive prices.

A finite census alone proves no statement about an external infinite graph.
The certificates below either prove domination for *all walks of the supplied
finite graph* by an induced row-sum bound, or explicitly retain a caller's
unproved external domination assumption.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Iterable, Mapping, Sequence

from .precision import _q

Q = Fraction
MAX_TYPES = 32
MAX_HISTOGRAM_TERMS = 50_000
MAX_DEGREE = 512
MAX_NODES = 4096
MAX_EDGES = 50_000
MAX_FRONTIER = 100_000
MAX_EXPANSIONS = 1_000_000


def _integer(value, name, minimum=0, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} must be an integer in the supported range.")
    return value


def _names(values: Iterable[str]) -> tuple[str, ...]:
    result = []
    for name in values:
        if len(result) >= MAX_TYPES:
            raise ValueError(f"At most {MAX_TYPES} types are supported.")
        if not isinstance(name, str) or not name or len(name) > 256 or name in result:
            raise ValueError("Type names must be unique, nonempty strings of at most 256 characters.")
        result.append(name)
    return tuple(result)


def _bounded_vector(values, size):
    result = []
    for value in values:
        if len(result) >= size:
            raise ValueError("One value is required for each type; too many supplied.")
        result.append(value)
    if len(result) != size:
        raise ValueError("One value is required for each type.")
    return tuple(result)


def _weights(names, values, *, positive=False) -> tuple[Q, ...]:
    if isinstance(values, Mapping):
        if set(values) != set(names):
            raise ValueError("Weights must specify exactly the histogram/graph types.")
        values = tuple(values[name] for name in names)
    else:
        values = _bounded_vector(values, len(names))
    if len(values) != len(names):
        raise ValueError("One weight is required for each type.")
    result = tuple(_q(x) for x in values)
    if any(x < 0 or (positive and x == 0) for x in result):
        raise ValueError("Weights must be positive." if positive else "Weights must be nonnegative.")
    if any(max(x.numerator.bit_length(), x.denominator.bit_length()) > 4096 for x in result):
        raise ValueError("Weight bit-size limit exceeded.")
    return result


def _floats(names, values) -> tuple[float, ...]:
    if isinstance(values, Mapping):
        if set(values) != set(names):
            raise ValueError("One log weight is required for each type.")
        values = tuple(values[name] for name in names)
    else:
        values = _bounded_vector(values, len(names))
    if len(values) != len(names):
        raise ValueError("One log weight is required for each type.")
    result = tuple(float(x) for x in values)
    if any(not math.isfinite(x) or abs(x) > 1e100 for x in result):
        raise ValueError("Log weights must be finite and have magnitude at most 1e100.")
    return result


def _power_guard(weights, degree):
    # A common denominator for any length-d product divides the product of
    # all type denominators to power d.  Bound this before forming powers.
    bits = sum(w.numerator.bit_length() + w.denominator.bit_length() for w in weights)
    if degree * bits > 1_000_000:
        raise ValueError("Requested rational path products exceed the bit-size work limit.")


@dataclass(frozen=True)
class PartitionEvaluation:
    partition: Q
    mean_counts: tuple[Q, ...] | None
    covariance: tuple[tuple[Q, ...], ...] | None
    weight_derivatives: tuple[Q, ...]
    positive_weights: bool

    def to_dict(self) -> dict:
        return {
            "partition": str(self.partition),
            "mean_counts": None if self.mean_counts is None else [str(x) for x in self.mean_counts],
            "covariance": None if self.covariance is None else [[str(x) for x in row] for row in self.covariance],
            "weight_derivatives": [str(x) for x in self.weight_derivatives],
            "arithmetic": "exact rational",
            "log_sensitivity_valid": self.positive_weights and self.partition > 0,
            "sensitivity_variables": "log weights; covariance equals the Hessian of log Z when all weights are positive",
        }


@dataclass(frozen=True)
class TypeHistogram:
    """Z(w)=sum_n c[n]*product_i w[i]**n[i], with exact integer multiplicities."""
    type_names: tuple[str, ...]
    counts: Mapping[tuple[int, ...], int]

    def __post_init__(self):
        names = _names(self.type_names)
        if len(self.counts) > MAX_HISTOGRAM_TERMS:
            raise ValueError("Histogram term limit exceeded.")
        cleaned = {}
        for exponents, count in self.counts.items():
            exponents = tuple(exponents)
            if len(exponents) != len(names):
                raise ValueError("Each count vector must have one coordinate per type.")
            for exponent in exponents:
                _integer(exponent, "type count", maximum=MAX_DEGREE)
            if sum(exponents) > MAX_DEGREE:
                raise ValueError("Histogram degree limit exceeded.")
            _integer(count, "multiplicity")
            if count.bit_length() > 65_536:
                raise ValueError("Multiplicity bit-size limit exceeded.")
            if count:
                cleaned[exponents] = count
        if sum(count.bit_length() for count in cleaned.values()) > 2_000_000:
            raise ValueError("Combined multiplicity bit-size limit exceeded.")
        object.__setattr__(self, "type_names", names)
        # Own a copy: changing the caller's input must not change a compiled census.
        from types import MappingProxyType
        object.__setattr__(self, "counts", MappingProxyType(dict(sorted(cleaned.items()))))

    @property
    def population(self) -> int:
        return sum(self.counts.values())

    def _evaluation_guard(self, weights):
        degree = max((sum(n) for n in self.counts), default=0)
        _power_guard(weights, degree)
        bits = max((max(w.numerator.bit_length(), w.denominator.bit_length()) for w in weights), default=1)
        if degree * bits > 100_000:
            raise ValueError("Requested exact powers exceed the bit-size work limit.")
        if len(self.counts) * max(1, len(weights) ** 2) > 5_000_000:
            raise ValueError("Requested sensitivity table exceeds the work limit.")

    def evaluate(self, weights) -> PartitionEvaluation:
        weights = _weights(self.type_names, weights)
        self._evaluation_guard(weights)
        dim = len(weights)
        powers = []
        for i, weight in enumerate(weights):
            degree = max((n[i] for n in self.counts), default=0)
            powers.append(tuple(weight ** k for k in range(degree + 1)))
        partition = Q(0)
        first = [Q(0)] * dim
        second = [[Q(0) for _ in range(dim)] for _ in range(dim)]
        derivatives = [Q(0)] * dim
        for exponents, count in self.counts.items():
            mass = Q(count)
            for i, exponent in enumerate(exponents):
                mass *= powers[i][exponent]
            partition += mass
            for i, ni in enumerate(exponents):
                first[i] += ni * mass
                for j, nj in enumerate(exponents):
                    second[i][j] += ni * nj * mass
                if ni:
                    derivative = Q(count * ni)
                    for j, nj in enumerate(exponents):
                        derivative *= powers[j][nj - int(i == j)]
                    derivatives[i] += derivative
        means = tuple(x / partition for x in first) if partition else None
        covariance = tuple(tuple(second[i][j] / partition - means[i] * means[j]
                                 for j in range(dim)) for i in range(dim)) if partition else None
        return PartitionEvaluation(partition, means, covariance, tuple(derivatives), all(weights))

    def log_partition(self, log_weights) -> dict:
        """Stable floating log-partition and moments; NOT a rigorous exp certificate."""
        values = _floats(self.type_names, log_weights)
        if not self.counts:
            return {"log_partition": None, "partition": 0.0, "mean_counts": None,
                    "covariance": None, "arithmetic": "floating-point approximation",
                    "rigorous_exponential_error_bound": None, "status": "empty_population"}
        if len(self.counts) * max(1, len(values) ** 2) > 5_000_000:
            raise ValueError("Requested sensitivity table exceeds the work limit.")
        entries = tuple(self.counts)
        logs = [math.log(self.counts[n]) + math.fsum(k * u for k, u in zip(n, values)) for n in entries]
        peak = max(logs)
        masses = [math.exp(x - peak) for x in logs]
        normalizer = math.fsum(masses)
        probabilities = [x / normalizer for x in masses]
        log_z = peak + math.log(normalizer)
        means = [math.fsum(p * n[i] for p, n in zip(probabilities, entries)) for i in range(len(values))]
        # Centered moments avoid a separate large-minus-large cancellation.
        covariance = [[math.fsum(p * (n[i] - means[i]) * (n[j] - means[j])
                                 for p, n in zip(probabilities, entries))
                       for j in range(len(values))] for i in range(len(values))]
        try:
            partition = math.exp(log_z)
        except OverflowError:
            partition = None
        return {"log_partition": log_z, "partition": partition, "mean_counts": means,
                "covariance": covariance, "arithmetic": "floating-point approximation",
                "rigorous_exponential_error_bound": None,
                "status": "finite_log_partition",
                "limits": "Exponentials and their sensitivities have no rigorous evaluation-error enclosure here."}

    def to_dict(self) -> dict:
        return {"type_names": list(self.type_names), "population": self.population,
                "histogram": [{"counts": list(n), "multiplicity": c} for n, c in self.counts.items()],
                "repricing_scope": "Constant multiplicative weights per retained type; chronology-dependent prices require extra state or weighted_paths."}


@dataclass(frozen=True)
class GrowthCertificate:
    """A block norm proof or explicitly conditional dominating-growth assumption."""
    block_length: int
    block_bound: Q
    remainder_bounds: tuple[Q, ...]
    scope: str
    assumptions: tuple[str, ...]
    conditional: bool = False

    def __post_init__(self):
        block = _integer(self.block_length, "block_length", minimum=1, maximum=MAX_DEGREE)
        bound = Q(self.block_bound)
        remainders = tuple(Q(x) for x in _bounded_vector(self.remainder_bounds, block))
        if bound < 0 or any(x < 0 for x in remainders):
            raise ValueError("Growth bounds must be nonnegative.")
        if any(max(x.numerator.bit_length(), x.denominator.bit_length()) > 1_000_000
               for x in (bound,) + remainders):
            raise ValueError("Growth coefficient bit-size limit exceeded.")
        if not isinstance(self.scope, str) or not self.scope:
            raise ValueError("A growth certificate must identify its scope.")
        if not self.assumptions or any(not isinstance(x, str) or not x.strip() for x in self.assumptions):
            raise ValueError("Explicit growth assumptions are required.")
        object.__setattr__(self, "block_bound", bound)
        object.__setattr__(self, "remainder_bounds", remainders)
        object.__setattr__(self, "assumptions", tuple(self.assumptions))

    @property
    def subcritical(self) -> bool:
        return self.block_bound < 1

    def tail(self, minimum_length: int = 0) -> Q:
        """Sum the proved residue-class bounds for all lengths >= minimum_length."""
        minimum_length = _integer(minimum_length, "minimum_length", maximum=1_000_000)
        if not self.subcritical:
            raise ValueError("No summable geometric tail: the block bound must be below one.")
        b = self.block_length
        total = Q(0)
        for r, prefactor in enumerate(self.remainder_bounds):
            first_block = max(0, (minimum_length - r + b - 1) // b)
            if first_block * (self.block_bound.numerator.bit_length() + self.block_bound.denominator.bit_length()) > 2_000_000:
                raise ValueError("Requested exact tail exceeds the bit-size work limit.")
            total += prefactor * self.block_bound ** first_block / (1 - self.block_bound)
        return total

    def to_dict(self, minimum_length: int = 0) -> dict:
        if self.block_bound:
            exponent = (math.log(self.block_bound.numerator) - math.log(self.block_bound.denominator)) / self.block_length
            try:
                numeric_bound = math.exp(exponent)
            except OverflowError:
                numeric_bound = None
        else:
            numeric_bound = 0.0
        return {"block_length": self.block_length, "block_bound": str(self.block_bound),
                "remainder_bounds": [str(x) for x in self.remainder_bounds],
                "subcritical": self.subcritical, "scope": self.scope,
                "conditional": self.conditional, "assumptions": list(self.assumptions),
                "tail_minimum_length": minimum_length,
                "tail_bound": str(self.tail(minimum_length)) if self.subcritical else None,
                "growth_rate_upper_bound_numeric": numeric_bound,
                "growth_rate_numeric_status": "approximation; exact block_bound is the certificate",
                "external_infinite_graph_claim": self.conditional}


@dataclass(frozen=True)
class ColoredEdge:
    source: int
    target: int
    color: str


class ColoredGraph:
    """A complete finite directed multigraph; parallel edges count separately."""
    def __init__(self, node_count: int, edges: Iterable[ColoredEdge | tuple], type_names: Sequence[str] | None = None):
        self.node_count = _integer(node_count, "node_count", minimum=1, maximum=MAX_NODES)
        retained = []
        colors = []
        for edge in edges:
            if len(retained) >= MAX_EDGES:
                raise ValueError("Edge-count limit exceeded.")
            if not isinstance(edge, ColoredEdge):
                try:
                    edge = ColoredEdge(*edge)
                except (TypeError, ValueError) as exc:
                    raise ValueError("Each edge must be (source, target, color).") from exc
            _integer(edge.source, "edge source", maximum=node_count - 1)
            _integer(edge.target, "edge target", maximum=node_count - 1)
            if not isinstance(edge.color, str) or not edge.color:
                raise ValueError("Edge colors must be nonempty strings.")
            if edge.color not in colors:
                colors.append(edge.color)
            retained.append(edge)
        self.type_names = _names(type_names if type_names is not None else colors)
        if set(colors) - set(self.type_names):
            raise ValueError("An edge color is absent from type_names.")
        self.edges = tuple(retained)
        self._colors = {name: i for i, name in enumerate(self.type_names)}
        outgoing = [[] for _ in range(node_count)]
        for index, edge in enumerate(retained):
            outgoing[edge.source].append(index)
        self.outgoing = tuple(tuple(row) for row in outgoing)

    def _start_accepting(self, start, accepting):
        start = _integer(start, "start", maximum=self.node_count - 1)
        if accepting is None:
            return start, frozenset(range(self.node_count))
        result = set()
        for node in accepting:
            result.add(_integer(node, "accepting state", maximum=self.node_count - 1))
        return start, frozenset(result)

    def histogram(self, length: int, *, start: int = 0, accepting: Iterable[int] | None = None,
                  self_avoiding: bool = False, max_frontier: int = MAX_FRONTIER,
                  max_expansions: int = MAX_EXPANSIONS) -> TypeHistogram:
        """Count paths by type vector after respecting ordered transitions.

        For self_avoiding=True, no vertex may be revisited (including the start).
        This is a finite-graph census, not a connective constant measurement.
        """
        length = _integer(length, "length", maximum=MAX_DEGREE)
        max_frontier = _integer(max_frontier, "max_frontier", minimum=1, maximum=MAX_FRONTIER)
        max_expansions = _integer(max_expansions, "max_expansions", minimum=1, maximum=MAX_EXPANSIONS)
        start, accepted = self._start_accepting(start, accepting)
        dim = len(self.type_names)
        frontier = {(start, 1 << start if self_avoiding else 0, (0,) * dim): 1}
        expansions = 0
        for _ in range(length):
            nxt = {}
            for (state, visited, counts), multiplicity in frontier.items():
                for edge_index in self.outgoing[state]:
                    expansions += 1
                    if expansions > max_expansions:
                        raise ValueError("Path expansion work limit exceeded.")
                    edge = self.edges[edge_index]
                    if self_avoiding and visited & (1 << edge.target):
                        continue
                    updated = list(counts)
                    updated[self._colors[edge.color]] += 1
                    key = (edge.target, visited | (1 << edge.target) if self_avoiding else 0, tuple(updated))
                    nxt[key] = nxt.get(key, 0) + multiplicity
                    if len(nxt) > max_frontier:
                        raise ValueError("Path frontier limit exceeded.")
            frontier = nxt
        histogram = {}
        for (state, _, counts), multiplicity in frontier.items():
            if state in accepted:
                histogram[counts] = histogram.get(counts, 0) + multiplicity
        return TypeHistogram(self.type_names, histogram)

    def path_weight(self, edge_indices: Iterable[int], weights, *, start: int = 0,
                    position_weights: Sequence | None = None) -> Q:
        """Price one ordered edge sequence, validating each state transition."""
        indices = []
        for index in edge_indices:
            if len(indices) >= MAX_DEGREE:
                raise ValueError("Path length limit exceeded.")
            indices.append(_integer(index, "edge index", maximum=len(self.edges) - 1))
        state, _ = self._start_accepting(start, None)
        base = _weights(self.type_names, weights)
        _power_guard(base, len(indices))
        if position_weights is not None and len(position_weights) != len(indices):
            raise ValueError("One position weight mapping/vector is required per path step.")
        result = Q(1)
        for t, index in enumerate(indices):
            edge = self.edges[index]
            if edge.source != state:
                raise ValueError("Edge sequence is not a path from the supplied start.")
            current = base if position_weights is None else _weights(self.type_names, position_weights[t])
            _power_guard(current, len(indices))
            result *= current[self._colors[edge.color]]
            state = edge.target
        return result

    def weighted_paths(self, length: int, weights, *, start: int = 0,
                       accepting: Iterable[int] | None = None,
                       position_weights: Sequence | None = None,
                       self_avoiding: bool = False,
                       max_frontier: int = MAX_FRONTIER, max_expansions: int = MAX_EXPANSIONS) -> Q:
        """Sum path products without dropping state, visited vertices, or time.

        Position weights replace the base weights at each step.  The histogram
        API deliberately does not accept them: type counts alone are insufficient.
        """
        length = _integer(length, "length", maximum=MAX_DEGREE)
        max_frontier = _integer(max_frontier, "max_frontier", minimum=1, maximum=MAX_FRONTIER)
        max_expansions = _integer(max_expansions, "max_expansions", minimum=1, maximum=MAX_EXPANSIONS)
        start, accepted = self._start_accepting(start, accepting)
        base = _weights(self.type_names, weights)
        _power_guard(base, length)
        if position_weights is not None and len(position_weights) != length:
            raise ValueError("One position weight mapping/vector is required per path step.")
        frontier = {(start, 1 << start if self_avoiding else 0): Q(1)}
        expansions = 0
        for t in range(length):
            current = base if position_weights is None else _weights(self.type_names, position_weights[t])
            _power_guard(current, length)
            nxt = {}
            for (state, visited), mass in frontier.items():
                for index in self.outgoing[state]:
                    expansions += 1
                    if expansions > max_expansions:
                        raise ValueError("Path expansion work limit exceeded.")
                    edge = self.edges[index]
                    if self_avoiding and visited & (1 << edge.target):
                        continue
                    key = (edge.target, visited | (1 << edge.target) if self_avoiding else 0)
                    nxt[key] = nxt.get(key, Q(0)) + mass * current[self._colors[edge.color]]
                    if len(nxt) > max_frontier:
                        raise ValueError("Path frontier limit exceeded.")
            frontier = nxt
        return sum((mass for (state, _), mass in frontier.items() if state in accepted), Q(0))

    def block_certificate(self, weights, block_length: int = 1, *, external_domination: str | None = None) -> GrowthCertificate:
        """Use the exact maximum row sum of A**N, uniformly over all starts.

        ||A**(kN+r)||_infinity <= ||A**N||_infinity**k * ||A**r||_infinity.
        This justifies an all-length finite-graph tail.  Merely enumerating a few
        self-avoiding path counts would not justify the same conclusion.
        """
        block_length = _integer(block_length, "block_length", minimum=1, maximum=MAX_DEGREE)
        if block_length * len(self.edges) > MAX_EXPANSIONS:
            raise ValueError("Certificate work limit exceeded.")
        values = _weights(self.type_names, weights)
        _power_guard(values, block_length)
        row_sums = [Q(1)] * self.node_count
        bounds = [Q(1)]
        for _ in range(block_length):
            nxt = [Q(0)] * self.node_count
            for edge in self.edges:
                nxt[edge.source] += values[self._colors[edge.color]] * row_sums[edge.target]
            row_sums = nxt
            bounds.append(max(row_sums))
        if external_domination is not None and (not isinstance(external_domination, str) or not external_domination.strip()):
            raise ValueError("External use requires an explicit nonempty domination assumption.")
        assumptions = (
            "The supplied finite multigraph contains every permitted transition of the claimed finite model.",
            "Every path weight is the product of the supplied nonnegative, time-independent type weights.",
            "The bound is uniform over start vertices; self-avoiding paths are a subset of these walks.",
        )
        if external_domination is not None:
            assumptions += ("UNPROVED EXTERNAL DOMINATION: " + external_domination,)
        scope = "finite_graph_all_walks" if external_domination is None else "external_model_conditional_on_weight_domination"
        return GrowthCertificate(block_length, bounds[-1], tuple(bounds[:-1]), scope, assumptions,
                                 external_domination is not None)

    def row_sum_certificate(self, weights, *, external_domination: str | None = None) -> GrowthCertificate:
        return self.block_certificate(weights, 1, external_domination=external_domination)


def assumed_geometric_tail(
    growth_ratio, minimum_length: int, *, prefactor=1, domination_assumption: str,
) -> dict:
    """Conditional C*q**d/(1-q); the caller must supply Z_l <= C*q**l for ALL l.

    A finite observed census or a scalar proxy does not discharge this premise.
    """
    ratio, prefactor = _q(growth_ratio), _q(prefactor)
    if not 0 <= ratio < 1 or prefactor < 0:
        raise ValueError("Require 0 <= growth_ratio < 1 and prefactor >= 0.")
    if not isinstance(domination_assumption, str) or not domination_assumption.strip():
        raise ValueError("An explicit all-length domination assumption is required.")
    certificate = GrowthCertificate(1, ratio, (prefactor,), "caller_supplied_all_length_domination",
                                    ("UNPROVED: " + domination_assumption,), True)
    return certificate.to_dict(minimum_length)


def receipt() -> dict:
    """Deterministic exact finite replay; historical 4-million-path claims excluded."""
    graph = ColoredGraph(2, [(0, 0, "space"), (0, 1, "time"), (1, 0, "space")])
    histogram = graph.histogram(10)
    weights = {"space": Q(1, 7), "time": Q(1, 5)}
    evaluation = histogram.evaluate(weights)
    certificate = graph.row_sum_certificate(weights)
    # Individual outgoing rows can exceed one while two-step growth contracts.
    block_graph = ColoredGraph(2, [(0, 1, "heavy"), (1, 0, "light")])
    block_weights = {"heavy": 2, "light": Q(1, 10)}
    block = block_graph.block_certificate(block_weights, 2)
    return {
        "mechanism": "weighted type histograms and scoped colored-path growth",
        "status": "exact_finite_graph_replay",
        "histogram": histogram.to_dict(), "repriced": evaluation.to_dict(),
        "floating_log_partition": histogram.log_partition([math.log(float(weights[name])) for name in graph.type_names]),
        "growth_certificate": certificate.to_dict(5), "block_certificate": block.to_dict(5),
        "checks": {"independent_direct_path_sum_agrees": evaluation.partition == graph.weighted_paths(10, weights),
                   "positive_covariance_diagonal": all(evaluation.covariance[i][i] >= 0 for i in range(2)),
                   "two_step_bound_improves_row_sum": not block_graph.row_sum_certificate(block_weights).subcritical and block.subcritical},
        "limits": ["No infinite graph is inferred from a finite census.",
                   "External model transfer is conditional on a supplied all-length weight domination statement.",
                   "Type histograms cannot reprice omitted order/chronology dependence.",
                   "Floating exponential outputs have no rigorous evaluation error bound."],
    }
