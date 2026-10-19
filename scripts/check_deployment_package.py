#!/usr/bin/env python3
"""Check a saved deployment artifact against a Singularity audit package.

The checker loads existing artifacts only: it never selects probes, calibrates
tolerances, retrains weights, or reconstructs the original reference outputs.
Its JSON separates disk/load cost from resident behavioral-check time.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from confirm_deployment_audit import DeploymentService, tensor_state_digest
from confirm_pretrained_audit import digest, file_digest, snapshot_manifest, write_json


def validate_artifact_files(directory, receipt):
    directory = Path(directory)
    manifest = receipt["artifacts"]
    if digest(manifest) != receipt["artifact_manifest_sha256"]:
        raise ValueError("artifact receipt manifest digest mismatch")
    for name, expected in manifest.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("artifact receipt contains a nonlocal path")
        path = directory / relative
        if path.stat().st_size != expected["bytes"] or file_digest(path) != expected["sha256"]:
            raise ValueError("artifact file changed: " + name)


def annotate_envelope(report, representation, batch_size, cache_split_denominator, backend="eager", approved=None):
    """Separate measured drift from an approved-envelope fault classification."""
    approved = approved or {"attention_backends": ["eager"], "batch_size": 1, "cache_execution": "full prefill"}
    inside = representation != "dynamic_int8" or (batch_size == approved["batch_size"] and not cache_split_denominator
                                                  and backend in approved["attention_backends"])
    report["calibration_envelope"] = {
        "status": "inside" if inside else "outside",
        "requested": {"backend": backend, "batch_size": batch_size, "cache_split_denominator": cache_split_denominator},
        "approved_int8_execution": approved,
    }
    if report["contract_mismatches"]:
        report["deployment_status"], report["exit_code"] = "contract_mismatch", 2
    elif not inside:
        report["deployment_status"], report["exit_code"] = "outside_calibration", 3
        report["interpretation"] = ("This execution is outside the calibrated INT8 backend/batch/cache envelope. "
                                    "The raw behavioral verdict measures drift only and does not classify the deployment as faulty.")
    elif report["verdict"] == "unchanged":
        if any(not survives for survives in report.get("construction_faults_still_separated", {}).values()):
            report["deployment_status"], report["exit_code"] = "inconclusive_missing_results", 4
            report["interpretation"] = "Missing probe results remove retained construction coverage; the remaining unchanged observations are inconclusive."
        else:
            report["deployment_status"], report["exit_code"] = "unchanged", 0
    else:
        report["deployment_status"], report["exit_code"] = "behavioral_change", 2
    return report


def check(args):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from singularity.model_audit import check_package, load_package, verify_package
    from singularity.model_audit.adapters import TorchCallableAdapter, tokenizer_fingerprint
    started = time.perf_counter()
    package = load_package(args.package)
    verification = verify_package(package)
    if not verification["verified"]:
        raise ValueError("audit package failed its integrity/coverage check")
    receipt = json.loads(args.artifact_receipt.read_text())
    validate_artifact_files(args.artifacts, receipt)
    declared = package["contract"]
    representation = receipt["kind"]
    if declared["representation"] != representation:
        raise ValueError("artifact representation differs from the package contract")
    source_sha = digest(snapshot_manifest(args.model_path))
    if declared["source_snapshot_sha256"] != source_sha:
        raise ValueError("source snapshot differs from the package contract")
    if declared["target_artifact_sha256"] != receipt["artifact_manifest_sha256"]:
        raise ValueError("deployment artifacts differ from the package contract")
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(args.threads)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False)
    graph, model = None, None
    if args.backend == "torchscript":
        if representation != "float32" or args.cache_split_denominator:
            raise ValueError("the exported graph supports FP32 full prefill only")
        from singularity.model_audit.exported import load_causal_graph
        graph = load_causal_graph(args.artifacts / "causal_graph.pt", receipt["graph_manifest"])
    else:
        location = args.artifacts if representation == "float32" else args.model_path
        model = AutoModelForCausalLM.from_pretrained(location, local_files_only=True, trust_remote_code=False,
                                                   torch_dtype=torch.float32, attn_implementation="eager").eval()
        if representation == "dynamic_int8":
            if "fbgemm" not in torch.backends.quantized.supported_engines:
                raise RuntimeError("the declared fbgemm quantization backend is unavailable")
            torch.backends.quantized.engine = "fbgemm"
            model = torch.ao.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8, inplace=True)
            state = torch.load(args.artifacts / "quantized_state.pt", map_location="cpu", weights_only=True)
            model.load_state_dict(state, strict=True)
            del state
            names = [name for name, module in model.named_modules() if isinstance(module, torch.ao.nn.quantized.dynamic.Linear)]
            if names != receipt["quantized_linear_modules"]:
                raise ValueError("quantized module layout differs from the saved artifact")
        if tensor_state_digest(model) != receipt["reloaded_state_sha256"]:
            raise ValueError("loaded model state differs from its saved artifact")
        model.set_attn_implementation(args.backend)
    identity = {"model_id": declared["model_id"], "revision": declared["revision"], "representation": representation,
                "source_snapshot_sha256": source_sha, "target_artifact_sha256": receipt["artifact_manifest_sha256"],
                **tokenizer_fingerprint(tokenizer)}
    changes = {"cache_split": 1/args.cache_split_denominator} if args.cache_split_denominator else {}
    service = DeploymentService(model, tokenizer, changes, graph)
    pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    adapter = TorchCallableAdapter(service.forward, service.encode, identity=identity, max_context=96,
                                   pad_id=int(pad), use_cache=False, batch_size=args.batch_size)
    ready = time.perf_counter()
    report = check_package(package, adapter.observe, adapter.contract(), missing=args.missing)
    ended = time.perf_counter()
    report["execution"] = {"representation": representation, "backend": args.backend, "threads": args.threads,
                           "batch_size": args.batch_size, "cache_split_denominator": args.cache_split_denominator,
                           "cache_execution": "two chunks, split after 1/N of input" if args.cache_split_denominator else "full prefill",
                           "graph_calls": service.graph_calls, "cache_receipts": service.cache_receipts,
                           "torch": torch.__version__, "transformers": transformers.__version__}
    report["seconds"] = {"artifact_validation_and_load": ready-started, "resident_check": ended-ready, "total": ended-started}
    annotate_envelope(report, representation, args.batch_size, args.cache_split_denominator, args.backend,
                      package.get("metadata", {}).get("calibration_envelope"))
    if args.output:
        write_json(args.output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--model-path", type=Path, required=True, help="original pinned local Hugging Face snapshot")
    parser.add_argument("--artifacts", type=Path, required=True, help="existing float32 or dynamic_int8 artifact directory")
    parser.add_argument("--artifact-receipt", type=Path, required=True, help="artifact.json from the original package build")
    parser.add_argument("--backend", choices=("eager", "sdpa", "torchscript"), default="eager")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--cache-split-denominator", type=int, choices=(2, 3), default=0,
                        help="two cache chunks, split after 1/N of the input")
    parser.add_argument("--missing", action="append", default=[], help="probe identifier unavailable at check time")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.batch_size < 1 or args.threads < 1:
        parser.error("batch size and threads must be positive")
    report = check(args)
    print(json.dumps(report, indent=1, sort_keys=True, allow_nan=False))
    raise SystemExit(report["exit_code"])


if __name__ == "__main__":
    main()
