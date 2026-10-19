#!/usr/bin/env python3
"""Prospective development/holdout study of causal repetition gates.

This is evaluation, not neural training. Freeze source bytes, token IDs, model
files, policies and code before any forward. Execute development, commit its
selection receipt, then execute heldout. No outcome chooses a heldout arm.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from singularity.training.online_blend import _log_mixture, _logsumexp
from singularity.training.repetition_blend import (REPETITION_POLICIES, count_target_probability,
                                                  repetition_feature, gate_enabled)

spec = importlib.util.spec_from_file_location("pretrained_gating_helpers", ROOT / "scripts/confirm_pretrained_prediction.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)

POLICIES = REPETITION_POLICIES
NEURAL_MASS = .95
DEPENDENCIES = ("scripts/confirm_pretrained_gating.py", "scripts/confirm_pretrained_prediction.py",
                "src/singularity/training/online_blend.py", "src/singularity/training/token_experts.py",
                "src/singularity/training/repetition_blend.py", "scripts/report_pretrained_gating.py")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    return helpers.file_sha(path)


def write_json(path, value):
    if len(json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode()) + 1 > 65536:
        raise ValueError("readable evidence file exceeds64KiB; split it before publishing")
    helpers.write_json(path, value)


def now():
    return datetime.now(timezone.utc).isoformat()


def load_json(path):
    return json.loads(Path(path).read_text())


def repo_path(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def portable_path(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def read_encoded(output, entry):
    path = output / entry["encoding_path"]
    if file_sha(path) != entry["encoding_sha256"]:
        raise ValueError("frozen native token IDs changed")
    encoded = load_json(path)
    if encoded["document"] != entry["document"] or sha(canonical(encoded["token_ids"])) != entry["token_ids_sha256"]:
        raise ValueError("frozen token identity mismatch")
    return encoded


def retain_record(output, path, record):
    """Keep source-like target chunks; derive redundant posterior arrays."""
    chunks = []
    for start in range(0, record["targets"], 64):
        chunk_path = path.parent / (path.stem + "_targets") / f"{start:04d}.json"
        write_json(chunk_path, {"target_start": start, "rows": record["target_rows"][start:start + 64]})
        chunks.append({"path": str(chunk_path.relative_to(output)), "sha256": file_sha(chunk_path)})
    replay = replay_rows(record["target_rows"])
    discarded = {"target_rows", "losses_hex", "prior_to_target_count_weights_hex",
                 "hierarchy_prior_to_target_posterior_hex", "ungated_prior_to_target_policy_weight_hex"}
    retained = {key: value for key, value in record.items() if key not in discarded}
    retained.update(target_chunks=chunks, replay_sha256=sha(canonical(replay)))
    write_json(path, retained)


def load_record(output, path):
    record = load_json(path)
    rows = []
    for entry in record["target_chunks"]:
        chunk_path = output / entry["path"]
        if file_sha(chunk_path) != entry["sha256"]:
            raise ValueError("target trace chunk changed")
        chunk = load_json(chunk_path)
        if chunk["target_start"] != len(rows):
            raise ValueError("target chunks reordered")
        rows.extend(chunk["rows"])
    record["target_rows"] = rows
    return record


def gate(policy, feature):
    """Only the longest previously observed context row controls the gate."""
    return gate_enabled(policy, feature)


def count_target_and_feature(counts, target):
    """Scalar Witten--Bell probability and features from the pretarget state.

    The target indexes an already fixed count distribution; it never chooses
    the feature or gate. The feature includes enough state to independently
    rebuild it from the frozen document token IDs.
    """
    feature = repetition_feature(counts)
    return count_target_probability(counts, target), feature


def replay_rows(rows):
    """Replay every declared arm in temporal order, with no future outcomes.

    A gate policy is itself a causal normalized expert: neural when inactive,
    a fixed neural/count mixture when active. Protected arms aggregate this
    expert and pure neural with 95%/5% priors. The hierarchy assigns 95% to
    pure neural and equal shares of the remaining 5% to the eighteen gates.
    """
    components = [0.] * (len(POLICIES) + 1)
    ungated_sum = 0.
    cumulative = {name: [] for name in ("neural", "adaptive_count", "ungated_protected", "hierarchy_protected")}
    cumulative.update({p["id"]: [] for p in POLICIES})
    active = {p["id"]: 0 for p in POLICIES}
    prior = [math.log(NEURAL_MASS)] + [math.log((1 - NEURAL_MASS) / len(POLICIES))] * len(POLICIES)
    previous_protected = {p["id"]: 0. for p in POLICIES}
    previous_hierarchy = previous_ungated = 0.
    weights = {p["id"]: [] for p in POLICIES}
    hierarchy_weights, ungated_weights = [], []
    raw_losses = {p["id"]: [] for p in POLICIES}
    for row in rows:
        neural_log = -float.fromhex(row["neural_nll_hex"])
        count_log = -float.fromhex(row["count_nll_hex"])
        feature = row["feature"]
        cumulative["neural"].append(-neural_log)
        cumulative["adaptive_count"].append(-count_log)
        # Every posterior is formed from the previous prefix, before this
        # row's target likelihood enters any component accumulator.
        hierarchy_before = _logsumexp([pi + ll for pi, ll in zip(prior, components)])
        hierarchy_weights.append([math.exp(pi + ll - hierarchy_before) for pi, ll in zip(prior, components)])
        ungated_before = _logsumexp((math.log(NEURAL_MASS) + components[0], math.log1p(-NEURAL_MASS) + ungated_sum))
        ungated_weights.append(math.exp(math.log1p(-NEURAL_MASS) + ungated_sum - ungated_before))
        for index, policy in enumerate(POLICIES, 1):
            enabled = gate(policy, feature)
            alpha = policy["alpha"] if enabled else 0.
            policy_log = _log_mixture(neural_log, count_log, alpha)
            raw_losses[policy["id"]].append(-policy_log)
            active[policy["id"]] += int(enabled)
            before = _logsumexp((math.log(NEURAL_MASS) + components[0], math.log1p(-NEURAL_MASS) + components[index]))
            weights[policy["id"]].append(math.exp(math.log1p(-NEURAL_MASS) + components[index] - before) * alpha)
            components[index] += policy_log
            after = _logsumexp((math.log(NEURAL_MASS) + components[0] + neural_log,
                                math.log1p(-NEURAL_MASS) + components[index]))
            loss_sum = -after
            cumulative[policy["id"]].append(loss_sum - previous_protected[policy["id"]])
            previous_protected[policy["id"]] = loss_sum
        components[0] += neural_log
        ungated_sum += _log_mixture(neural_log, count_log, .5)
        ungated = -_logsumexp((math.log(NEURAL_MASS) + components[0], math.log1p(-NEURAL_MASS) + ungated_sum))
        hierarchy = -_logsumexp([pi + ll for pi, ll in zip(prior, components)])
        cumulative["ungated_protected"].append(ungated - previous_ungated)
        cumulative["hierarchy_protected"].append(hierarchy - previous_hierarchy)
        previous_ungated, previous_hierarchy = ungated, hierarchy
    neural_sum = math.fsum(cumulative["neural"])
    ceiling = -math.log(NEURAL_MASS)
    tolerance = 1e-9 + 2**-36 * abs(neural_sum)
    arms = {}
    for name, losses in cumulative.items():
        total = math.fsum(losses)
        arms[name] = {"loss_sum_nats_hex": total.hex(), "nll_nats_per_token": total / len(rows)}
        if name not in ("neural", "adaptive_count"):
            slack = neural_sum + ceiling - total
            arms[name]["neural_protection_slack_nats"] = slack
            if slack < -tolerance:
                raise AssertionError("neural protection ceiling failed")
    return {"arms": arms, "losses_hex": {name: [v.hex() for v in values] for name, values in cumulative.items()},
            "raw_gate_loss_sum_nats_hex": {name: math.fsum(values).hex() for name, values in raw_losses.items()},
            "gate_active_targets": active,
            "prior_to_target_count_weights_hex": {name: [v.hex() for v in values] for name, values in weights.items()},
            "hierarchy_prior_to_target_posterior_hex": [[v.hex() for v in values] for values in hierarchy_weights],
            "ungated_prior_to_target_policy_weight_hex": [v.hex() for v in ungated_weights],
            "neural_extra_loss_ceiling_nats": ceiling, "rounding_allowance_nats": tolerance}


def score_document(model, token_ids, vocabulary_size):
    """Score all 512 or fewer targets with their entire available prefix."""
    import torch
    from singularity.training.token_experts import AdaptiveTokenCounts

    counts = AdaptiveTokenCounts(vocabulary_size, 4)
    counts.reset(token_ids[:1])
    with torch.inference_mode():
        inputs = torch.tensor([token_ids[:-1]], dtype=torch.long)
        logits = model(input_ids=inputs, attention_mask=torch.ones_like(inputs), use_cache=False).logits[0]
        targets = torch.tensor(token_ids[1:], dtype=torch.long)
        # Compute target log probabilities from a proper full vocabulary
        # distribution, retaining no vocabulary-sized prediction arrays.
        log_probabilities = torch.log_softmax(logits, dim=-1, dtype=torch.float64)
        neural_losses = (-log_probabilities[torch.arange(len(targets)), targets]).cpu().tolist()
    rows = []
    for target, neural_loss in zip(token_ids[1:], neural_losses):
        probability, feature = count_target_and_feature(counts, target)
        rows.append({"target": target, "neural_nll_hex": float(neural_loss).hex(),
                     "count_nll_hex": (-math.log(probability)).hex(), "feature": feature})
        counts.update(target)
    return {"targets": len(rows), "target_rows": rows, **replay_rows(rows)}


def source_documents(path):
    payload = load_json(path)
    documents = payload["documents"] if isinstance(payload, dict) else payload
    if not isinstance(documents, list) or not documents:
        raise ValueError("source JSON must contain a nonempty documents list")
    normalized = []
    for index, document in enumerate(documents):
        split = {"dev": "development", "test": "heldout"}.get(document["split"], document["split"])
        if split not in ("development", "heldout"):
            raise ValueError("split must be development or heldout")
        record_identity = {}
        if "text_path" in document:
            candidate = Path(document["text_path"])
            if not candidate.is_absolute():
                candidate = Path(path).parent / candidate
            record = load_json(candidate)
            raw = record["text"].encode()
            if document.get("json_sha256", file_sha(candidate)) != file_sha(candidate):
                raise ValueError("source record JSON hash mismatch")
            record_identity = {"source_record_path": portable_path(candidate), "source_record_sha256": file_sha(candidate)}
        else:
            raw = document["text"].encode() if "text" in document else base64.b64decode(document["base64"], validate=True)
        if document.get("sha256", sha(raw)) != sha(raw):
            raise ValueError("source text hash mismatch")
        if not document.get("license") or not document.get("source_url"):
            raise ValueError("each document requires license and source_url")
        normalized.append({"document": index, "name": document["name"], "domain": document["domain"],
                           "split": split, "bytes": len(raw), "sha256": sha(raw),
                           "source_url": document["source_url"], "license": document["license"],
                           "source_id": document.get("source_id", document["source_url"]),
                           "text": raw.decode("utf-8"), **record_identity})
    if len({d["sha256"] for d in normalized}) != len(normalized):
        raise ValueError("duplicate source document")
    for split in ("development", "heldout"):
        if not any(d["split"] == split for d in normalized):
            raise ValueError("both development and heldout documents required")
    dev_ids = {d["source_id"] for d in normalized if d["split"] == "development"}
    if dev_ids & {d["source_id"] for d in normalized if d["split"] == "heldout"}:
        raise ValueError("a source identity appears in both development and heldout")
    old = helpers.read_gzip(helpers.SOURCE)["documents"]
    old_sha = {d["sha256"] for d in old}
    if old_sha & {d["sha256"] for d in normalized}:
        raise ValueError("source repeats the existing cross-domain study")
    return normalized


def freeze(args):
    from transformers import AutoTokenizer

    output = args.output
    if (output / "protocol.json").exists():
        raise FileExistsError("protocol already frozen")
    documents = source_documents(args.source)
    models = {}
    overrides = dict(entry.split("=", 1) for entry in args.model_dtype or ())
    if not args.model:
        raise ValueError("declare at least one model")
    for entry in args.model:
        name, path = entry.split("=", 1)
        if name in models or not name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in name):
            raise ValueError("unique filesystem-safe model name required")
        path = Path(path).resolve()
        manifest = helpers.model_manifest(path)
        receipt = load_json(path / "download_manifest.json")
        tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False)
        encoded = []
        for document in documents:
            tokens = tokenizer.encode(document["text"], add_special_tokens=False, verbose=False)[:args.max_targets + 1]
            if len(tokens) < args.max_targets + 1:
                raise ValueError("every source must supply the declared number of full-prefix targets")
            encoding_path = output / "token_documents" / name / f"{document['document']:03d}.json"
            write_json(encoding_path, {"document": document["document"], "token_ids": tokens,
                                       "token_ids_sha256": sha(canonical(tokens))})
            encoded.append({"document": document["document"], "token_ids_sha256": sha(canonical(tokens)),
                            "encoding_path": str(encoding_path.relative_to(output)), "encoding_sha256": file_sha(encoding_path)})
        dtype = overrides.get(name, "float32" if "gpt2" in name else "bfloat16")
        if dtype not in ("float32", "bfloat16"):
            raise ValueError("unsupported dtype")
        identity = {"local_path": str(path), "files": manifest, "files_manifest_sha256": sha(canonical(manifest)),
                    "model_id": receipt["model_id"], "revision": receipt["revision"], "dtype": dtype,
                    "tokenizer_class": type(tokenizer).__name__, "encoded_documents": encoded}
        identity_path = output / "model_identities" / f"{name}.json"
        write_json(identity_path, identity)
        models[name] = {"identity_path": str(identity_path.relative_to(output)), "sha256": file_sha(identity_path)}
    if set(overrides) - set(models):
        raise ValueError("dtype override for unknown model")
    protocol = {
        "schema": "singularity.pretrained-gating-protocol/1", "frozen_at_utc": now(),
        "source_path": portable_path(args.source), "source_sha256": file_sha(args.source),
        "documents": [{k: v for k, v in d.items() if k != "text"} for d in documents],
        "source_split": "source_id groups are disjoint; all document identities and splits fixed before any model forward",
        "freshness": "no complete-document SHA256 repeats the earlier cross-domain corpus; pretraining overlap remains possible",
        "models": models, "max_targets": args.max_targets, "context": "entire available prefix, one causal forward over first max_targets inputs",
        "count_model": "order4 document-local uniform-vocabulary-backed Witten-Bell; initial token initializes history, counts update only after each prediction",
        "policies": list(POLICIES), "gate": "longest previously observed context row has order >= min_order and total prior followers >= min_support; no target or neural prediction used to choose gate",
        "protected_policy": "per-document Bayesian mixture of pure neural (prior .95) and one gated expert (prior .05)",
        "secondary_arms": {"ungated_protected": "95% neural/5% fixed alpha=.5 policy, Bayesian updated per target",
                           "hierarchy_protected": "95% pure neural and .05/18 per gated expert, Bayesian updated per target",
                           "adaptive_count": "unprotected count-only diagnostic"},
        "selection": "per model choose minimum development aggregate NLL from pure neural plus18 protected policies; ties choose lexical arm ID; write and freeze selection receipt before heldout inference",
        "primary": "heldout selected protected policy (possibly pure neural) minus neural, aggregate nats/native-token within model",
        "secondary": "hierarchy_protected and ungated_protected minus neural; all18 protected and raw gated outcomes retained as diagnostics, not used for heldout selection",
        "metrics": "paired per-document loss; document-cluster percentile bootstrap10000 draws seed7102026, descriptive; no cross-tokenizer ranking",
        "retention": "all sources, frozen native token IDs, target-level neural/count losses, pretarget context features, all18 gate outcomes and weights, attempts including aborts; no rerun or deletion of completed evidence",
        "guarantee": "each protected arm cumulative loss <= pure neural cumulative loss - log(.95), exact arithmetic, each document reset; this ceiling is not a predictive gain",
        "execution": {"device": "cpu", "threads": args.threads, "neural_training_updates": 0,
                      "transformers_attention": "eager", "deterministic_algorithms": True},
        "documents_scored_before_freeze": False,
        "dependency_sha256": {name: file_sha(ROOT / name) for name in DEPENDENCIES}}
    write_json(output / "protocol.json", protocol)
    return protocol


def checked_protocol(output):
    protocol = load_json(output / "protocol.json")
    if file_sha(repo_path(protocol["source_path"])) != protocol["source_sha256"]:
        raise ValueError("source manifest changed after freeze")
    for document in protocol["documents"]:
        if "source_record_path" in document and file_sha(repo_path(document["source_record_path"])) != document["source_record_sha256"]:
            raise ValueError("source document record changed after freeze")
    for name, expected in protocol["dependency_sha256"].items():
        if file_sha(ROOT / name) != expected:
            raise ValueError("source changed after freeze: " + name)
    if tuple(protocol["policies"]) != POLICIES:
        raise ValueError("policy table mismatch")
    for name, entry in tuple(protocol["models"].items()):
        path = output / entry["identity_path"]
        if file_sha(path) != entry["sha256"]:
            raise ValueError("model identity changed")
        protocol["models"][name] = load_json(path)
    return protocol


def verify_trace(record, encoded, vocabulary_size):
    from singularity.training.token_experts import AdaptiveTokenCounts

    tokens = encoded["token_ids"]
    if len(record["target_rows"]) != len(tokens) - 1:
        raise ValueError("trace target length mismatch")
    counts = AdaptiveTokenCounts(vocabulary_size, 4)
    counts.reset(tokens[:1])
    for row, target in zip(record["target_rows"], tokens[1:]):
        count_probability, feature = count_target_and_feature(counts, target)
        if row["target"] != target or row["feature"] != feature or row["count_nll_hex"] != (-math.log(count_probability)).hex():
            raise ValueError("count probability, target or pretarget feature does not independently replay")
        neural_loss = float.fromhex(row["neural_nll_hex"])
        if not math.isfinite(neural_loss) or neural_loss < 0:
            raise ValueError("neural loss must be finite and nonnegative")
        counts.update(target)
    replay = replay_rows(record["target_rows"])
    if "replay_sha256" in record and record["replay_sha256"] != sha(canonical(replay)):
        raise ValueError("derived per-target posterior/loss digest mismatch")
    for key, value in replay.items():
        if key in record and record[key] != value:
            raise ValueError("causal mixture evidence does not replay: " + key)


def execute(args):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM

    output = args.output
    protocol = checked_protocol(output)
    identity = protocol["models"][args.name]
    if helpers.model_manifest(identity["local_path"]) != identity["files"]:
        raise ValueError("model files changed after freeze")
    selection_path = output / "models" / args.name / "selection.json"
    selection_sha = None
    if args.split == "heldout":
        selection = load_json(selection_path)
        if selection["protocol_sha256"] != file_sha(output / "protocol.json"):
            raise ValueError("selection belongs to a different protocol")
        development = output / "models" / args.name / "development" / "results.json"
        if selection["development_results_sha256"] != file_sha(development):
            raise ValueError("development changed after selection")
        selection_sha = file_sha(selection_path)
    elif selection_path.exists():
        raise FileExistsError("development selection already frozen; do not execute development again")
    destination = output / "models" / args.name / args.split
    if (destination / "results.json").exists():
        raise FileExistsError("completed split already exists")
    if any(destination.glob("documents/*.json")) and not args.resume:
        raise FileExistsError("partial evidence exists; --resume retains completed documents")
    attempts_path = destination / "execution_attempts.json"
    attempts = load_json(attempts_path) if attempts_path.exists() else []
    attempt = {"started_at_utc": now(), "status": "running", "resume": args.resume,
               "selection_sha256": selection_sha}
    attempts.append(attempt)
    write_json(attempts_path, attempts)
    started = time.perf_counter()
    try:
        torch.set_num_threads(protocol["execution"]["threads"])
        torch.set_num_interop_threads(1)
        torch.use_deterministic_algorithms(True)
        model = AutoModelForCausalLM.from_pretrained(identity["local_path"], local_files_only=True, trust_remote_code=False,
                                                    torch_dtype=getattr(torch, identity["dtype"]), attn_implementation="eager")
        model.eval()
        rows, traces = [], {}
        for entry in identity["encoded_documents"]:
            encoded = read_encoded(output, entry)
            document = protocol["documents"][encoded["document"]]
            if document["split"] != args.split:
                continue
            path = destination / "documents" / f"{encoded['document']:03d}.json"
            if path.exists():
                record = load_record(output, path)
                if (record["protocol_sha256"] != file_sha(output / "protocol.json")
                        or record["selection_sha256"] != selection_sha
                        or record["token_ids_sha256"] != encoded["token_ids_sha256"]):
                    raise ValueError("partial trace has a different frozen identity")
                verify_trace(record, encoded, model.config.vocab_size)
            else:
                document_started = time.perf_counter()
                record = score_document(model, encoded["token_ids"], model.config.vocab_size)
                record.update({"document": encoded["document"], "name": document["name"], "domain": document["domain"],
                               "split": args.split, "source_sha256": document["sha256"], "model": args.name,
                               "token_ids_sha256": encoded["token_ids_sha256"],
                               "protocol_sha256": file_sha(output / "protocol.json"), "selection_sha256": selection_sha,
                               "scoring_wall_seconds": time.perf_counter() - document_started})
                verify_trace(record, encoded, model.config.vocab_size)
                retain_record(output, path, record)
            traces[str(path.relative_to(output))] = file_sha(path)
            rows.append({key: record[key] for key in ("document", "domain", "name", "targets", "arms", "gate_active_targets")})
            print(json.dumps({"model": args.name, "split": args.split, "document_completed": encoded["document"],
                              "wall_seconds": time.perf_counter() - started}), flush=True)
        report = {"schema": "singularity.pretrained-gating-results/1", "model": args.name, "split": args.split,
                  "created_at_utc": now(), "protocol_sha256": file_sha(output / "protocol.json"),
                  "selection_sha256": selection_sha, "vocabulary_size": model.config.vocab_size,
                  "parameters": sum(p.numel() for p in model.parameters()),
                  "documents": [{"document": row["document"], "path": relative, "sha256": traces[relative]}
                                for row, relative in zip(rows, traces)],
                  "aggregate": summarize(rows), "trace_files_sha256": traces,
                  "execution_wall_seconds": time.perf_counter() - started,
                  "environment": {"torch": torch.__version__, "transformers": transformers.__version__,
                                  "python": sys.version, "dtype": identity["dtype"], **protocol["execution"]}}
        write_json(destination / "results.json", report)
        attempt.update(status="completed", ended_at_utc=now(), results_sha256=file_sha(destination / "results.json"))
        write_json(attempts_path, attempts)
        return report
    except BaseException as error:
        attempt.update(status="aborted", ended_at_utc=now(), error_type=type(error).__name__, error=str(error))
        write_json(attempts_path, attempts)
        raise


def summarize(rows):
    targets = sum(r["targets"] for r in rows)
    return {name: {"loss_sum_nats_hex": math.fsum(float.fromhex(r["arms"][name]["loss_sum_nats_hex"]) for r in rows).hex(),
                   "nll_nats_per_token": math.fsum(float.fromhex(r["arms"][name]["loss_sum_nats_hex"]) for r in rows) / targets}
            for name in rows[0]["arms"]}


def select(args):
    output = args.output
    protocol = checked_protocol(output)
    path = output / "models" / args.name / "selection.json"
    if path.exists():
        raise FileExistsError("selection already frozen")
    destination = output / "models" / args.name
    if any((destination / "heldout").rglob("*.json")):
        raise FileExistsError("heldout evidence already exists; cannot select prospectively")
    verify(output, args.name, "development")
    development_path = destination / "development" / "results.json"
    result = load_json(development_path)
    candidates = ("neural", *(p["id"] for p in POLICIES))
    chosen = min(candidates, key=lambda name: (float.fromhex(result["aggregate"][name]["loss_sum_nats_hex"]), name))
    receipt = {"schema": "singularity.pretrained-gating-selection/1", "frozen_at_utc": now(), "model": args.name,
               "protocol_sha256": file_sha(output / "protocol.json"), "development_results_sha256": file_sha(development_path),
               "selected_arm": chosen, "development_candidate_losses": {name: result["aggregate"][name] for name in candidates},
               "heldout_scored_before_selection": False, "selection_rule": protocol["selection"]}
    write_json(path, receipt)
    return receipt


def verify(output, name, split):
    protocol = checked_protocol(output)
    report = load_json(output / "models" / name / split / "results.json")
    if report["protocol_sha256"] != file_sha(output / "protocol.json"):
        raise ValueError("protocol identity mismatch")
    expected_documents = {d["document"] for d in protocol["documents"] if d["split"] == split}
    rows = []
    for relative, expected in report["trace_files_sha256"].items():
        path = output / relative
        if file_sha(path) != expected:
            raise ValueError("trace file identity mismatch")
        record = load_record(output, path)
        encoded = read_encoded(output, protocol["models"][name]["encoded_documents"][record["document"]])
        verify_trace(record, encoded, report["vocabulary_size"])
        if record["protocol_sha256"] != report["protocol_sha256"] or record["selection_sha256"] != report["selection_sha256"]:
            raise ValueError("trace protocol/selection identity mismatch")
        rows.append({key: record[key] for key in ("document", "domain", "name", "targets", "arms", "gate_active_targets")})
    if {r["document"] for r in rows} != expected_documents or len(rows) != len(expected_documents):
        raise ValueError("document count mismatch")
    if [row["document"] for row in rows] != [entry["document"] for entry in report["documents"]] or summarize(rows) != report["aggregate"]:
        raise ValueError("aggregate evidence mismatch")
    if split == "heldout":
        selection_path = output / "models" / name / "selection.json"
        if file_sha(selection_path) != report["selection_sha256"]:
            raise ValueError("heldout selection receipt mismatch")
        selection = load_json(selection_path)
        if selection["development_results_sha256"] != file_sha(output / "models" / name / "development" / "results.json"):
            raise ValueError("development receipt mismatch")
    return {"verified": True, "model": name, "split": split, "documents": len(rows), "targets": sum(r["targets"] for r in rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "execute", "select", "verify"))
    parser.add_argument("--output", type=Path, default=ROOT / "applications/training_lab/results/pretrained_gating")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--model", action="append")
    parser.add_argument("--model-dtype", action="append")
    parser.add_argument("--name")
    parser.add_argument("--split", choices=("development", "heldout"))
    parser.add_argument("--max-targets", type=int, default=512)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.max_targets <= 512 or args.threads < 1:
        parser.error("1 <= max-targets <=512 and positive threads required")
    if args.phase == "freeze":
        if not args.source:
            parser.error("freeze requires --source")
        protocol = freeze(args)
        print(json.dumps({"frozen": True, "documents": len(protocol["documents"]), "protocol_sha256": file_sha(args.output / "protocol.json")}))
    elif args.phase == "execute":
        if not args.name or not args.split:
            parser.error("execute requires --name and --split")
        result = execute(args)
        print(json.dumps({"model": args.name, "split": args.split, "aggregate": result["aggregate"]}, indent=2))
    elif args.phase == "select":
        if not args.name:
            parser.error("select requires --name")
        print(json.dumps(select(args), indent=2))
    else:
        if not args.name or not args.split:
            parser.error("verify requires --name and --split")
        print(json.dumps(verify(args.output, args.name, args.split)))


if __name__ == "__main__":
    main()
