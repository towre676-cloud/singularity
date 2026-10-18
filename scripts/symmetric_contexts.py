#!/usr/bin/env python3
"""P52-P54: interface rank and observable quotient of swap-symmetric contexts.

For budgets R <= 7 at q0 = 1/2 the exact rank of the probe map from the
unknowns Y_o[v] (|o| <= v <= R) to glued series is computed for the family
symmetric_context(d, eps, c), once without the terminal edge and once with
it, next to the SNG-F48(a) top-degree defect.  The constructive recovery
(SNG-F48(b)) is replayed on every connected block on at most four vertices
without a terminal edge at R = 3, against the symmetrized kernel computed
by bag messages.  ``--census`` additionally groups all connected blocks on
at most six vertices by symmetrized kernel through volume 4 (about three
minutes; retained, not rerun by ``--check``).

SNG-F49/F50 sections: the proved quotient dimensions (formal and
realizable, with and without the terminal edge) for budgets 0..30, the
explicit blind directions at R = 25 and R = 26, the least degree at which
the lower-degree rank condition fails, the degree-25 diagonal ranks modulo
a prime, modular probe-map ranks confirming the dimension for R = 8..12
(``--extended`` retains R = 13..18), weighted-edge recovery on real weighted
gluings, and (``--benchmark``, retained) compile-once versus per-query cost.
"""
import argparse
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
import time

from singularity.contexts import (_context_series, interface_status, lower_degree_condition,
                                  recover_symmetrized_kernel, symmetric_context, symmetric_interface_rank,
                                  symmetric_interface_rank_mod, symmetric_probe_set, symmetrize, top_block_rank_mod,
                                  top_degree_defect, top_degree_kernel, weighted_probe)
from singularity.decomposition import decomposition_histogram, elimination_decomposition
from singularity.heights import weak_compositions
from singularity.transfer import histogram_coefficients
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.polynomials import polynomial_to_json
from singularity.terminals import glue, glue_graphs, terminal_kernel

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


def quotient():
    statuses = {f"{'realizable' if real else 'formal'}_kappa_{kappa}": [interface_status(R, kappa, real) for R in range(31)]
                for kappa in (1, 2) for real in (False, True)}
    vector = lambda vs: [{"orbit": list(o), "polynomial": polynomial_to_json(p)} for v in vs for o, p in v.items()]
    return {"statuses": statuses,
            "blind_direction_R25_formal_kappa_2": vector(top_degree_kernel(25, 2)),
            "blind_direction_R25_realizable_kappa_2": vector(top_degree_kernel(25, 2, True)),
            "blind_direction_R26_realizable_kappa_2": vector(top_degree_kernel(26, 2, True)),
            "lower_condition_first_failure": {f"{'realizable' if real else 'formal'}_kappa_{kappa}": lower_degree_condition(100, kappa, real)
                                              for kappa in (1, 2) for real in (False, True)},
            "degree_25_diagonal_rank_mod_p": {name: list(top_block_rank_mod(25, kappa, real)) for name, kappa, real in
                                              [("formal_kappa_2", 2, False), ("realizable_kappa_2", 2, True), ("formal_kappa_3", 3, False)]}}


def modular_ranks(budgets):
    out = []
    for R in budgets:
        status = interface_status(R, 1)
        target = status["unknowns"] - status["top_defect"]
        unknowns, rank = symmetric_interface_rank_mod(R, False, target=target)
        out.append({"budget": R, "unknowns": unknowns, "rank_mod_p": rank, "unknowns_minus_top_defect": target})
    return out


def weighted_recovery(R=3, W=2):
    checked = 0
    for graph in blocks(4):
        values = {}
        for d, e in symmetric_probe_set(R, W):
            probe = weighted_probe(graph, d, e)
            values[d, e] = [sum((Q0 ** probe.energy(a) for a in weak_compositions(v, probe.n)), Fraction(0)) for v in range(R + 1)]
        Y = recover_symmetrized_kernel(values, R, Q0, max_edge_weight=W)
        plus = symmetrize(terminal_kernel(graph, (0, 1), R))
        for o, series in Y.items():
            for interior in range(R + 1 - sum(o)):
                expected = sum((c * Q0 ** en for (v, en), c in plus.get(o, {}).items() if v == interior), Fraction(0))
                assert series[sum(o) + interior] == expected, (graph.edges, o, interior)
        checked += 1
    return {"budget": R, "max_edge_weight": W, "blocks": checked, "probes_per_block": len(symmetric_probe_set(R, W)),
            "glued_series": "weak-composition enumeration of the weighted glued graph"}


