#!/usr/bin/env python3
"""Show that an unchanged checkpoint can have a changed runtime pipeline.

A forward hook zeros positional-embedding OUTPUTS without modifying any saved
weights. One selected-context pass is compared with existing cached healthy and
no-position outputs. This is a post-study engineering equivalence demonstration,
not another independent statistical confirmation or a new fault-selection study.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import confirm_checkpoint_panels as study
from check_checkpoint_smoke import compare_bytes, select_prediction_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True, help="pinned WikiText parquet cache")
    parser.add_argument("--results", type=Path, default=ROOT / "applications/training_lab/results")
    parser.add_argument("--study", type=Path, default=ROOT / "applications/training_lab/results/checkpoint_confirmation")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    begin = time.perf_counter()
    torch = study.setup_torch()
    from singularity.training.runner import model_sha256
    preserved = {name: study.digest(args.study / name) for name in
                 ("protocol.json", "construction.json", "frozen_panel.json", "audit.json", "timing.json", "deployment_clean_check.json")}
    protocol = json.loads((args.study / "protocol.json").read_text())
    panel = json.loads((args.study / "frozen_panel.json").read_text())
    audit = json.loads((args.study / "audit.json").read_text())
    if preserved["protocol.json"] != panel["protocol_sha256"] or preserved["frozen_panel.json"] != audit["frozen_panel_sha256_before_audit"]:
        raise ValueError("frozen panel identity mismatch")
    checkpoint = study.checkpoint_path(args.results, 1002)
    file_before = study.digest(checkpoint)
    if file_before != protocol["checkpoints"]["1002"]["sha256"]:
        raise ValueError("seed1002 checkpoint differs from frozen study")
    windows, source = study.source_windows(args.source_dir, "test")
    if source != protocol["sources"]["test"]:
        raise ValueError("input contexts differ from frozen study")
    indices = [i for b in panel["selected_blocks"] for i in range(b * 64, (b + 1) * 64)]
    selected = windows[indices].clone()
    catalog = audit["reports"]["heldout_checkpoint_new_text"]["prediction_hex"]
    healthy = select_prediction_bytes(bytes.fromhex(catalog["seed_1002/healthy"]), panel["selected_blocks"])
    no_position = select_prediction_bytes(bytes.fromhex(catalog["seed_1002/no_position"]), panel["selected_blocks"])
    model = study.load_model(checkpoint)
    state_before = {name: tensor.detach().clone() for name, tensor in model.state_dict().items()}
    tensor_hash_before = model_sha256(model)
    versions_before = {name: tensor._version for name, tensor in model.state_dict().items()}
    hook_invocations = []
    hook_count_before = len(model.position._forward_hooks)

    def zero_position_output(_module, _inputs, output):
        hook_invocations.append(list(output.shape))
        return torch.zeros_like(output)

    hook = model.position.register_forward_hook(zero_position_output)
    inference_begin = time.perf_counter()
    try:
        prediction = study.predict(model, selected)
    finally:
        hook.remove()
    inference_seconds = time.perf_counter() - inference_begin
    raw = bytes(prediction.flatten().tolist())
    healthy_comparison = compare_bytes(raw, healthy)
    no_position_comparison = compare_bytes(raw, no_position)
    tensor_hash_after = model_sha256(model)
    file_after = study.digest(checkpoint)
    tensor_equalities = {name: bool(torch.equal(tensor, state_before[name]))
                         for name, tensor in model.state_dict().items()}
    versions_after = {name: tensor._version for name, tensor in model.state_dict().items()}
    files_preserved = {name: study.digest(args.study / name) == sha for name, sha in preserved.items()}
    checks = {
        "checkpoint_file_hash_unchanged": file_before == file_after,
        "all_state_dict_tensors_exactly_unchanged": all(tensor_equalities.values()),
        "model_tensor_hash_unchanged": tensor_hash_before == tensor_hash_after,
        "all_tensor_mutation_versions_unchanged": versions_before == versions_after,
        "selected_output_drift_detected_against_healthy": not healthy_comparison["unchanged"],
        "runtime_hook_output_exactly_matches_declared_no_position_variant": no_position_comparison["unchanged"],
        "hook_removed_after_inference": len(model.position._forward_hooks) == hook_count_before,
        "all_previous_study_artifacts_unchanged": all(files_preserved.values()),
        "one_selected_context_pass_only": len(hook_invocations) == len(selected) // 16,
    }
    result = {
        "schema": "singularity.runtime-pipeline-equivalence/1",
        "role": "Post-study implementation equivalence demonstration; not independent statistical confirmation or new fault selection",
        "mechanism": "Runtime forward hook on positional embedding returns zeros_like(output); no parameter or buffer mutation and no checkpoint write",
        "checkpoint_seed": 1002, "checkpoint_relative_path": str(checkpoint.relative_to(args.results)),
        "checkpoint_sha256_before": file_before, "checkpoint_sha256_after": file_after,
        "model_tensor_sha256_before": tensor_hash_before, "model_tensor_sha256_after": tensor_hash_after,
        "state_dict_tensor_count": len(tensor_equalities), "tensor_equalities": tensor_equalities,
        "tensor_mutation_versions_before": versions_before, "tensor_mutation_versions_after": versions_after,
        "selected_blocks": panel["selected_blocks"], "forwarded_input_tokens": selected.numel(),
        "context_length": 64, "batch_shape": [16, 64], "forward_calls": len(selected) // 16,
        "hook_output_shapes": hook_invocations, "resident_prediction_seconds": inference_seconds,
        "changed_predictions_against_cached_healthy": healthy_comparison["changed_prediction_count"],
        "changed_predictions_against_cached_no_position": no_position_comparison["changed_prediction_count"],
        "runtime_prediction_sha256": healthy_comparison["candidate_output_sha256"],
        "cached_healthy_prediction_sha256": healthy_comparison["golden_output_sha256"],
        "cached_no_position_prediction_sha256": no_position_comparison["golden_output_sha256"],
        "preserved_study_artifact_sha256": preserved, "preserved_study_artifact_checks": files_preserved,
        "script_sha256": study.digest(__file__), "checks": checks,
        "conclusion": f"Weight-file and tensor identity passed while the runtime pipeline changed {healthy_comparison['changed_prediction_count']} of{selected.numel()}selected byte predictions. The cached behavioral smoke test detects this declared runtime error; weight identity alone does not detect it.",
        "claim_boundary": "Engineering demonstration of one runtime change already represented by the declared no_position variant. No claim about unseen errors, statistical error rates, semantic equivalence, model quality, or end-to-end speed.",
    }
    result["total_demo_seconds_within_main"] = time.perf_counter() - begin
    if not all(checks.values()):
        raise AssertionError(json.dumps(checks, sort_keys=True))
    output = args.output or args.study / "runtime_pipeline_check.json"
    study.write_json(output, result)
    print(json.dumps({"output": str(output), "checks": checks,
                      "changed_predictions": result["changed_predictions_against_cached_healthy"],
                      "prediction_count": selected.numel(), "forward_calls": len(selected) // 16}))


if __name__ == "__main__":
    main()
