#!/usr/bin/env python3
"""P31: test the single-Whitney-twist relation on the late census collisions.

For every pair in results/late_collisions.json and each direction, every
two-vertex separator {s, t} of the first graph and every split of the
components of G - {s, t} into two nonempty sides is twisted (the edges from
one side to s and to t are exchanged) and compared with the second graph up
to isomorphism.  The receipt records the number of twists tried and whether
any reproduces the partner.  ``--check`` compares with the retained file.
"""
import argparse
from itertools import combinations, permutations
import json
from pathlib import Path

from singularity.graph import Graph

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "results/collision_cases.json"


def isomorphic(a: Graph, b: Graph) -> bool:
    if a.n != b.n or len(a.edges) != len(b.edges) or sorted(a.degrees) != sorted(b.degrees):
        return False
    target = set(b.edges)
    da, db = a.degrees, b.degrees
    for perm in permutations(range(a.n)):
        if all(da[v] == db[perm[v]] for v in range(a.n)) and \
                all(tuple(sorted((perm[u], perm[v]))) in target for u, v in a.edges):
            return True
    return False


def components(graph: Graph, removed: set) -> list[set]:
    seen, out = set(removed), []
    for v in range(graph.n):
        if v in seen:
            continue
        comp, stack = {v}, [v]
        seen.add(v)
        while stack:
            u = stack.pop()
            for w in graph.neighbors[u]:
                if w not in seen:
                    seen.add(w)
                    comp.add(w)
                    stack.append(w)
        out.append(comp)
    return out


def twists(graph: Graph):
    for s, t in combinations(range(graph.n), 2):
        comps = components(graph, {s, t})
        if len(comps) < 2:
            continue
        for k in range(1, len(comps)):
            for side_parts in combinations(range(len(comps)), k):
                side = set().union(*(comps[i] for i in side_parts))
                edges = []
                for u, v in graph.edges:
                    if (u in side and v in (s, t)) or (v in side and u in (s, t)):
                        inner, end = (u, v) if u in side else (v, u)
                        edges.append(tuple(sorted((inner, t if end == s else s))))
                    else:
                        edges.append((u, v))
                yield (s, t, sorted(side)), Graph(graph.n, edges)


def compute():
    data = json.loads((ROOT / "results/late_collisions.json").read_text())
    rows = []
    for pair in data["pairs"]:
        g = [Graph(x["n"], x["edges"]) for x in pair["graphs"]]
        tried, hits = 0, []
        for first, second in ((g[0], g[1]), (g[1], g[0])):
            for where, twisted in twists(first):
                tried += 1
                if isomorphic(twisted, second):
                    hits.append(where)
        rows.append({"codes": pair["codes"], "twists_tried": tried, "twist_reproduces_partner": bool(hits)})
    return {"schema": "singularity.collision-cases/1", "source": "results/late_collisions.json",
            "test": "single Whitney twist at a two-vertex separator, both directions", "pairs": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    text = json.dumps(result, indent=1, sort_keys=True) + "\n"
    if args.check:
        if TARGET.read_text() != text:
            raise SystemExit("collision cases differ")
        print("Collision cases match")
        return
    TARGET.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
