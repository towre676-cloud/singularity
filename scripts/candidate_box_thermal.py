#!/usr/bin/env python3
"""NX01-C: candidate-specific box panels on the unchanged thermal pool.

Compiles the original 112-protocol pool and six source-derived candidates with
the primary retained contract (initial radius 1/100, sensor noise 1/100), keeps
each candidate's own radius instead of the common envelope, and solves the
exact heterogeneous panel problem.  Readings are replayed by the separately
written neighbor-flux oracle in scripts/thermal_diagnostics.py; radii are
checked against the closed form nu + rho0 (1 - lambda_c)^T, which holds for
this positive plate family with normalized nonnegative sensors.  The optimum
is checked by a cover-state Dijkstra search and a cost-bounded exhaustive
box-intersection scan, neither of which uses production masks.

``--check`` compares with results/candidate_box_thermal.json and never
rewrites it.  The older common-envelope receipt is read, not regenerated.
Timings are printed, never retained.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

OUTPUT = ROOT / "results" / "candidate_box_thermal.json"
HORIZONS = (1, 2, 3, 4, 6, 8, 12, 20)
PRIMARY = (Fraction(1, 100), Fraction(1, 100))
GRID_RADII = (Fraction(0), Fraction(1, 10000), Fraction(1, 1000), Fraction(1, 100))
GRID_NOISE = (Fraction(0), Fraction(1, 1000), Fraction(1, 100))


def _load_thermal_script():
    spec = importlib.util.spec_from_file_location("_thermal_receipt", ROOT / "scripts" / "thermal_diagnostics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def q(x):
    x = Fraction(x)
    return [x.numerator, x.denominator]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare with the retained result")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    started = time.perf_counter()

    thermal_script = _load_thermal_script()
    source = thermal_script.verify_source_fixture()
    from singularity.thermal_diagnostics import (build_plate_candidates, default_protocols,
                                                 protocol_pool, SENSOR_LABELS, CANDIDATE_IDS)
    from singularity.panels import minimum_cost_panel, separates_all
    from singularity.candidate_boxes import (
        from_diagnostic_pool, common_envelope, candidate_box_masks, required_pairs,
        minimum_candidate_box_panel, candidate_box_separates, candidate_box_consistent,
        candidate_box_ambiguity, candidate_box_receipt, CandidateBoxPool)
    from singularity.candidate_box_oracles import cover_state_dijkstra, cost_bounded_box_panel

    candidates = build_plate_candidates(12)
    assert tuple(c.identifier for c in candidates) == CANDIDATE_IDS
    protocols = default_protocols(HORIZONS)
    rho0, nu = PRIMARY
    diagnostic = protocol_pool(candidates, protocols, initial_radius=rho0, sensor_noise=nu)
    pool = diagnostic.pool
    assert pool.size == 112 and pool.candidates == 6
    boxes = from_diagnostic_pool(diagnostic)
    assert boxes.radii == diagnostic.error_bounds and boxes.pool.readings == pool.readings

    # 1. Readings: every one of the 672 against the independent neighbor-flux oracle.
    states = {}
    for e, (word, sensor) in enumerate(protocols):
        for c, cand in enumerate(candidates):
            key = cand.identifier, word
            if key not in states:
                states[key] = thermal_script.stencil_state(12, cand.identifier, word)
            reading = sum((a * b for a, b in zip(cand.sensors[sensor], states[key])), Fraction(0))
            assert reading == pool.readings[e][c]
    readings_checked = pool.size * pool.candidates

    # 2. Radii: closed form nu + rho0 * (1 - lambda_c)^T, independent of |A| propagation.
    decay = {cid: 1 - (Fraction(1, 50) if cid == "loss_double" else Fraction(1, 100)) for cid in CANDIDATE_IDS}
    for e, (word, _) in enumerate(protocols):
        for c, cid in enumerate(CANDIDATE_IDS):
            assert boxes.radii[e][c] == nu + rho0 * decay[cid] ** len(word)
    radii_checked = readings_checked

    # 3. Agreement with the retained common-envelope receipt (read, not regenerated).
    old = json.loads((ROOT / "results" / "thermal_diagnostics.json").read_text())
    assert old["candidates"] == list(CANDIDATE_IDS) and old["experiments"] == pool.size
    assert old["assumptions"]["independent_initial_radius"] == "1/100"
    assert old["assumptions"]["sensor_noise"] == "1/100"
    assert Fraction(old["all_experiments_cost"]) == sum(pool.costs, Fraction(0))
    retained_rows = 0
    for name in ("exact_panel", "robust_panel", "greedy_robust_panel"):
        for e, item in zip(old[name]["indices"], old[name]["experiments"]):
            assert [str(x) for x in pool.readings[e]] == item["readings"]
            assert str(max(boxes.radii[e])) == item["error_radius"]
            assert str(pool.costs[e]) == item["cost"]
            retained_rows += 1
    assert tuple(max(row) for row in boxes.radii) == diagnostic.epsilon

    # 4. Common-envelope incumbent from the existing backend.
    common = minimum_cost_panel(pool, diagnostic.panel_epsilon)
    assert common.feasible and common.cost == Fraction(old["robust_panel"]["cost"])
    assert list(common.panel) == old["robust_panel"]["indices"]
    assert separates_all(pool, common.panel, diagnostic.epsilon)
    assert candidate_box_separates(boxes, common.panel)

    # 5. Heterogeneous optimum and independent oracles.
    hetero = minimum_candidate_box_panel(boxes)
    assert hetero.status == "optimal" and hetero.cost <= common.cost
    raw = (pool.costs, pool.readings, boxes.radii, boxes.target_labels)
    dijkstra = cover_state_dijkstra(*raw)
    assert dijkstra[0] == hetero.cost
    bounded = cost_bounded_box_panel(*raw, common.cost)
    assert bounded[0] and bounded[1] == hetero.cost
    envelope_boxes = common_envelope(boxes)
    envelope_result = minimum_candidate_box_panel(envelope_boxes)
    assert envelope_result.cost == common.cost

    # 6. Mask comparison: gains can only involve candidates with below-maximum radius.
    pairs = required_pairs(boxes)
    hm, em = candidate_box_masks(boxes), candidate_box_masks(envelope_boxes)
    gained = []
    for e, (h, m) in enumerate(zip(hm, em)):
        assert h & m == m
        for p, pair in enumerate(pairs):
            if (h & ~m) >> p & 1:
                gained.append((e, pair))
    assert all(3 in pair for _, pair in gained)

    # 7. Decoding at every corner of every candidate box, and an ambiguity witness.
    decoded = []
    for c in range(6):
        for signs in range(2 ** len(hetero.panel)):
            y = [pool.readings[e][c] + (1 if signs >> j & 1 else -1) * boxes.radii[e][c]
                 for j, e in enumerate(hetero.panel)]
            assert candidate_box_consistent(boxes, hetero.panel, y) == (c,)
        decoded.append(c)
    exact_index = old["exact_panel"]["indices"]
    witness = candidate_box_ambiguity(boxes, exact_index)
    assert witness is not None
    assert {witness.a, witness.b} <= set(candidate_box_consistent(boxes, exact_index, witness.observed))

    # 8. Uncertainty grid of the original receipt: heterogeneous versus common.
    grid = []
    for radius in GRID_RADII:
        base = protocol_pool(candidates, protocols, initial_radius=radius, sensor_noise=0)
        assert base.pool.readings == pool.readings
        for noise in GRID_NOISE:
            # rho = |C| b + nu exactly; sensor noise enters additively.
            radii = tuple(tuple(x + noise for x in row) for row in base.error_bounds)
            if (radius, noise) == PRIMARY:
                assert radii == boxes.radii
            gpool = CandidateBoxPool(base.pool, radii, None, base.candidate_ids)
            h = minimum_candidate_box_panel(gpool)
            env = minimum_candidate_box_panel(common_envelope(gpool))
            d = cover_state_dijkstra(base.pool.costs, base.pool.readings, radii, gpool.target_labels)
            assert d[0] == h.cost and h.cost <= env.cost
            hb = sum(bin(m).count("1") for m in candidate_box_masks(gpool))
            eb = sum(bin(m).count("1") for m in candidate_box_masks(common_envelope(gpool)))
            grid.append({"initial_radius": q(radius), "sensor_noise": q(noise),
                         "heterogeneous_cost": q(h.cost), "heterogeneous_indices": list(h.panel),
                         "common_envelope_cost": q(env.cost), "common_envelope_indices": list(env.panel),
                         "dijkstra_cost": q(d[0]), "heterogeneous_mask_bits": hb,
                         "common_envelope_mask_bits": eb})

    # 9. Small-plate contrast: a declared 4x4 sub-pool where the refinement matters.
    from singularity.candidate_box_oracles import exhaustive_box_panel
    small = build_plate_candidates(4)
    small_protocols = default_protocols((1, 2, 3, 4, 6, 8))[1::5][:12]
    s_rho0, s_nu = Fraction(1, 100), Fraction(1, 1000)
    sdiag = protocol_pool(small, small_protocols, initial_radius=s_rho0, sensor_noise=s_nu)
    sboxes = from_diagnostic_pool(sdiag)
    for e, (word, sensor) in enumerate(small_protocols):
        for c, cand in enumerate(small):
            state = thermal_script.stencil_state(4, cand.identifier, word)
            assert sum((a * b for a, b in zip(cand.sensors[sensor], state)), Fraction(0)) == sdiag.pool.readings[e][c]
            assert sboxes.radii[e][c] == s_nu + s_rho0 * decay[cand.identifier] ** len(word)
    s_common = minimum_cost_panel(sdiag.pool, sdiag.panel_epsilon)
    s_hetero = minimum_candidate_box_panel(sboxes)
    s_raw = (sdiag.pool.costs, sdiag.pool.readings, sboxes.radii, sboxes.target_labels)
    s_exhaustive = exhaustive_box_panel(*s_raw, max_subsets=2**12)
    s_env_exhaustive = exhaustive_box_panel(sdiag.pool.costs, sdiag.pool.readings,
                                            common_envelope(sboxes).radii, sboxes.target_labels,
                                            max_subsets=2**12)
    s_dijkstra = cover_state_dijkstra(*s_raw)
    assert not s_common.feasible and not s_env_exhaustive[0]
    assert s_hetero.status == "optimal" and s_exhaustive[1] == s_dijkstra[0] == s_hetero.cost
    pair_index = required_pairs(sboxes).index((0, 3))
    small_contrast = {
        "grid": 4, "protocols": [{"word": list(w), "sensor": SENSOR_LABELS[j]} for w, j in small_protocols],
        "protocol_selection": "default_protocols((1, 2, 3, 4, 6, 8))[1::5][:12]",
        "initial_radius": q(s_rho0), "sensor_noise": q(s_nu),
        "common_envelope": {"feasible": False, "uncoverable": [list(p) for p in s_common.uncoverable],
                            "exhaustive_oracle_feasible": False},
        "heterogeneous": {"status": s_hetero.status, "cost": q(s_hetero.cost),
                          "indices": list(s_hetero.panel), "exhaustive_cost": q(s_exhaustive[1]),
                          "exhaustive_subsets": s_exhaustive[3], "dijkstra_cost": q(s_dijkstra[0])},
        "pair_nominal_loss_double_margins": [
            {"index": e, "heterogeneous": q(abs(sdiag.pool.readings[e][0] - sdiag.pool.readings[e][3])
                                             - sboxes.radii[e][0] - sboxes.radii[e][3]),
             "common_envelope": q(abs(sdiag.pool.readings[e][0] - sdiag.pool.readings[e][3])
                                  - 2 * sdiag.epsilon[e])}
            for e in range(sdiag.pool.size) if candidate_box_masks(sboxes)[e] >> pair_index & 1],
        "scope": "declared 12-protocol sub-pool of a 4x4 plate; finite exact example, not a property of the 12x12 pool",
    }

    # 10. Arithmetic size growth.
    bits = []
    for horizon in HORIZONS:
        rows = [e for e, (w, _) in enumerate(protocols) if len(w) == horizon]
        values = [x for e in rows for x in pool.readings[e] + boxes.radii[e]]
        bits.append({"horizon": horizon,
                     "max_numerator_bits": max(abs(x.numerator).bit_length() for x in values),
                     "max_denominator_bits": max(x.denominator.bit_length() for x in values)})

    labels = [{"word": list(w), "sensor": SENSOR_LABELS[s]} for w, s in protocols]
    receipt = candidate_box_receipt(boxes, hetero, oracle_cost=dijkstra[0], protocol_labels=labels)
    record = {
        **receipt,
        "track": "NX01-C",
        "source_commit": source["source"]["commit"],
        "source_model_sha256": source["model_sha256"],
        "grid": 12, "horizons": list(HORIZONS),
        "contract": {"initial_center": q(0), "initial_radius": q(rho0), "process_radius": q(0),
                     "sensor_noise": q(nu), "reduction_error": q(0),
                     "scope": "synthetic exact discrete source with supplied faults and model-unit costs; "
                              "no measured fault data or physical calibration"},
        "solver_budget": {"max_nodes": 10**6, "cost_bounded_max_subsets": 10**6},
        "common_envelope": {"cost": q(common.cost), "indices": list(common.panel),
                            "valid_heterogeneous_incumbent": True,
                            "retained_receipt": "results/thermal_diagnostics.json"},
        "comparison": "unchanged" if hetero.cost == common.cost else "improved",
        "independent_checks": {
            "neighbor_flux_readings": readings_checked,
            "closed_form_radii": radii_checked,
            "retained_receipt_rows": retained_rows,
            "dijkstra_cost": q(dijkstra[0]), "dijkstra_settled_states": dijkstra[2],
            "cost_bounded_exhaustive": {"bound": q(common.cost), "cost": q(bounded[1]),
                                        "indices": list(bounded[2]), "subsets_scanned": bounded[3]},
        },
        "mask_gain": {"gained_experiment_pairs": [[e, list(p)] for e, p in gained],
                      "heterogeneous_bits": sum(bin(m).count("1") for m in hm),
                      "common_envelope_bits": sum(bin(m).count("1") for m in em)},
        "decoded_corner_candidates": decoded,
        "exact_panel_ambiguity": {"indices": exact_index, "pair": [witness.a, witness.b],
                                  "observed": [q(y) for y in witness.observed]},
        "uncertainty_grid": grid,
        "small_plate_contrast": small_contrast,
        "arithmetic_bits": bits,
    }
    if args.check:
        if not args.output.is_file() or json.loads(args.output.read_text()) != json.loads(json.dumps(record)):
            raise SystemExit("Retained candidate-box evidence differs; review before replacing it")
        print("Candidate-box thermal panel: readings, radii, incumbent, optimum and oracles agree.")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(record, indent=1) + "\n")
        print(f"wrote {args.output.relative_to(ROOT)}")
    print(json.dumps({"heterogeneous_cost": str(hetero.cost), "common_envelope_cost": str(common.cost),
                      "comparison": record["comparison"], "gained_bits": len(gained),
                      "seconds": round(time.perf_counter() - started, 2)}))


if __name__ == "__main__":
    main()
