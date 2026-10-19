#!/usr/bin/env python3
"""Frozen finite-catalog regression smoke tests for trained byte transformers.

This selects a reusable set of complete 64-byte causal windows, never truncates
context, never infers model quality from a fingerprint, and keeps construction,
audit, and timing as separately executable phases. Original training is untouched.
"""
from __future__ import annotations

import argparse
import copy
from fractions import Fraction
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import random
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SCHEMA = "singularity.checkpoint-regression-confirmation/1"
SOURCE_REVISION = "b08601e04326c79dfdd32d625aee71d232d685c3"
SOURCE_HASHES = {
    "tune": "204929b7ff9d6184953f867dedb860e40aa69c078fc1e54b3baaa8fb28511c4c",
    "test": "5f1bea067869d04849c0f975a2b29c4ff47d867f484f5010ea5e861eab246d91",
}
CONSTRUCTION_VARIANTS = ("healthy", "quantize_8", "quantize_6", "quantize_4", "no_position", "drop_layer_0", "stale")
AUDIT_VARIANTS = CONSTRUCTION_VARIANTS + ("quantize_7", "quantize_5", "clean_clone")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def exact_reading(predictions):
    """Injective encoding of a fixed-length byte-prediction sequence."""
    raw = bytes(predictions)
    return int.from_bytes(b"\x01" + raw, "big")


def minimum_plan(rows, costs):
    """Quotient duplicates, compare core exact/greedy and independent subsets."""
    from singularity.panels import reading_pool, minimum_cost_panel, greedy_panel, exhaustive_minimum_panel
    columns = list(zip(*rows))
    signatures = {}
    for c, column in enumerate(columns):
        signatures.setdefault(tuple(column), []).append(c)
    groups = list(signatures.values())
    representatives = [g[0] for g in groups]
    pairs = [(a, b) for a, b in combinations(range(len(columns)), 2) if columns[a] != columns[b]]
    if len(groups) > 1:
        pool = reading_pool(costs, [[row[c] for c in representatives] for row in rows])
        optimal, greedy, reference = minimum_cost_panel(pool), greedy_panel(pool), exhaustive_minimum_panel(pool, max_subsets=1 << len(rows))
        if not optimal.feasible or optimal.cost != reference.cost:
            raise ArithmeticError("exact planner and core exhaustive oracle disagree")
        selected = tuple(optimal.panel)
        exact_cost = optimal.cost
        greedy_selected = tuple(greedy.panel)
    else:
        selected, exact_cost, greedy_selected = (), Fraction(0), ()
    independent_cost, minimizers = None, []
    for mask in range(1 << len(rows)):
        panel = tuple(i for i in range(len(rows)) if mask >> i & 1)
        if all(any(rows[i][a] != rows[i][b] for i in panel) for a, b in pairs):
            cost = sum((Fraction(costs[i]) for i in panel), Fraction(0))
            if independent_cost is None or cost < independent_cost:
                independent_cost, minimizers = cost, [panel]
            elif cost == independent_cost:
                minimizers.append(panel)
    if independent_cost != exact_cost:
        raise ArithmeticError("independent direct-reading enumeration disagrees")
    def distinguishes(panel):
        return sum(any(rows[i][a] != rows[i][b] for i in panel) for a, b in pairs)
    rng = random.Random(90210)
    random_panels = [tuple(sorted(rng.sample(range(len(rows)), len(selected)))) for _ in range(100)]
    return {
        "selected_blocks": list(selected), "selected_cost_input_tokens": int(exact_cost),
        "full_cost_input_tokens": int(sum(costs)), "signature_classes": groups,
        "construction_distinct_pairs": len(pairs),
        "exact_selected_pair_separations": distinguishes(selected),
        "greedy_selected_blocks": list(greedy_selected),
        "greedy_cost_input_tokens": sum(costs[i] for i in greedy_selected),
        "independent_subsets_checked": 1 << len(rows),
        "independent_minimum_cost_input_tokens": int(independent_cost),
        "independent_minimizing_panels": [list(p) for p in minimizers],
        "first_k_blocks": list(range(len(selected))),
        "first_k_separated_pairs": distinguishes(range(len(selected))),
        "fixed_random_seed": 90210, "fixed_random_panels": [list(p) for p in random_panels],
        "fixed_random_pairs_separated": [distinguishes(p) for p in random_panels],
        "scope": "Exact minimum only in eight declared 64-window blocks; not all possible text probes.",
    }


