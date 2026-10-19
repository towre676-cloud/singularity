#!/usr/bin/env python3
"""Stronger post-hoc baseline: optimal pruning of each greedy output.

Enumerate every subset of the already retained greedy panel. This is at
least as strong as deleting redundant probes in any order. No model runs,
probe changes, fault changes or cost changes are involved.
"""
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from singularity.model_audit import deviation, flags


def compare():
    rows = {}
    for path in sorted((ROOT / "applications/training_lab/results/pretrained_audit").glob("*/results.json")):
        result = json.loads(path.read_text())
        observations = json.loads((path.parent / "observations.json").read_text())
        protocol = json.loads((path.parent / "protocol.json").read_text())
        greedy = result["selection"]["greedy"]["indices"]
        eligible = result["selection"]["eligible_faults"]
        tie = protocol["protocol"]["tolerance"]["tie_margin"]
        separates = {f: [flags(deviation(o, r, tie), t) for o, r, t in
                         zip(observations["construction"][f], observations["reference"], observations["tolerances"])]
                     for f in eligible}
        best, panels = float("inf"), []
        for count in range(len(greedy)+1):
            for panel in itertools.combinations(greedy, count):
                if all(sum(separates[f][i] for i in panel) >= 2 for f in eligible):
                    cost = sum(protocol["probes"][i]["cost"] for i in panel)
                    if cost < best:
                        best, panels = cost, [list(panel)]
                    elif cost == best:
                        panels.append(list(panel))
        exact = result["selection"]["exact"]["cost"]
        assert exact <= best <= result["selection"]["greedy"]["cost"]
        rows[path.parent.name] = {"model_id": result["model_id"], "original_greedy_cost": result["selection"]["greedy"]["cost"],
                                 "optimally_pruned_greedy_cost": best, "exact_cost": exact,
                                 "exact_reduction_vs_pruned_greedy_percent": 100*(1-exact/best),
                                 "pruning_subsets_checked": 2**len(greedy), "best_pruned_panels": panels,
                                 "source_results_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    assert len(rows) == 3
    return {"analysis_status": "POSTHOC deterministic stronger baseline on unchanged construction tables",
            "method": "Exhaustively optimize every subset of the original greedy output; at least as strong as any deletion-only cleanup",
            "new_model_forward_calls": 0, "models": rows}


if __name__ == "__main__":
    result = compare()
    path = ROOT / "applications/training_lab/results/pretrained_pruned_greedy.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result))
