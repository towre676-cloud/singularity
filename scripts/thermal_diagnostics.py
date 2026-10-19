#!/usr/bin/env python3
"""Replay the offline, source-pinned synthetic thermal diagnosis experiment."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import heapq
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _json(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json(v) for v in value]
    return value


def verify_source_fixture():
    """Check the imported source against a separately generated edge stencil."""
    base = ROOT / "applications" / "thermal_diagnostics"
    source = json.loads((base / "source_fixture.json").read_text())
    assert hashlib.sha256((base / "dynacomp_plate_source.py.txt").read_bytes()).hexdigest() == source["source"]["function_sha256"]
    model = source["model"]
    canonical = json.dumps(model, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == source["model_sha256"]
    n, k, loss = 12, Fraction(1, 8), Fraction(1, 100)
    # Build by undirected edge contributions, independently of DynaComp's
    # per-row construction and the diagnostic implementation.
    entries = {(i, i): 1 - loss for i in range(n * n)}
    for r in range(n):
        for c in range(n):
            i = r * n + c
            for rr, cc in ((r + 1, c), (r, c + 1)):
                if rr < n and cc < n:
                    j = rr * n + cc
                    entries[i, i] -= k
                    entries[j, j] -= k
                    entries[i, j] = k
                    entries[j, i] = k
    assert tuple((i, j, v) for (i, j), v in sorted(entries.items()) if v) == tuple((i, j, Fraction(v)) for i, j, v in model["entries"])
    middle, corners = {5, 6}, {0, 11}
    assert [row[0] for row in model["B"]] == [str(Fraction(int(i // n in middle and i % n in middle), 4)) for i in range(n * n)]
    assert model["C"][0] == [str(Fraction(int(i // n in corners and i % n in corners), 4)) for i in range(n * n)]
    return source


def stencil_state(grid, identifier, word, initial=None):
    """Direct neighbor-flux evolution; never reads compiled matrix entries."""
    k = Fraction(1, 16) if identifier == "conductance_half" else Fraction(1, 8)
    loss = Fraction(1, 50) if identifier == "loss_double" else Fraction(1, 100)
    gain = Fraction(1, 2) if identifier == "heater_half" else Fraction(1)
    middle = {grid // 2 - 1, grid // 2}
    left = ((grid // 2 - 1) * grid + grid // 2 - 2,
            (grid // 2 - 1) * grid + grid // 2 - 1)
    right = ((grid // 2 - 1) * grid + grid // 2,
             (grid // 2 - 1) * grid + grid // 2 + 1)
    blocked = frozenset(left if identifier == "blocked_left_center_bond" else
                        right if identifier == "blocked_right_center_bond" else ())
    x = [Fraction(v) for v in initial] if initial is not None else [Fraction(0)] * (grid * grid)
    for u in word:
        following = []
        for r in range(grid):
            for c in range(grid):
                i = r * grid + c
                value = (1 - loss) * x[i]
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= rr < grid and 0 <= cc < grid:
                        j = rr * grid + cc
                        if frozenset((i, j)) != blocked:
                            value += k * (x[j] - x[i])
                if r in middle and c in middle:
                    value += Fraction(u) * gain / 4
                following.append(value)
        x = following
    return tuple(x)


def stencil_oracle(grid, identifier, word, sensor, initial=None):
    return sum((Fraction(c) * v for c, v in zip(sensor, stencil_state(grid, identifier, word, initial))), Fraction(0))


def verify_dynacomp_checkout(path, source):
    """Optional direct comparison with the independently installed pinned source."""
    path = Path(path).resolve()
    raw = (path / source["source"]["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != source["source"]["module_sha256"]:
        raise ValueError("DynaComp thermal source does not match the pinned module")
    sys.path.insert(0, str(path / "src"))
    from dynacomp.thermal import plate_model
    assert plate_model(12).spec() == source["model"]


def independent_cover_oracle(pool, epsilon=None):
    """Dijkstra on all reached pair-cover subsets, without solver pruning.

    Cover masks are recomputed directly from the reading intervals.  This
    oracle does not call the production coverage, dominance or lower-bound
    routines.  Repeating an experiment cannot enlarge its mask, so paths
    in this finite graph have the same optimal cost as subsets of the pool.
    """
    pairs = tuple((a, b) for a in range(pool.candidates) for b in range(a + 1, pool.candidates))
    errors = (Fraction(0),) * pool.size if epsilon is None else epsilon
    masks = []
    for reading, radius in zip(pool.readings, errors):
        mask = 0
        for bit, (a, b) in enumerate(pairs):
            if abs(reading[a] - reading[b]) > 2 * radius:
                mask |= 1 << bit
        masks.append(mask)
    full = (1 << len(pairs)) - 1
    distances = {0: Fraction(0)}
    queue = [(Fraction(0), 0)]
    settled = 0
    while queue:
        cost, covered = heapq.heappop(queue)
        if distances[covered] != cost:
            continue
        settled += 1
        if covered == full:
            return cost, settled
        for price, mask in zip(pool.costs, masks):
            following = covered | mask
            candidate = cost + price
            if following != covered and (following not in distances or candidate < distances[following]):
                distances[following] = candidate
                heapq.heappush(queue, (candidate, following))
    return None, settled


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare all deterministic retained evidence")
    parser.add_argument("--dynacomp-source", "--dynacomp-root", type=Path, help="also compare an existing pinned DynaComp checkout")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "thermal_diagnostics.json")
    args = parser.parse_args()
    source = verify_source_fixture()
    if args.dynacomp_source:
        verify_dynacomp_checkout(args.dynacomp_source, source)
    # The core module is imported only after the source fixture has passed its
    # independent stencil check.
    from singularity.thermal_diagnostics import (build_plate_candidates,
        default_protocols, protocol_pool, simulate_protocol, SENSOR_LABELS)
    from singularity.panels import (reading_pool, minimum_cost_panel, greedy_panel,
        separates_all, consistent_candidates, candidate_pairs)
    candidates = build_plate_candidates(12)
    nominal = candidates[0]
    assert nominal.entries == tuple((i, j, Fraction(v)) for i, j, v in source["model"]["entries"])
    assert nominal.heater == tuple(Fraction(row[0]) for row in source["model"]["B"])
    assert nominal.sensors[0] == tuple(Fraction(v) for v in source["model"]["C"][0])
    protocols = default_protocols((1, 2, 3, 4, 6, 8, 12, 20))
    diagnostic = protocol_pool(candidates, protocols, initial_radius=Fraction(1, 100),
                               sensor_noise=Fraction(1, 100))
    pool, epsilon = diagnostic.pool, diagnostic.epsilon
    exact = minimum_cost_panel(pool)
    robust = minimum_cost_panel(pool, epsilon)
    greedy = greedy_panel(pool, epsilon)
    assert exact.feasible and robust.feasible and greedy.feasible
    assert separates_all(pool, robust.panel, epsilon)
    exact_oracle = independent_cover_oracle(pool)
    robust_oracle = independent_cover_oracle(pool, epsilon)
    assert exact_oracle[0] == exact.cost and robust_oracle[0] == robust.cost
    original_indices = [i for i, (_, sensor) in enumerate(protocols) if sensor == 0]
    original = reading_pool([pool.costs[i] for i in original_indices],
                            [pool.readings[i] for i in original_indices],
                            [pool.labels[i] for i in original_indices])
    original_result = minimum_cost_panel(original)
    assert not original_result.feasible
    fixed_index = protocols.index(((2,) * 20, 2))
    fixed_feasible = separates_all(pool, (fixed_index,), epsilon)
    # Sensor noise enters each scalar envelope additively.  Reuse the
    # candidate simulations across the twelve declared uncertainty contracts.
    sensitivity = []
    for radius in (Fraction(0), Fraction(1, 10000), Fraction(1, 1000), Fraction(1, 100)):
        base = protocol_pool(candidates, protocols, initial_radius=radius, sensor_noise=0)
        thresholds = [max(abs(row[a] - row[b]) / 2 - error
                          for row, error in zip(base.pool.readings, base.epsilon))
                      for a, b in candidate_pairs(len(candidates))]
        frontier = min(thresholds)
        at_frontier = minimum_cost_panel(base.pool, tuple(e + frontier for e in base.epsilon))
        assert not at_frontier.feasible
        entries = []
        for noise in (Fraction(0), Fraction(1, 1000), Fraction(1, 100)):
            margins = tuple(e + noise for e in base.epsilon)
            accepted_margins = margins if any(margins) else None
            best = minimum_cost_panel(base.pool, accepted_margins)
            heuristic = greedy_panel(base.pool, accepted_margins)
            entries.append({"sensor_noise": noise, "feasible": best.feasible,
                            "optimal_cost": best.cost, "optimal_indices": best.panel,
                            "greedy_cost": heuristic.cost, "uncoverable": best.uncoverable})
        sensitivity.append({"initial_radius": radius, "contracts": entries,
                            "sensor_noise_frontier": frontier,
                            "frontier_is_excluded": True,
                            "uncoverable_at_frontier": at_frontier.uncoverable})
    # Check every retained reading with a second algorithm.  This oracle
    # recomputes complete words by per-cell neighbor flux, without the
    # diagnostic sparse operator or its prefix-state cache.
    chosen = tuple(sorted(set(exact.panel + robust.panel + greedy.panel + (fixed_index,))))
    checks = 0
    independent_states = {}
    for index, (word, sensor) in enumerate(protocols):
        for c, candidate in enumerate(candidates):
            key = candidate.identifier, word
            if key not in independent_states:
                independent_states[key] = stencil_state(12, candidate.identifier, word)
            reading = sum((a * b for a, b in zip(candidate.sensors[sensor], independent_states[key])), Fraction(0))
            assert reading == pool.readings[index][c]
            checks += 1
    for index in chosen:
        word, sensor = protocols[index]
        for c, candidate in enumerate(candidates):
            assert simulate_protocol(candidate, word, sensor) == pool.readings[index][c]
    # An actual bounded noisy reading at an alternating corner of the common
    # envelope must decode uniquely, for every candidate.
    decoded = []
    for c in range(len(candidates)):
        observed = [pool.readings[e][c] + (epsilon[e] if j % 2 == 0 else -epsilon[e])
                    for j, e in enumerate(robust.panel)]
        result = consistent_candidates(pool, robust.panel, observed, epsilon)
        assert tuple(result) == (c,)
        decoded.append(c)
    def panel_record(result):
        return {"cost": result.cost, "indices": result.panel, "nodes": result.nodes,
                "root_lower_bound": result.root_lower_bound,
                "experiments": [{"word": protocols[e][0], "sensor": SENSOR_LABELS[protocols[e][1]],
                                 "cost": pool.costs[e], "error_radius": epsilon[e],
                                 "readings": pool.readings[e]} for e in result.panel]}
    record = _json({"schema": "singularity.thermal-diagnostics/1",
        "source_commit": source["source"]["commit"], "source_model_sha256": source["model_sha256"],
        "grid": 12, "states_per_candidate": 144,
        "candidates": [c.identifier for c in candidates], "experiments": pool.size,
        "readings": pool.size * len(candidates), "horizons": [1, 2, 3, 4, 6, 8, 12, 20],
        "assumptions": {"initial_center": "0", "independent_initial_radius": "1/100",
                        "process_radius": "0", "sensor_noise": "1/100", "model_reduction_error": "0",
                        "scope": "synthetic exact discrete source with supplied faults and model-unit costs; no measured fault data or physical calibration"},
        "exact_panel": panel_record(exact), "robust_panel": panel_record(robust),
        "greedy_robust_panel": panel_record(greedy),
        "all_experiments_cost": sum(pool.costs, Fraction(0)),
        "fixed_twenty_step_left_sensor": {"index": fixed_index, "cost": pool.costs[fixed_index],
                                          "robustly_identifies_all": fixed_feasible},
        "independent_minimum_cover_oracle": {"exact_cost": exact_oracle[0],
            "exact_settled_masks": exact_oracle[1], "robust_cost": robust_oracle[0],
            "robust_settled_masks": robust_oracle[1]},
        "original_corner_only_uncoverable": original_result.uncoverable,
        "uncertainty_sensitivity": sensitivity,
        "independent_stencil_readings_checked": checks,
        "selected_public_simulator_readings_checked": len(chosen) * len(candidates),
        "bounded_noisy_candidates_decoded": decoded})
    serialized = json.dumps(record, indent=2) + "\n"
    if args.check:
        if json.loads(args.output.read_text()) != record:
            raise SystemExit("Retained thermal evidence differs; review before replacing it")
        print("Thermal diagnosis source, exact optimization, noisy decoding, and independent stencil replay passed.")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized)
        print(json.dumps({"experiments": pool.size, "candidates": len(candidates),
                          "exact_cost": str(exact.cost), "robust_cost": str(robust.cost),
                          "greedy_cost": str(greedy.cost)}))


if __name__ == "__main__":
    main()
