#!/usr/bin/env python3
"""Post-training byte count-model references on the engine's causal targets.

This is a separate reference comparison, not a newly preregistered neural arm.
All counts come from TRAIN. Each order's Dirichlet alpha is selected on TUNE;
only then is its frozen model scored once on TEST. No neural results are read.
"""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time


ALPHA_GRID = (.01, .1, 1.)
ORDERS = (1, 2, 3)
SEQUENCE_LENGTH = 64
VOCABULARY_SIZE = 256
PROTOCOL = {
    "comparison": "post-training reference count models; no neural settings selected",
    "orders": list(ORDERS),
    "alpha_grid": list(ALPHA_GRID),
    "sequence_length": SEQUENCE_LENGTH,
    "vocabulary": "all 256 raw bytes",
    "fit_split": "TRAIN only",
    "selection": "independently for each order, minimum TUNE NLL; ties choose smaller alpha",
    "test": "one scoring call per selected order, after all alpha selections are frozen",
    "smoothing": "(count(context,target)+alpha)/(count(context)+256*alpha)",
    "backoff": "shorter history only when the current causal window lacks enough preceding bytes",
    "unseen_context": "uniform Dirichlet predictive distribution; no frequency-dependent backoff",
    "accuracy_tie_break": "smallest byte value",
    "context_convention": "target raw[i+1]; available input starts at floor(i/64)*64",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def events(raw, sequence_length=SEQUENCE_LENGTH):
    """Yield at most two prior bytes and the next byte, within each window.

    Every byte except the corpus's first is a target exactly once. For a
    trigram, the first target of each window therefore uses a bigram instead.
    """
    if sequence_length < 1 or len(raw) < 2:
        raise ValueError("positive window and at least two corpus bytes required")
    for input_index in range(len(raw) - 1):
        window_start = (input_index // sequence_length) * sequence_length
        start = max(window_start, input_index - 1)
        yield raw[start:input_index + 1], raw[input_index + 1]


def fit_counts(raw, sequence_length=SEQUENCE_LENGTH):
    """Fit a shared hierarchy; evaluation uses get() and never creates counts."""
    tables = {length: defaultdict(Counter) for length in range(3)}
    count = 0
    for history, target in events(raw, sequence_length):
        count += 1
        tables[0][b""][target] += 1
        tables[1][history[-1:]][target] += 1
        if len(history) >= 2:
            tables[2][history[-2:]][target] += 1
    tables = {length: dict(table) for length, table in tables.items()}
    totals = {length: {context: sum(row.values()) for context, row in table.items()}
              for length, table in tables.items()}
    predictions = {length: {context: min(row, key=lambda byte: (-row[byte], byte))
                            for context, row in table.items()}
                   for length, table in tables.items()}
    return {"tables": tables, "totals": totals, "predictions": predictions,
            "train_targets": count, "sequence_length": sequence_length}


def probability(model, order, alpha, history, target):
    if order not in ORDERS or not math.isfinite(alpha) or alpha <= 0:
        raise ValueError("supported order and positive finite alpha required")
    length = min(order - 1, len(history))
    context = history[-length:] if length else b""
    row = model["tables"][length].get(context, {})
    total = model["totals"][length].get(context, 0)
    return (row.get(target, 0) + alpha) / (total + VOCABULARY_SIZE * alpha)


def score(model, raw, order, alpha):
    losses, correct = [], 0
    history_lengths = Counter()
    for history, target in events(raw, model["sequence_length"]):
        length = min(order - 1, len(history))
        context = history[-length:] if length else b""
        losses.append(-math.log(probability(model, order, alpha, history, target)))
        prediction = model["predictions"][length].get(context, 0)
        correct += prediction == target
        history_lengths[length] += 1
    nll = math.fsum(losses) / len(losses)
    return {"nll_nats_per_byte": nll, "bits_per_byte": nll / math.log(2),
            "accuracy": correct / len(losses), "correct": correct,
            "valid_targets": len(losses),
            "targets_by_available_history_length": dict(sorted(history_lengths.items()))}


def select_alpha(model, tune_raw, order):
    candidates = [{"alpha": alpha, "tune": score(model, tune_raw, order, alpha)}
                  for alpha in ALPHA_GRID]
    selected = min(candidates, key=lambda result: (result["tune"]["nll_nats_per_byte"], result["alpha"]))
    return {"selected_alpha": selected["alpha"], "tune": selected["tune"],
            "tune_candidates": candidates}


def model_size(model, order):
    # A trigram uses observed bigram tables for its first-position backoff;
    # a bigram and unigram need no shorter context at a scored target.
    lengths = [0] if order == 1 else ([1] if order == 2 else [1, 2])
    contexts = {length: len(model["tables"][length]) for length in lengths}
    observed = sum(contexts.values())
    return {"observed_contexts_by_history_length": contexts, "observed_contexts_total": observed,
            "nonzero_transition_counts": sum(len(row) for length in lengths
                                               for row in model["tables"][length].values()),
            "dense_probability_cells": VOCABULARY_SIZE * observed,
            "simplex_degrees_of_freedom": (VOCABULARY_SIZE - 1) * observed,
            "parameter_count_interpretation": "count-table probability cells and simplex dimensions, not neural weights",
            "selected_smoothing_hyperparameters": 1}


def build_report(corpus_dir):
    started = time.perf_counter()
    source = Path(__file__).read_bytes()
    paths = {name: (Path(corpus_dir) / (name + ".txt")).resolve(strict=True)
             for name in ("train", "tune", "test")}
    train, tune = paths["train"].read_bytes(), paths["tune"].read_bytes()
    if paths["train"] == paths["tune"] or digest(train) == digest(tune):
        raise ValueError("TRAIN and TUNE must be separate corpus contents")
    fit_started = time.perf_counter()
    model = fit_counts(train)
    fit_seconds = time.perf_counter() - fit_started
    tune_started = time.perf_counter()
    # Complete every selection before opening or scoring TEST.
    selected = {order: select_alpha(model, tune, order) for order in ORDERS}
    tune_seconds = time.perf_counter() - tune_started
    test = paths["test"].read_bytes()
    if len(set(paths.values())) != 3 or len({digest(train), digest(tune), digest(test)}) != 3:
        raise ValueError("the three corpus paths and contents must be distinct")
    test_started = time.perf_counter()
    references = []
    for order in ORDERS:
        choice = selected[order]
        references.append({"order": order, "name": ("unigram", "bigram", "trigram")[order - 1],
                           **choice, "size": model_size(model, order),
                           "test": score(model, test, order, choice["selected_alpha"]),
                           "test_scoring_calls": 1})
    test_seconds = time.perf_counter() - test_started
    raw = {"train": train, "tune": tune, "test": test}
    return {"schema": "singularity.byte-reference-baselines/1", "protocol": PROTOCOL,
            "source_sha256": digest(source),
            "protocol_sha256": digest(json.dumps(PROTOCOL, sort_keys=True).encode()),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "corpora": {name: {"path": str(paths[name]), "bytes": len(content),
                                "sha256": digest(content), "valid_targets": len(content) - 1}
                        for name, content in raw.items()},
            "uniform_256_reference": {"nll_nats_per_byte": math.log(256), "bits_per_byte": 8.,
                                      "accuracy": test[1:].count(0) / (len(test) - 1),
                                      "deterministic_prediction": 0,
                                      "accuracy_if_uniform_random_sampling": 1 / 256},
            "fit_train_targets": model["train_targets"], "references": references,
            "timing_seconds": {"shared_train_count_fit": fit_seconds,
                               "all_tune_selection": tune_seconds, "selected_test_scoring": test_seconds,
                               "total_including_input_and_hashing": time.perf_counter() - started},
            "limitations": "Small fixed raw-byte prefixes; short-memory count references, not full-corpus language models. Alpha selection uses TUNE. No neural TEST metric was read to choose these references."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = build_report(args.corpus_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    for result in report["references"]:
        test = result["test"]
        print(f"{result['name']}: alpha={result['selected_alpha']:g}, "
              f"TEST NLL={test['nll_nats_per_byte']:.6f}, BPC={test['bits_per_byte']:.6f}, "
              f"accuracy={test['accuracy']:.6f}, targets={test['valid_targets']}")
    print("Saved", output)


if __name__ == "__main__":
    main()
