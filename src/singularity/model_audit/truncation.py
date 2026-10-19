"""Shape-observable truncation families and exact, replayable multicover.

For N real input tokens and a cap t>=1, a non-fabricating observer returning
one teacher-forced entry per retained token returns min(N,t) entries. Thus
N>t is a value-independent separator. It is NOT a theorem for a last-token
or generation-only API, nor for a service that fabricates missing entries.
Thresholds in each interval between distinct lengths have identical columns.
All columns are nested: the largest declared cap is the hardest. Keeping the
intervals makes the quantifier explicit and exposes insufficient pools.
"""
from __future__ import annotations

import hashlib
import json

from ..robust_coverage import (coverage_problem, minimum_robust_panel,
                              greedy_robust_panel, panel_coverage)

SCHEMA = "singularity.truncation-multicover/3"
OBSERVABILITY = "one teacher-forced argmax entry per retained real input token; no fabrication"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def positive(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(name + " must be a positive integer")
    return value


def threshold_intervals(lengths, maximum):
    """Partition ALL integer caps 1..maximum, without testing output values."""
    positive(maximum, "maximum")
    for length in lengths:
        positive(length, "length")
    starts = sorted({1, maximum + 1, *(n for n in lengths if 1 < n <= maximum)})
    return [{"first": a, "last": b - 1, "separates": [n > a for n in lengths]}
            for a, b in zip(starts, starts[1:])]


def specification(probes, construction, maximum, requirement=2):
    """No unobservable construction column is silently discarded.

    construction is a fault->boolean-list table derived only from construction
    observations. Held-out observations are deliberately absent from this API.
    tokens counts REAL input tokens, never padding or generated tokens.
    """
    positive(requirement, "requirement")
    if not probes or len({p["id"] for p in probes}) != len(probes):
        raise ValueError("need distinct probe ids")
    for p in probes:
        positive(p["tokens"], "tokens")
        if type(p["cost"]) is not int or p["cost"] < p["tokens"]:
            raise ValueError("cost must be an integer at least the real input length")
    if any(not isinstance(k, str) or not k for k in construction):
        raise ValueError("construction fault names must be nonempty strings")
    if any(len(v) != len(probes) or any(type(b) is not bool for b in v) for v in construction.values()):
        raise ValueError("construction columns must be aligned boolean lists")
    intervals = threshold_intervals([p["tokens"] for p in probes], maximum)
    columns = {"construction/" + name: list(col) for name, col in sorted(construction.items())}
    columns.update({f"shape/caps_{s['first']}_{s['last']}": s["separates"] for s in intervals})
    return {"probes": [{k: p[k] for k in ("id", "tokens", "cost")} for p in probes],
            "construction": construction, "maximum_cap": maximum, "requirement": requirement,
            "observability": OBSERVABILITY, "columns": columns, "intervals": intervals}


def _problem(spec):
    labels = list(spec["columns"])
    return coverage_problem([p["cost"] for p in spec["probes"]],
                            [[spec["columns"][k][e] for k in labels] for e in range(len(spec["probes"]))],
                            [p["id"] for p in spec["probes"]], labels)


def independent_optimum(costs, columns, requirement, allowed=None, max_probes=22, required=()):
    """Independent all-subsets oracle using integer masks; no optimizer calls.

    Returns an optimal cost and subset. Work-limit failure is never reported
    as infeasibility. Restricted enumeration proves optimal greedy pruning.
    """
    choices = list(range(len(costs))) if allowed is None else sorted(allowed)
    if len(choices) > max_probes:
        raise ValueError("independent enumeration budget exceeded")
    if not set(required) <= set(choices):
        raise ValueError("required probes outside allowed pool")
    required_mask = sum(1 << choices.index(e) for e in set(required))
    masks = [sum(1 << j for j, e in enumerate(choices) if col[e]) for col in columns.values()]
    if any(m.bit_count() < requirement for m in masks):
        return None, None
    best, winner = None, None
    subtotal = [0] * (1 << len(choices))
    for mask in range(1 << len(choices)):
        if mask:
            bit = mask & -mask
            subtotal[mask] = subtotal[mask ^ bit] + costs[choices[bit.bit_length() - 1]]
        if mask & required_mask != required_mask:
            continue
        if best is not None and subtotal[mask] >= best:
            continue
        if all((mask & c).bit_count() >= requirement for c in masks):
            best, winner = subtotal[mask], mask
    return best, None if winner is None else [choices[j] for j in range(len(choices)) if winner >> j & 1]


def compare(spec, representative_ids=()):
    """Matched comparators, including a feasible representative completion."""
    problem, req = _problem(spec), spec["requirement"]
    exact = minimum_robust_panel(problem, req)
    deficient = {k: sum(v) for k, v in spec["columns"].items() if sum(v) < req}
    if not exact.feasible:
        return {"feasible": False, "deficient": deficient, "panels": {}}
    greedy = greedy_robust_panel(problem, req)
    costs = [p["cost"] for p in spec["probes"]]
    oracle, _ = independent_optimum(costs, spec["columns"], req)
    if oracle != exact.cost:
        raise ArithmeticError("independent optimum differs")
    pruned_cost, pruned = independent_optimum(costs, spec["columns"], req, greedy.panel)
    indices = {p["id"]: e for e, p in enumerate(spec["probes"])}
    if len(set(representative_ids)) != len(representative_ids):
        raise ValueError("representative ids must be distinct")
    panels = {"exact": list(exact.panel), "greedy": list(greedy.panel), "pruned_greedy": pruned,
              "representative": [indices[k] for k in representative_ids]}
    # Also report the cheapest completion of the representative panel, so a
    # deficient baseline is not presented as a cheaper valid alternative.
    _, completed = independent_optimum(costs, spec["columns"], req, required=panels["representative"])
    panels["representative_completed"] = completed
    rows = {}
    for name, panel in panels.items():
        coverage = dict(zip(spec["columns"], panel_coverage(problem, panel)))
        rows[name] = {"indices": panel, "probe_ids": [spec["probes"][e]["id"] for e in panel],
                      "cost": sum(costs[e] for e in panel), "coverage": coverage,
                      "satisfies_requirement": all(n >= req for n in coverage.values())}
    return {"feasible": True, "deficient": {}, "independent_minimum_cost": oracle,
            "pruned_greedy_independent_minimum_cost": pruned_cost, "panels": rows}


def certificate(spec, comparison, provenance=None):
    cert = {"schema": SCHEMA, "specification": spec, "comparison": comparison,
            "provenance": provenance or {},
            "claim_boundary": "Conditional shape theorem plus recorded construction coverage; no semantic equivalence or GPU transfer claim."}
    cert["sha256"] = digest(cert)
    return cert


def verify_certificate(cert):
    """Rebuild columns, recount witnesses, and exhaust all cheaper subsets.

    Digest protects identity, not truth of observations. A source replay must
    additionally recompute the construction table from bound raw evidence.
    """
    try:
        if cert["schema"] != SCHEMA or cert["sha256"] != digest({k: v for k, v in cert.items() if k != "sha256"}):
            return False
        spec, comparison = cert["specification"], cert["comparison"]
        rebuilt = specification(spec["probes"], spec["construction"], spec["maximum_cap"], spec["requirement"])
        if rebuilt != spec:
            return False
        costs, cols, req = [p["cost"] for p in spec["probes"]], spec["columns"], spec["requirement"]
        optimum, _ = independent_optimum(costs, cols, req)
        if comparison["feasible"] != (optimum is not None):
            return False
        deficient = {k: sum(v) for k, v in cols.items() if sum(v) < req}
        if comparison["deficient"] != deficient:
            return False
        if optimum is None:
            return comparison["panels"] == {}
        if comparison["independent_minimum_cost"] != optimum:
            return False
        for name, row in comparison["panels"].items():
            panel = row["indices"]
            if len(set(panel)) != len(panel) or any(type(e) is not int or not 0 <= e < len(costs) for e in panel):
                return False
            coverage = {k: sum(col[e] for e in panel) for k, col in cols.items()}
            feasible = all(n >= req for n in coverage.values())
            if row["cost"] != sum(costs[e] for e in panel) or row["coverage"] != coverage or row["satisfies_requirement"] != feasible:
                return False
            if row["probe_ids"] != [spec["probes"][e]["id"] for e in panel]:
                return False
            if name != "representative" and not feasible:
                return False
        if set(comparison["panels"]) != {"exact", "greedy", "pruned_greedy", "representative", "representative_completed"}:
            return False
        if comparison["panels"]["exact"]["cost"] != optimum:
            return False
        # Rebuild ordinary greedy too; optimal pruning is constrained to its output.
        greedy = greedy_robust_panel(_problem(spec), req)
        if comparison["panels"]["greedy"]["indices"] != list(greedy.panel):
            return False
        if not set(comparison["panels"]["pruned_greedy"]["indices"]) <= set(greedy.panel):
            return False
        pruned, _ = independent_optimum(costs, cols, req, greedy.panel)
        completed, _ = independent_optimum(costs, cols, req, required=comparison["panels"]["representative"]["indices"])
        if not set(comparison["panels"]["representative"]["indices"]) <= set(comparison["panels"]["representative_completed"]["indices"]):
            return False
        return (comparison["panels"]["representative_completed"]["cost"] == completed and
                comparison["panels"]["pruned_greedy"]["cost"] == pruned == comparison["pruned_greedy_independent_minimum_cost"])
    except (KeyError, TypeError, ValueError, IndexError, OverflowError):
        return False
