#!/usr/bin/env python3
"""P16: a systematic Whitney-switch census with structural witnesses (SNG-F41/F46).

Family A: blocks are connected graphs on 3 or 4 vertices with terminals 0, 1.
Family B: the first block is a connected graph on 3-5 vertices whose two
terminals have equal degree (so the twist preserves the degree sequence),
and isomorphic outcomes are skipped.  In both, the second block never
contains the terminal edge, so the gluings are edge-disjoint and simple.
Every ordered pair of blocks is glued straight and twisted.  For each pair the receipt records:

* simplicity and connectedness of both graphs;
* cycle-matroid preservation, checked by comparing all circuits under the
  explicit edge correspondence of the two gluings;
* isomorphism, decided by the census canonical code (pairs that are
  isomorphic are kept with that label, not discarded);
* the first local and marked differences through volume 6, computed by weak
  compositions and by level chains independently, and the SNG-F41 pairing
  prediction.

Pairs are deduplicated by the canonical codes of (straight, twisted), with
the first witness retained.  ``--check`` compares with the retained file.
"""
import argparse
from itertools import combinations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from census import canonical_code  # noqa: E402
from singularity.chains import chain_marked_coefficients  # noqa: E402
from singularity.graph import Graph  # noqa: E402
from singularity.heights import local_coefficients, marked_coefficients  # noqa: E402
from singularity.polynomials import polynomial_to_json, sub  # noqa: E402
from singularity.terminals import circuits, glue_graphs, terminal_kernel, twist_difference  # noqa: E402

TARGET = ROOT / "results/whitney_switches.json"
BOUND = 6


def blocks(allow_terminal_edge, sizes=(3, 4), balanced=False):
    out = []
    for n in sizes:
        pairs = [p for p in combinations(range(n), 2) if allow_terminal_edge or p != (0, 1)]
        for mask in range(1 << len(pairs)):
            graph = Graph(n, [e for j, e in enumerate(pairs) if mask >> j & 1])
            if graph.connected and (not balanced or graph.degrees[0] == graph.degrees[1]):
                out.append(graph)
    return out


def edge_map(first, second, mapping):
    correspondence = {e: e for e in first.edges}
    for u, v in second.edges:
        correspondence[("b", u, v)] = tuple(sorted((mapping[u], mapping[v])))
    return correspondence


def first_marked_difference(a, b):
    keys = sorted(set(a) | set(b))
    cells = [k for k in keys if a.get(k, 0) != b.get(k, 0)]
    return None if not cells else min(cells)[0]


def compute():
    records, seen = [], set()
    pairs = [(f, s, "A") for f in blocks(True) for s in blocks(False)]
    pairs += [(f, s, "B") for f in blocks(True, (3, 4, 5), balanced=True) for s in blocks(False)]
    for first, second, family in pairs:
        if True:
            straight, map_s = glue_graphs(first, (0, 1), second, (0, 1))
            twisted, map_t = glue_graphs(first, (0, 1), second, (1, 0))
            key = (straight.n, canonical_code(straight), canonical_code(twisted))
            if key in seen:
                continue
            seen.add(key)
            isomorphic = canonical_code(straight) == canonical_code(twisted) and straight.n == twisted.n
            if isomorphic and family == "B":
                continue  # family B targets degree-preserving nonisomorphic switches
            # Cycle matroid: circuits correspond under the edge bijection.
            corr_s, corr_t = edge_map(first, second, map_s), edge_map(first, second, map_t)
            to_t = {corr_s[k]: corr_t[k] for k in corr_s}
            matroid = {frozenset(to_t[e] for e in c) for c in circuits(straight)} == circuits(twisted)
            local_s, local_t = local_coefficients(straight, BOUND), local_coefficients(twisted, BOUND)
            local_first = next((v for v in range(BOUND + 1) if local_s[v] != local_t[v]), None)
            marked_s, marked_t = marked_coefficients(straight, BOUND), marked_coefficients(twisted, BOUND)
            chains_s, chains_t = chain_marked_coefficients(straight, BOUND), chain_marked_coefficients(twisted, BOUND)
            assert marked_s == chains_s and marked_t == chains_t
            k1, k2 = terminal_kernel(first, (0, 1), BOUND), terminal_kernel(second, (0, 1), BOUND)
            predicted = twist_difference(k1, k2, BOUND)
            assert [sub(a, b) for a, b in zip(local_s, local_t)] == predicted
            records.append({"family": family,
                "first_block": first.to_dict(), "second_block": second.to_dict(),
                "straight": straight.to_dict(), "twisted": twisted.to_dict(),
                "simple_and_connected": straight.connected and twisted.connected,
                "cycle_matroid_preserved": matroid, "isomorphic": isomorphic,
                "first_local_difference": local_first,
                "first_marked_difference": first_marked_difference(marked_s, marked_t),
                "difference_at_first_volume": None if local_first is None else polynomial_to_json(sub(local_s[local_first], local_t[local_first])),
                "status": ("isomorphic graphs" if isomorphic else
                           "separated" if local_first is not None else
                           f"unresolved: agreement through volume {BOUND} only"),
            })
    summary = {}
    for r in records:
        summary[r["status"] if r["first_local_difference"] is None else f"separated at volume {r['first_local_difference']}"] = \
            summary.get(r["status"] if r["first_local_difference"] is None else f"separated at volume {r['first_local_difference']}", 0) + 1
    return {"schema": "singularity.whitney-switches/1", "bound": BOUND,
            "family": "A: connected blocks on 3-4 vertices; B: balanced first block on 3-5 vertices, nonisomorphic outcomes; terminals (0,1); second block without the terminal edge",
            "summary": dict(sorted(summary.items())), "pairs": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    assert all(r["cycle_matroid_preserved"] and r["simple_and_connected"] for r in result["pairs"])
    text = json.dumps(result, indent=1, sort_keys=True) + "\n"
    if args.check:
        if TARGET.read_text() != text:
            raise SystemExit("Whitney switch receipt differs")
        print("Whitney switch receipt matches:", result["summary"])
        return
    TARGET.write_text(text)
    print(result["summary"])


if __name__ == "__main__":
    main()
