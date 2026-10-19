#!/usr/bin/env python3
"""NX16: incremental connected-support compilation -- verification, scaling and receipts.

Retained (deterministic) in results/incremental_locality.json:

* contract (NX16-A): the two-vertex example (logs, series, support
  contributions, values at q = 1/2, exact reversal);
* exhaustive (NX16-B): every edge insertion, deletion and weight change
  on all 3^6 weightings of K4 with weights in {0, 1, 2} at R = 3, each
  compared with full recompilation (identical state: log and support index)
  and every recompiled series with direct enumeration; pinning changes and
  reversal on all 64 unweighted 4-vertex graphs; a 14-batch random
  sequential run on 5 vertices with direct enumeration after every batch,
  replayed update records, and exact reversal;
* scaling (NX16-C): the ladder P_2 x P_m (maximum degree 3) for
  m = 16 ... 512 at R = 4 with four local edits in the middle column
  (rung reweight, rail deletion, diagonal insertion, pinning change).
  Setup, update (cold and warm cache), query (formal exponentiation),
  storage and coefficient-bit counts are reported separately; every
  updated log equals full recompilation and, for unit-weight uniform-pinning
  edits, the unweighted compiler locality.pinned_log;
* receipts: singularity.locality-update/1 records on a 6- and a
  10-vertex ladder, replayed by verify_local_update (union-graph
  completeness by brute force, contributions from their definition,
  direct enumeration where the box is small).

Wall-clock times are printed and never retained.
"""
import argparse
from fractions import Fraction
import itertools
import json
import platform
import random
import time
from pathlib import Path

from singularity.graph import Graph
from singularity.incremental_locality import (SCHEMA, WeightedSpec, apply_local_changes, coefficient_bits,
                                              compile_locality, direct_series, edge_change, pin_change,
                                              support_contribution_by_definition, verify_local_update)
from singularity.locality import pinned_log
from singularity.polynomials import evaluate, polynomial_to_json, sub

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "results/incremental_locality.json"
LADDERS = (16, 32, 64, 128, 256, 512)
SCALING_R = 4
TIMES: list = []
PAIRS4 = list(itertools.combinations(range(4), 2))


def timed(label, function, *args, **kwargs):
    start = time.perf_counter()
    value = function(*args, **kwargs)
    TIMES.append((label, time.perf_counter() - start))
    return value


def sj(series):
    return [polynomial_to_json(p) for p in series]


def contract():
    R = 2
    iso = compile_locality(WeightedSpec(2), R)
    edge, record = apply_local_changes(iso, [edge_change(0, 1, 0, 1)])
    back, _ = apply_local_changes(edge, [edge_change(0, 1, 1, 0)])
    assert back.state_signature() == iso.state_signature()
    verify_local_update(record, oracle_budget=100)
    half = lambda s: [[v.numerator, v.denominator] for v in (evaluate(p, Fraction(1, 2)) for p in s)]
    return {"R": R, "isolated_log": sj(iso.log), "isolated_series": sj(iso.series()),
            "edge_log": sj(edge.log), "edge_series": sj(edge.series()),
            "singleton_contribution": sj(support_contribution_by_definition(edge.spec, [0], R)),
            "pair_contribution": sj(support_contribution_by_definition(edge.spec, [0, 1], R)),
            "affected_supports": [row["support"] for row in record["supports"]],
            "delta_log_at_q_half": half([sub(x, y) for x, y in zip(edge.log, iso.log)]),
            "edge_series_at_q_half": half(edge.series()), "reversal_exact": True}


def spec4(ws, pins=None):
    return WeightedSpec(4, [(u, v, w) for (u, v), w in zip(PAIRS4, ws)], pins)


