#!/usr/bin/env python3
"""Check one trusted byte-transformer checkpoint against cached golden outputs.

    python scripts/check_checkpoint_smoke.py --checkpoint PATH/checkpoint.pt \
      --source-dir PATH/wikitext2 --reference-seed 1002 --output smoke.json

Only selected complete contexts are forwarded. Exact equality is a regression
smoke test, not semantic equivalence or a statement about predictive quality.
Nonzero exit status means observed output drift against the selected reference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import confirm_checkpoint_panels as study


def select_prediction_bytes(full_bytes, block_ids, block_windows=64, context_length=64):
    """Keep complete chronological output blocks; reject malformed references."""
    size = block_windows * context_length
    if len(full_bytes) != 8 * size:
        raise ValueError("golden reference must contain exactly eight complete blocks")
    ids = list(block_ids)
    if len(set(ids)) != len(ids) or any(isinstance(b, bool) or not isinstance(b, int) or not 0 <= b < 8 for b in ids):
        raise ValueError("panel IDs must be distinct integers in0..7")
    return b"".join(full_bytes[b * size:(b + 1) * size] for b in ids)


def compare_bytes(actual, golden):
    if len(actual) != len(golden):
        raise ValueError("candidate and golden output lengths differ")
    changed = [i for i, (a, b) in enumerate(zip(actual, golden)) if a != b]
    return {"unchanged": not changed, "changed_prediction_count": len(changed),
            "total_prediction_count": len(actual), "changed_prediction_indices": changed,
            "candidate_output_sha256": hashlib.sha256(actual).hexdigest(),
            "golden_output_sha256": hashlib.sha256(golden).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True, help="trusted training-engine checkpoint")
    parser.add_argument("--source-dir", type=Path, required=True, help="pinned WikiText parquet cache")
    parser.add_argument("--reference-seed", type=int, choices=(1000, 1001, 1002), default=1002)
    parser.add_argument("--study", type=Path, default=ROOT / "applications/training_lab/results/checkpoint_confirmation")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    begin = time.perf_counter()
    study.setup_torch()
    protocol_path, panel_path = args.study / "protocol.json", args.study / "frozen_panel.json"
    protocol, panel = json.loads(protocol_path.read_text()), json.loads(panel_path.read_text())
    audit = json.loads((args.study / "audit.json").read_text())
    if study.digest(protocol_path) != panel["protocol_sha256"] or study.digest(panel_path) != audit["frozen_panel_sha256_before_audit"]:
        raise ValueError("frozen study identity mismatch")
    report_name = "heldout_checkpoint_new_text" if args.reference_seed == 1002 else "new_text_known_checkpoints"
    catalog = audit["reports"][report_name]["prediction_hex"]
    reference_id = f"seed_{args.reference_seed}/healthy"
    golden = select_prediction_bytes(bytes.fromhex(catalog[reference_id]), panel["selected_blocks"])
    full_windows, source = study.source_windows(args.source_dir, "test")
    if source != protocol["sources"]["test"]:
        raise ValueError("deployment input contexts differ from golden reference")
    indices = [j for b in panel["selected_blocks"] for j in range(b * 64, (b + 1) * 64)]
    selected = full_windows[indices].clone()
    model = study.load_model(args.checkpoint)
    setup_seconds = time.perf_counter() - begin
    inference_start = time.perf_counter()
    outputs = study.predict(model, selected)
    inference_seconds = time.perf_counter() - inference_start
    raw = bytes(outputs.flatten().tolist())
    comparison = compare_bytes(raw, golden)
    matching_catalog_states = [cid for cid, encoded in catalog.items()
                               if select_prediction_bytes(bytes.fromhex(encoded), panel["selected_blocks"]) == raw]
    result = {"schema": "singularity.checkpoint-smoke-check/1", "checkpoint_sha256": study.digest(args.checkpoint),
              "protocol_sha256": study.digest(protocol_path), "frozen_panel_sha256": study.digest(panel_path),
              "reference_id": reference_id, "selected_blocks": panel["selected_blocks"],
              "context_length": 64, "batch_shape": [16, 64], "forward_calls": len(selected) // 16,
              "forwarded_input_tokens": selected.numel(), "full_reference_input_tokens": full_windows.numel(),
              "known_catalog_states_with_identical_selected_outputs": matching_catalog_states,
              "setup_seconds_including_import_source_load_checkpoint_load": setup_seconds,
              "resident_prediction_seconds": inference_seconds, **comparison,
              "claim_boundary": "Exact selected-output comparison only. Unchanged does not establish semantic equivalence, predictive quality, no probability drift, or absence of unseen regressions. Golden predictions are cached; reference model is not forwarded."}
    result["total_check_seconds_within_main"] = time.perf_counter() - begin
    if args.output:
        study.write_json(args.output, result)
        print(json.dumps({k: v for k, v in result.items() if k != "changed_prediction_indices"}))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if comparison["unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
