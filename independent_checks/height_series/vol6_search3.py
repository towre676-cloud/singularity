#!/usr/bin/env python3
"""Volume 6, component-balance phase 3: meet-in-the-middle matching.
A = C (+) X (C a saturated component K3,3 or prism, X any pool block or
library graph), B = any single block, pair of small blocks, or the other
component (+) block, with I5(B) = I5(A) exactly.  Every matched pair gets
the full formula-variant test."""
import json, sys
from fractions import Fraction as Fr
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
def psub(A, B):
    out = dict(A)
    for e, c in B.items():
        out[e] = out.get(e, Fr(0)) - c
        if out[e] == 0: del out[e]
    return out
def full_data(n, edges):
    L = height_series_fast(n, edges, 6)
    s = induced_counts(n, edges, 6)
    return {"n": n, "edges": edges, "L": L, "N": subgraph_counts_all(s)}
def inv5(N): return tuple(N.get(NAMED[nm], 0) for nm in INV5)
def kappa6(j):
    return {6 - 2 * j + 2 * i: Fr(comb(6 + j, i)) * (-1) ** i for i in range(6 + j + 1)}
def formula_terms(NA, NB, termset):
    tot = {}
    for t in termset:
        pi = pat_index[(6, t)]
        d = NB.get(pi, 0) - NA.get(pi, 0)
        if d:
            j = bin(types[6][t]).count("1") - 6
            for e, c in kappa6(j).items():
                tot[e] = tot.get(e, Fr(0)) + d * c
    return {e: c for e, c in tot.items() if c}

pm_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["Nprism"]][0]
km_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["NK33"]][0]
def lib_i5(n, ed):
    s = induced_counts(n, ed, 5)
    return inv5(subgraph_counts_all(s))
LIB = {"K4": (4, [(i, j) for i in range(4) for j in range(i + 1, 4)]),
       "K33": (6, edges_of(types[6][km_t], 6)),
       "prism": (6, edges_of(types[6][pm_t], 6)),
       "cube": (8, [(i, j) for i in range(8) for j in range(i + 1, 8) if bin(i ^ j).count("1") == 1]),
       "M8": (8, [(i, (i + 1) % 8) for i in range(8)] + [(i, i + 4) for i in range(4)]),
       "petersen": (10, [(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)]
                    + [(5 + i, 5 + (i + 2) % 5) for i in range(5)])}
for nm, (n, ed) in LIB.items():
    log("library", nm, "I5 =", lib_i5(n, ed))

res = json.loads((HERE / "vol6_results.json").read_text())
pools2 = json.loads((HERE / "vol6_pools2.json").read_text())
blocks = []   # (label, n, edges, I5)
for bn, grec in res["graphs"].items():
    for g in grec:
        N = {int(pi): v for pi, v in g["N"].items()}
        blocks.append((f"{bn}:{g['name']}", g["n"], [tuple(e) for e in g["edges"]],
                       tuple(N.get(NAMED[x], 0) for x in INV5)))
for bn, grec in pools2.items():
    n = int(bn[1:])
    for g in grec:
        blocks.append((f"{bn}:{g['name']}", n, [tuple(e) for e in g["edges"]], tuple(g["I5"])))
for nm, (n, ed) in LIB.items():
    blocks.append((f"lib:{nm}", n, ed, lib_i5(n, ed)))
log("blocks:", len(blocks))

def shift_ed(edges, off): return [(u + off, v + off) for (u, v) in edges]
def add_i5(a, b): return tuple(x + y for x, y in zip(a, b))

out_pairs = []
def test_pair(A_desc, A_n, A_ed, B_desc, B_n, B_ed):
    A = full_data(A_n, A_ed); B = full_data(B_n, B_ed)
    assert inv5(A["N"]) == inv5(B["N"]), f"I5 mismatch {A_desc} vs {B_desc}"
    agree5 = all(A["L"][r] == B["L"][r] for r in range(1, 6))
    dL6 = psub(B["L"][6], A["L"][6])
    NEW8 = [t for t in ctypes[6] if types[6][t] in (1880, 1881, 956, 1884, 5907, 1916, 5948, 5941)]
    t2012 = [t for t in ctypes[6] if types[6][t] == 2012][0]
    variants = {"reduced8": NEW8, "reduced8+f3": NEW8 + [km_t, pm_t],
                "reduced8+f2_m2012": NEW8 + [t2012],
                "full": NEW8 + [km_t, pm_t] + [t2012], "raw_all_conn6": list(CONN6)}
    verdict = {vn: (formula_terms(A["N"], B["N"], ts) == dL6) for vn, ts in variants.items()}
    dN = {}
    for t in CONN6:
        pi = pat_index[(6, t)]
        d = B["N"].get(pi, 0) - A["N"].get(pi, 0)
        if d: dN[describe(types[6][t], 6)] = d
    out_pairs.append({"A": A_desc, "B": B_desc, "agree_through_5": agree5,
                      "dL6_nonzero": bool(dL6), "verdicts": verdict, "dN_conn6": dN})
    log(f"PAIR {A_desc} vs {B_desc} | agree<=5: {agree5} | dL6!=0: {bool(dL6)} | {verdict}")
    log("   dN:", dN)

# B-side index per total n with provenance (multiset of block indices),
# so trivial rearrangements of A can be excluded exactly.
from collections import defaultdict
lib_idx = {}
for idx, (lab, n, ed, i5) in enumerate(blocks):
    if lab.startswith("lib:"): lib_idx[lab[4:]] = idx
B_index = defaultdict(dict)   # N -> I5 -> (desc, n, edges, multiset)
for idx, (lab, n, ed, i5) in enumerate(blocks):
    B_index[n].setdefault(i5, (lab, n, ed, (idx,)))
small_idx = [i for i, b in enumerate(blocks) if b[1] <= 12]
for a, i in enumerate(small_idx):
    (l1, n1, e1, i1) = blocks[i]
    for j in small_idx[a:]:
        (l2, n2, e2, i2) = blocks[j]
        N = n1 + n2
        if N > 24: continue
        B_index[N].setdefault(add_i5(i1, i2), (f"{l1}+{l2}", N, e1 + shift_ed(e2, n1), tuple(sorted((i, j)))))
for cname in ("K33", "prism"):
    cn, ced = LIB[cname]
    ci5 = lib_i5(cn, ced)
    for idx, (lab, n, ed, i5) in enumerate(blocks):
        N = n + cn
        if N > 24: continue
        B_index[N].setdefault(add_i5(ci5, i5),
                              (f"{cname}+{lab}", N, ced + shift_ed(ed, cn),
                               tuple(sorted((lib_idx[cname], idx)))))
log("B-side index sizes:", {N: len(d) for N, d in sorted(B_index.items())})

made = {"K33": 0, "prism": 0}
for cname in ("K33", "prism"):
    cn, ced = LIB[cname]
    ci5 = lib_i5(cn, ced)
    for idx, (lab, n, ed, i5) in enumerate(blocks):
        N = n + cn
        if N > 24 or made[cname] >= 3: continue
        tgt = add_i5(ci5, i5)
        hit = B_index[N].get(tgt)
        if hit is None: continue
        if hit[3] == tuple(sorted((lib_idx[cname], idx))): continue  # A itself
        A_ed = ced + shift_ed(ed, cn)
        test_pair(f"{cname}+{lab}", N, A_ed, hit[0], hit[1], hit[2])
        made[cname] += 1
log("pairs made:", made)
(HERE / "vol6_search3.json").write_text(json.dumps({"pairs": out_pairs, "made": made}, indent=1, default=str))
(HERE / "vol6_search3.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_search3.json")
