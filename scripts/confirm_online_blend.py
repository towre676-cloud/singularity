#!/usr/bin/env python3
"""Freeze, then confirm causal Bayesian blend aggregation on a disjoint suffix.

The mathematical regret bound is standard. This experiment checks its numerical
identity and predictive behavior with our three frozen byte checkpoints. The
posterior receives each TEST target only after that target has been predicted;
this is online adaptation to past targets, not frozen calibration on TEST.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import time

import numpy as np


SEEDS = (1000, 1001, 1002)
REVISION = "b08601e04326c79dfdd32d625aee71d232d685c3"
PROTOCOL = {
    "schema": "singularity.online-blend-protocol/1",
    "purpose": "Prospective causal prediction and exact log-loss-regret audit on a new disjoint suffix",
    "method": "Standard equal-prior Bayesian aggregation of 21 fixed convex neural/count mixtures; no novelty claim",
    "source": {"dataset": "Salesforce/wikitext", "configuration": "wikitext-2-raw-v1", "revision": REVISION,
               "stream": "UTF-8 newline join of nonempty non-whitespace rows with terminal newline"},
    "train_interval_half_open": [0, 262144],
    "fresh_official_test_interval_half_open": [98304, 131072],
    "prior_official_test_intervals": [[0,32768], [32768,65536], [65536,98304]],
    "fresh_interval_selection": "Fixed before reading this suffix; no alternate suffix after scores",
    "seeds": list(SEEDS),
    "neural_experts": "All three retained fixed AdamW wikitext_byte baseline checkpoints; no seed selection or neural updates",
    "count_expert": {"order": 3, "fit": "same original TRAIN prefix only", "smoothing": .01,
                     "smoothing_source": "already frozen primary predictive_mixture fresh-TUNE selection; not selected on this TEST suffix"},
    "count_weight_grid": [i/20 for i in range(21)],
    "prior": "equal 1/21 mass on every fixed grid weight, reset once at start of this new suffix",
    "expert_prediction": "p_alpha=(1-alpha)*p_neural+alpha*p_count",
    "online_prediction": "posterior probability average of all fixed-grid experts, equivalent to mixture at prior-to-current-target posterior mean alpha",
    "causal_order": "for t: obtain causal expert predictions; predict with posterior from targets strictly before t; score target t; only then multiply posterior by expert likelihood of target t and renormalize",
    "online_adaptation": "Past TEST targets update only mixture posterior, never expert parameters/counts. This is a causal online predictor, not a frozen-weight predictor.",
    "posterior_numerics": "stable logsumexp with normalized log posterior; no clipping or target-dependent tuning",
    "context": "64-input masked windows; every noninitial suffix byte once; count contexts reset with neural windows; blend posterior persists across windows",
    "comparator": "same neural and count experts, plus each seed's fixed mixture weight selected earlier on a separate official TUNE suffix",
    "regret_reference": "best fixed grid weight evaluated retrospectively only for audit; never used to choose online predictions",
    "guarantee": "L_online=-log((1/K)*sum_alpha exp(-L_alpha)) <= min_alpha L_alpha + log(K), K=21, cumulative natural-log loss",
    "metrics": ["NLL nats/byte", "bits/byte", "top-1 accuracy", "exact marginal-likelihood identity residual", "regret bound slack", "all seed paired effects"],
    "uncertainty": "paired contiguous2048-target block bootstrap,10000draws,seed731923; average same-byte model losses before resampling; descriptive conditional on this suffix and these frozen models",
    "timing": "report model load, TRAIN fit, count prediction, neural inference, frozen blending, online update/prediction and total wall seconds; shared CPU, no speedup claim",
    "one_neural_forward_pass_per_checkpoint": True,
    "test_policy": "freeze protocol, dependencies and previous primary selection before first new TEST read; one pass per seed; no tuning after suffix scores",
    "scope": "Same dataset, one new32KiB interval, three frozen models. Universal log-loss bound needs positive target mass from at least one grid expert; empirical improvements do not establish superiority on new corpora.",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path = Path(path)
    raw = json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode()+b"\n"
    temporary = path.with_suffix(path.suffix+".tmp")
    with temporary.open("wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    if path.read_bytes() != raw:
        raise IOError("receipt persistence verification failed")


def dependency_paths():
    root = Path(__file__).resolve().parents[1]
    return {name: root/name for name in (
        "scripts/confirm_online_blend.py", "scripts/confirm_predictive_mixture.py",
        "src/singularity/training/online_blend.py", "src/singularity/training/byte_experts.py",
        "src/singularity/training/runner.py", "src/singularity/training/models.py", "src/singularity/training/data.py")}


def primary_module():
    path = Path(__file__).with_name("confirm_predictive_mixture.py")
    spec = importlib.util.spec_from_file_location("primary_mixture_for_online", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def freeze(results, output):
    output.mkdir(parents=True, exist_ok=True)
    if (output/"protocol.json").exists():
        raise FileExistsError("online protocol already frozen")
    primary = results/"predictive_mixture"
    selection = json.loads((primary/"selection.json").read_text())
    if selection["selected_smoothing"] != PROTOCOL["count_expert"]["smoothing"]:
        raise ValueError("fixed inherited smoothing differs from primary TUNE receipt")
    frozen_primary = json.loads((primary/"protocol.json").read_text())
    checkpoints = frozen_primary["checkpoints"]
    for seed in SEEDS:
        checkpoint = Path(checkpoints[str(seed)]["checkpoint"])
        if sha(checkpoint.read_bytes()) != checkpoints[str(seed)]["checkpoint_sha256"]:
            raise ValueError("checkpoint differs from previous frozen identity")
    record = {"protocol": PROTOCOL, "protocol_sha256": sha(canonical(PROTOCOL)), "frozen_at_utc": now(),
              "dependency_sha256": {name: sha(path.read_bytes()) for name,path in dependency_paths().items()},
              "primary_selection_sha256": sha((primary/"selection.json").read_bytes()),
              "fixed_comparator_count_weights": {str(seed): selection["per_seed"][str(seed)]["count_weight"] for seed in SEEDS},
              "checkpoints": checkpoints,
              "fresh_test_suffix_read_before_freeze": False}
    write_json(output/"protocol.json", record)
    return record


def source_interval(corpus_dir, role, manifest):
    import pyarrow.parquet as pq
    expected = manifest["splits"][role]
    split = "train" if role == "train" else "test"
    path = corpus_dir/f"{split}-00000-of-00001.parquet"
    if sha(path.read_bytes()) != expected["parquet_sha256"]:
        raise ValueError("pinned original parquet identity mismatch")
    table = pq.read_table(path, columns=["text"])
    rows = [row for row in table.column("text").to_pylist() if row and row.strip()]
    raw = ("\n".join(rows)+"\n").encode("utf-8")
    if sha(raw[:expected["selected_bytes"]]) != expected["selected_sha256"]:
        raise ValueError("original prefix reconstruction mismatch")
    start, stop = PROTOCOL["train_interval_half_open" if role == "train" else "fresh_official_test_interval_half_open"]
    selected = raw[start:stop]
    if len(selected) != stop-start:
        raise ValueError("declared source interval unavailable")
    if role == "test" and any(max(start,left)<min(stop,right) for left,right in PROTOCOL["prior_official_test_intervals"]):
        raise ValueError("new suffix overlaps a previous TEST interval")
    return selected, {"source_url": expected["source_url"], "parquet_sha256": expected["parquet_sha256"],
                      "official_split": split, "byte_interval_half_open": [start,stop], "bytes": len(selected),
                      "sha256": sha(selected), "valid_targets": len(selected)-1,
                      "first_source_target_offset": start+1, "last_source_target_offset": stop-1,
                      "overlap_with_prior_test_intervals": 0 if role == "test" else None}


def count_predictions(expert, raw):
    from singularity.training.byte_experts import byte_events
    values = np.empty((len(raw)-1,256), dtype=np.float64)
    cache = {}
    for index,(history,_) in enumerate(byte_events(raw,expert.sequence_length)):
        if history not in cache:
            cache[history] = np.asarray(expert.probabilities(history), dtype=np.float64)
        values[index] = cache[history]
    return values


def metrics(losses, correct):
    nll = math.fsum(losses)/len(losses)
    return {"nll_nats_per_byte": nll, "bits_per_byte": nll/math.log(2),
            "accuracy": int(np.sum(correct))/len(losses), "correct": int(np.sum(correct)), "valid_targets": len(losses)}


def execute(results, output, corpus_dir):
    import torch
    from singularity.training.byte_experts import CountByteExpert
    from singularity.training.online_blend import score_online_probabilities
    from singularity.training.runner import load_checkpoint, model_sha256
    started = time.perf_counter()
    frozen = json.loads((output/"protocol.json").read_text())
    if frozen["protocol_sha256"] != sha(canonical(PROTOCOL)):
        raise ValueError("protocol differs from frozen receipt")
    for name,path in dependency_paths().items():
        if frozen["dependency_sha256"][name] != sha(path.read_bytes()):
            raise ValueError("source changed after freeze: "+name)
    if frozen["primary_selection_sha256"] != sha((results/"predictive_mixture"/"selection.json").read_bytes()):
        raise ValueError("primary comparator changed after freeze")
    if (output/"results.json").exists() or (output/"target_audit.npz").exists():
        raise FileExistsError("fresh suffix already scored; no repeated prospective execution")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    primary = primary_module()
    manifest = json.loads((corpus_dir/"source_manifest.json").read_text())
    if manifest["revision"] != REVISION:
        raise ValueError("incorrect WikiText revision")
    events = [{"event": "protocol_frozen", "at_utc": frozen["frozen_at_utc"]}]
    train,train_info = source_interval(corpus_dir,"train",manifest)
    stage = time.perf_counter()
    expert = CountByteExpert.fit(train,order=3,alpha=.01,sequence_length=64)
    count_fit_seconds = time.perf_counter()-stage
    expert_identity = sha(canonical(expert.to_dict()))
    models,load_times = {},{}
    for seed in SEEDS:
        record = frozen["checkpoints"][str(seed)]
        path = Path(record["checkpoint"])
        if sha(path.read_bytes()) != record["checkpoint_sha256"]:
            raise ValueError("neural checkpoint changed after freeze")
        stage = time.perf_counter()
        model,_,_ = load_checkpoint(path)
        load_times[str(seed)] = time.perf_counter()-stage
        if model_sha256(model) != record["model_tensor_sha256"]:
            raise ValueError("checkpoint tensor identity mismatch")
        models[seed] = model
    # This is the first permitted access to the held-out suffix contents.
    events.append({"event": "fresh_TEST_first_read_started", "at_utc": now()})
    test,test_info = source_interval(corpus_dir,"test",manifest)
    targets = np.frombuffer(test[1:],dtype=np.uint8)
    stage = time.perf_counter()
    counts = count_predictions(expert,test)
    count_predict_seconds = time.perf_counter()-stage
    count_losses,count_metrics = primary.losses_and_metrics(counts,targets)
    arrays = {"targets": targets,"count_losses":count_losses}
    per_seed,timings = [],{}
    for seed in SEEDS:
        stage = time.perf_counter()
        neural,inferred_targets = primary.infer(models[seed],test)
        inference_seconds = time.perf_counter()-stage
        if not np.array_equal(targets,inferred_targets):
            raise AssertionError("neural targets misaligned")
        neural_losses,neural_metrics = primary.losses_and_metrics(neural,targets)
        fixed_alpha = frozen["fixed_comparator_count_weights"][str(seed)]
        stage = time.perf_counter()
        fixed = primary.mix_probabilities(neural,counts,fixed_alpha)
        fixed_losses,fixed_metrics = primary.losses_and_metrics(fixed,targets)
        fixed_seconds = time.perf_counter()-stage
        del fixed
        stage = time.perf_counter()
        online = score_online_probabilities(neural,counts,targets)
        online_seconds = time.perf_counter()-stage
        online_metrics = metrics(online["target_nll_nats"],online["target_correct"])
        audit = online["audit"]
        if abs(audit["marginal_likelihood_identity_error_nats"]) > 1e-6 or audit["bound_slack_nats"] < -1e-6:
            raise AssertionError("marginal likelihood identity or regret bound failed")
        if model_sha256(models[seed]) != frozen["checkpoints"][str(seed)]["model_tensor_sha256"]:
            raise AssertionError("online inference mutated neural tensors")
        arrays[f"neural_losses_seed_{seed}"] = neural_losses
        arrays[f"fixed_mixture_losses_seed_{seed}"] = fixed_losses
        arrays[f"online_losses_seed_{seed}"] = online["target_nll_nats"]
        arrays[f"prior_to_target_count_weights_seed_{seed}"] = online["prior_to_target_count_weights"]
        per_seed.append({"seed":seed,"neural":neural_metrics,"fixed_mixture":fixed_metrics,"online":online_metrics,
                         "fixed_comparator_count_weight":fixed_alpha,"regret_audit":audit,
                         "relative_online_nll_reduction_vs_neural":1-online_metrics["nll_nats_per_byte"]/neural_metrics["nll_nats_per_byte"],
                         "relative_online_nll_reduction_vs_fixed_mixture":1-online_metrics["nll_nats_per_byte"]/fixed_metrics["nll_nats_per_byte"],
                         "neural_tensors_unchanged":True,"neural_inference_passes":1})
        timings[str(seed)] = {"checkpoint_load":load_times[str(seed)],"neural_inference":inference_seconds,
                               "fixed_mixture_blend_and_score":fixed_seconds,"online_blend_update_and_score":online_seconds,
                               "inclusive_online_inference_plus_shared_count_predictions":inference_seconds+online_seconds+count_predict_seconds,
                               "inclusive_fixed_inference_plus_shared_count_predictions":inference_seconds+fixed_seconds+count_predict_seconds}
    if sha(canonical(expert.to_dict())) != expert_identity:
        raise AssertionError("online prediction mutated TRAIN-only counts")
    mean_losses = {name:np.stack([arrays[f"{key}_seed_{seed}"] for seed in SEEDS]).mean(0)
                   for name,key in (("neural","neural_losses"),("fixed_mixture","fixed_mixture_losses"),("online","online_losses"))}
    aggregate = {name:{metric:math.fsum(row[name][metric] for row in per_seed)/len(SEEDS)
                       for metric in ("nll_nats_per_byte","bits_per_byte","accuracy")} for name in mean_losses}
    aggregate["count"] = count_metrics
    aggregate["relative_online_nll_reduction_vs_neural"] = 1-aggregate["online"]["nll_nats_per_byte"]/aggregate["neural"]["nll_nats_per_byte"]
    aggregate["relative_online_nll_reduction_vs_fixed_mixture"] = 1-aggregate["online"]["nll_nats_per_byte"]/aggregate["fixed_mixture"]["nll_nats_per_byte"]
    aggregate["paired_online_minus_neural"] = primary.paired_blocks(mean_losses["online"]-mean_losses["neural"])
    aggregate["paired_online_minus_fixed_mixture"] = primary.paired_blocks(mean_losses["online"]-mean_losses["fixed_mixture"])
    aggregate["paired_online_minus_count"] = primary.paired_blocks(mean_losses["online"]-count_losses)
    np.savez_compressed(output/"target_audit.npz",**arrays)
    events.append({"event":"all_declared_TEST_comparisons_completed","at_utc":now()})
    report = {"schema":"singularity.online-blend-results/1","created_at_utc":now(),"protocol_sha256":frozen["protocol_sha256"],
              "protocol_receipt_sha256":sha((output/"protocol.json").read_bytes()),"corpora":{"train":train_info,"test":test_info},
              "count_expert_sha256":expert_identity,"count_expert_and_neural_parameters_unchanged":True,
              "past_target_posterior_updates_per_seed":len(targets),"neural_training_updates":0,
              "per_seed":per_seed,"aggregate":aggregate,"events":events,
              "uniform_regret_penalty_nats":math.log(21),"uniform_regret_penalty_nats_per_target":math.log(21)/len(targets),
              "target_audit_file":"target_audit.npz","target_audit_sha256":sha((output/"target_audit.npz").read_bytes()),
              "timing_seconds":{"TRAIN_count_fit":count_fit_seconds,"TEST_count_predictions":count_predict_seconds,
                                "per_seed":timings,"total":time.perf_counter()-started},
              "interpretation":"Standard universal cumulative log-loss bound versus fixed grid, numerically checked; positive empirical effects are conditional on this suffix. Online posterior sees only earlier TEST targets; fixed comparator uses earlier separate TUNE. No optimizer, training acceleration, model accuracy universality or inference speedup claim."}
    write_json(output/"results.json",report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results",type=Path,default=Path("applications/training_lab/results"))
    parser.add_argument("--output",type=Path,default=Path("applications/training_lab/results/online_blend"))
    parser.add_argument("--corpus-dir",type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze",action="store_true")
    group.add_argument("--execute",action="store_true")
    args = parser.parse_args()
    if args.freeze:
        record = freeze(args.results,args.output)
        print("Protocol frozen",record["protocol_sha256"],record["frozen_at_utc"])
    else:
        if args.corpus_dir is None:
            parser.error("--execute requires --corpus-dir")
        report = execute(args.results,args.output,args.corpus_dir)
        print(json.dumps(report["aggregate"],indent=2))
        print("Regret penalty:",report["uniform_regret_penalty_nats"],"nats total per seed")


if __name__ == "__main__":
    main()
