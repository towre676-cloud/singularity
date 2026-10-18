#!/usr/bin/env python3
"""P52/P53: interface rank of swap-symmetric contexts under a volume budget.

For budgets R <= 7 at q0 = 1/2 the exact rank of the probe map from the
unknowns Y_o[v] (|o| <= v <= R) to glued series is computed for the family
symmetric_context(d, eps, c), once without the terminal edge and once with
it, next to the SNG-F48(a) top-degree defect.  The constructive recovery
(SNG-F48(b)) is replayed on every connected block on at most four vertices
without a terminal edge at R = 3, against the symmetrized kernel computed
by bag messages.  ``--census`` additionally groups all connected blocks on
at most six vertices by symmetrized kernel through volume 4 (about three
minutes; retained, not rerun by ``--check``).
"""
import argparse
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
import time

from singularity.contexts import (recover_symmetrized_kernel, symmetric_context, symmetric_interface_rank,
                                  symmetric_probe_set, symmetrize, top_degree_defect)
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.terminals import glue_graphs, terminal_kernel

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "results/symmetric_contexts.json"
Q0 = Fraction(1, 2)


def blocks(max_n):
    for n in range(2, max_n + 1):
        pairs = [p for p in combinations(range(n), 2) if p != (0, 1)]
        for mask in range(1 << len(pairs)):
            graph = Graph(n, [e for j, e in enumerate(pairs) if mask >> j & 1])
            if graph.connected:
                yield graph


def at(poly):
    return sum((c * Q0 ** e for e, c in poly.items()), Fraction(0))


def recovery(R=3):
    checked = 0
    for graph in blocks(4):
        values = {}
        for d, e in symmetric_probe_set(R):
            context, terminals = symmetric_context(d, bool(e))
            glued, _ = glue_graphs(graph, (0, 1), context, terminals)
            values[d, e] = [at(row) for row in local_coefficients(glued, R)]
        Y = recover_symmetrized_kernel(values, R, Q0)
        plus = symmetrize(terminal_kernel(graph, (0, 1), R))
        for o, series in Y.items():
            for interior in range(R + 1 - sum(o)):
                expected = sum((c * Q0 ** en for (v, en), c in plus.get(o, {}).items() if v == interior), Fraction(0))
                assert series[sum(o) + interior] == expected, (graph.edges, o, interior)
        checked += 1
    return {"budget": R, "blocks": checked, "probes_per_block": len(symmetric_probe_set(R)),
            "population": "connected graphs on 2-4 labeled vertices, terminals (0,1), no terminal edge"}


def ranks(max_R=7):
    out = []
    for R in range(max_R + 1):
        unknowns, free = symmetric_interface_rank(R, Q0, False)
        _, edged = symmetric_interface_rank(R, Q0, True)
        out.append({"budget": R, "unknowns": unknowns, "rank_without_terminal_edge": free,
                    "rank_with_terminal_edge": edged, "top_degree_defect": top_degree_defect(R)})
    return out


def census(max_n=6, R=4):
    def swap(K):
        return {(b[1], b[0]): c for b, c in K.items()}

    def key(K):
        return repr(sorted((b, sorted(c.items())) for b, c in K.items()))

    groups, count = {}, 0
    for graph in blocks(max_n):
        K = terminal_kernel(graph, (0, 1), R)
        groups.setdefault(key(symmetrize(K)), set()).add(min(key(K), key(swap(K))))
        count += 1
    return {"population": f"connected graphs on 2-{max_n} labeled vertices, terminals (0,1), no terminal edge",
            "budget": R, "blocks": count, "symmetrized_classes": len(groups),
            "classes_with_two_kernel_swap_orbits": sum(len(g) > 1 for g in groups.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--census", action="store_true")
    args = parser.parse_args()
    start = time.time()
    result = {"schema": "singularity.symmetric-contexts/1", "q0": "1/2",
              "family": "symmetric_context(d, eps, c): d leaves on each terminal, c shared neighbours, optional terminal edge; d <= #orbits, c <= R",
              "ranks": ranks(), "recovery": recovery()}
    retained = json.loads(TARGET.read_text()) if TARGET.exists() else {}
    if args.check:
        if {k: retained.get(k) for k in result} != result:
            raise SystemExit("symmetric context receipt differs")
        print("Symmetric context receipt matches", round(time.time() - start, 1), "s")
        return
    result["census"] = census() if args.census else retained.get("census")
    TARGET.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps(result, indent=1), round(time.time() - start, 1), "s")


if __name__ == "__main__":
    main()
