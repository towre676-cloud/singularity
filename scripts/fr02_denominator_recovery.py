#!/usr/bin/env python3
"""Independent fixed-volume populations for the FR02 arithmetic decoder."""

from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations
import json
from math import comb
from pathlib import Path

from singularity.denominator_recovery import recover_degree_extremum, recovery_volume
from singularity.graph import Graph

ROOT = Path(__file__).resolve().parents[1]


def compositions(total: int, length: int):
    """Independent stars-and-bars oracle, not a decoder or transfer call."""
    for separators in combinations(range(total + length - 1), length - 1):
        stops = (-1,) + separators + (total + length - 1,)
        yield tuple(stops[i + 1] - stops[i] - 1 for i in range(length))


def coefficient(graph: Graph, q: Fraction, volume: int, shift: int = 0) -> Fraction:
    energies: Counter[int] = Counter()
    for heights in compositions(volume, graph.n):
        energy = sum((heights[u] - heights[v]) ** 2 for u, v in graph.edges)
        energy += shift * sum(height * height for height in heights)
        energies[energy] += 1
    return sum((count * q ** energy for energy, count in energies.items()), Fraction())


def all_graphs(max_order: int):
    for order in range(1, max_order + 1):
        edges = list(combinations(range(order), 2))
        for mask in range(1 << len(edges)):
            yield Graph(order, [edge for i, edge in enumerate(edges) if mask >> i & 1])


def multipartite(parts: list[int]) -> Graph:
    labels = [group for group, size in enumerate(parts) for _ in range(size)]
    return Graph(len(labels), ((u, v) for u, v in combinations(range(len(labels)), 2) if labels[u] != labels[v]))


def build_receipt() -> dict:
    pinnings = (Fraction(1, 2), Fraction(2, 3), Fraction(5, 6))
    graphs = checks = profile_evaluations = 0
    for graph in all_graphs(5):
        graphs += 1
        for q in pinnings:
            volume = recovery_volume(graph.n, q)
            for shift in (0, 2):
                value = coefficient(graph, q, volume, shift)
                decoded = recover_degree_extremum(graph.n, q, value, diagonal_shift=shift)
                expected = max(graph.degrees)
                if (decoded.maximum_degree, decoded.multiplicity) != (expected, graph.degrees.count(expected)):
                    raise AssertionError((graph.to_dict(), q, shift, decoded))
                checks += 1
                profile_evaluations += comb(graph.n + volume - 1, volume)
    examples = []
    for parts in ([1] * 12 + [3, 3], [2] * 9):
        graph = multipartite(parts)
        q = Fraction(1, 2)
        volume = recovery_volume(graph.n, q)
        value = coefficient(graph, q, volume)
        decoded = recover_degree_extremum(graph.n, q, value)
        examples.append({
            "multipartite_parts": parts,
            "coefficient_1": str(coefficient(graph, q, 1)),
            "coefficient_R": str(value),
            "profiles_at_R": comb(graph.n + volume - 1, volume),
            "decoded": decoded.to_dict(),
        })
    if examples[0]["coefficient_1"] != examples[1]["coefficient_1"]:
        raise AssertionError("the retained first-coefficient collision changed")
    return {
        "schema": "singularity.fr02-denominator-recovery/1",
        "series": "sum_h x^sum(h) q^(E_G(h)+lambda*sum(h_i^2))",
        "population": {"all_labeled_simple_graphs_through_order": 5, "graphs": graphs},
        "pinnings": [str(q) for q in pinnings],
        "diagonal_shifts": [0, 2],
        "exact_decoder_checks": checks,
        "profile_evaluations": profile_evaluations,
        "independent_oracle": "stars-and-bars separators, direct edge energy, exact rational evaluation",
        "first_coefficient_collision": examples,
        "scope": "maximum degree and multiplicity only; no general completeness or full-series collision claim",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "results/fr02_denominator_recovery.json"
    result = build_receipt()
    if args.check:
        retained = json.loads(target.read_text(encoding="utf-8"))
        if result != retained:
            raise SystemExit("FR02 retained receipt differs")
        print(f"FR02 checked {result['exact_decoder_checks']} exact recoveries on {result['population']['graphs']} graphs")
    else:
        target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(target)


if __name__ == "__main__":
    main()
