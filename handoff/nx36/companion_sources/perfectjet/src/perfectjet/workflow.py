"""A complete target -> measurement -> population -> bounded decision adapter.

The caller supplies a finite portfolio model and linear observations of latent
values. No market data, priors, prices or forecasts are silently invented. Exact
recovery weights propagate declared observation bounds to each item. The same
completion-count object enumerates every feasible portfolio, supplies its rank,
and certifies a winner only when its lower bound exceeds every rival upper bound.
"""
from fractions import Fraction as Q
from itertools import combinations

from .decisions import certified_choice
from .exact import rank, target_recovery
from .populations import SelectionPopulation
from .readout import identify


def rational(value):
    if isinstance(value, bool):
        raise ValueError("Boolean values are not numerical inputs")
    if isinstance(value, str) and len(value) > 250:
        raise ValueError("numeric input exceeds 250 characters")
    try:
        out = Q(str(value)) if isinstance(value, float) else Q(value)
    except (TypeError, ValueError, ZeroDivisionError, OverflowError) as error:
        raise ValueError("a finite integer, decimal or rational number is required") from error
    if out.numerator.bit_length() > 4096 or out.denominator.bit_length() > 4096:
        raise ValueError("numeric input exceeds the exact arithmetic size limit")
    return out


def _rows(values, width=None):
    out = [[rational(x) for x in row] for row in values]
    if len(out) > 14 or any(not row or len(row) > 12 for row in out):
        raise ValueError("at most 14 rows and 12 columns are supported")
    n = width if width is not None else (len(out[0]) if out else 0)
    if any(len(row) != n for row in out):
        raise ValueError("matrix rows have incompatible widths")
    return out


def cheapest_sensor_repair(observation, targets, candidates=(), costs=None):
    """Minimum total cost subset; cardinality and original indices break ties."""
    width = len(targets[0])
    candidate_rows = _rows(candidates, width)
    if len(candidate_rows) > 12:
        raise ValueError("repair supports at most 12 candidate sensors")
    costs = list(costs) if costs is not None else [1] * len(candidate_rows)
    if len(costs) != len(candidate_rows) or any(
        isinstance(x, bool) or not isinstance(x, int) or x <= 0 for x in costs
    ):
        raise ValueError("one positive integer cost is required per candidate sensor")
    best = None
    checked = 0
    for size in range(len(candidate_rows) + 1):
        for chosen in combinations(range(len(candidate_rows)), size):
            cost = sum(costs[i] for i in chosen)
            if best is not None and cost > best[0]:
                continue
            checked += 1
            if target_recovery(observation + [candidate_rows[i] for i in chosen], targets)["recoverable"]:
                key = cost, size, chosen
                if best is None or key < best:
                    best = key
    return {"possible": best is not None,
            "cost": None if best is None else best[0],
            "candidate_indices": [] if best is None else list(best[2]),
            "subsets_checked": checked,
            "meaning": "The measurements must still be obtained; this is an experiment plan."}


