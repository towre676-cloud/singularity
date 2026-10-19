#!/usr/bin/env python3
"""Retrospective v3 design evaluation from immutable v2 T4 raw observations.

No forward passes; no v2 file is written. Known 72-token failure is a retest,
never a new held-out result. All unmeasured threshold guarantees are expressly
conditional on shape observability. Run --verify to replay the saved receipt.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from singularity.model_audit.core import deviation, flags, tolerances_from_clean, verify_package
from singularity.model_audit.truncation import specification, compare, certificate, verify_certificate

SOURCE = ROOT / "applications/training_lab/results/gpu_deployment_audit/v2_t4_qwen2.5-1.5b"
OUTPUT = ROOT / "applications/training_lab/results/gpu_deployment_audit/v3_retrospective_t4"


def load_source(source):
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.iterdir()) if p.is_file()}
    protocol, observed, results = [json.loads((source / n).read_text()) for n in ("protocol.json", "observations.json", "results.json")]
    canonical = json.dumps({k: v for k, v in protocol.items() if k not in ("frozen_at_utc", "protocol_sha256")}, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(canonical).hexdigest() != protocol["protocol_sha256"]:
        raise ValueError("source protocol digest mismatch")
    if not verify_package(json.loads((source / "package.json").read_text()))["verified"]:
        raise ValueError("source package does not verify")
    probes, spec = protocol["probes"], protocol["tolerance"]
    stable = copy.deepcopy(observed["reference/reference"])
    raw_calibration = [observed["calibration/" + k] for k in protocol["calibration_clean_runs"]]
    for e, expected in enumerate(stable):
        if len(expected["argmax"]) != probes[e]["tokens"]:
            raise ValueError("token count does not match full teacher-forced observation")
        for run in raw_calibration:
            if len(run[e]["argmax"]) != len(expected["argmax"]):
                raise ValueError("unstable observation shape")
            for j, token in enumerate(run[e]["argmax"]):
                if token != expected["argmax"][j]:
                    expected["top_gap"][j] = min(expected["top_gap"][j], spec["tie_margin"])
        if "continuation" in expected:
            prefix = len(expected["continuation"])
            for run in raw_calibration:
                got = run[e].get("continuation", [])
                prefix = min(prefix, next((j for j in range(min(len(got), prefix)) if got[j] != expected["continuation"][j]), min(len(got), prefix)))
            if prefix:
                for k in ("continuation", "continuation_logprob"):
                    expected[k] = expected[k][:prefix]
            else:
                expected.pop("continuation"); expected.pop("continuation_logprob")

    def view(row, expected):
        out = {k: v for k, v in row.items() if k not in ("continuation", "continuation_logprob")}
        for k in ("continuation", "continuation_logprob"):
            if k in expected:
                out[k] = row.get(k, [])[:len(expected[k])]
        return out
    calibration = [[view(o, r) for o, r in zip(run, stable)] for run in raw_calibration]
    tolerance, _ = tolerances_from_clean(stable, calibration, spec["factor"], spec["floor"], spec["tie_margin"])
    tables = {k: [flags(deviation(view(o, r), r, spec["tie_margin"]), t) for o, r, t in zip(run, stable, tolerance)]
              for k, run in observed.items() if k.split("/")[0] in ("construction", "heldout", "validation")}
    if any(sum(v) != results["full_pool_separators"][k] for k, v in tables.items()):
        raise ValueError("source separation replay differs")
    return protocol, observed, tables, files


def evaluate(source=SOURCE):
    protocol, observed, tables, hashes = load_source(source)
    probes = protocol["probes"]
    construction = {k.split("/", 1)[1]: v for k, v in tables.items() if k.startswith("construction/") and sum(v) >= 2}
    unavailable = {k: sum(v) for k, v in tables.items() if k.startswith("construction/") and sum(v) < 2}
    # Caps are selected from the length order statistics, not held-out detection.
    # The entire cap family up to the two-witness frontier is guaranteed.
    lengths = sorted((p["tokens"] for p in probes), reverse=True)
    frontier = lengths[1] - 1
    spec = specification(probes, construction, frontier)
    comparison = compare(spec, protocol["typical_panel"])
    cert = certificate(spec, comparison, {"kind": "retrospective design, not prospective validation",
                                          "source_files_sha256": hashes, "source_protocol_sha256": protocol["protocol_sha256"]})
    if not verify_certificate(cert):
        raise ArithmeticError("v3 certificate failed independent check")
    panel_replay = {}
    for name, row in comparison["panels"].items():
        counts = {k: sum(v[e] for e in row["indices"]) for k, v in tables.items()}
        panel_replay[name] = {"counts": counts, "false_alarms": [k for k, n in counts.items() if k.startswith("validation/") and n],
                              "known_72_retest_witnesses": counts["heldout/truncate_to_72"],
                              "previously_exposed_v2_faults_detected": sum(n > 0 for k, n in counts.items() if k.startswith("heldout/")),
                              "genuinely_new_heldout_evaluations": 0}
    # Piecewise-constant exact cost frontier. All caps in each row are equivalent.
    curve = []
    for interval in __import__("singularity.model_audit.truncation", fromlist=["threshold_intervals"]).threshold_intervals([p["tokens"] for p in probes], lengths[0]):
        result = compare(specification(probes, construction, interval["last"]), protocol["typical_panel"])
        curve.append({"minimum_cap": interval["first"], "maximum_cap": interval["last"],
                      "feasible": result["feasible"], "shape_witnesses_available_at_maximum": sum(interval["separates"]),
                      "costs": {k: v["cost"] for k, v in result["panels"].items()}})
    t72 = tables["heldout/truncate_to_72"]
    measured = [{"id": p["id"], "tokens": p["tokens"], "shape_changes": len(observed["heldout/truncate_to_72"][e]["argmax"]) != p["tokens"]}
                for e, p in enumerate(probes) if t72[e]]
    # Conservative prospective design, NOT new numerical observations.
    # Two distinct 128-token inputs guarantee every cap through 127. Other
    # fault coverage is credited only to the original measured probes.
    design_probes = probes + [{"id": "new_guard_a", "tokens": 128, "cost": 128},
                              {"id": "new_guard_b", "tokens": 128, "cost": 128}]
    design_table = {k: v + ([True, True] if k == "truncate_to_48" else [False, False]) for k, v in construction.items()}
    design_spec = specification(design_probes, design_table, 127)
    design_comparison = compare(design_spec, protocol["typical_panel"])
    design_cert = certificate(design_spec, design_comparison,
                              {"kind": "conservative projected design; new probe inputs/output values unmeasured",
                               "new_probes_nontruncation_coverage": "no credit", "truncate_to_48_new_coverage": "conditional shape theorem"})
    if not verify_certificate(design_cert):
        raise ArithmeticError("projected-design certificate failed")
    report = {"status": "retrospective_only", "certificate": cert, "panel_replay": panel_replay, "cost_frontier": curve,
              "v2_exact_cost": 261, "conservative_127_design": design_cert, "extra_cost_at_two_witness_frontier": comparison["panels"]["exact"]["cost"] - 261,
              "unavailable_original_construction_faults_outside_guarantee": unavailable,
              "two_witness_shape_frontier": frontier, "one_witness_shape_frontier": lengths[0] - 1,
              "observed_72_signals": measured, "new_gpu_measurements": False,
              "limitations": "All old held-out cases were exposed before v3 design. This replay cannot establish new held-out generalization. Caps above the two-witness frontier need longer probes. Last-token-only, fabricated full-length outputs and hidden-context truncation lack this shape theorem."}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    report = evaluate(args.source)
    path = args.output / "results.json"
    if args.verify:
        if json.loads(path.read_text()) != report:
            raise SystemExit("retrospective receipt differs from independent source replay")
        print("Verified source-bound v3 retrospective receipt and optimality certificate")
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps({"frontier": report["two_witness_shape_frontier"], "panels": report["certificate"]["comparison"]["panels"], "retest": report["panel_replay"]}, indent=2))

if __name__ == "__main__":
    main()
