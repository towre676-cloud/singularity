"""Candidate-specific closed-box uncertainty for finite experiment panels (NX01).

The common-envelope panel contract of :mod:`singularity.panels` gives every
candidate the same radius ``eps_e`` in experiment ``e``.  The thermal compiler
:func:`singularity.thermal_diagnostics.protocol_pool` already computes a
sharper radius ``rho[e][c]`` for every experiment and candidate, then takes
``eps_e = max_c rho[e][c]`` deliberately.  This module keeps the individual
radii.

Semantics.  Experiment ``e`` run on candidate ``c`` yields one reading in the
closed interval ``I_ec = [r_ec - rho_ec, r_ec + rho_ec]``; every point of the
interval is possible.  Experiments are independently reset, so a panel ``P``
admits the product box ``Y_c(P) = prod_{e in P} I_ec`` (product uncertainty
contract).  Two boxes are disjoint iff some coordinate separates strictly:

    Y_a(P) and Y_b(P) disjoint  <=>  exists e in P with
    Delta_eab = |r_ea - r_eb| - rho_ea - rho_eb > 0.

Equality leaves a shared endpoint and is *not* separation.  Zero radii are
allowed directly, including mixtures of zero and positive entries.  Only the
unordered pairs with different target labels must be separated; original
candidate identities are never merged, even when readings coincide.

Minimum-cost panel selection is weighted set cover on the required pairs.
:func:`minimum_candidate_box_panel` is an exact branch and bound with an
explicit node budget; an exhausted budget returns status ``inconclusive``
with an incumbent upper bound and a proved lower bound, never
``infeasible``.  Independent oracles live in
:mod:`singularity.candidate_box_oracles` and do not use these masks.  Proofs
are in ``docs/research/CANDIDATE_BOXES.md``.

Exception contract: bool, float and str raise TypeError where a number is
required; wrong values or shapes raise ValueError.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .panels import PanelPool, reading_pool

__all__ = [
    "SCHEMA", "CandidateBoxPool", "CandidateBoxAmbiguity", "CandidateBoxPanelResult",
    "box_pool", "from_diagnostic_pool", "common_envelope", "interval",
    "separation_margin", "required_pairs", "candidate_box_masks", "uncoverable_pairs",
    "candidate_box_separates", "candidate_box_consistent", "candidate_box_targets",
    "candidate_box_ambiguity", "minimum_candidate_box_panel", "panel_cost",
    "rational_json", "candidate_box_receipt",
]

SCHEMA = "singularity.candidate-box-panel/1"


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


def _label(value, name):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise TypeError(f"{name} must be a str or int, not {type(value).__name__}")
    if isinstance(value, str) and not value:
        raise ValueError(f"{name} must be a nonempty string")
    return value


@dataclass(frozen=True)
class CandidateBoxPool:
    """A validated finite pool with an experiment-by-candidate radius matrix.

    ``pool.readings[e][c]`` is the exact central reading and ``radii[e][c]``
    the nonnegative closed-interval radius of candidate ``c`` in experiment
    ``e`` (rows are experiments, columns candidates; the transpose is a
    different contract).  ``candidate_ids`` name original candidates and must
    be distinct.  ``target_labels[c]`` is the target of candidate ``c``;
    by default every candidate is its own target."""

    pool: PanelPool
    radii: tuple
    target_labels: tuple | None = None
    candidate_ids: tuple | None = None

    def __post_init__(self):
        if not isinstance(self.pool, PanelPool):
            raise TypeError("pool must be a PanelPool")
        # Revalidate: a PanelPool can be constructed directly without checks.
        pool = reading_pool(self.pool.costs, self.pool.readings, self.pool.labels,
                            candidates=self.pool.candidates)
        k = pool.candidates
        rows = _sequence(self.radii, "radii")
        if len(rows) != pool.size:
            raise ValueError("one radius row per experiment is required")
        radii = []
        for row in rows:
            row = tuple(_q(x, "radius") for x in _sequence(row, "radius row"))
            if len(row) != k:
                raise ValueError("each radius row needs one entry per candidate")
            if any(x < 0 for x in row):
                raise ValueError("radii must be nonnegative")
            radii.append(row)
        if self.candidate_ids is None:
            ids = tuple(f"c{c}" for c in range(k))
        else:
            ids = tuple(_label(x, "candidate id") for x in _sequence(self.candidate_ids, "candidate_ids"))
            if len(ids) != k:
                raise ValueError("one candidate id per candidate is required")
            if len(set(ids)) != k:
                raise ValueError("candidate ids must be distinct; candidates are never deduplicated")
        if self.target_labels is None:
            targets = ids
        else:
            targets = tuple(_label(x, "target label") for x in _sequence(self.target_labels, "target_labels"))
            if len(targets) != k:
                raise ValueError("one target label per candidate is required")
        object.__setattr__(self, "pool", pool)
        object.__setattr__(self, "radii", tuple(radii))
        object.__setattr__(self, "candidate_ids", ids)
        object.__setattr__(self, "target_labels", targets)

    @property
    def size(self) -> int:
        return self.pool.size

    @property
    def candidates(self) -> int:
        return self.pool.candidates


def box_pool(costs, readings, radii, labels=None, *, candidates=None,
             candidate_ids=None, target_labels=None) -> CandidateBoxPool:
    """Convenience constructor from raw exact data."""
    return CandidateBoxPool(reading_pool(costs, readings, labels, candidates), radii,
                            target_labels, candidate_ids)


def from_diagnostic_pool(diagnostic, target_labels=None) -> CandidateBoxPool:
    """Adapter for :class:`thermal_diagnostics.DiagnosticPool`.

    Reuses the compiled readings and the per-candidate ``error_bounds``
    unchanged; no radius is recomputed here."""
    from .thermal_diagnostics import DiagnosticPool
    if not isinstance(diagnostic, DiagnosticPool):
        raise TypeError("diagnostic must be a DiagnosticPool")
    return CandidateBoxPool(diagnostic.pool, diagnostic.error_bounds, target_labels,
                            diagnostic.candidate_ids)


def common_envelope(pool: CandidateBoxPool) -> CandidateBoxPool:
    """The same pool with every radius replaced by its row maximum eps_e."""
    _check(pool)
    radii = tuple((max(row),) * len(row) for row in pool.radii)
    return CandidateBoxPool(pool.pool, radii, pool.target_labels, pool.candidate_ids)


def _check(pool):
    if not isinstance(pool, CandidateBoxPool):
        raise TypeError("pool must be a CandidateBoxPool")


def _experiment(pool, e):
    e = _int(e, "experiment")
    if e >= pool.size:
        raise ValueError("experiment index outside the pool")
    return e


def _candidate(pool, c):
    c = _int(c, "candidate")
    if c >= pool.candidates:
        raise ValueError("candidate index outside the pool")
    return c


# ---------------------------------------------------------------- geometry
def interval(pool: CandidateBoxPool, e, c):
    """Closed interval (lower, upper) of possible readings of c in e."""
    _check(pool)
    e, c = _experiment(pool, e), _candidate(pool, c)
    r, rho = pool.pool.readings[e][c], pool.radii[e][c]
    return r - rho, r + rho


def separation_margin(pool: CandidateBoxPool, e, a, b) -> Fraction:
    """Delta_eab = |r_ea - r_eb| - rho_ea - rho_eb; separation iff > 0."""
    _check(pool)
    e, a, b = _experiment(pool, e), _candidate(pool, a), _candidate(pool, b)
    r, rho = pool.pool.readings[e], pool.radii[e]
    return abs(r[a] - r[b]) - rho[a] - rho[b]


def required_pairs(pool: CandidateBoxPool):
    """Unordered pairs (a, b), a < b, whose target labels differ."""
    _check(pool)
    t = pool.target_labels
    k = pool.candidates
    return tuple((a, b) for a in range(k) for b in range(a + 1, k) if t[a] != t[b])


def candidate_box_masks(pool: CandidateBoxPool):
    """Bit p of mask e is set iff e strictly separates required pair p."""
    pairs = required_pairs(pool)
    masks = []
    for r, rho in zip(pool.pool.readings, pool.radii):
        mask = 0
        for p, (a, b) in enumerate(pairs):
            if abs(r[a] - r[b]) > rho[a] + rho[b]:
                mask |= 1 << p
        masks.append(mask)
    return tuple(masks)


def uncoverable_pairs(pool: CandidateBoxPool):
    """Required pairs that no pool member separates."""
    pairs = required_pairs(pool)
    union = 0
    for m in candidate_box_masks(pool):
        union |= m
    return tuple(pair for p, pair in enumerate(pairs) if not union >> p & 1)


def _panel(pool, panel):
    result = tuple(sorted(set(_int(i, "panel index") for i in _sequence(panel, "panel"))))
    if any(i >= pool.size for i in result):
        raise ValueError("panel index outside the pool")
    return result


def panel_cost(pool: CandidateBoxPool, panel) -> Fraction:
    _check(pool)
    return sum((pool.pool.costs[i] for i in _panel(pool, panel)), Fraction(0))


def candidate_box_separates(pool: CandidateBoxPool, panel) -> bool:
    """True iff every required pair is strictly separated by a panel member."""
    _check(pool)
    panel = _panel(pool, panel)
    masks = candidate_box_masks(pool)
    covered = 0
    for i in panel:
        covered |= masks[i]
    return covered == (1 << len(required_pairs(pool))) - 1


# ---------------------------------------------------------------- decoding
def candidate_box_consistent(pool: CandidateBoxPool, panel, observed):
    """Candidates c with every observed reading in I_ec (closed).

    ``observed`` is aligned with the sorted, deduplicated panel indices.  An
    empty result means no declared candidate fits: a model-contract failure
    signal, not identification of a new candidate."""
    _check(pool)
    panel = _panel(pool, panel)
    y = tuple(_q(v, "observed reading") for v in _sequence(observed, "observed"))
    if len(y) != len(panel):
        raise ValueError("one observed reading per panel member is required")
    r, rho = pool.pool.readings, pool.radii
    return tuple(c for c in range(pool.candidates)
                 if all(abs(ye - r[e][c]) <= rho[e][c] for e, ye in zip(panel, y)))


def candidate_box_targets(pool: CandidateBoxPool, panel, observed):
    """Distinct target labels of the consistent candidates, in candidate order."""
    seen = []
    for c in candidate_box_consistent(pool, panel, observed):
        t = pool.target_labels[c]
        if t not in seen:
            seen.append(t)
    return tuple(seen)


@dataclass(frozen=True)
class CandidateBoxAmbiguity:
    """``observed`` lies in I_ea and I_eb for every panel member e (sorted
    panel order), so it is a possible reading under truth a and under truth
    b, whose targets differ."""

    a: int
    b: int
    panel: tuple
    observed: tuple


def candidate_box_ambiguity(pool: CandidateBoxPool, panel):
    """None if the panel separates every required pair; otherwise the first
    unseparated required pair with the midpoint of each coordinate's
    nonempty interval intersection."""
    _check(pool)
    panel = _panel(pool, panel)
    r, rho = pool.pool.readings, pool.radii
    for a, b in required_pairs(pool):
        if all(abs(r[e][a] - r[e][b]) <= rho[e][a] + rho[e][b] for e in panel):
            y = []
            for e in panel:
                low = max(r[e][a] - rho[e][a], r[e][b] - rho[e][b])
                high = min(r[e][a] + rho[e][a], r[e][b] + rho[e][b])
                y.append((low + high) / 2)
            return CandidateBoxAmbiguity(a, b, panel, tuple(y))
    return None


# ------------------------------------------------------------ optimization
@dataclass(frozen=True)
class CandidateBoxPanelResult:
    """Status ``optimal``: ``panel`` is a minimum-cost separating panel.
    ``infeasible``: ``uncoverable`` lists every required pair no member
    separates; panel and cost are None.  ``inconclusive``: the node budget
    was exhausted; ``panel``/``cost`` are a feasible incumbent (an upper
    bound) and ``lower_bound`` a proved lower bound."""

    status: str
    panel: tuple | None
    cost: Fraction | None
    lower_bound: Fraction | None
    nodes: int
    uncoverable: tuple

    @property
    def feasible(self):
        return self.status != "infeasible"


class _Budget(Exception):
    pass


def _undominated(costs, masks):
    """Drop empty and dominated experiments (strict order with index tie-break)."""
    kept = []
    for e in range(len(costs)):
        if not masks[e]:
            continue
        for f in range(len(costs)):
            if f == e or masks[f] & masks[e] != masks[e] or costs[f] > costs[e]:
                continue
            if masks[f] != masks[e] or costs[f] < costs[e] or f < e:
                break
        else:
            kept.append(e)
    return kept


def _cover_kernel(costs, masks, npairs, max_nodes, packing, reduce):
    """Exact weighted pair cover on validated masks (private: masks must come
    from :func:`candidate_box_masks`).  Returns (status, indices, cost, lb, nodes)."""
    full = (1 << npairs) - 1
    if npairs == 0:
        return "optimal", (), Fraction(0), Fraction(0), 1
    index = _undominated(costs, masks) if reduce else [e for e in range(len(costs)) if masks[e]]
    cs = [costs[e] for e in index]
    ms = [masks[e] for e in index]
    coverers = [sorted((i for i in range(len(index)) if ms[i] >> p & 1), key=lambda i: (cs[i], i))
                for p in range(npairs)]

    def bound(uncovered, allowed):
        cheap = {}
        for p in range(npairs):
            if uncovered >> p & 1:
                i = next((i for i in coverers[p] if allowed >> i & 1), None)
                if i is None:
                    return None
                cheap[p] = cs[i]
        if not packing:
            return max(cheap.values())
        total, packed = Fraction(0), 0
        for p in sorted(cheap, key=lambda p: (-cheap[p], p)):
            reach = 0
            for i in coverers[p]:
                if allowed >> i & 1:
                    reach |= ms[i]
            if not reach & packed:
                packed |= 1 << p
                total += cheap[p]
        return total

    covered, chosen = 0, []
    while covered != full:
        best = None
        for i, m in enumerate(ms):
            new = bin(m & ~covered).count("1")
            if new and (best is None or cs[i] * best[1] < cs[best[0]] * new):
                best = (i, new)
        chosen.append(best[0])
        covered |= ms[best[0]]
    state = {"cost": sum((cs[i] for i in chosen), Fraction(0)), "panel": list(chosen), "nodes": 0}
    everyone = (1 << len(index)) - 1
    root = bound(full, everyone)

    def search(uncovered, allowed, picked, cost):
        state["nodes"] += 1
        if state["nodes"] > max_nodes:
            raise _Budget
        if not uncovered:
            if cost < state["cost"]:
                state["cost"], state["panel"] = cost, list(picked)
            return
        lb = bound(uncovered, allowed)
        if lb is None or cost + lb >= state["cost"]:
            return
        options = None
        for p in range(npairs):
            if uncovered >> p & 1:
                opts = [i for i in coverers[p] if allowed >> i & 1]
                if options is None or len(opts) < len(options):
                    options = opts
        for i in options:
            picked.append(i)
            search(uncovered & ~ms[i], allowed & ~(1 << i), picked, cost + cs[i])
            picked.pop()
            allowed &= ~(1 << i)

    status = "optimal"
    try:
        search(full, everyone, [], Fraction(0))
    except _Budget:
        status = "inconclusive"
        state["nodes"] = max_nodes
    panel = tuple(sorted(index[i] for i in state["panel"]))
    lower = state["cost"] if status == "optimal" else root
    return status, panel, state["cost"], lower, state["nodes"]


def minimum_candidate_box_panel(pool: CandidateBoxPool, *, max_nodes: int = 10**6,
                                packing: bool = True, reduce: bool = True) -> CandidateBoxPanelResult:
    """Exact minimum-cost panel separating every required pair.

    Branch and bound over the heterogeneous masks: branch on an uncovered
    pair with fewest admissible coverers (include the i-th coverer, exclude
    earlier ones), prune with the independent-pair packing lower bound.
    Zero-cost experiments are allowed; every branch removes an experiment
    from the admissible set, so the search tree is finite.  Exceeding
    ``max_nodes`` gives status ``inconclusive``."""
    _check(pool)
    _int(max_nodes, "max_nodes", 1)
    if not isinstance(packing, bool) or not isinstance(reduce, bool):
        raise TypeError("packing and reduce must be bool")
    pairs = required_pairs(pool)
    masks = candidate_box_masks(pool)
    bad = uncoverable_pairs(pool)
    if bad:
        return CandidateBoxPanelResult("infeasible", None, None, None, 0, bad)
    status, panel, cost, lower, nodes = _cover_kernel(pool.pool.costs, masks, len(pairs),
                                                      max_nodes, packing, reduce)
    return CandidateBoxPanelResult(status, panel, cost, lower, nodes, ())


# ----------------------------------------------------------------- receipts
def rational_json(value):
    """Canonical NX exact encoding [numerator, denominator]."""
    value = _q(value)
    return [value.numerator, value.denominator]


def candidate_box_receipt(pool: CandidateBoxPool, result: CandidateBoxPanelResult,
                          *, oracle_cost=None, protocol_labels=None):
    """Deterministic JSON-ready record of schema ``singularity.candidate-box-panel/1``.

    Records the complete readings, radii and costs, so every coverage
    decision can be recomputed, plus the raw margins Delta_eab of every
    selected experiment on every required pair."""
    _check(pool)
    if not isinstance(result, CandidateBoxPanelResult):
        raise TypeError("result must be a CandidateBoxPanelResult")
    pairs = required_pairs(pool)
    labels = pool.pool.labels if protocol_labels is None else _sequence(protocol_labels, "protocol_labels")
    if len(labels) != pool.size:
        raise ValueError("one protocol label per experiment is required")
    record = {
        "schema": SCHEMA,
        "rational_encoding": "[numerator, denominator]",
        "uncertainty_contract": "independent reset per experiment; closed product boxes "
                                "prod_e [r_ec - rho_ec, r_ec + rho_ec]; strict separation",
        "candidate_ids": list(pool.candidate_ids),
        "target_labels": list(pool.target_labels),
        "protocol_labels": list(labels),
        "costs": [rational_json(c) for c in pool.pool.costs],
        "readings": [[rational_json(x) for x in row] for row in pool.pool.readings],
        "radii": [[rational_json(x) for x in row] for row in pool.radii],
        "required_pairs": [list(p) for p in pairs],
        "status": result.status,
        "selected_indices": None if result.panel is None else list(result.panel),
        "cost": None if result.cost is None else rational_json(result.cost),
        "lower_bound": None if result.lower_bound is None else rational_json(result.lower_bound),
        "search_nodes": result.nodes,
        "uncoverable": [list(p) for p in result.uncoverable],
        "independent_oracle_cost": None if oracle_cost is None else rational_json(oracle_cost),
    }
    if result.panel is not None:
        r, rho = pool.pool.readings, pool.radii
        record["selected_margins"] = {
            str(e): [rational_json(abs(r[e][a] - r[e][b]) - rho[e][a] - rho[e][b]) for a, b in pairs]
            for e in result.panel}
        cover = []
        for a, b in pairs:
            hits = [e for e in result.panel if abs(r[e][a] - r[e][b]) > rho[e][a] + rho[e][b]]
            cover.append({"pair": [a, b], "covered_by": hits})
        record["covered_pairs"] = cover
    return record
