"""Reproducible CPU runs with sealed test access and complete small checkpoints."""
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import time

import torch
import torch.nn.functional as F

from .data import build_data, canonical_hash, loss_from_logits
from .models import build_model
from .optim import build_optimizer, meta_proposal
from .telemetry import UpdateSketch, ffn_rank


def _json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def evaluate(model, rows, batch_size=256, predictions=False):
    """Loss is weighted by scored targets, including partial byte windows."""
    was_training = model.training
    model.eval()
    total_loss = correct = targets = 0
    saved = []
    with torch.no_grad():
        for start in range(0, len(rows["labels"]), batch_size):
            batch = {k: v[start:start+batch_size] for k, v in rows.items()}
            logits = model(batch["input_ids"])
            labels = batch["labels"]
            count = int((labels != -100).sum())
            loss = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), labels.reshape(-1), ignore_index=-100, reduction="sum")
            total_loss += float(loss)
            pred = logits.argmax(-1)
            correct += int(((pred == labels) & (labels != -100)).sum())
            targets += count
            if predictions:
                for x, y, pr in zip(batch["input_ids"].tolist(), labels.tolist(), pred.tolist()):
                    saved.append({"input_ids": x, "label": y, "prediction": pr})
    model.train(was_training)
    if targets == 0:
        raise ValueError("evaluation split has no scored targets")
    result = {"loss": total_loss / targets, "accuracy": correct / targets,
              "valid_targets": targets, "examples": len(rows["labels"])}
    if rows["labels"].ndim == 2:
        result["perplexity"] = math.exp(min(result["loss"], 700))
    if predictions:
        result["predictions"] = saved
    return result


def _environment():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(Path(__file__).parent.glob("*.py"))}
    return {"python": sys.version, "torch": torch.__version__, "platform": platform.platform(),
            "device": "cpu", "threads": torch.get_num_threads(), "git_commit": commit,
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
            "source_file_sha256": sources}


def model_sha256(model):
    """Hash sorted named tensor bytes, shapes and dtypes, independent of pickle."""
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        tensor = tensor.detach().cpu().contiguous()
        description = json.dumps([name, list(tensor.shape), str(tensor.dtype)], separators=(",", ":"))
        digest.update(description.encode()+b"\0")
        digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_checkpoint(path):
    """Load only a trusted checkpoint produced by this engine; includes RNG."""
    state = torch.load(path, map_location="cpu", weights_only=False)
    model = build_model(state["config"], state["data_metadata"])
    model.load_state_dict(state["model"])
    optimizer = build_optimizer(model, state["config"])
    optimizer.load_state_dict(state["optimizer"])
    model.eval()
    return model, optimizer, state


