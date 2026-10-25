#!/usr/bin/env python3
"""Volume 5, phase 3: pattern identification, determination relations,
and the reduced formula verified on all agreeing pairs."""
import json, sys
from fractions import Fraction as Fr
from itertools import combinations
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol5_lib import *
import importlib.util
HERE = Path(__file__).resolve().parent
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)

def solve_span(basis_cols, target):
    n = len(target); cols = len(basis_cols)
    A = [[basis_cols[c][i] for c in range(cols)] + [target[i]] for i in range(n)]
    pivrow = {}; r = 0
    for c in range(cols):
        piv = next((i for i in range(r, n) if A[i][c] != 0), None)
        if piv is None: continue
        A[r], A[piv] = A[piv], A[r]
        pv = A[r][c]; A[r] = [x / pv for x in A[r]]
        for i in range(n):
            if i != r and A[i][c] != 0:
                f = A[i][c]; A[i] = [a - f * b for a, b in zip(A[i], A[r])]
        pivrow[c] = r; r += 1
        if r == n: break
    for i in range(r, n):
        if A[i][cols] != 0: return None
    sol = [Fr(0)] * cols
    for c, i in pivrow.items(): sol[c] = A[i][cols]
    return sol

# ---------- identify support patterns structurally ----------
def tri_of(mask, k):
    E = set(edges_of(mask, k)); c = 0
    for a, b, cc in combinations(range(k), 3):
        if (a, b) in E and (b, cc) in E and (a, cc) in E: c += 1
    return c
def sq_of(mask, k):
    return sub_count(mask_from_edges(4, [(0,1),(1,2),(2,3),(3,0)]), 4, mask, k)
def maxdeg(mask, k):
    d = [0] * k
    for (a, b) in edges_of(mask, k): d[a] += 1; d[b] += 1
    return max(d)

dec2 = json.loads((HERE / "vol5_decomp2.json").read_text())
support = {}
for j, a in dec2["alpha_P"].items():
    for desc in a: support.setdefault(desc, []).append(int(j))
out = {"support_patterns": {}}
for desc, js in sorted(support.items()):
    # recover mask from describe string m<mask>
    mask = int(desc.split("_m")[1]); k = 5
    out["support_patterns"][desc] = {
        "f_powers": js, "edges": len(edges_of(mask, k)),
        "triangles": tri_of(mask, k), "squares": sq_of(mask, k),
        "maxdeg": maxdeg(mask, k),
        "vacuous_in_cubic": maxdeg(mask, k) > 3}
    log(desc, "f_powers", js, "tri", tri_of(mask, k), "sq", sq_of(mask, k),
        "maxdeg", maxdeg(mask, k))

# ---------- load pools, recompute counts ----------
spec = importlib.util.spec_from_file_location("orig_ext", EXT / "singularity_extension.py")
orig = importlib.util.module_from_spec(spec); spec.loader.exec_module(orig)
data = json.loads((EXT / "singularity_extension.json").read_text())
pools = {}
for bn in ("n10", "n12"):
    blk = data["blocks"][bn]
    pools[bn] = (blk["n"], blk["named_graphs"] + blk["random_sample_records"])
sampled8, _ = orig.sample_records(8, 60, 20261024, "n8_g")
pools["n8"] = (8, [{"name": "cube_Q3", "edges": orig.cube_edges()},
                    {"name": "mobius_M8", "edges": orig.mobius_ladder(8)}] +
               [{"name": r["name"], "edges": r["edges"]} for r in sampled8])

graphs = {}
for bn, (n, recs) in pools.items():
    gs = []
    for r in recs:
        edges = sorted(set(tuple(sorted(e)) for e in r["edges"]))
        sc = induced_counts(n, edges)
        N = full_subgraph_counts(sc)
        S4 = {}
        for (k, t), s in sc.items():
            if k <= 4 and s and (k, t) in cumulants:
                for e, c in cumulants[(k, t)][5].items():
                    S4[e] = S4.get(e, Fr(0)) + s * c
        gs.append({"name": r["name"], "n": n, "N": N, "S4": S4})
    graphs[bn] = gs
    log(bn, len(gs), "graphs recomputed")

OLD = ["N3_triangle", "N4_square", "Ndia", "NK4"]
def oldkey(g):
    return (g["n"],) + tuple(g["N"][NAMED[o]] for o in OLD)

# ---------- check 1: size<=4 part S4 is a function of (n, old) ----------
bad = 0
seen = {}
for bn, gs in graphs.items():
    for g in gs:
        k = oldkey(g)
        v = {e: c for e, c in g["S4"].items() if c}
        if k in seen and seen[k] != v: bad += 1
        seen[k] = v
out["size_le4_part_determined_by_old"] = (bad == 0)
log("size<=4 part: collisions with different S4:", bad)

