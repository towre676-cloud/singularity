#!/usr/bin/env python3
"""New 19 October 2026 coordinate-basis hypothesis test, not a recovered result.

Prepare the immutable protocol and nontraining checks:
  PYTHONPATH=src python applications/training_lab/basis_study.py --output DIR
Launch its six predeclared runs only after review:
  PYTHONPATH=src python applications/training_lab/basis_study.py --output DIR --run

This module never edits the frozen training engine. Its factory interception is
process-local and temporary. The ordinary runner.load_checkpoint does not know
the basis_mlp architecture: use load_basis_checkpoint from this file instead.
"""
from contextlib import contextmanager
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import torch
from torch import nn
import torch.nn.functional as F

from singularity.training import runner
from singularity.training.data import canonical_hash, modular_addition, loss_from_logits
from singularity.training.models import ModularMLP
from singularity.training.optim import build_optimizer


def real_fourier_basis(p, dtype=torch.float32):
    """Rows: constant, cosine/sine pairs k=1,...,(p-1)/2.

    For odd p the exact trigonometric matrix is orthogonal. Construction uses
    float64 and stores float32; receipts report the resulting numerical error.
    It uses the input alphabet only, with no target or split information.
    """
    if not isinstance(p, int) or p < 3 or p % 2 != 1:
        raise ValueError("an odd input alphabet size is required")
    positions = torch.arange(p, dtype=torch.float64)
    rows = [torch.ones(p, dtype=torch.float64) / math.sqrt(p)]
    for k in range(1, (p-1)//2 + 1):
        phase = (2*math.pi*k/p)*positions
        rows.extend((math.sqrt(2/p)*phase.cos(), math.sqrt(2/p)*phase.sin()))
    return torch.stack(rows).to(dtype=dtype)


class BasisMLP(nn.Module):
    """Same trainable architecture/count as ModularMLP; fixed input coordinates."""
    def __init__(self, p, hidden=128, basis="onehot", matrix=None):
        super().__init__()
        self.p = p
        self.net = nn.Sequential(nn.Linear(2*p, hidden), nn.GELU(), nn.Linear(hidden, p))
        if matrix is None:
            matrix = torch.eye(p) if basis == "onehot" else real_fourier_basis(p)
        if tuple(matrix.shape) != (p, p):
            raise ValueError("basis matrix has wrong shape")
        self.register_buffer("input_basis", matrix.detach().clone().float())
        # Column input coordinates are Q e_a.  Rotating W by Q^T preserves the
        # same affine preactivations, hence the complete nonlinear network.
        block = torch.block_diag(self.input_basis.T, self.input_basis.T)
        with torch.no_grad():
            self.net[0].weight.copy_(self.net[0].weight @ block)

    def forward(self, input_ids):
        onehot = F.one_hot(input_ids, self.p).float()
        features = onehot @ self.input_basis.T
        return self.net(features.flatten(1))


def _factory(cfg, metadata):
    model_cfg = cfg.get("model", {})
    if not isinstance(model_cfg, dict) or model_cfg.get("name") != "basis_mlp":
        raise ValueError("basis study factory accepts only its declared basis_mlp")
    if metadata["task"] != "modular_addition":
        raise ValueError("basis study applies only to modular addition")
    basis = model_cfg.get("basis")
    if basis not in ("onehot", "fourier"):
        raise ValueError("unknown study basis")
    return BasisMLP(metadata["p"], int(model_cfg.get("hidden", 128)), basis)


@contextmanager
def basis_factory():
    """Intercept only this process; restore the original function on every exit."""
    original = runner.build_model
    runner.build_model = _factory
    try:
        yield
    finally:
        runner.build_model = original


def load_basis_checkpoint(path):
    """Load a trusted basis-study checkpoint with its registered fixed features.

    Returns (model, optimizer, state).  Saved RNG states remain available in the
    returned state; loading for prediction does not claim to resume training.
    """
    state = torch.load(path, map_location="cpu", weights_only=False)
    model = _factory(state["config"], state["data_metadata"])
    model.load_state_dict(state["model"], strict=True)
    optimizer = build_optimizer(model, state["config"])
    optimizer.load_state_dict(state["optimizer"])
    model.eval()
    return model, optimizer, state


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n")


def _source_hash():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def protocol():
    engine = Path(runner.__file__).parent
    engine_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(engine.glob("*.py"))}
    return {
        "schema": "singularity-basis-study/1", "hypothesis_date": "2026-10-19",
        "status": "new prospectively frozen hypothesis test, not historical recovery",
        "hypothesis": "AdamW coordinate dependence can change modular generalization under a complete real orthogonal Fourier input basis, despite matched initial nonlinear functions",
        "task": "modular addition p31", "p": 31, "hidden": 128,
        "split": {"split_seed": 31415, "train_orbits_per_label": 8,
                  "tune_orbits_per_label": 4, "test_orbits_per_label": 4},
        "seeds": [3000, 3001, 3002], "arms": ["onehot", "fourier"],
        "optimizer": {"name": "AdamW", "lr": .001, "weight_decay": 1.0,
                      "betas": [.9, .99], "eps": 1e-8,
                      "exclude_bias_norm_decay": True},
        "steps": 20000, "eval_every": 200, "batch_size": 128,
        "grad_clip": 1.0, "threads": 1,
        "selection": "no hyperparameter selection from TUNE or TEST; all six runs fixed in advance",
        "test_policy": "TEST scored exactly once at end of each run, never used to adapt training",
        "thresholds": {"memorization": "TRAIN accuracy >=0.99 for three consecutive scheduled evaluations",
                       "generalization": "TUNE accuracy >=0.95 for three consecutive scheduled evaluations",
                       "censoring": "uncrossed thresholds right-censored at 20000 updates",
                       "delay": "report threshold-start difference only when both are observed; positive delay is required to describe delayed generalization"},
        "basis": {"rows": "1/sqrt(p); sqrt(2/p)cos(2*pi*k*a/p), sqrt(2/p)sin(2*pi*k*a/p), k1..15",
                  "feature_orientation": "column Q*e_a for each input, two independent blocks",
                  "first_weight_transport": "W_fourier=W_onehot*blockdiag(Q.T,Q.T)",
                  "information": "complete invertible orthogonal coordinates, no labels in features",
                  "precision": "constructed float64, stored float32, numerical tolerances recorded",
                  "initial_function_max_error_limit": 1e-6},
        "controls": "separate single-update SGD Fourier equivariance, AdamW permutation equivariance, and AdamW Fourier non-equivariance; not training policies",
        "basis_source_sha256": _source_hash(), "engine_source_file_sha256": engine_hashes,
    }