def setup_torch():
    import torch
    torch.set_num_threads(2)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    torch.use_deterministic_algorithms(True)
    return torch


def checkpoint_path(results, seed):
    return Path(results) / "confirmation" / "wikitext_byte" / "baseline" / f"seed_{seed}" / "checkpoint.pt"


def load_model(path):
    from singularity.training.runner import load_checkpoint
    model, _, _ = load_checkpoint(path)
    return model.eval()


def mutate_model(base, variant, stale=None):
    """Deterministic deployment changes; weight-only fake quantization uses FP32 compute."""
    import torch
    from torch import nn
    if variant == "stale":
        if stale is None:
            raise ValueError("stale reference model required")
        return copy.deepcopy(stale).eval()
    model = copy.deepcopy(base).eval()
    with torch.no_grad():
        if variant.startswith("quantize_"):
            bits = int(variant.split("_")[1])
            if not 2 <= bits <= 16:
                raise ValueError("invalid quantization precision")
            qmax = (1 << (bits - 1)) - 1
            for p in model.parameters():
                if p.ndim < 2:
                    continue
                maximum = p.abs().max()
                if maximum > 0:
                    scale = maximum / qmax
                    p.copy_((p / scale).round().clamp(-qmax, qmax) * scale)
        elif variant == "no_position":
            model.position.weight.zero_()
        elif variant == "drop_layer_0":
            if len(model.body.layers) < 2:
                raise ValueError("need two encoder layers")
            model.body.layers = nn.ModuleList(list(model.body.layers)[1:])
        elif variant not in ("healthy", "clean_clone"):
            raise ValueError("unknown regression variant")
    return model


def source_windows(source_dir, split, start=65536, end=98304):
    import pyarrow.parquet as pq
    import torch
    name = "validation" if split == "tune" else "test"
    path = Path(source_dir) / f"{name}-00000-of-00001.parquet"
    if digest(path) != SOURCE_HASHES[split]:
        raise ValueError("pinned WikiText parquet hash mismatch")
    rows = pq.read_table(path, columns=["text"]).column("text").to_pylist()
    raw = ("\n".join(row for row in rows if row and row.strip()) + "\n").encode("utf-8")
    excerpt = raw[start:end]
    if len(excerpt) != end - start or len(excerpt) % 64:
        raise ValueError("source excerpt must contain complete contexts")
    windows = torch.tensor(list(excerpt), dtype=torch.long).reshape(-1, 64)
    return windows, {"split": split, "parquet_sha256": digest(path),
                     "stream_sha256": hashlib.sha256(raw).hexdigest(),
                     "stream_total_bytes": len(raw), "range_half_open": [start, end],
                     "excerpt_sha256": hashlib.sha256(excerpt).hexdigest(),
                     "input_windows": len(windows), "context_length": 64,
                     "forwarded_input_tokens": windows.numel(),
                     "window_sha256": hashlib.sha256(windows.numpy().tobytes()).hexdigest()}


def predict(model, windows, batch_size=16):
    import torch
    outputs = []
    with torch.inference_mode():
        for start in range(0, len(windows), batch_size):
            outputs.append(model(windows[start:start+batch_size]).argmax(-1).to(torch.uint8))
    return torch.cat(outputs)


def blocks_from_prediction(prediction):
    return [exact_reading(prediction[start:start+64].flatten().tolist()) for start in range(0, len(prediction), 64)]