def decision_pipeline(spec):
    """Choose among all portfolios of at most 14 original items.

    Keys: observation H, observed y, targets G (one row per item), costs,
    capacities, optional observation_errors, item_model_errors, names and repair
    candidates. Real latent state has no extra positivity/integrality constraints.
    Intervals are deterministic supplied bounds, not estimated confidence levels.
    Measurement centers must fit an exact nominal latent state; general noisy
    redundant-center interval feasibility is not solved by this adapter.
    """
    if not isinstance(spec, dict):
        raise ValueError("workflow must be an object")
    target = _rows(spec.get("targets", [[1, 0], [0, 1], [1, 2]]))
    if not target:
        raise ValueError("one target row is required per item")
    n, width = len(target), len(target[0])
    observation = _rows(spec.get("observation", [[1, 0], [0, 1]]), width)
    observed = [rational(x) for x in spec.get("observed", [12, 8])]
    if len(observed) != len(observation):
        raise ValueError("one observed value is required per measurement row")
    if rank([row + [value] for row, value in zip(observation, observed)]) != rank(observation):
        raise ValueError("measurement centers must fit one exact nominal latent state; general noisy-center interval feasibility is not supported")
    names = list(spec.get("names", [f"Option {i+1}" for i in range(n)]))
    if len(names) != n or any(not isinstance(x, str) or not x or len(x) > 100 for x in names) or len(set(names)) != n:
        raise ValueError("one distinct nonempty name is required per item")
    costs = spec.get("costs", [[2, 1], [1, 2], [2, 2]])
    capacities = spec.get("capacities", [3, 3])
    if len(costs) != n or not capacities or len(capacities) > 3:
        raise ValueError("one compatible resource row is required per item, with 1-3 resources")
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 or x > 100000 for x in capacities):
        raise ValueError("resource capacities must be integers in 0..100000")
    if any(len(row) != len(capacities) or any(isinstance(x, bool) or not isinstance(x, int) or x < 0 or x > 100000 for x in row) for row in costs):
        raise ValueError("resource costs must be compatible integers in 0..100000")
    recovery = target_recovery(observation, target)
    count_only = SelectionPopulation(costs, capacities)
    common = {"schema": "perfectjet/decision-workflow/1", "items": names,
              "feasible_count": count_only.count(), "recovery": recovery,
              "scope": "Declared finite resource model, real linear latent values and supplied deterministic error bounds. No live market or predictive superiority claim."}
    if not recovery["recoverable"]:
        common.update({"status": "needs_measurement", "settled": False,
                       "repair": cheapest_sensor_repair(observation, target, spec.get("candidates", []), spec.get("candidate_costs")),
                       "next": "Obtain a measurement that distinguishes the hidden target direction."})
        return common
    observation_errors = [rational(x) for x in spec.get("observation_errors", [0] * len(observation))]
    model_errors = [rational(x) for x in spec.get("item_model_errors", [0] * n)]
    if len(observation_errors) != len(observation) or len(model_errors) != n or any(x < 0 for x in observation_errors + model_errors):
        raise ValueError("compatible nonnegative observation and item model bounds are required")
    weights = [identify(observation, row)["weights"] for row in target]
    values = [sum((w*y for w, y in zip(row, observed)), Q(0)) for row in weights]
    radii = [sum((abs(w)*e for w, e in zip(row, observation_errors)), Q(0)) + m for row, m in zip(weights, model_errors)]
    population = SelectionPopulation(costs, capacities, values)
    bounds, bits_by_key = {}, {}
    for index in range(population.count()):
        bits = population.unrank(index)
        key = ''.join(map(str, bits))
        estimate = sum((v*b for v, b in zip(values, bits)), Q(0))
        error = sum((v*b for v, b in zip(radii, bits)), Q(0))
        bounds[key] = estimate, error
        bits_by_key[key] = bits
    verdict = certified_choice(bounds)
    exact_tie = not verdict['settled'] and all(radius == 0 for _, radius in bounds.values())
    chosen_key = verdict["choice"] if verdict["settled"] else verdict["leader"]
    chosen = bits_by_key[chosen_key]
    chosen_bounds = bounds[chosen_key]
    best_value = max(value for value, _ in bounds.values())
    exact_optima = [bits_by_key[key] for key, (value, _) in bounds.items() if value == best_value] if exact_tie else []
    common.update({"status": "settled" if verdict["settled"] else "exact_tie" if exact_tie else "needs_tighter_bounds",
                   "settled": verdict["settled"], "decision": verdict,
                   "item_values": values, "item_error_bounds": radii, "recovery_weights": weights,
                   "nominal_optimum": population.optimum(), "selected_bits": chosen,
                   "selected_names": [name for name, b in zip(names, chosen) if b],
                   "selected_rank": population.rank(chosen),
                   "selected_value": chosen_bounds[0], "selected_error_bound": chosen_bounds[1],
                   "exact_optimal_tie_count": len(exact_optima), "exact_optimal_portfolios": exact_optima[:20],
                   "portfolios": [{"bits": bits_by_key[key], "estimate": bounds[key][0], "error": bounds[key][1]} for key in sorted(bounds, key=lambda k: bounds[k][0], reverse=True)[:20]],
                   "bound_semantics": "Shared observation errors are propagated conservatively; overlapping intervals do not prove the underlying decision is impossible.",
                   "next": "The winner is separated under the supplied bounds." if verdict["settled"] else "The optimal values tie exactly. Choose an additional preference or keep every optimum." if exact_tie else "Tighten the supplied bounds for the overlapping contenders."})
    return common


def receipt():
    return {"settled": decision_pipeline({}),
            "hidden": decision_pipeline({"observation": [[1, 1]], "observed": [20],
                                         "candidates": [[1, 0], [0, 1]], "candidate_costs": [2, 1]}),
            "uncertain": decision_pipeline({"observation_errors": [5, 5]})}
