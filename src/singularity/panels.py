"""Shared experiment panels for finite candidate collections (unit OE08).

A *pool* is a finite list of experiments e, each with an exact cost
c(e) >= 0 and an exact reading r_e(v_c) for every candidate c of a
finite family v_1, ..., v_k (k >= 2).  For an operator system the
experiment (j, w) reads r_e(v) = L_j M_w v (word w chronological, as in
``observability``).  A *panel* is a set of pool members; its cost is the
sum of member costs.

Three separation criteria are kept apart.

* **Exact**: e separates {a, b} iff r_e(v_a) != r_e(v_b).
* **Box (l-infinity) noise**: y_e = r_e(v_t) + eta_e with |eta_e| <= eps_e.
  e robustly separates {a, b} iff |r_e(v_a) - r_e(v_b)| > 2 eps_e.  The
  consistency decoder returns every c with |y_e - r_e(v_c)| <= eps_e on
  the whole panel.
* **Ball (l2) noise**: the panel's noise vector has Euclidean norm <= eps.
  The panel separates {a, b} iff the squared Euclidean distance of the two
  reading vectors exceeds 4 eps^2.  This is a property of the panel as a
  whole, not of single members, and is not a set-cover problem.

Minimum-cost exact and box-robust panels are weighted set cover over
candidate pairs, solved by exact branch and bound.  Weighted set cover is
NP-hard in general; the method is worst-case exponential and carries a
node budget.  ``greedy_panel`` is a heuristic only.  Proofs are in
``docs/research/PANELS.md``.

Exception contract: bool, float and str raise TypeError; wrong values or
shapes raise ValueError, as does an exceeded work budget.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from .observability import (OperatorSystem, experiment,
                            minimum_distinguishing_experiment, observable_closure)

__all__ = [
    "PanelPool", "PanelResult", "reading_pool", "experiment_pool", "explicit_pool",
    "candidate_pairs", "coverage_masks", "minimum_cost_panel", "exhaustive_minimum_panel",
    "greedy_panel", "panel_cost", "separates_all", "consistent_candidates",
    "certifies_identification", "ambiguous_reading", "l2_separates", "l2_certifies",
    "l2_consistent_candidates", "l2_ambiguous_reading", "minimum_cost_l2_panel",
    "pairwise_cheapest_witnesses",
]


# ------------------------------------------------------------------ inputs
def _q(value, name="value") -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(f"{name} must be an int or Fraction, not {type(value).__name__}")
    return Fraction(value)


def _int(value, name, minimum=0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, not {type(value).__name__}")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _sequence(value, name):
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must be a sequence, not a string")
    if isinstance(value, (bool, int, float, Fraction)):
        raise TypeError(f"{name} must be a sequence, not {type(value).__name__}")
    try:
        return tuple(value)
    except TypeError:
        raise TypeError(f"{name} must be a sequence") from None


@dataclass(frozen=True)
class PanelPool:
    """A finite experiment pool: ``readings[e][c]`` is r_e(v_c)."""

    costs: tuple[Fraction, ...]
    readings: tuple[tuple[Fraction, ...], ...]
    labels: tuple
    candidates: int

    @property
    def size(self) -> int:
        return len(self.costs)


def reading_pool(costs, readings, labels=None, candidates=None) -> PanelPool:
    """Validate an abstract pool.  ``candidates`` is needed only when the
    pool is empty; otherwise it is the common length of the reading rows."""
    costs = tuple(_q(c, "cost") for c in _sequence(costs, "costs"))
    rows = tuple(tuple(_q(x, "reading") for x in _sequence(r, "reading row"))
                 for r in _sequence(readings, "readings"))
    if any(c < 0 for c in costs):
        raise ValueError("experiment costs must be nonnegative")
    if len(rows) != len(costs):
        raise ValueError("one reading row per experiment is required")
    if candidates is not None:
        k = _int(candidates, "candidates", 2)
    elif rows:
        k = len(rows[0])
    else:
        raise ValueError("an empty pool needs an explicit candidate count")
    if k < 2 or any(len(r) != k for r in rows):
        raise ValueError("reading rows must all have one entry per candidate, k >= 2")
    if labels is None:
        labels = tuple(range(len(costs)))
    else:
        labels = _sequence(labels, "labels")
        if len(labels) != len(costs):
            raise ValueError("one label per experiment is required")
    return PanelPool(costs, rows, labels, k)


def _states(system: OperatorSystem, states):
    if not isinstance(system, OperatorSystem):
        raise TypeError("system must be an OperatorSystem")
    result = []
    for s in _sequence(states, "states"):
        row = tuple(_q(x, "state entry") for x in _sequence(s, "state"))
        if len(row) != system.dimension:
            raise ValueError("state has the wrong dimension")
        result.append(row)
    if len(result) < 2:
        raise ValueError("a candidate family needs at least two states")
    return tuple(result)


def _dot(a, b):
    return sum((x * y for x, y in zip(a, b)), Fraction(0))


def _pool_from(system, states, experiments):
    return reading_pool([e.cost for e in experiments],
                        [[_dot(e.row, v) for v in states] for e in experiments],
                        [(e.observation, e.word) for e in experiments])


def experiment_pool(system: OperatorSystem, states, max_cost, max_experiments: int = 4096) -> PanelPool:
    """All experiments (j, w) with gamma_j + c(w) <= max_cost.

    The set is finite because attachment costs are positive.  Order: by
    cost, then word length, word, observation.  More than
    ``max_experiments`` members raises ValueError (a budget refusal)."""
    states = _states(system, states)
    budget = _q(max_cost, "max_cost")
    if budget < 0:
        raise ValueError("max_cost must be nonnegative")
    _int(max_experiments, "max_experiments", 1)
    if not system.observations:
        return reading_pool((), (), (), candidates=len(states))
    slack = budget - min(system.observation_costs)
    words, stack = [], [((), Fraction(0))]
    while stack:
        word, cost = stack.pop()
        words.append((word, cost))
        if len(words) > max_experiments:
            raise ValueError("experiment pool exceeds max_experiments")
        for i, c in enumerate(system.attachment_costs):
            if cost + c <= slack:
                stack.append((word + (i,), cost + c))
    keys = []
    for word, cost in words:
        for j, gamma in enumerate(system.observation_costs):
            if gamma + cost <= budget:
                keys.append((gamma + cost, len(word), word, j))
    if len(keys) > max_experiments:
        raise ValueError("experiment pool exceeds max_experiments")
    keys.sort()
    return _pool_from(system, states, [experiment(system, j, w) for _, _, w, j in keys])


def explicit_pool(system: OperatorSystem, states, experiments) -> PanelPool:
    """A pool from an explicit list of (observation, word) pairs."""
    states = _states(system, states)
    chosen = []
    for item in _sequence(experiments, "experiments"):
        pair = _sequence(item, "experiment")
        if len(pair) != 2:
            raise ValueError("an experiment is an (observation, word) pair")
        chosen.append(experiment(system, pair[0], _sequence(pair[1], "word")))
    return _pool_from(system, states, chosen)


# ------------------------------------------------------------- coverage
def candidate_pairs(k: int):
    return tuple((a, b) for a in range(k) for b in range(a + 1, k))


def _margins(pool: PanelPool, epsilon):
    """None gives exact separation (margin 0).  Otherwise a positive
    rational, or one positive rational per pool experiment."""
    if epsilon is None:
        return (Fraction(0),) * pool.size
    if isinstance(epsilon, (bool, int, float, Fraction, str, bytes)):
        e = _q(epsilon, "epsilon")
        if e <= 0:
            raise ValueError("epsilon must be positive")
        return (e,) * pool.size
    values = tuple(_q(x, "epsilon") for x in _sequence(epsilon, "epsilon"))
    if len(values) != pool.size:
        raise ValueError("one epsilon per pool experiment is required")
    if any(x <= 0 for x in values):
        raise ValueError("epsilon must be positive")
    return values


def coverage_masks(pool: PanelPool, epsilon=None):
    """Bit p of mask e is set iff e separates pair p (exactly, or robustly)."""
    margins = _margins(pool, epsilon)
    pairs = candidate_pairs(pool.candidates)
    masks = []
    for r, m in zip(pool.readings, margins):
        mask = 0
        for p, (a, b) in enumerate(pairs):
            if abs(r[a] - r[b]) > 2 * m:
                mask |= 1 << p
        masks.append(mask)
    return tuple(masks)


def _panel(pool, panel):
    result = tuple(sorted(set(_int(i, "panel index") for i in _sequence(panel, "panel"))))
    if any(i >= pool.size for i in result):
        raise ValueError("panel index outside the pool")
    return result


def panel_cost(pool: PanelPool, panel) -> Fraction:
    return sum((pool.costs[i] for i in _panel(pool, panel)), Fraction(0))


def separates_all(pool: PanelPool, panel, epsilon=None) -> bool:
    masks = coverage_masks(pool, epsilon)
    covered = 0
    for i in _panel(pool, panel):
        covered |= masks[i]
    return covered == (1 << len(candidate_pairs(pool.candidates))) - 1


@dataclass(frozen=True)
class PanelResult:
    """``panel`` lists pool indices.  If ``feasible`` is False, ``panel`` is
    None and ``uncoverable`` names every pair no pool member separates."""

    feasible: bool
    panel: tuple[int, ...] | None
    cost: Fraction | None
    nodes: int
    uncoverable: tuple[tuple[int, int], ...]
    root_lower_bound: Fraction | None = None


def _uncoverable(pool, masks):
    union = 0
    for m in masks:
        union |= m
    return tuple(pair for p, pair in enumerate(candidate_pairs(pool.candidates))
                 if not union >> p & 1)


def _undominated(costs, masks):
    """Indices kept after removing empty and dominated experiments.

    f dominates e iff mask_f contains mask_e, c_f <= c_e, and the pair is
    strictly ordered by (mask strictly larger) or (cost smaller) or (equal
    mask and cost, smaller index).  This is a strict partial order; every
    removed experiment is dominated by a kept one (PANELS.md, Lemma 2)."""
    n = len(costs)
    kept = []
    for e in range(n):
        if not masks[e]:
            continue
        dominated = False
        for f in range(n):
            if f == e or masks[f] & masks[e] != masks[e] or costs[f] > costs[e]:
                continue
            if masks[f] != masks[e] or costs[f] < costs[e] or f < e:
                dominated = True
                break
        if not dominated:
            kept.append(e)
    return kept


def greedy_panel(pool: PanelPool, epsilon=None) -> PanelResult:
    """Greedy cost-effectiveness heuristic: repeatedly add the experiment
    minimizing cost / (newly separated pairs).  HEURISTIC ONLY; the result
    is a valid panel when feasible but need not be optimal."""
    masks = coverage_masks(pool, epsilon)
    bad = _uncoverable(pool, masks)
    if bad:
        return PanelResult(False, None, None, 0, bad)
    full = (1 << len(candidate_pairs(pool.candidates))) - 1
    covered, chosen, steps = 0, [], 0
    while covered != full:
        steps += 1
        best = None
        for e, m in enumerate(masks):
            new = bin(m & ~covered).count("1")
            if not new:
                continue
            if best is None or pool.costs[e] * best[1] < pool.costs[best[0]] * new:
                best = (e, new)
        chosen.append(best[0])
        covered |= masks[best[0]]
    panel = tuple(sorted(chosen))
    return PanelResult(True, panel, panel_cost(pool, panel), steps, ())


def minimum_cost_panel(pool: PanelPool, epsilon=None, *, packing: bool = True,
                       reduce: bool = True, max_nodes: int = 10**6) -> PanelResult:
    """Exact minimum-cost separating panel by branch and bound.

    epsilon=None: exact separation.  Otherwise box-robust separation with
    the declared positive margins.  Branches on an uncovered pair with the
    fewest admissible covering experiments; the i-th branch includes the
    i-th coverer and excludes the earlier ones, so the branches partition
    the covers.  Lower bound: the independent-pair packing bound
    (PANELS.md, Lemma 1), which dominates the max-cheapest-witness bound;
    with packing=False only the latter is used.  Worst-case exponential:
    more than ``max_nodes`` explored nodes raises ValueError."""
    masks = coverage_masks(pool, epsilon)
    _int(max_nodes, "max_nodes", 1)
    if not isinstance(packing, bool) or not isinstance(reduce, bool):
        raise TypeError("packing and reduce must be bool")
    bad = _uncoverable(pool, masks)
    if bad:
        return PanelResult(False, None, None, 0, bad)
    npairs = len(candidate_pairs(pool.candidates))
    full = (1 << npairs) - 1
    index = _undominated(pool.costs, masks) if reduce else [e for e in range(pool.size) if masks[e]]
    costs = [pool.costs[e] for e in index]
    cmasks = [masks[e] for e in index]
    coverers = [sorted((e for e in range(len(index)) if cmasks[e] >> p & 1),
                       key=lambda e: (costs[e], e)) for p in range(npairs)]

    def bound(uncovered, allowed):
        cheap = {}
        for p in range(npairs):
            if uncovered >> p & 1:
                e = next((e for e in coverers[p] if allowed >> e & 1), None)
                if e is None:
                    return None
                cheap[p] = costs[e]
        if not packing:
            return max(cheap.values())
        total, packed = Fraction(0), 0
        for p in sorted(cheap, key=lambda p: (-cheap[p], p)):
            reach = 0
            for e in coverers[p]:
                if allowed >> e & 1:
                    reach |= cmasks[e]
            if not reach & packed:
                packed |= 1 << p
                total += cheap[p]
        return total

    # Initial incumbent: the greedy cover restricted to kept experiments.
    covered, chosen = 0, []
    while covered != full:
        best = None
        for e, m in enumerate(cmasks):
            new = bin(m & ~covered).count("1")
            if new and (best is None or costs[e] * best[1] < costs[best[0]] * new):
                best = (e, new)
        chosen.append(best[0])
        covered |= cmasks[best[0]]
    state = {"cost": sum((costs[e] for e in chosen), Fraction(0)), "panel": list(chosen), "nodes": 0}
    everyone = (1 << len(index)) - 1
    root = bound(full, everyone)

    def search(uncovered, allowed, picked, cost):
        state["nodes"] += 1
        if state["nodes"] > max_nodes:
            raise ValueError("branch-and-bound node budget exceeded")
        if not uncovered:
            if cost < state["cost"]:
                state["cost"], state["panel"] = cost, list(picked)
            return
        lb = bound(uncovered, allowed)
        if lb is None or cost + lb >= state["cost"]:
            return
        best_p, options = None, None
        for p in range(npairs):
            if uncovered >> p & 1:
                opts = [e for e in coverers[p] if allowed >> e & 1]
                if options is None or len(opts) < len(options):
                    best_p, options = p, opts
        for e in options:
            picked.append(e)
            search(uncovered & ~cmasks[e], allowed & ~(1 << e), picked, cost + costs[e])
            picked.pop()
            allowed &= ~(1 << e)

    search(full, everyone, [], Fraction(0))
    panel = tuple(sorted(index[e] for e in state["panel"]))
    return PanelResult(True, panel, state["cost"], state["nodes"], (), root)


def exhaustive_minimum_panel(pool: PanelPool, epsilon=None, max_subsets: int = 2**16) -> PanelResult:
    """Reference oracle: scan every subset of the pool.  Separation is
    recomputed from the readings; no coverage masks are reused."""
    margins = _margins(pool, epsilon)
    _int(max_subsets, "max_subsets", 1)
    if 2 ** pool.size > max_subsets:
        raise ValueError("exhaustive panel search exceeds max_subsets")
    pairs = candidate_pairs(pool.candidates)

    def sep(e, a, b):
        return abs(pool.readings[e][a] - pool.readings[e][b]) > 2 * margins[e]

    bad = tuple((a, b) for a, b in pairs if not any(sep(e, a, b) for e in range(pool.size)))
    if bad:
        return PanelResult(False, None, None, 2 ** pool.size, bad)
    best = None
    for subset in range(2 ** pool.size):
        members = [e for e in range(pool.size) if subset >> e & 1]
        if all(any(sep(e, a, b) for e in members) for a, b in pairs):
            cost = sum((pool.costs[e] for e in members), Fraction(0))
            if best is None or cost < best[0]:
                best = (cost, tuple(members))
    return PanelResult(True, best[1], best[0], 2 ** pool.size, ())


# ------------------------------------------------- box-noise decoding
def consistent_candidates(pool: PanelPool, panel, observed, epsilon):
    """Candidates c with |y_e - r_e(v_c)| <= eps_e for every e in the panel.
    ``observed`` is aligned with the sorted panel indices."""
    margins = _margins(pool, epsilon)
    if epsilon is None:
        raise ValueError("the decoder needs a declared positive epsilon")
    panel = _panel(pool, panel)
    y = tuple(_q(v, "observed reading") for v in _sequence(observed, "observed"))
    if len(y) != len(panel):
        raise ValueError("one observed reading per panel member is required")
    return tuple(c for c in range(pool.candidates)
                 if all(abs(ye - pool.readings[e][c]) <= margins[e] for e, ye in zip(panel, y)))


def certifies_identification(pool: PanelPool, panel, epsilon) -> bool:
    """True iff every pair is robustly separated by some panel member;
    by PANELS.md Theorem 3 this is equivalent to unique decoding for every
    true candidate and every admissible box noise."""
    if epsilon is None:
        raise ValueError("certification needs a declared positive epsilon")
    return separates_all(pool, panel, epsilon)


def ambiguous_reading(pool: PanelPool, panel, epsilon):
    """If the panel does not certify, return (a, b, y) with y admissible for
    truth a and consistent with both a and b (the midpoint readings).
    Otherwise None."""
    if epsilon is None:
        raise ValueError("ambiguity needs a declared positive epsilon")
    margins = _margins(pool, epsilon)
    panel = _panel(pool, panel)
    for a, b in candidate_pairs(pool.candidates):
        if all(abs(pool.readings[e][a] - pool.readings[e][b]) <= 2 * margins[e] for e in panel):
            return a, b, tuple((pool.readings[e][a] + pool.readings[e][b]) / 2 for e in panel)
    return None


# ------------------------------------------------- ball-noise decoding
def _radius(radius):
    r = _q(radius, "radius")
    if r <= 0:
        raise ValueError("radius must be positive")
    return r


def _sq(pool, panel, a, b):
    return sum(((pool.readings[e][a] - pool.readings[e][b]) ** 2 for e in panel), Fraction(0))


def l2_separates(pool: PanelPool, panel, radius, pair) -> bool:
    """Ball model: ||r(v_a) - r(v_b)||_2^2 > 4 radius^2 over the panel."""
    r, panel = _radius(radius), _panel(pool, panel)
    pair = _sequence(pair, "pair")
    if len(pair) != 2:
        raise ValueError("a pair has two candidates")
    a, b = (_int(x, "candidate") for x in pair)
    if a >= pool.candidates or b >= pool.candidates or a == b:
        raise ValueError("pair must name two distinct candidates")
    return _sq(pool, panel, a, b) > 4 * r * r


def l2_certifies(pool: PanelPool, panel, radius) -> bool:
    r, panel = _radius(radius), _panel(pool, panel)
    return all(_sq(pool, panel, a, b) > 4 * r * r for a, b in candidate_pairs(pool.candidates))


def l2_consistent_candidates(pool: PanelPool, panel, observed, radius):
    """Candidates c with ||y - r(v_c)||_2^2 <= radius^2 over the panel."""
    r, panel = _radius(radius), _panel(pool, panel)
    y = tuple(_q(v, "observed reading") for v in _sequence(observed, "observed"))
    if len(y) != len(panel):
        raise ValueError("one observed reading per panel member is required")
    return tuple(c for c in range(pool.candidates)
                 if sum(((ye - pool.readings[e][c]) ** 2 for e, ye in zip(panel, y)),
                        Fraction(0)) <= r * r)


def l2_ambiguous_reading(pool: PanelPool, panel, radius):
    r, panel = _radius(radius), _panel(pool, panel)
    for a, b in candidate_pairs(pool.candidates):
        if _sq(pool, panel, a, b) <= 4 * r * r:
            return a, b, tuple((pool.readings[e][a] + pool.readings[e][b]) / 2 for e in panel)
    return None


def minimum_cost_l2_panel(pool: PanelPool, radius, max_subsets: int = 2**16) -> PanelResult:
    """Exhaustive minimum-cost panel under the ball model (not set cover:
    separation is a property of the whole panel).  Bounded by max_subsets."""
    r = _radius(radius)
    _int(max_subsets, "max_subsets", 1)
    if 2 ** pool.size > max_subsets:
        raise ValueError("exhaustive l2 panel search exceeds max_subsets")
    pairs = candidate_pairs(pool.candidates)
    everything = tuple(range(pool.size))
    bad = tuple(p for p in pairs if _sq(pool, everything, *p) <= 4 * r * r)
    if bad:
        return PanelResult(False, None, None, 2 ** pool.size, bad)
    best = None
    for subset in range(2 ** pool.size):
        members = tuple(e for e in range(pool.size) if subset >> e & 1)
        if all(_sq(pool, members, a, b) > 4 * r * r for a, b in pairs):
            cost = sum((pool.costs[e] for e in members), Fraction(0))
            if best is None or cost < best[0]:
                best = (cost, members)
    return PanelResult(True, best[1], best[0], 2 ** pool.size, ())


# ----------------------------------------------- closure cross-check
def pairwise_cheapest_witnesses(system: OperatorSystem, states, max_cost, certificate=None):
    """Per pair, SNG-O03's globally cheapest witness for v_a - v_b.

    Returns tuples (a, b, status, cost, (observation, word)) where status
    is 'within_budget' (cost <= max_cost: the cheapest pool coverer of a
    complete cost-<=C pool costs exactly this), 'beyond_budget' (separable,
    but not by any experiment of cost <= max_cost) or 'future_equivalent'
    (no experiment of any cost separates the pair)."""
    states = _states(system, states)
    budget = _q(max_cost, "max_cost")
    cert = observable_closure(system) if certificate is None else certificate
    out = []
    for a, b in candidate_pairs(len(states)):
        d = tuple(x - y for x, y in zip(states[a], states[b]))
        e = minimum_distinguishing_experiment(system, d, cert)
        if e is None:
            out.append((a, b, "future_equivalent", None, None))
        else:
            status = "within_budget" if e.cost <= budget else "beyond_budget"
            out.append((a, b, status, e.cost, (e.observation, e.word)))
    return tuple(out)
