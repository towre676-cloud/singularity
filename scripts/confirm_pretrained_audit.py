#!/usr/bin/env python3
"""Frozen, local-only behavioral audits of downloaded pretrained causal models.

Run ``freeze`` before ``run``; ``freeze`` loads only the tokenizer and hashes
the pinned local snapshot, never executes the model. ``run`` constructs a
minimum-cost two-witness panel and then measures excluded fault variants.
``cli`` separately checks the package in a fresh process, avoiding two large
resident models. No weight training or test-driven probe revision occurs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
MAX_CONTEXT = 96
REQUIREMENT = 2

# These texts and settings are declared independently of model observations.
# Mixed-feature probes are intentional; selection must pay their actual
# tokenizer-specific forwarded length, including every padding position.
PROBE_TEXTS = [
    ("plain_city", "The city was founded near a river and became an important trading centre.", None),
    ("plain_science", "A polynomial is a linear combination of its basis functions.", None),
    ("pad48_history", "After the war ended, the town was rebuilt.", 48),
    ("pad64_science", "The experiment measured temperature and pressure.", 64),
    ("pad96_code", "def square(x):\n    return x * x\n", 96),
    ("pad80_unicode", "Caf\u00e9 owners read the \ufb01nal r\u00e9sum\u00e9: \u00bd of 2\u00b3.", 80),
    ("unicode_ligature", "The \ufb01nal score was \u00bd point; the \ufb02oor area was 2\u00b3 square metres.", None),
    ("unicode_accents", "A na\u00efve visitor ordered caf\u00e9 in Montr\u00e9al and S\u00e3o Paulo.", None),
    ("newline_list", "Results:\n1. First observation\n2. Second observation\n3. Third observation\n", None),
    ("newline_code", "def evaluate(coefficients, x):\n    total = 0\n    for c in reversed(coefficients):\n        total = total * x + c\n    return total\n", None),
    ("long_reference", "An observation is useful when it distinguishes possible explanations. " * 12, None),
    ("long_code", "values = [2, -1, 3]\nfor index, value in enumerate(values):\n    print(index, value)\n" * 5, None),
    ("long_unicode", "The caf\u00e9 recorded its \ufb01nal r\u00e9sum\u00e9: \u00bd of 2\u00b3. " * 12, None),
    ("long_unicode_newline", "= Caf\u00e9 report =\nThe \ufb01nal r\u00e9sum\u00e9 records \u00bd of 2\u00b3.\n" * 10, 96),
    ("long_accent_newline", "Caf\u00e9 in Montr\u00e9al\nA na\u00efve r\u00e9sum\u00e9 from S\u00e3o Paulo.\n" * 10, 96),
    ("pad96_unicode_newline", "= Caf\u00e9 =\nThe \ufb01nal r\u00e9sum\u00e9 costs \u00bd of 2\u00b3.\n", 96),
    ("pad64_unicode_newline", "Caf\u00e9 \ufb01nal:\nA na\u00efve r\u00e9sum\u00e9.\n", 64),
    ("pad48_unicode_newline", "\ufb01nal caf\u00e9:\n\u00bd of 2\u00b3.\n", 48),
]

CONSTRUCTION_FAULTS = {
    "padding_mask_dropped": {"pass_attention_mask": False},
    "position_ids_all_zero": {"zero_positions": True},
    "truncate_48": {"truncate_to": 48},
    "unicode_nfkc": {"normalization": "NFKC"},
    "temperature_1.3": {"temperature": 1.3},
}
HELDOUT_FAULTS = {
    "crlf_newlines": {"newline": "\r\n"},
    "unicode_nfd": {"normalization": "NFD"},
    "temperature_1.1": {"temperature": 1.1},
    "truncate_64": {"truncate_to": 64},
    # A constant RoPE translation can be invariant. It is measured, never
    # required to produce a detection or silently relabelled a success.
    "left_pad_absolute_positions": {"position_correction": False},
}
PROTOCOL = {
    "schema": "singularity.pretrained-audit-protocol/1",
    "probes": [{"id": i, "text": t, "pad_to": p} for i, t, p in PROBE_TEXTS],
    "max_context": MAX_CONTEXT,
    "cost": "forwarded tokenizer tokens, including explicit left padding; keep final 96 tokens",
    "observations": "all real teacher-forced positions: argmax, top log probability, top-two gap, entropy",
    "construction_faults": CONSTRUCTION_FAULTS,
    "heldout_faults": HELDOUT_FAULTS,
    "clean_calibration": ["same batch size, one CPU thread", "batch size two, configured CPU threads"],
    "clean_audit": ["reverse probe order", "two CPU threads"],
    "tolerance": {"factor": 4., "floor": 1e-5, "tie_margin": 1e-3},
    "requirement": REQUIREMENT,
    "selection": "exact and matched greedy on construction faults with at least two pool witnesses; enumerate every subset independently",
    "unavailable_distinctions": "retain every fault in reports; fewer than two pool witnesses means excluded from robust guarantee, never counted as robust",
    "fault_execution": "only pipeline settings change; all faulty adapters silently declare the original healthy contract",
    "timing": {"pairs": 3, "order_seed": 12871, "warmup_pairs": 1},
    "model_execution": {"device": "cpu", "dtype": "frozen per model: float32 or bfloat16", "cache": False, "batch_size": 1,
                        "local_files_only": True, "trust_remote_code": False},
    "claim_boundary": "Per-model construction-table guarantee only. Held-out faults and clean controls are empirical; no quality, safety, equivalence or unseen-fault guarantee.",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=1, sort_keys=True, allow_nan=False) + "\n")
    os.replace(temporary, path)


def dependencies():
    return {name: file_digest(ROOT / name) for name in (
        "scripts/confirm_pretrained_audit.py", "src/singularity/model_audit/core.py",
        "src/singularity/model_audit/adapters.py", "src/singularity/model_audit/__main__.py",
        "src/singularity/robust_coverage.py")}


def snapshot_manifest(model_path):
    """Hash all model/tokenizer artifacts; ignore download bookkeeping."""
    suffixes = {".json", ".safetensors", ".bin", ".model", ".txt", ".tiktoken"}
    paths = sorted(p for p in Path(model_path).rglob("*")
                   if p.is_file() and ".cache" not in p.parts and p.suffix in suffixes)
    if not paths or not any(p.suffix in {".safetensors", ".bin"} for p in paths):
        raise ValueError("local snapshot has no model weights")
    return {str(p.relative_to(model_path)): {"bytes": p.stat().st_size, "sha256": file_digest(p)} for p in paths}


def probes_for(tokenizer):
    probes = []
    for identifier, text, pad_to in PROBE_TEXTS:
        tokens = tokenizer(text, add_special_tokens=False)["input_ids"][-MAX_CONTEXT:]
        if not tokens:
            raise ValueError("empty probe: " + identifier)
        probe = {"id": identifier, "text": text, "cost": max(len(tokens), pad_to or 0)}
        if pad_to is not None:
            probe["pad_to"] = pad_to
        probes.append(probe)
    return probes


def freeze(args):
    from transformers import AutoTokenizer
    output = args.output / "protocol.json"
    if output.exists():
        raise FileExistsError("protocol already frozen; use a new output directory for a distinct experiment")
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False)
    record = {"protocol": PROTOCOL, "protocol_sha256": digest(PROTOCOL),
              "model_id": args.model_id, "revision": args.revision,
              "snapshot_manifest": snapshot_manifest(args.model_path),
              "probes": probes_for(tokenizer), "dependency_sha256": dependencies(),
              "threads": args.threads, "dtype": args.dtype, "observations_before_freeze": False,
              "frozen_at_utc": datetime.now(timezone.utc).isoformat()}
    write_json(output, record)
    return {"phase": "freeze", "protocol_sha256": record["protocol_sha256"],
            "model_id": args.model_id, "revision": args.revision, "probes": len(record["probes"])}


def checked(args):
    record = json.loads((args.output / "protocol.json").read_text())
    if record["protocol_sha256"] != digest(PROTOCOL) or record["dependency_sha256"] != dependencies():
        raise ValueError("protocol or implementation changed after freeze")
    if (record["model_id"], record["revision"], record["threads"], record["dtype"]) != (args.model_id, args.revision, args.threads, args.dtype):
        raise ValueError("model identity, revision, dtype or thread setting changed after freeze")
    if record["snapshot_manifest"] != snapshot_manifest(args.model_path):
        raise ValueError("local model snapshot changed after freeze")
    return record


def independent_minimum(rows, costs, requirement=REQUIREMENT):
    """Standalone subset oracle, independent of the branch-and-bound solver."""
    masks = [sum(1 << e for e, row in enumerate(rows) if row[p]) for p in range(len(rows[0]))]
    best, best_panels = None, []
    for subset in range(1 << len(rows)):
        if all((subset & mask).bit_count() >= requirement for mask in masks):
            cost = sum(c for e, c in enumerate(costs) if subset >> e & 1)
            if best is None or cost < best:
                best, best_panels = cost, [subset]
            elif cost == best:
                best_panels.append(subset)
    return {"subsets": 1 << len(rows), "minimum_cost": best,
            "minimizing_panels": [[e for e in range(len(rows)) if s >> e & 1] for s in best_panels]}


def select_panel(probes, fault_flags):
    """Never pretend an invariant or undercovered fault meets robustness."""
    from singularity.robust_coverage import coverage_problem, greedy_robust_panel, minimum_robust_panel
    counts = {name: sum(values) for name, values in fault_flags.items()}
    eligible = [name for name, count in counts.items() if count >= REQUIREMENT]
    unavailable = {name: count for name, count in counts.items() if count < REQUIREMENT}
    if not eligible:
        raise ValueError("no construction distinction has two separating pool probes")
    rows = [[bool(fault_flags[name][e]) for name in eligible] for e in range(len(probes))]
    problem = coverage_problem([p["cost"] for p in probes], rows, [p["id"] for p in probes], eligible)
    exact, greedy = minimum_robust_panel(problem, REQUIREMENT), greedy_robust_panel(problem, REQUIREMENT)
    oracle = independent_minimum(rows, [p["cost"] for p in probes])
    if oracle["minimum_cost"] != exact.cost:
        raise ArithmeticError("independent enumeration disagrees with exact solver")
    return {"eligible_faults": eligible, "unavailable_faults": unavailable, "pool_separator_counts": counts,
            "exact": {"indices": list(exact.panel), "probe_ids": [probes[e]["id"] for e in exact.panel],
                      "cost": int(exact.cost), "nodes": exact.nodes},
            "greedy": {"indices": list(greedy.panel), "probe_ids": [probes[e]["id"] for e in greedy.panel],
                       "cost": int(greedy.cost)}, "independent_enumeration": oracle}


def make_adapter(model, tokenizer, *, threads, contract=None, provenance=None, **change):
    from singularity.model_audit.adapters import HuggingFaceCausalAdapter

    class PretrainedAuditAdapter(HuggingFaceCausalAdapter):
        def encode(self, text):
            return super().encode(text.replace("\n", newline))

        def _positions(self, torch, pads, width):
            positions = super()._positions(torch, pads, width)
            return torch.zeros_like(positions) if zero_positions else positions

    zero_positions = change.pop("zero_positions", False)
    newline = change.pop("newline", "\n")
    settings = {"max_context": MAX_CONTEXT, "use_cache": False, "batch_size": 1, **change}
    adapter = PretrainedAuditAdapter(model, tokenizer, declared_contract=contract, provenance=provenance, **settings)
    # The healthy pipeline has exactly the public HF adapter behavior; retain
    # its name so the stock package-check CLI can independently reconstruct it.
    if contract is None:
        declared = adapter.contract()
        declared["adapter"] = "HuggingFaceCausalAdapter"
        adapter._declared = declared
    return adapter


def run(args):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from singularity.model_audit import (build_package, check_package, deviation, flags,
                                         save_package, tolerances_from_clean, verify_package)

    frozen = checked(args)
    if (args.output / "results.json").exists():
        raise FileExistsError("completed run already exists")
    started = time.perf_counter()
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(args.threads)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(args.model_path, local_files_only=True, low_cpu_mem_usage=True,
                                                trust_remote_code=False, torch_dtype=getattr(torch, args.dtype)).eval()
    model_loaded = time.perf_counter()
    probes = frozen["probes"]
    provenance = {"model_id": args.model_id, "revision": args.revision,
                  "snapshot_manifest_sha256": digest(frozen["snapshot_manifest"])}
    healthy = make_adapter(model, tokenizer, threads=args.threads, provenance=provenance)
    contract = healthy.contract()

    def observe(change, inputs=probes):
        change = dict(change)
        threads = change.pop("threads", args.threads)
        reverse = change.pop("reverse", False)
        previous = torch.get_num_threads()
        torch.set_num_threads(threads)
        try:
            rows = make_adapter(model, tokenizer, threads=threads, contract=contract, **change).observe(
                list(reversed(inputs)) if reverse else inputs)
        finally:
            torch.set_num_threads(previous)
        return list(reversed(rows)) if reverse else rows

    def progress(label):
        print(json.dumps({"model": args.model_id, "stage": label,
                          "elapsed_seconds": time.perf_counter() - started}), flush=True)

    progress("reference")
    reference = observe({})
    progress("clean calibration")
    calibration = [observe({"threads": 1}), observe({"batch_size": 2})]
    spec = PROTOCOL["tolerance"]
    tolerances, maxima = tolerances_from_clean(reference, calibration, spec["factor"], spec["floor"], spec["tie_margin"])

    def compare(rows):
        return [flags(deviation(o, r, spec["tie_margin"]), t) for o, r, t in zip(rows, reference, tolerances)]

    construction = {}
    for name, change in CONSTRUCTION_FAULTS.items():
        progress("construction/" + name)
        construction[name] = observe(change)
    construction_flags = {name: compare(rows) for name, rows in construction.items()}
    selection = select_panel(probes, construction_flags)
    # Freeze selection before even executing excluded fault variants.
    selection_record = {**selection, "frozen_before_heldout_observations": True,
                        "protocol_sha256": frozen["protocol_sha256"]}
    write_json(args.output / "frozen_panel.json", selection_record)
    package = build_package(probes, reference, calibration,
                            {name: construction[name] for name in selection["eligible_faults"]},
                            contract=contract, requirement=REQUIREMENT,
                            tolerance_factor=spec["factor"], tolerance_floor=spec["floor"], tie_margin=spec["tie_margin"],
                            panel_ids=selection["exact"]["probe_ids"],
                            metadata={"model_id": args.model_id, "revision": args.revision,
                                      "snapshot_manifest_sha256": digest(frozen["snapshot_manifest"]),
                                      "protocol_sha256": frozen["protocol_sha256"],
                                      "unavailable_faults": selection["unavailable_faults"]})
    save_package(package, args.output / "package.json")
    heldout = {}
    for name, change in HELDOUT_FAULTS.items():
        progress("heldout/" + name)
        heldout[name] = observe(change)
    clean = {}
    for name, change in {"reversed_order": {"reverse": True}, "threads_2": {"threads": 2}}.items():
        progress("clean audit/" + name)
        clean[name] = observe(change)
    observations = {**construction, **heldout}
    all_flags = {name: compare(rows) for name, rows in observations.items()}
    clean_flags = {name: compare(rows) for name, rows in clean.items()}
    panel_reports = {}
    for label in ("exact", "greedy"):
        members = selection[label]["indices"]
        panel_reports[label] = {"probe_ids": selection[label]["probe_ids"], "cost": selection[label]["cost"],
            "faults": {name: {"separating_probes": sum(values[e] for e in members),
                               "detected": any(values[e] for e in members),
                               "robust": sum(values[e] for e in members) >= REQUIREMENT,
                               "heldout": name in HELDOUT_FAULTS} for name, values in all_flags.items()},
            "clean_false_alarms": {name: [probes[e]["id"] for e in members if values[e]] for name, values in clean_flags.items()}}
    index = {p["id"]: e for e, p in enumerate(probes)}

    def recorded(rows):
        return lambda inputs: [rows[index[p["id"]]] for p in inputs]

    missing = {}
    for probe in package["probes"]:
        report = check_package(package, recorded(reference), contract, missing=[probe["id"]])
        missing[probe["id"]] = report["construction_faults_still_separated"]
    resident = check_package(package, healthy.observe, contract)
    probability_resident = check_package(package, lambda inputs: observe({"temperature": 1.1}, inputs), contract)
    recorded_checks = {name: {k: v for k, v in check_package(package, recorded(rows), contract).items() if k != "probes"}
                       for name, rows in observations.items()}
    # Isolate timing from construction and store every interleaved pair.
    progress("resident timing")
    healthy.observe(probes)
    check_package(package, healthy.observe, contract)
    rng, timings = random.Random(PROTOCOL["timing"]["order_seed"]), []
    for repeat in range(PROTOCOL["timing"]["pairs"]):
        order = ["full_pool", "panel_check"]
        rng.shuffle(order)
        record = {"repeat": repeat, "order": order}
        for label in order:
            t0 = time.perf_counter()
            if label == "full_pool":
                healthy.observe(probes)
            else:
                check_package(package, healthy.observe, contract)
            record[label] = time.perf_counter() - t0
        timings.append(record)
    medians = {label: statistics.median(row[label] for row in timings) for label in ("full_pool", "panel_check")}
    result = {"schema": "singularity.pretrained-audit-results/1", "model_id": args.model_id,
              "revision": args.revision, "parameters": sum(p.numel() for p in model.parameters()),
              "protocol_sha256": frozen["protocol_sha256"], "frozen_panel_sha256": file_digest(args.output / "frozen_panel.json"),
              "selection": selection, "panels": panel_reports,
              "pool_separator_counts": {name: sum(values) for name, values in all_flags.items()},
              "pool_clean_false_alarms": {name: [p["id"] for p, flag in zip(probes, values) if flag] for name, values in clean_flags.items()},
              "full_pool_cost": sum(p["cost"] for p in probes), "package_verification": verify_package(package),
              "clean_resident_check": {k: v for k, v in resident.items() if k != "probes"},
              "temperature_resident_check": {k: v for k, v in probability_resident.items() if k != "probes"},
              "package_checks_from_retained_observations": recorded_checks,
              "all_single_probe_erasures": missing,
              "temperature_1.1_preserves_all_argmax": all(a["argmax"] == b["argmax"] for a, b in zip(heldout["temperature_1.1"], reference)),
              "timing": {"pairs": timings, "median_seconds": medians,
                         "speed_ratio_full_over_panel": medians["full_pool"] / medians["panel_check"],
                         "panel_includes": "package verification, observation, comparison", "full_pool_includes": "observation only"},
              "environment": {"torch": torch.__version__, "transformers": transformers.__version__,
                              "threads": args.threads, "device": "cpu", "dtype": args.dtype},
              "seconds": {"load": model_loaded - started, "total": time.perf_counter() - started}}
    write_json(args.output / "observations.json", {"reference": reference, "calibration": calibration,
               "tolerances": tolerances, "calibration_maxima": maxima, "construction": construction,
               "heldout": heldout, "clean_audit": clean})
    write_json(args.output / "results.json", result)
    return result


def cli_check(args):
    checked(args)
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "OMP_NUM_THREADS": str(args.threads),
           "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    started = time.perf_counter()
    completed = subprocess.run([sys.executable, "-m", "singularity.model_audit", "check",
                                str(args.output / "package.json"), "--hf-model", str(args.model_path)],
                               env=env, capture_output=True, text=True)
    record = {"exit_code": completed.returncode, "process_wall_seconds": time.perf_counter() - started,
              "report": json.loads(completed.stdout) if completed.stdout.strip() else None,
              "stderr": completed.stderr[-8000:]}
    write_json(args.output / "cli_check.json", record)
    if completed.returncode != 0:
        raise RuntimeError("fresh-process package check failed; see cli_check.json")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "run", "cli"))
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", required=True, help="immutable upstream commit id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--dtype", choices=("float32", "bfloat16"), default="float32")
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("threads must be positive")
    result = {"freeze": freeze, "run": run, "cli": cli_check}[args.phase](args)
    print(json.dumps(result, indent=1, default=str)[:8000])


if __name__ == "__main__":
    main()
