#!/usr/bin/env python3
"""Freeze and confirm a TUNE-fitted neural/count probability mixture.

This uses retained, frozen neural checkpoints and new nonoverlapping byte
intervals. It trains no neural parameters and does not claim a new algorithm.
Run --freeze first; --execute refuses a changed source or protocol.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time

import numpy as np


SEEDS = (1000, 1001, 1002)
SMOOTHING_GRID = (.01, .1, 1.)
COUNT_WEIGHTS = tuple(i / 20 for i in range(21))
REVISION = "b08601e04326c79dfdd32d625aee71d232d685c3"
PROTOCOL = {
    "schema": "singularity.predictive-mixture-protocol/1",
    "purpose": "One prospective confirmation of an ordinary probability mixture, after earlier neural study",
    "neural_models": "All three existing wikitext_byte/baseline/fixed AdamW final checkpoints; no seed selection",
    "seeds": list(SEEDS),
    "neural_exposure": "TRAIN prefix [0,262144), previous TUNE prefix [0,32768); prior TEST prefix [0,32768) was already reported",
    "source": {"dataset": "Salesforce/wikitext", "configuration": "wikitext-2-raw-v1", "revision": REVISION,
               "stream": "UTF-8 of newline-joined nonempty, non-whitespace rows, with terminal newline"},
    "fresh_intervals": {"train": [0, 262144], "tune": [32768, 65536], "test": [32768, 65536]},
    "interval_convention": "zero-based half-open; TUNE and TEST are distinct official splits; neither suffix was used previously",
    "train_counts": "One count hierarchy from TRAIN only; max two preceding bytes; same reset windows as neural model",
    "smoothing_grid": list(SMOOTHING_GRID),
    "smoothing_selection": "Minimum fresh-TUNE trigram NLL; exact tie chooses smaller smoothing",
    "mixture": "P=(1-w)*P_neural+w*P_trigram, same scalar w for every prediction within one checkpoint",
    "count_weight_grid": list(COUNT_WEIGHTS),
    "weight_selection": "Minimum fresh-TUNE NLL independently for each retained checkpoint; exact tie chooses smaller w",
    "sequence_length": 64,
    "targets": "Every noninitial suffix byte exactly once; target raw[i+1], context starts at floor(i/64)*64; no overlap with earlier prefix context",
    "test_policy": "Freeze all three TUNE selections before reading fresh TEST; one neural inference pass per checkpoint and one count prediction pass on TEST; score declared comparisons together",
    "baselines": ["each frozen neural checkpoint", "TRAIN-only trigram with fresh-TUNE selected smoothing", "equal-weight probability ensemble of all three neural checkpoints"],
    "primary_comparison": "Each seed's TUNE-selected mixture versus its same frozen neural checkpoint; mean over all three seeds",
    "secondary_comparison": "TUNE-selected ensemble/count mixture versus equal-weight neural probability ensemble and strongest unblended comparator selected only by TUNE",
    "ensemble_selection": "Same count-weight grid and tie rule fitted once on fresh TUNE; neural ensemble probabilities arithmetic mean of all three checkpoints",
    "strongest_unblended_reference": "Minimum fresh-TUNE NLL among three individual checkpoints, their equal-weight neural probability ensemble, and selected trigram; ties alphabetical",
    "ensemble_cost": "Requires all three neural forward passes, separately stated; no inexpensive-ensemble or faster-inference claim",
    "metrics": ["target-weighted NLL nats/byte", "bits/byte", "top-1 accuracy", "paired per-target mixture-minus-baseline NLL"],
    "aggregate": "Arithmetic mean across three model seeds, equivalently target-weighted over all three equal-length predictions; same TEST bytes are repeated measures, not independent corpora",
    "uncertainty": {"kind": "paired contiguous-block bootstrap, conditional on these three frozen models and this source interval",
                    "block_windows": 32, "block_bytes": 2048, "bootstrap_draws": 10000, "rng_seed": 731923,
                    "seed_aggregation": "average each byte's loss over the three models before resampling blocks; never treat seed copies of same text as independent",
                    "limitation": "Descriptive interval for finite suffix; 16 blocks do not establish broader-corpus or architecture superiority"},
    "training_updates": 0,
    "test_search": "No alternative model, window, mixture grid, smoothing grid or suffix after seeing TEST",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def now():
    return datetime.now(timezone.utc).isoformat()


def _references():
    path = Path(__file__).with_name("byte_reference_baselines.py")
    spec = importlib.util.spec_from_file_location("byte_reference_baselines", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def freeze(results, output):
    output.mkdir(parents=True, exist_ok=True)
    path = output / "protocol.json"
    if path.exists():
        raise FileExistsError("Protocol already frozen; do not overwrite a prospective experiment")
    checkpoints = {}
    for seed in SEEDS:
        folder = results / "confirmation" / "wikitext_byte" / "baseline" / f"seed_{seed}"
        summary = json.loads((folder / "summary.json").read_text())
        checkpoint = folder / "checkpoint.pt"
        actual = sha(checkpoint.read_bytes())
        if actual != summary["checkpoint_sha256"]:
            raise ValueError("retained checkpoint hash mismatch")
        checkpoints[str(seed)] = {"checkpoint": str(checkpoint.resolve()), "checkpoint_sha256": actual,
                                  "model_tensor_sha256": summary["final_model_sha256"],
                                  "parameter_count": summary["parameter_count"]}
    record = {"protocol": PROTOCOL, "protocol_sha256": sha(canonical(PROTOCOL)),
              "frozen_at_utc": now(), "source_sha256": sha(Path(__file__).read_bytes()),
              "count_reference_source_sha256": sha(Path(__file__).with_name("byte_reference_baselines.py").read_bytes()),
              "checkpoints": checkpoints}
    write_json(path, record)
    return record


def source_interval(corpus_dir, role, source_manifest):
    """Read one declared source split only, validating pinned prior provenance."""
    import pyarrow.parquet as pq
    split = {"train": "train", "tune": "validation", "test": "test"}[role]
    parquet = corpus_dir / f"{split}-00000-of-00001.parquet"
    expected = source_manifest["splits"][role]
    if sha(parquet.read_bytes()) != expected["parquet_sha256"]:
        raise ValueError("pinned source parquet hash differs from original receipt")
    table = pq.read_table(parquet, columns=["text"])
    texts = [row for row in table.column("text").to_pylist() if row and row.strip()]
    raw = ("\n".join(texts) + "\n").encode("utf-8")
    old_prefix = raw[:expected["selected_bytes"]]
    if sha(old_prefix) != expected["selected_sha256"]:
        raise ValueError("original prefix reconstruction mismatch")
    start, stop = PROTOCOL["fresh_intervals"][role]
    selected = raw[start:stop]
    if len(selected) != stop-start:
        raise ValueError("source shorter than declared interval")
    if role != "train" and start < expected["selected_bytes"]:
        raise ValueError("new evaluation interval overlaps previous prefix")
    info = {"source_url": expected["source_url"], "parquet_sha256": expected["parquet_sha256"],
            "source_rows": table.num_rows, "source_stream_bytes": len(raw),
            "official_split": split, "byte_interval_half_open": [start, stop],
            "bytes": len(selected), "valid_targets": len(selected)-1, "sha256": sha(selected),
            "prior_prefix_sha256": expected["selected_sha256"], "overlap_with_prior_evaluation_bytes": 0 if role != "train" else None,
            "first_source_target_offset": start+1, "last_source_target_offset": stop-1}
    return selected, info


def count_probabilities(model, raw, smoothing):
    refs = _references()
    probabilities = np.empty((len(raw)-1, 256), dtype=np.float64)
    for i, (history, _) in enumerate(refs.events(raw, 64)):
        length = min(2, len(history))
        context = history[-length:]
        row = model["tables"][length].get(context, {})
        total = model["totals"][length].get(context, 0)
        probabilities[i, :] = smoothing / (total+256*smoothing)
        for token, count in row.items():
            probabilities[i, token] += count / (total+256*smoothing)
    if not np.allclose(probabilities.sum(1), 1., atol=1e-12, rtol=0):
        raise AssertionError("count probabilities do not normalize")
    return probabilities


def validate_probabilities(probabilities, targets):
    if probabilities.ndim != 2 or probabilities.shape != (len(targets), 256):
        raise ValueError("expected one vocabulary distribution per target")
    if (not np.isfinite(probabilities).all() or np.min(probabilities) < 0
            or not np.allclose(probabilities.sum(1), 1., rtol=0, atol=2e-6)):
        raise ValueError("invalid probability distribution")


def losses_and_metrics(probabilities, targets):
    validate_probabilities(probabilities, targets)
    target_probs = probabilities[np.arange(len(targets)), targets]
    if np.min(target_probs) <= 0:
        raise ValueError("nonpositive scored probability")
    losses = -np.log(target_probs)
    correct = int(np.sum(probabilities.argmax(1) == targets))
    nll = math.fsum(losses) / len(losses)
    return losses, {"nll_nats_per_byte": nll, "bits_per_byte": nll/math.log(2),
                    "accuracy": correct/len(losses), "correct": correct, "valid_targets": len(losses)}


def mix_probabilities(neural, counts, weight):
    if weight == 0:
        return neural
    if weight == 1:
        return counts
    return neural + weight*(counts-neural)


def select_weight(neural, counts, targets):
    candidates = []
    for weight in COUNT_WEIGHTS:
        _, metrics = losses_and_metrics(mix_probabilities(neural, counts, weight), targets)
        candidates.append({"count_weight": weight, **metrics})
    selected = min(candidates, key=lambda row: (row["nll_nats_per_byte"], row["count_weight"]))
    return {"count_weight": selected["count_weight"], "tune": selected, "tune_candidates": candidates}


def infer(model, raw, batch_size=64):
    import torch
    from singularity.training.data import _byte_windows
    rows = _byte_windows(raw, 64)
    valid = rows["labels"] != -100
    targets = rows["labels"][valid].numpy()
    if not np.array_equal(targets, np.frombuffer(raw[1:], dtype=np.uint8)):
        raise AssertionError("byte windows shift or duplicate targets")
    pieces = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(rows["labels"]), batch_size):
            x = rows["input_ids"][start:start+batch_size]
            mask = valid[start:start+batch_size]
            probabilities = model(x).double().softmax(-1)
            pieces.append(probabilities[mask].numpy())
    probabilities = np.concatenate(pieces)
    validate_probabilities(probabilities, targets)
    return probabilities, targets


def paired_blocks(differences):
    """One vector already averaged over seeds; contiguous 2048-target blocks."""
    differences = np.asarray(differences, dtype=np.float64)
    block_size = PROTOCOL["uncertainty"]["block_bytes"]
    sums = np.array([math.fsum(differences[i:i+block_size]) for i in range(0, len(differences), block_size)])
    sizes = np.array([len(differences[i:i+block_size]) for i in range(0, len(differences), block_size)])
    rng = np.random.default_rng(PROTOCOL["uncertainty"]["rng_seed"])
    indices = rng.integers(0, len(sums), size=(PROTOCOL["uncertainty"]["bootstrap_draws"], len(sums)))
    draws = sums[indices].sum(1) / sizes[indices].sum(1)
    return {"mean_difference_nats": math.fsum(differences)/len(differences),
            "block_count": len(sums), "block_target_counts": sizes.tolist(),
            "block_mean_differences": (sums/sizes).tolist(),
            "blocks_with_negative_mean": int(np.sum(sums < 0)),
            "percentile_95_interval": np.quantile(draws, [.025, .975]).tolist(),
            "interpretation": "negative favors mixture; paired descriptive block bootstrap, conditional on frozen models and this suffix"}


def execute(corpus_dir, output):
    import torch
    from singularity.training.runner import load_checkpoint, model_sha256
    started = time.perf_counter()
    protocol_path = output / "protocol.json"
    frozen = json.loads(protocol_path.read_text())
    if frozen["protocol_sha256"] != sha(canonical(PROTOCOL)) or frozen["source_sha256"] != sha(Path(__file__).read_bytes()):
        raise ValueError("frozen protocol/source changed")
    if frozen["count_reference_source_sha256"] != sha(Path(__file__).with_name("byte_reference_baselines.py").read_bytes()):
        raise ValueError("count reference source changed")
    if (output/"results.json").exists() or (output/"selection.json").exists():
        raise FileExistsError("this prospective experiment was already selected/scored; do not rerun TEST")
    source_manifest = json.loads((corpus_dir/"source_manifest.json").read_text())
    if source_manifest["revision"] != REVISION:
        raise ValueError("incorrect source revision")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    refs = _references()
    events = [{"event": "protocol_already_frozen", "at_utc": frozen["frozen_at_utc"]}]
    train, train_info = source_interval(corpus_dir, "train", source_manifest)
    tune, tune_info = source_interval(corpus_dir, "tune", source_manifest)
    events.append({"event": "TRAIN_and_fresh_TUNE_read", "at_utc": now()})
    stage = time.perf_counter()
    counts = refs.fit_counts(train, 64)
    train_count_fit_seconds = time.perf_counter()-stage
    targets = np.frombuffer(tune[1:], dtype=np.uint8)
    smoothing_candidates = []
    for smoothing in SMOOTHING_GRID:
        _, metrics = losses_and_metrics(count_probabilities(counts, tune, smoothing), targets)
        smoothing_candidates.append({"smoothing": smoothing, **metrics})
    smoothing = min(smoothing_candidates, key=lambda row: (row["nll_nats_per_byte"], row["smoothing"]))["smoothing"]
    tune_counts = count_probabilities(counts, tune, smoothing)
    models, selections, inference_times, tune_neural_sum = {}, {}, {}, None
    baseline_tune_metrics = {"count": losses_and_metrics(tune_counts, targets)[1]}
    for seed in SEEDS:
        receipt = frozen["checkpoints"][str(seed)]
        path = Path(receipt["checkpoint"])
        if sha(path.read_bytes()) != receipt["checkpoint_sha256"]:
            raise ValueError("checkpoint differs from freeze")
        model, _, _ = load_checkpoint(path)
        if model_sha256(model) != receipt["model_tensor_sha256"]:
            raise ValueError("model tensors differ from freeze")
        stage = time.perf_counter()
        probabilities, inferred_targets = infer(model, tune)
        inference_times[str(seed)] = {"fresh_tune_seconds": time.perf_counter()-stage}
        if not np.array_equal(inferred_targets, targets):
            raise AssertionError("target mismatch")
        selections[str(seed)] = select_weight(probabilities, tune_counts, targets)
        baseline_tune_metrics[f"neural_seed_{seed}"] = losses_and_metrics(probabilities, targets)[1]
        tune_neural_sum = probabilities.copy() if tune_neural_sum is None else tune_neural_sum + probabilities
        models[seed] = model
    tune_ensemble = tune_neural_sum / len(SEEDS)
    baseline_tune_metrics["neural_ensemble"] = losses_and_metrics(tune_ensemble, targets)[1]
    ensemble_selection = select_weight(tune_ensemble, tune_counts, targets)
    strongest_reference = min(baseline_tune_metrics, key=lambda key: (baseline_tune_metrics[key]["nll_nats_per_byte"], key))
    selection = {"schema": "singularity.predictive-mixture-selection/1", "frozen_at_utc": now(),
                 "protocol_sha256": frozen["protocol_sha256"], "selected_smoothing": smoothing,
                 "smoothing_candidates": smoothing_candidates, "per_seed": selections,
                 "ensemble": ensemble_selection, "unblended_reference_tune_metrics": baseline_tune_metrics,
                 "strongest_unblended_reference": strongest_reference,
                 "corpora": {"train": train_info, "tune": tune_info},
                 "fresh_test_read_before_selection": False}
    write_json(output/"selection.json", selection)
    events.append({"event": "all_TUNE_selections_frozen", "at_utc": selection["frozen_at_utc"]})
    del tune_counts, probabilities, tune_neural_sum, tune_ensemble
    # Do not move this read above the persistent selection receipt.
    test, test_info = source_interval(corpus_dir, "test", source_manifest)
    events.append({"event": "fresh_TEST_first_read", "at_utc": now()})
    stage = time.perf_counter()
    test_counts = count_probabilities(counts, test, smoothing)
    test_count_predict_seconds = time.perf_counter()-stage
    test_targets = np.frombuffer(test[1:], dtype=np.uint8)
    count_losses, count_metrics = losses_and_metrics(test_counts, test_targets)
    per_seed, neural_losses, mixture_losses, test_neural_sum = [], [], [], None
    arrays = {"targets": test_targets, "count_losses": count_losses}
    for seed in SEEDS:
        model = models[seed]
        stage = time.perf_counter()
        probabilities, inferred_targets = infer(model, test)
        inference_times[str(seed)]["fresh_test_seconds"] = time.perf_counter()-stage
        if not np.array_equal(test_targets, inferred_targets):
            raise AssertionError("TEST target mismatch")
        neural_loss, neural_metrics = losses_and_metrics(probabilities, test_targets)
        test_neural_sum = probabilities.copy() if test_neural_sum is None else test_neural_sum + probabilities
        weight = selections[str(seed)]["count_weight"]
        mixture_loss, mixture_metrics = losses_and_metrics(mix_probabilities(probabilities, test_counts, weight), test_targets)
        after = model_sha256(model)
        expected = frozen["checkpoints"][str(seed)]["model_tensor_sha256"]
        if after != expected:
            raise AssertionError("evaluation mutated neural tensors")
        if sha(Path(frozen["checkpoints"][str(seed)]["checkpoint"]).read_bytes()) != frozen["checkpoints"][str(seed)]["checkpoint_sha256"]:
            raise AssertionError("evaluation mutated checkpoint")
        neural_losses.append(neural_loss)
        mixture_losses.append(mixture_loss)
        arrays[f"neural_losses_seed_{seed}"] = neural_loss
        arrays[f"mixture_losses_seed_{seed}"] = mixture_loss
        per_seed.append({"seed": seed, "count_weight": weight, "neural": neural_metrics, "mixture": mixture_metrics,
                         "mixture_minus_neural_nats": mixture_metrics["nll_nats_per_byte"]-neural_metrics["nll_nats_per_byte"],
                         "relative_nll_reduction_vs_neural": 1-mixture_metrics["nll_nats_per_byte"]/neural_metrics["nll_nats_per_byte"],
                         "mixture_minus_count_nats": mixture_metrics["nll_nats_per_byte"]-count_metrics["nll_nats_per_byte"],
                         "neural_test_inference_passes": 1, "neural_tensors_unchanged": True, "model_tensor_sha256_after": after})
    mean_neural = np.stack(neural_losses).mean(0)
    mean_mixture = np.stack(mixture_losses).mean(0)
    test_ensemble = test_neural_sum / len(SEEDS)
    ensemble_losses, ensemble_metrics = losses_and_metrics(test_ensemble, test_targets)
    ensemble_weight = ensemble_selection["count_weight"]
    ensemble_mix_losses, ensemble_mix_metrics = losses_and_metrics(mix_probabilities(test_ensemble, test_counts, ensemble_weight), test_targets)
    arrays["neural_ensemble_losses"] = ensemble_losses
    arrays["ensemble_mixture_losses"] = ensemble_mix_losses
    if strongest_reference == "count":
        reference_losses, reference_metrics = count_losses, count_metrics
    elif strongest_reference == "neural_ensemble":
        reference_losses, reference_metrics = ensemble_losses, ensemble_metrics
    else:
        ref_seed = int(strongest_reference.rsplit("_", 1)[1])
        reference_losses = arrays[f"neural_losses_seed_{ref_seed}"]
        reference_metrics = next(row["neural"] for row in per_seed if row["seed"] == ref_seed)
    secondary = {"count_weight": ensemble_weight, "neural_ensemble": ensemble_metrics,
                 "ensemble_mixture": ensemble_mix_metrics,
                 "strongest_unblended_reference_selected_on_TUNE": strongest_reference,
                 "strongest_unblended_reference": reference_metrics,
                 "paired_mixture_minus_neural_ensemble": paired_blocks(ensemble_mix_losses-ensemble_losses),
                 "paired_mixture_minus_strongest_reference": paired_blocks(ensemble_mix_losses-reference_losses),
                 "relative_nll_reduction_vs_neural_ensemble": 1-ensemble_mix_metrics["nll_nats_per_byte"]/ensemble_metrics["nll_nats_per_byte"],
                 "relative_nll_reduction_vs_strongest_reference": 1-ensemble_mix_metrics["nll_nats_per_byte"]/reference_metrics["nll_nats_per_byte"],
                 "neural_models_per_prediction": 3, "neural_parameter_count": 3*frozen["checkpoints"][str(SEEDS[0])]["parameter_count"]}
    aggregate = {}
    for name in ("neural", "mixture"):
        aggregate[name] = {key: math.fsum(row[name][key] for row in per_seed)/len(SEEDS)
                           for key in ("nll_nats_per_byte", "bits_per_byte", "accuracy")}
    aggregate["count"] = count_metrics
    aggregate["mixture_relative_nll_reduction_vs_neural"] = 1-aggregate["mixture"]["nll_nats_per_byte"]/aggregate["neural"]["nll_nats_per_byte"]
    aggregate["mixture_relative_nll_reduction_vs_count"] = 1-aggregate["mixture"]["nll_nats_per_byte"]/count_metrics["nll_nats_per_byte"]
    aggregate["paired_mixture_minus_neural"] = paired_blocks(mean_mixture-mean_neural)
    aggregate["paired_mixture_minus_count"] = paired_blocks(mean_mixture-count_losses)
    events.append({"event": "declared_TEST_comparisons_completed", "at_utc": now()})
    np.savez_compressed(output/"paired_test_losses.npz", **arrays)
    arrays_sha = sha((output/"paired_test_losses.npz").read_bytes())
    report = {"schema": "singularity.predictive-mixture-results/1", "created_at_utc": now(),
              "protocol_sha256": frozen["protocol_sha256"], "selection_sha256": sha((output/"selection.json").read_bytes()),
              "source_sha256": frozen["source_sha256"], "corpora": {"train": train_info, "tune": tune_info, "test": test_info},
              "selected_smoothing": smoothing, "count_test": count_metrics, "per_seed": per_seed, "aggregate": aggregate,
              "secondary_ensemble": secondary,
              "training_updates": 0, "neural_parameter_count_each": frozen["checkpoints"][str(SEEDS[0])]["parameter_count"],
              "state_unchanged": True, "events": events,
              "paired_losses_file": "paired_test_losses.npz", "paired_losses_sha256": arrays_sha,
              "timing_seconds": {"train_count_fit": train_count_fit_seconds, "test_count_predictions": test_count_predict_seconds,
                                 "neural_inference": inference_times, "total": time.perf_counter()-started},
              "scope": "A new suffix from the same named official dataset splits, not a new corpus. Ordinary count/neural ensembling improves if measured; no optimizer or training acceleration claim. All three previously retained fixed AdamW seeds reported."}
    write_json(output/"results.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("applications/training_lab/results"))
    parser.add_argument("--output", type=Path, default=Path("applications/training_lab/results/predictive_mixture"))
    parser.add_argument("--corpus-dir", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--freeze", action="store_true")
    action.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        result = freeze(args.results, args.output)
        print("Protocol frozen", result["protocol_sha256"], result["frozen_at_utc"])
    else:
        if args.corpus_dir is None:
            parser.error("--execute requires --corpus-dir")
        result = execute(args.corpus_dir, args.output)
        print(json.dumps(result["aggregate"], indent=2))


if __name__ == "__main__":
    main()