def freeze(args):
    setup_torch()
    output = Path(args.output)
    protocol_path = output / "protocol.json"
    if protocol_path.exists():
        raise FileExistsError("frozen protocol already exists; do not silently replace it")
    sources = {split: source_windows(args.source_dir, split)[1] for split in ("tune", "test")}
    checkpoints = {str(seed): {"relative_path": str(checkpoint_path(args.results, seed).relative_to(Path(args.results))),
                              "sha256": digest(checkpoint_path(args.results, seed))} for seed in (1000, 1001, 1002)}
    protocol = {
        "schema": SCHEMA, "role": "Confirmatory finite regression smoke-test study; no new training or quality claim",
        "construction_seeds": [1000, 1001], "heldout_seed": 1002,
        "heldout_meaning": "Previously trained checkpoint, never used in this panel's construction or selection",
        "construction_variants": list(CONSTRUCTION_VARIANTS), "audit_variants": list(AUDIT_VARIANTS),
        "heldout_variant_strengths": [7, 5],
        "stale_reference_seed": {"1000": 1001, "1001": 1000, "1002": 1000},
        "quantization_definition": "For each weight tensor ndim>=2 independently: qmax=2**(bits-1)-1; scale=max(abs(W))/qmax; W'=clamp(round(W/scale),-qmax,qmax)*scale. Bias/norm vectors unchanged. FP32 storage and compute; no acceleration claim.",
        "other_variants": {"no_position": "zero entire positional embedding", "drop_layer_0": "remove first of two encoder layers", "stale": "load declared other seed checkpoint", "clean_clone": "bit-identical deepcopy control"},
        "checkpoints": checkpoints, "sources": sources,
        "probe_pool": {"count": 8, "block_windows": 64, "context_length": 64, "cost_input_tokens_each": 4096,
                       "complete_pool_windows": 512, "complete_pool_tokens": 32768,
                       "rule": "eight consecutive nonoverlapping 64-window blocks covering the complete declared suffix",
                       "readout": "all argmax byte predictions in chronological order; injective sentinel-prefixed base256 integer"},
        "selection": "TUNE with seeds1000/1001 only; quotient exactly equal complete signatures; minimum exact pair-distinguishing panel; direct enumeration of all256subsets and greedy comparator; seeded100random panels at same cardinality; retain selected block IDs without adaptation",
        "audit": "Apply frozen block IDs on TEST suffix and heldout seed1002 on TUNE+TEST. For each variant report all drift against own healthy reference, selected drift, clean controls and all pairwise separation. No reselection.",
        "timing": {"threads": 2, "batch_size": 16, "context_length": 64, "warmup_pairs": 5, "measured_pairs": 30,
                   "order_seed": 41073, "workload_model_seed": 1002,
                   "rule": "one resident healthy model, identical prediction API and exact16x64batches for full and selected; randomize paired order; reportP50/P90; host shared; construction/source/model loading+solver charged once for break-even"},
        "script_sha256": digest(__file__), "model_source_sha256": digest(ROOT / "src/singularity/training/models.py"),
        "claim_boundary": "Finite exact discrimination of observed deployment variants and measured inference work. Missing drift is retained. No bound on unseen regressions, semantic equivalence, model quality, neural training improvement, GPU speed or unique advantage over simple panels.",
    }
    write_json(protocol_path, protocol)
    print(json.dumps({"protocol": str(protocol_path), "sha256": digest(protocol_path), "source_ranges": [65536, 98304]}))


def checked_protocol(args):
    path = Path(args.output) / "protocol.json"
    protocol = json.loads(path.read_text())
    if protocol["script_sha256"] != digest(__file__):
        raise ValueError("study code changed after protocol freeze")
    for seed, cp in protocol["checkpoints"].items():
        if digest(checkpoint_path(args.results, int(seed))) != cp["sha256"]:
            raise ValueError("checkpoint changed after freeze")
    return protocol


