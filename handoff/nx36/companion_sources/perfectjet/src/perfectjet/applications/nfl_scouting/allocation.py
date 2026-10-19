"""Target-directed measurement packages and conditional scouting decisions.

This bridge uses PerfectJet's exact Gaussian readout and finite-population cores.
For source covariance S, frozen scouting loading H and an independent noisy
measurement e, the covariance update is

    S' = S - (S e)(S e)^T / (noise_variance + e^T S e).

Its scouting value is trace(W H(S-S')H^T), not trace(S-S') and not the sum of
isolated measurement values. Repeated observations improve precision, while
only new row-space directions can resolve structural non-identifiability.

All conclusions are conditional on the supplied linear Gaussian model, fixed
training-derived loadings and independent measurement errors. Measurement
allocation does not establish NFL prediction improvement. Scenario bounds below
are supplied fixed-fit measurement bounds; empirical uncertainty is separate.
"""
from dataclasses import dataclass
from collections.abc import Iterable
from fractions import Fraction as Q
from numbers import Integral
from itertools import combinations

from ...decisions import certified_choice
from ...exact import matmul, rank, transpose
from ...populations import SelectionPopulation
from ...readout import adds_direction, dot, identify, inverse, posterior_covariance, repair

MAX_EXACT_CANDIDATES = 18


def _q(value):
    """Preserve declared decimal inputs, rather than expose their binary expansion."""
    return Q(str(value)) if isinstance(value, float) else Q(value)


def _integer(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < int(positive):
        raise ValueError(f"{name} must be a {'positive' if positive else 'nonnegative'} integer")
    return int(value)


def _rows(values, width, name):
    out = tuple(tuple(_q(v) for v in row) for row in values)
    if any(len(row) != width for row in out):
        raise ValueError(f"{name} rows must have source width {width}")
    return out


def _covariance(values, name="prior_covariance"):
    out = tuple(tuple(_q(v) for v in row) for row in values)
    n = len(out)
    if not n or any(len(row) != n for row in out):
        raise ValueError(f"{name} must be a nonempty square matrix")
    if any(out[i][j] != out[j][i] for i in range(n) for j in range(n)):
        raise ValueError(f"{name} must be symmetric")
    # Exact LDL^T: positive pivots establish positive definiteness. The reused
    # posterior_covariance core requires an invertible Gaussian prior.
    lower = [[Q(0)] * n for _ in range(n)]
    diag = []
    for i in range(n):
        pivot = out[i][i] - sum((lower[i][k] ** 2 * diag[k] for k in range(i)), Q(0))
        if pivot <= 0:
            raise ValueError(f"{name} must be positive definite")
        diag.append(pivot)
        lower[i][i] = Q(1)
        for j in range(i + 1, n):
            lower[j][i] = (out[j][i] - sum((lower[j][k] * lower[i][k] * diag[k]
                                           for k in range(i)), Q(0))) / pivot
    return out


def _target_rows(values, width):
    rows = tuple(values)
    if not rows:
        raise ValueError("at least one target loading is required")
    if not isinstance(rows[0], Iterable) or isinstance(rows[0], (str, bytes)):
        rows = (rows,)
    return _rows(rows, width, "target_loadings")


def _trace(cov):
    return sum((cov[i][i] for i in range(len(cov))), Q(0))


def _target_covariance(cov, loadings):
    return tuple(tuple(row) for row in matmul(matmul(loadings, cov), transpose(loadings)))


def _weighted_variance(cov, weights):
    return sum((weight * cov[i][i] for i, weight in enumerate(weights)), Q(0))


@dataclass(frozen=True)
class MeasurementCandidate:
    """One optional package of independent repetitions; ``cost`` is total cost.

    ``row`` acts on the model's global source vector. For several athletes this
    vector may concatenate their states; correlated priors are permitted.
    Athlete IDs describe provenance; global rows need not have one athlete ID.
    Repetitions are independent attempts, never extra frames from one attempt.
    """
    candidate_id: str
    row: tuple
    noise_variance: Q
    cost: int
    athlete_id: object = None
    repetitions: int = 1
    attempt_ids: tuple = ()

    def __post_init__(self):
        if not isinstance(self.candidate_id, str) or not self.candidate_id:
            raise ValueError("candidate_id must be a nonempty string")
        object.__setattr__(self, "row", tuple(_q(v) for v in self.row))
        noise = _q(self.noise_variance)
        if noise <= 0:
            raise ValueError("measurement noise_variance must be positive")
        object.__setattr__(self, "noise_variance", noise)
        object.__setattr__(self, "cost", _integer(self.cost, "candidate cost"))
        object.__setattr__(self, "repetitions", _integer(self.repetitions, "repetitions", positive=True))
        ids = tuple(self.attempt_ids)
        if ids and (len(ids) != self.repetitions or len(set(ids)) != len(ids)):
            raise ValueError("attempt_ids must be distinct original attempts, one per repetition")
        object.__setattr__(self, "attempt_ids", ids)


    @property
    def rows(self):
        return (self.row,)


@dataclass(frozen=True)
class MeasurementBlockCandidate:
    """A jointly observed channel block, with correlated noise within each attempt.

    One block is one selection candidate and has one total package cost. Distinct
    channels from the same original attempt use R's covariance, not independent
    scalar repetitions. Different repeated blocks still assume independent
    attempts; their supplied original attempt IDs must be distinct.
    """
    candidate_id: str
    rows: tuple
    noise_covariance: tuple
    cost: int
    athlete_id: object = None
    repetitions: int = 1
    attempt_ids: tuple = ()

    def __post_init__(self):
        if not isinstance(self.candidate_id, str) or not self.candidate_id:
            raise ValueError("candidate_id must be a nonempty string")
        rows = tuple(tuple(_q(v) for v in row) for row in self.rows)
        if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
            raise ValueError("measurement block rows must be a nonempty rectangular matrix")
        noise = _covariance(self.noise_covariance, "noise_covariance")
        if len(noise) != len(rows):
            raise ValueError("noise covariance dimension must match the jointly measured channels")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "noise_covariance", noise)
        object.__setattr__(self, "cost", _integer(self.cost, "candidate cost"))
        object.__setattr__(self, "repetitions", _integer(self.repetitions, "repetitions", positive=True))
        ids = tuple(self.attempt_ids)
        if ids and (len(ids) != self.repetitions or len(set(ids)) != len(ids)):
            raise ValueError("attempt_ids must be distinct original attempts, one per repeated block")
        object.__setattr__(self, "attempt_ids", ids)


