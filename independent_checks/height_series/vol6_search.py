#!/usr/bin/env python3
"""Volume 6, targeted tests:
 (1) component-balance pairs A = C (+) H vs B = H' with I5(B) = I5(A),
     C in {K3,3, prism} (then also C+C' pairs if singles are scarce):
     decisive tests of the f^3 terms (K3,3, prism) and of the
     K3,3-e (m2012) f^2 term on graphs where those counts actually move;
 (2) audit of the 19 fitted size-6 determination identities and the
     beta-support size<=5 identities on disconnected graphs containing
     saturated components (K4, K3,3, prism)."""
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
    ell = series_log(L, 6)
    s = induced_counts(n, edges, 6)
    N = subgraph_counts_all(s)
    return {"n": n, "edges": edges, "L": L, "ell": ell, "N": N}

def inv5(N):
    return tuple(N.get(NAMED[nm], 0) for nm in INV5)

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

# ---------- component graphs ----------
pm_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["Nprism"]][0]
km_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["NK33"]][0]
COMPS = {"K33": (6, edges_of(types[6][km_t], 6)), "prism": (6, edges_of(types[6][pm_t], 6))}
comp_data = {}
for nm, (n, ed) in COMPS.items():
    comp_data[nm] = full_data(n, ed)
    log(nm, "I5 =", inv5(comp_data[nm]["N"]),
        "| N_C6 =", comp_data[nm]["N"].get(pat_index[(6, [t for t in ctypes[6] if types[6][t] == 1880][0])], 0))

# ---------- pools ----------
res = json.loads((HERE / "vol6_results.json").read_text())
pool = []   # (block, name, n, edges, I5)
for bn, grec in res["graphs"].items():
    for g in grec:
        N = {int(pi): v for pi, v in g["N"].items()}
        pool.append((bn, g["name"], g["n"], [tuple(e) for e in g["edges"]],
                     tuple(N.get(NAMED[x], 0) for x in INV5)))
by_n = {}
for rec in pool: by_n.setdefault(rec[2], []).append(rec)
log("pool sizes by n:", {n: len(v) for n, v in sorted(by_n.items())})

def shift(n, edges, comp_edges, off):
    return [(u + off, v + off) for (u, v) in edges]

out_pairs = []
def test_pair(A, B, label):
    """A, B: full_data dicts.  Assumes inv5 equal; verifies L_r equal r<=5,
    then tests formula variants for dL6."""
    assert inv5(A["N"]) == inv5(B["N"]), f"I5 mismatch {label}"
    agree5 = all(A["L"].get(r, {}) == B["L"].get(r, {}) for r in range(1, 6))
    dL6 = psub(B["L"][6], A["L"][6])
    NEW8 = [t for t in ctypes[6] if types[6][t] in (1880, 1881, 956, 1884, 5907, 1916, 5948, 5941)]
    t2012 = [t for t in ctypes[6] if types[6][t] == 2012][0]
    SAT = [km_t, pm_t]
    variants = {
        "reduced8": NEW8,
        "reduced8+f3": NEW8 + SAT,
        "reduced8+f2_m2012": NEW8 + [t2012],
        "full": NEW8 + SAT + [t2012],
        "raw_all_conn6": list(CONN6),
    }
    verdict = {}
    for vn, ts in variants.items():
        verdict[vn] = (formula_terms(A["N"], B["N"], ts) == dL6)
    dN = {}
    for t in CONN6:
        pi = pat_index[(6, t)]
        d = B["N"].get(pi, 0) - A["N"].get(pi, 0)
        if d: dN[describe(types[6][t], 6)] = d
    rec = {"label": label, "agree_through_5": agree5, "dL6_nonzero": bool(dL6),
           "verdicts": verdict, "dN_conn6": dN}
    out_pairs.append(rec)
    log(label, "| agree<=5:", agree5, "| dL6 != 0:", bool(dL6), "| verdicts:", verdict)
    log("   dN:", dN)
    return rec

# ---------- single-component balance ----------
found = {"K33": 0, "prism": 0}
for cname, cdata in comp_data.items():
    ci5 = inv5(cdata["N"])
    for hn in (8, 10, 12):
        if hn not in by_n or hn + 6 not in by_n: continue
        Hp = {(rec[4]): rec for rec in by_n[hn + 6]}
        for rec in by_n[hn]:
            tgt = tuple(a + b for a, b in zip(rec[4], ci5))
            if tgt in Hp:
                h2 = Hp[tgt]
                A_edges = cdata["edges"] + shift(rec[2], rec[3], [], 0) if False else \
                    COMPS[cname][1] + [(u + 6, v + 6) for (u, v) in rec[3]]
                A = full_data(rec[2] + 6, A_edges)
                B = full_data(h2[2], h2[3])
                test_pair(A, B, f"{cname} + {rec[1]}(n{rec[2]}) vs {h2[1]}(n{h2[2]})")
                found[cname] += 1
                if found[cname] >= 3: break
        if found[cname] >= 3: break