def exhaustive():
    R, cache, full = 3, {}, {}

    def recompiled(ws):
        if ws not in full:
            full[ws] = compile_locality(spec4(ws), R, cache)
            assert full[ws].series() == direct_series(spec4(ws), R)
        return full[ws]

    kinds = {"insertion": 0, "deletion": 0, "weight_change": 0}
    affected = []
    start = time.perf_counter()
    for ws in itertools.product(range(3), repeat=6):
        comp = recompiled(ws)
        for i, (u, v) in enumerate(PAIRS4):
            for new in range(3):
                if new == ws[i]:
                    continue
                stats = {}
                updated, _ = apply_local_changes(comp, [edge_change(u, v, ws[i], new)], record=False,
                                                 statistics=stats)
                assert updated.state_signature() == recompiled(ws[:i] + (new,) + ws[i + 1:]).state_signature()
                kinds["insertion" if ws[i] == 0 else "deletion" if new == 0 else "weight_change"] += 1
                affected.append(stats["affected_supports"])
    TIMES.append(("exhaustive K4 weightings: compile + 8748 updates + oracle", time.perf_counter() - start))
    pins = 0
    for mask in range(64):
        ws = tuple(mask >> i & 1 for i in range(6))
        comp = compile_locality(spec4(ws), R)
        for v in range(4):
            p = [0] * 4
            p[v] = 2
            up, _ = apply_local_changes(comp, [pin_change(v, 0, 2)], record=False)
            assert up.series() == direct_series(spec4(ws, p), R)
            back, _ = apply_local_changes(up, [pin_change(v, 2, 0)], record=False)
            assert back.state_signature() == comp.state_signature()
            pins += 1
    rng = random.Random(16)
    n = 5
    comp = compile_locality(WeightedSpec(n, [(u, v, rng.randint(0, 2)) for u, v in itertools.combinations(range(n), 2)],
                                         [rng.randint(0, 1) for _ in range(n)]), R)
    original = comp.state_signature()
    history, replayed = [], 0
    for step in range(14):
        batch, used = [], set()
        for _ in range(rng.randint(1, 3)):
            if rng.random() < .7:
                u, v = sorted(rng.sample(range(n), 2))
                if (u, v) in used:
                    continue
                used.add((u, v))
                old = comp.weight(u, v)
                batch.append(edge_change(u, v, old, rng.choice([w for w in range(4) if w != old])))
            else:
                v = rng.randrange(n)
                if v in used:
                    continue
                used.add(v)
                old = comp.pinning(v)
                batch.append(pin_change(v, old, rng.choice([p for p in range(3) if p != old])))
        comp, record = apply_local_changes(comp, batch)
        history.append(batch)
        assert comp.state_signature() == compile_locality(comp.spec, R).state_signature()
        assert verify_local_update(record, oracle_budget=4 ** n)["oracle"]
        replayed += 1
    for batch in reversed(history):
        comp, _ = apply_local_changes(comp, [ch.inverse() for ch in batch], record=False)
    assert comp.state_signature() == original
    return {"R": R, "family": "all weightings of K4 with edge weights in {0,1,2}, zero pinning",
            "weighted_graphs": 729, "single_edits": sum(kinds.values()), "edit_kinds": kinds,
            "affected_supports_range": [min(affected), max(affected)],
            "comparison": "identical log and support index versus full recompilation; every recompiled series "
                          "equals direct_series (box [0,R]^4, edge-difference energy)",
            "pin_edits_with_reversal": pins,
            "sequential": {"vertices": n, "batches": len(history), "changes": sum(map(len, history)),
                           "records_replayed_with_direct_oracle": replayed, "reversal_exact": True}}


def ladder(m):
    edges = ([(i, i + 1, 1) for i in range(m - 1)] + [(m + i, m + i + 1, 1) for i in range(m - 1)]
             + [(i, m + i, 1) for i in range(m)])
    return WeightedSpec(2 * m, edges)


def ladder_edits(m):
    c = m // 2
    return [("rung reweight 1->3", [edge_change(c, m + c, 1, 3)], False),
            ("rail deletion", [edge_change(c, c + 1, 1, 0)], True),
            ("diagonal insertion", [edge_change(c, m + c + 1, 0, 1)], True),
            ("pinning 0->2", [pin_change(c + 1, 0, 2)], False)]


UPDATE_FIELDS = ("affected_supports", "supports_changed", "supports_added", "supports_removed", "phi_lookups",
                 "phi_computed", "restricted_logs", "profiles", "poly_adds")