def infer_catalog(args, split, seeds, variants):
    from singularity.training.runner import model_sha256
    torch = setup_torch()
    protocol = checked_protocol(args)
    windows, source = source_windows(args.source_dir, split)
    if source != protocol["sources"][split]:
        raise ValueError("source changed after freeze")
    models = {seed: load_model(checkpoint_path(args.results, seed)) for seed in set(seeds) | {protocol["stale_reference_seed"][str(s)] for s in seeds}}
    candidate_ids, predictions, hashes = [], {}, {}
    for seed in seeds:
        for variant in variants:
            cid = f"seed_{seed}/{variant}"
            model = mutate_model(models[seed], variant, models[protocol["stale_reference_seed"][str(seed)]])
            prediction = predict(model, windows)
            candidate_ids.append(cid)
            predictions[cid] = prediction
            hashes[cid] = model_sha256(model)
    columns = [blocks_from_prediction(predictions[c]) for c in candidate_ids]
    rows = [list(row) for row in zip(*columns)]
    encoded = {cid: bytes(pred.flatten().tolist()).hex() for cid, pred in predictions.items()}
    return candidate_ids, rows, predictions, {"source": source, "prediction_hex": encoded, "model_tensor_sha256": hashes,
        "environment": {"torch": torch.__version__, "threads": torch.get_num_threads(), "device": "cpu", "batch_size": 16,
                        "forward_calls_per_candidate_full": 32, "input_tokens_per_candidate_full": 32768}}


def construct(args):
    begin = time.perf_counter()
    protocol = checked_protocol(args)
    cids, rows, _, inference = infer_catalog(args, "tune", protocol["construction_seeds"], protocol["construction_variants"])
    inference_seconds = time.perf_counter() - begin
    t0 = time.perf_counter()
    plan = minimum_plan(rows, [4096] * 8)
    solver_seconds = time.perf_counter() - t0
    if not plan["selected_blocks"]:
        raise RuntimeError("empty panel does not identify any distinct model states")
    result = {"schema": SCHEMA, "protocol_sha256": digest(Path(args.output) / "protocol.json"),
              "candidate_ids": cids, "plan": plan, **inference,
              "construction_cost": {"source_load_checkpoint_load_all_inference_seconds": inference_seconds,
                                    "all_planner_comparator_oracle_seconds": solver_seconds,
                                    "total_seconds": time.perf_counter() - begin,
                                    "forwarded_input_tokens": len(cids) * 32768,
                                    "forward_calls": len(cids) * 32,
                                    "includes": "all TUNE construction candidates, source/checkpoint loading, exact/greedy/exhaustive/direct/random planning; no amortization hides this cost"}}
    write_json(Path(args.output) / "construction.json", result)
    write_json(Path(args.output) / "frozen_panel.json", {"protocol_sha256": result["protocol_sha256"],
               "construction_sha256": digest(Path(args.output) / "construction.json"),
               "selected_blocks": plan["selected_blocks"], "selected_cost_input_tokens": plan["selected_cost_input_tokens"],
               "frozen_before_audit": True})
    print(json.dumps({"phase": "construction", "plan": plan, "cost": result["construction_cost"]}))


def separation(rows, selected):
    count = len(rows[0])
    distinct_full, distinct_selected, losses = 0, 0, []
    for a, b in combinations(range(count), 2):
        full = any(row[a] != row[b] for row in rows)
        small = any(rows[e][a] != rows[e][b] for e in selected)
        distinct_full += full
        distinct_selected += small
        if full and not small:
            losses.append([a, b])
    return {"all_candidate_pairs": count * (count - 1) // 2, "full_distinct_pairs": distinct_full,
            "selected_distinct_pairs": distinct_selected, "full_distinct_pairs_missed": losses}