class TargetInformationModel:
    """Exact conditional information for frozen, training-derived target loadings.

    Inputs are copied to immutable tuples. ``noise_variance`` for the existing
    design is either one common variance or one variance per row. The training
    receipt is provenance supplied by the caller; this class neither learns H
    from evaluated athletes nor verifies the caller's training chronology.
    """
    def __init__(self, prior_covariance, target_loadings, design=(), noise_variance=1,
                 target_weights=None, training_receipt=None, target_ids=None, observation_ids=None):
        self.prior_covariance = _covariance(prior_covariance)
        self.width = len(self.prior_covariance)
        self.target_loadings = _target_rows(target_loadings, self.width)
        self.design = _rows(design, self.width, "design")
        self.observation_ids = tuple(observation_ids) if observation_ids is not None else ()
        if self.observation_ids and (len(self.observation_ids) != len(self.design)
                                     or len(set(self.observation_ids)) != len(self.observation_ids)):
            raise ValueError("observation_ids must be distinct original attempts, one per design row")
        if isinstance(noise_variance, Iterable) and not isinstance(noise_variance, (str, bytes)):
            noises = tuple(_q(v) for v in noise_variance)
            if len(noises) != len(self.design):
                raise ValueError("one observation variance per existing design row is required")
        else:
            noises = (_q(noise_variance),) * len(self.design)
            if _q(noise_variance) <= 0:
                raise ValueError("observation noise_variance must be positive")
        if any(noise <= 0 for noise in noises):
            raise ValueError("observation variances must be positive")
        self.observation_noise_variances = noises
        self.target_weights = (tuple(_q(v) for v in target_weights)
                               if target_weights is not None else (Q(1),) * len(self.target_loadings))
        if len(self.target_weights) != len(self.target_loadings) or any(v < 0 for v in self.target_weights):
            raise ValueError("one nonnegative weight per target is required")
        self.target_ids = tuple(target_ids) if target_ids is not None else None
        if self.target_ids is not None:
            if len(self.target_ids) != len(self.target_loadings) or len(set(self.target_ids)) != len(self.target_ids):
                raise ValueError("target_ids must be unique and match the target rows")
        self.training_receipt = str(training_receipt) if training_receipt is not None else None
        if len(set(noises)) <= 1:
            # Reuse the readout core directly for its homogeneous-noise domain.
            cov = tuple(tuple(row) for row in posterior_covariance(
                self.design, noises[0] if noises else Q(1), self.prior_covariance))
        else:
            cov = self.prior_covariance
            for row, noise in zip(self.design, noises):
                cov = self._update(cov, row, noise)
        self.source_covariance = cov
        self.target_covariance = _target_covariance(cov, self.target_loadings)
        self.target_variance = _weighted_variance(self.target_covariance, self.target_weights)

    @staticmethod
    def _update(cov, row, noise):
        # Rational Sherman--Morrison: heterogeneous noise requires no irrational
        # whitening and full source correlations are preserved.
        projected = tuple(dot(source_row, row) for source_row in cov)
        denominator = noise + dot(row, projected)
        return tuple(tuple(value - projected[i] * projected[j] / denominator
                           for j, value in enumerate(source_row))
                     for i, source_row in enumerate(cov))

    def _candidates(self, candidates):
        candidates = tuple(candidates)
        if any(not isinstance(candidate, (MeasurementCandidate, MeasurementBlockCandidate))
               for candidate in candidates):
            raise TypeError("scalar or block measurement candidate instances are required")
        if len({candidate.candidate_id for candidate in candidates}) != len(candidates):
            raise ValueError("candidate_id values must be unique")
        if any(len(row) != self.width for candidate in candidates for row in candidate.rows):
            raise ValueError("candidate row width differs from the source width")
        ids = [attempt for candidate in candidates for attempt in candidate.attempt_ids]
        if len(set(ids)) != len(ids) or set(ids).intersection(self.observation_ids):
            raise ValueError("an original attempt cannot supply two independent observations")
        return candidates

    @staticmethod
    def _update_block(cov, rows, noise_covariance):
        # S' = S - S E^T (R + E S E^T)^(-1) E S. Correlated channels
        # remain one observation block; rational arithmetic needs no whitening.
        left = matmul(cov, transpose(rows))
        projected = matmul(rows, left)
        innovation = [[noise + value for noise, value in zip(r_noise, r_value)]
                      for r_noise, r_value in zip(noise_covariance, projected)]
        reduction = matmul(matmul(left, inverse(innovation)), transpose(left))
        return tuple(tuple(value - delta for value, delta in zip(source_row, delta_row))
                     for source_row, delta_row in zip(cov, reduction))

    def _apply(self, cov, candidate):
        for _ in range(candidate.repetitions):
            if isinstance(candidate, MeasurementBlockCandidate):
                cov = self._update_block(cov, candidate.rows, candidate.noise_covariance)
            else:
                cov = self._update(cov, candidate.row, candidate.noise_variance)
        return cov

    def _package_repair(self, h, candidates):
        if identify(self.design, h)["identified"]:
            return {"needed": 0, "candidate_indices": (), "smaller_sets_rejected": 0}
        rejected = 0
        for size in range(1, min(self.width, len(candidates)) + 1):
            for idx in combinations(range(len(candidates)), size):
                design = list(self.design) + [row for i in idx for row in candidates[i].rows]
                if identify(design, h)["identified"]:
                    return {"needed": size, "candidate_indices": idx,
                            "smaller_sets_rejected": rejected}
                rejected += 1
        return {"needed": None, "candidate_indices": None, "smaller_sets_rejected": rejected}

    def _objective(self, cov, objective):
        after = _target_covariance(cov, self.target_loadings)
        reductions = tuple(self.target_covariance[i][i] - after[i][i]
                           for i in range(len(after)))
        if objective == "worst_target":
            return min(reductions)
        weight = sum(self.target_weights, Q(0))
        return (sum((w * value for w, value in zip(self.target_weights, reductions)), Q(0)) / weight
                if weight else Q(0))

    def package_information(self, candidates):
        """Joint information, structural identification and repeat/new-direction receipts."""
        candidates = self._candidates(candidates)
        cov = self.source_covariance
        design = list(self.design)
        details = []
        for candidate in candidates:
            new = (adds_direction(design, candidate.row)
                   if isinstance(candidate, MeasurementCandidate)
                   else rank(design + list(candidate.rows), self.width) > rank(design, self.width))
            details.append({"candidate_id": candidate.candidate_id,
                            "athlete_id": candidate.athlete_id,
                            "repetitions": candidate.repetitions,
                            "attempt_ids": candidate.attempt_ids,
                            "independence_provenance": "distinct supplied original attempt IDs"
                                if candidate.attempt_ids else "planned independent-observation assumption",
                            "channels": len(candidate.rows),
                            "repeat_of_observed_row": all(row in self.design for row in candidate.rows),
                            "new_design_direction": new,
                            "classification": "new_direction" if new else "precision_only"})
            cov = self._apply(cov, candidate)
            for _ in range(candidate.repetitions):
                design.extend(candidate.rows)
        after = _target_covariance(cov, self.target_loadings)
        after_variance = _weighted_variance(after, self.target_weights)
        candidate_rows = [row for candidate in candidates for row in candidate.rows]
        readouts = [{"target": i,
                     "before": identify(self.design, h),
                     "after": identify(design, h),
                     "repair_from_this_package": self._package_repair(h, candidates),
                     "row_repair": repair(self.design, h, candidate_rows,
                                          max_new=min(self.width, len(candidate_rows)))}
                    for i, h in enumerate(self.target_loadings)]
        return {"candidate_ids": tuple(candidate.candidate_id for candidate in candidates),
                "cost": sum(candidate.cost for candidate in candidates),
                "source_covariance_before": self.source_covariance,
                "source_covariance_after": cov,
                "source_variance_before": _trace(self.source_covariance),
                "source_variance_after": _trace(cov),
                "source_variance_reduction": _trace(self.source_covariance) - _trace(cov),
                "target_covariance_before": self.target_covariance,
                "target_covariance_after": after,
                "target_variance_before": self.target_variance,
                "target_variance_after": after_variance,
                "target_variance_reduction": self.target_variance - after_variance,
                "target_variance_scope": "H source_covariance H^T; excludes irreducible NFL noise "
                                         "and uncertainty in the frozen transfer loading",
                "marginal_target_reductions": tuple(self.target_covariance[i][i] - after[i][i]
                                                    for i in range(len(after))),
                "design_rank_before": rank(self.design, self.width),
                "design_rank_after": rank(design, self.width),
                "readouts": readouts, "measurements": details,
                "training_receipt": self.training_receipt,
                "assumptions": ("fixed training-derived target loadings",
                                "supplied linear Gaussian source and transfer model",
                                "independent measurement errors, including repetitions",
                                "conditional information; no asserted NFL prediction lift")}

    def optimize_package(self, candidates, budget, max_candidates=MAX_EXACT_CANDIDATES,
                         objective="weighted_mean"):

        """Globally maximize joint target variance reduction over a small exact population.

        The objective is nonlinear in selected measurements. SelectionPopulation
        supplies feasible counting, conditional counts and original-order ranks;
        its additive-profit optimizer is deliberately not used. Every feasible
        subset is evaluated. There is no claim of 100-candidate scalability.
        weighted_mean normalizes the supplied nonnegative output weights;
        worst_target maximizes the minimum reduction across every supplied H
        row. Worst-case rows must represent commensurate declared training
        loading scenarios; they are not automatically a confidence region.
        """
        candidates = self._candidates(candidates)
        if objective not in ("weighted_mean", "worst_target"):
            raise ValueError("objective must be weighted_mean or worst_target")
        budget = _integer(budget, "budget")
        limit = _integer(max_candidates, "max_candidates")
        if limit > MAX_EXACT_CANDIDATES or len(candidates) > limit:
            raise ValueError(f"exact allocation supports at most {MAX_EXACT_CANDIDATES} candidates "
                             "and must respect max_candidates")
        population = SelectionPopulation([(candidate.cost,) for candidate in candidates], (budget,))
        total = population.count()
        best = None
        tie_ranks = []
        best_bits = None
        best_cost = None
        ordinal = 0

        def visit(prefix, cov, spent):
            nonlocal best, best_bits, best_cost, ordinal
            if population.conditional_count(prefix) == 0:
                return
            if len(prefix) == len(candidates):
                gain = self._objective(cov, objective)
                if best is None or gain > best:
                    best, best_bits, best_cost = gain, prefix, spent
                    tie_ranks[:] = [ordinal]
                elif gain == best:
                    tie_ranks.append(ordinal)
                    # Minimum cost breaks representation ties; all objective
                    # ties, including supersets with no useful information, count.
                    if spent < best_cost:
                        best_bits, best_cost = prefix, spent
                ordinal += 1
                return
            candidate = candidates[len(prefix)]
            visit(prefix + (0,), cov, spent)
            if spent + candidate.cost <= budget:
                visit(prefix + (1,), self._apply(cov, candidate), spent + candidate.cost)

        visit((), self.source_covariance, 0)
        if ordinal != total:
            raise AssertionError("finite-population traversal did not cover the feasible population")
        chosen = tuple(candidate for candidate, bit in zip(candidates, best_bits) if bit)
        selected_rank = population.rank(best_bits)
        if population.unrank(selected_rank) != best_bits:
            raise AssertionError("selection rank replay failed")
        return {"candidate_ids": tuple(candidate.candidate_id for candidate in chosen),
                "bits": best_bits, "cost": best_cost, "budget": budget,
                "objective_reduction": best, "objective": objective,
                "objective_scope": "conditional reduction across supplied frozen training loading rows; "
                                   "worst_target rows are declared scenarios, not a confidence region",
                "tie_count": len(tie_ranks),
                "tie_ranks": tuple(tie_ranks), "population_rank": selected_rank,
                "feasible_count": total, "evaluated_packages": ordinal,
                "optimality": "exhaustive over the declared finite candidate population",
                "package": self.package_information(chosen)}


