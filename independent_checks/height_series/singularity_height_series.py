"""Independent height-series calculator for Singularity's L_G(x, q).

Definition used (from the Singularity README):
    L_G(x, q) = sum_{h in N^{V(G)}} x^{sum_v h_v} q^{sum_{uv in E(G)} (h_u - h_v)^2}
So the coefficient of x^n q^e is the number of labelled height
assignments with total volume n and squared-edge energy e.

Graphs compared here:
- Cube Q3: vertices {0,1}^3, edges differ in exactly one coordinate.
  This is bipartite, cubic, 8 vertices, 12 edges, 6 square faces.
- Mobius ladder M8: vertices 0..7, cycle edges (i, i+1 mod 8) plus
  diameter edges (i, i+4 mod 8) for i = 0..3. This is cubic,
  8 vertices, 12 edges, non-bipartite (it contains 5-cycles such as
  0-1-2-3-4-0), and has 4 squares in the sense counted by the
  repository. It is NOT isomorphic to the cube: bipartiteness alone
  distinguishes them, and the height series below distinguishes
  them at volume 4 even without using bipartiteness directly.

Method: exact enumeration of all assignments with a given total
volume, for volumes up to a bound given on the command line.
Enumeration is by recursion over vertices, so counts are exact
integers, not floating approximations and not sampled estimates.

What this is NOT: it is not a proof of general reconstruction,
and it does not claim that the height series alone reconstructs
every graph. It is a computed, independently checkable instance
showing the first separation volume and the exact discrepancy
polynomial at that volume, which is the kind of finite evidence
that a reconstruction theorem for a restricted class would build on.
"""

import json
import pathlib
import sys
from collections import Counter


def cube_edges():
    verts = [(a, b, c) for a in (0, 1) for b in (0, 1) for c in (0, 1)]
    index = {v: i for i, v in enumerate(verts)}
    edges = []
    for v in verts:
        for k in range(3):
            w = list(v)
            w[k] ^= 1
            w = tuple(w)
            if index[v] < index[w]:
                edges.append((index[v], index[w]))
    return edges


def mobius_edges():
    edges = set()
    for i in range(8):
        a, b = i, (i + 1) % 8
        edges.add((min(a, b), max(a, b)))
    for i in range(4):
        a, b = i, i + 4
        edges.add((a, b))
    return sorted(edges)


def count_cycles(edges, length):
    """Count simple cycles of a given length, as sets of vertices
    in cyclic order, divided by the usual 2*length symmetries.
    Only used for the square-count sanity check (length 4)."""
    adj = {i: set() for i in range(8)}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    cycles = set()
    # Enumerate closed walks with distinct vertices, starting at the
    # smallest vertex, and canonicalise by rotation/reversal.
    def dfs(start, current, path, visited):
        if len(path) == length:
            if start in adj[current]:
                # canonical form: rotate so smallest is first, take
                # the lexicographically smaller of the two directions
                cyc = tuple(path)
                rev = (cyc[0],) + tuple(reversed(cyc[1:]))
                # rotations
                def rotations(t):
                    return [tuple(t[i:] + t[:i]) for i in range(len(t))]
                canon = min(rotations(cyc) + rotations(rev))
                cycles.add(canon)
            return
        for nxt in adj[current]:
            if nxt not in visited:
                dfs(start, nxt, path + [nxt], visited | {nxt})
    for s in range(8):
        dfs(s, s, [s], {s})
    return len(cycles)


def height_series(edges, max_volume):
    """Return dict volume -> Counter energy -> count."""
    n = 8
    # adjacency list with edge index, for incremental energy
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    result = {v: Counter() for v in range(max_volume + 1)}
    heights = [0] * n

    def rec(v, remaining, energy):
        if v == n - 1:
            # last vertex takes all remaining volume
            h = remaining
            e = energy
            for u in adj[v]:
                if u < v:
                    e += (h - heights[u]) ** 2
            heights[v] = h
            result[sum(heights)][e] += 1
            return
        for h in range(remaining + 1):
            e = energy
            for u in adj[v]:
                if u < v:
                    e += (h - heights[u]) ** 2
            heights[v] = h
            rec(v + 1, remaining - h, e)
        heights[v] = 0

    for volume in range(max_volume + 1):
        rec(0, volume, 0)
    return result


def main(max_volume=8):
    cube = cube_edges()
    mob = mobius_edges()
    print(f"cube edges={len(cube)} squares={count_cycles(cube, 4)}")
    print(f"mobius edges={len(mob)} squares={count_cycles(mob, 4)}")
    sc = height_series(cube, max_volume)
    sm = height_series(mob, max_volume)
    table = {}
    for v in range(max_volume + 1):
        dc = sc[v]
        dm = sm[v]
        energies = sorted(set(dc) | set(dm))
        diff = {e: dc.get(e, 0) - dm.get(e, 0) for e in energies if dc.get(e, 0) != dm.get(e, 0)}
        table[v] = {
            "total_cube": sum(dc.values()),
            "total_mobius": sum(dm.values()),
            "cube_by_energy": {str(e): dc[e] for e in sorted(dc)},
            "mobius_by_energy": {str(e): dm[e] for e in sorted(dm)},
            "difference_cube_minus_mobius": {str(e): d for e, d in sorted(diff.items())},
        }
        print(f"volume {v}: total cube={sum(dc.values())} mobius={sum(dm.values())} differ={bool(diff)}")
        if diff:
            print(f"  difference (cube - mobius) by energy: {diff}")
    out = pathlib.Path(__file__).resolve().parent / "singularity_height_series.json"
    with open(out, "w") as f:
        json.dump(table, f, indent=2)
    print("wrote singularity_height_series.json")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8)
