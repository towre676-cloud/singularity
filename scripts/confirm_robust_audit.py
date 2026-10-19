#!/usr/bin/env python3
"""Robust deployment-fault panels for the training lab's byte transformers.

Phases, each run once and in order:

  freeze     write the protocol: probe pool, fault catalogue, tolerance rule
  construct  observe seeds 1000/1001 under clean reruns and construction
             faults; choose the minimum-cost 2-robust panel and comparators
  audit      apply the frozen panels to excluded seed 1002, held-out fault
             strengths, an excluded fault family and separate clean controls;
             export a standalone package for seed 1002
  timing     resident panel versus full-pool checks, cold command-line checks
             and amortized cost

Faults are simulated silently: the faulty adapter declares the healthy
contract, so only executed behavior can reveal it.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
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
OUTPUT = RESULTS / "robust_audit"
CONSTRUCTION_SEEDS, HELDOUT_SEED = (1000, 1001), 1002
REQUIREMENT = 2


def probe(identifier, text, pad_to=None):
    raw = text.encode("utf-8")
    if len(raw) > 64 or (pad_to is not None and not len(raw) <= pad_to <= 64):
        raise ValueError("probe exceeds the 64-byte context: " + identifier)
    record = {"id": identifier, "text": text, "cost": pad_to or len(raw)}
    if pad_to is not None:
        record["pad_to"] = pad_to
    return record


# Declared before any observation. Cost = forwarded input tokens (bytes).
PROBES = [
    probe("full_history", "The history of the city begins with a small settlement on the ri"),
    probe("full_season", "During the 1998 season the team won eleven of sixteen games and"),
    probe("full_album", "The album was released in March and reached number four on the c"),
    probe("full_species", "This species is found in forests and grasslands across the south"),
    probe("pad64_born", "He was born in 1907.", 64),
    probe("pad64_river", "The river is long.", 64),
    probe("pad64_game", "The game was a draw", 64),
    probe("pad64_church", "A church was built there", 64),
    probe("pad32_war", "After the war ended", 32),
    probe("pad32_film", "The film received", 32),
    probe("short_city", "The city has a population"),
    probe("short_first", "It was the first time"),
    probe("short_known", "She is known for"),
    probe("uni_ligature", "The \ufb01nal score was \u00bd point \u2014 a record\u2026"),
    probe("uni_accents", "Caf\u00e9 owners in Montr\u00e9al and S\u00e3o Paulo"),
    probe("uni_padded", "Na\u00efve r\u00e9sum\u00e9 \u00b2", 48),
    probe("uni_long", "The Z\u00fcrich \ufb02oor plan of 1924 covers 2\u00b3 m and more."),
    probe("nl_short", "= History =\nThe town", 40),
    probe("nl_long", "= Early life =\nHe grew up in a small town.\n= Career =\nHe then"),
    probe("nl_list", "Results:\n1. First\n2. Second\n3. Third"),
]

CONSTRUCTION_FAULTS = {
    "padding_mask_dropped": {"pass_attention_mask": False},
    "position_offset_missing": {"position_correction": False},
    "truncate_48": {"truncate_to": 48},
    "unicode_nfkc": {"normalization": "NFKC"},
    "ascii_replace": {"encoding_errors": "replace"},
    "temperature_1.3": {"temperature": 1.3},
    "quantize_layer1_ffn_in_6bit": {"quantize": ["body.layers.1.linear1.weight", 6]},
}
HELDOUT_FAULTS = {
    "crlf_newlines": {"newline": "\r\n"},                           # excluded family
    "unicode_nfd": {"normalization": "NFD"},                        # new variant of a known family
    "temperature_1.1": {"temperature": 1.1},                        # weaker strength
    "truncate_56": {"truncate_to": 56},                             # weaker strength
    "quantize_layer0_attn_out_6bit": {"quantize": ["body.layers.0.self_attn.out_proj.weight", 6]},  # new location
}
CALIBRATION_CLEAN = {"batch_size_1": {"batch_size": 1}, "threads_1": {"threads": 1}}
FALSE_ALARM_CLEAN = {"deepcopy_clone": {"clone": True}, "batch_size_3": {"batch_size": 3},
                     "reversed_order": {"reverse": True}, "threads_4": {"threads": 4}}

PROTOCOL = {
    "schema": "singularity.robust-audit-protocol/1",
    "purpose": "Minimum-cost probe panels that detect realistic silent deployment faults with one missing result tolerated",
    "models": "retained WikiText byte transformers; construction seeds 1000 and 1001; seed 1002 excluded from selection",
    "probes": PROBES,
    "cost": "forwarded input tokens: pad_to when declared, otherwise UTF-8 length",
    "observations": "teacher-forced argmax, top log-probability, top-two gap and entropy at every real position",
    "construction_faults": CONSTRUCTION_FAULTS,
    "heldout_faults": HELDOUT_FAULTS,
    "calibration_clean_runs": CALIBRATION_CLEAN,
    "false_alarm_clean_runs": FALSE_ALARM_CLEAN,
    "tolerance": {"factor": 4.0, "floor": 1e-6, "tie_margin": 1e-4,
                  "rule": "per probe and continuous feature: factor * max calibration-clean deviation + floor; non-tie discrete changes always flag"},
    "quantization": "symmetric per-tensor: qmax=2**(bits-1)-1, scale=max|W|/qmax, W'=clamp(round(W/scale))*scale",
    "silent_fault_rule": "faulty adapters declare the healthy contract",
    "distinctions": "each (construction seed, construction fault) pair; separated by a probe when that probe flags under the seed's own tolerances",
    "requirement": REQUIREMENT,
    "selection": "exact minimum-cost 2-robust coverage over 20 probes, verified by exhaustive enumeration of all 2**20 subsets",
    "comparators": {"greedy": "cost per remaining deficit reduced",
                    "fixed_typical": "the four full-length typical sentences (a conventional regression panel)",
                    "fixed_all_short": "all probes of at most 32 forwarded tokens",
                    "random": "1000 seeded random orders (seed 51713); add probes while total cost stays within the exact panel's cost"},
    "audit": "freeze panels, then on seed 1002 and on construction seeds: construction faults, held-out faults, false-alarm clean runs; no reselection",
    "timing": {"threads": 2, "warmup_pairs": 5, "measured_pairs": 30, "order_seed": 30319, "cold_cli_repeats": 5},
    "claim_boundary": "Exact robust coverage of the declared construction table only. Transfer to seed 1002, held-out faults and false-alarm rates are measured on these declared runs; no bound for other models or faults.",
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
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=1, sort_keys=True, allow_nan=False) + "\n")
    os.replace(temporary, path)


def checkpoint(seed):
    return RESULTS / f"confirmation/wikitext_byte/baseline/seed_{seed}/checkpoint.pt"


def dependencies():
    return {name: sha((ROOT / name).read_bytes()) for name in (
        "scripts/confirm_robust_audit.py", "src/singularity/model_audit/core.py",
        "src/singularity/model_audit/adapters.py", "src/singularity/robust_coverage.py",
        "src/singularity/training/models.py", "src/singularity/training/runner.py")}


def quantized(model, name, bits):
    import torch
    model = copy.deepcopy(model)
    parameter = dict(model.named_parameters())[name]
    qmax = (1 << (bits - 1)) - 1
    with torch.no_grad():
        scale = parameter.abs().max() / qmax
        parameter.copy_((parameter / scale).round().clamp(-qmax, qmax) * scale)
    return model


def observe(model, contract, change, probes=PROBES):
    """Observations of ``probes`` under one healthy or changed pipeline."""
    import torch
    from singularity.model_audit.adapters import ByteTransformerAdapter
    change = dict(change)
    threads = change.pop("threads", 2)
    if change.pop("clone", False):
        model = copy.deepcopy(model)
    if "quantize" in change:
        model = quantized(model, *change.pop("quantize"))
    reverse = change.pop("reverse", False)
    adapter = ByteTransformerAdapter(model, declared_contract=contract, **change)
    previous = torch.get_num_threads()
    torch.set_num_threads(threads)
    try:
        ordered = list(reversed(probes)) if reverse else list(probes)
        result = adapter.observe(ordered)
    finally:
        torch.set_num_threads(previous)
    return list(reversed(result)) if reverse else result


def load(seed):
    from singularity.training.runner import load_checkpoint
    return load_checkpoint(checkpoint(seed))[0]


def healthy_contract(model):
    from singularity.model_audit.adapters import ByteTransformerAdapter
    return ByteTransformerAdapter(model).contract()


def seed_table(seed, faults):
    """Reference, tolerances and per-fault probe flags for one checkpoint."""
    from singularity.model_audit import deviation, flags, tolerances_from_clean
    model = load(seed)
    contract = healthy_contract(model)
    reference = observe(model, contract, {})
    calibration = [observe(model, contract, change) for change in CALIBRATION_CLEAN.values()]
    spec = PROTOCOL["tolerance"]
    tolerances, maxima = tolerances_from_clean(reference, calibration, spec["factor"], spec["floor"], spec["tie_margin"])
    table, observations = {}, {}
    for name, change in faults.items():
        rows = observe(model, contract, change)
        observations[name] = rows
        table[name] = [flags(deviation(o, r, spec["tie_margin"]), t) for o, r, t in zip(rows, reference, tolerances)]
    return {"model": model, "contract": contract, "reference": reference, "calibration": calibration,
            "tolerances": tolerances, "clean_maxima": maxima, "flags": table, "observations": observations}


def freeze(output):
    if (output / "protocol.json").exists():
        raise FileExistsError("robust audit protocol already frozen")
    record = {"protocol": PROTOCOL, "protocol_sha256": sha(canonical(PROTOCOL)), "frozen_at_utc": now(),
              "dependency_sha256": dependencies(),
              "checkpoint_sha256": {str(s): sha(checkpoint(s).read_bytes()) for s in CONSTRUCTION_SEEDS + (HELDOUT_SEED,)},
              "observations_before_freeze": False}
    write_json(output / "protocol.json", record)
    return record


def checked(output):
    record = json.loads((output / "protocol.json").read_text())
    if record["protocol_sha256"] != sha(canonical(PROTOCOL)) or record["dependency_sha256"] != dependencies():
        raise ValueError("protocol or dependency changed after freeze")
    for seed, digest in record["checkpoint_sha256"].items():
        if sha(checkpoint(int(seed)).read_bytes()) != digest:
            raise ValueError("checkpoint changed after freeze")
    return record


def setup():
    import torch
    torch.use_deterministic_algorithms(True)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    torch.set_num_threads(2)


def coverage_table(tables):
    from singularity.robust_coverage import coverage_problem
    labels = [f"seed_{seed}/{fault}" for seed in CONSTRUCTION_SEEDS for fault in CONSTRUCTION_FAULTS]
    rows = [[tables[seed]["flags"][fault][e] for seed in CONSTRUCTION_SEEDS for fault in CONSTRUCTION_FAULTS]
            for e in range(len(PROBES))]
    return coverage_problem([p["cost"] for p in PROBES], rows, [p["id"] for p in PROBES], labels), rows, labels


def independent_minimum(rows, costs):
    """Direct 2**20 subset scan with bit masks, separate from the solver."""
    width = len(rows[0])
    masks = [[sum(1 << e for e in range(len(rows)) if rows[e][p])] for p in range(width)]
    best, minimizers = None, []
    for subset in range(1 << len(rows)):
        if all(bin(subset & mask[0]).count("1") >= REQUIREMENT for mask in masks):
            cost = sum(costs[e] for e in range(len(rows)) if subset >> e & 1)
            if best is None or cost < best:
                best, minimizers = cost, [subset]
            elif cost == best:
                minimizers.append(subset)
    return best, [[e for e in range(len(rows)) if subset >> e & 1] for subset in minimizers]


def construct(output):
    from singularity.robust_coverage import fixed_panel, greedy_robust_panel, minimum_robust_panel
    setup()
    checked(output)
    if (output / "construction.json").exists():
        raise FileExistsError("construction already run")
    started = time.perf_counter()
    tables = {seed: seed_table(seed, CONSTRUCTION_FAULTS) for seed in CONSTRUCTION_SEEDS}
    observed_seconds = time.perf_counter() - started
    problem, rows, labels = coverage_table(tables)
    t0 = time.perf_counter()
    exact = minimum_robust_panel(problem, REQUIREMENT)
    solver_seconds = time.perf_counter() - t0
    if not exact.feasible:
        raise RuntimeError("no 2-robust panel exists for the declared pool")
    greedy = greedy_robust_panel(problem, REQUIREMENT)
    t0 = time.perf_counter()
    oracle_cost, oracle_panels = independent_minimum(rows, [p["cost"] for p in PROBES])
    oracle_seconds = time.perf_counter() - t0
    if oracle_cost != exact.cost:
        raise ArithmeticError("exact solver disagrees with independent enumeration")
    ids = [p["id"] for p in PROBES]
    panels = {"exact": list(exact.panel), "greedy": list(greedy.panel),
              "fixed_typical": [ids.index(i) for i in ("full_history", "full_season", "full_album", "full_species")],
              "fixed_all_short": [e for e, p in enumerate(PROBES) if p["cost"] <= 32]}
    comparators = {name: {**fixed_panel(problem, panel, REQUIREMENT), "probe_ids": [ids[e] for e in panel]}
                   for name, panel in panels.items()}
    rng, randoms = random.Random(51713), []
    for _ in range(1000):
        order, chosen, spent = list(range(len(PROBES))), [], 0
        rng.shuffle(order)
        for e in order:
            if spent + PROBES[e]["cost"] <= exact.cost:
                chosen.append(e)
                spent += PROBES[e]["cost"]
        randoms.append(fixed_panel(problem, chosen, REQUIREMENT))
    for report in list(comparators.values()) + randoms:
        report["cost"] = int(report["cost"])
    result = {"schema": "singularity.robust-audit-construction/1", "protocol_sha256": checked(output)["protocol_sha256"],
              "distinctions": labels, "separation_table": {ids[e]: rows[e] for e in range(len(PROBES))},
              "separators_per_distinction": {labels[p]: len(cover) for p, cover in enumerate(problem.coverers)},
              "tolerances": {str(s): tables[s]["tolerances"] for s in CONSTRUCTION_SEEDS},
              "calibration_clean_maxima": {str(s): tables[s]["clean_maxima"] for s in CONSTRUCTION_SEEDS},
              "exact": {"probe_ids": [ids[e] for e in exact.panel], "cost": int(exact.cost), "nodes": exact.nodes,
                        "root_lower_bound": str(exact.root_lower_bound)},
              "independent_enumeration": {"subsets": 1 << len(PROBES), "minimum_cost": oracle_cost,
                                          "minimizing_panels": [[ids[e] for e in p] for p in oracle_panels],
                                          "seconds": oracle_seconds},
              "comparators": comparators,
              "random_at_exact_budget": {"draws": len(randoms), "satisfying_requirement": sum(r["satisfies_requirement"] for r in randoms),
                                         "detecting_all": sum(r["distinctions_detected"] == len(labels) for r in randoms),
                                         "mean_distinctions_meeting_requirement": statistics.fmean(r["distinctions_meeting_requirement"] for r in randoms),
                                         "mean_cost": statistics.fmean(r["cost"] for r in randoms)},
              "full_pool_cost": sum(p["cost"] for p in PROBES),
              "contract": tables[CONSTRUCTION_SEEDS[0]]["contract"],
              "cost_seconds": {"observation": observed_seconds, "exact_solver": solver_seconds, "independent_enumeration": oracle_seconds,
                               "total": time.perf_counter() - started}}
    write_json(output / "construction.json", result)
    write_json(output / "frozen_panels.json", {"construction_sha256": sha((output / "construction.json").read_bytes()),
                                               "panels": {name: c["probe_ids"] for name, c in comparators.items()},
                                               "frozen_before_audit": True})
    return result


def audit(output):
    from singularity.model_audit import build_package, check_package, deviation, flags, save_package, verify_package
    setup()
    checked(output)
    if (output / "audit.json").exists():
        raise FileExistsError("audit already run")
    started = time.perf_counter()
    frozen = json.loads((output / "frozen_panels.json").read_text())
    if frozen["construction_sha256"] != sha((output / "construction.json").read_bytes()):
        raise ValueError("construction changed after panels were frozen")
    ids = [p["id"] for p in PROBES]
    everything = {**CONSTRUCTION_FAULTS, **HELDOUT_FAULTS}
    spec = PROTOCOL["tolerance"]
    seeds = {}
    for seed in CONSTRUCTION_SEEDS + (HELDOUT_SEED,):
        faults = everything if seed == HELDOUT_SEED else HELDOUT_FAULTS
        table = seed_table(seed, faults)
        alarms = {}
        for name, change in FALSE_ALARM_CLEAN.items():
            rows = observe(table["model"], table["contract"], change)
            alarms[name] = [flags(deviation(o, r, spec["tie_margin"]), t)
                            for o, r, t in zip(rows, table["reference"], table["tolerances"])]
        seeds[seed] = {**table, "alarms": alarms}
    panels = {}
    for name, probe_ids in frozen["panels"].items():
        members = [ids.index(i) for i in probe_ids]
        per_seed = {}
        for seed, table in seeds.items():
            per_seed[str(seed)] = {
                "faults": {fault: {"separating_probes": sum(table["flags"][fault][e] for e in members),
                                   "detected": any(table["flags"][fault][e] for e in members),
                                   "robust": sum(table["flags"][fault][e] for e in members) >= REQUIREMENT,
                                   "heldout": fault in HELDOUT_FAULTS}
                           for fault in table["flags"]},
                "false_alarms": {clean: [ids[e] for e in members if table["alarms"][clean][e]] for clean in FALSE_ALARM_CLEAN}}
        panels[name] = {"probe_ids": probe_ids, "cost": sum(PROBES[e]["cost"] for e in members), "per_seed": per_seed}
    full = {str(seed): {"faults_detected_by_some_probe": {f: any(v) for f, v in t["flags"].items()},
                        "separators_in_pool": {f: sum(v) for f, v in t["flags"].items()},
                        "false_alarm_probes": {c: [ids[e] for e, v in enumerate(a) if v] for c, a in t["alarms"].items()}}
            for seed, t in seeds.items()}
    # Standalone package for the excluded checkpoint: frozen exact panel; its
    # evidence uses only construction faults observed on seed 1002.
    heldout = seeds[HELDOUT_SEED]
    package = build_package(PROBES, heldout["reference"], heldout["calibration"],
                            {f: heldout["observations"][f] for f in CONSTRUCTION_FAULTS}, contract=heldout["contract"],
                            requirement=REQUIREMENT, tolerance_factor=spec["factor"], tolerance_floor=spec["floor"],
                            tie_margin=spec["tie_margin"], panel_ids=frozen["panels"]["exact"],
                            metadata={"checkpoint": str(checkpoint(HELDOUT_SEED).relative_to(ROOT)),
                                      "checkpoint_sha256": sha(checkpoint(HELDOUT_SEED).read_bytes()),
                                      "panel_selected_on": [str(s) for s in CONSTRUCTION_SEEDS],
                                      "protocol_sha256": checked(output)["protocol_sha256"]})
    package_sha = save_package(package, output / "seed_1002_package.json")
    verification = verify_package(package)
    index = {p["id"]: e for e, p in enumerate(PROBES)}
    checks = {}
    for name in list(everything) + list(FALSE_ALARM_CLEAN):
        change = everything.get(name, FALSE_ALARM_CLEAN.get(name))
        report = check_package(package, lambda probes, c=change: observe(heldout["model"], heldout["contract"], c,
                                                                        [PROBES[index[p["id"]]] for p in probes]),
                               heldout["contract"])
        checks[name] = {"verdict": report["verdict"], "flagged_probes": report["flagged_probes"],
                        "contract_mismatches": len(report["contract_mismatches"])}
    result = {"schema": "singularity.robust-audit-results/1", "protocol_sha256": checked(output)["protocol_sha256"],
              "frozen_panels_sha256": sha((output / "frozen_panels.json").read_bytes()), "panels_selected_using_audit": False,
              "panels": panels, "full_pool": full,
              "heldout_tolerances": heldout["tolerances"],
              "seed_1002_package": {"file": "seed_1002_package.json", "sha256": package_sha,
                                    "verification": verification, "coverage": package["coverage"],
                                    "deficient_faults": package["deficient_faults"], "checks": checks},
              "audit_seconds": time.perf_counter() - started, "created_at_utc": now()}
    write_json(output / "audit.json", result)
    return result


def timing(output):
    import torch
    from singularity.model_audit import check_package, load_package
    from singularity.model_audit.adapters import ByteTransformerAdapter
    setup()
    checked(output)
    package = load_package(output / "seed_1002_package.json")
    model = load(HELDOUT_SEED)
    adapter = ByteTransformerAdapter(model)
    contract = adapter.contract()
    spec = PROTOCOL["timing"]

    def full_check():
        return adapter.observe(PROBES)

    def panel_check():
        return check_package(package, adapter.observe, contract)

    for _ in range(spec["warmup_pairs"]):
        full_check()
        panel_check()
    rng, records = random.Random(spec["order_seed"]), []
    for repeat in range(spec["measured_pairs"]):
        order = ["full_pool_observation", "panel_check"]
        rng.shuffle(order)
        record = {"repeat": repeat, "order": order}
        for label in order:
            t0 = time.perf_counter()
            (full_check if label == "full_pool_observation" else panel_check)()
            record[label] = time.perf_counter() - t0
        records.append(record)
    summary = {label: {"median_seconds": statistics.median(r[label] for r in records),
                       "p90_seconds": sorted(r[label] for r in records)[math.ceil(.9 * len(records)) - 1]}
               for label in ("full_pool_observation", "panel_check")}
    cold = []
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "OMP_NUM_THREADS": "2"}
    for _ in range(spec["cold_cli_repeats"]):
        t0 = time.perf_counter()
        completed = subprocess.run([sys.executable, "-m", "singularity.model_audit", "check",
                                    str(output / "seed_1002_package.json"), "--byte-checkpoint", str(checkpoint(HELDOUT_SEED))],
                                   env=environment, capture_output=True, text=True)
        wall = time.perf_counter() - t0
        report = json.loads(completed.stdout)
        cold.append({"process_wall_seconds": wall, "exit_code": completed.returncode, "verdict": report["verdict"],
                     "internal_seconds": report["seconds"]})
    construction = json.loads((output / "construction.json").read_text())
    audit_record = json.loads((output / "audit.json").read_text())
    saved = summary["full_pool_observation"]["median_seconds"] - summary["panel_check"]["median_seconds"]
    development = construction["cost_seconds"]["total"] + audit_record["audit_seconds"]
    result = {"schema": "singularity.robust-audit-timing/1", "records": records, "summary": summary,
              "speed_ratio_full_over_panel": summary["full_pool_observation"]["median_seconds"] / summary["panel_check"]["median_seconds"],
              "token_ratio_full_over_panel": construction["full_pool_cost"] / construction["exact"]["cost"],
              "cold_cli": cold, "cold_cli_median_seconds": statistics.median(c["process_wall_seconds"] for c in cold),
              "construction_seconds": construction["cost_seconds"]["total"], "audit_seconds": audit_record["audit_seconds"],
              "break_even_checks_construction_only": math.ceil(construction["cost_seconds"]["total"] / saved) if saved > 0 else None,
              "break_even_checks_construction_plus_audit": math.ceil(development / saved) if saved > 0 else None,
              "conditions": {"threads": torch.get_num_threads(), "device": "cpu", "torch": torch.__version__,
                             "panel_check_includes": "package verification, observation and comparison",
                             "full_pool_observation_includes": "observation of all 20 probes only (no comparison)"},
              "created_at_utc": now()}
    write_json(output / "timing.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "construct", "audit", "timing"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = {"freeze": freeze, "construct": construct, "audit": audit, "timing": timing}[args.phase](args.output)
    print(json.dumps(result, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