def audit(args):
    audit_begin = time.perf_counter()
    protocol = checked_protocol(args)
    panel_path = Path(args.output) / "frozen_panel.json"
    frozen_panel_hash = digest(panel_path)
    panel = json.loads(panel_path.read_text())
    construction = json.loads((Path(args.output) / "construction.json").read_text())
    if digest(Path(args.output) / "construction.json") != panel["construction_sha256"]:
        raise ValueError("construction changed after panel freeze")
    selected = panel["selected_blocks"]
    reports = {}
    for name, split, seeds, variants in (
        ("new_text_known_checkpoints", "test", [1000, 1001], protocol["construction_variants"]),
        ("heldout_checkpoint_tune", "tune", [1002], protocol["audit_variants"]),
        ("heldout_checkpoint_new_text", "test", [1002], protocol["audit_variants"]),
    ):
        cids, rows, predictions, inference = infer_catalog(args, split, seeds, variants)
        selected_indices = [j for b in selected for j in range(b * 64, (b + 1) * 64)]
        drifts = []
        for seed in seeds:
            healthy = predictions[f"seed_{seed}/healthy"]
            for variant in variants:
                if variant == "healthy":
                    continue
                pred = predictions[f"seed_{seed}/{variant}"]
                diff = pred != healthy
                full_count = int(diff.sum())
                selected_count = int(diff[selected_indices].sum())
                drifts.append({"seed": seed, "variant": variant, "full_drift_tokens": full_count,
                               "selected_drift_tokens": selected_count,
                               "full_drift_detected": bool(full_count), "selected_drift_detected": bool(selected_count),
                               "heldout_strength": variant in ("quantize_7", "quantize_5"),
                               "clean_control": variant == "clean_clone"})
        reports[name] = {"split": split, "checkpoint_seeds": seeds, "candidate_ids": cids,
            "selected_blocks": selected, "all_pair_separation": separation(rows, selected),
            "drift_detection_against_own_reference": drifts,
            "actual_full_forwarded_tokens": len(cids) * 32768,
            "actual_full_forward_calls": len(cids) * 32,
            "counterfactual_selected_forwarded_tokens_per_candidate": len(selected) * 4096,
            "counterfactual_selected_forward_calls_per_candidate": len(selected) * 4,
            "note": "Full outputs retained to audit frozen panel; audit full inference charged to study, not hidden as deployment panel cost.",
            **inference}
    result = {"schema": SCHEMA, "protocol_sha256": digest(Path(args.output) / "protocol.json"),
              "frozen_panel_sha256_before_audit": frozen_panel_hash, "frozen_panel_unchanged_after_audit": digest(panel_path) == frozen_panel_hash,
              "panels_selected_using_audit": False, "reports": reports,
              "full_audit_wall_seconds": time.perf_counter() - audit_begin,
              "claim_boundary": protocol["claim_boundary"]}
    write_json(Path(args.output) / "audit.json", result)
    for name, report in reports.items():
        print(json.dumps({"phase": "audit", "name": name, "separation": report["all_pair_separation"],
                          "drifts": report["drift_detection_against_own_reference"]}))


def percentile(values, p):
    values = sorted(values)
    i = (len(values) - 1) * p
    lo, hi = math.floor(i), math.ceil(i)
    return values[lo] * (hi - i) + values[hi] * (i - lo) if lo != hi else values[lo]


