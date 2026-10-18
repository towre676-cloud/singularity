#!/usr/bin/env python3
"""P27 receipt: certified enclosures of K_{G,H}(s, 1/2) for the reference pairs (SNG-F38).

Each run keeps every prime up to N^b exactly, encloses each normalized local
factor on a checked decomposition, and bounds the omitted primes with the
coefficient-aware constant.  The exact dyadic endpoints are the result;
floats are summaries.  ``--check`` recomputes and compares every field except
elapsed time.  Runtime is several minutes in pure Python.
"""
import argparse
import json
from fractions import Fraction
from pathlib import Path
import platform
import time

from singularity.certified import certified_k
from singularity.examples import GRAPHS
from singularity.graph import Graph

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "results/certified_k.json"
CUBE = Graph(8, ((i, i ^ (1 << b)) for i in range(8) for b in range(3) if i < i ^ (1 << b)))
MOBIUS = Graph(8, tuple((i, (i + 1) % 8) for i in range(8)) + tuple((i, i + 4) for i in range(4)))
RUNS = [
    ("spectral", "spectral_g", "spectral_h", 1, 2, 100),
    ("spectral", "spectral_g", "spectral_h", 3, 5, 6),
    ("spectral", "spectral_g", "spectral_h", 1, 1, 1000),
    ("binary_census", "binary_g", "binary_h", 1, 3, 30),
]


def compute(partial=None):
    records = []
    for name, left, right, a, b, n_root in RUNS:
        started = time.perf_counter()
        record = certified_k(GRAPHS[left], GRAPHS[right], Fraction(1, 2), a, b, n_root)
        record.update({"pair": name, "elapsed_seconds": round(time.perf_counter() - started, 1)})
        records.append(record)
        print(name, record["s"], record["k_interval"], flush=True)
        if partial is not None:
            partial(records)
    return {"schema": "singularity.certified-k/1", "theorem": "SNG-F38", "q": "1/2",
            "python": platform.python_version(), "runs": records,
            "interpretation": "rigorous enclosures; the singularity exponent delta at s=1/r is proved by SNG-A11, not fitted"}


def strip(record):
    return {k: v for k, v in record.items() if k not in {"elapsed_seconds", "python"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    def save(records):
        TARGET.write_text(json.dumps({"schema": "singularity.certified-k/1", "complete": False, "runs": records}, indent=2, sort_keys=True) + "\n")

    result = compute(None if args.check else save)
    if args.check:
        retained = json.loads(TARGET.read_text())
        if [strip(r) for r in retained["runs"]] != [strip(r) for r in result["runs"]]:
            raise SystemExit("certified K enclosures differ from retained output")
        print("certified K enclosures match")
        return
    TARGET.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