def _bounds(values, name):
    out = {}
    for key, endpoints in values.items():
        if len(endpoints) != 2:
            raise ValueError(f"{name} needs (lower, upper) pairs")
        lo, hi = map(_q, endpoints)
        if lo > hi:
            raise ValueError(f"{name} lower bound exceeds upper bound")
        out[key] = (lo, hi)
    return out


def scouting_decision(scenario_bounds, empirical_uncertainty=None, maximize=True):
    """Replay ranking implications of supplied fixed-fit scenario bounds exactly.

    Bounds must cover the caller's declared measurement scenarios. No confidence
    level or probability follows from these bounds. Empirical intervals are
    stored separately and never silently merged with deterministic bounds.
    """
    bounds = _bounds(scenario_bounds, "scenario_bounds")
    if not bounds:
        raise ValueError("at least one player's scenario bounds are required")
    estimate_error = {key: ((lo + hi) / 2, (hi - lo) / 2)
                      for key, (lo, hi) in bounds.items()}
    decision = certified_choice(estimate_error, maximize=maximize)
    empirical = _bounds(empirical_uncertainty or {}, "empirical_uncertainty")
    if any(key not in bounds for key in empirical):
        raise ValueError("empirical uncertainty refers to a player without scenario bounds")
    comparisons = []
    contenders = decision["contenders"] if not decision["settled"] else []
    for i, left in enumerate(contenders):
        for right in contenders[i + 1:]:
            difference = (bounds[left][0] - bounds[right][1],
                          bounds[left][1] - bounds[right][0])
            if difference[0] <= 0 <= difference[1]:
                comparisons.append({"players": (left, right), "difference_bounds": difference})
    return {**decision, "scenario_bounds": bounds,
            "empirical_uncertainty": empirical, "unresolved_comparisons": comparisons,
            "guarantee_scope": "supplied fixed-fit measurement scenario bounds only",
            "statistical_confidence_claim": None}


