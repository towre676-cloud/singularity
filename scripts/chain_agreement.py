#!/usr/bin/env python3
"""P02 receipt: chain and weak-composition marked histograms on a declared population.

Population: every labeled simple graph on 1..5 vertices (1+2+8+64+1024 = 1099
graphs), every minimum-zero profile of total volume at most 6.  The per-graph
profile count is C(6+n,n)-C(6,n), so the comparison covers 479,963 profiles.
No isomorphism quotient is taken.  Elapsed time is recorded but ignored by
``--check``, which compares every exact field.
"""
import argparse
from itertools import combinations
import json
from math import comb
from pathlib import Path
import platform
import time

from singularity import __version__
from singularity.chains import chain_marked_coefficients
from singularity.graph import Graph
from singularity.heights import marked_coefficients

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "results/chain_agreement.json"
MAX_N, MAX_VOLUME = 5, 6


def compute():
    started = time.perf_counter()
    orders = []
    for n in range(1, MAX_N + 1):
        pairs = list(combinations(range(n), 2))
        graphs = cells = profiles = gap_profiles = 0
        disagreements = []
        for mask in range(1 << len(pairs)):
            graph = Graph(n, [edge for j, edge in enumerate(pairs) if mask >> j & 1])
            chains = chain_marked_coefficients(graph, MAX_VOLUME)
            compositions = marked_coefficients(graph, MAX_VOLUME)
            if chains != compositions:
                disagreements.append(graph.to_dict())
            graphs += 1
            cells += len(chains)
            profiles += sum(chains.values())
        # Profiles with a height gap: span exceeds the number of distinct
        # positive heights.  Counted independently of both engines.
        for volume in range(MAX_VOLUME + 1):
            stack = [((), 0)]
            while stack:
                prefix, used = stack.pop()
                if len(prefix) == n:
                    if used == volume and min(prefix) == 0:
                        values = set(prefix)
                        gap_profiles += any(h not in values for h in range(max(prefix) + 1))
                    continue
                for value in range(volume - used + 1):
                    stack.append((prefix + (value,), used + value))
        orders.append({
            "n": n, "labeled_graphs": graphs, "marked_cells_compared": cells,
            "profiles_per_graph": comb(MAX_VOLUME + n, n) - comb(MAX_VOLUME, n),
            "profiles_compared": profiles, "gap_profiles_per_graph": gap_profiles,
            "disagreements": disagreements,
        })
    return {
        "schema": "singularity.chain-agreement/1",
        "version": __version__,
        "population": "all labeled simple graphs on 1..5 vertices; minimum-zero profiles of volume <= 6",
        "max_n": MAX_N, "max_volume": MAX_VOLUME,
        "methods": {
            "chains": "singularity.chains.chain_marked_coefficients (nested level sets, SNG-F10 energy)",
            "oracle": "singularity.heights.marked_coefficients (weak compositions, squared differences)",
        },
        "orders": orders,
        "totals": {
            "labeled_graphs": sum(o["labeled_graphs"] for o in orders),
            "profiles_compared": sum(o["profiles_compared"] for o in orders),
            "marked_cells_compared": sum(o["marked_cells_compared"] for o in orders),
            "disagreements": sum(len(o["disagreements"]) for o in orders),
        },
        "interpretation": "Exact finite agreement on the declared population; not a proof for larger graphs or volumes.",
        "environment": {"python": platform.python_version()},
        "elapsed_seconds": round(time.perf_counter() - started, 2),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    if args.check:
        retained = json.loads(TARGET.read_text())
        exact = lambda record: {k: v for k, v in record.items() if k not in {"elapsed_seconds", "environment"}}
        if exact(retained) != exact(result):
            raise SystemExit("chain agreement differs from retained output")
        print("Chain agreement matches retained output:", json.dumps(result["totals"]))
        return
    if result["totals"]["disagreements"]:
        raise SystemExit("chain enumeration disagrees with weak compositions")
    TARGET.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["totals"]), result["elapsed_seconds"], "s")


if __name__ == "__main__":
    main()
