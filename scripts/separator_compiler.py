#!/usr/bin/env python3
"""OE11: charge-aware separator compiler -- verification and benchmarks.

Retained (deterministic) in results/separator_compiler.json:

* verification: compile_graph and compile_decomposition against direct
  enumeration (heights.local_coefficients) on every labelled graph with at
  most five vertices, three vertex orders each, at R = 3; strip families
  against direct enumeration at R <= 4; cross-checks against the
  bag-message engine and the connected-support compiler (lam = 0);
* benchmarks for P_n, C_n, P_2 x P_n and P_3 x P_n at R = 3, 4: width,
  peak and widest-step nonzero charge cells against the proved cell bound,
  maximal count bit length against the proved bit bound, charge and energy
  ranges, step-operator size, a work proxy (cells summed over operations),
  the direct-enumeration profile count, and agreement of every route;
* the SHA-256 of each coefficient list (integrity only, not a proof).

Wall-clock times (compilation, operator construction, operator
application, query, direct enumeration, connected-support compiler) are
printed and never retained.
"""
import argparse
import hashlib
import itertools
import json
from math import comb
from pathlib import Path
import platform
import random
import time

from singularity.decomposition import decomposition_histogram, elimination_decomposition
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.locality import pinned_series
from singularity.separator_compiler import (apply_step_operator, build_step_operator, closed_coefficients,
                                            compile_decomposition, compile_graph, compile_interface,
                                            count_bit_bound, empty_interface, operator_size, periodic_plan,
                                            run_schedule, strip_graph)
from singularity.transfer import histogram_coefficients

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "results/separator_compiler.json"
FAMILIES = [("P_n", 1, False, ()), ("C_n", 1, True, (0,)), ("P_2 x P_n", 2, False, ()), ("P_3 x P_n", 3, False, ())]
SIZES = (5, 10, 20, 40, 80, 160, 200)
DIRECT_LIMIT = 24      # direct enumeration only while the graph has at most this many vertices
LOCALITY_LIMIT = 80    # connected-support cross-check for n up to this many columns
TIMES: list[str] = []


def digest(rows) -> str:
    return hashlib.sha256(json.dumps([sorted(r.items()) for r in rows]).encode()).hexdigest()[:16]


def graphs_on(n):
    edges = list(itertools.combinations(range(n), 2))
    for mask in range(1 << len(edges)):
        yield Graph(n, [e for i, e in enumerate(edges) if mask >> i & 1])


def verification():
    rng = random.Random(2026)
    graphs = orders = 0
    for n in range(1, 6):
        for graph in graphs_on(n):
            expected = local_coefficients(graph, 3)
            shuffled = list(range(n))
            rng.shuffle(shuffled)
            for order in (list(range(n)), list(range(n - 1, -1, -1)), shuffled):
                assert compile_graph(graph, order, 3) == expected
                assert compile_decomposition(graph, elimination_decomposition(graph, order), 3) == expected
                orders += 1
            graphs += 1
    families = 0
    for name, rows, cyclic, _ in FAMILIES:
        for n in range(3 if cyclic else 1, 9 if rows == 1 else (5 if rows == 2 else 4)):
            graph = strip_graph(rows, n, cyclic)
            for R in range(5):
                assert compile_graph(graph, range(graph.n), R) == local_coefficients(graph, R), (name, n, R)
                families += 1
    cross = 0
    for graph in (strip_graph(1, 12), strip_graph(1, 10, True), strip_graph(2, 6), strip_graph(3, 4),
                  Graph(7, [(0, 6), (6, 3), (2, 5)])):
        ours = compile_graph(graph, range(graph.n), 4)
        dec = elimination_decomposition(graph, list(range(graph.n)))
        assert ours == histogram_coefficients(decomposition_histogram(graph, dec, 4, 4), 4)
        assert ours == pinned_series(graph, 4, lam=0)
        cross += 1
    return {"all_graphs_at_most_5_vertices": graphs, "graph_order_pairs_R3": orders,
            "routes": ["compile_graph", "compile_decomposition (elimination decomposition, with joins)"],
            "oracle": "heights.local_coefficients (weak compositions of the actual graph)",
            "family_comparisons_R_le_4": families, "bag_message_and_connected_support_cross_checks": cross}


def timed(label, function, *args):
    start = time.perf_counter()
    value = function(*args)
    TIMES.append((label, time.perf_counter() - start))
    return value


