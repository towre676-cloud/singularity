#!/usr/bin/env python3
"""Catalogue the 29 non-vacuous connected types on 6 vertices (max deg <= 3):
structural features for naming, spanning polynomials, and the f-power at
which each enters the raw volume-6 identity."""
import json, sys
from itertools import combinations
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol6_lib import *
HERE = Path(__file__).resolve().parent
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)

def cycle_count_mask(mask, k, length):
    adj = [set() for _ in range(k)]
    for a, b in edges_of(mask, k): adj[a].add(b); adj[b].add(a)
    cnt = 0
    def dfs(start, v, path):
        nonlocal cnt
        if len(path) == length:
            if start in adj[v]: cnt += 1
            return
        for w in adj[v]:
            if w > start and w not in path: dfs(start, w, path + [w])
    for s in range(k): dfs(s, s, [s])
    return cnt // 2

def theta_params(mask, k):
    """If mask is a theta graph (exactly two vertices of degree 3, rest
    degree 2, bicyclic): return sorted path lengths between the two
    branch vertices, else None."""
    degs = degrees_of(mask, k)
    if sorted(degs) != [2, 2, 2, 2, 3, 3]: return None
    if len(edges_of(mask, k)) != k + 1: return None
    adj = [[] for _ in range(k)]
    for a, b in edges_of(mask, k): adj[a].append(b); adj[b].append(a)
    br = [v for v in range(k) if degs[v] == 3]
    u, v = br
    # three internally disjoint u-v paths: walk from u along each neighbour
    # not using the direct edge more than once; do DFS for simple paths
    paths = []
    def dfs(cur, target, path, used):
        if cur == target:
            paths.append(tuple(path)); return
        for w in adj[cur]:
            e = (min(cur, w), max(cur, w))
            if e in used or w in path[:-0] and w != target: continue
            if w in path and w != target: continue
            dfs(w, target, path + [w], used | {e})
    dfs(u, v, [u], set())
    # internally disjoint triples
    best = None
    for p1, p2, p3 in combinations(paths, 3):
        s1, s2, s3 = set(p1[1:-1]), set(p2[1:-1]), set(p3[1:-1])
        if not (s1 & s2) and not (s1 & s3) and not (s2 & s3):
            lens = tuple(sorted((len(p1) - 1, len(p2) - 1, len(p3) - 1)))
            if best is None or lens < best: best = lens
    return best

def core2(mask, k):
    """2-core: repeatedly delete vertices of degree <= 1; return
    (core vertex count, core edge count, core degree multiset)."""
    adj = {v: set() for v in range(k)}
    for a, b in edges_of(mask, k): adj[a].add(b); adj[b].add(a)
    alive = set(range(k))
    changed = True
    while changed:
        changed = False
        for v in list(alive):
            if len(adj[v] & alive) <= 1:
                alive.discard(v); changed = True
    e = sum(1 for a, b in edges_of(mask, k) if a in alive and b in alive)
    return len(alive), e, tuple(sorted((len(adj[v] & alive) for v in alive), reverse=True))

def leaves(mask, k):
    return sum(1 for d in degrees_of(mask, k) if d == 1)

out = {}
for t in CONN6:
    m = types[6][t]
    e = len(edges_of(m, 6))
    info = {
        "type_index": t, "mask": m, "describe": describe(m, 6),
        "edges": e, "f_power_in_raw": e,
        "degree_seq": sorted(degrees_of(m, 6), reverse=True),
        "triangles": tri_count(m, 6),
        "squares": cycle_count_mask(m, 6, 4),
        "pentagons": cycle_count_mask(m, 6, 5),
        "hexagons": cycle_count_mask(m, 6, 6),
        "bipartite": cycle_count_mask(m, 6, 3) == 0 and cycle_count_mask(m, 6, 5) == 0,
        "leaves": leaves(m, 6),
        "core2": core2(m, 6),
        "theta": theta_params(m, 6),
        "P_poly": {str(j): c for j, c in sorted(P_poly[(6, t)].items())},
        "aut": aut_count(m, 6),
    }
    out[describe(m, 6)] = info
    log(describe(m, 6), "| e", e, "tri", info["triangles"], "sq", info["squares"],
        "pent", info["pentagons"], "hex", info["hexagons"], "leaves", info["leaves"],
        "core2", info["core2"], "theta", info["theta"],
        "P", info["P_poly"])
(HERE / "vol6_types6.json").write_text(json.dumps(out, indent=1))
(HERE / "vol6_types6.log").write_text("\n".join(LOG) + "\n")
log("catalogued", len(out), "non-vacuous connected 6-types")
