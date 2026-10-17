#!/usr/bin/env python3
"""Measure exact low-volume path transfer and check independent marginals.

Run ``python scripts/benchmark_transfer.py`` from a checkout. Mathematical
counts are reproducible; elapsed seconds are environment measurements, never
CI correctness thresholds. No full bounded-height cube is enumerated.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from math import comb
from pathlib import Path
import platform
import sys
from time import perf_counter

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from singularity.graph import Graph  # noqa: E402
from singularity.transfer import bounded_height_histogram  # noqa: E402


def independent_volume_count(vertices: int, height_bound: int, volume: int) -> int:
    """[x^volume](1+x+...+x^H)^n by inclusion-exclusion, without graph DP."""
    step = height_bound + 1
    return sum(
        (-1) ** j * comb(vertices, j) * comb(volume - step * j + vertices - 1, vertices - 1)
        for j in range(min(vertices, volume // step) + 1)
    )


def run_benchmark() -> dict:
    cases = []
    for vertices in (24, 48, 96):
        height_bound, max_volume = 2, 12
        graph = Graph(vertices, [(i, i + 1) for i in range(vertices - 1)])
        started = perf_counter()
        histogram = bounded_height_histogram(graph, height_bound, max_volume=max_volume, min_zero=True)
        elapsed = perf_counter() - started
        marginals = []
        for volume in range(max_volume + 1):
            observed = sum(count for (v, _), count in histogram.items() if v == volume)
            expected = independent_volume_count(vertices, height_bound, volume)
            if observed != expected:
                raise ArithmeticError(f"independent marginal mismatch: n={vertices}, volume={volume}")
            marginals.append({"volume": volume, "transfer_count": observed, "independent_count": expected})
        cases.append({
            "graph": "path", "vertices": vertices, "edges": vertices - 1,
            "height_bound": height_bound, "max_volume": max_volume, "min_zero": True,
            "normalization_note": "The volume budget is smaller than vertex count, so every retained profile has minimum zero.",
            "labeled_profiles_retained": sum(histogram.values()),
            "joint_volume_energy_cells": len(histogram),
            "complete_bounded_cube_size_not_enumerated": (height_bound + 1) ** vertices,
            "elapsed_seconds_environment_measurement": elapsed,
            "independent_marginals": marginals,
            "all_marginals_match": True,
        })
    return {
        "format": "singularity.transfer_benchmark/1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(), "platform": platform.platform(),
        "method": "Exact bounded-height forest messages with volume pruning; no assignment sampling.",
        "oracle": "For every retained volume v, compare sum_e C(v,e) to sum_j (-1)^j binom(n,j) binom(v-(H+1)j+n-1,n-1).",
        "timing_policy": "Elapsed seconds describe this run only. Correctness checks never assert a runtime threshold.",
        "scope": "Only profiles of total height at most 12 are counted. Counts are not the entire bounded-height cube.",
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPOSITORY / "results" / "transfer_benchmark.json")
    parser.add_argument("--stdout", action="store_true")
    arguments = parser.parse_args(argv)
    report = run_benchmark()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if arguments.stdout:
        print(json.dumps(report, indent=2))
    else:
        print(arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