def _all_pairs(p):
    return torch.tensor([(a, b) for a in range(p) for b in range(p)], dtype=torch.long)


def initial_match(seed, p=31, hidden=128):
    torch.manual_seed(seed)
    ordinary = ModularMLP(p, hidden).eval()
    torch.manual_seed(seed)
    onehot = BasisMLP(p, hidden, "onehot").eval()
    torch.manual_seed(seed)
    fourier = BasisMLP(p, hidden, "fourier").eval()
    inputs = _all_pairs(p)
    with torch.no_grad():
        reference = ordinary(inputs)
        identity_error = float((reference-onehot(inputs)).abs().max())
        rotation_error = float((reference-fourier(inputs)).abs().max())
    q = fourier.input_basis.double()
    orthogonality_error = float((q@q.T-torch.eye(p, dtype=torch.float64)).abs().max())
    column_norm_error = float((q.square().sum(0)-1).abs().max())
    parameter_counts = [sum(v.numel() for v in model.parameters()) for model in (ordinary, onehot, fourier)]
    if max(identity_error, rotation_error) > 1e-6 or len(set(parameter_counts)) != 1:
        raise AssertionError("initial nonlinear functions or trainable parameter counts do not match")
    return {"seed": seed, "pairs_checked": p*p, "ordinary_vs_basis_identity_max_error": identity_error,
            "ordinary_vs_fourier_max_error": rotation_error,
            "Q_QT_max_error_float32_storage": orthogonality_error,
            "feature_squared_norm_max_error": column_norm_error,
            "parameter_counts": parameter_counts,
            "onehot_initial_tensor_sha256": runner.model_sha256(onehot),
            "fourier_initial_tensor_sha256": runner.model_sha256(fourier),
            "interpretation": "parameter hashes differ under transport; complete initial functions agree within declared tolerance"}


