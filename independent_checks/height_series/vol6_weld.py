#!/usr/bin/env python3
"""Volume 6: weld constructions.  A 'unit' is a 6-vertex graph with
exactly two degree-2 vertices (K3,3-e, prism minus a triangle edge,
prism minus a spoke).  A ring of >=2 units joined by bridges between
consecutive units' degree-2 vertices is a connected cubic graph, and
every I5 pattern (all 2-connected) lies inside one unit, so I5 is
additive over units as long as inter-unit cycles have length >= 6
(they have length >= 8 here).  Search ring sums against
component (+) block combinations for an agreeing pair with a K3,3
component on one side only."""
import json, sys
from fractions import Fraction as Fr
from itertools import combinations_with_replacement
from math import comb
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol6_lib import *
HERE = Path(__file__).resolve().parent
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)

INV5 = ['N3_triangle', 'N4_square', 'Ndia', 'NK4',
        'N5_pentagon', 'NK23', 'N_theta123', 'NK23_plus_e']
def counts_of(n, edges):
    s = induced_counts(n, edges, 6)
    return subgraph_counts_all(s)
def inv5(N): return tuple(N.get(NAMED[nm], 0) for nm in INV5)
def add_i5(a, b): return tuple(x + y for x, y in zip(a, b))
def shift_ed(edges, off): return [(u + off, v + off) for (u, v) in edges]

pm_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["Nprism"]][0]
km_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["NK33"]][0]
t2012 = [t for t in ctypes[6] if types[6][t] == 2012][0]
t1916 = [t for t in ctypes[6] if types[6][t] == 1916][0]
t5941 = [t for t in ctypes[6] if types[6][t] == 5941][0]

def deg2_vertices(mask):
    deg = [0] * 6
    for (u, v) in edges_of(mask, 6):
        deg[u] += 1; deg[v] += 1
    return [v for v in range(6) if deg[v] == 2]

UNITS = {"K33-e": types[6][km_t] if False else types[6][t2012],
         "prism-tri": types[6][t1916], "prism-spoke": types[6][t5941]}
unit_info = {}
for nm, mask in UNITS.items():
    ed = edges_of(mask, 6)
    d2 = deg2_vertices(mask)
    assert len(d2) == 2, (nm, d2)
    N = counts_of(6, ed)
    unit_info[nm] = {"edges": ed, "d2": d2, "I5": inv5(N), "N": N}
    log("unit", nm, "I5 =", inv5(N), "deg2:", d2)

def ring_edges(unit_names):
    """Ring of units: unit i occupies vertices 6i..6i+5; bridges join
    d2[1] of unit i to d2[0] of unit i+1 (cyclically), with the A/B-side
    alternation chosen consistently for the bipartite unit; for prism
    units any consistent choice gives a cubic graph (checked)."""
    ed = []
    k = len(unit_names)
    for i, nm in enumerate(unit_names):
        ed += shift_ed(unit_info[nm]["edges"], 6 * i)
    for i in range(k):
        j = (i + 1) % k
        a = 6 * i + unit_info[unit_names[i]]["d2"][1]
        b = 6 * j + unit_info[unit_names[j]]["d2"][0]
        ed.append((a, b))
    return ed

# verify additivity on one example: ring(K33-e, K33-e) I5 == 2*u
ed2 = ring_edges(["K33-e", "K33-e"])
N2 = counts_of(12, ed2)
log("ring(2x K33-e) I5 =", inv5(N2), "vs 2u =", tuple(2 * x for x in unit_info["K33-e"]["I5"]))
assert inv5(N2) == tuple(2 * x for x in unit_info["K33-e"]["I5"])

rings = {}   # (n, I5) -> (desc, edges)
unit_names = list(UNITS)
for k in (2, 3, 4):
    for combo in combinations_with_replacement(unit_names, k):
        ed = ring_edges(list(combo))
        n = 6 * k
        i5 = inv5(counts_of(n, ed))
        # sanity: additive?
        s = unit_info[combo[0]]["I5"]
        tot = s
        for nm in combo[1:]: tot = add_i5(tot, unit_info[nm]["I5"])
        assert i5 == tot, (combo, i5, tot)
        rings.setdefault((n, i5), ("ring(" + ",".join(combo) + ")", ed))
log("rings built:", len(rings))

# blocks: all pools + library comps
res = json.loads((HERE / "vol6_results.json").read_text())
pools2 = json.loads((HERE / "vol6_pools2.json").read_text())
pools3 = json.loads((HERE / "vol6_pools3.json").read_text())
blocks = []
for bn, grec in res["graphs"].items():
    for g in grec:
        N = {int(pi): v for pi, v in g["N"].items()}
        blocks.append((f"{bn}:{g['name']}", g["n"], [tuple(e) for e in g["edges"]],
                       tuple(N.get(NAMED[x], 0) for x in INV5)))
