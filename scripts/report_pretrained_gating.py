#!/usr/bin/env python3
"""Model-free heldout analysis of the prospectively selected repetition gates."""
from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gating_analysis_helpers", ROOT / "scripts/confirm_pretrained_gating.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def paired(rows, arm):
    import numpy as np

    neural = np.asarray([float.fromhex(r["arms"]["neural"]["loss_sum_nats_hex"]) for r in rows])
    candidate = np.asarray([float.fromhex(r["arms"][arm]["loss_sum_nats_hex"]) for r in rows])
    sizes = np.asarray([r["targets"] for r in rows])
    difference = candidate - neural
    draws = np.random.default_rng(7102026).integers(0, len(rows), size=(10000, len(rows)))
    bootstraps = difference[draws].sum(1) / sizes[draws].sum(1)
    return {"arm": arm, "documents": len(rows), "targets": int(sizes.sum()),
            "neural_nll_nats_per_token": float(neural.sum() / sizes.sum()),
            "candidate_nll_nats_per_token": float(candidate.sum() / sizes.sum()),
            "difference_nats_per_token": float(difference.sum() / sizes.sum()),
            "loss_reduction_percent": float(100 * (neural.sum() - candidate.sum()) / neural.sum()),
            "descriptive_paired_document_bootstrap_95_interval": np.quantile(bootstraps, [.025, .975]).tolist(),
            "bootstrap_draws": 10000, "bootstrap_seed": 7102026,
            "documents_improved": int((difference < -1e-10).sum()),
            "documents_worse": int((difference > 1e-10).sum()),
            "documents_numerically_tied": int((np.abs(difference) <= 1e-10).sum()),
            "document_tie_allowance_nats": 1e-10,
            "interpretation": "negative difference favors candidate; descriptive document bootstrap, not independent token inference"}


def report(output, name):
    study.verify(output, name, "development")
    study.verify(output, name, "heldout")
    path = output / "models" / name / "heldout" / "results.json"
    result = study.load_json(path)
    selection_path = output / "models" / name / "selection.json"
    selection = study.load_json(selection_path)
    rows = [study.load_json(output / entry["path"]) for entry in result["documents"]]
    selected = selection["selected_arm"]
    groups = {"all_domains": rows}
    groups.update({domain: [r for r in rows if r["domain"] == domain] for domain in sorted({r["domain"] for r in rows})})
    comparisons = {domain: {"primary_selected_minus_neural": paired(members, selected),
                            "secondary_hierarchy_minus_neural": paired(members, "hierarchy_protected"),
                            "secondary_ungated_minus_neural": paired(members, "ungated_protected")}
                   for domain, members in groups.items()}
    diagnostics = {policy["id"]: {"loss_sum_nats_hex": result["aggregate"][policy["id"]]["loss_sum_nats_hex"],
                                   "nll_nats_per_token": result["aggregate"][policy["id"]]["nll_nats_per_token"],
                                   "active_targets": sum(r["gate_active_targets"][policy["id"]] for r in rows),
                                   "raw_unprotected_policy_nll_nats_per_token": math.fsum(float.fromhex(r["raw_gate_loss_sum_nats_hex"][policy["id"]]) for r in rows) / sum(r["targets"] for r in rows)}
                   for policy in study.POLICIES}
    report = {"schema": "singularity.pretrained-gating-heldout-analysis/1", "model": name,
              "protocol_sha256": study.file_sha(output / "protocol.json"),
              "selection_sha256": study.file_sha(selection_path), "selected_arm": selected,
              "heldout_results_sha256": study.file_sha(path), "comparisons": comparisons,
              "all_policy_diagnostics_never_used_for_selection": diagnostics,
              "scope": "Fresh experimental document/source split; source projects and pretraining may overlap. NLL is within native tokenizer. No neural weight updates, cross-tokenizer ranking or universal gain claim.",
              "neural_extra_loss_ceiling_nats_per_document": -math.log(.95),
              "protection_is_not_improvement": True}
    destination = output / "models" / name / "heldout_analysis.json"
    study.write_json(destination, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "applications/training_lab/results/pretrained_gating")
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    result = report(args.output, args.name)
    import json
    print(json.dumps({"model": args.name, "selected_arm": result["selected_arm"],
                      "primary": result["comparisons"]["all_domains"]["primary_selected_minus_neural"]}, indent=2))


if __name__ == "__main__":
    main()
