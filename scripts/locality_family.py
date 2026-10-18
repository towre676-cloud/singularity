#!/usr/bin/env python3
"""Observation depth: connected-support compiler, first-cycle collisions, cycle reconstruction.

SNG-F55 to SNG-F57.  ``--check`` compares with the retained file.

* Compiler against weak-composition enumeration (A_H with lam = 2 and the
  local series L_H with lam = 0) on fixtures and seeded random graphs.
* First-cycle theorem: cube against Moebius ladder (squares 6 and 4) and
  prism against K_{3,3} (triangles 2 and 0), compared with
  Delta N_g q^((d + lam - 2) g) (1 - q^2)^g; the cube-Moebius local
  difference equals the retained fixture.
* Cycle family: A(C_g + C_g) - A(C_2g) first differs at volume g with
  2 [q^2 (1 - q^2)]^g, g = 3..8 (enumeration oracle for g <= 6).
* Dominating blocks over C_12 and C_6 + C_6 glued to one shared neighbour:
  the actual 15-vertex glued graphs, counted by weak compositions, agree
  through volume five and differ at six by 729/8388608 at q = 1/2.
* Reconstruction of every 2-regular graph on at most 14 vertices at budget
  floor(n/2), and the sharpness pairs C_n against C_g + C_(n-g).
* ``--benchmark`` (retained): random cubic graphs, compiler against tree
  decomposition (L_G).
"""
import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
import random
import time

from singularity.charges import _at, dominating_block
from singularity.decomposition import decomposition_histogram, elimination_decomposition
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.locality import (cycle, cycle_log_difference, disjoint_union, kappa, pinned_log, pinned_series,
                                  pinned_series_by_enumeration, reconstruct_cycle_type, series_from_log)
from singularity.polynomials import normalize, polynomial_from_json, polynomial_to_json, power, scale, sub
from singularity.terminals import glue_graphs
from singularity.transfer import histogram_coefficients

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "results/locality_family.json"
CUBE = Graph(8, [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3), (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)])
MOBIUS = Graph(8, [(0, 1), (0, 4), (0, 7), (1, 2), (1, 5), (2, 3), (2, 6), (3, 4), (3, 7), (4, 5), (5, 6), (6, 7)])
K33 = Graph(6, [(u, v) for u in range(3) for v in range(3, 6)])
PRISM = Graph(6, [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (0, 3), (1, 4), (2, 5)])


def diff(a, b):
    return [normalize(sub(x, y)) for x, y in zip(a, b)]


def first(d):
    return next((v for v, c in enumerate(d) if c), None)


def oracle():
    rng = random.Random(2026)
    graphs = [CUBE, MOBIUS, K33, PRISM] + [Graph(n, [e for e in combinations(range(n), 2) if rng.random() < 0.5])
                                            for n in (4, 5, 5, 6, 6, 6)]
    for G in graphs:
        for lam in (0, 2):
            assert pinned_series(G, 4, lam) == pinned_series_by_enumeration(G, 4, lam)
    return {"graphs": len(graphs), "budget": 4, "shifts": [0, 2], "agreement": True}


def first_cycle():
    rows = []
    retained = json.loads((ROOT / "results/exact_examples.json").read_text())["pairs"]["regular_cube_mobius"]
    for name, a, b, d, g, cycles in [("cube - moebius", CUBE, MOBIUS, 3, 4, 2), ("prism - K33", PRISM, K33, 3, 3, 2)]:
        for lam in (0, 2):
            D = diff(pinned_series(a, g + 1, lam), pinned_series(b, g + 1, lam))
            predicted = scale(power(kappa(lam, d), g), cycles)
            assert first(D) == g and D[g] == predicted
            if name.startswith("cube") and lam == 0:
                assert D[g] == polynomial_from_json(retained["difference"])
            rows.append({"pair": name, "lam": lam, "first_volume": g, "cycle_count_difference": cycles,
                         "difference": polynomial_to_json(D[g])})
    return rows


def cycle_family(max_g=8):
    rows = []
    for g in range(3, max_g + 1):
        two, one = disjoint_union(cycle(g), cycle(g)), cycle(2 * g)
        D = diff(pinned_series(two, g), pinned_series(one, g))
        assert first(D) == g and D[g] == scale(power(kappa(2), g), 2)
        if g <= 6:
            assert D == diff(pinned_series_by_enumeration(two, g), pinned_series_by_enumeration(one, g))
        rows.append({"g": g, "first_volume": g, "difference": polynomial_to_json(D[g]), "enumeration_oracle": g <= 6})
    return rows


