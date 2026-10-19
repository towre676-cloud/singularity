#!/usr/bin/env python3
"""Post-calibration repair: freeze an eager-only INT8 execution contract.

The original prospective INT8 study failed its declared clean-stability rule
when SDPA changed non-tie outputs. That failure is retained. This separate
profile keeps the original probes, faults, tolerances and comparators, and
narrows the approved backend before any new forwards. It is explicitly a
post-calibration repair, not another independent prospective confirmation.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("frozen_deployment_producer_for_int8_contract", ROOT / "scripts/confirm_deployment_audit.py")
STUDY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STUDY)
PARENT = ROOT / "applications/training_lab/results/deployment_audit/smollm2-360m/dynamic_int8"
BASE_PROTOCOL = copy.deepcopy(STUDY.PROTOCOL)
BASE_DEPENDENCIES = STUDY.dependencies


def repaired_protocol(parent_protocol_sha256, parent_failure_sha256):
    value = copy.deepcopy(BASE_PROTOCOL)
    value.update({
        "schema": "singularity.deployment-audit-protocol/1",
        "status": "POST-CALIBRATION eager-only INT8 contract repair; original SDPA calibration failure retained",
        "parent_protocol_file_sha256": parent_protocol_sha256,
        "parent_calibration_failure_file_sha256": parent_failure_sha256,
        "repair_scope": "No probe, fault, tolerance, requirement, comparator or numerical-observation changes. Eager batch-one/full-prefill backend only; select no policy from new observations.",
        "approved_int8_execution": {"attention_backends": ["eager"], "batch_size": 1, "cache_execution": "full prefill"},
        "dynamic_int8_clean_policy": "eager batch-one full prefill calibrated at threads1 and2 against threads4; SDPA, batch3 and cache chunking remain clean transfer measurements outside this approved envelope",
    })
    value["calibration"]["dynamic_int8"] = [{"attention_backend": "eager", "batch_size": 1, "threads": 1},
                                              {"attention_backend": "eager", "batch_size": 1, "threads": 2}]
    value["clean_heldout"]["sdpa_batch1_threads2_reverse"] = {"attention_backend": "sdpa", "batch_size": 1, "threads": 2, "reverse": True}
    return value


def configure():
    protocol = PARENT / "protocol.json"
    failure = PARENT / "calibration_failure.json"
    if not protocol.is_file() or not failure.is_file():
        raise ValueError("restore the retained original protocol and calibration failure before freezing the repaired profile")
    parent = json.loads(protocol.read_text())
    if parent["target"] != "dynamic_int8" or parent["protocol"] != BASE_PROTOCOL:
        raise ValueError("original failure does not belong to the expected frozen INT8 protocol")
    failed = json.loads(failure.read_text())
    if not failed.get("reference") or not failed.get("calibration") or "reference unstable" not in failed["error"]:
        raise ValueError("expected retained non-tie calibration-instability evidence")
    STUDY.PROTOCOL = repaired_protocol(STUDY.file_digest(protocol), STUDY.file_digest(failure))
    def dependencies():
        return {**BASE_DEPENDENCIES(), "scripts/confirm_int8_contract.py": STUDY.file_digest(Path(__file__))}
    STUDY.dependencies = dependencies


def envelope_metadata(protocol):
    return {"calibration_envelope": copy.deepcopy(protocol["approved_int8_execution"]),
            "post_calibration_refinement": True,
            "original_protocol_file_sha256": protocol["parent_protocol_file_sha256"],
            "original_failure_file_sha256": protocol["parent_calibration_failure_file_sha256"]}


def run(args):
    # The frozen producer imports this public factory at run entry. Add the
    # predeclared envelope before package creation, digesting and all timings.
    import singularity.model_audit as api
    original = api.build_package
    def contracted_package(*positional, **settings):
        settings["metadata"] = {**settings.get("metadata", {}), **envelope_metadata(STUDY.PROTOCOL)}
        return original(*positional, **settings)
    api.build_package = contracted_package
    try:
        return STUDY.run(args)
    finally:
        api.build_package = original


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "run"))
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--target", choices=("dynamic_int8",), default="dynamic_int8")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--threads", type=int, choices=(4,), default=4)
    args = parser.parse_args()
    configure()
    result = {"freeze": STUDY.freeze, "run": run}[args.phase](args)
    print(json.dumps(result, indent=1, default=str)[:8000])


if __name__ == "__main__":
    main()