def run(config, output_dir):
    """Run one seed or an explicitly supplied list. No TEST trajectory exists.

    Discovery plans set evaluate_test=false, forbidding TEST evaluation. Data
    construction still reads/hashes every supplied corpus and constructs every
    modular split. Frozen confirmation plans may score TEST once after the last
    update, and retain modular predictions for audit.
    """
    cfg = json.loads(json.dumps(config))
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if "seeds" in cfg:
        seeds = cfg.pop("seeds")
        if not seeds or len(set(seeds)) != len(seeds):
            raise ValueError("seeds must be a nonempty distinct list")
        results = [run({**cfg, "seed": int(s)}, out / ("seed_"+str(s))) for s in seeds]
        summary = {"plan_sha256": canonical_hash(config), "runs": results}
        _json(out / "summary.json", summary)
        return summary
    seed = int(cfg.get("seed", 0))
    threads = int(cfg.get("threads", 1))
    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True)
    random.seed(seed)
    torch.manual_seed(seed)
    plan_hash = canonical_hash(cfg)
    _json(out / "config.json", cfg)
    _json(out / "environment.json", _environment())
    started = time.perf_counter()
    data = build_data(cfg)
    _json(out / "data.json", data.metadata)
    model = build_model(cfg, data.metadata).cpu()
    initial_model_hash = model_sha256(model)
    optimizer = build_optimizer(model, cfg)
    parameters = list(model.parameters())
    parameter_count = sum(p.numel() for p in parameters)
    if parameter_count > int(cfg.get("max_parameters", 1000000)):
        raise ValueError("model exceeds declared parameter budget")
    sampler_seed = seed+104729
    gen = torch.Generator().manual_seed(sampler_seed)
    tc = cfg.get("telemetry", {})
    sketch = UpdateSketch(parameter_count, int(tc.get("sketch_dimension", 16)),
                          int(tc.get("sketch_window", 32)), int(tc.get("sketch_seed", 314159)))
    steps, batch_size = int(cfg.get("steps", 1000)), int(cfg.get("batch_size", 128))
    eval_every = int(cfg.get("eval_every", 100))
    if min(steps, batch_size, eval_every) < 1:
        raise ValueError("steps, batch_size, eval_every must be positive")
    grad_clip = float(cfg.get("grad_clip", 1.0))
    eval_batch = int(cfg.get("eval_batch_size", 256))
    variant = cfg.get("variant", "baseline")
    base_lrs = [g["lr"] for g in optimizer.param_groups]
    metrics, clipped = [], 0
    test_accesses = meta_calls = 0
    meta_cfg = dict(cfg.get("meta", {}))
    meta_cfg.setdefault("grad_clip", grad_clip)
    meta_probe = None
    tune_probe = None
    if variant == "meta":
        probe_seed = int(meta_cfg.get("probe_seed", 271828))
        tune_rows = data.splits["tune"]
        tune_n = min(int(meta_cfg.get("batch_size", batch_size)), len(tune_rows["labels"]))
        if tune_n < 1:
            raise ValueError("meta probe batch_size must be positive")
        probe_gen = torch.Generator().manual_seed(probe_seed)
        probe_indices = torch.randperm(len(tune_rows["labels"]), generator=probe_gen)[:tune_n]
        tune_probe = {k: v[probe_indices] for k, v in tune_rows.items()}
        meta_probe = {"seed": probe_seed, "selection": "uniform shuffled fixed TUNE row indices without replacement",
                      "indices": probe_indices.tolist(), "rows": tune_n}
        meta_probe["indices_sha256"] = canonical_hash(meta_probe["indices"])
        # Probe sampling has a separate RNG and never advances the TRAIN sampler.
        _json(out / "meta_probe.json", meta_probe)
    model.train()
    raw_path = out / "metrics.jsonl"
    with raw_path.open("w") as raw:
        for step in range(1, steps+1):
            if variant == "cosine":
                multiplier = .5*(1+math.cos(math.pi*(step-1)/steps))
                for group, initial in zip(optimizer.param_groups, base_lrs):
                    group["lr"] = initial*multiplier
            batch = data.sample(batch_size, gen)
            meta = None
            if variant == "meta" and step % int(meta_cfg.get("every", 25)) == 0:
                meta = meta_proposal(model, optimizer, batch, tune_probe, loss_from_logits, meta_cfg)
                meta_calls += 1
                if meta.get("accepted"):
                    for i, group in enumerate(optimizer.param_groups):
                        group["lr"] = meta.get("group_lrs", [meta["lr"]]*len(base_lrs))[i]
                        group["weight_decay"] = meta.get("group_weight_decays", [meta["weight_decay"]]*len(base_lrs))[i]
            optimizer.zero_grad(set_to_none=True)
            logits = model(batch["input_ids"])
            loss = loss_from_logits(logits, batch)
            if not torch.isfinite(loss):
                raise FloatingPointError("nonfinite training loss")
            loss.backward()
            grad_norm = math.sqrt(sum(float(p.grad.detach().double().square().sum()) for p in parameters if p.grad is not None))
            if not math.isfinite(grad_norm):
                raise FloatingPointError("nonfinite gradient")
            did_clip = grad_clip > 0 and grad_norm > grad_clip
            if grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(parameters, grad_clip)
            clipped += int(did_clip)
            before = torch.cat([p.detach().reshape(-1) for p in parameters]).clone()
            optimizer.step()
            after = torch.cat([p.detach().reshape(-1) for p in parameters])
            sketch.update(after-before)
            record = {"step": step, "optimizer_updates": step, "train_batch_loss": float(loss.detach()),
                      "train_batch_valid_targets": int((batch["labels"] != -100).sum()),
                      "grad_norm_before_clip": grad_norm, "clipped_step": did_clip,
                      "clipped_step_fraction": clipped/step,
                      "learning_rates": [g["lr"] for g in optimizer.param_groups],
                      "weight_decays": [g["weight_decay"] for g in optimizer.param_groups]}
            if meta is not None:
                record["meta"] = meta
            if step % eval_every == 0 or step == steps:
                record["train"] = evaluate(model, data.splits["train"], eval_batch)
                record["tune"] = evaluate(model, data.splits["tune"], eval_batch)
                record["update_sketch"] = sketch.summary()
                if tc.get("ffn_rank", False):
                    record["ffn_weights"] = ffn_rank(model)
            record["elapsed_seconds_including_monitoring"] = time.perf_counter()-started
            raw.write(json.dumps(record, allow_nan=False, sort_keys=True)+"\n")
            raw.flush()
            metrics.append(record)
    # The append stream supports progress inspection. Seal an authoritative
    # complete payload from the in-memory records with a fresh inode, fsync and
    # atomic replacement before publishing a checkpoint or completion receipt.
    # This also makes missing streamed writes a detectable artifact failure.
    if len(metrics) != steps or any(row['step'] != i+1 for i, row in enumerate(metrics)):
        raise RuntimeError("incomplete optimizer-update history")
    payload = ''.join(json.dumps(row, allow_nan=False, sort_keys=True)+'\n'
                      for row in metrics).encode('utf-8')
    sealed = out / ('.metrics.final.'+str(os.getpid()))
    with sealed.open('wb') as file:
        file.write(payload)
        file.flush()
        os.fsync(file.fileno())
    os.replace(sealed, raw_path)
    if raw_path.read_bytes() != payload:
        raise RuntimeError("sealed metric log failed byte-for-byte verification")
    sealed_metrics_hash = hashlib.sha256(payload).hexdigest()
    final_tune = evaluate(model, data.splits["tune"], eval_batch, predictions=data.metadata["task"] == "modular_addition")
    predictions = {"tune": final_tune.pop("predictions", None)}
    final_test = None
    if cfg.get("evaluate_test", True):
        final_test = evaluate(model, data.splits["test"], eval_batch, predictions=data.metadata["task"] == "modular_addition")
        test_accesses += 1
        predictions["test"] = final_test.pop("predictions", None)
    if data.metadata["task"] == "modular_addition":
        _json(out / "predictions.json", {"plan_sha256": plan_hash, "test_evaluations": test_accesses, **predictions})
    checkpoint = {"format": "singularity-training/1", "config": cfg, "plan_sha256": plan_hash,
                  "data_metadata": data.metadata, "model": model.state_dict(),
                  "optimizer": optimizer.state_dict(), "torch_rng": torch.get_rng_state(),
                  "python_rng": random.getstate(), "sampler_rng": gen.get_state(),
                  "sampler_seed": sampler_seed, "initial_model_sha256": initial_model_hash,
                  "final_model_sha256": model_sha256(model),
                  "meta_probe": meta_probe,
                  "optimizer_updates": steps, "meta_calls": meta_calls, "test_evaluations": test_accesses}
    checkpoint_path = out / "checkpoint.pt"
    torch.save(checkpoint, checkpoint_path)
    checkpoint_hash = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
    # Elapsed includes training, all probes/evaluations, telemetry, and checkpoint.
    summary = {"plan_sha256": plan_hash, "seed": seed, "parameter_count": parameter_count,
               "sampler_seed": sampler_seed, "initial_model_sha256": initial_model_hash,
               "final_model_sha256": checkpoint["final_model_sha256"],
               "meta_probe": meta_probe,
               "optimizer_updates": steps, "meta_calls": meta_calls, "test_evaluations": test_accesses,
               "final_train": metrics[-1]["train"], "final_tune": final_tune, "final_test": final_test,
               "counts": data.metadata["counts"], "split_sha256": data.metadata["split_sha256"],
               "wall_seconds_including_monitoring": time.perf_counter()-started,
               "checkpoint_sha256": checkpoint_hash, "checkpoint_bytes": checkpoint_path.stat().st_size,
               "metrics_sha256": sealed_metrics_hash,
               "output_dir": str(out), "feature_telemetry": "actual-update CountSketch, centered and uncentered"}
    _json(out / "summary.json", summary)
    return summary