def _transported_parameters(model):
    answer = {n: p.detach().clone() for n, p in model.named_parameters()}
    q = model.input_basis
    answer["net.0.weight"] = answer["net.0.weight"] @ torch.block_diag(q, q)
    return answer


def one_step_controls(p=31, hidden=128):
    """Three isolated updates on one fixed TRAIN batch; no tuning or TEST."""
    data = modular_addition(p, split_seed=31415, train_orbits_per_label=8,
                            tune_orbits_per_label=4, test_orbits_per_label=4)
    gen = torch.Generator().manual_seed(60219)
    index = torch.randperm(len(data.splits["train"]["labels"]), generator=gen)[:128]
    batch = {k: v[index] for k, v in data.splits["train"].items()}
    q = real_fourier_basis(p)
    perm = torch.randperm(p, generator=torch.Generator().manual_seed(60220))
    permutation = torch.eye(p)[perm]
    results = []
    for optimizer_name, basis_name, matrix in (("SGD", "fourier", q),
                                              ("AdamW", "permutation", permutation),
                                              ("AdamW", "fourier", q)):
        torch.manual_seed(6000)
        first = BasisMLP(p, hidden, "onehot")
        torch.manual_seed(6000)
        second = BasisMLP(p, hidden, matrix=matrix)
        config = {"optimizer": "adamw", "variant": "baseline", "lr": .001,
                  "weight_decay": 1.0, "betas": [.9, .99], "eps": 1e-8}
        opts = [build_optimizer(m, config) for m in (first, second)]
        if optimizer_name == "SGD":
            # Reuse the exact same decay mask as AdamW, with isotropic SGD.
            opts = [torch.optim.SGD(o.param_groups, lr=.001) for o in opts]
        initial = []
        losses = []
        all_pairs = _all_pairs(p)
        for model, opt in zip((first, second), opts):
            initial.append(model(all_pairs).detach())
            opt.zero_grad(set_to_none=True)
            loss = loss_from_logits(model(batch["input_ids"]), batch)
            losses.append(float(loss.detach()))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        a, b = _transported_parameters(first), _transported_parameters(second)
        squared_error = sum(float((a[n]-b[n]).double().square().sum()) for n in a)
        norm = sum(float(a[n].double().square().sum()) for n in a)
        with torch.no_grad():
            output_error = float((first(all_pairs)-second(all_pairs)).abs().max())
        results.append({"optimizer": optimizer_name, "coordinate_transform": basis_name,
                        "initial_function_max_error": float((initial[0]-initial[1]).abs().max()),
                        "train_losses_before_step": losses,
                        "parameter_error_back_in_onehot_coordinates": math.sqrt(squared_error),
                        "relative_parameter_error": math.sqrt(squared_error/max(norm, 1e-300)),
                        "post_step_function_max_error": output_error,
                        "interpretation": "numerical single-step control, not proof of an eventual accuracy difference"})
    return {"seed": 6000, "train_batch_indices_sha256": canonical_hash(index.tolist()),
            "train_batch_size": len(index), "test_evaluations": 0, "controls": results}


