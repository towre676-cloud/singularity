#!/usr/bin/env python3
"""Build exact neural diagnostic tables from completed confirmation runs.

    python scripts/build_training_prediction_table.py \
      --results applications/training_lab/results/confirmation \
      --output-dir applications/training_lab/results/diagnostic_panels

The two architectures, four arms, three seeds and eight probe bins are fixed
below, not selected from outcomes. Construction uses frozen TUNE predictions
partitioned by target label modulo eight. TEST predictions evaluate the chosen
panel descriptively and cannot select, prune or break optimizer ties. No
training, inference, checkpoint mutation or third-party package is needed.

All 24 jobs must be complete before any output is written. Checkpoint bytes,
plan and split identities, explicit data-orbit membership, counts, and common
example identities are checked. These checks bind counts to retained artifacts;
they do not rerun the network to independently verify its predictions. The
underlying TUNE split has already served training/hyperparameter selection, so
its diagnostic discrimination is construction evidence, not an unbiased test.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import singularity.training_panels as training_panels

ARCHITECTURES = ("modular_mlp", "modular_transformer")
ARMS = ("baseline", "cosine", "layer_decay", "meta")
SEEDS = (1000, 1001, 1002)
PROBE_COUNT = 8


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical_hash(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def _load(path):
    raw = path.read_bytes()
    return json.loads(raw), _sha(raw)


def _int(value, name, lower=0, upper=None):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < lower or (upper is not None and value > upper):
        raise ValueError(f"{name} is outside its permitted range")
    return value


def _expected_examples(data, split, p):
    orbits = data.get("orbits", {}).get(split)
    if not isinstance(orbits, list):
        raise ValueError(f"data.json needs explicit {split} orbits")
    examples, unordered = set(), set()
    for orbit in orbits:
        if not isinstance(orbit, list) or len(orbit) != 3:
            raise ValueError("each data orbit must be [a, b, label]")
        a, b, label = (_int(v, "orbit value", upper=p - 1) for v in orbit)
        if label != (a + b) % p:
            raise ValueError("data orbit has an incorrect modular-addition target")
        key = (min(a, b), max(a, b))
        if key in unordered:
            raise ValueError("duplicate unordered orbit in declared data split")
        unordered.add(key)
        examples.add((a, b, label))
        examples.add((b, a, label))
    return examples, unordered


def _prediction_rows(predictions, split, p, expected):
    rows = predictions.get(split)
    if not isinstance(rows, list):
        raise ValueError(f"predictions.json needs a {split} array")
    seen, output = set(), []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("input_ids"), list) or len(row["input_ids"]) != 2:
            raise ValueError("each modular prediction needs two integer input IDs")
        a, b = (_int(v, "input ID", upper=p - 1) for v in row["input_ids"])
        label = _int(row.get("label"), "label", upper=p - 1)
        prediction = _int(row.get("prediction"), "prediction", upper=p - 1)
        if label != (a + b) % p:
            raise ValueError("prediction row has an incorrect target")
        key = (a, b, label)
        if key in seen:
            raise ValueError("duplicate prediction example")
        seen.add(key)
        output.append((a, b, label, prediction))
    if seen != expected:
        raise ValueError(f"{split} predictions do not match explicit data.json examples")
    return tuple(sorted(output))


def build_table(results, architecture):
    """Return one source-bound table; fail on any missing or inconsistent run."""
    results = Path(results)
    candidates, sources, stored = [], [], {}
    common_data_hash, common_split_hash, common_p = None, None, None
    identities = {}
    for arm in ARMS:
        for seed in SEEDS:
            directory = results / architecture / arm / f"seed_{seed}"
            required = [directory / name for name in
                        ("predictions.json", "summary.json", "config.json", "data.json", "checkpoint.pt")]
            missing = [str(path) for path in required if not path.is_file()]
            if missing:
                raise ValueError("confirmation jobs are incomplete; missing: " + ", ".join(missing))
            predictions, prediction_hash = _load(directory / "predictions.json")
            summary, summary_hash = _load(directory / "summary.json")
            config, config_hash = _load(directory / "config.json")
            data, data_hash = _load(directory / "data.json")
            checkpoint_hash = _sha((directory / "checkpoint.pt").read_bytes())
            if checkpoint_hash != summary.get("checkpoint_sha256"):
                raise ValueError(f"checkpoint hash mismatch: {directory}")
            if config.get("seed") != seed or summary.get("seed") != seed or config.get("variant") != arm:
                raise ValueError(f"run identity does not match its directory: {directory}")
            if config.get("task") != "modular_addition" or data.get("task") != "modular_addition":
                raise ValueError("only the declared modular-addition tasks are supported")
            model = "mlp" if architecture == "modular_mlp" else "transformer"
            if config.get("model", {}).get("name") != model:
                raise ValueError("architecture directory does not match model configuration")
            if (summary.get("plan_sha256") != _canonical_hash(config)
                or predictions.get("plan_sha256") != summary["plan_sha256"]):
                raise ValueError("prediction and summary plan hashes differ")
            p = _int(data.get("p"), "modulus", PROBE_COUNT)
            if config.get("p") != p or summary.get("split_sha256") != data.get("split_sha256"):
                raise ValueError("configuration or summary disagrees with data split")
            if not isinstance(data.get("split_sha256"), str) or len(data["split_sha256"]) != 64:
                raise ValueError("data split needs a declared SHA256 identity")
            if data["split_sha256"] != _canonical_hash(data.get("orbits")):
                raise ValueError("split SHA256 does not match explicit data orbits")
            if common_data_hash is None:
                common_data_hash, common_split_hash, common_p = data_hash, data["split_sha256"], p
            if (data_hash, data["split_sha256"], p) != (common_data_hash, common_split_hash, common_p):
                raise ValueError("all checkpoints of an architecture must use identical data.json")
            expectations = {split: _expected_examples(data, split, p) for split in ("train", "tune", "test")}
            for first, second in (("train", "tune"), ("train", "test"), ("tune", "test")):
                if expectations[first][1] & expectations[second][1]:
                    raise ValueError("declared train/tune/test unordered orbits overlap")
            candidate_id = f"{arm}-seed-{seed}"
            candidates.append({"id": candidate_id, "label": f"{arm}, seed {seed}",
                               "checkpoint_sha256": checkpoint_hash, "arm": arm, "seed": seed})
            stored[candidate_id] = {}
            for split in ("tune", "test"):
                rows = _prediction_rows(predictions, split, p, expectations[split][0])
                if summary.get("counts", {}).get(split, {}).get("examples") != len(rows):
                    raise ValueError("summary example count disagrees with predictions")
                identity = tuple(row[:3] for row in rows)
                if split not in identities:
                    identities[split] = identity
                elif identities[split] != identity:
                    raise ValueError("checkpoint prediction examples differ")
                stored[candidate_id][split] = rows
            sources.append({
                "candidate_id": candidate_id, "run_path": directory.relative_to(results).as_posix(),
                "predictions_sha256": prediction_hash, "summary_sha256": summary_hash,
                "config_sha256": config_hash, "data_sha256": data_hash,
                "checkpoint_sha256": checkpoint_hash, "plan_sha256": summary["plan_sha256"],
            })
    table = {"schema": training_panels.INPUT_SCHEMA, "candidates": candidates,
             "cost_unit": "evaluated modular-addition examples per checkpoint",
             "provenance": {
                 "architecture": architecture, "task": "modular_addition", "p": common_p,
                 "split_sha256": common_split_hash, "data_file_sha256": common_data_hash,
                 "probe_policy": "Exactly eight fixed bins: target label modulo 8. Bins are specified before reading outcomes; correct/incorrect counts never determine bin membership.",
                 "construction_source": "tune", "audit_source": "test",
                 "construction_note": "TUNE has also served training/hyperparameter construction. The panel is a retrospective diagnostic of frozen checkpoint signatures, not an unbiased quality estimate.",
                 "prediction_verification": "Counts recomputed from retained predictions; checkpoint and metadata hashes verified. Neural inference is not rerun by this script.",
                 "builder_source_sha256": _sha(Path(__file__).read_bytes()),
                 "adapter_source_sha256": _sha(Path(training_panels.__file__).read_bytes()),
                 "sources": sources}}
    for role, split in (("construction", "tune"), ("audit", "test")):
        probes = []
        for residue in range(PROBE_COUNT):
            counts = {}
            for candidate in candidates:
                rows = [row for row in stored[candidate["id"]][split] if row[2] % PROBE_COUNT == residue]
                if not rows:
                    raise ValueError("all eight fixed probe bins must be nonempty")
                counts[candidate["id"]] = {"correct_count": sum(row[2] == row[3] for row in rows),
                                           "total_count": len(rows)}
            probe = {"id": f"label-mod-8-{residue}", "counts": counts}
            if role == "construction":
                probe["cost"] = [next(iter(counts.values()))["total_count"], 1]
            probes.append(probe)
        table[role] = {"split_id": f"{common_split_hash}:{split}", "probes": probes}
    return table


def _check_eight_probe_minimum(table, report):
    """Independent 256-subset oracle, including the one-class empty panel.

    It compares input count fractions directly and does not use planner
    coverage masks, its equivalence classes or its exhaustive implementation.
    """
    ids = [candidate["id"] for candidate in table["candidates"]]
    probes = table["construction"]["probes"]
    if len(probes) != PROBE_COUNT:
        raise ValueError("the independent oracle requires exactly eight probes")
    rows = [tuple(Fraction(probe["counts"][ident]["correct_count"],
                           probe["counts"][ident]["total_count"]) for ident in ids)
            for probe in probes]
    signatures = [tuple(row[c] for row in rows) for c in range(len(ids))]
    pairs = [(a, b) for a, b in combinations(range(len(ids)), 2)
             if signatures[a] != signatures[b]]
    costs = [Fraction(*probe["cost"]) for probe in probes]
    best, minimizers = None, 0
    for subset in range(1 << PROBE_COUNT):
        selected = [e for e in range(PROBE_COUNT) if subset >> e & 1]
        if all(any(rows[e][a] != rows[e][b] for e in selected) for a, b in pairs):
            cost = sum((costs[e] for e in selected), Fraction(0))
            if best is None or cost < best:
                best, minimizers = cost, 1
            elif cost == best:
                minimizers += 1
    selected = [e for e, probe in enumerate(probes) if probe["id"] in report["selected_probe_ids"]]
    if (best != Fraction(*report["selected_panel_cost"])
        or not all(any(rows[e][a] != rows[e][b] for e in selected) for a, b in pairs)):
        raise ArithmeticError("independent input-count subset oracle disagrees with selected panel")
    return {"subsets_checked": 1 << PROBE_COUNT,
            "minimum_cost": [best.numerator, best.denominator],
            "minimum_cost_panel_count": minimizers, "matches_selected_cost": True,
            "scope": "Distinct full construction accuracy signatures; identical checkpoints signatures remain unresolved."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "applications/training_lab/results/confirmation")
    parser.add_argument("--output-dir", "--output", dest="output", type=Path, required=True)
    args = parser.parse_args()
    # Finish validation and planning for both architectures before writing any
    # output, so an incomplete confirmation is never presented as a full panel.
    assembled = []
    shared_data = None
    for architecture in ARCHITECTURES:
        table = build_table(args.results, architecture)
        identity = tuple(table["provenance"][key] for key in
                         ("p", "split_sha256", "data_file_sha256"))
        if shared_data is None:
            shared_data = identity
        elif identity != shared_data:
            raise ValueError("both architectures must share the same modular data and split")
        raw = (json.dumps(table, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
        report = training_panels.training_panel_report(table)
        report["independent_probe_subset_check"] = _check_eight_probe_minimum(table, report)
        report["input_file_sha256"] = _sha(raw)
        assembled.append((architecture, raw, report))
    args.output.mkdir(parents=True, exist_ok=True)
    summaries = []
    for architecture, raw, report in assembled:
        (args.output / f"{architecture}_prediction_table.json").write_bytes(raw)
        (args.output / f"{architecture}_panel_report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
        summaries.append({"architecture": architecture, "candidates": len(report["candidates"]),
                          "signature_classes": report["quotient_class_count"],
                          "selected_probe_ids": report["selected_probe_ids"],
                          "selected_panel_cost": report["selected_panel_cost"],
                          "full_panel_cost": report["full_panel_cost"],
                          "discovery_cost_examples": report["discovery_cost_examples"],
                          "audit_evaluated_example_slots": report["audit"]["evaluated_example_slots"],
                          "audit_construction_distinct_pairs_still_separated":
                              report["audit"]["construction_distinct_pairs_still_separated"],
                          "construction_distinct_pair_count": report["audit"]["construction_distinct_pair_count"]})
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
