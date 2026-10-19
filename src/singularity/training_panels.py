"""Exact experiment selection from frozen neural checkpoint predictions.

Input JSON schema ``singularity.training-predictions/1``::

    {"schema": "singularity.training-predictions/1",
     "candidates": [{"id": "adamw-0", "label": "AdamW seed 0"}, ...],
     "construction": {"split_id": "probe-construction", "probes": [
       {"id": "block-0", "cost": [12, 1], "counts": {
          "adamw-0": {"correct_count": 7, "total_count": 12}, ...}}, ...]},
     "audit": {"split_id": "probe-audit", "probes": [
       {"id": "block-0", "counts": {
          "adamw-0": {"correct_count": 6, "total_count": 12}, ...}}, ...]}}

``audit`` is optional. Its probe IDs must match construction, but may be in
another order and contain different examples/counts. Only construction selects
the panel. Split IDs must differ; this checks a declaration, not dataset
disjointness. The caller must supply genuine construction/audit splits and must
not put test results in construction. Counts have to cover every candidate,
with a common positive total_count within each probe. Costs are nonnegative
integers or [integer numerator, positive integer denominator] pairs. No floating
point observations or costs are accepted. Candidate ``checkpoint_sha256``, top
level ``provenance`` and ``cost_unit`` are optional metadata.

The planner identifies equivalence classes of the finite construction reading
table, NOT all checkpoint identities. Identical signatures remain explicitly
unresolved. Audit transfer is descriptive and never changes the chosen panel.
Rationals in receipts use reduced [numerator, denominator] pairs. Exactness is
about counts of supplied predictions and finite combinatorial selection, not
about neural numerical arithmetic, training dynamics, or generalization.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
from itertools import combinations
import json
import re

from .panels import (
    exhaustive_minimum_panel, greedy_panel, minimum_cost_panel, reading_pool,
)

INPUT_SCHEMA = "singularity.training-predictions/1"
REPORT_SCHEMA = "singularity.training-panel-report/1"


def _integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def _name(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _cost(value):
    if isinstance(value, int) and not isinstance(value, bool):
        q = Fraction(value)
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        q = Fraction(_integer(value[0], "cost numerator"),
                     _integer(value[1], "cost denominator", 1))
    else:
        raise TypeError("cost must be an integer or [numerator, denominator]")
    if q < 0:
        raise ValueError("cost must be nonnegative")
    return q


def _q_json(value):
    return [value.numerator, value.denominator]


def _split(value, candidate_ids, *, audit=False):
    if not isinstance(value, dict):
        raise TypeError("each split must be an object")
    split_id = _name(value.get("split_id"), "split_id")
    probes = value.get("probes")
    if not isinstance(probes, list):
        raise TypeError("probes must be a list")
    rows, totals, ids, costs = [], [], [], []
    for probe in probes:
        if not isinstance(probe, dict):
            raise TypeError("each probe must be an object")
        ident = _name(probe.get("id"), "probe id")
        if ident in ids:
            raise ValueError("probe IDs must be unique within a split")
        ids.append(ident)
        costs.append(_cost(probe["cost"]) if "cost" in probe else None)
        if not audit and costs[-1] is None:
            raise ValueError("every construction probe needs a cost")
        counts = probe.get("counts")
        if not isinstance(counts, dict) or set(counts) != set(candidate_ids):
            raise ValueError("each probe must contain counts for exactly every candidate ID")
        row, ns = [], []
        for candidate in candidate_ids:
            cell = counts[candidate]
            if not isinstance(cell, dict):
                raise TypeError("each count cell must be an object")
            correct = _integer(cell.get("correct_count"), "correct_count")
            total = _integer(cell.get("total_count"), "total_count", 1)
            if correct > total:
                raise ValueError("correct_count cannot exceed total_count")
            row.append(Fraction(correct, total))
            ns.append(total)
        if len(set(ns)) != 1:
            raise ValueError("total_count must be equal across candidates within each probe")
        rows.append(tuple(row))
        totals.append(ns[0])
    return split_id, tuple(ids), tuple(costs), tuple(rows), tuple(totals)


def _classes(rows, candidate_count, indices):
    groups = {}
    for candidate in range(candidate_count):
        signature = tuple(rows[e][candidate] for e in indices)
        groups.setdefault(signature, []).append(candidate)
    return tuple(tuple(group) for group in groups.values())


def _pairs(ids, pairs):
    return [[ids[a], ids[b]] for a, b in pairs]


def _result(result, probe_ids):
    return {
        "feasible": result.feasible,
        "probe_ids": None if result.panel is None else [probe_ids[e] for e in result.panel],
        "cost": None if result.cost is None else _q_json(result.cost),
        "nodes": result.nodes,
        "root_lower_bound": None if result.root_lower_bound is None else _q_json(result.root_lower_bound),
    }


def training_panel_report(table, *, max_nodes=10**6):
    """Choose a minimum-cost panel on construction signatures, then audit it.

    All identical full construction signatures are quotiented before calling
    the existing exact set-cover planner. Their members and uncoverable pairs
    are retained. If all candidates coincide, the quotient panel is empty.
    Pools of at most sixteen probes receive an exhaustive reference check.
    Exceeding the planner's work budget raises ValueError, not a result.
    """
    _integer(max_nodes, "max_nodes", 1)
    if not isinstance(table, dict) or table.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"expected schema {INPUT_SCHEMA}")
    candidates = table.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise ValueError("at least two candidate objects are required")
    ids = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise TypeError("each candidate must be an object")
        ident = _name(candidate.get("id"), "candidate id")
        _name(candidate.get("label"), "candidate label")
        if ident in ids:
            raise ValueError("candidate IDs must be unique")
        ids.append(ident)
        if "checkpoint_sha256" in candidate and (
            not isinstance(candidate["checkpoint_sha256"], str)
            or re.fullmatch(r"[0-9a-fA-F]{64}", candidate["checkpoint_sha256"]) is None
        ):
            raise ValueError("checkpoint_sha256 must contain 64 hexadecimal characters")
    if "provenance" in table and not isinstance(table["provenance"], dict):
        raise TypeError("provenance must be an object")
    cost_unit = _name(table.get("cost_unit", "declared experiment units"), "cost_unit")
    split_id, probe_ids, costs, rows, totals = _split(table.get("construction"), ids)
    groups = _classes(rows, len(ids), range(len(rows)))
    representatives = tuple(group[0] for group in groups)
    class_of = {candidate: i for i, group in enumerate(groups) for candidate in group}
    unresolved = tuple(pair for group in groups for pair in combinations(group, 2))
    if len(groups) > 1:
        pool = reading_pool(costs, [[row[c] for c in representatives] for row in rows],
                            labels=probe_ids)
        optimum = minimum_cost_panel(pool, max_nodes=max_nodes)
        greedy = greedy_panel(pool)
        if not optimum.feasible or optimum.panel is None:
            raise ArithmeticError("distinct full signatures were unexpectedly uncoverable")
        selected = optimum.panel
        exact = _result(optimum, probe_ids)
        heuristic = _result(greedy, probe_ids)
        reference = None
        if len(probe_ids) <= 16:
            oracle = exhaustive_minimum_panel(pool, max_subsets=1 << len(probe_ids))
            if not oracle.feasible or oracle.cost != optimum.cost:
                raise ArithmeticError("panel optimizer disagrees with exhaustive reference")
            reference = _result(oracle, probe_ids)
            reference["matches_optimal_cost"] = True
    else:
        selected = ()
        exact = {"feasible": True, "probe_ids": [], "cost": [0, 1], "nodes": 0,
                 "root_lower_bound": [0, 1]}
        heuristic = dict(exact)
        reference = {**exact, "matches_optimal_cost": True} if len(probe_ids) <= 16 else None
    canonical = json.dumps(table, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    witnesses = []
    for a, b in combinations(range(len(ids)), 2):
        if class_of[a] == class_of[b]:
            continue
        e = next((e for e in selected if rows[e][a] != rows[e][b]), None)
        if e is None:
            raise ArithmeticError("selected panel failed to separate distinct signatures")
        witnesses.append({"candidates": [ids[a], ids[b]], "probe_id": probe_ids[e],
                          "readings": [_q_json(rows[e][a]), _q_json(rows[e][b])]})
    report = {
        "schema": REPORT_SCHEMA,
        "input_table_sha256": hashlib.sha256(canonical).hexdigest(),
        "candidates": candidates,
        "provenance": table.get("provenance", {}),
        "selection_split": {"role": "construction", "split_id": split_id},
        "cost_unit": cost_unit,
        "probe_ids": list(probe_ids),
        "construction_readings": [[_q_json(v) for v in row] for row in rows],
        "construction_total_count_per_probe": list(totals),
        "probe_costs": [_q_json(c) for c in costs],
        "construction_signature_classes": [[ids[c] for c in group] for group in groups],
        "construction_uncoverable_pairs": _pairs(ids, unresolved),
        "construction_pair_witnesses": witnesses,
        "all_original_candidates_discriminated": not unresolved,
        "quotient_class_count": len(groups),
        "selected_probe_ids": [probe_ids[e] for e in selected],
        "exact": exact,
        "greedy": heuristic,
        "exhaustive_reference": reference,
        "full_panel_cost": _q_json(sum(costs, Fraction(0))),
        "selected_panel_cost": exact["cost"],
        "full_panel_examples_per_checkpoint": sum(totals),
        "selected_panel_examples_per_checkpoint": sum(totals[e] for e in selected),
        "discovery_cost_examples": len(ids) * sum(totals),
        "discovery_cost_note": "Candidate-by-probe example slots already evaluated to build the full construction table; repeated examples count once per probe, not as unique inputs. This is not measured runtime or a free discovery saving.",
        "claim_boundary": "Minimum declared cost to distinguish the finite construction signature classes within the supplied probe pool. Identical signatures remain unresolved. No training improvement, population generalization, neural linearity, or noise-bound claim is made.",
    }
    # Validate audit only after the construction-only optimizer has finished.
    # Neither its rows nor its costs participate in selection or tie breaking.
    if "audit" in table:
        audit_id, audit_ids, audit_costs, audit_rows, audit_totals = _split(table["audit"], ids, audit=True)
        if audit_id == split_id:
            raise ValueError("construction and audit split IDs must differ")
        if set(audit_ids) != set(probe_ids):
            raise ValueError("audit must provide exactly the construction probe IDs")
        positions = {ident: i for i, ident in enumerate(audit_ids)}
        audit_rows = tuple(audit_rows[positions[ident]] for ident in probe_ids)
        audit_totals = tuple(audit_totals[positions[ident]] for ident in probe_ids)
        for i, ident in enumerate(probe_ids):
            c = audit_costs[positions[ident]]
            if c is not None and c != costs[i]:
                raise ValueError("optional audit probe costs must equal construction costs")
        unseparated = tuple((a, b) for a, b in combinations(range(len(ids)), 2)
                            if all(audit_rows[e][a] == audit_rows[e][b] for e in selected))
        construction_distinct = tuple((a, b) for a, b in combinations(range(len(ids)), 2)
                                      if class_of[a] != class_of[b])
        unseparated_set = set(unseparated)
        report["audit"] = {
            "role": "audit", "split_id": audit_id, "used_for_selection": False,
            "readings": [[_q_json(v) for v in row] for row in audit_rows],
            "full_signature_classes": [[ids[c] for c in group] for group in
                                       _classes(audit_rows, len(ids), range(len(rows)))],
            "selected_panel_signature_classes": [[ids[c] for c in group] for group in
                                                 _classes(audit_rows, len(ids), selected)],
            "selected_panel_unseparated_pairs": _pairs(ids, unseparated),
            "all_original_candidates_separated": not unseparated,
            "construction_distinct_pair_count": len(construction_distinct),
            "construction_distinct_pairs_still_separated": sum(pair not in unseparated_set
                                                               for pair in construction_distinct),
            "evaluated_example_slots": len(ids) * sum(audit_totals),
            "selected_panel_examples_per_checkpoint": sum(audit_totals[e] for e in selected),
            "interpretation": "Descriptive transfer of a frozen construction-selected panel to supplied audit readings; no reselection and no confidence/noise guarantee.",
        }
    return report
