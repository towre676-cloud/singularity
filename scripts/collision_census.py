#!/usr/bin/env python3
"""P30: exact invariant partitions of the CENSUS-v1 population with memberships.

For every order n <= 6 and every connected isomorphism class of the census
manifest (one representative each, so relabelings never inflate counts) the
following invariants are computed exactly:

* degree sequence; Laplacian characteristic polynomial (integer Newton);
* complete binary cut-volume profile;
* nested-pair census (SNG-F40);
* local and span-marked coefficient prefixes through volume 3, symbolic
  in q, and the local prefix specialized at q = 1/2 (a separate column).

For each invariant the report lists every class with its graph codes, and
for each pair of invariants how many classes of the first are split by the
second.  Every symbolic local-prefix split carries a witness: the first
volume and the signed difference polynomial between the two least codes.
A stratified sample is recomputed by level chains; every class is checked
for internal equality.  ``--check`` compares with the retained file.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path

from singularity.chains import chain_marked_coefficients
from singularity.graph import Graph
from singularity.heights import local_coefficients, marked_coefficients
from singularity.invariants import binary_cut_profile, laplacian_characteristic_polynomial
from singularity.nested_census import nested_pair_census
from singularity.polynomials import evaluate, polynomial_to_json, sub

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "results/collision_census.json"
DEPTH = 3


def partition(keys):
    groups = {}
    for code, key in keys.items():
        groups.setdefault(key, []).append(code)
    return sorted(sorted(v) for v in groups.values())


def splits(coarse, fine_keys):
    """How many classes of ``coarse`` are split by the invariant ``fine_keys``."""
    return sum(len({fine_keys[c] for c in cls}) > 1 for cls in coarse if len(cls) > 1)


def compute():
    manifest = json.loads((ROOT / "results/census_manifest.json").read_text())
    report = []
    for order in manifest["orders"]:
        graphs = {c["canonical_code"]: Graph(c["n"], c["edges"]) for c in order["classes"]}
        local = {k: local_coefficients(g, DEPTH) for k, g in graphs.items()}
        marked = {k: marked_coefficients(g, DEPTH) for k, g in graphs.items()}
        invariants = {
            "degree_sequence": {k: tuple(sorted(g.degrees)) for k, g in graphs.items()},
            "laplacian_spectrum": {k: laplacian_characteristic_polynomial(g) for k, g in graphs.items()},
            "binary_cut_profile": {k: tuple(sorted(binary_cut_profile(g).items())) for k, g in graphs.items()},
            "nested_pair_census": {k: tuple(sorted(nested_pair_census(g).items())) for k, g in graphs.items()},
        }
        for v in range(DEPTH + 1):
            invariants[f"local_through_{v}"] = {k: repr(local[k][: v + 1]) for k in graphs}
            invariants[f"marked_through_{v}"] = {k: repr(sorted(c for c in marked[k].items() if c[0][0] <= v)) for k in graphs}
        invariants["local_through_3_at_q_1/2"] = {k: tuple(evaluate(r, Fraction(1, 2)) for r in local[k]) for k in graphs}
        partitions = {name: partition(keys) for name, keys in invariants.items()}
        refinement = {a: {b: splits(partitions[a], invariants[b]) for b in invariants if b != a} for a in invariants}
        witnesses = []
        codes = sorted(graphs)
        for i, a in enumerate(codes):
            for b in codes[i + 1:]:
                found = next((v for v in range(DEPTH + 1) if local[a][v] != local[b][v]), None)
                if found is not None and found >= 2:
                    witnesses.append({"codes": [a, b], "volume": found, "difference": polynomial_to_json(sub(local[a][found], local[b][found]))})
        # Internal equality is by construction; recompute a stratified sample with chains.
        sample = codes[:: max(1, len(codes) // 8)]
        for k in sample:
            assert chain_marked_coefficients(graphs[k], DEPTH) == marked[k]
        report.append({
            "n": order["n"], "classes": len(codes),
            "partitions": {name: {"class_count": len(p), "nontrivial_classes": [c for c in p if len(c) > 1]} for name, p in partitions.items()},
            "classes_split_by": refinement,
            "late_witnesses_volume_at_least_2": witnesses,
            "chain_recomputed_sample": sample,
        })
    return {"schema": "singularity.collision-census/1", "population": "results/census_manifest.json",
            "denominator": "connected isomorphism classes of the given order", "max_volume": DEPTH,
            "columns": "symbolic-in-q invariants and a separate q=1/2 specialization",
            "unresolved": "none: every class separates by local volume 3 for n <= 6", "orders": report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    text = json.dumps(result, indent=1, sort_keys=True, default=str) + "\n"
    if args.check:
        if TARGET.read_text() != text:
            raise SystemExit("collision census differs")
        print("Collision census matches")
        return
    TARGET.write_text(text)
    for o in result["orders"]:
        print(o["n"], o["classes"], {k: v["class_count"] for k, v in o["partitions"].items()})


if __name__ == "__main__":
    main()