# ---------- check 2: the 11 four-vertex pattern count formulas ----------
# N_Y for the 11 patterns on 4 vertices as functions of (n, m, N3, N4, Ndia, NK4)
def pat4(k, edgelist): return find_pattern(k, mask_from_edges(k, edgelist))
P4 = {
    "empty": pat4(4, []),
    "one_edge": pat4(4, [(0, 1)]),
    "2K2": pat4(4, [(0, 1), (2, 3)]),
    "P3+iso": pat4(4, [(0, 1), (1, 2)]),
    "P4": pat4(4, [(0, 1), (1, 2), (2, 3)]),
    "K13": pat4(4, [(0, 1), (0, 2), (0, 3)]),
    "C3+iso": pat4(4, [(0, 1), (1, 2), (0, 2)]),
    "C4": NAMED['N4_square'],
    "paw": pat4(4, [(0, 1), (1, 2), (0, 2), (0, 3)]),
    "diamond": NAMED['Ndia'],
    "K4": NAMED['NK4'],
}
def formulas4(g):
    n = g["n"]; m = 3 * n // 2
    N3, N4, Nd, NK = (g["N"][NAMED[o]] for o in OLD)
    return {"empty": comb(n, 4), "one_edge": m * comb(n - 2, 2),
            "2K2": comb(m, 2) - 3 * n, "P3+iso": 3 * n * (n - 3),
            "P4": 4 * m - 3 * N3, "K13": n, "C3+iso": N3 * (n - 3),
            "C4": N4, "paw": 3 * N3, "diamond": Nd, "K4": NK}
bad4 = 0
for bn, gs in graphs.items():
    for g in gs:
        f = formulas4(g)
        for nm, pi in P4.items():
            if g["N"][pi] != f[nm]: bad4 += 1
out["four_vertex_pattern_formulas_hold"] = (bad4 == 0)
log("4-vertex pattern formula mismatches:", bad4)

# ---------- check 3: vacuous patterns are identically zero ----------
vac = [desc for desc, info in out["support_patterns"].items() if info["vacuous_in_cubic"]]
vac_pi = {}
for desc in vac:
    mask = int(desc.split("_m")[1]); vac_pi[desc] = pat_index[(5, type_id[5][mask])]
nonzero_vac = 0
for bn, gs in graphs.items():
    for g in gs:
        for desc, pi in vac_pi.items():
            if g["N"][pi] != 0: nonzero_vac += 1
out["vacuous_patterns_always_zero"] = (nonzero_vac == 0)
log("vacuous support patterns with nonzero count:", nonzero_vac)

# ---------- per-n determination fits for every support pattern ----------
support_pi = {}
for desc in support:
    mask = int(desc.split("_m")[1]); support_pi[desc] = pat_index[(5, type_id[5][mask])]
basis_names = ["const", "N3", "N4", "Ndia", "NK4", "N5", "NK23", "NTheta123"]
def basis_vec(g):
    return [Fr(1), Fr(g["N"][NAMED['N3_triangle']]), Fr(g["N"][NAMED['N4_square']]),
            Fr(g["N"][NAMED['Ndia']]), Fr(g["N"][NAMED['NK4']]),
            Fr(g["N"][NAMED['N5_pentagon']]), Fr(g["N"][NAMED['NK23']]),
            Fr(g["N"][NAMED['N_theta123']])]
fits = {}
for desc, pi in support_pi.items():
    if out["support_patterns"][desc]["vacuous_in_cubic"]: continue
    fits[desc] = {}
    for bn, gs in graphs.items():
        cols = list(zip(*[basis_vec(g) for g in gs]))
        sol = solve_span([list(c) for c in cols], [Fr(g["N"][pi]) for g in gs])
        fits[desc][bn] = None if sol is None else {basis_names[i]: str(sol[i])
                                                  for i in range(8) if sol[i] != 0}
    log(desc, "fits:", fits[desc])
out["support_pattern_fits"] = fits

# old-only fits
fits_old = {}
for desc, pi in support_pi.items():
    if out["support_patterns"][desc]["vacuous_in_cubic"]: continue
    fits_old[desc] = {}
    for bn, gs in graphs.items():
        cols = list(zip(*[[Fr(1), Fr(g["N"][NAMED['N3_triangle']]),
                            Fr(g["N"][NAMED['N4_square']]), Fr(g["N"][NAMED['Ndia']]),
                            Fr(g["N"][NAMED['NK4']])] for g in gs]))
        sol = solve_span([list(c) for c in cols], [Fr(g["N"][pi]) for g in gs])
        fits_old[desc][bn] = None if sol is None else [str(x) for x in sol]
out["support_pattern_fits_old_only"] = fits_old

(HERE / "vol5_relations.json").write_text(json.dumps(out, indent=1))
(HERE / "vol5_relations.log").write_text("\n".join(LOG) + "\n")
log("wrote vol5_relations.json")
