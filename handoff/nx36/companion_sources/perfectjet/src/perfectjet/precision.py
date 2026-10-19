"""Exact cancellation analysis and adaptive binary precision.

Terms are exact rational numbers.  A float input denotes its *stored binary
value*, not a measured real number.  We simulate round-to-nearest, ties-to-even
with an arbitrary exponent range; this is not an IEEE overflow/underflow model.
Evaluation, measurement/input, and model error are separate supplied absolute
budgets.  None is inferred from a cancellation condition number.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
import math
import re
from typing import Iterable, Mapping

Q = Fraction
MAX_TERMS = 10_000
MAX_INPUT_BITS = 65_536
MAX_TOTAL_BITS = 2_000_000
MAX_PRECISION_BITS = 16_384


def _q(value) -> Q:
    if isinstance(value, str):
        if len(value) > 4096:
            raise ValueError("Rational input is too long.")
        exponent = re.search(r"[eE]([+-]?\d+)$", value)
        if exponent and abs(int(exponent.group(1))) > 4096:
            raise ValueError("Decimal exponent exceeds the resource limit.")
    elif isinstance(value, Decimal):
        if not value.is_finite() or abs(value.as_tuple().exponent) > 4096:
            raise ValueError("Decimal input is nonfinite or exceeds the exponent limit.")
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Inputs must be finite.")
    elif not isinstance(value, (int, Q)):
        raise TypeError("Terms must be integers, fractions, finite floats, or decimal strings.")
    result = Q(value)
    if max(result.numerator.bit_length(), result.denominator.bit_length()) > MAX_INPUT_BITS:
        raise ValueError("Rational input exceeds the bit-size limit.")
    return result


def _nonnegative(value, name: str) -> Q:
    result = _q(value)
    if result < 0:
        raise ValueError(f"{name} must be nonnegative.")
    return result


def _terms(values: Iterable) -> tuple[Q, ...]:
    result = []
    budget = 0
    for value in values:
        if len(result) >= MAX_TERMS:
            raise ValueError(f"At most {MAX_TERMS} terms are supported.")
        term = _q(value)
        budget += term.numerator.bit_length() + term.denominator.bit_length()
        if budget > MAX_TOTAL_BITS:
            raise ValueError("Combined input bit-size limit exceeded.")
        result.append(term)
    return tuple(result)


def _bits(bits: int) -> int:
    if type(bits) is not int or not 2 <= bits <= MAX_PRECISION_BITS:
        raise ValueError(f"bits must be an integer from 2 to {MAX_PRECISION_BITS}.")
    return bits


def _pow2(exponent: int) -> Q:
    return Q(1 << exponent) if exponent >= 0 else Q(1, 1 << -exponent)


def round_binary(value, bits: int = 53) -> Q:
    """Round exactly to a p-significant-bit dyadic, with unbounded exponents."""
    bits = _bits(bits)
    value = _q(value)
    if not value:
        return Q(0)
    sign = 1 if value > 0 else -1
    value = abs(value)
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    if value < _pow2(exponent):
        exponent -= 1
    step = _pow2(exponent - bits + 1)
    scaled = value / step
    integer, remainder = divmod(scaled.numerator, scaled.denominator)
    twice = 2 * remainder
    if twice > scaled.denominator or (twice == scaled.denominator and integer % 2):
        integer += 1
    return sign * integer * step


def _log2_fraction(value: Q) -> float:
    # math.log2 handles arbitrarily large integers without first making a float.
    return math.log2(value.numerator) - math.log2(value.denominator)


@dataclass(frozen=True)
class SumAnalysis:
    term_count: int
    bits: int
    exact_sum: Q
    approximation: Q
    absolute_mass: Q
    condition: Q | None
    condition_status: str
    cancellation_bits: float | None
    unit_roundoff: Q
    gamma: Q | None
    conversion_error_bound: Q
    recursive_error_bound: Q | None
    forward_error_bound: Q | None
    actual_arithmetic_error: Q
    evaluation_error: Q
    input_error: Q
    model_error: Q

    @property
    def external_error(self) -> Q:
        return self.evaluation_error + self.input_error + self.model_error

    @property
    def certified_arithmetic_error(self) -> Q:
        """Exact replay tightens the generic forward bound when it is available."""
        return self.actual_arithmetic_error if self.forward_error_bound is None else min(
            self.actual_arithmetic_error, self.forward_error_bound)

    @property
    def total_error_bound(self) -> Q:
        return self.certified_arithmetic_error + self.external_error

    @property
    def interval(self) -> tuple[Q, Q]:
        return self.approximation - self.total_error_bound, self.approximation + self.total_error_bound

    def to_dict(self) -> dict:
        return {
            "term_count": self.term_count, "bits": self.bits,
            "exact_sum": str(self.exact_sum), "approximation": str(self.approximation),
            "absolute_mass": str(self.absolute_mass),
            "condition": None if self.condition is None else str(self.condition),
            "condition_status": self.condition_status, "cancellation_bits": self.cancellation_bits,
            "unit_roundoff": str(self.unit_roundoff),
            "gamma": None if self.gamma is None else str(self.gamma),
            "conversion_error_bound": str(self.conversion_error_bound),
            "recursive_error_bound": None if self.recursive_error_bound is None else str(self.recursive_error_bound),
            "forward_error_bound": None if self.forward_error_bound is None else str(self.forward_error_bound),
            "relative_forward_error_bound": None if self.forward_error_bound is None or not self.exact_sum else str(self.forward_error_bound / abs(self.exact_sum)),
            "gamma_condition_bound_for_exactly_representable_terms": None if self.gamma is None or self.condition is None or self.conversion_error_bound else str(self.gamma * self.condition),
            "actual_arithmetic_error": str(self.actual_arithmetic_error),
            "certified_arithmetic_error": str(self.certified_arithmetic_error),
            "evaluation_error": str(self.evaluation_error), "input_error": str(self.input_error),
            "model_error": str(self.model_error), "total_error_bound": str(self.total_error_bound),
            "interval": [str(x) for x in self.interval],
            "arithmetic_model": "round-to-nearest ties-to-even; arbitrary exponent range",
            "error_scope": "Supplied external budgets must themselves be justified by the caller.",
        }


def analyze_sum(
    terms: Iterable, *, bits: int = 53, evaluation_error=0, input_error=0, model_error=0,
) -> SumAnalysis:
    """Replay an ordered recursive sum and bound its rounding error exactly.

    Conversion is accounted for separately.  The standard gamma_(n-1) bound
    applies to the already rounded terms when (n-1)*2**(-bits) < 1.  If that
    premise fails, the generic bound is absent; the exact replay remains valid.
    """
    values = _terms(terms)
    bits = _bits(bits)
    evaluation_error = _nonnegative(evaluation_error, "evaluation_error")
    input_error = _nonnegative(input_error, "input_error")
    model_error = _nonnegative(model_error, "model_error")
    exact_sum = sum(values, Q(0))
    mass = sum(map(abs, values), Q(0))
    rounded = tuple(round_binary(x, bits) for x in values)
    approximation = rounded[0] if rounded else Q(0)
    for value in rounded[1:]:
        approximation = round_binary(approximation + value, bits)
    conversion = sum((abs(x - y) for x, y in zip(values, rounded)), Q(0))
    u = Q(1, 1 << bits)
    mu = max(0, len(values) - 1) * u
    gamma = mu / (1 - mu) if mu < 1 else None
    recursive = None if gamma is None else gamma * sum(map(abs, rounded), Q(0))
    forward = None if recursive is None else conversion + recursive
    condition = mass / abs(exact_sum) if exact_sum else None
    status = "finite" if exact_sum else ("infinite_zero_sum" if mass else "all_zero")
    lost = _log2_fraction(condition) if condition is not None else None
    return SumAnalysis(
        len(values), bits, exact_sum, approximation, mass, condition, status, lost,
        u, gamma, conversion, recursive, forward, abs(approximation - exact_sum),
        evaluation_error, input_error, model_error,
    )


@dataclass(frozen=True)
class PrecisionRepair:
    initial: SumAnalysis
    final: SumAnalysis
    attempted_bits: tuple[int, ...]
    arithmetic_tolerance: Q
    satisfied: bool
    total_budget_satisfied: bool

    def to_dict(self) -> dict:
        return {
            "initial": self.initial.to_dict(), "final": self.final.to_dict(),
            "attempted_bits": list(self.attempted_bits),
            "arithmetic_tolerance": str(self.arithmetic_tolerance),
            "satisfied": self.satisfied, "total_budget_satisfied": self.total_budget_satisfied,
            "reason": "Arithmetic tolerance met." if self.satisfied else "Precision resource limit reached.",
        }


def repair_sum(
    terms: Iterable, *, absolute_tolerance=Q(1, 10**12), relative_tolerance=0,
    initial_bits: int = 53, max_bits: int = 4096,
    evaluation_error=0, input_error=0, model_error=0,
) -> PrecisionRepair:
    """Double precision until the certified arithmetic error meets the target.

    The tolerance is abs_tol + rel_tol*abs(exact nominal sum).  This repairs
    evaluation arithmetic only; supplied physical/model budgets do not shrink.
    """
    values = _terms(terms)
    initial_bits, max_bits = _bits(initial_bits), _bits(max_bits)
    if max_bits < initial_bits:
        raise ValueError("max_bits must be at least initial_bits.")
    abs_tol = _nonnegative(absolute_tolerance, "absolute_tolerance")
    rel_tol = _nonnegative(relative_tolerance, "relative_tolerance")
    tolerance = abs_tol + rel_tol * abs(sum(values, Q(0)))
    initial = analyze_sum(values, bits=initial_bits, evaluation_error=evaluation_error,
                          input_error=input_error, model_error=model_error)
    final = initial
    attempts = [initial_bits]
    while final.certified_arithmetic_error > tolerance and final.bits < max_bits:
        bits = min(2 * final.bits, max_bits)
        final = analyze_sum(values, bits=bits, evaluation_error=evaluation_error,
                            input_error=input_error, model_error=model_error)
        attempts.append(bits)
    return PrecisionRepair(initial, final, tuple(attempts), tolerance,
                           final.certified_arithmetic_error <= tolerance,
                           final.total_error_bound <= tolerance)


@dataclass(frozen=True)
class DecisionReport:
    status: str
    winner: str | None
    maximize: bool
    nominal_order: tuple[str, ...]
    candidates: Mapping[str, PrecisionRepair]
    certified_gap: Q | None

    def to_dict(self) -> dict:
        return {
            "status": self.status, "winner": self.winner, "maximize": self.maximize,
            "nominal_order": list(self.nominal_order),
            "certified_gap": None if self.certified_gap is None else str(self.certified_gap),
            "candidates": {name: result.to_dict() for name, result in self.candidates.items()},
            "decision_scope": "Nominal exact terms plus caller-supplied absolute uncertainty budgets.",
        }


def compare_sums(
    candidates: Mapping[str, Iterable], *, error_budgets: Mapping[str, Mapping] | None = None,
    maximize: bool = True, initial_bits: int = 53, max_bits: int = 4096,
) -> DecisionReport:
    """Repair numerical near ties, then require disjoint uncertainty intervals.

    error_budgets maps each candidate to evaluation_error/input_error/model_error.
    A high nominal score alone never certifies a winner under overlapping bounds.
    """
    if not 1 <= len(candidates) <= 256:
        raise ValueError("Supply between 1 and 256 candidates.")
    if any(not isinstance(name, str) or not name for name in candidates):
        raise ValueError("Candidate names must be nonempty strings.")
    budgets = error_budgets or {}
    if set(budgets) - set(candidates):
        raise ValueError("Error budget names must identify supplied candidates.")
    materialized = {name: _terms(values) for name, values in candidates.items()}
    if sum(map(len, materialized.values())) > MAX_TERMS:
        raise ValueError("Combined candidate term-count limit exceeded.")
    if sum(x.numerator.bit_length() + x.denominator.bit_length()
           for values in materialized.values() for x in values) > MAX_TOTAL_BITS:
        raise ValueError("Combined candidate input bit-size limit exceeded.")
    scores = {name: sum(values, Q(0)) for name, values in materialized.items()}
    order = tuple(sorted(scores, key=lambda name: (-scores[name] if maximize else scores[name], name)))
    distinct = sorted(set(scores.values()))
    gaps = [y - x for x, y in zip(distinct, distinct[1:])]
    tolerance = min(gaps) / 8 if gaps else Q(0)
    results = {}
    allowed = {"evaluation_error", "input_error", "model_error"}
    for name, values in materialized.items():
        budget = budgets.get(name, {})
        if set(budget) - allowed:
            raise ValueError("Unknown error category; use evaluation_error, input_error, model_error.")
        results[name] = repair_sum(values, absolute_tolerance=tolerance, initial_bits=initial_bits,
                                   max_bits=max_bits, **budget)
    winner, gap = None, None
    for name in order:
        lo, hi = results[name].final.interval
        competitors = [result.final.interval for other, result in results.items() if other != name]
        margin = min((lo - v[1] if maximize else v[0] - hi for v in competitors), default=Q(1))
        if margin > 0:
            winner, gap = name, (margin if competitors else None)
            break
    exact_tie = len(set(scores.values())) == 1 and all(
        result.final.total_error_bound == 0 for result in results.values())
    status = "certified_winner" if winner else ("exact_tie" if exact_tie else "unresolved_uncertainty")
    return DecisionReport(status, winner, maximize, order, results, gap)


def receipt() -> dict:
    """Small deterministic replay used by the combined workbench."""
    terms = [10**16, 1, -10**16]
    repaired = repair_sum(terms, absolute_tolerance=0)
    ambiguous = compare_sums(
        {"A": [101], "B": [100]},
        error_budgets={"A": {"model_error": 1}, "B": {"input_error": 1}},
    )
    near_tie = compare_sums({"A": terms, "B": [Q(3, 4)]})
    return {
        "mechanism": "cancellation guard and adaptive precision",
        "status": "implemented_exact_binary_rounding_model",
        "repair": repaired.to_dict(), "near_tie": near_tie.to_dict(),
        "uncertainty_overlap": ambiguous.to_dict(),
        "checks": {"initial_loses_unit": repaired.initial.approximation == 0,
                   "repair_recovers_unit": repaired.final.approximation == 1,
                   "separates_near_tie": near_tie.winner == "A",
                   "retains_external_uncertainty": ambiguous.winner is None},
        "limits": ["Arbitrary binary exponent range; IEEE range exceptions are not modeled.",
                   "External error budgets require independent justification.",
                   "Exact rational term replay is not an error certificate for unknown exponential inputs."],
    }
