#!/usr/bin/env python3
"""Prospectively frozen, local-only serialization/backend/INT8 audit study.

Each numerical representation has its own reference and package: quantization
is an approved representation change, not an assumption of FP32 equivalence.
The adapter is unchanged; executed faults live in a separate deployment service.
Saved artifacts remain outside the repository; published manifests bind them.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import sys
import time
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from confirm_pretrained_audit import canonical, digest, file_digest, probes_for, snapshot_manifest, select_panel, write_json

CONSTRUCTION = {
    "service_mask_shift_right": {"mask_shift": 1},
    "service_position_ids_zero": {"positions_zero": True},
    "service_truncate48": {"truncate": 48},
    "service_unicode_nfkc": {"normalization": "NFKC"},
    "service_logit_scale_1.3": {"temperature": 1.3},
    "service_cache_prefix_dropped_half": {"cache_split": 0.5, "drop_cache": True},
}
HELDOUT = {
    "service_dropped_mask": {"drop_mask": True},
    "service_crlf": {"newline": "\r\n"},
    "service_unicode_nfd": {"normalization": "NFD"},
    "service_truncate64": {"truncate": 64},
    "service_logit_scale_1.1": {"temperature": 1.1},
    "service_output_vocabulary_rolled": {"roll_vocabulary": True},
    "service_cache_prefix_dropped_third": {"cache_split": 1/3, "drop_cache": True},
}
PROTOCOL = {
    "schema": "singularity.deployment-audit-protocol/1",
    "status": "prospective deployment extension of the published 0.9 probe pool",
    "pool": "the 18 unchanged confirm_pretrained_audit.py texts, context96; native-token costs include padding",
    "targets": ["float32", "dynamic_int8"],
    "serialization": "FP32 save_pretrained safetensors then reload; additionally trace/save/reload a no-cache eager TorchScript graph and test as heldout clean execution; INT8 Linear state_dict torch.save then weights_only reload into independently reconstructed quantized model",
    "target_policy": "each target has its own contract, baseline, tolerances and panel; no INT8 versus FP32 equivalence claim",
    "reference": {"attention_backend": "eager", "batch_size": 1},
    "calibration": {"float32": [{"attention_backend": "sdpa", "batch_size": 2}, {"attention_backend": "eager", "threads": 1},
                                  {"change": {"cache_split": 0.5}, "attention_backend": "eager", "batch_size": 1}],
                    "dynamic_int8": [{"attention_backend": "sdpa", "batch_size": 1}, {"attention_backend": "eager", "threads": 1}]},
    "clean_heldout": {"sdpa_batch3_threads2_reverse": {"attention_backend": "sdpa", "batch_size": 3, "threads": 2, "reverse": True},
                      "eager_batch3_threads2_reverse": {"attention_backend": "eager", "batch_size": 3, "threads": 2, "reverse": True},
                      "eager_cache_third_threads2": {"change": {"cache_split": 1/3}, "attention_backend": "eager", "threads": 2},
                      "eager_batch1_threads2_reverse": {"attention_backend": "eager", "batch_size": 1, "threads": 2, "reverse": True},
                      "torchscript_batch3_threads2_reverse": {"attention_backend": "torchscript", "batch_size": 3, "threads": 2, "reverse": True}},
    "graph_scope": "FP32 only: actual traced/saved/reloaded CPU eager Llama graph, no cache, shape bound batch1..3/width1..96; excluded from INT8 controls",
    "dynamic_int8_clean_policy": "activation quantization depends on batch/chunk extent; calibrate only batch1 full prefill; independent batch3 and cache controls are explicitly outside calibrated execution envelope and may flag",
    "construction_faults": CONSTRUCTION, "heldout_faults": HELDOUT,
    "fault_location": "deployment service preprocessing/forward, outside unchanged TorchCallableAdapter; intentionally injected synthetic pipeline errors",
    "tolerance": {"factor": 4., "floor": 1e-5, "tie_margin": 1e-3},
    "instability": "any non-tie discrete change in a clean calibration is a reported failure, never silently widen tolerance",
    "selection": {"requirement": 2, "exact_oracle": "all 2^18 subsets", "greedy": "cost-per-new-witness greedy followed by exhaustive optimal pruning of its output",
                  "random": "64 seeded random permutations, stop when same two-witness requirements met, then exhaustively optimally prune each prefix; retain all costs; time lower median-cost representative", "seed": 18273},
    "timing": {"pairs": 3, "order_seed": 77213, "warmup_rounds": 1,
               "arms": ["full_pool", "exact", "pruned_greedy", "random_median"],
               "construction_cost": "reference+all calibration+construction fault forwards+selection+package creation; excluded heldout/timing; include separately report load/serialization",
               "amortization": "ceil(construction_seconds/(median_full_seconds-median_panel_check_seconds)); package checks include verification and comparison; no generation/training speed claim"},
    "execution": {"device": "cpu", "dtype": "float32", "cache": False, "local_only": True, "trust_remote_code": False},
    "scope": "two-witness guarantee applies only to retained construction observations; unseen faults and clean cases are empirical; passing is not behavioral equivalence",
}


def dependencies():
    return {name: file_digest(ROOT / name) for name in (
        "scripts/confirm_deployment_audit.py", "scripts/confirm_pretrained_audit.py",
        "src/singularity/model_audit/core.py", "src/singularity/model_audit/adapters.py",
        "src/singularity/model_audit/exported.py", "src/singularity/robust_coverage.py")}


def freeze(args):
    from transformers import AutoTokenizer
    path = args.output / "protocol.json"
    if path.exists():
        raise FileExistsError("protocol already frozen")
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False)
    record = {"protocol": PROTOCOL, "protocol_sha256": digest(PROTOCOL), "dependency_sha256": dependencies(),
              "model_id": args.model_id, "revision": args.revision, "target": args.target, "threads": args.threads,
              "snapshot_manifest": snapshot_manifest(args.model_path), "probes": probes_for(tokenizer),
              "observations_before_freeze": False, "frozen_at_utc": datetime.now(timezone.utc).isoformat()}
    write_json(path, record)
    return {"frozen": str(path), "protocol_sha256": digest(PROTOCOL), "target": args.target}


def checked(args):
    record = json.loads((args.output / "protocol.json").read_text())
    if record["protocol_sha256"] != digest(PROTOCOL) or record["dependency_sha256"] != dependencies():
        raise ValueError("protocol or implementation changed since freeze")
    if (record["model_id"], record["revision"], record["target"], record["threads"]) != (args.model_id, args.revision, args.target, args.threads):
        raise ValueError("frozen execution identity differs")
    if record["snapshot_manifest"] != snapshot_manifest(args.model_path):
        raise ValueError("source snapshot changed")
    return record


def tensor_state_digest(model):
    """Bind every state tensor, packed quantized tuple, scalar and dtype."""
    import torch
    h = hashlib.sha256()
    def visit(value):
        if isinstance(value, torch.Tensor):
            h.update(str((str(value.dtype), list(value.shape))).encode())
            if value.is_quantized:
                h.update(str((str(value.qscheme()),)).encode())
                if value.qscheme() in (torch.per_tensor_affine, torch.per_tensor_symmetric):
                    h.update(canonical([value.q_scale(), value.q_zero_point()]))
                else:
                    visit(value.q_per_channel_scales()); visit(value.q_per_channel_zero_points())
                    h.update(str(value.q_per_channel_axis()).encode())
                visit(value.int_repr())
            else:
                h.update(value.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes())
        elif isinstance(value, (tuple, list)):
            h.update(type(value).__name__.encode())
            for part in value:
                visit(part)
        else:
            h.update(str((type(value).__name__, value)).encode())
    for key, value in sorted(model.state_dict().items()):
        h.update(key.encode()); visit(value)
    return h.hexdigest()


def load_artifact(args, frozen):
    import torch
    from transformers import AutoModelForCausalLM
    artifact = args.artifacts / args.target
    if artifact.exists():
        raise FileExistsError("use a fresh artifact directory; no stale target reuse")
    artifact.mkdir(parents=True)
    started = time.perf_counter()
    source = AutoModelForCausalLM.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False,
                                                torch_dtype=torch.float32, attn_implementation="eager").eval()
    source_state = tensor_state_digest(source)
    float_parameters = sum(p.numel() for p in source.parameters())
    load_seconds = time.perf_counter() - started
    serialized = time.perf_counter()
    quantized_modules = []
    if args.target == "float32":
        source.save_pretrained(artifact, safe_serialization=True, max_shard_size="2GB")
        expected_state = source_state
        del source
        gc.collect()
        model = AutoModelForCausalLM.from_pretrained(artifact, local_files_only=True, trust_remote_code=False,
                                                   torch_dtype=torch.float32, attn_implementation="eager").eval()
        manifest = snapshot_manifest(artifact)
    else:
        engine = "fbgemm"
        if engine not in torch.backends.quantized.supported_engines:
            raise RuntimeError("declared fbgemm dynamic quantization backend unavailable")
        torch.backends.quantized.engine = engine
        source = torch.ao.quantization.quantize_dynamic(source, {torch.nn.Linear}, dtype=torch.qint8, inplace=True)
        quantized_modules = [name for name, module in source.named_modules()
                             if isinstance(module, torch.ao.nn.quantized.dynamic.Linear)]
        if not quantized_modules:
            raise RuntimeError("target has no dynamically quantized Linear modules")
        expected_state = tensor_state_digest(source)
        torch.save(source.state_dict(), artifact / "quantized_state.pt")
        del source
        gc.collect()
        model = AutoModelForCausalLM.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False,
                                                   torch_dtype=torch.float32, attn_implementation="eager").eval()
        model = torch.ao.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8, inplace=True)
        state = torch.load(artifact / "quantized_state.pt", map_location="cpu", weights_only=True)
        model.load_state_dict(state, strict=True)
        del state
        gc.collect()
        manifest = {"quantized_state.pt": {"bytes": (artifact / "quantized_state.pt").stat().st_size,
                                           "sha256": file_digest(artifact / "quantized_state.pt")}}
    reloaded_state = tensor_state_digest(model)
    if reloaded_state != expected_state:
        raise ArithmeticError("serialization reload changed target state")
    graph_manifest = None
    if args.target == "float32":
        from singularity.model_audit.exported import export_causal_graph
        graph_manifest = export_causal_graph(model, artifact / "causal_graph.pt", max_context=96, max_batch_size=3)
        manifest["causal_graph.pt"] = {"bytes": (artifact / "causal_graph.pt").stat().st_size, "sha256": file_digest(artifact / "causal_graph.pt")}
    return model, {"kind": args.target, "graph_export": args.target == "float32", "graph_manifest": graph_manifest,
                   "source_state_sha256": source_state,
                   "expected_target_state_sha256": expected_state, "reloaded_state_sha256": reloaded_state,
                   "state_reload_identical": True, "float_parameter_count": float_parameters,
                   "quantized_linear_modules": quantized_modules, "quantized_linear_count": len(quantized_modules),
                   "artifacts": manifest, "artifact_manifest_sha256": digest(manifest), "weights_only_load": args.target == "dynamic_int8",
                   "load_seconds": load_seconds, "serialization_conversion_reload_seconds": time.perf_counter() - serialized}


class DeploymentService:
    """Standalone text-to-logit service. The audit adapter does not inject faults."""
    def __init__(self, model, tokenizer, change=None, graph=None):
        self.model, self.tokenizer, self.change = model, tokenizer, dict(change or {})
        self.cache_receipts = []
        self.graph, self.graph_calls = graph, 0

    def encode(self, text):
        change = self.change
        if "newline" in change:
            text = text.replace("\n", change["newline"])
        if "normalization" in change:
            text = unicodedata.normalize(change["normalization"], text)
        tokens = self.tokenizer(text, add_special_tokens=False, padding=False, truncation=False)["input_ids"]
        return tokens[-int(change.get("truncate", 96)):]

    def forward(self, ids, mask, positions):
        import torch
        change = self.change
        if change.get("drop_mask"):
            mask = None
        elif "mask_shift" in change:
            # Off-by-one left-padding boundary in a serving implementation.
            mask = torch.roll(mask, shifts=change["mask_shift"], dims=1)
            mask[:, :change["mask_shift"]] = 0
        if change.get("positions_zero"):
            positions = torch.zeros_like(positions)
        if self.graph is not None:
            if "cache_split" in change:
                raise ValueError("declared graph has no cache support")
            logits = self.graph(ids, mask, positions)
            self.graph_calls += 1
        elif "cache_split" in change:
            split = max(1, min(ids.shape[1]-1, int(ids.shape[1]*change["cache_split"])))
            prefix = self.model(input_ids=ids[:, :split], attention_mask=None if mask is None else mask[:, :split],
                                position_ids=positions[:, :split], use_cache=True, return_dict=True)
            drop = change.get("drop_cache", False)
            self.cache_receipts.append({"prefix_tokens": split, "suffix_tokens": ids.shape[1]-split,
                                        "cache_sequence_length": prefix.past_key_values.get_seq_length(),
                                        "cache_passed_to_suffix": not drop})
            suffix = self.model(input_ids=ids[:, split:], attention_mask=None if mask is None else mask[:, split:] if drop else mask,
                                position_ids=positions[:, split:], past_key_values=None if drop else prefix.past_key_values,
                                use_cache=True, return_dict=True)
            logits = torch.cat((prefix.logits, suffix.logits), dim=1)
        else:
            logits = self.model(input_ids=ids, attention_mask=mask, position_ids=positions,
                                use_cache=False, return_dict=True).logits
        if change.get("roll_vocabulary"):
            logits = torch.roll(logits, shifts=1, dims=-1)
        return logits / float(change.get("temperature", 1.))


def exhaustive_prune(indices, separates, costs, requirement=2):
    best = None
    for subset in range(1 << len(indices)):
        panel = [e for j, e in enumerate(indices) if subset >> j & 1]
        if all(sum(values[e] for e in panel) >= requirement for values in separates.values()):
            item = (sum(costs[e] for e in panel), tuple(panel))
            if best is None or item < best:
                best = item
    if best is None:
        raise ValueError("panel does not meet required coverage")
    return {"cost": best[0], "indices": list(best[1]), "subsets_checked": 1 << len(indices)}


def comparators(probes, construction_flags):
    t0 = time.perf_counter()
    selected = select_panel(probes, construction_flags)
    seconds = {"exact_and_basic_greedy_and_independent_oracle": time.perf_counter()-t0}
    eligible = {k: construction_flags[k] for k in selected["eligible_faults"]}
    costs = [p["cost"] for p in probes]
    t0 = time.perf_counter()
    selected["pruned_greedy"] = exhaustive_prune(selected["greedy"]["indices"], eligible, costs)
    seconds["optimal_pruning_greedy"] = time.perf_counter()-t0
    rng, random_panels = random.Random(PROTOCOL["selection"]["seed"]), []
    t0 = time.perf_counter()
    for trial in range(64):
        order = list(range(len(probes)))
        rng.shuffle(order)
        members = []
        for index in order:
            members.append(index)
            if all(sum(values[e] for e in members) >= 2 for values in eligible.values()):
                break
        pruned = exhaustive_prune(sorted(members), eligible, costs)
        random_panels.append({"trial": trial, **pruned, "unpruned_indices": sorted(members), "unpruned_cost": sum(costs[e] for e in members)})
    seconds["random64_optimal_pruning"] = time.perf_counter()-t0
    ordered = sorted(random_panels, key=lambda row: (row["cost"], row["trial"]))
    selected["random_median"] = dict(ordered[(len(ordered)-1)//2])
    selected["random_panels"] = random_panels
    selected["selection_seconds"] = seconds
    for label in ("pruned_greedy", "random_median"):
        selected[label]["probe_ids"] = [probes[e]["id"] for e in selected[label]["indices"]]
    return selected


def shard_observations(output, observations, probes):
    """Readable bounded-size chunks, with explicit list coordinates and hashes."""
    entries = []
    def save(path, rows):
        chunk, indices = [], []
        def flush():
            if not chunk:
                return
            name = "observations/" + "__".join(map(str, path)) + "__" + str(indices[0]) + ".json"
            value = {"collection": path, "probe_indices": list(indices), "probe_ids": [probes[e]["id"] for e in indices], "rows": list(chunk)}
            write_json(output / name, value)
            size = (output / name).stat().st_size
            if size > 65536:
                raise ValueError("observation chunk exceeds publication budget")
            entries.append({"file": name, "sha256": file_digest(output / name), "bytes": size,
                            "collection": list(path), "probe_indices": list(indices)})
        for index, row in enumerate(rows):
            candidate = {"rows": chunk+[row], "probe_indices": indices+[index], "collection": path,
                         "probe_ids": [probes[e]["id"] for e in indices+[index]]}
            if chunk and len(json.dumps(candidate, indent=1, sort_keys=True).encode()) > 60000:
                flush(); chunk.clear(); indices.clear()
            chunk.append(row); indices.append(index)
        flush()
    for collection, value in observations.items():
        if collection == "calibration":
            for i, rows in enumerate(value):
                save([collection, i], rows)
        elif isinstance(value, dict):
            for name, rows in value.items():
                save([collection, name], rows)
        else:
            save([collection], value)
    write_json(output / "observations_manifest.json", {"schema": "singularity.deployment-observations/1", "probe_count": len(probes),
                                                       "entries": entries, "entries_sha256": digest(entries)})


def run(args):
    import torch
    import transformers
    from transformers import AutoTokenizer
    from singularity.model_audit import build_package, check_package, deviation, flags, save_package, tolerances_from_clean, verify_package
    from singularity.model_audit.adapters import TorchCallableAdapter, tokenizer_fingerprint
    frozen = checked(args)
    if (args.output / "results.json").exists():
        raise FileExistsError("completed experiment already exists")
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(args.threads)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    started = time.perf_counter()
    model, artifact = load_artifact(args, frozen)
    write_json(args.output / "artifact.json", artifact)
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False)
    graph = None
    probes = frozen["probes"]
    identity = {"model_id": args.model_id, "revision": args.revision, "representation": args.target,
                "source_snapshot_sha256": digest(frozen["snapshot_manifest"]),
                "target_artifact_sha256": artifact["artifact_manifest_sha256"], **tokenizer_fingerprint(tokenizer)}
    pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    def adapter(change=None, batch_size=1, graph=None):
        service = DeploymentService(model, tokenizer, change, graph)
        instance = TorchCallableAdapter(service.forward, service.encode, identity=identity, max_context=96,
                                        pad_id=int(pad), use_cache=False, batch_size=batch_size)
        instance._service = service
        return instance
    contract = adapter().contract()
    execution_receipts = []
    def observe(change=None, inputs=probes, *, attention_backend="eager", batch_size=1, threads=None, reverse=False, prove=False):
        from unittest.mock import patch
        nonlocal graph
        previous = torch.get_num_threads()
        torch.set_num_threads(threads or args.threads)
        if attention_backend == "torchscript":
            if args.target != "float32":
                raise ValueError("graph clean control declared for FP32 only")
            if graph is None:
                from singularity.model_audit.exported import load_causal_graph
                graph = load_causal_graph(args.artifacts / args.target / "causal_graph.pt", artifact["graph_manifest"])
        else:
            model.set_attn_implementation(attention_backend)
        instance = adapter(change, batch_size, graph if attention_backend == "torchscript" else None)
        hooks, quantized_calls = [], {}
        if prove:
            for name, module in model.named_modules():
                if isinstance(module, torch.ao.nn.quantized.dynamic.Linear):
                    def hook(_module, _inputs, _output, key=name):
                        quantized_calls[key] = quantized_calls.get(key, 0)+1
                    hooks.append(module.register_forward_hook(hook))
        try:
            ordered = list(reversed(inputs)) if reverse else inputs
            if prove:
                original_sdpa = torch.nn.functional.scaled_dot_product_attention
                with patch("torch.nn.functional.scaled_dot_product_attention", wraps=original_sdpa) as wrapped:
                    rows = instance.observe(ordered)
                sdpa_calls = wrapped.call_count
                if (attention_backend == "sdpa" and not sdpa_calls) or (attention_backend == "eager" and sdpa_calls):
                    raise ArithmeticError("declared attention backend did not execute its expected kernel")
                if args.target == "dynamic_int8" and not quantized_calls:
                    raise ArithmeticError("quantized Linear modules were not executed")
                execution_receipts.append({"attention_backend": attention_backend, "batch_size": batch_size, "threads": threads or args.threads,
                                           "sdpa_calls": sdpa_calls, "quantized_linear_calls": quantized_calls,
                                           "graph_calls": instance._service.graph_calls,
                                           "change": dict(change or {}), "cache": instance._service.cache_receipts})
            else:
                rows = instance.observe(ordered)
            return list(reversed(rows)) if reverse else rows
        finally:
            for hook in hooks:
                hook.remove()
            model.set_attn_implementation("eager")
            torch.set_num_threads(previous)
    def progress(label):
        print(json.dumps({"model": args.model_id, "target": args.target, "stage": label, "seconds": time.perf_counter()-started}), flush=True)
    build_started = time.perf_counter()
    progress("reference")
    reference = observe(prove=True)
    reference_seconds = time.perf_counter()-build_started
    calibration_started = time.perf_counter()
    calibration = [observe(**config, prove=True) for config in PROTOCOL["calibration"][args.target]]
    calibration_seconds = time.perf_counter()-calibration_started
    spec = PROTOCOL["tolerance"]
    try:
        tolerances, maxima = tolerances_from_clean(reference, calibration, **{k: spec[k] for k in ("factor", "floor", "tie_margin")})
    except ValueError as error:
        write_json(args.output / "calibration_failure.json", {"error": str(error), "reference": reference, "calibration": calibration,
                                                              "claim": "no package built; representation failed declared clean-stability rule"})
        raise
    def compare(rows):
        return [flags(deviation(o, r, spec["tie_margin"]), t) for o, r, t in zip(rows, reference, tolerances)]
    construction = {}
    fault_started = time.perf_counter()
    for name, change in CONSTRUCTION.items():
        progress("construction/" + name)
        construction[name] = observe(change)
    construction_fault_seconds = time.perf_counter()-fault_started
    construction_flags = {k: compare(v) for k, v in construction.items()}
    selection_started = time.perf_counter()
    selection = comparators(probes, construction_flags)
    selection_seconds = time.perf_counter()-selection_started
    selection["full_pool"] = {"indices": list(range(len(probes))), "probe_ids": [p["id"] for p in probes], "cost": sum(p["cost"] for p in probes)}
    write_json(args.output / "frozen_panel.json", {**selection, "frozen_before_heldout": True, "protocol_sha256": frozen["protocol_sha256"]})
    packages, package_seconds = {}, {}
    for label in ("exact", "pruned_greedy", "random_median", "full_pool"):
        package_started = time.perf_counter()
        package = build_package(probes, reference, calibration, {k: construction[k] for k in selection["eligible_faults"]},
                                contract=contract, requirement=2, tolerance_factor=spec["factor"], tolerance_floor=spec["floor"],
                                tie_margin=spec["tie_margin"], panel_ids=selection[label]["probe_ids"],
                                metadata={"target": args.target, "protocol_sha256": frozen["protocol_sha256"]})
        save_package(package, args.output / ("package_"+label+".json"))
        packages[label] = package
        package_seconds[label] = time.perf_counter()-package_started
    construction_seconds = time.perf_counter()-build_started
    heldout, clean = {}, {}
    for name, change in HELDOUT.items():
        progress("heldout/" + name)
        heldout[name] = observe(change, prove="cache_split" in change)
    for name, config in PROTOCOL["clean_heldout"].items():
        if config["attention_backend"] == "torchscript" and args.target != "float32":
            continue
        progress("clean/" + name)
        clean[name] = observe(**config, prove=True)
    all_flags = {k: compare(v) for k, v in {**construction, **heldout}.items()}
    clean_flags = {k: compare(v) for k, v in clean.items()}
    index = {p["id"]: e for e, p in enumerate(probes)}
    recorded = lambda rows: lambda inputs: [rows[index[p["id"]]] for p in inputs]
    reports = {}
    for label, package in packages.items():
        members = selection[label]["indices"]
        reports[label] = {"faults": {name: {"separating_probes": sum(values[e] for e in members), "detected": any(values[e] for e in members),
                                          "two_witness": sum(values[e] for e in members) >= 2, "heldout": name in HELDOUT} for name, values in all_flags.items()},
                          "clean_false_alarms": {name: [probes[e]["id"] for e in members if values[e]] for name, values in clean_flags.items()},
                          "verification": verify_package(package),
                          "all_single_probe_erasures": {p["id"]: check_package(package, recorded(reference), contract, missing=[p["id"]])["construction_faults_still_separated"] for p in package["probes"]}}
    progress("timing")
    arms = PROTOCOL["timing"]["arms"]
    def timed(label):
        return check_package(packages[label], lambda inputs: observe(inputs=inputs), contract)
    for label in arms:
        timed(label)
    rng, timings = random.Random(PROTOCOL["timing"]["order_seed"]), []
    for repeat in range(PROTOCOL["timing"]["pairs"]):
        order = list(arms); rng.shuffle(order)
        row = {"repeat": repeat, "order": order}
        for label in order:
            t0 = time.perf_counter(); timed(label); row[label] = time.perf_counter()-t0
        timings.append(row)
    medians = {label: statistics.median(row[label] for row in timings) for label in arms}
    breakeven = {}
    for label in arms[1:]:
        saved = medians["full_pool"]-medians[label]
        incremental = construction_fault_seconds+selection_seconds+package_seconds[label]
        breakeven[label] = {"seconds_saved_per_check": saved,
                            "gross_all_comparators_build_checks": math.ceil(construction_seconds/saved) if saved > 0 else None,
                            "conservative_incremental_build_checks": math.ceil(incremental/saved) if saved > 0 else None,
                            "conservative_incremental_seconds": incremental,
                            "including_artifact_checks": math.ceil((construction_seconds+artifact["load_seconds"]+artifact["serialization_conversion_reload_seconds"])/saved) if saved > 0 else None,
                            "full_pool_over_panel": medians["full_pool"]/medians[label]}
    observations = {"reference": reference, "calibration": calibration, "tolerances": tolerances,
                    "calibration_maxima": maxima, "construction": construction, "heldout": heldout, "clean_heldout": clean}
    shard_observations(args.output, observations, probes)
    result = {"schema": "singularity.deployment-audit-results/1", "model_id": args.model_id, "revision": args.revision,
              "target": args.target, "protocol_sha256": frozen["protocol_sha256"], "artifact": artifact,
              "execution_receipts": execution_receipts,
              "selection": selection, "panels": reports, "full_pool_cost": sum(p["cost"] for p in probes),
              "pool_separator_counts": {k: sum(v) for k, v in all_flags.items()},
              "pool_clean_false_alarms": {k: [p["id"] for p, flag in zip(probes, v) if flag] for k, v in clean_flags.items()},
              "timing": {"pairs": timings, "median_seconds": medians, "amortization": breakeven,
                         "construction_seconds": construction_seconds, "selection_seconds": selection_seconds,
                         "common_reference_seconds": reference_seconds, "common_calibration_seconds": calibration_seconds,
                         "construction_fault_seconds": construction_fault_seconds, "package_seconds": package_seconds,
                         "full_pool_includes": "complete 18-probe package verification, observation and comparison",
                         "incremental_caveat": "conservative: charges all comparator selection work to each panel; common reference+calibration and fullpool package creation excluded"},
              "environment": {"torch": torch.__version__, "transformers": transformers.__version__, "threads": args.threads,
                              "quantization_engine": torch.backends.quantized.engine, "device": "cpu", "dtype": "float32"},
              "total_seconds": time.perf_counter()-started, "scope": PROTOCOL["scope"]}
    write_json(args.output / "results.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "run"))
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--target", choices=PROTOCOL["targets"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("threads must be positive")
    print(json.dumps({"freeze": freeze, "run": run}[args.phase](args), indent=1, default=str)[:8000])


if __name__ == "__main__":
    main()