for src in (pools2, pools3):
    for bn, grec in src.items():
        n = int(bn[1:])
        for g in grec:
            blocks.append((f"{bn}:{g['name']}", n, [tuple(e) for e in g["edges"]], tuple(g["I5"])))
K33_ed = edges_of(types[6][km_t], 6)
PRISM_ed = edges_of(types[6][pm_t], 6)
K33_I5 = inv5(counts_of(6, K33_ed)); PRISM_I5 = inv5(counts_of(6, PRISM_ed))

# B-side candidates: rings alone, rings (+) one block, blocks alone
from collections import defaultdict
B = defaultdict(list)
for (lab, n, ed, i5) in blocks:
    B[(n, i5)].append((lab, ed))
for (n, i5), (desc, ed) in rings.items():
    B[(n, i5)].append((desc, ed))
for (n, i5), (desc, ed) in list(rings.items()):
    for (lab, n2, ed2, i52) in blocks:
        if n + n2 > 30: continue
        B[(n + n2, add_i5(i5, i52))].append((f"{desc}+{lab}", ed + shift_ed(ed2, n)))
log("B candidates:", sum(len(v) for v in B.values()))

def psub(A, Bq):
    out = dict(A)
    for e, c in Bq.items():
        out[e] = out.get(e, Fr(0)) - c
        if out[e] == 0: del out[e]
    return out
def kappa6(j):
    return {6 - 2 * j + 2 * i: Fr(comb(6 + j, i)) * (-1) ** i for i in range(6 + j + 1)}
def fterms(NA, NB, termset):
    tot = {}
    for t in termset:
        pi = pat_index[(6, t)]
        dv = NB.get(pi, 0) - NA.get(pi, 0)
        if dv:
            j = bin(types[6][t]).count("1") - 6
            for e, c in kappa6(j).items():
                tot[e] = tot.get(e, Fr(0)) + dv * c
    return {e: c for e, c in tot.items() if c}

out_pairs = []
def test_pair(A_desc, A_n, A_ed, B_desc, B_ed):
    LA = height_series_fast(A_n, A_ed, 6); NA = counts_of(A_n, A_ed)
    LB = height_series_fast(A_n, B_ed, 6); NB = counts_of(A_n, B_ed)
    assert inv5(NA) == inv5(NB)
    agree5 = all(LA[r] == LB[r] for r in range(1, 6))
    dL6 = psub(LB[6], LA[6])
    NEW8 = [t for t in ctypes[6] if types[6][t] in (1880, 1881, 956, 1884, 5907, 1916, 5948, 5941)]
    variants = {"reduced8": NEW8, "reduced8+f3": NEW8 + [km_t, pm_t],
                "reduced8+f2_m2012": NEW8 + [t2012],
                "full": NEW8 + [km_t, pm_t] + [t2012], "raw_all_conn6": list(CONN6)}
    verdict = {vn: (fterms(NA, NB, ts) == dL6) for vn, ts in variants.items()}
    dN = {}
    for t in CONN6:
        pi = pat_index[(6, t)]
        dv = NB.get(pi, 0) - NA.get(pi, 0)
        if dv: dN[describe(types[6][t], 6)] = dv
    out_pairs.append({"A": A_desc, "B": B_desc, "agree_through_5": agree5,
                      "verdicts": verdict, "dN_conn6": dN})
    log(f"PAIR {A_desc} vs {B_desc} | agree<=5: {agree5} | {verdict}")
    log("   dN:", dN)

made = 0
# A-side: K33 (+) block, K33 (+) ring, K33+prism (+) block
A_sides = []
for (lab, n, ed, i5) in blocks:
    A_sides.append((f"K33+{lab}", n + 6, K33_ed + shift_ed(ed, 6), add_i5(K33_I5, i5)))
for (n, i5), (desc, ed) in rings.items():
    A_sides.append((f"K33+{desc}", n + 6, K33_ed + shift_ed(ed, 6), add_i5(K33_I5, i5)))
for (lab, n, ed, i5) in blocks:
    if n + 12 > 30: continue
    A_sides.append((f"K33+prism+{lab}", n + 12,
                    K33_ed + shift_ed(PRISM_ed, 6) + shift_ed(ed, 12),
                    add_i5(add_i5(K33_I5, PRISM_I5), i5)))
for (adesc, an, aed, ai5) in A_sides:
    if made >= 4: break
    for (bdesc, bed) in B.get((an, ai5), []):
        # skip if B contains a K33 component by construction (desc check
        # is insufficient; rely on count check below)
        NB = counts_of(an, bed)
        NA = counts_of(an, aed)
        if NB.get(pat_index[(6, km_t)], 0) != 0: continue
        if NA.get(pat_index[(6, km_t)], 0) == 0: continue
        test_pair(adesc, an, aed, bdesc, bed)
        made += 1
        break
log("weld pairs tested:", made)
(HERE / "vol6_weld.json").write_text(json.dumps({"pairs": out_pairs}, indent=1, default=str))
(HERE / "vol6_weld.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_weld.json")
