#!/usr/bin/env python3
"""Analyze the frozen training revision without loading models or evaluating TEST.

Run from the repository root::

    python scripts/analyze_training_revision.py

The JSON analysis uses only the standard library. Figure generation requires
Matplotlib; use --no-figure to omit it. --allow-partial is for development and
never creates the publication figure. No confidence interval is estimated from
three seeds. Cross-entropy effects are variant minus its same-seed baseline.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any
from xml.sax.saxutils import escape
from itertools import product


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = ROOT / "applications/training_lab/results"
ARM_LABELS = {"baseline": "Fixed AdamW", "cosine": "Cosine", "layer_decay": "Layer decay", "meta": "Meta"}
TASK_LABELS = {"modular_mlp": "Modular addition · MLP", "modular_transformer": "Modular addition · transformer", "wikitext_byte": "WikiText-2 · byte transformer"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def describe(values: list[float]) -> dict[str, Any]:
    """Retain every observation, its arithmetic mean, and observed range."""
    return {"values": values, "n": len(values), "mean": statistics.mean(values) if values else None,
            "min": min(values) if values else None, "max": max(values) if values else None,
            "uncertainty": "Observed seed range only; no confidence interval or significance claim."}


def metric_records(directory: Path) -> tuple[list[dict], str, str]:
    """Hash the original JSONL bytes, also when stored as metrics.jsonl.gz."""
    path = directory / "metrics.jsonl"
    if path.exists():
        raw = path.read_bytes()
    else:
        path = directory / "metrics.jsonl.gz"
        raw = gzip.decompress(path.read_bytes())
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    return rows, hashlib.sha256(raw).hexdigest(), path.name


def audit_data(directory: Path, summary: dict, check, identifier: str) -> dict[str, Any]:
    """Recompute split metadata hashes; hash original corpus bytes if available."""
    data = load_json(directory / "data.json")
    payload = data["orbits"] if "orbits" in data else data["corpora"]
    observed = canonical_hash(payload)
    check("data_split_binding:" + identifier, observed == data.get("split_sha256") == summary.get("split_sha256"))
    check("data_population_binding:" + identifier, data.get("counts") == summary.get("counts"))
    corpora = {}
    if "corpora" in data:
        for split, metadata in data["corpora"].items():
            targets = metadata["bytes"] - 1
            expected = {"examples": (targets + data["seq_len"] - 1) // data["seq_len"], "valid_targets": targets}
            check(f"byte_target_population:{identifier}/{split}", data["counts"][split] == expected)
            path = Path(metadata["path"])
            if path.exists():
                passed = file_hash(path) == metadata["sha256"] and path.stat().st_size == metadata["bytes"]
                check(f"corpus_content_hash:{identifier}/{split}", passed)
                corpora[split] = "original_file_hash_verified" if passed else "original_file_hash_mismatch"
            else:
                corpora[split] = "original_path_unavailable; metadata_binding_only"
    else:
        listed = [tuple(orbit) for block in data["orbits"].values() for orbit in block]
        p = data["p"]
        check("modular_orbit_partition:" + identifier, len(listed) == len(set(listed)) == p * (p + 1) // 2 and
              all(0 <= a <= b < p and (a + b) % p == label for a, b, label in listed))
        for split, block in data["orbits"].items():
            examples = sum(1 if a == b else 2 for a, b, _ in block)
            expected = {"examples": examples, "valid_targets": examples, "orbits": len(block)}
            check(f"modular_target_population:{identifier}/{split}", data["counts"][split] == expected)
    return {"split_metadata_sha256": observed, "corpus_file_checks": corpora}


def first_threshold(evaluations: list[dict], split: str, threshold: float, cap: int,
                    required: int = 3) -> dict[str, Any]:
    """First full scheduled streak; onset is separate from confirmation time."""
    streak: list[int] = []
    for row in evaluations:
        if row[split]["accuracy"] >= threshold:
            streak.append(row["step"])
            if len(streak) == required:
                return {"threshold": threshold, "consecutive_evaluations": required,
                        "onset_step": streak[0], "confirmed_at_step": streak[-1],
                        "supporting_steps": streak.copy(), "right_censored": False,
                        "censoring_step": None}
        else:
            streak = []
    return {"threshold": threshold, "consecutive_evaluations": required,
            "onset_step": None, "confirmed_at_step": None, "supporting_steps": [],
            "right_censored": True, "censoring_step": cap}


def grokking(evaluations: list[dict], cap: int) -> dict[str, Any]:
    memory = first_threshold(evaluations, "train", .99, cap)
    generalization = first_threshold(evaluations, "tune", .95, cap)
    observed = not memory["right_censored"] and not generalization["right_censored"]
    delay = generalization["onset_step"] - memory["onset_step"] if observed else None
    return {"memorization": memory, "generalization": generalization,
            "onset_delay_updates": delay,
            "confirmation_delay_updates": generalization["confirmed_at_step"] - memory["confirmed_at_step"] if observed else None,
            "delayed_generalization_observed": observed and delay > 0,
            "interpretation": ("Both thresholds observed with positive delay." if observed and delay > 0 else
                               "Both thresholds observed; no positive delayed-generalization gap." if observed else
                               "Generalization threshold not observed within the declared cap." if generalization["right_censored"] else
                               "Memorization threshold not observed within the declared cap."),
            "scope": "First observed scheduled TRAIN/TUNE streak, not an interpolated crossing time; no TEST time series. Censoring does not imply never generalizing."}


def grokking_counts(rows: list[dict]) -> dict[str, int]:
    return {"runs": len(rows),
            "memorization_confirmed": sum(not r["grokking"]["memorization"]["right_censored"] for r in rows),
            "generalization_confirmed": sum(not r["grokking"]["generalization"]["right_censored"] for r in rows),
            "delayed_generalization_observed": sum(r["grokking"]["delayed_generalization_observed"] for r in rows)}


def analyze_followup(directory: Path) -> dict[str, Any] | None:
    """Keep the newly declared retuning experiment separate from the first one."""
    if not (directory / "protocol.json").exists():
        return None
    protocol = load_json(directory / "protocol.json")
    ph = canonical_hash(protocol)
    result = {"status": "pending_confirmation", "protocol_sha256": ph,
              "scope": protocol["scope"], "motivation": protocol["motivation"],
              "uniform_prediction_reference": {"cross_entropy_nats": math.log(protocol["p"]),
                                                "expected_random_accuracy": 1 / protocol["p"],
                                                "scope": "Analytic uniform-probability reference, not an additional trained run."},
              "relationship_to_original": "Separate follow-up with new discovery/confirmation seeds and a new split; original results are unchanged."}
    if not (directory / "confirmation.json").exists():
        return result
    confirmation = load_json(directory / "confirmation.json")
    plan = load_json(directory / "confirmation_plan.json")
    selection = load_json(directory / "selection.json")
    checks = []

    def check(name, passed):
        checks.append({"check": name, "passed": bool(passed)})

    check("frozen_protocol", confirmation.get("protocol_sha256") == ph == plan.get("protocol_sha256") == selection.get("protocol_sha256"))
    check("discovery_zero_test_evaluations", selection.get("test_evaluations") == 0 and all(
        x["summary"].get("test_evaluations") == 0 and x["summary"].get("final_test") is None for x in selection["all_candidates"]))
    check("all_declared_discovery_candidates", len(selection["all_candidates"]) == len(protocol["discovery_grid"]))
    check("exact_declared_discovery_identifiers", {x["candidate"] for x in selection["all_candidates"]} == set(range(len(protocol["discovery_grid"]))))
    for candidate in selection["all_candidates"]:
        run_directory = directory / "discovery" / f"candidate_{candidate['candidate']}"
        summary = candidate["summary"]
        records, digest, _ = metric_records(run_directory)
        config = load_json(run_directory / "config.json")
        identifier = f"candidate_{candidate['candidate']}"
        hp = protocol["discovery_grid"][candidate["candidate"]]
        check("discovery_grid_hyperparameters:" + identifier, candidate["hyperparameters"] == hp and all(config.get(k) == value for k, value in hp.items()))
        check("discovery_declared_budget_seed:" + identifier, config.get("steps") == protocol["discovery_steps"] and config.get("seed") == protocol["discovery_seed"])
        check("discovery_full_update_log:" + identifier, [r.get("step") for r in records] == list(range(1, config["steps"] + 1)))
        check("discovery_metrics_hash:" + identifier, digest == summary.get("metrics_sha256"))
        check("discovery_checkpoint_hash:" + identifier, file_hash(run_directory / "checkpoint.pt") == summary.get("checkpoint_sha256"))
        check("discovery_configuration_hash:" + identifier, canonical_hash(config) == summary.get("plan_sha256"))
        audit_data(run_directory, summary, check, "discovery/" + identifier)
    chosen = min(selection["all_candidates"], key=lambda x: (x["tune_loss"], x["candidate"]))
    check("tune_only_selection_rule", chosen == selection["selected"])
    planned = {(p["arm"], p["seed"]): p for p in plan["plans"]}
    actual = {(r["arm"], r["seed"]): r for r in confirmation["runs"]}
    check("declared_confirmation_plan_matrix", set(planned) == set(product(protocol["confirmation_arms"], protocol["confirmation_seeds"])) and len(planned) == len(plan["plans"]))
    check("complete_confirmation_matrix", set(actual) == set(planned) and len(actual) == len(confirmation["runs"]))
    rows = []
    for key, summary in sorted(actual.items()):
        arm, seed = key
        cfg = planned[key]["config"]
        records, digest, filename = metric_records(directory / "confirmation" / arm / f"seed_{seed}")
        cap = cfg["steps"]
        evaluations = [r for r in records if "train" in r and "tune" in r]
        expected = list(range(cfg["eval_every"], cap + 1, cfg["eval_every"]))
        if not expected or expected[-1] != cap:
            expected.append(cap)
        ident = f"{arm}/seed_{seed}"
        check("declared_task_configuration:" + ident,
              cfg.get("steps") == protocol["confirmation_steps"] and cfg.get("seed") == seed and
              cfg.get("task") == protocol["task"] and cfg.get("p") == protocol["p"] and
              cfg.get("model") == protocol["model"] and cfg.get("split", {}).get("split_seed") == protocol["split_seed"] and
              [cfg.get("split", {}).get(s + "_orbits_per_label") for s in ("train", "tune", "test")] == protocol["orbits_per_label"] and
              cfg.get("evaluate_test") is True and cfg.get("protocol_sha256") == ph and
              cfg.get("variant") == ("meta" if arm == "retuned_meta" else "baseline"))
        check("full_update_log:" + ident, [r.get("step") for r in records] == list(range(1, cap + 1)))
        check("scheduled_evaluations:" + ident, [r["step"] for r in evaluations] == expected)
        check("metrics_hash:" + ident, digest == summary.get("metrics_sha256"))
        check("checkpoint_hash:" + ident, file_hash(directory / "confirmation" / arm / f"seed_{seed}" / "checkpoint.pt") == summary.get("checkpoint_sha256"))
        check("configuration_hash:" + ident, canonical_hash(cfg) == summary.get("plan_sha256"))
        check("saved_configuration_matches_plan:" + ident,
              load_json(directory / "confirmation" / arm / f"seed_{seed}" / "config.json") == cfg)
        expected_hp = {"lr": .001, "weight_decay": .1, "betas": [.9, .999]} if arm == "original_fixed" else selection["selected"]["hyperparameters"]
        check("selected_start_hyperparameters:" + ident, all(cfg.get(k) == value for k, value in expected_hp.items()))
        check("equal_declared_update_budget:" + ident, summary.get("optimizer_updates") == cap)
        check("one_final_test_evaluation:" + ident, summary.get("test_evaluations") == 1 and isinstance(summary.get("final_test"), dict))
        check("no_test_metrics_in_feedback_log:" + ident, not any("test" in r or "final_test" in r for r in records))
        data_audit = audit_data(directory / "confirmation" / arm / f"seed_{seed}", summary, check, ident)
        rows.append({"arm": arm, "seed": seed, "optimizer_updates": cap,
                     "test_cross_entropy_nats": summary["final_test"]["loss"], "test_accuracy": summary["final_test"]["accuracy"],
                     "train_accuracy": summary["final_train"]["accuracy"], "tune_accuracy": summary["final_tune"]["accuracy"],
                     "wall_seconds_including_monitoring": summary["wall_seconds_including_monitoring"],
                     "meta_calls": summary["meta_calls"], "initial_model_sha256": summary.get("initial_model_sha256"),
                     "split_sha256": summary.get("split_sha256"), "sampler_seed": summary.get("sampler_seed"),
                     "metrics_file": filename, "data_audit": data_audit, "grokking": grokking(evaluations, cap),
                     "evaluation_curve": [{"step": r["step"], "train_loss": r["train"]["loss"], "tune_loss": r["tune"]["loss"],
                                           "train_accuracy": r["train"]["accuracy"], "tune_accuracy": r["tune"]["accuracy"]} for r in evaluations]})
    for seed in protocol["confirmation_seeds"]:
        paired = [r for r in rows if r["seed"] == seed]
        for field in ("initial_model_sha256", "split_sha256", "sampler_seed", "optimizer_updates"):
            values = [r[field] for r in paired]
            check(f"paired_{field}:seed_{seed}", len(paired) == len(protocol["confirmation_arms"]) and all(x is not None for x in values) and len(set(values)) == 1)
    comparisons = {}
    for variant, baseline in (("retuned_fixed", "original_fixed"), ("retuned_meta", "retuned_fixed"), ("retuned_meta", "original_fixed")):
        paired = []
        for seed in protocol["confirmation_seeds"]:
            left = next(r for r in rows if r["arm"] == variant and r["seed"] == seed)
            right = next(r for r in rows if r["arm"] == baseline and r["seed"] == seed)
            paired.append({"seed": seed, "test_cross_entropy_delta_nats": left["test_cross_entropy_nats"] - right["test_cross_entropy_nats"],
                           "test_accuracy_delta_percentage_points": 100 * (left["test_accuracy"] - right["test_accuracy"]),
                           "wall_seconds_delta": left["wall_seconds_including_monitoring"] - right["wall_seconds_including_monitoring"],
                           "wall_time_ratio": left["wall_seconds_including_monitoring"] / right["wall_seconds_including_monitoring"]})
        comparisons[f"{variant}_minus_{baseline}"] = {"raw_effects": paired,
            "summaries": {metric: describe([p[metric] for p in paired]) for metric in list(paired[0])[1:]}}
    failed = [c["check"] for c in checks if not c["passed"]]
    result.update({"status": "complete", "audit": {"passed": not failed, "failed_checks": failed, "checks": checks},
                   "selected_hyperparameters": selection["selected"]["hyperparameters"], "runs": rows, "comparisons": comparisons,
                   "arms": {arm: {"metrics": {metric: describe([r[metric] for r in rows if r["arm"] == arm]) for metric in
                                               ("test_cross_entropy_nats", "test_accuracy", "wall_seconds_including_monitoring")},
                                  "grokking_counts": grokking_counts([r for r in rows if r["arm"] == arm])}
                            for arm in protocol["confirmation_arms"]},
                   "discovery_seconds_sum": sum(x["summary"]["wall_seconds_including_monitoring"] for x in selection["all_candidates"]),
                   "discovery_runs": len(selection["all_candidates"]),
                   "discovery_optimizer_updates": sum(x["summary"]["optimizer_updates"] for x in selection["all_candidates"]),
                   "confirmation_seconds_sum": sum(r["wall_seconds_including_monitoring"] for r in rows),
                   "confirmation_meta_calls": sum(r["meta_calls"] for r in rows),
                   "confirmation_orchestrator_seconds": confirmation.get("wall_seconds"),
                   "reporting": "Raw paired three-seed effects, arithmetic means and observed ranges; no confidence intervals."})
    return result


def analyze_basis_study(directory: Path) -> dict[str, Any] | None:
    """Separate matched-function coordinate experiment, without assuming equal tensors."""
    if not (directory / "results.json").exists():
        return None
    protocol, source = load_json(directory / "protocol.json"), load_json(directory / "results.json")
    preflight = load_json(directory / "preflight_checks.json")
    ph = canonical_hash(protocol)
    checks = []

    def check(name, passed):
        checks.append({"check": name, "passed": bool(passed)})

    check("frozen_protocol", source.get("protocol_sha256") == ph == preflight.get("protocol_sha256"))
    check("preflight_precedes_training", preflight.get("training_runs_launched") == 0)
    check("controls_do_not_evaluate_test", preflight["one_step_controls"].get("test_evaluations") == 0)
    actual = {(r["basis_arm"], r["seed"]): r for r in source["runs"]}
    check("declared_run_matrix", set(actual) == set(product(protocol["arms"], protocol["seeds"])) and len(actual) == len(source["runs"]))
    matching = {m["seed"]: m for m in preflight["initial_function_matches"]}
    rows = []
    for (arm, seed), summary in sorted(actual.items()):
        run_directory = directory / "runs" / f"seed_{seed}" / arm
        cfg = load_json(run_directory / "config.json")
        records, digest, filename = metric_records(run_directory)
        evaluations = [r for r in records if "train" in r and "tune" in r]
        ident = f"{arm}/seed_{seed}"
        check("configuration_binding:" + ident, canonical_hash(cfg) == summary["plan_sha256"] and cfg.get("study_protocol_sha256") == ph)
        check("declared_run_configuration:" + ident, cfg.get("seed") == seed and cfg.get("steps") == protocol["steps"] and
              cfg.get("model", {}).get("basis") == arm and cfg.get("split") == protocol["split"] and
              all(cfg.get(k) == protocol["optimizer"][k] for k in ("lr", "weight_decay", "betas", "eps")))
        check("full_update_log:" + ident, [r.get("step") for r in records] == list(range(1, protocol["steps"] + 1)))
        check("declared_update_count:" + ident, summary.get("optimizer_updates") == protocol["steps"])
        check("scheduled_evaluations:" + ident, [r["step"] for r in evaluations] == list(range(protocol["eval_every"], protocol["steps"] + 1, protocol["eval_every"])))
        check("metrics_hash:" + ident, digest == summary["metrics_sha256"])
        check("checkpoint_hash:" + ident, file_hash(run_directory / "checkpoint.pt") == summary["checkpoint_sha256"])
        check("one_final_test_evaluation:" + ident, summary.get("test_evaluations") == 1)
        check("no_test_metrics_in_feedback_log:" + ident, not any("test" in r or "final_test" in r for r in records))
        match = matching[seed]
        check("matched_initial_function:" + ident, match["pairs_checked"] == protocol["p"] ** 2 and
              match["ordinary_vs_fourier_max_error"] <= protocol["basis"]["initial_function_max_error_limit"] and
              summary["initial_model_sha256"] == match[arm + "_initial_tensor_sha256"])
        data_audit = audit_data(run_directory, summary, check, ident)
        rows.append({"arm": arm, "seed": seed, "optimizer_updates": summary["optimizer_updates"],
                     "test_cross_entropy_nats": summary["final_test"]["loss"], "test_accuracy": summary["final_test"]["accuracy"],
                     "train_accuracy": summary["final_train"]["accuracy"], "tune_accuracy": summary["final_tune"]["accuracy"],
                     "wall_seconds_including_monitoring": summary["wall_seconds_including_monitoring"],
                     "sampler_seed": summary["sampler_seed"], "split_sha256": summary["split_sha256"],
                     "parameter_count": summary["parameter_count"], "data_audit": data_audit, "metrics_file": filename,
                     "grokking": grokking(evaluations, protocol["steps"])})
    for seed in protocol["seeds"]:
        paired = [r for r in rows if r["seed"] == seed]
        for field in ("sampler_seed", "split_sha256", "parameter_count", "optimizer_updates"):
            check(f"paired_{field}:seed_{seed}", len(paired) == 2 and len({r[field] for r in paired}) == 1)
    pairs = []
    for seed in protocol["seeds"]:
        onehot = next(r for r in rows if r["seed"] == seed and r["arm"] == "onehot")
        fourier = next(r for r in rows if r["seed"] == seed and r["arm"] == "fourier")
        pairs.append({"seed": seed, "test_cross_entropy_delta_nats": fourier["test_cross_entropy_nats"] - onehot["test_cross_entropy_nats"],
                      "test_accuracy_delta_percentage_points": 100 * (fourier["test_accuracy"] - onehot["test_accuracy"]),
                      "wall_seconds_delta": fourier["wall_seconds_including_monitoring"] - onehot["wall_seconds_including_monitoring"],
                      "wall_time_ratio": fourier["wall_seconds_including_monitoring"] / onehot["wall_seconds_including_monitoring"]})
    failed = [c["check"] for c in checks if not c["passed"]]
    return {"status": "complete", "protocol_sha256": ph, "audit": {"passed": not failed, "failed_checks": failed, "checks": checks},
            "scope": protocol["status"], "hypothesis": protocol["hypothesis"], "matching_and_controls": preflight,
            "initialization_semantics": "Initial functions match within the declared tolerance after weight transport; parameter hashes intentionally differ.",
            "runs": rows, "paired_effect_direction": "fourier minus same-seed onehot",
            "paired_effects": pairs, "paired_summaries": {key: describe([p[key] for p in pairs]) for key in list(pairs[0])[1:]},
            "arms": {arm: {"metrics": {metric: describe([r[metric] for r in rows if r["arm"] == arm]) for metric in
                                       ("test_cross_entropy_nats", "test_accuracy", "wall_seconds_including_monitoring")},
                           "grokking_counts": grokking_counts([r for r in rows if r["arm"] == arm])} for arm in protocol["arms"]},
            "uniform_prediction_reference_nats": math.log(protocol["p"]),
            "confirmation_seconds_sum": sum(r["wall_seconds_including_monitoring"] for r in rows),
            "preflight_seconds": preflight["wall_seconds_controls_and_matching"],
            "interpretation": "New coordinate experiment, separate from optimizer selection. Loss changes do not establish generalization or grokking; compare the uniform-probability reference."}


def integrity_replays(results: Path, check) -> dict[str, Any] | None:
    """Preserve verification repeats and restore first-pass timing accounting."""
    path = results / "integrity_replays.json"
    if not path.exists():
        return None
    manifest = load_json(path)
    adjustments = {"discovery": 0.0, "confirmation": 0.0}
    for entry in manifest.get("entries", []):
        identifier = entry["relative_path"]
        for field in ("model_equal", "optimizer_equal", "tune_equal", "test_equal"):
            check(f"integrity_replay_{field}:{identifier}", entry.get(field) is True)
        original_path = results / entry["archive_dir"] / "summary.json"
        canonical_path = results / identifier / "summary.json"
        if original_path.exists() and canonical_path.exists():
            original, canonical = load_json(original_path), load_json(canonical_path)
            phase = identifier.split("/", 1)[0]
            if phase in adjustments:
                adjustments[phase] += original["wall_seconds_including_monitoring"] - canonical["wall_seconds_including_monitoring"]
    return {"manifest_sha256": file_hash(path), "manifest": manifest,
            "canonical_to_first_pass_wall_adjustment": adjustments,
            "additional_wall_seconds": manifest["additional_wall_seconds_total"],
            "additional_optimizer_updates": manifest["extra_optimizer_updates"],
            "additional_test_evaluations": manifest["extra_test_evaluations"],
            "independent_confirmation_runs_added": 0,
            "interpretation": "Integrity verification repeats, including failed attempts, cost additional work and are not new independent seeds. Repeated TEST evaluations are explicitly disclosed."}


def analyze(results: Path = DEFAULT_RESULTS, *, require_complete: bool = True) -> dict[str, Any]:
    """Return source-bound descriptive results and protocol checks; no model use."""
    results = Path(results)
    protocol = load_json(results / "protocol.json")
    selection = load_json(results / "selection.json")
    plan = load_json(results / "confirmation_plan.json")
    final_path = results / "confirmation.json"
    if require_complete and not final_path.exists():
        raise ValueError("confirmation.json is not present; the planned confirmation experiment is still incomplete")
    source = final_path if final_path.exists() else results / "confirmation_progress.json"
    confirmation = load_json(source)
    runs = confirmation["runs"]
    tasks, arms, seeds = list(protocol["tasks"]), protocol["confirmation_arms"], protocol["confirmation_seeds"]
    planned = {(p["task_name"], p["arm"], p["seed"]): p for p in plan["plans"]}
    actual = {(r["task_name"], r["arm"], r["seed"]): r for r in runs}
    complete = set(actual) == set(planned) and len(actual) == len(runs)
    errors: list[str] = []
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, **details: Any) -> None:
        checks.append({"check": name, "passed": bool(passed), **details})
        if not passed:
            errors.append(name)

    check("unique_run_identifiers", len(actual) == len(runs))
    expected_matrix = set(product(tasks, arms, seeds))
    check("declared_confirmation_plan_matrix", set(planned) == expected_matrix and len(planned) == len(plan["plans"]))
    check("no_unplanned_confirmation_runs", set(actual) <= set(planned))
    if require_complete:
        check("complete_confirmation_matrix", complete, expected=len(planned), actual=len(actual))
    ph = canonical_hash(protocol)
    check("plan_binds_frozen_protocol", plan.get("protocol_sha256") == ph)
    check("selection_binds_frozen_protocol", selection.get("protocol_sha256") == ph)
    check("plan_binds_frozen_selection", plan.get("selection_sha256") == canonical_hash(selection))
    check("selection_does_not_use_test", selection.get("test_evaluations") == 0 and plan.get("test_metrics_used_for_selection") is False)
    if final_path.exists():
        check("confirmation_binds_frozen_protocol", confirmation.get("protocol_sha256") == ph)
        check("confirmation_binds_frozen_plan", confirmation.get("confirmation_plan_sha256") == canonical_hash(plan))

    discovery_rows = []
    for path in sorted((results / "discovery").glob("*/*/summary.json")):
        summary = load_json(path)
        identifier = "/".join(path.parts[-3:-1])
        passed = summary.get("test_evaluations") == 0 and summary.get("final_test") is None
        check("discovery_zero_test_evaluations:" + identifier, passed)
        config = load_json(path.parent / "config.json")
        records, digest, _ = metric_records(path.parent)
        check("discovery_full_update_log:" + identifier, [r.get("step") for r in records] == list(range(1, config["steps"] + 1)))
        check("discovery_metrics_hash:" + identifier, digest == summary.get("metrics_sha256"))
        check("discovery_checkpoint_hash:" + identifier, file_hash(path.parent / "checkpoint.pt") == summary.get("checkpoint_sha256"))
        check("discovery_configuration_hash:" + identifier, canonical_hash(config) == summary.get("plan_sha256"))
        check("discovery_no_test_metrics_in_log:" + identifier, not any("test" in r or "final_test" in r for r in records))
        audit_data(path.parent, summary, check, "discovery/" + identifier)
        discovery_rows.append({"run": identifier, "test_evaluations": summary.get("test_evaluations"),
                               "wall_seconds": summary["wall_seconds_including_monitoring"],
                               "optimizer_updates": summary["optimizer_updates"],
                               "final_tune_loss": summary["final_tune"]["loss"]})
    check("all_discovery_candidates_accounted", len(discovery_rows) == len(tasks) * len(protocol["fixed_discovery_grid"]),
          observed=len(discovery_rows))
    expected_discovery = {f"{task}/candidate_{index}" for task in tasks for index in range(len(protocol["fixed_discovery_grid"]))}
    check("exact_declared_discovery_matrix", {row["run"] for row in discovery_rows} == expected_discovery)
    for task in tasks:
        candidates = []
        for index, hp in enumerate(protocol["fixed_discovery_grid"]):
            directory = results / "discovery" / task / f"candidate_{index}"
            summary, config = load_json(directory / "summary.json"), load_json(directory / "config.json")
            check(f"discovery_grid_hyperparameters:{task}/candidate_{index}", all(config.get(k) == value for k, value in hp.items()))
            candidates.append((summary["final_tune"]["loss"], index, hp))
        loss, selected_index, hyperparameters = min(candidates, key=lambda x: (x[0], x[1]))
        selected = selection["selections"][task]["selected"]
        check("tune_only_selection_rule:" + task, selected.get("candidate") == selected_index and
              selected.get("hyperparameters") == hyperparameters and selected.get("final_tune_loss") == loss)

    rows = []
    for key in sorted(actual):
        task, arm, seed = key
        summary = actual[key]
        cfg = planned[key]["config"]
        directory = results / "confirmation" / task / arm / f"seed_{seed}"
        metrics, metrics_hash, metric_file = metric_records(directory)
        cap, interval = cfg["steps"], cfg["eval_every"]
        specification = protocol["tasks"][task]
        evaluations = [r for r in metrics if "train" in r and "tune" in r]
        expected_evals = list(range(interval, cap + 1, interval))
        if not expected_evals or expected_evals[-1] != cap:
            expected_evals.append(cap)
        ident = f"{task}/{arm}/seed_{seed}"
        expected_fields = {k: v for k, v in specification.items() if k not in ("discovery_steps", "confirmation_steps")}
        expected_fields.update({"steps": specification["confirmation_steps"], "seed": seed, "variant": arm,
                                "evaluate_test": True, "phase": "confirmation", "protocol_sha256": ph})
        check("declared_task_configuration:" + ident, all(cfg.get(k) == value for k, value in expected_fields.items()))
        check("full_update_log:" + ident, [r.get("step") for r in metrics] == list(range(1, cap + 1)))
        check("scheduled_evaluations:" + ident, [r["step"] for r in evaluations] == expected_evals)
        check("metrics_hash:" + ident, metrics_hash == summary.get("metrics_sha256"))
        check("checkpoint_hash:" + ident, file_hash(directory / "checkpoint.pt") == summary.get("checkpoint_sha256"))
        check("configuration_hash:" + ident, canonical_hash(cfg) == summary.get("plan_sha256"))
        check("saved_configuration_matches_plan:" + ident, load_json(directory / "config.json") == cfg)
        selected_hp = selection["selections"][task]["selected"]["hyperparameters"]
        check("selected_start_hyperparameters:" + ident, all(cfg.get(k) == value for k, value in selected_hp.items()))
        check("equal_declared_update_budget:" + ident, summary.get("optimizer_updates") == cap)
        check("one_final_test_evaluation:" + ident, summary.get("test_evaluations") == 1 and isinstance(summary.get("final_test"), dict))
        check("no_test_metrics_in_feedback_log:" + ident, not any("test" in r or "final_test" in r for r in metrics))
        data_audit = audit_data(directory, summary, check, ident)
        test = summary["final_test"]
        meta_rows = [r["meta"] for r in metrics if "meta" in r]
        row = {"task": task, "arm": arm, "seed": seed, "optimizer_updates": cap,
               "test_cross_entropy_nats": test["loss"], "test_accuracy": test["accuracy"],
               "train_accuracy": summary["final_train"]["accuracy"], "tune_accuracy": summary["final_tune"]["accuracy"],
               "wall_seconds_including_monitoring": summary["wall_seconds_including_monitoring"],
               "parameter_count": summary["parameter_count"], "test_valid_targets": test["valid_targets"],
               "meta_calls": summary["meta_calls"], "accepted_meta_proposals": sum(bool(r.get("accepted")) for r in meta_rows),
               "initial_model_sha256": summary.get("initial_model_sha256"), "split_sha256": summary.get("split_sha256"),
               "sampler_seed": summary.get("sampler_seed"), "metrics_file": metric_file, "data_audit": data_audit,
               "evaluation_curve": [{"step": r["step"], "train_loss": r["train"]["loss"],
                                      "tune_loss": r["tune"]["loss"], "train_accuracy": r["train"]["accuracy"],
                                      "tune_accuracy": r["tune"]["accuracy"]} for r in evaluations]}
        if protocol["tasks"][task]["task"] == "byte_lm":
            row["test_bits_per_byte"] = test["loss"] / math.log(2)
            row["test_byte_perplexity"] = math.exp(test["loss"])
        else:
            row["grokking"] = grokking(evaluations, cap)
        rows.append(row)

    for task in tasks:
        for seed in seeds:
            paired = [r for r in rows if r["task"] == task and r["seed"] == seed]
            if len(paired) != len(arms):
                continue
            for field in ("initial_model_sha256", "split_sha256", "sampler_seed", "parameter_count", "optimizer_updates"):
                values = [r[field] for r in paired]
                check(f"paired_{field}:{task}/seed_{seed}", all(x is not None for x in values) and len(set(values)) == 1,
                      value=values[0])

    task_results = {}
    for task in tasks:
        per_arm = {}
        is_byte = protocol["tasks"][task]["task"] == "byte_lm"
        for arm in arms:
            group = sorted((r for r in rows if r["task"] == task and r["arm"] == arm), key=lambda r: r["seed"])
            pairs = []
            for row in group:
                baseline = next((r for r in rows if r["task"] == task and r["arm"] == "baseline" and r["seed"] == row["seed"]), None)
                if baseline is not None:
                    pair = {"seed": row["seed"],
                            "test_cross_entropy_delta_nats": row["test_cross_entropy_nats"] - baseline["test_cross_entropy_nats"],
                            "test_accuracy_delta_percentage_points": 100 * (row["test_accuracy"] - baseline["test_accuracy"]),
                            "wall_seconds_delta": row["wall_seconds_including_monitoring"] - baseline["wall_seconds_including_monitoring"],
                            "wall_time_ratio": row["wall_seconds_including_monitoring"] / baseline["wall_seconds_including_monitoring"]}
                    if is_byte:
                        pair["test_bits_per_byte_delta"] = pair["test_cross_entropy_delta_nats"] / math.log(2)
                    pairs.append(pair)
            metrics = ["test_cross_entropy_nats", "test_accuracy", "wall_seconds_including_monitoring", "meta_calls", "accepted_meta_proposals"]
            if is_byte:
                metrics += ["test_bits_per_byte", "test_byte_perplexity"]
            per_arm[arm] = {"seeds": [r["seed"] for r in group],
                            "metrics": {metric: describe([r[metric] for r in group]) for metric in metrics},
                            "paired_effects": pairs,
                            "paired_summaries": {metric: describe([p[metric] for p in pairs]) for metric in (list(pairs[0])[1:] if pairs else [])}}
            if not is_byte:
                per_arm[arm]["grokking_counts"] = grokking_counts(group)
        task_results[task] = {"label": TASK_LABELS.get(task, task), "task": protocol["tasks"][task]["task"],
                              "confirmation_updates": protocol["tasks"][task]["confirmation_steps"], "arms": per_arm,
                              "uniform_prediction_reference": {"cross_entropy_nats": math.log(256 if is_byte else protocol["tasks"][task]["p"]),
                                  "scope": "Analytic uniform-probability reference, not an additional trained run."}}

    followup = analyze_followup(results / "grokking_followup")
    basis = analyze_basis_study(results / "basis_study")
    replays = integrity_replays(results, check)
    discovery_wall = sum(r["wall_seconds"] for r in discovery_rows)
    confirmation_wall = sum(r["wall_seconds_including_monitoring"] for r in rows)
    first_discovery = discovery_wall + (replays["canonical_to_first_pass_wall_adjustment"]["discovery"] if replays else 0)
    first_confirmation = confirmation_wall + (replays["canonical_to_first_pass_wall_adjustment"]["confirmation"] if replays else 0)
    followup_wall = (followup.get("discovery_seconds_sum", 0) + followup.get("confirmation_seconds_sum", 0)) if followup else 0
    basis_wall = basis["confirmation_seconds_sum"] + basis["preflight_seconds"] if basis else 0
    initial_updates = sum(r["optimizer_updates"] for r in discovery_rows + rows) + (
        followup.get("discovery_optimizer_updates", 0) + sum(r["optimizer_updates"] for r in followup.get("runs", [])) if followup else 0) + (
        sum(r["optimizer_updates"] for r in basis["runs"]) if basis else 0)
    initial_runs = len(discovery_rows) + len(rows) + (followup.get("discovery_runs", 0) + len(followup.get("runs", [])) if followup else 0) + (len(basis["runs"]) if basis else 0)
    overall_passed = not errors and all(study["audit"]["passed"] for study in (followup, basis) if study and "audit" in study)
    return {"schema": "singularity.training-revision-analysis/1", "complete": complete,
            "overall_audit_passed": overall_passed,
            "analysis_script_sha256": file_hash(Path(__file__)),
            "input_file_sha256": {name: file_hash(results / name) for name in
                                  ("protocol.json", "selection.json", "confirmation_plan.json", source.name)},
            "protocol_sha256": ph, "confirmation_plan_sha256": canonical_hash(plan),
            "confirmation_source": source.name, "expected_runs": len(planned), "analyzed_runs": len(rows),
            "seed_order": seeds, "arm_order": arms, "task_order": tasks,
            "primary_effect": "meta minus same-seed selected fixed AdamW final TEST cross-entropy; negative favors meta",
            "reporting": "Raw three-seed effects, arithmetic means and observed ranges; no confidence interval or significance claim.",
            "byte_metric_scope": "Cross-entropy is nats per next byte; bits per byte = NLL / log(2); exp(NLL) is byte perplexity, never standard word perplexity.",
            "metric_units": {"test_cross_entropy_nats": "nats per target", "test_accuracy": "fraction correct",
                             "test_accuracy_delta_percentage_points": "100 times the variant-minus-baseline accuracy fraction",
                             "wall_seconds_including_monitoring": "seconds", "test_bits_per_byte": "bits per next byte"},
            "timing_scope": protocol["timing"], "audit": {"passed": not errors, "failed_checks": errors, "checks": checks,
                "scope": "Recorded plan/summary/log/checkpoint consistency, split metadata hashes, available corpus-file hashes and declared access counts; not a formal proof of implementation correctness. Optional follow-up audit is separate."},
            "compute": {"discovery_seconds_sum": discovery_wall,
                        "confirmation_seconds_sum": confirmation_wall,
                        "first_pass_discovery_seconds": first_discovery,
                        "first_pass_confirmation_seconds": first_confirmation,
                        "integrity_replay_additional_seconds": replays["additional_wall_seconds"] if replays else 0,
                        "basis_run_and_preflight_seconds": basis_wall,
                        "all_accounted_job_wall_seconds": first_discovery + first_confirmation + followup_wall + basis_wall + (replays["additional_wall_seconds"] if replays else 0),
                        "initial_neural_training_runs_including_discovery": initial_runs,
                        "initial_optimizer_updates": initial_updates,
                        "integrity_replay_extra_optimizer_updates": replays["additional_optimizer_updates"] if replays else 0,
                        "all_accounted_optimizer_updates": initial_updates + (replays["additional_optimizer_updates"] if replays else 0),
                        "optimizer_update_scope": "Declared study training runs and integrity repeats; isolated single-step numerical controls and regression tests are separate.",
                        "job_wall_scope": "Sum of inclusive job elapsed seconds, not total elapsed user waiting time or exclusive CPU time; overlapping jobs and shared-host contention are possible.",
                        "confirmation_orchestrator_seconds": confirmation.get("confirmation_total_seconds"),
                        "discovery_orchestrator_seconds": selection.get("discovery_total_seconds"),
                        "confirmation_meta_calls": sum(r["meta_calls"] for r in rows),
                        "timing_warning": "Shared host; not a dedicated-hardware throughput comparison. Discovery and extra meta work are included, not free."},
            "discovery": discovery_rows, "tasks": task_results, "runs": rows,
            "integrity_replays": replays,
            "protocol_deviations": ([{"kind": "integrity_verification_test_repeats",
                                      "additional_test_evaluations": replays["additional_test_evaluations"],
                                      "scope": "Verification repeats after saved-log integrity failures; not independent seeds or model-selection trials."}]
                                    if replays and replays["additional_test_evaluations"] else []),
            "grokking_followup": followup, "basis_study": basis}


def plot_results(analysis: dict[str, Any], destination: Path, *, preview: Path | None = None) -> None:
    """Three task panels, individual seeds and observed ranges; no invented data."""
    if not analysis["complete"] or not analysis["audit"]["passed"]:
        raise ValueError("Publication figure requires all planned runs and a passing protocol audit")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    matplotlib.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "svg.hashsalt": "singularity-training-revision",
                               "axes.titlesize": 13, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10})
    bg, cream, muted, grid = "#0a1120", "#f4f0e6", "#acb9cf", "#283650"
    colors = {"baseline": cream, "cosine": "#8ea9e8", "layer_decay": "#e9b886", "meta": "#6bd9c1"}
    fig, axes = plt.subplots(1, 3, figsize=(14.4, 7.2), facecolor=bg)
    fig.subplots_adjust(left=.065, right=.98, bottom=.29, top=.68, wspace=.32)
    for panel, (axis, task) in enumerate(zip(axes, analysis["task_order"])):
        result = analysis["tasks"][task]
        axis.set_facecolor(bg)
        arms = analysis["arm_order"]
        for j, seed in enumerate(analysis["seed_order"]):
            ys = [next(r["test_cross_entropy_nats"] for r in analysis["runs"] if r["task"] == task and r["arm"] == arm and r["seed"] == seed) for arm in arms]
            axis.plot(range(len(arms)), ys, color=muted, alpha=.26, linewidth=.8, zorder=1)
        maximum = 0.0
        for x, arm in enumerate(arms):
            stat = result["arms"][arm]["metrics"]["test_cross_entropy_nats"]
            maximum = max(maximum, stat["max"])
            axis.vlines(x, stat["min"], stat["max"], color=colors[arm], linewidth=1.5, zorder=3)
            axis.hlines([stat["min"], stat["max"]], x-.06, x+.06, color=colors[arm], linewidth=1, zorder=3)
            axis.scatter([x-.08, x, x+.08], stat["values"], s=35, color=colors[arm], edgecolor=bg, linewidth=.6, zorder=4)
            axis.hlines(stat["mean"], x-.19, x+.19, color=colors[arm], linewidth=3, zorder=5)
        axis.set_ylim(0, maximum * 1.16)
        axis.set_xlim(-.4, len(arms)-.6)
        axis.set_xticks(range(len(arms)), ["Fixed\nAdamW", "Cosine", "Layer\ndecay", "Meta"])
        axis.set_ylabel("Final TEST cross-entropy · nats", color=muted)
        axis.tick_params(colors=muted, length=0, pad=9)
        axis.yaxis.grid(True, color=grid, linewidth=.8)
        axis.set_axisbelow(True)
        for spine in axis.spines.values():
            spine.set_visible(False)
        title = result["label"].replace(" · ", "\n")
        axis.set_title(title, color=cream, loc="left", fontweight="bold", pad=34)
        axis.text(0, 1.035, f"{result['confirmation_updates']:,} updates · 3 paired seeds", transform=axis.transAxes, color=muted, fontsize=9.5)
        effect = result["arms"]["meta"]["paired_summaries"]["test_cross_entropy_delta_nats"]
        axis.text(0, -.27, f"Meta − fixed: {effect['mean']:+.4f} nats", transform=axis.transAxes,
                  color=colors["meta"], fontsize=11, fontweight="bold")
        axis.text(0, -.35, "Seed effects: " + ", ".join(f"{v:+.4f}" for v in effect["values"]),
                  transform=axis.transAxes, color=muted, fontsize=8.6)
    fig.text(.065, .94, "TRAINING, MEASURED", color="#6bd9c1", fontsize=10, fontweight="bold", ha="left")
    fig.text(.065, .875, "One frozen test. Three paired seeds. Every optimizer arm.", color=cream, fontsize=21, fontweight="bold", ha="left")
    fig.text(.065, .825, "Within-task update budgets are equal. Lower loss is better; lines pair the same initialization and sampler seed.", color=muted, fontsize=11, ha="left")
    handles = [Line2D([0], [0], marker="o", linestyle="none", color=cream, label="Individual seed", markersize=5),
               Line2D([0], [0], color=cream, linewidth=3, label="Arithmetic mean"),
               Line2D([0], [0], marker="|", color=muted, label="Observed min–max, no confidence interval")]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(.058, .085), ncol=3, frameon=False, labelcolor=muted, fontsize=10, handlelength=1.5)
    fig.text(.065, .065, "WikiText-2 uses declared byte prefixes: NLL / log(2) gives bits per byte; this is not standard word perplexity.", color=muted, fontsize=10)
    extra_tests = (analysis.get("integrity_replays") or {}).get("additional_test_evaluations", 0)
    footer = (f"One final TEST per logical run; {extra_tests} integrity-verification TEST repeats disclosed. Extra tuning and meta work counted; shared CPU host."
              if extra_tests else "TEST evaluated once per frozen run. All tuning and extra meta computation are accounted for; shared-host timing is not a throughput benchmark.")
    fig.text(.065, .03, footer, color=muted, fontsize=9)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, format="svg", facecolor=bg, metadata={"Date": None, "Title": "Measured optimizer comparison across three training tasks"})
    svg = destination.read_text()
    position = svg.index(">", svg.index("<svg"))
    description = "Three panels show final TEST cross-entropy for modular MLP, modular transformer and WikiText-2 byte transformer. Individual seeds, arithmetic means and observed ranges are retained. Negative meta-minus-baseline cross-entropy favors meta. This figure contains measured data, not confidence intervals."
    svg = svg[:position] + ' role="img" aria-labelledby="training-title training-description"' + svg[position:position+1] + \
        '<title id="training-title">Measured optimizer comparisons</title><desc id="training-description">' + escape(description) + '</desc>' + svg[position+1:]
    destination.write_text(svg)
    if preview:
        preview.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(preview, dpi=160, facecolor=bg)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--figure", type=Path, default=ROOT / "docs/assets/training-results.svg")
    parser.add_argument("--preview", type=Path, default=None)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--no-figure", action="store_true")
    args = parser.parse_args()
    try:
        result = analyze(args.results, require_complete=not args.allow_partial)
        output = args.output or args.results / "analysis.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
        if result["complete"] and not args.no_figure and not args.allow_partial:
            plot_results(result, args.figure, preview=args.preview)
        print(json.dumps({"analysis": str(output), "complete": result["complete"], "runs": result["analyzed_runs"],
                          "audit_passed": result["audit"]["passed"], "overall_audit_passed": result["overall_audit_passed"],
                          "failed_checks": result["audit"]["failed_checks"]}))
        if not result["overall_audit_passed"]:
            raise SystemExit(1)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, f"Analysis cannot complete: {exc}\n")


if __name__ == "__main__":
    main()
