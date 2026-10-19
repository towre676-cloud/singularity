#!/usr/bin/env python3
"""Independent standard-library replay of deployment audit evidence.

This verifier imports neither the experiment runner nor Singularity's audit
or selection implementation. It needs published observations and receipts,
not model weights, PyTorch, or execution artifacts.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "applications/training_lab/results/deployment_audit"
CONTINUOUS = ("top_logprob", "entropy", "continuation_logprob")


def read(path):
    return json.loads(Path(path).read_text())


def load_observations(directory, probes=None):
    """Restore each exact probe coordinate from bounded readable JSON shards."""
    manifest = read(directory / "observations_manifest.json")
    require(manifest["schema"] == "singularity.deployment-observations/1", "unknown observation schema")
    require(digest(manifest["entries"]) == manifest["entries_sha256"], "observation manifest digest differs")
    count, collections, seen_files = manifest["probe_count"], {}, set()
    if probes is not None:
        require(count == len(probes), "observation probe population differs")
    for entry in manifest["entries"]:
        path = (directory / entry["file"]).resolve()
        require(path.is_relative_to(directory.resolve()), "observation shard escapes evidence directory")
        require(entry["file"] not in seen_files, "duplicate observation shard")
        seen_files.add(entry["file"])
        raw = path.read_bytes()
        require(len(raw) == entry["bytes"] and hashlib.sha256(raw).hexdigest() == entry["sha256"], "observation shard bytes differ")
        chunk = json.loads(raw)
        require(chunk["collection"] == entry["collection"] and chunk["probe_indices"] == entry["probe_indices"], "observation coordinates differ")
        require(len(chunk["rows"]) == len(chunk["probe_indices"]) == len(chunk["probe_ids"]), "observation shard alignment differs")
        require(all(type(index) is int and 0 <= index < count for index in chunk["probe_indices"]), "invalid observation coordinate")
        if probes is not None:
            require(chunk["probe_ids"] == [probes[index]["id"] for index in chunk["probe_indices"]], "observation probe labels differ")
        key = tuple(chunk["collection"])
        rows = collections.setdefault(key, [None] * count)
        for index, row in zip(chunk["probe_indices"], chunk["rows"]):
            require(isinstance(index, int) and 0 <= index < count and rows[index] is None, "overlapping or invalid observation coordinate")
            rows[index] = row
    require(all(all(row is not None for row in rows) for rows in collections.values()), "missing observation coordinate")
    restored = {}
    for key, rows in collections.items():
        if len(key) == 1:
            restored[key[0]] = rows
        else:
            require(len(key) == 2, "unexpected observation collection depth")
            restored.setdefault(key[0], {})[key[1]] = rows
    calibration = restored["calibration"]
    require(set(calibration) == set(range(len(calibration))), "calibration indices are not contiguous")
    restored["calibration"] = [calibration[i] for i in range(len(calibration))]
    return restored


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def near(actual, expected, message, absolute=1e-12):
    require(math.isclose(actual, expected, rel_tol=1e-12, abs_tol=absolute), message)


def compare(actual, expected, tie_margin):
    """Reconstruct deviations directly, including reference-only tie masking."""
    length, discrete = False, 0
    for key in ("argmax", "continuation"):
        if key not in expected:
            continue
        values = actual.get(key, [])
        if len(values) != len(expected[key]):
            length = True
            continue
        for index, (got, want) in enumerate(zip(values, expected[key])):
            ignore = key == "argmax" and expected.get("top_gap", [math.inf] * len(values))[index] <= tie_margin
            discrete += int(got != want and not ignore)
    maxima = {}
    for key in CONTINUOUS:
        if key not in expected:
            continue
        values = actual.get(key, [])
        if len(values) != len(expected[key]):
            length = True
            continue
        require(all(math.isfinite(x) for x in values), "nonfinite observation")
        maxima[key] = max((abs(x - y) for x, y in zip(values, expected[key])), default=0.)
    return {"length_mismatch": length, "discrete_mismatches": discrete, "max_abs": maxima}


def flagged(report, tolerance):
    return bool(report["length_mismatch"] or report["discrete_mismatches"]
                or any(value > tolerance[key] for key, value in report["max_abs"].items()))


def exhaustive(costs, fault_flags, indices=None, requirement=2):
    """Enumerate every subset of a pool, independently of branch-and-bound."""
    indices = list(range(len(costs))) if indices is None else list(indices)
    masks = [sum(1 << j for j, index in enumerate(indices) if values[index]) for values in fault_flags.values()]
    best = math.inf
    minimizers = []
    for subset in range(1 << len(indices)):
        if not all((subset & mask).bit_count() >= requirement for mask in masks):
            continue
        panel = tuple(index for j, index in enumerate(indices) if subset >> j & 1)
        cost = sum(costs[index] for index in panel)
        if cost < best:
            best, minimizers = cost, [panel]
        elif cost == best:
            minimizers.append(panel)
    require(best < math.inf, "infeasible required coverage")
    return best, minimizers


def verify_identity(directory):
    frozen, result = read(directory / "protocol.json"), read(directory / "results.json")
    require(digest(frozen["protocol"]) == frozen["protocol_sha256"], "protocol digest differs")
    require(result["protocol_sha256"] == frozen["protocol_sha256"], "result protocol differs")
    require(frozen["observations_before_freeze"] is False, "study not frozen before observations")
    for key in ("model_id", "revision", "target"):
        require(result[key] == frozen[key], "frozen identity differs: " + key)
    for name, expected in frozen["dependency_sha256"].items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected,
                "frozen implementation changed: " + name)
    panel = read(directory / "frozen_panel.json")
    require(panel["protocol_sha256"] == frozen["protocol_sha256"], "panel protocol differs")
    require(panel["frozen_before_heldout"] is True, "panel not frozen before excluded observations")
    for key, value in result["selection"].items():
        require(panel[key] == value, "frozen selection changed: " + key)
    artifact = read(directory / "artifact.json")
    require(result["artifact"] == artifact, "artifact receipt differs")
    require(artifact["graph_export"] == (frozen["target"] == "float32"), "graph target policy differs")
    require(artifact["state_reload_identical"] is True, "target reload differs")
    require(artifact["expected_target_state_sha256"] == artifact["reloaded_state_sha256"], "target state digest differs")
    require(digest(artifact["artifacts"]) == artifact["artifact_manifest_sha256"], "artifact manifest digest differs")
    if frozen["target"] == "dynamic_int8":
        require(artifact["quantized_linear_count"] > 0, "no real quantized modules")
        require(len(set(artifact["quantized_linear_modules"])) == artifact["quantized_linear_count"], "quantized module population differs")
        require(artifact["source_state_sha256"] != artifact["reloaded_state_sha256"], "INT8 state did not change")
        require(artifact["weights_only_load"] is True, "unrestricted quantized reload")
    else:
        require(artifact["quantized_linear_count"] == 0, "float target unexpectedly quantized")
        require(artifact["source_state_sha256"] == artifact["reloaded_state_sha256"], "float serialization changed weights")
        graph = artifact["graph_manifest"]
        require(graph["schema"] == "singularity.causal-torchscript/1" and graph["graph_export"] is True, "executable graph manifest missing")
        require(graph["artifact_sha256"] == artifact["artifacts"]["causal_graph.pt"]["sha256"], "executable graph hash differs")
        require(graph["artifact_bytes"] == artifact["artifacts"]["causal_graph.pt"]["bytes"], "executable graph size differs")
        require(graph["use_cache"] is False and graph["max_context"] == 96 and graph["max_batch_size"] == 3, "export shape/cache contract differs")
    return frozen, result


def verify_refinement(directory, frozen, result):
    """Bind the narrower INT8 contract to its retained rejected predecessor."""
    protocol = frozen["protocol"]
    if "parent_calibration_failure_file_sha256" not in protocol:
        return
    parent = DEFAULT / "smollm2-360m/dynamic_int8"
    original = read(parent / "protocol.json")
    require(hashlib.sha256((parent / "protocol.json").read_bytes()).hexdigest() == protocol["parent_protocol_file_sha256"],
            "refinement predecessor protocol changed")
    require(hashlib.sha256((parent / "calibration_failure.json").read_bytes()).hexdigest() == protocol["parent_calibration_failure_file_sha256"],
            "refinement predecessor failure changed")
    verify_calibration_failure(parent)
    require("POST-CALIBRATION" in protocol["status"], "refinement mislabeled as independent prospective study")
    for key in ("model_id", "revision", "target", "threads", "snapshot_manifest", "probes"):
        require(frozen[key] == original[key], "refinement changed model or probe identity: " + key)
    for key in ("pool", "construction_faults", "heldout_faults", "tolerance", "selection", "timing", "execution"):
        require(protocol[key] == original["protocol"][key], "refinement changed fixed scientific setting: " + key)
    approved = {"attention_backends": ["eager"], "batch_size": 1, "cache_execution": "full prefill"}
    require(protocol["approved_int8_execution"] == approved, "refinement approval is not eager-only batch1 fullprefill")
    require(protocol["calibration"]["dynamic_int8"] == [{"attention_backend": "eager", "batch_size": 1, "threads": 1},
                                                        {"attention_backend": "eager", "batch_size": 1, "threads": 2}],
            "refinement calibration differs from declared narrow profile")
    clean = copy.deepcopy(original["protocol"]["clean_heldout"])
    clean["sdpa_batch1_threads2_reverse"] = {"attention_backend": "sdpa", "batch_size": 1, "threads": 2, "reverse": True}
    require(protocol["clean_heldout"] == clean, "refinement discarded a clean transfer or added undeclared settings")
    require("scripts/confirm_int8_contract.py" in frozen["dependency_sha256"], "refinement wrapper is not frozen")
    old_artifact = read(parent / "artifact.json")
    require(result["artifact"]["reloaded_state_sha256"] == old_artifact["reloaded_state_sha256"],
            "refinement changed quantized model state")
    expected_metadata = {"calibration_envelope": approved, "post_calibration_refinement": True,
                         "original_protocol_file_sha256": protocol["parent_protocol_file_sha256"],
                         "original_failure_file_sha256": protocol["parent_calibration_failure_file_sha256"]}
    for label in result["panels"]:
        package = read(directory / ("package_" + label + ".json"))
        require(all(package["metadata"][key] == value for key, value in expected_metadata.items()),
                "refinement package lacks its approved machine contract or failure link")


def verify_execution(frozen, result):
    """Check proof receipts for genuine kernels, quantized modules and caches."""
    protocol = frozen["protocol"]
    expected = [{}]
    expected.extend(protocol["calibration"][frozen["target"]])
    expected.extend({"change": change} for change in protocol["heldout_faults"].values() if "cache_split" in change)
    expected.extend(config for config in protocol["clean_heldout"].values()
                    if frozen["target"] == "float32" or config["attention_backend"] != "torchscript")
    receipts = result["execution_receipts"]
    require(len(receipts) == len(expected), "execution proof population differs")
    normalized = [{"attention_backend": config.get("attention_backend", "eager"),
                   "batch_size": config.get("batch_size", 1), "threads": config.get("threads", frozen["threads"]),
                   "change": config.get("change", {})} for config in expected]
    actual = [{key: receipt[key] for key in ("attention_backend", "batch_size", "threads", "change")}
              for receipt in receipts]
    require(sorted(map(digest, actual)) == sorted(map(digest, normalized)), "execution configuration population differs")
    quantized = set(result["artifact"]["quantized_linear_modules"])
    for receipt in receipts:
        backend, change = receipt["attention_backend"], receipt["change"]
        require((receipt["sdpa_calls"] > 0) if backend == "sdpa" else receipt["sdpa_calls"] == 0,
                "attention backend kernel not proved")
        require((receipt["graph_calls"] > 0) if backend == "torchscript" else receipt["graph_calls"] == 0,
                "executable graph execution not proved")
        require(set(receipt["quantized_linear_calls"]) == quantized, "quantized module execution population differs")
        require(all(count > 0 for count in receipt["quantized_linear_calls"].values()), "quantized module did not execute")
        if "cache_split" in change:
            require(bool(receipt["cache"]), "cache execution not proved")
            for row in receipt["cache"]:
                require(row["prefix_tokens"] > 0 and row["suffix_tokens"] > 0, "empty cache chunk")
                require(row["cache_sequence_length"] == row["prefix_tokens"], "cache length differs from forwarded prefix")
                require(row["cache_passed_to_suffix"] == (not change.get("drop_cache", False)), "cache transfer policy differs")
        else:
            require(receipt["cache"] == [], "unrequested cache execution")


def verify_observations(directory, frozen, result):
    probes, protocol = frozen["probes"], frozen["protocol"]
    observations = load_observations(directory, probes)
    spec = protocol["tolerance"]
    clean = {name: config for name, config in protocol["clean_heldout"].items()
             if frozen["target"] == "float32" or config["attention_backend"] != "torchscript"}
    expected_runs = {"construction": protocol["construction_faults"], "heldout": protocol["heldout_faults"],
                     "clean_heldout": clean}
    for kind, names in expected_runs.items():
        require(set(observations[kind]) == set(names), "missing or extra " + kind + " observations")
    require(len(observations["calibration"]) == len(protocol["calibration"][frozen["target"]]), "calibration population differs")
    runs = [observations["reference"], *observations["calibration"],
            *(run for kind in expected_runs for run in observations[kind].values())]
    for run in runs:
        require(len(run) == len(probes), "observations do not align with probes")
        for row in run:
            for key in (*CONTINUOUS, "top_gap"):
                require(all(math.isfinite(value) for value in row.get(key, [])), "nonfinite retained observation")
    for index, expected in enumerate(observations["reference"]):
        maxima = {key: 0. for key in CONTINUOUS if key in expected}
        for run in observations["calibration"]:
            delta = compare(run[index], expected, spec["tie_margin"])
            require(not delta["length_mismatch"] and not delta["discrete_mismatches"], "unstable clean calibration")
            maxima = {key: max(value, delta["max_abs"][key]) for key, value in maxima.items()}
        require(maxima == observations["calibration_maxima"][index], "calibration maximum differs")
        tolerance = {key: spec["factor"] * value + spec["floor"] for key, value in maxima.items()}
        require(tolerance == observations["tolerances"][index], "calibrated tolerance differs")
        require(probes[index]["cost"] == max(len(expected["argmax"]), probes[index].get("pad_to", 0)), "native token cost differs")
    reports, flags = {}, {}
    for kind in expected_runs:
        for name, run in observations[kind].items():
            reports[name] = [compare(row, reference, spec["tie_margin"])
                             for row, reference in zip(run, observations["reference"])]
            flags[name] = [flagged(row, tolerance) for row, tolerance in zip(reports[name], observations["tolerances"])]
    require(result["pool_separator_counts"] == {name: sum(flags[name]) for kind in ("construction", "heldout")
                                               for name in observations[kind]}, "pool fault counts differ")
    require(result["pool_clean_false_alarms"] == {name: [p["id"] for p, flag in zip(probes, flags[name]) if flag]
                                                for name in observations["clean_heldout"]}, "pool clean alarms differ")
    return observations, reports, flags


def verify_selection(directory, frozen, result, observations, reports, flags):
    probes, selection = frozen["probes"], result["selection"]
    costs, requirement = [p["cost"] for p in probes], frozen["protocol"]["selection"]["requirement"]
    eligible = {name: flags[name] for name in observations["construction"] if sum(flags[name]) >= requirement}
    require(bool(eligible), "no retained construction distinction")
    unavailable = {name: sum(flags[name]) for name in observations["construction"] if name not in eligible}
    require(set(selection["eligible_faults"]) == set(eligible), "eligible construction catalogue differs")
    require(selection["unavailable_faults"] == unavailable, "unavailable distinctions misreported")
    optimum, minimizers = exhaustive(costs, eligible, requirement=requirement)
    require(selection["exact"]["cost"] == optimum, "exact panel is not globally optimal")
    require(tuple(selection["exact"]["indices"]) in minimizers, "reported exact indices are not minimizing")
    require(selection["independent_enumeration"]["subsets"] == 1 << len(probes), "oracle omitted subsets")
    require(selection["independent_enumeration"]["minimum_cost"] == optimum, "reported oracle cost differs")
    prune_cost, prune_panels = exhaustive(costs, eligible, selection["greedy"]["indices"], requirement)
    require(selection["pruned_greedy"]["cost"] == prune_cost, "pruned greedy is not optimal within greedy output")
    require(tuple(selection["pruned_greedy"]["indices"]) in prune_panels, "pruned indices differ")
    require(result["full_pool_cost"] == sum(costs), "full pool cost differs")
    index = {probe["id"]: i for i, probe in enumerate(probes)}
    for label, panel_report in result["panels"].items():
        panel = selection[label]
        members = panel["indices"]
        require(panel["cost"] == sum(costs[i] for i in members), "panel cost differs: " + label)
        require(panel["probe_ids"] == [probes[i]["id"] for i in members], "panel ids differ")
        require(all(sum(values[i] for i in members) >= requirement for values in eligible.values()), "panel lacks construction coverage")
        for name, evidence in panel_report["faults"].items():
            count = sum(flags[name][i] for i in members)
            require((evidence["separating_probes"], evidence["detected"], evidence["two_witness"])
                    == (count, count > 0, count >= 2), "panel detection report differs")
            require(evidence["heldout"] == (name in observations["heldout"]), "heldout label differs")
        require(panel_report["clean_false_alarms"] == {name: [probes[i]["id"] for i in members if flags[name][i]]
                                                      for name in observations["clean_heldout"]}, "panel clean alarms differ")
        package = read(directory / ("package_" + label + ".json"))
        require(package["package_sha256"] == digest({k: v for k, v in package.items() if k != "package_sha256"}), "package digest differs")
        require([p["id"] for p in package["probes"]] == panel["probe_ids"], "package membership differs")
        require(package["requirement"] == requirement and not package["deficient_faults"], "package guarantee is deficient")
        spec = frozen["protocol"]["tolerance"]
        require(package["constants"] == {"tie_margin": spec["tie_margin"], "tolerance_factor": spec["factor"],
                                          "tolerance_floor": spec["floor"]}, "package numerical constants differ")
        require(package["metadata"]["protocol_sha256"] == frozen["protocol_sha256"]
                and package["metadata"]["target"] == frozen["target"], "package protocol/target metadata differs")
        identity = {"model_id": frozen["model_id"], "revision": frozen["revision"], "representation": frozen["target"],
                    "source_snapshot_sha256": digest(frozen["snapshot_manifest"]),
                    "target_artifact_sha256": result["artifact"]["artifact_manifest_sha256"]}
        require(all(package["contract"][key] == value for key, value in identity.items()), "package execution identity differs")
        for probe in package["probes"]:
            i = index[probe["id"]]
            require(all(probe[key] == value for key, value in probes[i].items()), "package probe inputs or costs differ")
            require(probe["expected"] == observations["reference"][i], "package reference differs")
            require(probe["tolerance"] == observations["tolerances"][i], "package tolerance differs")
            require(probe["clean_maximum"] == observations["calibration_maxima"][i], "package calibration differs")
        require(set(package["fault_evidence"]) == set(eligible), "package fault evidence population differs")
        require(len(package["witness"]) == len(eligible)
                and {row["distinction"] for row in package["witness"]} == set(eligible), "package witness population differs")
        require(panel_report["verification"] == {"faults": len(eligible), "panel_probes": len(members),
                                                   "problems": [], "requirement": requirement, "verified": True},
                "reported package verification differs")
        for name, values in eligible.items():
            separating = [probes[i]["id"] for i in members if values[i]]
            require(package["coverage"][name] == len(separating), "package coverage differs")
            witness = next(row["separating_probes"] for row in package["witness"] if row["distinction"] == name)
            require(len(witness) >= requirement and len(set(witness)) == len(witness) and set(witness) <= set(separating), "package witness invalid")
            for probe_id in panel["probe_ids"]:
                actual = any(values[i] for i in members if probes[i]["id"] != probe_id)
                require(panel_report["all_single_probe_erasures"][probe_id][name] == actual and actual, "erasure guarantee differs")
            require(set(package["fault_evidence"][name]) == set(panel["probe_ids"]), "package fault/probe evidence population differs")
            for probe_id, evidence in package["fault_evidence"][name].items():
                expected = reports[name][index[probe_id]]
                require(evidence == {**expected, "flags": flagged(expected, observations["tolerances"][index[probe_id]])}, "package fault evidence differs")
    return {"optimum_tokens": optimum, "pruned_greedy_tokens": prune_cost,
            "construction_distinctions": len(eligible), "excluded_distinctions": unavailable}


def verify_random(frozen, result, flags):
    selection = result["selection"]
    rng = random.Random(frozen["protocol"]["selection"]["seed"])
    probes = frozen["probes"]
    eligible = [flags[name] for name in selection["eligible_faults"]]
    reconstructed = []
    for trial, actual in enumerate(selection["random_panels"]):
        order = list(range(len(probes)))
        rng.shuffle(order)
        members = []
        for index in order:
            members.append(index)
            if all(sum(values[i] for i in members) >= 2 for values in eligible):
                break
        cost, panels = exhaustive([p["cost"] for p in probes],
                                  {str(i): values for i, values in enumerate(eligible)},
                                  sorted(members))
        pruned = min(panels)
        expected = {"trial": trial, "indices": list(pruned), "cost": cost,
                    "unpruned_indices": sorted(members), "unpruned_cost": sum(probes[i]["cost"] for i in members),
                    "subsets_checked": 1 << len(members)}
        require(actual == expected, "random baseline differs")
        reconstructed.append(expected)
    require(len(reconstructed) == 64, "random population differs")
    ordered = sorted(reconstructed, key=lambda row: (row["cost"], row["trial"]))
    expected = ordered[(len(ordered) - 1) // 2]
    for key, value in expected.items():
        require(selection["random_median"][key] == value, "random median representative differs")


def verify_timing(frozen, result):
    protocol, timing, artifact = frozen["protocol"], result["timing"], result["artifact"]
    arms = protocol["timing"]["arms"]
    require(len(timing["pairs"]) == protocol["timing"]["pairs"], "timing population differs")
    rng = random.Random(protocol["timing"]["order_seed"])
    for repeat, row in enumerate(timing["pairs"]):
        order = list(arms)
        rng.shuffle(order)
        require(row["order"] == order and row["repeat"] == repeat, "timing interleaving differs")
        require(all(math.isfinite(row[label]) and row[label] > 0 for label in arms), "invalid timing")
    medians = {label: statistics.median(row[label] for row in timing["pairs"]) for label in arms}
    require(timing["median_seconds"] == medians, "timing medians differ")
    for label in arms[1:]:
        report = timing["amortization"][label]
        saved = medians["full_pool"] - medians[label]
        near(report["seconds_saved_per_check"], saved, "saved runtime differs")
        near(report["full_pool_over_panel"], medians["full_pool"] / medians[label], "speed ratio differs")
        require(report["gross_all_comparators_build_checks"] == (math.ceil(timing["construction_seconds"] / saved) if saved > 0 else None), "gross construction break-even differs")
        incremental = timing["construction_fault_seconds"] + timing["selection_seconds"] + timing["package_seconds"][label]
        near(report["conservative_incremental_seconds"], incremental, "incremental construction cost differs")
        require(report["conservative_incremental_build_checks"] == (math.ceil(incremental / saved) if saved > 0 else None), "incremental break-even differs")
        gross = timing["construction_seconds"] + artifact["load_seconds"] + artifact["serialization_conversion_reload_seconds"]
        require(report["including_artifact_checks"] == (math.ceil(gross / saved) if saved > 0 else None), "gross artifact break-even differs")


def verify_directory(directory):
    directory = Path(directory)
    if not (directory / "results.json").exists():
        return verify_calibration_failure(directory)
    frozen, result = verify_identity(directory)
    verify_refinement(directory, frozen, result)
    verify_execution(frozen, result)
    observations, reports, flags = verify_observations(directory, frozen, result)
    summary = verify_selection(directory, frozen, result, observations, reports, flags)
    verify_random(frozen, result, flags)
    verify_timing(frozen, result)
    return {"directory": str(directory), "model_id": result["model_id"], "target": result["target"],
            "verified": True, **summary}


def verify_calibration_failure(directory):
    """A correctly reported clean-instability outcome need not build a panel."""
    frozen = read(directory / "protocol.json")
    failure = read(directory / "calibration_failure.json")
    require(digest(frozen["protocol"]) == frozen["protocol_sha256"], "failed study protocol digest differs")
    require(frozen["observations_before_freeze"] is False, "failed study not frozen before observations")
    for name, expected in frozen["dependency_sha256"].items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, "failed study implementation changed")
    require(len(failure["reference"]) == len(frozen["probes"]), "failed study reference population differs")
    require(len(failure["calibration"]) == len(frozen["protocol"]["calibration"][frozen["target"]]), "failed study clean population differs")
    unstable = []
    for clean_index, run in enumerate(failure["calibration"]):
        require(len(run) == len(failure["reference"]), "failed study clean observations unaligned")
        for probe_index, (actual, expected) in enumerate(zip(run, failure["reference"])):
            report = compare(actual, expected, frozen["protocol"]["tolerance"]["tie_margin"])
            if report["length_mismatch"] or report["discrete_mismatches"]:
                unstable.append({"calibration": clean_index, "probe": probe_index})
    require(bool(unstable), "reported clean instability has no independent evidence")
    require(not (directory / "results.json").exists() and not (directory / "frozen_panel.json").exists(), "failed calibration silently produced a panel")
    return {"directory": str(directory), "model_id": frozen["model_id"], "target": frozen["target"],
            "verified": True, "outcome": "clean calibration unstable; no audit guarantee", "unstable_coordinates": unstable}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="*", type=Path)
    args = parser.parse_args()
    directories = args.directories or sorted({path.parent for name in ("results.json", "calibration_failure.json")
                                            for path in DEFAULT.glob("**/" + name)})
    require(bool(directories), "no complete deployment audit evidence")
    print(json.dumps({"verified": [verify_directory(path) for path in directories]}, indent=2))


if __name__ == "__main__":
    main()
