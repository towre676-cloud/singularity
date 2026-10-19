#!/usr/bin/env python3
"""Frozen next-token comparison on real, locally downloaded pretrained models.

Freeze all model identities, document prefixes and arms before execution.
Models are never updated. Document-local count tables and Bayesian mixture
posteriors observe each target only after predicting it. Loss is nats per
token of THAT model's tokenizer, not nats per byte or a cross-tokenizer rank.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUTPUT = ROOT / "applications/training_lab/results/pretrained_prediction"
SOURCE = ROOT / "applications/training_lab/results/cross_domain/documents.json.gz"
DOMAINS = ("reference_prose", "legal_prose", "source_code")
ARMS = ("neural", "adaptive_count", "fixed_half_blend", "online_blend",
        "neural_backed_adaptive", "online_neural_backed")
DEPENDENCIES = ("scripts/confirm_pretrained_prediction.py", "src/singularity/training/token_experts.py",
                "src/singularity/training/online_blend.py")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n")
    os.replace(temporary, path)


def write_gzip(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as handle:
            handle.write(canonical(value))
    os.replace(temporary, path)


def read_gzip(path):
    return json.loads(gzip.decompress(Path(path).read_bytes()))


def model_manifest(path):
    """Hash every downloaded file, including all weights and tokenizer files."""
    path = Path(path).resolve()
    receipt_path = path / "download_manifest.json"
    receipt = json.loads(receipt_path.read_text())
    if (receipt.get("schema") != "singularity.pretrained-download/1" or not receipt.get("model_id")
            or not receipt.get("revision")):
        raise ValueError("pinned Hugging Face download receipt required")
    files = [receipt_path]
    for record in receipt["files"]:
        candidate = (path / record["path"]).resolve()
        if not candidate.is_relative_to(path) or candidate in files:
            raise ValueError("invalid or duplicate path in download receipt")
        if candidate.stat().st_size != record["bytes"] or file_sha(candidate) != record["sha256"]:
            raise ValueError("download receipt disagrees with model file: " + record["path"])
        files.append(candidate)
    files.sort()
    if not (path / "config.json").is_file() or not any(p.suffix in (".safetensors", ".bin") for p in files):
        raise ValueError("complete local model weights and config required: " + str(path))
    return {str(p.relative_to(path)): {"bytes": p.stat().st_size, "sha256": file_sha(p)} for p in files}


def source_documents(per_domain):
    payload = read_gzip(SOURCE)
    selected = []
    for domain in DOMAINS:
        candidates = [d for d in payload["documents"] if d["domain"] == domain]
        candidates.sort(key=lambda d: sha(("singularity-pretrained-v1/" + domain + "/" + d["name"]).encode()))
        if len(candidates) < per_domain:
            raise ValueError("not enough stored documents in " + domain)
        for d in candidates[:per_domain]:
            raw = base64.b64decode(d["base64"], validate=True)
            if len(raw) != d["bytes"] or sha(raw) != d["sha256"]:
                raise ValueError("stored source document identity mismatch")
            selected.append({k: d[k] for k in ("domain", "name", "bytes", "sha256", "base64")})
    return selected


def window_plan(token_count, context_length=256, stride=128):
    """Yield input/score slices covering every noninitial token exactly once.

    Row i predicts token i+1. Subsequent windows overlap, but overlap logits
    are discarded. Each scored row sees only preceding tokens through the
    model's causal mask. Positions start at zero in each input window.
    """
    if token_count < 2 or not 1 <= stride <= context_length:
        raise ValueError("at least two tokens and 1 <= stride <= context_length required")
    target_start = 1
    while target_start < token_count:
        target_stop = min(token_count, target_start + (context_length if target_start == 1 else stride))
        input_stop = target_stop - 1
        input_start = max(0, input_stop - context_length)
        yield {"input_start": input_start, "input_stop": input_stop,
               "score_start": target_start - 1 - input_start,
               "score_stop": input_stop - input_start,
               "target_start": target_start, "target_stop": target_stop}
        target_start = target_stop


def freeze(args):
    from transformers import AutoTokenizer

    output = args.output
    if (output / "protocol.json").exists():
        raise FileExistsError("protocol already frozen; use a new output directory")
    if not args.model:
        raise ValueError("at least one --model NAME=LOCAL_PATH required")
    dtype_overrides = {}
    for entry in args.model_dtype or ():
        name, separator, dtype = entry.partition("=")
        if not separator or name in dtype_overrides or dtype not in ("float32", "bfloat16"):
            raise ValueError("--model-dtype must be unique NAME=float32 or NAME=bfloat16")
        dtype_overrides[name] = dtype
    documents = source_documents(args.documents_per_domain)
    models = {}
    for entry in args.model:
        name, separator, path = entry.partition("=")
        if not separator or not name or name in models or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in name):
            raise ValueError("model must be a unique filesystem-safe NAME=LOCAL_PATH")
        path = Path(path).resolve()
        manifest = model_manifest(path)
        download = json.loads((path / "download_manifest.json").read_text())
        tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False)
        encoded = []
        for i, document in enumerate(documents):
            text = base64.b64decode(document["base64"]).decode("utf-8", errors="replace")
            tokens = tokenizer.encode(text, add_special_tokens=False, verbose=False)[:args.max_targets + 1]
            if len(tokens) < 2:
                raise ValueError("document has fewer than two tokenizer tokens")
            encoded.append({"document": i, "token_ids": tokens, "targets": len(tokens) - 1,
                            "token_ids_sha256": sha(canonical(tokens))})
        models[name] = {"local_path": str(path), "files": manifest,
                        "files_manifest_sha256": sha(canonical(manifest)),
                        "model_id": download["model_id"], "revision": download["revision"],
                        "license": download.get("license"),
                        "dtype": dtype_overrides.get(name, args.dtype),
                        "tokenizer_class": type(tokenizer).__name__, "tokenizer_length": len(tokenizer),
                        "encoded_documents": encoded}
    if set(dtype_overrides) - set(models):
        raise ValueError("dtype override names must identify a declared model")
    protocol = {
        "schema": "singularity.pretrained-prediction-protocol/1", "frozen_at_utc": now(),
        "document_source": str(SOURCE.relative_to(ROOT)), "document_source_sha256": file_sha(SOURCE),
        "document_selection": "rank stored source documents per domain by sha256('singularity-pretrained-v1/'+domain+'/'+name); take first declared count",
        "documents_per_domain": args.documents_per_domain, "max_targets_per_document": args.max_targets,
        "text_decoding": "UTF-8 with replacement for any incomplete source suffix; add_special_tokens=False; first max_targets+1 tokenizer IDs",
        "context_length": args.context_length, "stride": args.stride,
        "neural_contract": "eval(), no gradients, causal masked teacher forcing; each noninitial token scored once; overlapping windows discard previously scored rows; position IDs reset per window",
        "arms": {
            "neural": "pretrained model softmax; no model updates",
            "adaptive_count": "document-local Witten-Bell order4 with strictly positive uniform vocabulary backoff",
            "fixed_half_blend": "0.5 neural + 0.5 adaptive_count; declared without tuning",
            "online_blend": "equal-prior Bayesian mixture over count weights k/20, k=0..20, of neural+adaptive_count",
            "neural_backed_adaptive": "secondary: same Witten-Bell document counts over current causal neural probabilities instead of uniform backoff",
            "online_neural_backed": "secondary: equal-prior21-weight Bayesian mixture of neural+neural_backed_adaptive"},
        "adaptation": "counts and mixture posteriors reset every document; first token initializes history only; predict target, then update counts/posterior; no future targets or future documents used",
        "primary_comparisons": ["online_blend minus neural", "online_blend minus adaptive_count"],
        "secondary_comparisons": ["online_neural_backed minus neural", "neural_backed_adaptive minus neural", "fixed_half_blend minus neural"],
        "metrics": ["NLL nats/token within each tokenizer", "top1 token accuracy", "per-document regret versus own21 fixed mixtures"],
        "uncertainty": "paired document-cluster percentile bootstrap per model/domain,10000 draws, numpy RNG seed90211; descriptive, no independent-token inference",
        "scope": "Previously used, licensed build-environment documents are a fixed transfer benchmark, not a pristine unseen corpus; overlap with original pretraining may exist. No cross-tokenizer NLL comparison, general LLM performance claim or finetuning claim.",
        "execution": {"device": "cpu", "dtype": args.dtype, "threads": args.threads,
                      "sampling": "none; full vocabulary softmax", "neural_training_updates": 0},
        "documents_scored_before_freeze": False, "models": models,
        "dependency_sha256": {name: file_sha(ROOT / name) for name in DEPENDENCIES},
        "documents_sha256": sha(canonical(documents)),
    }
    # Both payloads are complete before the receipt is made visible.
    write_gzip(output / "documents.json.gz", documents)
    write_json(output / "protocol.json", protocol)
    return protocol


def audit_tolerance(audit):
    return 1e-9 + 2.**-36 * abs(audit["online_cumulative_nll"])


def score_document(model, token_ids, vocabulary_size, context_length, stride):
    import numpy as np
    import torch
    from singularity.training.online_blend import VectorizedBlendState
    from singularity.training.token_experts import AdaptiveTokenCounts

    counts = AdaptiveTokenCounts(vocabulary_size, 4)
    counts.reset(token_ids[:1])
    online, online_backed = VectorizedBlendState(), VectorizedBlendState()
    parts = {arm: [] for arm in ARMS}
    correct = {arm: 0 for arm in ARMS}
    weight_parts = {"online_blend": [], "online_neural_backed": []}
    with torch.inference_mode():
        for window in window_plan(len(token_ids), context_length, stride):
            inputs = torch.tensor([token_ids[window["input_start"]:window["input_stop"]]], dtype=torch.long)
            logits = model(input_ids=inputs, attention_mask=torch.ones_like(inputs), use_cache=False).logits[0]
            selected = logits[window["score_start"]:window["score_stop"]]
            neural = torch.softmax(selected, dim=-1, dtype=torch.float64).cpu().numpy()
            if neural.shape[1] != vocabulary_size or not np.all(neural > 0):
                raise ValueError("unexpected vocabulary size or underflowed neural probability")
            targets = np.asarray(token_ids[window["target_start"]:window["target_stop"]], dtype=np.int64)
            if len(neural) != len(targets):
                raise AssertionError("neural/target alignment mismatch")
            adaptive, backed = np.empty_like(neural), np.empty_like(neural)
            for i, target in enumerate(targets):
                adaptive[i] = counts.probabilities()
                backed[i] = counts.probabilities(neural[i])
                counts.update(int(target))  # strictly AFTER both distributions emitted
            probabilities = {"neural": neural, "adaptive_count": adaptive,
                             "fixed_half_blend": .5 * neural + .5 * adaptive,
                             "neural_backed_adaptive": backed}
            for arm, values in probabilities.items():
                parts[arm].append(-np.log(values[np.arange(len(targets)), targets]))
                correct[arm] += int((values.argmax(1) == targets).sum())
            for arm, state, expert in (("online_blend", online, adaptive),
                                       ("online_neural_backed", online_backed, backed)):
                result = state.score_chunk(neural, expert, targets)
                parts[arm].append(result["target_nll_nats"])
                correct[arm] += int(result["target_correct"].sum())
                weight_parts[arm].append(result["prior_to_target_count_weights"])
            del logits, selected, neural, adaptive, backed, probabilities
    losses = {arm: np.concatenate(values) for arm, values in parts.items()}
    audits = {"online_blend": online.guarantee(), "online_neural_backed": online_backed.guarantee()}
    for audit in audits.values():
        if audit["bound_slack_nats"] < -audit_tolerance(audit):
            raise AssertionError("Bayesian regret bound exceeded rounding allowance")
    return {
        "targets": len(token_ids) - 1, "token_ids_sha256": sha(canonical(token_ids)),
        "arms": {arm: {"loss_sum_nats_hex": math.fsum(values).hex(), "correct": correct[arm],
                       "nll_nats_per_token": math.fsum(values) / len(values),
                       "accuracy": correct[arm] / len(values)} for arm, values in losses.items()},
        "losses_hex": {arm: [float(v).hex() for v in values] for arm, values in losses.items()},
        "prior_to_target_count_weights_hex": {arm: [float(v).hex() for v in np.concatenate(values)]
                                               for arm, values in weight_parts.items()},
        "online_audits": audits,
    }


def cluster_bootstrap(rows, first, second):
    import numpy as np

    differences = np.asarray([float.fromhex(r["arms"][first]["loss_sum_nats_hex"])
                              - float.fromhex(r["arms"][second]["loss_sum_nats_hex"]) for r in rows])
    sizes = np.asarray([r["targets"] for r in rows])
    draws = np.random.default_rng(90211).integers(0, len(rows), size=(10000, len(rows)))
    values = differences[draws].sum(1) / sizes[draws].sum(1)
    return {"difference_nats_per_token": float(differences.sum() / sizes.sum()),
            "percentile_95_interval": np.quantile(values, [.025, .975]).tolist(),
            "documents": len(rows), "documents_first_better": int((differences < 0).sum()),
            "interpretation": "negative favors first; descriptive paired document-cluster bootstrap"}


def summarize_rows(rows):
    result = {}
    for domain in (*DOMAINS, "all_domains"):
        members = [r for r in rows if domain == "all_domains" or r["domain"] == domain]
        total = sum(r["targets"] for r in members)
        result[domain] = {"documents": len(members), "targets": total,
                          "arms": {arm: {"nll_nats_per_token": math.fsum(float.fromhex(r["arms"][arm]["loss_sum_nats_hex"]) for r in members) / total,
                                         "accuracy": sum(r["arms"][arm]["correct"] for r in members) / total} for arm in ARMS},
                          "paired": {a + "_minus_" + b: cluster_bootstrap(members, a, b)
                                     for a, b in (("online_blend", "neural"), ("online_blend", "adaptive_count"),
                                                  ("online_neural_backed", "neural"), ("neural_backed_adaptive", "neural"),
                                                  ("fixed_half_blend", "neural"))}}
    return result


def validate_trace(record):
    from singularity.training.online_blend import BayesianByteBlend

    decoded = {}
    for arm in ARMS:
        losses = [float.fromhex(v) for v in record["losses_hex"][arm]]
        decoded[arm] = losses
        if (len(losses) != record["targets"] or any(not math.isfinite(v) or v < 0 for v in losses)
                or math.fsum(losses).hex() != record["arms"][arm]["loss_sum_nats_hex"]):
            raise ValueError("retained trace does not reproduce loss sum for " + arm)
        if not 0 <= record["arms"][arm]["correct"] <= record["targets"]:
            raise ValueError("invalid correct-target count")
    for arm, values in record["prior_to_target_count_weights_hex"].items():
        weights = [float.fromhex(v) for v in values]
        if len(weights) != record["targets"] or any(not 0 <= v <= 1 for v in weights):
            raise ValueError("invalid causal mixture weights")
        if abs(weights[0] - .5) > 1e-14:
            raise ValueError("document posterior did not start from equal prior")
        audit = record["online_audits"][arm]
        if audit["bound_slack_nats"] < -audit_tolerance(audit):
            raise ValueError("retained regret certificate fails")
        # Independent standard-library streaming replay: it computes the
        # posterior row by row, unlike the vectorized exclusive-prefix path.
        expert_arm = "adaptive_count" if arm == "online_blend" else "neural_backed_adaptive"
        reference = BayesianByteBlend()
        for neural_loss, expert_loss, observed_loss, weight in zip(decoded["neural"], decoded[expert_arm], decoded[arm], weights):
            if abs(reference.posterior_count_weight - weight) > 1e-9:
                raise ValueError("retained prior-to-target weight does not replay")
            expected_loss = reference._observe_target_probabilities(math.exp(-neural_loss), math.exp(-expert_loss))
            if abs(expected_loss - observed_loss) > 1e-9:
                raise ValueError("retained online loss does not replay")
        reference_audit = reference.guarantee()
        for key in ("online_cumulative_nll", "best_fixed_grid_cumulative_nll", "regret_nats", "bound_slack_nats"):
            if abs(reference_audit[key] - audit[key]) > audit_tolerance(audit):
                raise ValueError("retained regret audit does not replay: " + key)


def execute(args):
    import numpy as np
    import torch
    import transformers
    from transformers import AutoModelForCausalLM

    output = args.output
    protocol_path = output / "protocol.json"
    frozen = json.loads(protocol_path.read_text())
    if args.name not in frozen["models"]:
        raise ValueError("--name must identify one frozen model")
    for name, expected in frozen["dependency_sha256"].items():
        if file_sha(ROOT / name) != expected:
            raise ValueError("source changed after freeze: " + name)
    documents = read_gzip(output / "documents.json.gz")
    if sha(canonical(documents)) != frozen["documents_sha256"]:
        raise ValueError("document bytes changed after freeze")
    identity = frozen["models"][args.name]
    if model_manifest(identity["local_path"]) != identity["files"]:
        raise ValueError("model/tokenizer files changed after freeze")
    destination = output / "models" / args.name
    if (destination / "results.json").exists():
        raise FileExistsError("this model already completed; do not execute twice")
    if destination.exists() and any(destination.glob("documents/*.json.gz")) and not args.resume:
        raise FileExistsError("partial evidence exists; --resume preserves completed documents")
    attempts_path = destination / "execution_attempts.json"
    attempts = json.loads(attempts_path.read_text()) if attempts_path.exists() else []
    attempt = {"started_at_utc": now(), "resume": bool(args.resume), "status": "running"}
    attempts.append(attempt)
    write_json(attempts_path, attempts)
    started = time.perf_counter()
    try:
        torch.set_num_threads(frozen["execution"]["threads"])
        torch.set_num_interop_threads(1)
        torch.use_deterministic_algorithms(True)
        dtype = getattr(torch, identity["dtype"])
        model = AutoModelForCausalLM.from_pretrained(identity["local_path"], local_files_only=True,
                                                    trust_remote_code=False, torch_dtype=dtype,
                                                    attn_implementation="eager")
        model.eval()
        parameters = sum(p.numel() for p in model.parameters())
        rows, trace_files = [], {}
        for encoded in identity["encoded_documents"]:
            i = encoded["document"]
            document = documents[i]
            trace_path = destination / "documents" / f"{i:03d}.json.gz"
            if trace_path.exists():
                record = read_gzip(trace_path)
                if (record["token_ids_sha256"] != encoded["token_ids_sha256"]
                        or record["model_files_manifest_sha256"] != identity["files_manifest_sha256"]
                        or record["protocol_receipt_sha256"] != file_sha(protocol_path)):
                    raise ValueError("resumed document belongs to a different protocol")
                validate_trace(record)
            else:
                t0 = time.perf_counter()
                record = score_document(model, encoded["token_ids"], model.config.vocab_size,
                                        frozen["context_length"], frozen["stride"])
                record.update({"document": i, "domain": document["domain"], "name": document["name"],
                               "source_sha256": document["sha256"], "model": args.name,
                               "model_files_manifest_sha256": identity["files_manifest_sha256"],
                               "protocol_receipt_sha256": file_sha(protocol_path),
                               "scoring_wall_seconds": time.perf_counter() - t0})
                validate_trace(record)
                write_gzip(trace_path, record)
            trace_files[str(trace_path.relative_to(output))] = file_sha(trace_path)
            rows.append({k: v for k, v in record.items() if k not in ("losses_hex", "prior_to_target_count_weights_hex")})
            print(json.dumps({"model": args.name, "document_completed": i, "documents_total": len(documents),
                              "targets": record["targets"], "wall_seconds": time.perf_counter() - started}), flush=True)
        report = {"schema": "singularity.pretrained-prediction-results/1", "model": args.name,
                  "created_at_utc": now(), "protocol_receipt_sha256": file_sha(protocol_path),
                  "model_files_manifest_sha256": identity["files_manifest_sha256"], "parameters": parameters,
                  "domains": summarize_rows(rows), "documents": rows, "trace_files_sha256": trace_files,
                  "execution_wall_seconds": time.perf_counter() - started,
                  "neural_training_updates": 0,
                  "environment": {"python": sys.version, "numpy": np.__version__, "torch": torch.__version__,
                                  "transformers": transformers.__version__, **frozen["execution"], "dtype": identity["dtype"]},
                  "interpretation": frozen["scope"]}
        write_json(destination / "results.json", report)
        attempt.update({"status": "completed", "ended_at_utc": now(), "results_sha256": file_sha(destination / "results.json")})
        write_json(attempts_path, attempts)
        return report
    except BaseException as error:
        attempt.update({"status": "aborted", "ended_at_utc": now(), "error_type": type(error).__name__, "error": str(error)})
        write_json(attempts_path, attempts)
        raise


def verify(output, name):
    """Recompute every retained per-document loss sum without Torch or models."""
    result_path = output / "models" / name / "results.json"
    report = json.loads(result_path.read_text())
    if report["protocol_receipt_sha256"] != file_sha(output / "protocol.json"):
        raise ValueError("protocol receipt mismatch")
    rows = []
    for relative, expected in report["trace_files_sha256"].items():
        path = output / relative
        if file_sha(path) != expected:
            raise ValueError("trace file changed: " + relative)
        record = read_gzip(path)
        validate_trace(record)
        rows.append(record)
    if len(rows) != len(report["documents"]):
        raise ValueError("retained document count mismatch")
    for domain, summary in report["domains"].items():
        members = [r for r in rows if domain == "all_domains" or r["domain"] == domain]
        targets = sum(r["targets"] for r in members)
        for arm in ARMS:
            loss = math.fsum(float.fromhex(r["arms"][arm]["loss_sum_nats_hex"]) for r in members) / targets
            accuracy = sum(r["arms"][arm]["correct"] for r in members) / targets
            if loss != summary["arms"][arm]["nll_nats_per_token"] or accuracy != summary["arms"][arm]["accuracy"]:
                raise ValueError("aggregate does not match retained traces")
    return {"model": name, "verified": True, "documents": len(rows),
            "targets": sum(r["targets"] for r in rows), "arms": len(ARMS)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "execute", "verify"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--model", action="append", help="freeze: NAME=LOCAL_PATH, repeat for all models")
    parser.add_argument("--model-dtype", action="append", help="freeze: optional NAME=float32 or NAME=bfloat16 override")
    parser.add_argument("--name", help="execute/verify: one model name in the frozen protocol")
    parser.add_argument("--documents-per-domain", type=int, default=8)
    parser.add_argument("--max-targets", type=int, default=512)
    parser.add_argument("--context-length", type=int, default=256)
    parser.add_argument("--stride", type=int, default=128)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--dtype", choices=("float32", "bfloat16"), default="float32")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if (args.documents_per_domain < 1 or args.max_targets < 1 or args.threads < 1
            or not 1 <= args.stride <= args.context_length):
        parser.error("positive document/target/thread counts and 1 <= stride <= context required")
    if args.phase == "freeze":
        record = freeze(args)
        print(json.dumps({"frozen": True, "models": list(record["models"]),
                          "documents": args.documents_per_domain * 3,
                          "protocol_receipt_sha256": file_sha(args.output / "protocol.json")}))
    elif args.phase == "execute":
        report = execute(args)
        print(json.dumps({"model": args.name, "domains": report["domains"]}, indent=2))
    else:
        print(json.dumps(verify(args.output, args.name)))


if __name__ == "__main__":
    main()
