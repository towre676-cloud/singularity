#!/usr/bin/env python3
"""Explicit POSTHOC neural-protected-prior analysis of retained token losses.

No neural model is loaded or called. The original frozen confirmation is
unchanged. After the equal-prior blend's negative 360M result, this analysis
declares a 95% pure-neural prior for its analytical comparator ceiling, then
replays every document of every model in that confirmation. It is a design
diagnostic, not a new prospective confirmation or a tuned winning result.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DEFAULT_INPUT = ROOT / "applications/training_lab/results/pretrained_prediction"
DEPENDENCIES = ("scripts/replay_pretrained_prior.py", "src/singularity/training/prior_blend.py",
                "src/singularity/training/online_blend.py", "scripts/confirm_pretrained_prediction.py")
DOMAINS = ("reference_prose", "legal_prose", "source_code")
ARMS = ("neural", "adaptive_count", "equal_prior_blend", "neural_protected_prior_blend")


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_gzip(path):
    return json.loads(gzip.decompress(Path(path).read_bytes()))


def write_json(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n")
    os.replace(temporary, path)


def primary_module():
    spec = importlib.util.spec_from_file_location("frozen_pretrained_prediction_for_prior_replay",
                                                 ROOT / "scripts/confirm_pretrained_prediction.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay_document(record):
    """Scalar causal posterior replay, using only realized target probabilities."""
    from singularity.training.prior_blend import PriorBayesianBlend

    neural = [float.fromhex(v) for v in record["losses_hex"]["neural"]]
    counts = [float.fromhex(v) for v in record["losses_hex"]["adaptive_count"]]
    equal = [float.fromhex(v) for v in record["losses_hex"]["online_blend"]]
    if len(neural) != record["targets"] or len(counts) != len(neural) or len(equal) != len(neural):
        raise ValueError("retained target trace length mismatch")
    state, protected, before_weights = PriorBayesianBlend(), [], []
    for neural_loss, count_loss in zip(neural, counts):
        # The current posterior is recorded before either target probability
        # is supplied to the update. Neither full vocabulary nor model calls
        # are needed for realized log-loss replay.
        before_weights.append(state.posterior_count_weight)
        protected.append(state._observe_target_probabilities(math.exp(-neural_loss), math.exp(-count_loss)))
    audit = state.guarantee()
    tolerance = 1e-9 + 2.**-36 * abs(audit["online_cumulative_nll"])
    if audit["bound_slack_nats"] < -tolerance or audit["pure_neural_protection_slack_nats"] < -tolerance:
        raise AssertionError("nonuniform-prior comparator bound failed beyond rounding allowance")
    losses = {"neural": neural, "adaptive_count": counts, "equal_prior_blend": equal,
              "neural_protected_prior_blend": protected}
    return {"document": record["document"], "domain": record["domain"], "name": record["name"],
            "targets": record["targets"], "token_ids_sha256": record["token_ids_sha256"],
            "arms": {arm: {"loss_sum_nats_hex": math.fsum(values).hex(),
                           "nll_nats_per_token": math.fsum(values) / len(values)}
                     for arm, values in losses.items()},
            "protected_target_losses_hex": [float(v).hex() for v in protected],
            "protected_prior_to_target_count_weights_hex": [float(v).hex() for v in before_weights],
            "prior_guarantee": audit,
            "observed_protected_minus_neural_nats": math.fsum(protected) - math.fsum(neural),
            "observed_protected_minus_equal_prior_nats": math.fsum(protected) - math.fsum(equal),
            "guarantee_rounding_allowance_nats": tolerance}


def paired_bootstrap(rows, first, second):
    import numpy as np

    differences = np.asarray([float.fromhex(r["arms"][first]["loss_sum_nats_hex"])
                              - float.fromhex(r["arms"][second]["loss_sum_nats_hex"]) for r in rows])
    sizes = np.asarray([r["targets"] for r in rows])
    draws = np.random.default_rng(90211).integers(0, len(rows), size=(10000, len(rows)))
    values = differences[draws].sum(1) / sizes[draws].sum(1)
    return {"difference_nats_per_token": float(differences.sum() / sizes.sum()),
            "percentile_95_interval": np.quantile(values, [.025, .975]).tolist(),
            "documents": len(rows), "documents_first_better": int((differences < 0).sum()),
            "interpretation": "posthoc descriptive paired document-cluster bootstrap; negative favors first"}


def summarize_rows(rows):
    summaries = {}
    for domain in (*DOMAINS, "all_domains"):
        members = [r for r in rows if domain == "all_domains" or r["domain"] == domain]
        if not members:
            raise ValueError("missing declared domain: " + domain)
        total = sum(r["targets"] for r in members)
        summaries[domain] = {
            "documents": len(members), "targets": total,
            "arms": {arm: {"nll_nats_per_token": math.fsum(float.fromhex(r["arms"][arm]["loss_sum_nats_hex"])
                                                                 for r in members) / total}
                     for arm in ARMS},
            "paired": {first + "_minus_" + second: paired_bootstrap(members, first, second)
                       for first, second in (("neural_protected_prior_blend", "neural"),
                                             ("neural_protected_prior_blend", "equal_prior_blend"),
                                             ("equal_prior_blend", "neural"))},
            "all_documents_within_neural_excess_loss_ceiling": all(r["prior_guarantee"]["pure_neural_protection_slack_nats"]
                                                                   >= -r["guarantee_rounding_allowance_nats"] for r in members),
            "total_neural_excess_loss_ceiling_nats": math.fsum(r["prior_guarantee"]["pure_neural_extra_loss_ceiling_nats"]
                                                                for r in members),
        }
    return summaries


def replay(input_path, output_path, trigger_model="smollm2-360m"):
    if output_path.exists():
        raise FileExistsError("posthoc analysis already exists; preserve it rather than overwrite")
    primary = primary_module()
    protocol_path = input_path / "protocol.json"
    frozen = json.loads(protocol_path.read_text())
    if trigger_model not in frozen["models"]:
        raise ValueError("trigger model must be part of the frozen confirmation")
    expected_models = sorted(frozen["models"])
    result_paths = {name: input_path / "models" / name / "results.json" for name in expected_models}
    missing = [name for name, path in result_paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError("all frozen models must complete before replay; missing " + ", ".join(missing))
    models, primary_receipts = {}, {}
    for name in expected_models:
        primary.verify(input_path, name)
        original = json.loads(result_paths[name].read_text())
        rows, traces = [], {}
        for relative, digest in original["trace_files_sha256"].items():
            path = input_path / relative
            if file_sha(path) != digest:
                raise ValueError("primary trace changed: " + relative)
            rows.append(replay_document(read_gzip(path)))
            traces[relative] = digest
        if {r["document"] for r in rows} != {r["document"] for r in frozen["models"][name]["encoded_documents"]}:
            raise ValueError("posthoc analysis must include every declared document")
        models[name] = {"model_id": frozen["models"][name]["model_id"],
                        "revision": frozen["models"][name]["revision"],
                        "parameters": original["parameters"], "dtype": original["environment"]["dtype"],
                        "domains": summarize_rows(rows), "documents": rows,
                        "primary_results_sha256": file_sha(result_paths[name]), "primary_trace_files_sha256": traces}
        primary_receipts[name] = file_sha(result_paths[name])
    from singularity.training.prior_blend import PriorBayesianBlend
    prior = PriorBayesianBlend().initial_prior
    report = {
        "schema": "singularity.posthoc-prior-analysis/1", "analysis_status": "POSTHOC; not frozen primary confirmation",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "motivation": "After observing the equal-prior blend's negative 360M transfer result, evaluate an analytically baseline-protected prior without changing the original confirmation.",
        "trigger_model": trigger_model, "trigger_results_sha256": primary_receipts[trigger_model],
        "prior_choice": "95% mass on pure neural, remaining 5% uniform over 20 other fixed mixture weights; chosen for -log(.95) comparator ceiling, not fitted to document losses",
        "initial_prior": list(prior), "weight_grid": [k / 20 for k in range(21)],
        "bound": "L_online <= min_k(L_k - log(pi_k)) <= L_neural - log(.95)",
        "neural_excess_loss_ceiling_nats_per_document": -math.log(prior[0]),
        "neural_excess_loss_ceiling_nats_per_token_at512_targets": -math.log(prior[0]) / 512,
        "protocol_receipt_sha256": file_sha(protocol_path),
        "source_sha256": {name: file_sha(ROOT / name) for name in DEPENDENCIES},
        "all_frozen_models_included": expected_models,
        "selection_policy": "Every completed model and every document in the frozen confirmation; no model, document, mixture weight or prior tuning",
        "metrics": "realized target NLL only; retained target probabilities cannot reconstruct full-vocabulary accuracy",
        "uncertainty": "posthoc descriptive paired document-cluster bootstrap, 10000 draws, seed 90211; not a new held-out validation",
        "model_forward_calls": 0, "neural_training_updates": 0, "models": models,
        "interpretation": "This demonstrates the declared prior's finite-sequence protection and measures its retained-data behavior. Predictive improvements remain posthoc observations requiring a new prospective benchmark.",
    }
    write_json(output_path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--trigger-model", default="smollm2-360m")
    args = parser.parse_args()
    destination = args.output or args.input / "posthoc_prior_analysis.json"
    report = replay(args.input, destination, args.trigger_model)
    print(json.dumps({"status": report["analysis_status"], "neural_extra_loss_ceiling_nats": report["neural_excess_loss_ceiling_nats_per_document"],
                      "models": {name: model["domains"]["all_domains"] for name, model in report["models"].items()}}, indent=2))


if __name__ == "__main__":
    main()
