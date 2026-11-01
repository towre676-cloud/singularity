#!/usr/bin/env python3
"""Volume 6, K3,3 component-balance hunt (phase 5): A = K3,3 (+) X vs
B at the same total n, using all pools including fresh n=24 / n=26.
Channels: X single at 18 -> B at 24 (singles, pairs of 12s, triples of
8s); X single at 20 -> B at 26 (singles); X = pair(10,10) -> B at 26.
Same interesting-pair filter and formula-variant tests as phase 4."""
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
def add_N(*dicts):
    out = {}
    for d in dicts:
        for k, v in d.items(): out[k] = out.get(k, 0) + v
    return out
def add_i5(a, b): return tuple(x + y for x, y in zip(a, b))
def shift_ed(edges, off): return [(u + off, v + off) for (u, v) in edges]

pm_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["Nprism"]][0]
km_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["NK33"]][0]
t2012 = [t for t in ctypes[6] if types[6][t] == 2012][0]
piK33, piPrism, pi2012 = pat_index[(6, km_t)], pat_index[(6, pm_t)], pat_index[(6, t2012)]
K33_ed = edges_of(types[6][km_t], 6)
K33_N = counts_of(6, K33_ed)
K33_I5 = inv5(K33_N)
log("K33 I5 =", K33_I5)

res = json.loads((HERE / "vol6_results.json").read_text())
pools2 = json.loads((HERE / "vol6_pools2.json").read_text())
pools3 = json.loads((HERE / "vol6_pools3.json").read_text())
blocks = []   # (label, n, edges, I5)
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
log("blocks:", len(blocks))
_Ncache = {}
def block_N(idx):
    if idx not in _Ncache:
        lab, n, ed, i5 = blocks[idx]
        _Ncache[idx] = counts_of(n, ed)
    return _Ncache[idx]

from collections import defaultdict
B_index = defaultdict(lambda: defaultdict(list))
def add_B(N, i5, desc, ed, mult):
    lst = B_index[N][i5]
    if all(e[3] != mult for e in lst) and len(lst) < 6:
        lst.append((desc, N, ed, mult))
for idx, (lab, n, ed, i5) in enumerate(blocks):
    add_B(n, i5, lab, ed, (idx,))
idx12 = [i for i, b in enumerate(blocks) if b[1] == 12]
for a, i in enumerate(idx12):
    (l1, n1, e1, i1) = blocks[i]
    for j in idx12[a:]:
        (l2, n2, e2, i2) = blocks[j]
        add_B(24, add_i5(i1, i2), f"{l1}+{l2}", e1 + shift_ed(e2, 12), tuple(sorted((i, j))))
idx8 = [i for i, b in enumerate(blocks) if b[1] == 8]
for a, i in enumerate(idx8):
    (l1, n1, e1, i1) = blocks[i]
    for b, j in enumerate(idx8[a:], a):
        (l2, n2, e2, i2) = blocks[j]
        for k in idx8[b:]:
            (l3, n3, e3, i3) = blocks[k]
            add_B(24, add_i5(add_i5(i1, i2), i3), f"{l1}+{l2}+{l3}",
                  e1 + shift_ed(e2, 8) + shift_ed(e3, 16), tuple(sorted((i, j, k))))
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
            NB.get(pi2012, 0) - NA.get(pi2012, 0) != 0)

tested = 0
seen_cand = 0
def scan(Xs, N):
    """Xs entries: (label, edges, I5, tuple of block indices for N).  The
    expensive count dicts are computed lazily, only after an I5 hit."""
    global tested, seen_cand
    for (xlab, xed, xi5, xidx) in Xs:
        if tested >= 4: return
        tgt = add_i5(K33_I5, xi5)
        reps = B_index[N].get(tgt, [])
        if not reps: continue
        NA = add_N(K33_N, *[block_N(i) for i in xidx])
        for (bdesc, bN, bed, bmult) in reps:
            seen_cand += 1
            NB = add_N(*[block_N(i) for i in bmult])
            if not interesting(NA, NB): continue
            A_ed = K33_ed + shift_ed(xed, 6)
            test_pair(f"K33+{xlab}", N, A_ed, bdesc, bed)
            tested += 1
            if tested >= 4: return

# channel 1: X singles at 18 -> N=24
Xs = [(lab, ed, i5, (idx,)) for idx, (lab, n, ed, i5) in enumerate(blocks) if n == 18]
scan(Xs, 24)
log("after channel 1 (X18): tested", tested, "candidates", seen_cand)
# channel 2: X singles at 20 -> N=26
if tested < 4:
    Xs = [(lab, ed, i5, (idx,)) for idx, (lab, n, ed, i5) in enumerate(blocks) if n == 20]
    scan(Xs, 26)
    log("after channel 2 (X20): tested", tested, "candidates", seen_cand)
# channel 3: X = pair(10,10) -> N=26
if tested < 4:
    idx10 = [i for i, b in enumerate(blocks) if b[1] == 10]
    Xs = []
    for a, i in enumerate(idx10):
        (l1, n1, e1, i1) = blocks[i]
        for j in idx10[a:]:
            (l2, n2, e2, i2) = blocks[j]
            Xs.append((f"{l1}+{l2}", e1 + shift_ed(e2, 10), add_i5(i1, i2), (i, j)))
    scan(Xs, 26)
    log("after channel 3 (X=10+10): tested", tested, "candidates", seen_cand)
(HERE / "vol6_search5.json").write_text(json.dumps({"pairs": out_pairs, "tested": tested}, indent=1, default=str))
(HERE / "vol6_search5.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_search5.json; K33 interesting pairs tested:", tested)
