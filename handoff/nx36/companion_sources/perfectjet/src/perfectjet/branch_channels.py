"""Exact outcome partitions and explicitly modelled bounded retry schedules.

This is a probability model, not a device calibration.  Attempts are independent
and identically distributed, a repeat outcome is heralded, and every other
outcome terminates the schedule.  Silent accepts are failures.  Exhaustion has
its own explicit failure probability, so rejected work need not be silently
treated as an accepted error.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Iterable


def _fraction(value: Fraction | int | str, name: str) -> Fraction:
    if isinstance(value, (float, bool)):
        raise TypeError(f"{name} must be an exact Fraction, integer, or string")
    try:
        return Fraction(value)
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"invalid {name}") from exc


def _probability(value: Fraction | int | str, name: str) -> Fraction:
    result = _fraction(value, name)
    if not 0 <= result <= 1:
        raise ValueError(f"{name} must lie in [0, 1]")
    return result


def _cost(value: Fraction | int | str, name: str) -> Fraction:
    result = _fraction(value, name)
    if result < 0:
        raise ValueError(f"{name} must be nonnegative")
    return result


class OutcomeKind(str, Enum):
    EXACT = "exact"
    FRAME = "frame"
    REPEAT = "repeat"
    SILENT = "silent"


@dataclass(frozen=True)
class Branch:
    """A mutually exclusive outcome; ``cost`` is paid on this outcome.

    A frame branch denotes a successfully correctable outcome.  The optional
    correction label records the caller's correction; this module does not
    assert that a physical operator implements that correction.
    """

    name: str
    kind: OutcomeKind | str
    probability: Fraction | int | str
    cost: Fraction | int | str = 0
    correction: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("branch names must be nonempty strings")
        object.__setattr__(self, "kind", OutcomeKind(self.kind))
        object.__setattr__(self, "probability", _probability(self.probability, "probability"))
        object.__setattr__(self, "cost", _cost(self.cost, "branch cost"))
        if self.correction is not None and self.kind is not OutcomeKind.FRAME:
            raise ValueError("only frame outcomes may carry a correction label")


@dataclass(frozen=True)
class BranchPartition:
    """A complete, disjoint list of named outcome events."""

    branches: tuple[Branch, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "branches", tuple(self.branches))
        if not self.branches or any(not isinstance(b, Branch) for b in self.branches):
            raise ValueError("a partition needs at least one Branch")
        if len({b.name for b in self.branches}) != len(self.branches):
            raise ValueError("branch event names must be distinct")
        if sum((b.probability for b in self.branches), Fraction()) != 1:
            raise ValueError("branch probabilities must sum exactly to 1")

    def probability(self, kind: OutcomeKind | str) -> Fraction:
        kind = OutcomeKind(kind)
        return sum((b.probability for b in self.branches if b.kind is kind), Fraction())

    def receipt(self) -> dict:
        return {
            "probability_total": "1",
            "channels": {kind.value: str(self.probability(kind)) for kind in OutcomeKind},
            "branches": [
                {"name": b.name, "kind": b.kind.value, "probability": str(b.probability),
                 "cost": str(b.cost), "correction": b.correction}
                for b in self.branches
            ],
        }


@dataclass(frozen=True)
class RetryResult:
    max_attempts: int
    exact_probability: Fraction
    frame_probability: Fraction
    silent_probability: Fraction
    exhausted_probability: Fraction
    effective_failure: Fraction
    expected_attempts: Fraction
    expected_cost: Fraction
    silent_floor: Fraction

    @property
    def accepted_probability(self) -> Fraction:
        return self.exact_probability + self.frame_probability + self.silent_probability

    @property
    def silent_given_acceptance(self) -> Fraction | None:
        return self.silent_probability / self.accepted_probability if self.accepted_probability else None

    def receipt(self) -> dict:
        result = {key: (value if isinstance(value, int) else str(value))
                  for key, value in self.__dict__.items()}
        result["accepted_probability"] = str(self.accepted_probability)
        conditional = self.silent_given_acceptance
        result["silent_given_acceptance"] = None if conditional is None else str(conditional)
        return result


@dataclass(frozen=True)
class RetryModel:
    partition: BranchPartition
    attempt_cost: Fraction | int | str = 1
    exhaustion_failure: Fraction | int | str = 1
    exhaustion_cost: Fraction | int | str = 0

    def __post_init__(self) -> None:
        if not isinstance(self.partition, BranchPartition):
            raise TypeError("partition must be a BranchPartition")
        object.__setattr__(self, "attempt_cost", _cost(self.attempt_cost, "attempt cost"))
        object.__setattr__(self, "exhaustion_failure", _probability(self.exhaustion_failure, "exhaustion failure"))
        object.__setattr__(self, "exhaustion_cost", _cost(self.exhaustion_cost, "exhaustion cost"))

    @property
    def silent_floor(self) -> Fraction:
        """Limit of unconditional silent-accept probability as depth grows.

        If every attempt repeats there can never be a silent acceptance, so
        this is zero even though exhaustion may still be a failure.
        """
        repeat = self.partition.probability(OutcomeKind.REPEAT)
        return self.partition.probability(OutcomeKind.SILENT) / (1 - repeat) if repeat < 1 else Fraction()

    @property
    def asymptotic_failure(self) -> Fraction:
        return self.silent_floor if self.partition.probability(OutcomeKind.REPEAT) < 1 else self.exhaustion_failure

    def evaluate(self, max_attempts: int) -> RetryResult:
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer")
        repeat = self.partition.probability(OutcomeKind.REPEAT)
        exhausted = repeat ** max_attempts
        visits = Fraction(max_attempts) if repeat == 1 else (1 - exhausted) / (1 - repeat)
        exact = self.partition.probability(OutcomeKind.EXACT) * visits
        frame = self.partition.probability(OutcomeKind.FRAME) * visits
        silent = self.partition.probability(OutcomeKind.SILENT) * visits
        one_attempt_cost = self.attempt_cost + sum(
            (branch.probability * branch.cost for branch in self.partition.branches), Fraction())
        return RetryResult(
            max_attempts, exact, frame, silent, exhausted,
            silent + self.exhaustion_failure * exhausted,
            visits, one_attempt_cost * visits + self.exhaustion_cost * exhausted,
            self.silent_floor,
        )

    def optimize(self, max_attempts: int, failure_threshold: Fraction | int | str,
                 risk_price: Fraction | int | str = 0,
                 allowed_depths: Iterable[int] | None = None) -> "ScheduleResult":
        """Minimize cost + risk_price*failure, subject to failure < threshold.

        Exhaustively searches the supplied finite depth set. Ties go to the
        shallower schedule. An infeasible result is returned explicitly.
        """
        self.evaluate(max_attempts)  # validate before constructing the search
        threshold = _probability(failure_threshold, "failure threshold")
        price = _cost(risk_price, "risk price")
        depths = tuple(range(1, max_attempts + 1) if allowed_depths is None else allowed_depths)
        if not depths:
            raise ValueError("allowed_depths must not be empty")
        for depth in depths:
            if isinstance(depth, bool) or not isinstance(depth, int) or not 1 <= depth <= max_attempts:
                raise ValueError("allowed depths must be integers between 1 and max_attempts")
        evaluations = [self.evaluate(depth) for depth in sorted(set(depths))]
        feasible = [r for r in evaluations if r.effective_failure < threshold]
        best = min(feasible, key=lambda r: (r.expected_cost + price * r.effective_failure, r.max_attempts), default=None)
        reason = "feasible optimum in enumerated depth set" if best else "no feasible depth in enumerated depth set"
        # The floor obstructs every finite depth only when failure approaches
        # it from above.  If exhaustion is harmless, deeper repetition can
        # instead increase unconditional silent errors toward the floor.
        repeat = self.partition.probability(OutcomeKind.REPEAT)
        floor_blocks = repeat < 1 and self.exhaustion_failure >= self.silent_floor >= threshold
        if best is None and floor_blocks:
            reason = "silent acceptance floor blocks every finite depth under this exhaustion model"
        return ScheduleResult(best, tuple(evaluations), threshold, price, reason)


@dataclass(frozen=True)
class ScheduleResult:
    best: RetryResult | None
    evaluated: tuple[RetryResult, ...]
    failure_threshold: Fraction
    risk_price: Fraction
    reason: str

    def receipt(self) -> dict:
        return {"best": self.best.receipt() if self.best else None,
                "evaluated": [r.receipt() for r in self.evaluated],
                "failure_threshold": str(self.failure_threshold),
                "risk_price": str(self.risk_price), "reason": self.reason}


def receipt() -> dict:
    model = RetryModel(BranchPartition((
        Branch("exact", "exact", "3/5"),
        Branch("tracked correction", "frame", "1/5", cost="1/10", correction="recorded frame"),
        Branch("heralded retry", "repeat", "19/100"),
        Branch("unnoticed error", "silent", "1/100"),
    )))
    return {"mechanism": "exact branch conservation and constrained retry scheduling",
            "status": "explicit illustrative probability model; no hardware calibration",
            "assumptions": ["independent identical attempts", "repeat is observed",
                            "frame outcomes are successfully corrected as supplied",
                            "silent outcomes terminate as failures"],
            "partition": model.partition.receipt(),
            "silent_floor": str(model.silent_floor),
            "schedule": model.optimize(8, "1/20").receipt(),
            "floor_rejection": model.optimize(8, "1/100").receipt()}
