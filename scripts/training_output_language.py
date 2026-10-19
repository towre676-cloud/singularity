#!/usr/bin/env python3
"""Explore a richer observer on the same frozen modular model predictions.

    python scripts/training_output_language.py --self-check
    python scripts/training_output_language.py --results \
      applications/training_lab/results/confirmation --output-dir \
      applications/training_lab/results/output_language

This NEW exploratory language was chosen after observing that aggregate
accuracy hid checkpoint distinctions. No model is trained or evaluated again.
Each fixed target-label-modulo-eight block is read as its full predicted-class
histogram. Its cost is the block's number of examples, not that count times the
number of predicted classes. A histogram with total N has digits in 0..N, so
base N+1 encodes it injectively as one exact integer; decoding is checked.

TUNE alone defines full signature classes and selects the cheapest panel. TEST
evaluates those frozen blocks descriptively. This is neither a new independent
training study nor evidence of improved model accuracy or semantic equivalence.
Encoded integers are JSON decimal strings to avoid JavaScript precision loss.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_training_prediction_table as builder
from singularity.panels import exhaustive_minimum_panel, greedy_panel, minimum_cost_panel, reading_pool

SCHEMA = "singularity.training-output-language/1"
OBSERVER = "full-predicted-class-histogram/base-N-plus-one"


def encode_histogram(counts, total):
    """Lossless base-(N+1) code for nonnegative class counts summing to N."""
    if isinstance(total, bool) or not isinstance(total, int) or total < 1:
        raise ValueError("histogram total must be a positive integer")
    counts = tuple(counts)
    if not counts or any(isinstance(c, bool) or not isinstance(c, int) or c < 0 or c > total for c in counts):
        raise ValueError("histogram counts must be integers in 0..N")
    if sum(counts) != total:
        raise ValueError("histogram counts must sum to N")
    base = total + 1
    return sum(count * base ** index for index, count in enumerate(counts))


def decode_histogram(encoded, total, classes):
    if (isinstance(encoded, bool) or not isinstance(encoded, int) or encoded < 0
        or isinstance(total, bool) or not isinstance(total, int) or total < 1
        or isinstance(classes, bool) or not isinstance(classes, int) or classes < 1):
        raise ValueError("invalid histogram decoding arguments")
    remainder, counts = encoded, []
    for _ in range(classes):
        remainder, count = divmod(remainder, total + 1)
        counts.append(count)
    if remainder or sum(counts) != total:
        raise ValueError("encoded integer is not a histogram with the declared shape and total")
    return tuple(counts)


def _classes(rows, candidate_count, selected=None):
    selected = range(len(rows)) if selected is None else selected
    selected = tuple(selected)
    groups = {}
    for c in range(candidate_count):
        groups.setdefault(tuple(rows[e][c] for e in selected), []).append(c)
    return tuple(tuple(group) for group in groups.values())


def _cost(value):
    return [value.numerator, value.denominator]


def _result(result, probe_ids):
    return {"probe_ids": [probe_ids[e] for e in result.panel], "cost": _cost(result.cost),
            "nodes": result.nodes}


def _plan(rows, costs, probe_ids, candidate_ids):
    """Plan on full-signature classes and independently scan all eight-bin subsets."""
    groups = _classes(rows, len(candidate_ids))
    representatives = [group[0] for group in groups]
    if len(groups) > 1:
        pool = reading_pool(costs, [[row[c] for c in representatives] for row in rows], labels=probe_ids)
        optimal = minimum_cost_panel(pool)
        greedy = greedy_panel(pool)
        reference = exhaustive_minimum_panel(pool, max_subsets=1 << len(rows))
        if not optimal.feasible or not reference.feasible or optimal.cost != reference.cost:
            raise ArithmeticError("histogram panel planner disagrees with exhaustive reference")
        selected, best_cost = optimal.panel, optimal.cost
        exact_report, greedy_report = _result(optimal, probe_ids), _result(greedy, probe_ids)
    else:
        selected, best_cost = (), Fraction(0)
        exact_report = {"probe_ids": [], "cost": [0, 1], "nodes": 0}
        greedy_report = dict(exact_report)
    # This second oracle uses direct reading comparisons, not panel masks or
    # the planner's exhaustive code. It also really visits every singleton-
    # quotient subset, instead of calling a trivial minimum an executed scan.
    pairs = [(a, b) for a, b in combinations(range(len(candidate_ids)), 2)
             if any(row[a] != row[b] for row in rows)]
    independent_best, minimizers = None, 0
    for subset in range(1 << len(rows)):
        chosen = [e for e in range(len(rows)) if subset >> e & 1]
        if all(any(rows[e][a] != rows[e][b] for e in chosen) for a, b in pairs):
            cost = sum((costs[e] for e in chosen), Fraction(0))
            if independent_best is None or cost < independent_best:
                independent_best, minimizers = cost, 1
            elif cost == independent_best:
                minimizers += 1
    if independent_best != best_cost or not all(any(rows[e][a] != rows[e][b] for e in selected) for a, b in pairs):
        raise ArithmeticError("direct histogram-reading subset oracle disagrees")
    unresolved = [(a, b) for group in groups for a, b in combinations(group, 2)]
    return {"signature_classes": [[candidate_ids[c] for c in group] for group in groups],
            "class_count": len(groups),
            "unresolved_checkpoint_pairs": [[candidate_ids[a], candidate_ids[b]] for a, b in unresolved],
            "full_panel_cost": _cost(sum(costs, Fraction(0))), "selected_panel_cost": _cost(best_cost),
            "selected_probe_ids": [probe_ids[e] for e in selected],
            "exact": exact_report, "greedy": greedy_report,
            "independent_subset_check": {"subsets_checked": 1 << len(rows),
                                         "minimum_cost": _cost(independent_best),
                                         "minimum_cost_panel_count": minimizers,
                                         "matches_selected_cost": True}}, tuple(selected), pairs


def build_report(results, architecture):
    # Reuse source-bound count/example/config/checkpoint verification, while
    # leaving the earlier accuracy tables and their receipts untouched.
    accuracy = builder.build_table(results, architecture)
    candidate_ids = [candidate["id"] for candidate in accuracy["candidates"]]
    p = accuracy["provenance"]["p"]
    probe_ids = [f"label-mod-8-{i}" for i in range(builder.PROBE_COUNT)]
    costs = [Fraction(*probe["cost"]) for probe in accuracy["construction"]["probes"]]
    matrices = {split: [[] for _ in probe_ids] for split in ("tune", "test")}
    histograms = {split: {probe: {} for probe in probe_ids} for split in ("tune", "test")}
    totals = {}
    for source in accuracy["provenance"]["sources"]:
        candidate = source["candidate_id"]
        path = Path(results) / source["run_path"] / "predictions.json"
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != source["predictions_sha256"]:
            raise ValueError("prediction file changed during observer construction; rerun on completed artifacts")
        predictions = json.loads(raw)
        for split in ("tune", "test"):
            for e, probe in enumerate(probe_ids):
                block = [row for row in predictions[split] if row["label"] % builder.PROBE_COUNT == e]
                n = len(block)
                counts = [0] * p
                for row in block:
                    counts[row["prediction"]] += 1
                encoded = encode_histogram(counts, n)
                if decode_histogram(encoded, n, p) != tuple(counts):
                    raise ArithmeticError("prediction histogram failed lossless encoding replay")
                matrices[split][e].append(encoded)
                histograms[split][probe][candidate] = {
                    "total_count": n, "base": n + 1, "predicted_class_counts": counts,
                    "encoded_decimal": str(encoded), "decoding_verified": True}
                if (split, e) in totals and totals[split, e] != n:
                    raise ValueError("histogram block totals differ across candidates")
                totals[split, e] = n
    plan, selected, construction_pairs = _plan(matrices["tune"], costs, probe_ids, candidate_ids)
    accuracy_rows = [[Fraction(probe["counts"][c]["correct_count"], probe["counts"][c]["total_count"])
                      for c in candidate_ids] for probe in accuracy["construction"]["probes"]]
    audit_unseparated = [(a, b) for a, b in combinations(range(len(candidate_ids)), 2)
                         if all(matrices["test"][e][a] == matrices["test"][e][b] for e in selected)]
    audit_unseparated_set = set(audit_unseparated)
    audit_full_classes = _classes(matrices["test"], len(candidate_ids))
    audit_selected_classes = _classes(matrices["test"], len(candidate_ids), selected)
    return {"schema": SCHEMA, "observer": OBSERVER, "architecture": architecture,
            "study_role": "exploratory observation-language extension after accuracy blindness",
            "candidates": accuracy["candidates"], "probe_ids": probe_ids, "class_count_per_histogram": p,
            "cost_unit": "evaluated examples per checkpoint; reading all predicted-class counts needs no per-class model rerun",
            "accuracy_language_full_signature_class_count": len(_classes(accuracy_rows, len(candidate_ids))),
            "histogram_language_full_signature_class_count": plan["class_count"],
            "construction": {"source_split": "tune", "split_id": accuracy["construction"]["split_id"],
                             "histograms": histograms["tune"], "plan": plan},
            "audit": {"source_split": "test", "split_id": accuracy["audit"]["split_id"],
                      "used_for_selection": False, "histograms": histograms["test"],
                      "construction_distinct_pair_count": len(construction_pairs),
                      "construction_distinct_pairs_still_separated": sum(pair not in audit_unseparated_set for pair in construction_pairs),
                      "selected_panel_unseparated_pairs": [[candidate_ids[a], candidate_ids[b]] for a, b in audit_unseparated],
                      "full_signature_classes": [[candidate_ids[c] for c in group] for group in audit_full_classes],
                      "selected_panel_signature_classes": [[candidate_ids[c] for c in group] for group in audit_selected_classes]},
            "accounting": {
                "additional_neural_inference_examples": 0,
                "construction_prediction_example_slots_already_evaluated": len(candidate_ids) * sum(totals["tune", e] for e in range(len(probe_ids))),
                "audit_prediction_example_slots_already_evaluated": len(candidate_ids) * sum(totals["test", e] for e in range(len(probe_ids))),
                "full_construction_examples_per_checkpoint": sum(totals["tune", e] for e in range(len(probe_ids))),
                "selected_construction_examples_per_checkpoint": sum(totals["tune", e] for e in selected),
                "selected_audit_examples_per_checkpoint": sum(totals["test", e] for e in selected),
                "interpretation": "Reuses already evaluated frozen predictions. Panel costs describe evaluating those probes on a future checkpoint; full-table discovery is already spent and periodic training monitoring is not included."},
            "provenance": {**accuracy["provenance"],
                           "output_language_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                           "observer_selection_note": "The histogram language was proposed after observing the original accuracy language's blindness. This extension is exploratory and is not an independent confirmation study."},
            "claim_boundary": "Exact discrimination of supplied finite histogram signatures and exact minimum cost within eight fixed probe blocks. Histogram equality is coarser than equality of per-input predictions and is not model equivalence. No model accuracy gain, neural dynamical quotient, statistical confidence, or external generalization theorem is claimed."}


def self_check():
    # Independently enumerate every small histogram, proving the tested codes
    # collide only when the full vectors coincide and always decode exactly.
    checked = 0
    for n in range(1, 5):
        seen = {}
        for counts in product(range(n + 1), repeat=4):
            if sum(counts) != n:
                continue
            encoded = encode_histogram(counts, n)
            if encoded in seen and seen[encoded] != counts:
                raise AssertionError("histogram encoding collision")
            seen[encoded] = counts
            if decode_histogram(encoded, n, 4) != counts:
                raise AssertionError("histogram encoding did not round-trip")
            checked += 1
    # Valid N=1 histograms give codes 1,2,4,8. The exact three-cost probe
    # identifies four candidates; the greedy pair of binary probes costs four.
    rows = [[1, 1, 2, 2, 1], [1, 2, 1, 2, 1], [1, 2, 4, 8, 1]] + [[1] * 5 for _ in range(5)]
    costs = tuple(map(Fraction, (2, 2, 3, 1, 1, 1, 1, 1)))
    report, _, _ = _plan(rows, costs, [f"p{i}" for i in range(8)], ["a", "b", "c", "d", "copy-a"])
    assert report["class_count"] == 4 and report["selected_panel_cost"] == [3, 1]
    assert report["greedy"]["cost"] == [4, 1]
    assert report["independent_subset_check"]["subsets_checked"] == 256
    assert report["unresolved_checkpoint_pairs"] == [["a", "copy-a"]]
    return {"small_histograms_checked": checked, "independent_subsets_checked": 256,
            "nontrivial_minimum_cost": [3, 1], "greedy_cost": [4, 1], "status": "PASS"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "applications/training_lab/results/confirmation")
    parser.add_argument("--output-dir", "--output", dest="output", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        print(json.dumps(self_check(), indent=2))
        if args.output is None:
            return
    if args.output is None:
        parser.error("--output-dir is required unless only --self-check is requested")
    reports = [build_report(args.results, architecture) for architecture in builder.ARCHITECTURES]
    identities = {(r["provenance"]["p"], r["provenance"]["split_sha256"],
                   r["provenance"]["data_file_sha256"]) for r in reports}
    if len(identities) != 1:
        raise ValueError("both architectures must share the same data and split")
    args.output.mkdir(parents=True, exist_ok=True)
    summary = []
    for report in reports:
        path = args.output / f"{report['architecture']}_output_language_report.json"
        path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
        plan = report["construction"]["plan"]
        summary.append({"architecture": report["architecture"],
                        "accuracy_classes": report["accuracy_language_full_signature_class_count"],
                        "histogram_classes": report["histogram_language_full_signature_class_count"],
                        "selected_probe_ids": plan["selected_probe_ids"],
                        "selected_cost": plan["selected_panel_cost"], "full_cost": plan["full_panel_cost"],
                        "greedy_cost": plan["greedy"]["cost"],
                        "test_pairs_still_separated": report["audit"]["construction_distinct_pairs_still_separated"],
                        "construction_distinct_pairs": report["audit"]["construction_distinct_pair_count"]})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