def benchmark_case(name, rows, cyclic, anchors, n, R):
    graph = strip_graph(rows, n, cyclic)
    tag = f"{name} n={n} R={R}"
    stats = {}
    interface = timed(f"{tag}: compile", compile_interface, graph, range(graph.n), R, stats)
    coefficients = timed(f"{tag}: query", closed_coefficients, interface)
    plan = periodic_plan(graph, range(graph.n), rows, anchors)
    record = {"family": name, "n": n, "vertices": graph.n, "R": R, "max_degree": max(graph.degrees),
              "width": stats["width"], "operations": stats["operations"], "peak_cells": stats["max_cells"],
              "peak_charge_keys": stats["max_charge_keys"], "cells_at_widest": stats["cells_at_widest"],
              "cell_bound_at_widest": stats["cell_bound_at_widest"], "bound_violations": stats["bound_violations"],
              "max_count_bits": stats["max_count_bits"], "count_bit_bound": count_bit_bound(graph.n, R),
              "max_charge": stats["max_charge"], "energy_range": [stats["min_energy"], stats["max_energy"]],
              "work_cells_summed": stats["total_cells"],
              "direct_profiles": sum(comb(graph.n + j - 1, j) for j in range(R + 1)),
              "top_coefficient_total": sum(coefficients[R].values()),
              "coefficients_sha256_16": digest(coefficients)}
    assert record["top_coefficient_total"] == comb(graph.n + R - 1, R)
    assert record["max_count_bits"] <= record["count_bit_bound"] and not record["bound_violations"]
    assert 0 <= stats["min_energy"] and stats["max_energy"] <= record["max_degree"] * R * R and stats["max_charge"] <= R
    if plan["steps"]:
        start = timed(f"{tag}: prefix", run_schedule, empty_interface(R), plan["prefix"])
        operator = timed(f"{tag}: operator construction", build_step_operator, start, plan["segment"])
        t0 = time.perf_counter()
        state = start
        for m in range(plan["steps"]):
            state = apply_step_operator(operator, state, plan["labels"][m + 1])
        TIMES.append((f"{tag}: operator application x{plan['steps']}", time.perf_counter() - t0))
        state = run_schedule(state, plan["suffix"])
        assert closed_coefficients(state) == coefficients
        record["operator"] = dict(operator_size(operator), steps=plan["steps"])
    else:
        record["operator"] = None
    if graph.n <= DIRECT_LIMIT:
        assert timed(f"{tag}: direct enumeration", local_coefficients, graph, R) == coefficients
        record["direct_checked"] = True
    else:
        record["direct_checked"] = False
    if n <= LOCALITY_LIMIT:
        assert timed(f"{tag}: connected-support compiler", pinned_series, graph, R, 0) == coefficients
        record["connected_support_checked"] = True
    else:
        record["connected_support_checked"] = False
    return record


def benchmarks():
    out = []
    for name, rows, cyclic, anchors in FAMILIES:
        for R in (3, 4):
            for n in SIZES:
                out.append(benchmark_case(name, rows, cyclic, anchors, n, R))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="recompute and compare with the retained receipt")
    args = parser.parse_args()
    start = time.perf_counter()
    result = {"schema": "singularity.separator-compiler/1", "unit": "OE11",
              "verification": verification(), "benchmarks": benchmarks(),
              "theorems": {"exactness": "introduce, forget and join preserve the charge-interface invariant",
                           "cell_bound": "cells <= sum_{j<=R} (j+1)^k (D j^2 + 1), k active boundary vertices",
                           "bit_bound": "n_{j,Q,E} <= C(m+j-1, j) <= m^j, m interior vertices",
                           "ranges": "0 <= Q_i <= j and 0 <= E <= D j^2"}}
    total = time.perf_counter() - start
    print(f"{'measurement (seconds; not retained)':60s} time")
    for label, seconds in TIMES:
        print(f"{label:60s} {seconds:.4f}")
    print(f"total {total:.2f} s; Python {platform.python_version()}")
    if args.check:
        retained = json.loads(TARGET.read_text()) if TARGET.exists() else None
        if retained != json.loads(json.dumps(result)):
            raise SystemExit("separator compiler receipt differs")
        print("Separator compiler receipt matches")
        return
    TARGET.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(f"wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