def dominating_closure():
    R, q = 6, Fraction(1, 2)
    context = Graph(3, [(0, 2), (1, 2)])
    series = []
    for H in (cycle(12), disjoint_union(cycle(6), cycle(6))):
        G, T = dominating_block(H)
        glued, _ = glue_graphs(G, T, context, (0, 1))
        series.append([_at(row, q) for row in local_coefficients(glued, R)])
    difference = [b - a for a, b in zip(*series)]
    assert difference[:6] == [0] * 6 and difference[6] == Fraction(729, 8388608)
    return {"interiors": ["C_12", "C_6 + C_6"], "context": "one shared neighbour", "glued_vertices": 15,
            "q": "1/2", "first_volume": 6, "difference": str(difference[6])}


def reconstruction(max_n=14):
    def partitions(n, smallest=3):
        if n == 0:
            yield []
            return
        for k in range(smallest, n + 1):
            for rest in partitions(n - k, k):
                yield [k] + rest

    total, sharp = 0, []
    for n in range(3, max_n + 1):
        R = n // 2
        tables = cycle_log_difference(R)
        for parts in partitions(n):
            H = disjoint_union(*[cycle(l) for l in parts])
            assert reconstruct_cycle_type(pinned_log(H, R), n, R, tables=tables) == dict(sorted(Counter(parts).items()))
            total += 1
        if n >= 6:
            g = n // 2
            D = diff(pinned_series(cycle(n), g), pinned_series(disjoint_union(cycle(g), cycle(n - g)), g))
            assert first(D) == g
            sharp.append({"n": n, "pair": f"C_{n} vs C_{g} + C_{n - g}", "first_volume": g})
    return {"graphs_reconstructed": total, "max_n": max_n, "budget": "floor(n/2)", "sharpness": sharp}


def random_cubic(n, seed):
    rng = random.Random(seed)
    while True:
        points = [v for v in range(n) for _ in range(3)]
        rng.shuffle(points)
        edges = {tuple(sorted(points[i:i + 2])) for i in range(0, 3 * n, 2)}
        if len(edges) == 3 * n // 2 and all(u != v for u, v in edges):
            G = Graph(n, sorted(edges))
            if G.connected:
                return G


def _order(g):
    rem = {v: set(g.neighbors[v]) for v in range(g.n)}
    out = []
    while rem:
        v = min(rem, key=lambda u: (len(rem[u]), u))
        nb = rem.pop(v)
        for a in nb:
            rem[a] |= nb - {a}
            rem[a].discard(v)
        out.append(v)
    return out


def benchmark():
    rows = []
    for R in (4, 6):
        for n in (16, 32, 64, 128):
            G = random_cubic(n, n)
            stats = {}
            start = time.perf_counter()
            L = series_from_log(pinned_log(G, R, 0, stats))
            compiler = time.perf_counter() - start
            dec = elimination_decomposition(G, _order(G))
            row = {"budget": R, "n": n, "compiler_seconds": round(compiler, 3), **stats, "min_degree_width": dec.width,
                   "bag_assignments": f"{sum((R + 1) ** len(b) for b in dec.bags):.3e}"}
            if R == 4 and n <= 32:
                start = time.perf_counter()
                ref = histogram_coefficients(decomposition_histogram(G, dec, R, R), R)
                row["decomposition_seconds"] = round(time.perf_counter() - start, 3)
                assert L == [{e: Fraction(c) for e, c in r.items()} for r in ref]
            rows.append(row)
    return {"graphs": "random connected cubic graphs (configuration model, seed n)", "series": "L_G (lam = 0)",
            "rows": rows, "note": "wall-clock on the session machine"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()
    result = {"schema": "singularity.locality-family/1", "oracle": oracle(), "first_cycle": first_cycle(),
              "cycle_family": cycle_family(), "dominating_closure": dominating_closure(), "reconstruction": reconstruction()}
    retained = json.loads(TARGET.read_text()) if TARGET.exists() else {}
    if args.check:
        if {k: retained.get(k) for k in result} != result:
            raise SystemExit("locality receipt differs")
        print("Locality receipt matches")
        return
    result["benchmark"] = benchmark() if args.benchmark else retained.get("benchmark")
    TARGET.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "benchmark"}, indent=1)[:3000])


if __name__ == "__main__":
    main()
