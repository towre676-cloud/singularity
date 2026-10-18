#!/usr/bin/env python3
"""P29: canonical manifest of connected simple graphs on 1..6 vertices.

Specification: docs/specifications/CENSUS-v1.md.  Every labeled simple graph
of each order is generated, filtered by exact connectedness and grouped by
``census.canonical_code``.  For every class the manifest records the
representative (first labeled graph in generation order), its source digest,
the size of its code group, and the independently computed automorphism
group order.  Reconciliation is independent of the stored counts:

* connected labeled counts are compared with the recurrence
  c_n = 2^C(n,2) - sum_{k<n} C(n-1,k-1) c_k 2^C(n-k,2);
* each code group must have exactly n!/|Aut(representative)| members, with
  |Aut| found by testing all n! permutations, so every group is exactly one
  isomorphism orbit (coverage and uniqueness).

``--check`` regenerates everything and compares with the retained file.
"""
import argparse
from hashlib import sha256
from itertools import combinations, permutations
import json
from math import comb, factorial
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from census import canonical_code  # noqa: E402
from singularity.graph import Graph  # noqa: E402

TARGET = ROOT / "results/census_manifest.json"
MAX_ORDER = 6


def digest(graph):
    source = {"n": graph.n, "edges": [list(e) for e in graph.edges]}
    return sha256(json.dumps(source, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def automorphism_count(graph):
    edges = set(graph.edges)
    return sum(
        all(tuple(sorted((p[u], p[v]))) in edges for u, v in graph.edges)
        for p in permutations(range(graph.n))
    )


def connected_labeled_recurrence(max_order):
    counts = {}
    for n in range(1, max_order + 1):
        counts[n] = 2 ** comb(n, 2) - sum(comb(n - 1, k - 1) * counts[k] * 2 ** comb(n - k, 2) for k in range(1, n))
    return counts


def build():
    recurrence = connected_labeled_recurrence(MAX_ORDER)
    orders = []
    for n in range(1, MAX_ORDER + 1):
        pairs = list(combinations(range(n), 2))
        groups, labeled = {}, 0
        for mask in range(1 << len(pairs)):
            graph = Graph(n, [edge for j, edge in enumerate(pairs) if mask >> j & 1])
            if not graph.connected:
                continue
            labeled += 1
            code = canonical_code(graph)
            entry = groups.setdefault(code, {"representative": graph, "mask": mask, "members": 0})
            entry["members"] += 1
        classes = []
        for code, entry in sorted(groups.items()):
            graph = entry["representative"]
            automorphisms = automorphism_count(graph)
            if entry["members"] * automorphisms != factorial(n):
                raise ArithmeticError(f"code group {code} on {n} vertices is not one isomorphism orbit")
            classes.append({
                "canonical_code": code, "generation_mask": entry["mask"], "n": n,
                "edges": [list(e) for e in graph.edges], "sha256": digest(graph),
                "degrees": sorted(graph.degrees), "labeled_copies": entry["members"],
                "automorphism_group_order": automorphisms,
            })
        if labeled != recurrence[n]:
            raise ArithmeticError(f"connected labeled count {labeled} differs from recurrence {recurrence[n]}")
        orders.append({
            "n": n, "labeled_graphs_generated": 2 ** len(pairs),
            "connected_labeled_graphs": labeled, "recurrence_connected_labeled": recurrence[n],
            "isomorphism_classes": len(classes),
            "orbit_stabilizer_total": sum(factorial(n) // c["automorphism_group_order"] for c in classes),
            "classes": classes,
        })
    return {
        "schema": "singularity.census-manifest/1",
        "specification": "docs/specifications/CENSUS-v1.md",
        "graph_class": "connected simple loopless graphs, original labels 0..n-1",
        "orders_included": [1, MAX_ORDER],
        "generation": "every edge subset of combinations(range(n), 2), bit j selecting pair j, masks in increasing order",
        "isomorphism": "census.canonical_code: minimum adjacency bit string over degree-sorted vertex orders",
        "representative": "first connected labeled graph in mask order with the class code",
        "digest": "sha256 of compact sorted-key JSON {n, edges} with canonical edges, as in certificates",
        "orders": orders,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest = build()
    text = json.dumps(manifest, indent=1, sort_keys=True) + "\n"
    if args.check:
        if TARGET.read_text(encoding="utf-8") != text:
            raise SystemExit("census manifest differs from retained output")
        print("Census manifest matches:", [o["isomorphism_classes"] for o in manifest["orders"]])
        return
    TARGET.write_text(text, encoding="utf-8")
    print([o["connected_labeled_graphs"] for o in manifest["orders"]], [o["isomorphism_classes"] for o in manifest["orders"]])


if __name__ == "__main__":
    main()
