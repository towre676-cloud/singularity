#!/usr/bin/env python3
"""Exhaustive connected unlabeled census via all labeled graphs, n<=6.

This intentionally small independent baseline makes no claim of scalable
canonical labeling. Degree-respecting permutations are sufficient for an
exact isomorphism code because any isomorphism preserves degrees.
"""
from collections import defaultdict
from itertools import combinations, permutations, product
from pathlib import Path
import argparse
import json

from singularity.graph import Graph
from singularity.heights import local_coefficients, marked_coefficients
from singularity.invariants import binary_cut_profile


def canonical_code(graph):
    by_degree = defaultdict(list)
    for i, d in enumerate(graph.degrees):
        by_degree[d].append(i)
    choices = [tuple(permutations(by_degree[d])) for d in sorted(by_degree)]
    edge_set = set(graph.edges)
    best = None
    for blocks in product(*choices):
        order = sum(blocks, ())
        code = 0
        for new_i, new_j in combinations(range(graph.n), 2):
            code = (code << 1) | (tuple(sorted((order[new_i], order[new_j]))) in edge_set)
        if best is None or code < best:
            best = code
    return best


def connected_representatives(n):
    pairs = tuple(combinations(range(n), 2))
    representatives = {}
    connected_labeled = 0
    for mask in range(1 << len(pairs)):
        graph = Graph(n, (edge for j, edge in enumerate(pairs) if mask & (1 << j)))
        if not graph.connected:
            continue
        connected_labeled += 1
        code = canonical_code(graph)
        representatives.setdefault(code, graph)
    return connected_labeled, representatives


def census(max_order=6, max_volume=6):
    if not 1 <= max_order <= 6:
        raise ValueError("this exhaustive baseline explicitly supports orders 1..6")
    answer = {"schema": "singularity.small-census/1", "max_order": max_order,
              "max_volume": max_volume, "scope": "all labeled simple graphs, exact connectedness and degree-respecting isomorphism quotient", "orders": []}
    for n in range(1, max_order + 1):
        labeled, representatives = connected_representatives(n)
        binary_groups = defaultdict(list)
        local_groups = [defaultdict(list) for _ in range(max_volume + 1)]
        marked_groups = [defaultdict(list) for _ in range(max_volume + 1)]
        for code, graph in sorted(representatives.items()):
            binary = tuple(sorted(binary_cut_profile(graph).items()))
            binary_groups[binary].append(code)
            local = local_coefficients(graph, max_volume)
            marked = marked_coefficients(graph, max_volume)
            for m in range(max_volume + 1):
                key = tuple(tuple(sorted(row.items())) for row in local[:m+1])
                local_groups[m][key].append(code)
                mark = tuple(sorted((key, value) for key, value in marked.items() if key[0] <= m))
                marked_groups[m][mark].append(code)
        record = {
            "n": n, "connected_labeled_graphs": labeled, "connected_isomorphism_classes": len(representatives),
            "binary_census_classes": len(binary_groups),
            "local_classes_by_volume": [len(g) for g in local_groups],
            "marked_classes_by_volume": [len(g) for g in marked_groups],
            "remaining_local_collision_classes": [values for values in local_groups[-1].values() if len(values) > 1],
            "remaining_marked_collision_classes": [values for values in marked_groups[-1].values() if len(values) > 1],
            "graphs": [{"canonical_code": code, **graph.to_dict()} for code,graph in sorted(representatives.items())],
        }
        answer["orders"].append(record)
        print(f"n={n}: {labeled} connected labeled; {len(representatives)} isomorphism classes; local depth {max_volume}: {len(local_groups[-1])}; marked: {len(marked_groups[-1])}", flush=True)
    return answer


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-order', type=int, default=6)
    parser.add_argument('--max-volume', type=int, default=6)
    parser.add_argument('--output', default='results/small_census.json')
    args = parser.parse_args()
    result = census(args.max_order, args.max_volume)
    target = Path(args.output); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