def benchmark(R=6):
    """Compile a ladder block once, then answer symmetric-context queries by contraction."""
    rungs = 6
    edges = [(i, i + 1) for i in range(rungs - 1)] + [(rungs + i, rungs + i + 1) for i in range(rungs - 1)]
    edges += [(i, rungs + i) for i in range(rungs)]
    # terminals: opposite corners 0 and 2*rungs-1, relabelled to 0, 1
    far = 2 * rungs - 1
    relabel = {0: 0, far: 1}
    relabel.update({v: i + 2 for i, v in enumerate(v for v in range(2 * rungs) if v not in (0, far))})
    block = Graph(2 * rungs, [(relabel[u], relabel[v]) for u, v in edges])
    start = time.perf_counter()
    kernel = terminal_kernel(block, (0, 1), R)
    compile_time = time.perf_counter() - start
    queries = [(d, e, c) for d in range(4) for e in (0, 1) for c in range(3)]
    contraction, direct = 0.0, 0.0
    for d, e, c in queries:
        context, terminals = symmetric_context(d, bool(e), c)
        start = time.perf_counter()
        series = glue(kernel, terminal_kernel(context, terminals, R), R)
        contraction += time.perf_counter() - start
        glued, _ = glue_graphs(block, (0, 1), context, terminals)
        start = time.perf_counter()
        remaining = {v: set(glued.neighbors[v]) for v in range(glued.n)}
        order = []
        while remaining:
            v = min(remaining, key=lambda u: (len(remaining[u]), u))
            nbrs = remaining.pop(v)
            for a in nbrs:
                remaining[a] |= nbrs - {a}
                remaining[a].discard(v)
            order.append(v)
        reference = histogram_coefficients(decomposition_histogram(glued, elimination_decomposition(glued, order), R, R), R)
        direct += time.perf_counter() - start
        assert series == reference
    per_contraction, per_direct = contraction / len(queries), direct / len(queries)
    return {"block": "2 x 6 ladder, terminals at opposite corners", "budget": R, "queries": len(queries),
            "compile_seconds": round(compile_time, 3), "contraction_seconds_per_query": round(per_contraction, 4),
            "direct_decomposition_seconds_per_query": round(per_direct, 4),
            "break_even_queries": None if per_direct <= per_contraction else round(compile_time / (per_direct - per_contraction), 1),
            "note": "wall-clock on the session machine; context kernels are recomputed per query, block kernel once"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--census", action="store_true")
    parser.add_argument("--extended", action="store_true")
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()
    start = time.time()
    result = {"schema": "singularity.symmetric-contexts/1", "q0": "1/2",
              "family": "symmetric_context(d, eps, c): d leaves on each terminal, c shared neighbours, optional terminal edge; d <= #orbits, c <= R",
              "ranks": ranks(), "recovery": recovery(), "quotient": quotient(),
              "modular_ranks_without_terminal_edge": modular_ranks(range(8, 13)),
              "weighted_recovery": weighted_recovery()}
    retained = json.loads(TARGET.read_text()) if TARGET.exists() else {}
    if args.check:
        if {k: retained.get(k) for k in result} != result:
            raise SystemExit("symmetric context receipt differs")
        print("Symmetric context receipt matches", round(time.time() - start, 1), "s")
        return
    result["census"] = census() if args.census else retained.get("census")
    result["modular_ranks_extended"] = modular_ranks(range(13, 19)) if args.extended else retained.get("modular_ranks_extended")
    result["benchmark"] = benchmark() if args.benchmark else retained.get("benchmark")
    TARGET.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps(result, indent=1), round(time.time() - start, 1), "s")


if __name__ == "__main__":
    main()
