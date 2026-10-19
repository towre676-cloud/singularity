#!/usr/bin/env python3
"""Fit portable TRAIN counts, or score a frozen neural/count probability mix.

The score command accepts one already trained, trusted Singularity byte-model
checkpoint. It never trains a neural model, chooses alpha, or fits a blend
weight. Choose hyperparameters on a separate TUNE corpus before using TEST.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def fit_counts(args):
    from singularity.training.byte_experts import CountByteExpert

    started = time.perf_counter()
    train_path = Path(args.train_path).expanduser().resolve(strict=True)
    expert = CountByteExpert.fit(train_path.read_bytes(), args.order, args.alpha, args.sequence_length)
    output = Path(args.output).expanduser().resolve()
    digest = expert.save(output)
    receipt = {"schema": "singularity.byte-count-fit/1", "created_at_utc": datetime.now(timezone.utc).isoformat(),
               "fit_split": "TRAIN only; this command opens only --train-path",
               "train_path": str(train_path), "train_sha256": expert.train_sha256,
               "train_bytes": expert.train_bytes, "train_targets": expert.train_bytes - 1,
               "order": expert.order, "alpha": expert.alpha, "sequence_length": expert.sequence_length,
               "count_expert_path": str(output), "count_expert_sha256": digest,
               "hyperparameter_selection": "none; supplied order and alpha are frozen",
               "wall_seconds": time.perf_counter() - started}
    if args.receipt:
        _write(args.receipt, receipt)
    print(json.dumps(receipt, sort_keys=True))


def score(args):
    import torch
    from singularity.training import byte_experts
    from singularity.training.runner import load_checkpoint, model_sha256

    started = time.perf_counter()
    checkpoint_path = Path(args.checkpoint).expanduser().resolve(strict=True)
    expert_path = Path(args.counts).expanduser().resolve(strict=True)
    corpus_path = Path(args.corpus).expanduser().resolve(strict=True)
    checkpoint_hash = file_sha256(checkpoint_path)
    if args.expected_checkpoint_sha256 and checkpoint_hash != args.expected_checkpoint_sha256:
        raise ValueError("checkpoint hash does not match the supplied expected hash")
    expert = byte_experts.CountByteExpert.load(expert_path)
    torch.set_num_threads(args.threads)
    model, _, state = load_checkpoint(checkpoint_path)
    metadata = state["data_metadata"]
    if state.get("format") != "singularity-training/1" or metadata.get("task") != "byte_lm":
        raise ValueError("only trusted Singularity byte-language checkpoints are supported")
    if metadata["seq_len"] != expert.sequence_length:
        raise ValueError("count and neural experts must use the same causal window length")
    if metadata["corpora"]["train"]["sha256"] != expert.train_sha256:
        raise ValueError("count and neural experts must be fitted on the same TRAIN bytes")
    tensor_hash = model_sha256(model)
    if tensor_hash != state.get("final_model_sha256"):
        raise ValueError("neural tensor hash disagrees with checkpoint provenance")
    # The weight was a required argument before this corpus was opened. This
    # command has no selection branch and never updates either expert.
    result = byte_experts.score_frozen_mixture(model, expert, corpus_path.read_bytes(),
                                              args.neural_weight, args.batch_size)
    receipt = {"schema": "singularity.frozen-byte-mixture-score/1",
               "created_at_utc": datetime.now(timezone.utc).isoformat(), "split_label": args.split,
               "checkpoint_path": str(checkpoint_path), "checkpoint_sha256": checkpoint_hash,
               "neural_tensor_sha256": tensor_hash, "checkpoint_plan_sha256": state["plan_sha256"],
               "count_expert_path": str(expert_path), "count_expert_sha256": file_sha256(expert_path),
               "count_train_sha256": expert.train_sha256, "count_order": expert.order,
               "count_alpha": expert.alpha, "corpus_path": str(corpus_path), **result,
               "method": "ordinary convex blend of normalized probabilities, evaluated in log space",
               "selection": "none; alpha and neural weight were supplied frozen; no corpus-driven fitting",
               "source_sha256": {"score_byte_mixture.py": file_sha256(__file__),
                                   "byte_experts.py": file_sha256(byte_experts.__file__)},
               "environment": {"torch": torch.__version__, "threads": torch.get_num_threads(), "device": "cpu"},
               "wall_seconds": time.perf_counter() - started}
    if args.weight_receipt:
        selection = Path(args.weight_receipt).expanduser().resolve(strict=True)
        receipt["supplied_weight_receipt"] = {"path": str(selection), "sha256": file_sha256(selection),
                                               "interpretation": "linked provenance only; caller must verify it selects the supplied weight"}
    _write(args.output, receipt)
    print(json.dumps({"output": str(Path(args.output).resolve()), "neural_weight": args.neural_weight,
                      "experts": receipt["experts"]}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
             epilog="Run with PYTHONPATH=src, or install the package. fit-counts needs only Python; score needs the training extra. Checkpoints contain pickle and must come from a trusted source.")
    commands = parser.add_subparsers(dest="command", required=True)
    fit = commands.add_parser("fit-counts", help="Fit portable JSON counts using TRAIN only; no alpha selection")
    fit.add_argument("--train-path", required=True, help="Raw-byte TRAIN corpus, never TUNE or TEST")
    fit.add_argument("--order", type=int, choices=(1, 2, 3), default=3)
    fit.add_argument("--alpha", type=float, required=True, help="Positive frozen add-alpha smoothing value")
    fit.add_argument("--sequence-length", type=int, default=64)
    fit.add_argument("--output", required=True, help="Portable count-expert JSON path")
    fit.add_argument("--receipt", help="Optional separate fit-provenance JSON path")
    fit.set_defaults(function=fit_counts)
    scoring = commands.add_parser("score", help="Score one trusted checkpoint and a FROZEN supplied mixture weight")
    scoring.add_argument("--checkpoint", required=True, help="Trusted Singularity byte-model checkpoint.pt")
    scoring.add_argument("--expected-checkpoint-sha256", help="Optional expected file hash checked before loading")
    scoring.add_argument("--counts", required=True, help="TRAIN-only JSON from fit-counts, same TRAIN as checkpoint")
    scoring.add_argument("--corpus", required=True, help="Raw bytes to score; each noninitial byte is a target once")
    scoring.add_argument("--neural-weight", type=float, required=True, help="Frozen number in [0,1]; count weight is 1 minus this")
    scoring.add_argument("--weight-receipt", help="Optional existing selection receipt linked by SHA256; not used for fitting")
    scoring.add_argument("--split", choices=("tune", "test", "audit", "other"), default="audit", help="Receipt label only; never changes scoring")
    scoring.add_argument("--batch-size", type=int, default=64)
    scoring.add_argument("--threads", type=int, default=1)
    scoring.add_argument("--output", required=True, help="Metrics and hashes JSON receipt")
    scoring.set_defaults(function=score)
    args = parser.parse_args()
    if getattr(args, "threads", 1) < 1:
        parser.error("--threads must be positive")
    args.function(args)


if __name__ == "__main__":
    main()
