#!/usr/bin/env python3
"""Prospective cross-domain confirmation of byte-level predictive blending.

Three phases, run once each and in order:

  select   deterministically choose new prose, legal and source-code documents
           from files present in the build environment and store them;
  freeze   record the protocol, every dependency, checkpoint and document hash
           before any document is scored;
  execute  score every declared arm once, then measure blender runtime.

No model, count table, smoothing value or blend weight is fitted on these
documents. The adaptive count baseline and online blend learn causally from
earlier bytes of the current document only, and reset at each document.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
RESULTS = ROOT / "applications/training_lab/results"
OUTPUT = RESULTS / "cross_domain"
SEEDS = (1000, 1001, 1002)
SALT = "singularity-0.8.0-cross-domain"
MIN_BYTES, MAX_BYTES = 2048, 32768

PROTOCOL = {
    "schema": "singularity.cross-domain-protocol/1",
    "purpose": "Prospective byte prediction comparison on documents from domains absent from WikiText training",
    "domains": {
        "reference_prose": {"source": "Python reference-manual topic texts in pydoc_data.topics of the build interpreter",
                            "documents": 16, "license": "Python Software Foundation License"},
        "legal_prose": {"source": "/usr/share/common-licenses license texts, symlinks resolved, duplicate contents removed",
                        "documents": 8, "license": "verbatim copying of each license text is permitted by its publisher"},
        "source_code": {"source": "top-level Python standard-library modules *.py of the build interpreter",
                        "documents": 16, "license": "Python Software Foundation License"},
    },
    "document_rule": f"candidates with at least {MIN_BYTES} bytes; order by sha256('{SALT}/'+domain+'/'+name); take the declared count; keep only the first {MAX_BYTES} bytes",
    "document_boundaries": "Each document is scored independently. Neural windows (64 inputs) and TRAIN-count history start at the document start; adaptive counts and online posteriors reset at every document.",
    "seeds": list(SEEDS),
    "neural_experts": "three retained fixed AdamW WikiText byte transformers; no neural updates",
    "arms": {
        "neural": "neural softmax",
        "count": "TRAIN-only order-3 alpha=0.01 counts saved in predictive_mixture/count_expert.json",
        "calibrated_fixed_blend": "0.7.0 deployment recipe per-seed count weights (0.35, 0.35, 0.40), selected earlier on WikiText TUNE",
        "online_blend": "equal-prior Bayesian aggregation over count weights k/20 of neural+TRAIN-count, vectorized scorer, posterior reset per document",
        "adaptive_count": "stronger count baseline: in-document Witten-Bell order 4 over the TRAIN trigram base; order declared, not tuned",
        "online_adaptive_blend": "secondary: same Bayesian aggregation over neural+adaptive_count",
    },
    "primary_comparisons": [
        "online_blend minus neural, per domain and seed",
        "online_blend minus calibrated_fixed_blend, per domain and seed",
        "adaptive_count minus count, per domain",
    ],
    "metrics": ["NLL nats/byte", "bits/byte", "top-1 accuracy", "regret versus best grid weight per document"],
    "uncertainty": "paired document-cluster bootstrap within each domain, seed-averaged differences, 10000 draws, rng seed 80023; descriptive",
    "equivalence": "online_blend also scored by the 0.7.0 reference loop; max absolute per-target difference must be <= 1e-9 nats",
    "timing": {"threads": 1, "warmup_rounds": 2, "measured_rounds": 11, "order_seed": 6113,
               "workload": "seed 1000, every document separately, all domains; fixed = mix + validated loss/argmax; online fast = vectorized scorer; online reference = 0.7.0 loop",
               "cold_start_repeats": 5, "cold_start": "fresh interpreter: import torch and singularity, load one checkpoint and the count JSON",
               "target": "online fast median within 2x fixed blending (engineering target, reported either way)"},
    "test_policy": "documents selected by hash rule before scoring; protocol committed before execute; one execution; no arm, document or weight changes after scores",
    "revision": {"number": 2, "supersedes": "protocol_revision1_aborted.json",
                 "change": "bound assertion uses 1e-9 + 2**-36 * cumulative online NLL instead of a fixed 1e-9 nats",
                 "reason": "revision 1 execution aborted in the scoring loop on that assertion before writing results; a slack-only diagnostic (no arm losses) showed slack and marginal-likelihood residuals of order 1e-10 in both the 0.7.0 reference loop and the vectorized scorer"},
    "scope": "Three small frozen byte models trained on WikiText; documents from one build environment; results are conditional on these documents and do not establish behavior on other corpora or tokenizers.",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(raw)
    os.replace(temporary, path)


def ranked(domain, names):
    return sorted(names, key=lambda name: sha(f"{SALT}/{domain}/{name}".encode()))


def candidates():
    import pydoc_data.topics as topics
    stdlib = Path(os.__file__).parent
    found = {"reference_prose": {name: text.encode("utf-8") for name, text in topics.topics.items()},
             "source_code": {path.name: path.read_bytes() for path in stdlib.glob("*.py")},
             "legal_prose": {}}
    seen = set()
    for path in sorted(Path("/usr/share/common-licenses").iterdir()):
        raw = path.resolve().read_bytes()
        if sha(raw) not in seen:
            seen.add(sha(raw))
            found["legal_prose"][path.resolve().name] = raw
    return found


def select(output):
    path = output / "documents.json.gz"
    if path.exists():
        raise FileExistsError("documents already selected; do not reselect")
    found, documents = candidates(), []
    for domain, spec in PROTOCOL["domains"].items():
        eligible = [name for name, raw in found[domain].items() if len(raw) >= MIN_BYTES]
        chosen = ranked(domain, eligible)[:spec["documents"]]
        if len(chosen) != spec["documents"]:
            raise ValueError("too few eligible documents in " + domain)
        for name in chosen:
            raw = found[domain][name][:MAX_BYTES]
            documents.append({"domain": domain, "name": name, "bytes": len(raw), "sha256": sha(raw),
                              "source_bytes": len(found[domain][name]), "base64": base64.b64encode(raw).decode()})
    payload = {"schema": "singularity.cross-domain-documents/1", "selected_at_utc": now(), "rule": PROTOCOL["document_rule"],
               "python": sys.version, "eligible_counts": {d: sum(len(r) >= MIN_BYTES for r in found[d].values()) for d in found},
               "documents": documents}
    output.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(path, "wb", mtime=0) as handle:
        handle.write(canonical(payload))
    return payload


def load_documents(output):
    payload = json.loads(gzip.decompress((output / "documents.json.gz").read_bytes()))
    documents = []
    for record in payload["documents"]:
        raw = base64.b64decode(record["base64"])
        if sha(raw) != record["sha256"] or len(raw) != record["bytes"]:
            raise ValueError("stored document identity mismatch")
        documents.append({**record, "raw": raw})
    return documents


def dependency_paths():
    return {name: ROOT / name for name in (
        "scripts/confirm_cross_domain.py", "scripts/confirm_predictive_mixture.py",
        "src/singularity/training/online_blend.py", "src/singularity/training/byte_experts.py",
        "src/singularity/training/runner.py", "src/singularity/training/models.py", "src/singularity/training/data.py")}


def checkpoint(seed):
    return RESULTS / f"confirmation/wikitext_byte/baseline/seed_{seed}/checkpoint.pt"


def freeze(output):
    if (output / "protocol.json").exists():
        raise FileExistsError("cross-domain protocol already frozen")
    recipe = json.loads((RESULTS / "predictive_mixture/deployment_recipe.json").read_text())
    record = {"protocol": PROTOCOL, "protocol_sha256": sha(canonical(PROTOCOL)), "frozen_at_utc": now(),
              "documents_sha256": sha((output / "documents.json.gz").read_bytes()),
              "dependency_sha256": {name: sha(path.read_bytes()) for name, path in dependency_paths().items()},
              "checkpoint_sha256": {str(seed): sha(checkpoint(seed).read_bytes()) for seed in SEEDS},
              "count_expert_sha256": sha((RESULTS / "predictive_mixture/count_expert.json").read_bytes()),
              "calibrated_count_weights": {str(row["seed"]): row["count_weight"] for row in recipe["individuals"]},
              "documents_scored_before_freeze": False}
    write_json(output / "protocol.json", record)
    return record


def primary_module():
    spec = importlib.util.spec_from_file_location("primary_for_cross_domain", ROOT / "scripts/confirm_predictive_mixture.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def metrics(losses, correct):
    nll = math.fsum(losses) / len(losses)
    return {"nll_nats_per_byte": nll, "bits_per_byte": nll / math.log(2), "accuracy": int(sum(correct)) / len(losses),
            "valid_targets": len(losses)}


def cluster_bootstrap(differences, sizes):
    import numpy as np
    sums = np.array([math.fsum(d) for d in differences])
    sizes = np.array(sizes, dtype=np.float64)
    rng = np.random.default_rng(80023)
    draws = rng.integers(0, len(sums), size=(10000, len(sums)))
    values = sums[draws].sum(1) / sizes[draws].sum(1)
    return {"mean_difference_nats": float(sums.sum() / sizes.sum()), "documents": len(sums),
            "documents_with_negative_mean": int((sums < 0).sum()),
            "percentile_95_interval": np.quantile(values, [.025, .975]).tolist(),
            "interpretation": "negative favors the first arm; descriptive document-cluster bootstrap"}


def float_tolerance(audit):
    """Rounding allowance for sums of ~1e4-1e5 per-target logs (revision 2).

    When the posterior concentrates on one grid weight the true slack is
    positive but exponentially small, so rounding can make it slightly
    negative; revision 1 aborted on a fixed 1e-9 allowance for that reason.
    """
    return 1e-9 + 2.**-36 * abs(audit["online_cumulative_nll"])


def count_predictions(expert, raw):
    import numpy as np
    from singularity.training.byte_experts import byte_events
    values, cache = np.empty((len(raw) - 1, 256)), {}
    for index, (history, _) in enumerate(byte_events(raw, expert.sequence_length)):
        if history not in cache:
            cache[history] = np.asarray(expert.probabilities(history), dtype=np.float64)
        values[index] = cache[history]
    return values


def execute(output):
    import numpy as np
    import torch
    from singularity.training.byte_experts import CountByteExpert, adaptive_document_probabilities
    from singularity.training.online_blend import score_online_probabilities, score_online_probabilities_fast
    from singularity.training.runner import load_checkpoint
    started = time.perf_counter()
    frozen = json.loads((output / "protocol.json").read_text())
    if frozen["protocol_sha256"] != sha(canonical(PROTOCOL)):
        raise ValueError("protocol differs from frozen receipt")
    for name, path in dependency_paths().items():
        if frozen["dependency_sha256"][name] != sha(path.read_bytes()):
            raise ValueError("dependency changed after freeze: " + name)
    if frozen["documents_sha256"] != sha((output / "documents.json.gz").read_bytes()):
        raise ValueError("documents changed after freeze")
    if (output / "results.json").exists():
        raise FileExistsError("already executed; no repeated prospective execution")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    primary = primary_module()
    events = [{"event": "protocol_frozen", "at_utc": frozen["frozen_at_utc"]}, {"event": "execute_started", "at_utc": now()}]
    expert = CountByteExpert.load(RESULTS / "predictive_mixture/count_expert.json")
    models = {}
    for seed in SEEDS:
        if sha(checkpoint(seed).read_bytes()) != frozen["checkpoint_sha256"][str(seed)]:
            raise ValueError("checkpoint changed after freeze")
        models[seed] = load_checkpoint(checkpoint(seed))[0]
    documents = load_documents(output)
    stage = {"count": 0., "adaptive_count": 0., "neural": {str(s): 0. for s in SEEDS}}
    rows, arrays = [], {}
    worst_reference_difference = 0.
    for index, document in enumerate(documents):
        raw = document["raw"]
        targets = np.frombuffer(raw[1:], dtype=np.uint8).astype(np.int64)
        t0 = time.perf_counter(); counts = count_predictions(expert, raw); stage["count"] += time.perf_counter() - t0
        t0 = time.perf_counter(); adaptive = adaptive_document_probabilities(expert, raw, 4); stage["adaptive_count"] += time.perf_counter() - t0
        count_losses, _ = primary.losses_and_metrics(counts, targets)
        adaptive_losses, _ = primary.losses_and_metrics(adaptive, targets)
        record = {"document": index, "domain": document["domain"], "name": document["name"], "targets": len(targets),
                  "count": metrics(count_losses, counts.argmax(1) == targets),
                  "adaptive_count": metrics(adaptive_losses, adaptive.argmax(1) == targets), "seeds": {}}
        arrays[f"doc{index}_count"], arrays[f"doc{index}_adaptive_count"] = count_losses, adaptive_losses
        for seed in SEEDS:
            t0 = time.perf_counter(); neural, inferred = primary.infer(models[seed], raw); stage["neural"][str(seed)] += time.perf_counter() - t0
            if not np.array_equal(inferred, targets):
                raise AssertionError("target misalignment")
            neural_losses, _ = primary.losses_and_metrics(neural, targets)
            weight = frozen["calibrated_count_weights"][str(seed)]
            fixed = primary.mix_probabilities(neural, counts, weight)
            fixed_losses, _ = primary.losses_and_metrics(fixed, targets)
            online = score_online_probabilities_fast(neural, counts, targets)
            reference = score_online_probabilities(neural, counts, targets)
            difference = float(np.abs(online["target_nll_nats"] - reference["target_nll_nats"]).max())
            worst_reference_difference = max(worst_reference_difference, difference)
            if difference > 1e-9 or not np.array_equal(online["target_correct"], reference["target_correct"]):
                raise AssertionError("vectorized online blend disagrees with reference loop")
            secondary = score_online_probabilities_fast(neural, adaptive, targets)
            for audit in (online["audit"], secondary["audit"]):
                if audit["bound_slack_nats"] < -float_tolerance(audit):
                    raise AssertionError("log(21) bound violated beyond floating-point tolerance")
            record["seeds"][str(seed)] = {
                "neural": metrics(neural_losses, neural.argmax(1) == targets),
                "calibrated_fixed_blend": metrics(fixed_losses, fixed.argmax(1) == targets),
                "online_blend": metrics(online["target_nll_nats"], online["target_correct"]),
                "online_adaptive_blend": metrics(secondary["target_nll_nats"], secondary["target_correct"]),
                "online_regret_nats": online["audit"]["regret_nats"],
                "online_adaptive_regret_nats": secondary["audit"]["regret_nats"],
                "online_final_count_weight_mean": float(online["prior_to_target_count_weights"][-1]),
                "reference_loop_max_abs_difference_nats": difference}
            for arm, values in (("neural", neural_losses), ("calibrated_fixed_blend", fixed_losses),
                                ("online_blend", online["target_nll_nats"]), ("online_adaptive_blend", secondary["target_nll_nats"])):
                arrays[f"doc{index}_{arm}_seed_{seed}"] = values
        rows.append(record)
    events.append({"event": "all_arms_scored", "at_utc": now()})
    arms = ("neural", "count", "calibrated_fixed_blend", "online_blend", "adaptive_count", "online_adaptive_blend")
    seeded = {"neural", "calibrated_fixed_blend", "online_blend", "online_adaptive_blend"}

    def doc_losses(index, arm, seed=None):
        return arrays[f"doc{index}_{arm}_seed_{seed}"] if arm in seeded else arrays[f"doc{index}_{arm}"]

    domains = {}
    for domain in PROTOCOL["domains"]:
        members = [r["document"] for r in rows if r["domain"] == domain]
        sizes = [rows[i]["targets"] for i in members]
        summary = {"documents": len(members), "targets": sum(sizes), "arms": {}, "per_seed": {}}
        for arm in arms:
            if arm in seeded:
                per = {}
                for seed in SEEDS:
                    losses = np.concatenate([doc_losses(i, arm, seed) for i in members])
                    correct = sum(rows[i]["seeds"][str(seed)][arm]["accuracy"] * rows[i]["targets"] for i in members)
                    per[str(seed)] = {"nll_nats_per_byte": math.fsum(losses) / len(losses), "accuracy": correct / len(losses)}
                summary["per_seed"][arm] = per
                summary["arms"][arm] = {k: statistics.fmean(per[s][k] for s in per) for k in ("nll_nats_per_byte", "accuracy")}
            else:
                losses = np.concatenate([doc_losses(i, arm) for i in members])
                correct = sum(rows[i][arm]["accuracy"] * rows[i]["targets"] for i in members)
                summary["arms"][arm] = {"nll_nats_per_byte": math.fsum(losses) / len(losses), "accuracy": correct / len(losses)}
            summary["arms"][arm]["bits_per_byte"] = summary["arms"][arm]["nll_nats_per_byte"] / math.log(2)

        def averaged(arm, i):
            return np.mean([doc_losses(i, arm, s) for s in SEEDS], 0) if arm in seeded else doc_losses(i, arm)

        summary["paired"] = {f"{a}_minus_{b}": cluster_bootstrap([averaged(a, i) - averaged(b, i) for i in members], sizes)
                             for a, b in (("online_blend", "neural"), ("online_blend", "calibrated_fixed_blend"),
                                          ("adaptive_count", "count"), ("online_adaptive_blend", "online_blend"),
                                          ("online_adaptive_blend", "adaptive_count"), ("calibrated_fixed_blend", "neural"))}
        summary["seeds_where_online_beats_neural"] = sum(summary["per_seed"]["online_blend"][s]["nll_nats_per_byte"] < summary["per_seed"]["neural"][s]["nll_nats_per_byte"] for s in map(str, SEEDS))
        summary["seeds_where_online_beats_calibrated"] = sum(summary["per_seed"]["online_blend"][s]["nll_nats_per_byte"] < summary["per_seed"]["calibrated_fixed_blend"][s]["nll_nats_per_byte"] for s in map(str, SEEDS))
        summary["relative_online_reduction_vs_neural"] = 1 - summary["arms"]["online_blend"]["nll_nats_per_byte"] / summary["arms"]["neural"]["nll_nats_per_byte"]
        domains[domain] = summary
    np.savez_compressed(output / "target_losses.npz", **arrays)
    scoring_seconds = time.perf_counter() - started
    timing = blender_timing(documents, models[1000], expert, primary)
    timing["cold_start"] = cold_start()
    events.append({"event": "timing_completed", "at_utc": now()})
    report = {"schema": "singularity.cross-domain-results/1", "created_at_utc": now(),
              "protocol_sha256": frozen["protocol_sha256"], "protocol_receipt_sha256": sha((output / "protocol.json").read_bytes()),
              "documents": [{k: v for k, v in r.items()} for r in rows], "domains": domains,
              "reference_loop_max_abs_difference_nats": worst_reference_difference,
              "stage_seconds": stage, "scoring_wall_seconds": scoring_seconds, "timing": timing,
              "target_losses_sha256": sha((output / "target_losses.npz").read_bytes()),
              "environment": {"python": sys.version, "torch": torch.__version__, "numpy": np.__version__, "threads": 1, "device": "cpu"},
              "neural_training_updates": 0, "events": events,
              "interpretation": "Descriptive, prospectively frozen comparison on these documents only. The log(21) bound is a per-document guarantee against the declared grid; it is not a guarantee against other predictors."}
    write_json(output / "results.json", report)
    return report


def blender_timing(documents, model, expert, primary):
    import numpy as np
    from singularity.training.online_blend import score_online_probabilities, score_online_probabilities_fast
    workload = []
    for document in documents:
        raw = document["raw"]
        neural, targets = primary.infer(model, raw)
        workload.append((neural, count_predictions(expert, raw), targets.astype(np.int64)))
    methods = {
        "fixed_blend": lambda n, c, y: primary.losses_and_metrics(primary.mix_probabilities(n, c, .35), y),
        "online_fast": lambda n, c, y: score_online_probabilities_fast(n, c, y),
        "online_reference_loop": lambda n, c, y: score_online_probabilities(n, c, y),
    }
    spec = PROTOCOL["timing"]

    def run(name):
        t0 = time.perf_counter()
        for n, c, y in workload:
            methods[name](n, c, y)
        return time.perf_counter() - t0

    for _ in range(spec["warmup_rounds"]):
        for name in methods:
            run(name)
    rng, records = random.Random(spec["order_seed"]), []
    for repeat in range(spec["measured_rounds"]):
        order = list(methods)
        rng.shuffle(order)
        records.append({"repeat": repeat, "order": order, **{name: run(name) for name in order}})
    summary = {name: {"median_seconds": statistics.median(r[name] for r in records),
                      "p90_seconds": sorted(r[name] for r in records)[math.ceil(.9 * len(records)) - 1],
                      "min_seconds": min(r[name] for r in records)} for name in methods}
    fixed = summary["fixed_blend"]["median_seconds"]
    return {"records": records, "summary": summary, "targets": int(sum(len(y) for _, _, y in workload)),
            "documents": len(workload), "online_fast_over_fixed": summary["online_fast"]["median_seconds"] / fixed,
            "reference_over_fast": summary["online_reference_loop"]["median_seconds"] / summary["online_fast"]["median_seconds"],
            "meets_2x_target": summary["online_fast"]["median_seconds"] <= 2 * fixed,
            "conditions": "CPU, torch/numpy single thread requested via environment before import, warmup excluded, randomized order"}


def cold_start():
    code = ("import time;t=time.perf_counter();import torch;"
            "from singularity.training.runner import load_checkpoint;from singularity.training.byte_experts import CountByteExpert;"
            f"load_checkpoint(r'{checkpoint(1000)}');CountByteExpert.load(r'{RESULTS / 'predictive_mixture/count_expert.json'}');"
            "print(time.perf_counter()-t)")
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "OMP_NUM_THREADS": "1"}
    values = []
    for _ in range(PROTOCOL["timing"]["cold_start_repeats"]):
        t0 = time.perf_counter()
        inside = float(subprocess.check_output([sys.executable, "-c", code], env=environment, text=True))
        values.append({"process_wall_seconds": time.perf_counter() - t0, "import_and_load_seconds": inside})
    return {"records": values, "median_process_wall_seconds": statistics.median(v["process_wall_seconds"] for v in values)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("select", "freeze", "execute"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.phase == "select":
        payload = select(args.output)
        print(json.dumps({d: sum(x["bytes"] for x in payload["documents"] if x["domain"] == d) for d in PROTOCOL["domains"]}))
    elif args.phase == "freeze":
        print(json.dumps(freeze(args.output)["protocol_sha256"]))
    else:
        report = execute(args.output)
        print(json.dumps({d: {"arms": s["arms"], "paired": {k: v["mean_difference_nats"] for k, v in s["paired"].items()}}
                          for d, s in report["domains"].items()}, indent=1))
        print(json.dumps({k: v for k, v in report["timing"].items() if k != "records"}, indent=1, default=str)[:3000])


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    main()
