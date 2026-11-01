#!/usr/bin/env python3
"""Volume 6, component-balance phase 4 (final design):
A = C (+) X with C in {K3,3, prism} and X a block or a pair of small
blocks; B ranges over singles, pairs of small blocks, and library-comp
(+) block representatives.  A pair is only height-tested when the cheap
count check shows it is INTERESTING: Delta N != 0 for at least one of
K3,3 / prism / K3,3-e.  This filters out the isomorphism-duplicate
pairs that swamped phases 2-3."""
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
def counts_of(n, edges):
    s = induced_counts(n, edges, 6)
    return subgraph_counts_all(s)
def full_data(n, edges):
    L = height_series_fast(n, edges, 6)
    return {"n": n, "edges": edges, "L": L, "N": counts_of(n, edges)}
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
t2012 = [t for t in ctypes[6] if types[6][t] == 2012][0]
piK33, piPrism, pi2012 = pat_index[(6, km_t)], pat_index[(6, pm_t)], pat_index[(6, t2012)]
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
compN = {nm: counts_of(n, ed) for nm, (n, ed) in LIB.items()}
for nm in LIB: log("library", nm, "I5 =", inv5(compN[nm]))

res = json.loads((HERE / "vol6_results.json").read_text())
pools2 = json.loads((HERE / "vol6_pools2.json").read_text())
blocks = []
for bn, grec in res["graphs"].items():
    for g in grec:
        N = {int(pi): v for pi, v in g["N"].items()}
        blocks.append((f"{bn}:{g['name']}", g["n"], [tuple(e) for e in g["edges"]],
                       tuple(N.get(NAMED[x], 0) for x in INV5)))
for bn, grec in pools2.items():
    n = int(bn[1:])
    for g in grec:
        blocks.append((f"{bn}:{g['name']}", n, [tuple(e) for e in g["edges"]], tuple(g["I5"])))
lib_idx = {}
for nm, (n, ed) in LIB.items():
    blocks.append((f"lib:{nm}", n, ed, inv5(compN[nm])))
    lib_idx[nm] = len(blocks) - 1
log("blocks:", len(blocks))
def shift_ed(edges, off): return [(u + off, v + off) for (u, v) in edges]
def add_i5(a, b): return tuple(x + y for x, y in zip(a, b))

# ---- B-side: up to 6 distinct-multiset representatives per (N, I5) ----
from collections import defaultdict
B_index = defaultdict(lambda: defaultdict(list))
def add_B(N, i5, desc, ed, mult):
    lst = B_index[N][i5]
    if all(e[3] != mult for e in lst) and len(lst) < 6:
        lst.append((desc, N, ed, mult))
for idx, (lab, n, ed, i5) in enumerate(blocks):
    add_B(n, i5, lab, ed, (idx,))
small_idx = [i for i, b in enumerate(blocks) if b[1] <= 12]
for a, i in enumerate(small_idx):
    (l1, n1, e1, i1) = blocks[i]
    for j in small_idx[a:]:
        (l2, n2, e2, i2) = blocks[j]
        if n1 + n2 > 24: continue
        add_B(n1 + n2, add_i5(i1, i2), f"{l1}+{l2}", e1 + shift_ed(e2, n1), tuple(sorted((i, j))))
for cname, (cn, ced) in LIB.items():
    ci5 = inv5(compN[cname])
    for idx, (lab, n, ed, i5) in enumerate(blocks):
        if n + cn > 24: continue
        add_B(n + cn, add_i5(ci5, i5), f"{cname}+{lab}", ced + shift_ed(ed, cn),
              tuple(sorted((lib_idx[cname], idx))))
log("B-side ready:", {N: sum(len(v) for v in d.values()) for N, d in sorted(B_index.items())})

out_pairs = []
def test_pair(A_desc, A_n, A_ed, B_desc, B_ed):
    A = full_data(A_n, A_ed); B = full_data(A_n, B_ed)
    assert inv5(A["N"]) == inv5(B["N"])
    agree5 = all(A["L"][r] == B["L"][r] for r in range(1, 6))
    dL6 = psub(B["L"][6], A["L"][6])
    NEW8 = [t for t in ctypes[6] if types[6][t] in (1880, 1881, 956, 1884, 5907, 1916, 5948, 5941)]
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

def interesting(NA, NB):
    return (NB.get(piK33, 0) - NA.get(piK33, 0) != 0 or
            NB.get(piPrism, 0) - NA.get(piPrism, 0) != 0 or
            NB.get(pi2012, 0) - NA.get(pi2012, 0) != 0)

def add_N(*dicts):
    out = {}
    for d in dicts:
        for k, v in d.items(): out[k] = out.get(k, 0) + v
    return out
_Ncache = {}
def block_N(idx):
    if idx not in _Ncache:
        lab, n, ed, i5 = blocks[idx]
        _Ncache[idx] = counts_of(n, ed)
    return _Ncache[idx]
def rep_N(mult, N, ed):
    # connected-pattern counts are additive over disjoint unions, and
    # every representative multiset consists of block indices
    return add_N(*[block_N(i) for i in mult])

tested = {"K33": 0, "prism": 0}
candidates_seen = 0
for cname in ("K33", "prism"):
    cn, ced = LIB[cname]
    ci5 = inv5(compN[cname])
    Xs = [(lab, n, ed, i5, (idx,), None) for idx, (lab, n, ed, i5) in enumerate(blocks)]
    for a, i in enumerate(small_idx):
        (l1, n1, e1, i1) = blocks[i]
        for j in small_idx[a:]:
            (l2, n2, e2, i2) = blocks[j]
            Xs.append((f"{l1}+{l2}", n1 + n2, e1 + shift_ed(e2, n1), add_i5(i1, i2),
                       tuple(sorted((i, j))), (i, j)))
    for (xlab, xn, xed, xi5, xmult, xpair) in Xs:
        N = xn + cn
        if N > 24 or tested[cname] >= 4: continue
        tgt = add_i5(ci5, xi5)
        for (bdesc, bN, bed, bmult) in B_index[N].get(tgt, []):
            if bmult == tuple(sorted((lib_idx[cname],) + xmult)): continue
            candidates_seen += 1
            if xpair is None:
                NA = add_N(compN[cname], block_N(xmult[0]))
            else:
                NA = add_N(compN[cname], block_N(xpair[0]), block_N(xpair[1]))
            NB = rep_N(bmult, N, bed)
            if not interesting(NA, NB): continue
            A_ed = ced + shift_ed(xed, cn)
            test_pair(f"{cname}+{xlab}", N, A_ed, bdesc, bed)
            tested[cname] += 1
            if tested[cname] >= 4: break
log("I5-matched candidates examined:", candidates_seen, "| tested interesting pairs:", tested)
(HERE / "vol6_search4.json").write_text(json.dumps({"pairs": out_pairs, "tested": tested}, indent=1, default=str))
(HERE / "vol6_search4.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_search4.json")
