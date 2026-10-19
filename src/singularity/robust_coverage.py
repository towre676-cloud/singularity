"""Minimum-cost panels that survive missing observations (multicover).

A finite *coverage problem* has probes e = 0..m-1 with exact nonnegative
costs c(e) and declared distinctions p = 0..k-1 (for example "healthy versus
fault p").  ``separates[e][p]`` records whether probe e alone separates
distinction p under a declared, already frozen rule.  A panel P is
*r-robust* when every distinction is separated by at least r members of P.

Erasure lemma.  Let f = r - 1.  P still separates every distinction after any
f of its probes are lost if and only if P is r-robust.  If some distinction p
has at most f separating members, erasing exactly those members leaves p
unseparated; conversely, erasing f members of an r-robust panel leaves at
least one separator of each distinction.  ``survives_erasures`` checks the
statement directly by enumerating erasures, without counting coverage.

Minimum-cost r-robust selection is weighted set multicover, NP-hard in
general.  ``minimum_robust_panel`` is exact branch and bound with an explicit
node budget.  It branches on the deficient distinction with least slack; the
i-th branch includes that distinction's i-th admissible separator and
excludes earlier ones, so branches partition every completion.  The lower
bound sums the d cheapest admissible separators of each deficient
distinction (d its deficit) over a family whose admissible separator sets are
pairwise disjoint; probes counted for different members of that family are
distinct, so the sum never exceeds the remaining optimum.  The bound for one
distinction is the special case of a one-member family.

``exhaustive_robust_panel`` is an independent reference: it scans every
subset and recounts coverage from ``separates`` without the branch-and-bound
data structures.  ``greedy_robust_panel`` is a heuristic.  ``fixed_panel``
and ``random_panels`` are comparators evaluated under the same requirement.
Exceeding a work budget raises ValueError; it is not an infeasibility result.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
import random

__all__ = [
    "CoverageProblem", "RobustResult", "coverage_problem", "panel_coverage",
    "is_robust", "erasure_tolerance", "survives_erasures", "minimum_robust_panel",
    "exhaustive_robust_panel", "greedy_robust_panel", "fixed_panel", "random_panels",
    "robust_witness", "check_robust_witness",
]


def _int(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, not {type(value).__name__}")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _cost(value):
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError("probe costs must be int or Fraction")
    value = Fraction(value)
    if value < 0:
        raise ValueError("probe costs must be nonnegative")
    return value


@dataclass(frozen=True)
class CoverageProblem:
    """``coverers[p]`` is the frozenset of probes separating distinction p."""

    costs: tuple[Fraction, ...]
    coverers: tuple[frozenset, ...]
    probe_labels: tuple[str, ...]
    distinction_labels: tuple[str, ...]

    @property
    def probes(self):
        return len(self.costs)

    @property
    def distinctions(self):
        return len(self.coverers)


def coverage_problem(costs, separates, probe_labels=None, distinction_labels=None):
    """Build a problem from costs and a probe-by-distinction boolean table."""
    costs = tuple(_cost(c) for c in costs)
    rows = tuple(tuple(row) for row in separates)
    if not costs or len(rows) != len(costs):
        raise ValueError("need one separation row per probe and at least one probe")
    width = len(rows[0])
    if width < 1 or any(len(row) != width for row in rows):
        raise ValueError("separation rows must have equal positive length")
    if any(not isinstance(v, bool) for row in rows for v in row):
        raise TypeError("separation entries must be bool")
    probe_labels = tuple(probe_labels) if probe_labels is not None else tuple(f"probe-{e}" for e in range(len(costs)))
    distinction_labels = (tuple(distinction_labels) if distinction_labels is not None
                          else tuple(f"distinction-{p}" for p in range(width)))
    if len(probe_labels) != len(costs) or len(distinction_labels) != width:
        raise ValueError("label counts must match the table")
    if len(set(probe_labels)) != len(probe_labels) or len(set(distinction_labels)) != width:
        raise ValueError("labels must be unique")
    coverers = tuple(frozenset(e for e in range(len(costs)) if rows[e][p]) for p in range(width))
    return CoverageProblem(costs, coverers, probe_labels, distinction_labels)


def _panel(problem, panel):
    panel = tuple(panel)
    for e in panel:
        _int(e, "probe index")
        if e >= problem.probes:
            raise ValueError("probe index outside the pool")
    if len(set(panel)) != len(panel):
        raise ValueError("panel repeats a probe")
    return tuple(sorted(panel))


def panel_coverage(problem, panel):
    """Number of panel members separating each distinction."""
    chosen = set(_panel(problem, panel))
    return tuple(len(chosen & cover) for cover in problem.coverers)


def is_robust(problem, panel, requirement):
    _int(requirement, "requirement", 1)
    return min(panel_coverage(problem, panel)) >= requirement


def erasure_tolerance(problem, panel):
    """Largest f such that every f-erasure leaves all distinctions separated;
    -1 when the panel does not separate every distinction at all."""
    return min(panel_coverage(problem, panel)) - 1


def survives_erasures(problem, panel, erasures, max_subsets=10**6):
    """Direct check of the erasure lemma: enumerate every erased subset."""
    panel = _panel(problem, panel)
    _int(erasures, "erasures")
    sizes = [len(list(combinations(range(len(panel)), j))) for j in range(min(erasures, len(panel)) + 1)]
    if sum(sizes) > max_subsets:
        raise ValueError("erasure enumeration exceeds max_subsets")
    for j in range(min(erasures, len(panel)) + 1):
        for lost in combinations(panel, j):
            remaining = set(panel) - set(lost)
            for cover in problem.coverers:
                if not remaining & cover:
                    return False
    return True


@dataclass(frozen=True)
class RobustResult:
    feasible: bool
    panel: tuple[int, ...] | None
    cost: Fraction | None
    nodes: int
    deficient: tuple[int, ...] = ()
    root_lower_bound: Fraction | None = None


def _deficient(problem, requirement):
    return tuple(p for p, cover in enumerate(problem.coverers) if len(cover) < requirement)


def _cost_of(problem, panel):
    return sum((problem.costs[e] for e in panel), Fraction(0))


def greedy_robust_panel(problem, requirement):
    """Repeatedly add the probe minimizing cost per unit of remaining deficit
    it reduces.  HEURISTIC ONLY."""
    _int(requirement, "requirement", 1)
    bad = _deficient(problem, requirement)
    if bad:
        return RobustResult(False, None, None, 0, bad)
    need = [requirement] * problem.distinctions
    chosen, steps = [], 0
    while any(need):
        steps += 1
        best = None
        for e in range(problem.probes):
            if e in chosen:
                continue
            gain = sum(1 for p, cover in enumerate(problem.coverers) if need[p] and e in cover)
            if gain and (best is None or problem.costs[e] * best[1] < problem.costs[best[0]] * gain):
                best = (e, gain)
        chosen.append(best[0])
        for p, cover in enumerate(problem.coverers):
            if need[p] and best[0] in cover:
                need[p] -= 1
    panel = tuple(sorted(chosen))
    return RobustResult(True, panel, _cost_of(problem, panel), steps)


def minimum_robust_panel(problem, requirement, *, max_nodes=10**6):
    """Exact minimum-cost r-robust panel (see module docstring)."""
    _int(requirement, "requirement", 1)
    _int(max_nodes, "max_nodes", 1)
    bad = _deficient(problem, requirement)
    if bad:
        return RobustResult(False, None, None, 0, bad)
    costs = problem.costs
    order = {p: sorted(cover, key=lambda e: (costs[e], e)) for p, cover in enumerate(problem.coverers)}
    greedy = greedy_robust_panel(problem, requirement)
    state = {"cost": greedy.cost, "panel": greedy.panel, "nodes": 0}

    def bound(need, allowed):
        terms = []
        for p, d in enumerate(need):
            if not d:
                continue
            options = [e for e in order[p] if e in allowed]
            if len(options) < d:
                return None
            terms.append((sum((costs[e] for e in options[:d]), Fraction(0)), p, frozenset(options)))
        total, used = Fraction(0), set()
        for value, _, options in sorted(terms, key=lambda t: (-t[0], t[1])):
            if not options & used:
                total += value
                used |= options
        return total

    everyone = frozenset(range(problem.probes))
    root = bound([requirement] * problem.distinctions, everyone)

    def search(need, allowed, picked, cost):
        state["nodes"] += 1
        if state["nodes"] > max_nodes:
            raise ValueError("robust coverage node budget exceeded")
        if not any(need):
            if cost < state["cost"]:
                state["cost"], state["panel"] = cost, tuple(sorted(picked))
            return
        lb = bound(need, allowed)
        if lb is None or cost + lb >= state["cost"]:
            return
        target, options = None, None
        for p, d in enumerate(need):
            if d:
                available = [e for e in order[p] if e in allowed]
                if options is None or len(available) - d < len(options) - need[target]:
                    target, options = p, available
        for e in options:
            next_need = [d - 1 if d and e in problem.coverers[p] else d for p, d in enumerate(need)]
            picked.append(e)
            search(next_need, allowed - {e}, picked, cost + costs[e])
            picked.pop()
            allowed = allowed - {e}

    search([requirement] * problem.distinctions, everyone, [], Fraction(0))
    return RobustResult(True, state["panel"], state["cost"], state["nodes"], (), root)


def exhaustive_robust_panel(problem, requirement, max_subsets=2**16):
    """Reference oracle over all 2**m subsets; ties keep the first subset in
    increasing bitmask order."""
    _int(requirement, "requirement", 1)
    _int(max_subsets, "max_subsets", 1)
    if 2 ** problem.probes > max_subsets:
        raise ValueError("exhaustive robust search exceeds max_subsets")
    best = None
    for mask in range(2 ** problem.probes):
        members = [e for e in range(problem.probes) if mask >> e & 1]
        ok = True
        for cover in problem.coverers:
            if sum(1 for e in members if e in cover) < requirement:
                ok = False
                break
        if ok:
            cost = sum((problem.costs[e] for e in members), Fraction(0))
            if best is None or cost < best[0]:
                best = (cost, tuple(members))
    if best is None:
        return RobustResult(False, None, None, 2 ** problem.probes, _deficient(problem, requirement))
    return RobustResult(True, best[1], best[0], 2 ** problem.probes)


def fixed_panel(problem, panel, requirement):
    """Evaluate a declared panel under the same robustness requirement."""
    panel = _panel(problem, panel)
    coverage = panel_coverage(problem, panel)
    return {"panel": list(panel), "cost": _cost_of(problem, panel),
            "satisfies_requirement": min(coverage) >= requirement,
            "distinctions_meeting_requirement": sum(c >= requirement for c in coverage),
            "distinctions_detected": sum(c >= 1 for c in coverage),
            "erasure_tolerance": min(coverage) - 1}


def random_panels(problem, size, draws, requirement, seed):
    """Seeded uniform panels of a fixed cardinality, evaluated identically."""
    _int(size, "size", 0)
    _int(draws, "draws", 1)
    if size > problem.probes:
        raise ValueError("random panel larger than the pool")
    rng = random.Random(seed)
    return [fixed_panel(problem, rng.sample(range(problem.probes), size), requirement) for _ in range(draws)]


def robust_witness(problem, panel, requirement):
    """For each distinction, the first ``requirement`` separating panel members."""
    panel = _panel(problem, panel)
    witness = []
    for p, cover in enumerate(problem.coverers):
        members = [e for e in panel if e in cover][:requirement]
        if len(members) < requirement:
            raise ValueError(f"panel does not meet the requirement for {problem.distinction_labels[p]}")
        witness.append({"distinction": problem.distinction_labels[p],
                        "separating_probes": [problem.probe_labels[e] for e in members]})
    return witness


def check_robust_witness(witness, panel_labels, requirement, distinctions, separates):
    """Independent check: every declared distinction appears exactly once with
    ``requirement`` distinct panel probes, and ``separates(probe_label,
    distinction_label)`` (a caller predicate recomputing separation from raw
    readings) holds for each."""
    panel_labels = set(panel_labels)
    seen = set()
    for row in witness:
        probes = row["separating_probes"]
        if row["distinction"] in seen or len(set(probes)) < requirement:
            return False
        seen.add(row["distinction"])
        if not set(probes) <= panel_labels:
            return False
        if not all(separates(probe, row["distinction"]) for probe in probes):
            return False
    return seen == set(distinctions)
