#!/usr/bin/env python3
"""Volume 6, component-balance phase 2: match fresh n=18 / n=20 pools
against stored pools for single- and double-component balances and run
the decisive formula-variant tests on every matched pair."""
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
    N = subgraph_counts_all(s)
    return {"n": n, "edges": edges, "L": L, "N": N}

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
COMPS = {"K33": (6, edges_of(types[6][km_t], 6)), "prism": (6, edges_of(types[6][pm_t], 6))}
compN = {}
for nm, (n, ed) in COMPS.items():
    s = induced_counts(n, ed, 6)
    compN[nm] = subgraph_counts_all(s)
    log(nm, "I5 =", inv5(compN[nm]))

res = json.loads((HERE / "vol6_results.json").read_text())
pools2 = json.loads((HERE / "vol6_pools2.json").read_text())
by_n = {}
for bn, grec in res["graphs"].items():
    for g in grec:
        N = {int(pi): v for pi, v in g["N"].items()}
        by_n.setdefault(g["n"], []).append(
            (g["name"], g["n"], [tuple(e) for e in g["edges"]],
             tuple(N.get(NAMED[x], 0) for x in INV5)))
for bn, grec in pools2.items():
    n = int(bn[1:])
    for g in grec:
        by_n.setdefault(n, []).append(
            (g["name"], n, [tuple(e) for e in g["edges"]], tuple(g["I5"])))
log("pools by n:", {n: len(v) for n, v in sorted(by_n.items())})

out_pairs = []
def test_pair(A, B, label):
    assert inv5(A["N"]) == inv5(B["N"]), f"I5 mismatch {label}"
    agree5 = all(A["L"].get(r, {}) == B["L"].get(r, {}) for r in range(1, 6))
    dL6 = psub(B["L"][6], A["L"][6])
    NEW8 = [t for t in ctypes[6] if types[6][t] in (1880, 1881, 956, 1884, 5907, 1916, 5948, 5941)]
    t2012 = [t for t in ctypes[6] if types[6][t] == 2012][0]
    SAT = [km_t, pm_t]
    variants = {"reduced8": NEW8, "reduced8+f3": NEW8 + SAT,
                "reduced8+f2_m2012": NEW8 + [t2012],
                "full": NEW8 + SAT + [t2012], "raw_all_conn6": list(CONN6)}
    verdict = {vn: (formula_terms(A["N"], B["N"], ts) == dL6) for vn, ts in variants.items()}
    dN = {}
    for t in CONN6:
        pi = pat_index[(6, t)]
        d = B["N"].get(pi, 0) - A["N"].get(pi, 0)
        if d: dN[describe(types[6][t], 6)] = d
    out_pairs.append({"label": label, "agree_through_5": agree5,
                      "dL6_nonzero": bool(dL6), "verdicts": verdict, "dN_conn6": dN})
    log(label, "| agree<=5:", agree5, "| dL6!=0:", bool(dL6), "| verdicts:", verdict)
    log("   dN:", dN)

def balance(comp_names, h_n, max_pairs=3):
    """A = comps (+) H (H at h_n), B = H' at h_n + 6*len(comps)."""
    tot = sum(6 for _ in comp_names)
    ci5 = [0] * 8
    for c in comp_names:
        ci5 = [a + b for a, b in zip(ci5, inv5(compN[c]))]
    Hp = {}
    for rec in by_n.get(h_n + tot, []): Hp.setdefault(rec[3], []).append(rec)
    made = 0
    for rec in by_n.get(h_n, []):
        tgt = tuple(a + b for a, b in zip(rec[3], ci5))
        for h2 in Hp.get(tgt, []):
            ed = []; off = 0
            for c in comp_names:
                ed += [(u + off, v + off) for (u, v) in COMPS[c][1]]; off += 6
            ed += [(u + off, v + off) for (u, v) in rec[2]]
            A = full_data(h_n + tot, ed)
            B = full_data(h2[1], h2[2])
            test_pair(A, B, f"{'+'.join(comp_names)} + {rec[0]}(n{h_n}) vs {h2[0]}(n{h2[1]})")
            made += 1
            if made >= max_pairs: return made
    return made

counts = {}
counts["K33 single (H12)"] = balance(["K33"], 12)
counts["prism single (H12)"] = balance(["prism"], 12)
counts["K33 single (H14)"] = balance(["K33"], 14)
counts["prism single (H14)"] = balance(["prism"], 14)
counts["K33+K33 (H8)"] = balance(["K33", "K33"], 8)
counts["K33+prism (H8)"] = balance(["K33", "prism"], 8)
counts["prism+prism (H8)"] = balance(["prism", "prism"], 8)
log("pairs made:", counts)
(HERE / "vol6_search2.json").write_text(json.dumps({"pairs": out_pairs, "counts": counts}, indent=1, default=str))
(HERE / "vol6_search2.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_search2.json")