def config_for(frozen, arm, seed):
    return {"task": "modular_addition", "p": frozen["p"], "split": frozen["split"],
            "model": {"name": "basis_mlp", "basis": arm, "hidden": frozen["hidden"],
                      "basis_source_sha256": frozen["basis_source_sha256"]},
            "optimizer": "adamw", "variant": "baseline", "lr": .001,
            "weight_decay": 1.0, "betas": [.9, .99], "eps": 1e-8,
            "exclude_bias_norm_decay": True, "batch_size": frozen["batch_size"],
            "steps": frozen["steps"], "eval_every": frozen["eval_every"],
            "threads": frozen["threads"], "grad_clip": frozen["grad_clip"],
            "evaluate_test": True, "seed": seed,
            "study_protocol_sha256": canonical_hash(frozen),
            "telemetry": {"sketch_dimension": 16, "sketch_window": 32, "ffn_rank": False}}


def prepare(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    frozen = protocol()
    path = output / "protocol.json"
    if path.exists() and json.loads(path.read_text()) != frozen:
        raise ValueError("existing protocol differs from source/settings; use a new output directory")
    _write(path, frozen)
    _write(output / "protocol.sha256.json", {"protocol_sha256": canonical_hash(frozen)})
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    started = time.perf_counter()
    matches = [initial_match(seed, frozen["p"], frozen["hidden"]) for seed in frozen["seeds"]]
    controls = one_step_controls(frozen["p"], frozen["hidden"])
    checks = {"protocol_sha256": canonical_hash(frozen), "initial_function_matches": matches,
              "one_step_controls": controls,
              "wall_seconds_controls_and_matching": time.perf_counter()-started,
              "training_runs_launched": 0}
    _write(output / "preflight_checks.json", checks)
    return frozen, checks


def _threshold(records, split, accuracy):
    seen = [r for r in records if split in r]
    for i in range(len(seen)-2):
        if all(r[split]["accuracy"] >= accuracy for r in seen[i:i+3]):
            return {"observed": True, "threshold_start_step": seen[i]["step"],
                    "confirmed_step": seen[i+2]["step"]}
    return {"observed": False, "right_censored_at": 20000}


def run_study(output):
    frozen, checks = prepare(output)
    output = Path(output).resolve()
    progress = []
    with basis_factory():
        for seed in frozen["seeds"]:
            for arm in frozen["arms"]:
                directory = output / "runs" / ("seed_"+str(seed)) / arm
                if (directory / "summary.json").exists():
                    raise ValueError("run already exists; no implicit replacement/resume: "+str(directory))
                cfg = config_for(frozen, arm, seed)
                summary = runner.run(cfg, directory)
                records = [json.loads(line) for line in (directory/"metrics.jsonl").read_text().splitlines()]
                train = _threshold(records, "train", .99)
                tune = _threshold(records, "tune", .95)
                delay = tune["threshold_start_step"]-train["threshold_start_step"] if train["observed"] and tune["observed"] else None
                summary["basis_arm"] = arm
                summary["memorization_threshold"] = train
                summary["generalization_threshold"] = tune
                summary["threshold_start_delay_updates"] = delay
                summary["delayed_generalization_observed"] = delay is not None and delay > 0
                # Factory-specific restoration is checked without another TEST
                # evaluation. Recorded final predictions already came from run.
                restored, _, state = load_basis_checkpoint(directory/"checkpoint.pt")
                summary["checkpoint_roundtrip_model_hash_matches"] = runner.model_sha256(restored) == state["final_model_sha256"]
                progress.append(summary)
                _write(output/"progress.json", {"protocol_sha256": canonical_hash(frozen), "runs": progress})
    report = {"protocol_sha256": canonical_hash(frozen), "runs": progress,
              "matching_and_controls": checks,
              "interpretation": "paired new hypothesis test; negative or censored outcomes are retained; no automatic success claim"}
    _write(output/"results.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="applications/training_lab/results/basis_study")
    parser.add_argument("--run", action="store_true", help="launch the frozen six-run experiment")
    args = parser.parse_args(argv)
    if args.run:
        result = run_study(args.output)
        print(json.dumps({"output": str(Path(args.output).resolve()), "runs_completed": len(result["runs"])}))
    else:
        frozen, checks = prepare(args.output)
        print(json.dumps({"output": str(Path(args.output).resolve()), "protocol_sha256": canonical_hash(frozen),
                          "training_runs_launched": 0, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