def allocate_contenders(model, candidates, budget, scenario_bounds,
                        empirical_uncertainty=None, maximize=True,
                        max_candidates=MAX_EXACT_CANDIDATES, objective="weighted_mean"):
    """Target unresolved leader differences while respecting the global information model.

    ``model.target_ids`` links one frozen loading row to each athlete. The
    optimized target rows are H_a-H_b for unresolved contender pairs. All supplied
    measurement candidates remain available while comparisons are unresolved:
    an outsider can help through correlated source states or unlock another
    measurement despite zero standalone value. Athlete IDs cannot justify
    exclusion from a global correlated model. Once the declared scenario decision
    is settled, no further measurement is selected for that decision.
    """
    if model.target_ids is None:
        raise ValueError("target_ids linking frozen target rows to athletes are required")
    candidates = model._candidates(candidates)
    decision = scouting_decision(scenario_bounds, empirical_uncertainty, maximize)
    index = {athlete: i for i, athlete in enumerate(model.target_ids)}
    if any(athlete not in index for athlete in decision["scenario_bounds"]):
        raise ValueError("a scenario-bound athlete has no target loading")
    pairs = [comparison["players"] for comparison in decision["unresolved_comparisons"]]
    included = candidates if pairs else ()
    excluded = (() if pairs else tuple(
        {"candidate_id": candidate.candidate_id,
         "reason": "all_leader_comparisons_settled_within_declared_scenario_bounds"}
        for candidate in candidates))
    loadings = [tuple(a - b for a, b in zip(model.target_loadings[index[left]],
                                          model.target_loadings[index[right]]))
                for left, right in pairs]
    if not loadings:
        loadings = [(Q(0),) * model.width]
    comparison_model = TargetInformationModel(
        model.prior_covariance, loadings, design=model.design,
        noise_variance=model.observation_noise_variances,
        target_weights=[Q(1, len(loadings))] * len(loadings),
        training_receipt=model.training_receipt,
        observation_ids=model.observation_ids)
    allocation = comparison_model.optimize_package(included, budget, max_candidates, objective)
    return {"decision": decision, "allocation": allocation,
            "excluded_candidates": excluded, "comparison_pairs": tuple(pairs),
            "candidate_scope": "all supplied measurements retained while comparisons are unresolved; "
                               "global correlations and joint complementarity can make outsiders useful",
            "objective": objective + " conditional variance reduction of unresolved prediction differences",
            "settlement_after_measurement": "requires observed results and recomputed valid scenario bounds"}


def allocation_receipt():
    """Exact small witness: a zero-isolated-value measurement unlocks a joint package."""
    model = TargetInformationModel([[1, 0], [0, 1]], [1, 0],
                                   training_receipt="synthetic fixed loading; not NFL evidence")
    candidates = (MeasurementCandidate("direct", (1, 0), 1, 1),
                  MeasurementCandidate("mixed", (1, 1), Q(1, 10), 1),
                  MeasurementCandidate("nuisance", (0, 1), Q(1, 10), 1))
    isolated = {candidate.candidate_id: model.package_information([candidate])["target_variance_reduction"]
                for candidate in candidates}
    greedy = model.package_information(candidates[:2])
    optimum = model.optimize_package(candidates, 2)
    return {"isolated_reductions": isolated,
            "greedy_selected": ("direct", "mixed"),
            "greedy_joint_reduction": greedy["target_variance_reduction"],
            "optimal_selected": optimum["candidate_ids"],
            "optimal_joint_reduction": optimum["objective_reduction"],
            "feasible_packages": optimum["feasible_count"],
            "interpretation": "the nuisance observation has zero isolated scouting value, "
                              "but unlocks the mixed observation; isolated gains are not additive",
            "evidence_scope": "exact declared Gaussian example, not a football result"}
