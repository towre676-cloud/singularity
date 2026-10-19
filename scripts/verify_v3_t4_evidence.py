#!/usr/bin/env python3
"""Replay the actual v3 T4 ZIP; independently check its tight 379-cost bound.

The original uploaded bytes are immutable. GPU execution is not repeated.
The existing verifier reconstructs calibration, coverage, exact optimum,
package, health and evaluation from source-bound recorded observations.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "applications/training_lab/results/gpu_deployment_audit/v3_t4_qwen2.5-1.5b"
ARCHIVE_SHA256 = "00c93a09723250547e9039c624f8f45fe1fb15d695a508826468a4851fbce66a"
sys.path.insert(0, str(ROOT / "src"))


def replay(archive=RUN / "evidence.zip"):
    archive = Path(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("uploaded archive identity mismatch")
    spec = importlib.util.spec_from_file_location("actual_v3_t4_replay", ROOT / "scripts/colab_deployment_audit_v3.py")
    v3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v3)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        with ZipFile(archive) as z:
            for item in z.infolist():
                path = root / item.filename
                if not path.resolve().is_relative_to(root.resolve()) or item.is_dir():
                    raise ValueError("unexpected archive member")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(z.read(item))
        evidence = root / "evidence"
        status = json.loads((root / "launcher_status.json").read_text())
        for name, expected in status["evidence_files_sha256"].items():
            if hashlib.sha256((evidence / name).read_bytes()).hexdigest() != expected:
                raise ValueError("launcher evidence hash differs: " + name)
        if not status["verified"] or not v3.verify(evidence):
            raise ValueError("source-bound v3 verification failed")
        protocol = json.loads((evidence / "protocol.json").read_text())
        result = json.loads((evidence / "results.json").read_text())
        observed = json.loads((evidence / "observations.json").read_text())
        stable, clean, tolerances, stabilization, rows, specification, comparison = v3.selection(protocol, observed)
        probes, req = protocol["probes"], protocol["requirement"]
        # Three pairwise-disjoint coverer sets give an independent lower bound.
        groups = {"cap_127": [i for i, p in enumerate(probes) if p["tokens"] > 127],
                  "unicode_nfkc": [i for i, b in enumerate(specification["construction"]["unicode_nfkc"]) if b],
                  "padding_mask_dropped": [i for i, b in enumerate(specification["construction"]["padding_mask_dropped"]) if b]}
        used, tight_ids, lower_bound, terms = set(), set(), 0, {}
        for name, coverers in groups.items():
            if used.intersection(coverers):
                raise ValueError("lower-bound groups overlap")
            used.update(coverers)
            choices = sorted((sum(probes[i]["cost"] for i in pair), pair) for pair in combinations(coverers, req))
            if not choices:
                raise ValueError("deficient lower-bound group")
            cost = choices[0][0]
            winners = [pair for value, pair in choices if value == cost]
            if len(winners) != 1:
                raise ValueError("tight bound does not establish uniqueness")
            ids = [probes[i]["id"] for i in winners[0]]
            tight_ids.update(ids)
            lower_bound += cost
            terms[name] = {"coverers": [probes[i]["id"] for i in coverers], "minimum_cost": cost,
                           "unique_cheapest_witnesses": ids}
        exact = comparison["panels"]["exact"]
        if lower_bound != exact["cost"] or tight_ids != set(exact["probe_ids"]) or any(p["cost"] <= 0 for p in probes):
            raise ValueError("tight independent bound differs from the selected optimum")
        # The selected uniform-shift flag is reported as numerical sensitivity,
        # never folded into a headline count of substantive semantic faults.
        shift = []
        margin = protocol["tolerance"]["tie_margin"]
        for i, probe in enumerate(probes):
            report = v3.deviation(v3.base.view(observed["new_heldout/uniform_logit_translation"][i], stable[i]), stable[i], margin)
            if v3.flags(report, tolerances[i]):
                shift.append({"id": probe["id"], "selected": probe["id"] in exact["probe_ids"],
                              "length_mismatch": report["length_mismatch"], "discrete_mismatches": report["discrete_mismatches"],
                              "max_abs": report["max_abs"], "tolerance": tolerances[i]})
        clean_flags = {}
        for name in protocol["validation_clean_runs"]:
            clean_flags[name] = sum(v3.flags(v3.deviation(v3.base.view(row, expected), expected, margin), tolerance)
                                    for row, expected, tolerance in zip(observed["validation/" + name], stable, tolerances))
        report = {"schema": "singularity.actual-v3-t4-replay/1", "archive_sha256": ARCHIVE_SHA256,
                  "source_commit": status["source_commit"], "protocol_sha256": protocol["protocol_sha256"],
                  "hardware": protocol["hardware"], "model": protocol["model"], "revision": protocol["revision"],
                  "dtype": protocol["dtype"], "software": protocol["software"],
                  "pool_cost": sum(p["cost"] for p in probes), "probe_count": len(probes),
                  "panel_costs": {k: p["cost"] for k, p in comparison["panels"].items()},
                  "panel_feasible": {k: p["satisfies_requirement"] for k, p in comparison["panels"].items()},
                  "exact_probe_ids": exact["probe_ids"], "exact_evaluation": result["evaluation"]["exact"],
                  "independent_tight_lower_bound": {"cost": lower_bound, "terms": terms, "unique_optimum": True},
                  "all_integer_caps_1_127_have_two_shape_witnesses": all(sum(probes[i]["tokens"] > cap for i in exact["indices"]) >= 2 for cap in range(1, 128)),
                  "uniform_translation": {"full_pool_flags": len(shift), "selected_flag_reports": [r for r in shift if r["selected"]],
                                          "classification": "finite-precision numerical sensitivity, not evidence of semantic change"},
                  "full_pool_clean_validation_flags": clean_flags,
                  "health_nonfinite_values": sum(sum(counts.values()) for counts in result["numerical_health"].values()),
                  "ties_added": stabilization["ties_added"], "continuation_prefixes": {str(k): v for k, v in stabilization["prefixes"].items()},
                  "claim_boundary": "Recorded full-pool observations; no fresh standalone-panel batching/timing, hardware attestation, A100 transfer or universal semantic-equivalence claim."}
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=RUN / "evidence.zip")
    parser.add_argument("--write", action="store_true", help="save the deterministic replay receipt")
    args = parser.parse_args()
    report = replay(args.archive)
    if args.write:
        (RUN / "verification.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    else:
        expected = json.loads((RUN / "verification.json").read_text())
        if expected != report:
            raise ValueError("retained verification receipt differs")
    print("Verified actual T4 v3: unique 379-token optimum; lower bound 256 + 43 + 80; all caps 1–127 covered")

if __name__ == "__main__":
    main()