log("single-component pairs found:", found)

# ---------- double-component balance (if needed) ----------
if min(found.values()) < 1:
    combos = [("K33", "K33"), ("K33", "prism"), ("prism", "prism")]
    for c1, c2 in combos:
        ci5 = tuple(a + b for a, b in zip(inv5(comp_data[c1]["N"]), inv5(comp_data[c2]["N"])))
        done = False
        for hn in (8, 10):
            if hn not in by_n or hn + 12 not in by_n: continue
            Hp = {rec[4]: rec for rec in by_n[hn + 12]}
            for rec in by_n[hn]:
                tgt = tuple(a + b for a, b in zip(rec[4], ci5))
                if tgt in Hp:
                    h2 = Hp[tgt]
                    A_edges = COMPS[c1][1] + [(u + 6, v + 6) for (u, v) in COMPS[c2][1]] + \
                              [(u + 12, v + 12) for (u, v) in rec[3]]
                    A = full_data(rec[2] + 12, A_edges)
                    B = full_data(h2[2], h2[3])
                    test_pair(A, B, f"{c1}+{c2} + {rec[1]}(n{rec[2]}) vs {h2[1]}(n{h2[2]})")
                    done = True
                    break
            if done: break

# ---------- identity audit on component-rich disconnected graphs ----------
rel = json.loads((HERE / "vol6_relations.json").read_text())
fits6 = rel["conn6_pattern_fits_I5basis"]
BASIS_NAMES = ["1", "N3", "N4", "Ndia", "NK4", "N5", "NK23", "NTheta", "NK23e"]
def eval_fit(fit, n, N):
    tot = Fr(0)
    base = {"1": Fr(1), "N3": N.get(NAMED['N3_triangle'], 0), "N4": N.get(NAMED['N4_square'], 0),
            "Ndia": N.get(NAMED['Ndia'], 0), "NK4": N.get(NAMED['NK4'], 0),
            "N5": N.get(NAMED['N5_pentagon'], 0), "NK23": N.get(NAMED['NK23'], 0),
            "NTheta": N.get(NAMED['N_theta123'], 0), "NK23e": N.get(NAMED['NK23_plus_e'], 0)}
    for key, val in fit.items():
        a_part, b = key.split("*")
        a = int(a_part[2:])
        tot += Fr(val) * (n ** a) * base[b]
    return tot

K4_edges = [(i, j) for i in range(4) for j in range(i + 1, 4)]
cube = None
for rec in pool:
    if rec[0] == "n8" and rec[1] == "cube": cube = rec
pet = None
for rec in pool:
    if rec[0] == "n10" and rec[1] == "petersen": pet = rec
def union_graph(parts):
    """parts: list of (n, edges); returns full_data of disjoint union."""
    n = 0; ed = []
    for (pn, pe) in parts:
        ed += [(u + n, v + n) for (u, v) in pe]
        n += pn
    return full_data(n, ed)
audit_graphs = {
    "K4": [(4, K4_edges)],
    "K33": [COMPS["K33"]], "prism": [COMPS["prism"]],
    "K4+K4": [(4, K4_edges), (4, K4_edges)],
    "K4+K33": [(4, K4_edges), COMPS["K33"]],
    "K33+prism": [COMPS["K33"], COMPS["prism"]],
}
if cube: audit_graphs["K4+cube"] = [(4, K4_edges), (cube[2], cube[3])]
if pet: audit_graphs["prism+petersen"] = [COMPS["prism"], (pet[2], pet[3])]
if cube: audit_graphs["K33+cube"] = [COMPS["K33"], (cube[2], cube[3])]
audit = {}
for gname, parts in audit_graphs.items():
    G = union_graph(parts)
    bad = {}
    for desc, fit in fits6.items():
        if fit in (None, "FIT_FAILED_ON_FULL") or fit == {}: continue
        t = [t for t in ctypes[6] if describe(types[6][t], 6) == desc][0]
        pi = pat_index[(6, t)]
        lhs = G["N"].get(pi, 0)
        rhs = eval_fit(fit, G["n"], G["N"])
        if Fr(lhs) != rhs: bad[desc] = {"actual": lhs, "fitted": str(rhs)}
    audit[gname] = bad
    log("audit", gname, "violations:", bad if bad else "none")

out = {"pairs": out_pairs, "audit": audit}
(HERE / "vol6_search.json").write_text(json.dumps(out, indent=1, default=str))
(HERE / "vol6_search.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_search.json")