def timing(args):
    setup_torch()
    protocol = checked_protocol(args)
    panel = json.loads((Path(args.output) / "frozen_panel.json").read_text())
    construction = json.loads((Path(args.output) / "construction.json").read_text())
    start_setup = time.perf_counter()
    model = load_model(checkpoint_path(args.results, 1002))
    full, source = source_windows(args.source_dir, "test")
    indices = [j for b in panel["selected_blocks"] for j in range(b * 64, (b + 1) * 64)]
    selected = full[indices].clone()
    setup_seconds = time.perf_counter() - start_setup
    # Both paths use complete16x64batches. No padding or shortened context.
    if len(full) % 16 or len(selected) % 16:
        raise AssertionError("timing requires identical complete batch shape")
    for _ in range(protocol["timing"]["warmup_pairs"]):
        predict(model, full)
        predict(model, selected)
    rng = random.Random(protocol["timing"]["order_seed"])
    records = []
    for repeat in range(protocol["timing"]["measured_pairs"]):
        order = ["full", "selected"]
        rng.shuffle(order)
        record = {"repeat": repeat, "order": order}
        for label in order:
            start = time.perf_counter()
            out = predict(model, full if label == "full" else selected)
            record[label + "_seconds"] = time.perf_counter() - start
            record[label + "_output_sha256"] = hashlib.sha256(out.numpy().tobytes()).hexdigest()
        records.append(record)
    summary = {}
    for label in ("full", "selected"):
        values = [r[label + "_seconds"] for r in records]
        summary[label] = {"median_seconds": statistics.median(values), "p90_seconds": percentile(values, .9),
                          "min_seconds": min(values), "max_seconds": max(values),
                          "forwarded_input_tokens": len(full if label == "full" else selected) * 64,
                          "forward_calls": len(full if label == "full" else selected) // 16,
                          "batch_shape": [16, 64]}
    savings = summary["full"]["median_seconds"] - summary["selected"]["median_seconds"]
    construction_cost = construction["construction_cost"]["total_seconds"]
    audit = json.loads((Path(args.output) / "audit.json").read_text())
    audit_calls = sum(r["actual_full_forward_calls"] for r in audit["reports"].values())
    result = {"schema": SCHEMA, "protocol_sha256": digest(Path(args.output) / "protocol.json"),
              "frozen_panel_sha256": digest(Path(args.output) / "frozen_panel.json"),
              "source": source, "resident_model_setup_seconds": setup_seconds,
              "timing_conditions": protocol["timing"], "records": records, "summary": summary,
              "ratio_full_median_over_selected_median": summary["full"]["median_seconds"] / summary["selected"]["median_seconds"],
              "input_token_ratio_full_over_selected": len(full) / len(selected),
              "median_saved_seconds_per_check": savings,
              "construction_cost_seconds": construction_cost,
              "construction_break_even_checks_by_median_walltime": math.ceil(construction_cost / savings) if savings > 0 else None,
              "construction_break_even_checks_by_input_token_budget": math.ceil(construction["construction_cost"]["forwarded_input_tokens"] / ((len(full) - len(selected)) * 64)),
              "full_audit_forward_calls_spent_in_study": audit_calls,
              "full_audit_seconds_spent_in_study": audit["full_audit_wall_seconds"],
              "construction_plus_audit_break_even_checks_by_median_walltime": math.ceil((construction_cost + audit["full_audit_wall_seconds"]) / savings) if savings > 0 else None,
              "interpretation": "Deployment checking one resident candidate against cached golden outputs. Construction and development audits are separate costs. Break-even includes full measured construction, not audit/repeatedbenchmark overhead; all audit calls reported. Shared host, CPU only; no GPU or throughput claim.",
              "all_outputs_repeat_identical": all(len({r[label + "_output_sha256"] for r in records}) == 1 for label in ("full", "selected"))}
    write_json(Path(args.output) / "timing.json", result)
    print(json.dumps({"phase": "timing", "summary": summary, "speed_ratio": result["ratio_full_median_over_selected_median"],
                      "breakeven": result["construction_break_even_checks_by_median_walltime"], "construction_seconds": construction_cost}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "construct", "audit", "timing"))
    parser.add_argument("--results", type=Path, default=ROOT / "applications/training_lab/results")
    parser.add_argument("--output", type=Path, default=ROOT / "applications/training_lab/results/checkpoint_confirmation")
    parser.add_argument("--source-dir", type=Path, required=True)
    args = parser.parse_args()
    {"freeze": freeze, "construct": construct, "audit": audit, "timing": timing}[args.phase](args)


if __name__ == "__main__":
    main()
