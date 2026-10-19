"""Fail-closed CI boundary and model-free replay of deployment evidence.

python -m singularity.model_audit.ci check --help
python -m singularity.model_audit.ci replay ARTIFACT_DIRECTORY
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
import time

from . import (check_package, deviation, flags, package_digest,
               settings_from_contract, verify_package)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("non-finite JSON: " + value)))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def validate_package(package, expected):
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("expected package SHA256 must be a lowercase 64-character canonical package digest")
    if package_digest(package) != expected:
        raise ValueError("reference package does not match the externally pinned digest")
    result = verify_package(package)
    if not result["verified"]:
        raise ValueError("package verification failed: " + "; ".join(result["problems"]))
    probes = package["probes"]
    if len({p["id"] for p in probes}) != len(probes) or not probes:
        raise ValueError("panel ids must be unique and nonempty")
    requirement = package["requirement"]
    if type(requirement) is not int or requirement < 1:
        raise ValueError("invalid coverage requirement")
    for p in probes:
        if not p["tolerance"] or any(type(t) not in (int, float) or not 0 <= t < float("inf")
                                      for t in p["tolerance"].values()):
            raise ValueError("invalid frozen tolerance")
    # Recompute flags from deviations; never trust stored evidence booleans.
    for fault, records in package["fault_evidence"].items():
        for p in probes:
            record = records[p["id"]]
            if record["flags"] != flags(record, p["tolerance"]):
                raise ValueError("inconsistent fault flag: " + fault)
    return result


def verdict(package, report):
    if report["verdict"] != "unchanged":
        return "changed"
    if len(report["missing_probes"]) >= package["requirement"]:
        return "incomplete"
    if not all(report["construction_faults_still_separated"].values()):
        return "incomplete"
    return "pass"


def evaluate(package, observe, contract, missing=()):
    captured = []
    def capture(probes):
        rows = observe(probes)
        captured.extend(rows)
        return rows
    report = check_package(package, capture, contract, missing=missing)
    return report, captured, verdict(package, report)


def hf_adapter(model_path, tokenizer_path, package, execution):
    from .__main__ import _local_hf_provenance
    from .adapters import HuggingFaceCausalAdapter
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    required = set(settings_from_contract(package["contract"])) | {"dtype", "device", "batch_size", "attention_backend"}
    if set(execution) != required:
        raise ValueError("execution JSON must specify exactly: " + ", ".join(sorted(required)))
    settings = settings_from_contract(package["contract"])
    for key, value in settings.items():
        if execution[key] != value:
            raise ValueError("execution setting differs from reference contract: " + key)
    if execution["dtype"] != package["contract"]["dtype"]:
        raise ValueError("execution dtype differs from reference contract")
    if type(execution["batch_size"]) is not int or execution["batch_size"] < 1:
        raise ValueError("batch_size must be a positive integer")
    if execution["attention_backend"] not in ("eager", "sdpa"):
        raise ValueError("attention_backend must be eager or sdpa")
    dtypes = {"torch.float32": torch.float32, "torch.float16": torch.float16, "torch.bfloat16": torch.bfloat16}
    if execution["dtype"] not in dtypes:
        raise ValueError("unsupported dtype")
    if not Path(model_path).is_dir() or not Path(tokenizer_path or model_path).is_dir():
        raise ValueError("CI requires local model and tokenizer directories; acquire pinned snapshots separately")
    declared = package["contract"].get("checkpoint_provenance", {})
    if "snapshot_manifest_sha256" not in declared:
        raise ValueError("CI requires a content-bound snapshot_manifest_sha256 identity")
    provenance = _local_hf_provenance(model_path, declared)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path or model_path, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True, trust_remote_code=False,
                 torch_dtype=dtypes[execution["dtype"]], attn_implementation=execution["attention_backend"])
    model.to(execution["device"])
    return HuggingFaceCausalAdapter(model, tokenizer, provenance=provenance,
                                   batch_size=execution["batch_size"], **settings)


def markdown(result):
    report = result.get("check", {})
    return ("# Singularity deployment audit\n\n"
            f"**Result: {result['status'].upper()}**\n\n"
            f"{result.get('error', report.get('interpretation', 'No model verdict was produced.'))}\n\n"
            f"Package: `{result.get('expected_package_sha256', '')}`\n\n"
            f"Flagged probes: `{report.get('flagged_probes', [])}`. "
            f"Missing probes: `{report.get('missing_probes', [])}`. "
            f"Identity/setting differences: `{report.get('contract_mismatches', [])}`.\n\n"
            "Coverage is limited to the certificate's declared construction faults and frozen tolerances. "
            "A pass is not model equivalence, general quality, safety, or coverage of untested faults. "
            "Expected updates require a separately reviewed reference; CI never refreshes it automatically.\n\n"
            "certificate.json contains the coverage witness; observations.json and report.json permit "
            "model-free replay. Hashes provide integrity, not authentication of research observations.\n")


def run_check(args):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    # Never reuse evidence from a preceding successful invocation.
    for name in ("certificate.json", "observations.json", "execution.json", "report.json", "report.md", "manifest.json"):
        (out / name).unlink(missing_ok=True)
    started = time.perf_counter()
    result = {"schema": "singularity.ci-report/1", "status": "error",
              "expected_package_sha256": args.expected_package_sha256,
              "runtime": {"python": platform.python_version(), "platform": platform.platform()}}
    try:
        package = read_json(args.package)
        result["verification"] = validate_package(package, args.expected_package_sha256)
        write_json(out / "certificate.json", package)
        execution = read_json(args.execution)
        write_json(out / "execution.json", execution)
        adapter = hf_adapter(args.model, args.tokenizer, package, execution)
        loaded = time.perf_counter()
        report, observations, status = evaluate(package, adapter.observe, adapter.contract(), args.missing)
        result.update(status=status, check=report, deployed_contract=adapter.contract())
        result["seconds"] = {"verification_and_load": loaded-started, "selected_probes": time.perf_counter()-loaded}
        import torch, transformers
        result["runtime"].update(torch=torch.__version__, transformers=transformers.__version__)
        write_json(out / "observations.json", observations)
    except Exception as error:
        result.update(status="error", error=f"{type(error).__name__}: {error}")
    result["total_seconds"] = time.perf_counter() - started
    write_json(out / "report.json", result)
    (out / "report.md").write_text(markdown(result), encoding="utf-8")
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()
                if p.name in {"certificate.json", "observations.json", "execution.json", "report.json", "report.md"}}
    write_json(out / "manifest.json", manifest)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write(markdown(result))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write("verdict=" + result["status"] + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


def replay(directory, expected):
    root = Path(directory)
    package = read_json(root / "certificate.json")
    validate_package(package, expected)
    result = read_json(root / "report.json")
    observations = read_json(root / "observations.json")
    report, _, status = evaluate(package, lambda probes: observations, result["deployed_contract"],
                                  result["check"]["missing_probes"])
    if report != result["check"] or status != result["status"] or result["expected_package_sha256"] != expected:
        raise ValueError("deployment evidence does not replay")
    return {"replayed": True, "status": status,
            "boundary": "Replays stored observations; does not authenticate their origin or prove model execution."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    for option in ("package", "model", "execution", "expected-package-sha256", "output"):
        check.add_argument("--" + option, required=True)
    check.add_argument("--tokenizer")
    check.add_argument("--missing", nargs="*", default=[])
    verify = sub.add_parser("replay")
    verify.add_argument("directory")
    verify.add_argument("--expected-package-sha256", required=True)
    args = parser.parse_args(argv)
    if args.command == "check":
        return run_check(args)
    try:
        print(json.dumps(replay(args.directory, args.expected_package_sha256), indent=2))
        return 0
    except Exception as error:
        print(json.dumps({"replayed": False, "error": str(error)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