def scaling():
    R = SCALING_R
    rows, reference = [], None
    for m in LADDERS:
        spec = ladder(m)
        setup = {}
        comp = timed(f"ladder m={m}: setup compile (n={2 * m})", compile_locality, spec, R, None, setup)
        base_sig = comp.state_signature()
        edits = []
        for name, batch, unweighted in ladder_edits(m):
            cold = {}
            timed(f"ladder m={m}: update cold [{name}]", apply_local_changes, comp, batch, in_place=True,
                  record=False, statistics=cold)
            log_bits = coefficient_bits(comp.log)
            query = {}
            series = timed(f"ladder m={m}: query exp [{name}]", comp.series, query)
            fresh = {}
            full = timed(f"ladder m={m}: full recompile [{name}]", compile_locality, comp.spec, R, None, fresh)
            assert full.state_signature() == comp.state_signature()
            if unweighted:
                g = Graph(comp.n, [(u, v) for u, v, _ in comp.spec.weights])
                assert timed(f"ladder m={m}: locality.pinned_log [{name}]", pinned_log, g, R, 0) == comp.log
            undo = {}
            apply_local_changes(comp, [ch.inverse() for ch in batch], in_place=True, record=False, statistics=undo)
            assert comp.state_signature() == base_sig
            warm = {}
            timed(f"ladder m={m}: update warm [{name}]", apply_local_changes, comp, batch, in_place=True,
                  record=False, statistics=warm)
            apply_local_changes(comp, [ch.inverse() for ch in batch], in_place=True, record=False)
            edits.append({"edit": name, "cold": {f: cold.get(f, 0) for f in UPDATE_FIELDS},
                          "warm": {f: warm.get(f, 0) for f in UPDATE_FIELDS},
                          "undo_phi_computed": undo.get("phi_computed", 0),
                          "query_exp_poly_products": query["exp_poly_products"],
                          "log_bits": log_bits,
                          "series_bits": coefficient_bits(series),
                          "full_recompile_supports": fresh["supports"],
                          "checked_against_pinned_log": unweighted})
        assert comp.state_signature() == base_sig
        local = [{k: e[k] for k in ("edit", "cold", "warm", "undo_phi_computed", "query_exp_poly_products")}
                 for e in edits]
        if reference is None:
            reference = local
        assert local == reference, f"update work changed at m={m}"
        rows.append({"m": m, "vertices": 2 * m, "max_degree_after_edits": 4,
                     "setup": {k: setup[k] for k in ("supports", "distinct_keys", "phi_computed", "restricted_logs",
                                                     "profiles", "poly_adds")},
                     "storage": {"support_index_entries": len(comp.support_index), "cache_entries": len(comp.cache)},
                     "baseline_log_bits": coefficient_bits(comp.log), "edits": edits})
    # exactness on a tiny ladder against direct enumeration as well
    small = compile_locality(ladder(3), R)
    for name, batch, _ in ladder_edits(3):
        up, _ = apply_local_changes(small, batch, record=False)
        assert up.series() == direct_series(up.spec, R)
    return {"family": "ladder P_2 x P_m, unit weights, zero pinning; edits in column c = m // 2", "R": R,
            "update_work_identical_for_all_m": True, "direct_oracle_ladder_m3": True, "sizes": rows}


def receipts():
    out = []
    for m, R, oracle in ((3, 3, 4 ** 6), (5, 3, 0)):
        comp = compile_locality(ladder(m), R)
        c = m // 2
        _, record = apply_local_changes(comp, [edge_change(c, m + c, 1, 2), edge_change(c, c + 1, 1, 0),
                                               pin_change(m + c, 0, 1)])
        summary = timed(f"receipt ladder m={m}: replay", verify_local_update, record, oracle_budget=oracle)
        out.append({"record": record, "replay_summary": summary})
    return out


def replay_retained(retained):
    for item in retained["receipts"]:
        record = item["record"]
        oracle = 4 ** WeightedSpec.from_json(record["baseline"]["spec"]).n if item["replay_summary"]["oracle"] else 0
        if verify_local_update(record, oracle_budget=oracle) != item["replay_summary"]:
            raise SystemExit("retained receipt replay summary differs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="recompute, replay and compare with the retained receipt")
    args = parser.parse_args()
    start = time.perf_counter()
    result = {"schema": "singularity.incremental-locality-receipt/1", "track": "NX16",
              "update_schema": SCHEMA, "contract": contract(), "exhaustive": exhaustive(),
              "scaling": scaling(), "receipts": receipts(),
              "theorems": {"support_expansion": "log F_w mod x^(R+1) = sum over positive-weight-connected S, "
                                                "|S| <= R, of Phi_S(w)",
                           "union_difference": "Delta log F = sum over U-connected S, |S| <= R, S meets D, "
                                               "of Phi_S(w') - Phi_S(w)",
                           "locality": "affected supports lie within union distance R-1 of D",
                           "proofs": "docs/research/INCREMENTAL_LOCALITY.md"}}
    total = time.perf_counter() - start
    print(f"{'measurement (seconds; not retained)':64s} time")
    for label, seconds in TIMES:
        print(f"{label:64s} {seconds:.4f}")
    print(f"total {total:.2f} s; Python {platform.python_version()}")
    if args.check:
        retained = json.loads(TARGET.read_text()) if TARGET.exists() else None
        if retained != json.loads(json.dumps(result)):
            raise SystemExit("incremental locality receipt differs")
        replay_retained(retained)
        print("Incremental locality receipt matches; retained update records replay")
        return
    TARGET.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(f"wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
