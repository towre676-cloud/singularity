#!/usr/bin/env python3
"""Volume 6, final check: the reduced formula over the varying patterns
(the candidate new invariants) tested on EVERY agreeing pair; per-term
isolation counts and drop-one necessity; Delta-relation analysis among
the new invariants; re-verification that Delta N = 0 for K3,3-e (m2012)
on every agreeing pair."""
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

res = json.loads((HERE / "vol6_results.json").read_text())
pairs = [row for rows in res["pair_rows"].values() for row in rows]

def kappa6(j):
    # kappa^6 f^j = q^6 (1-q^2)^6 * q^{-2j} (1-q^2)^j = q^{6-2j} (1-q^2)^{6+j}
    return {6 - 2 * j + 2 * i: Fr(comb(6 + j, i)) * (-1) ** i for i in range(6 + j + 1)}

varying = set()
for pr in pairs:
    for ts in pr["dN_conn6"]: varying.add(int(ts))
NEWSET = sorted(varying)
log("varying connected 6-types on agreeing pairs:",
    [describe(types[6][t], 6) for t in NEWSET])
by_mask = {types[6][t]: t for t in ctypes[6]}

def predict(dN, terms):
    tot = {}
    for t in terms:
        d = dN.get(str(t), 0)
        if d:
            j = bin(types[6][t]).count("1") - 6
            for e, c in kappa6(j).items():
                tot[e] = tot.get(e, Fr(0)) + d * c
    return {e: c for e, c in tot.items() if c}

fails = 0
isol = {t: 0 for t in NEWSET}
dropfail = {t: 0 for t in NEWSET}
nonzero_terms = {t: 0 for t in NEWSET}
m2012_t = by_mask[2012]
m2012_varies = 0
for pr in pairs:
    dN = pr["dN_conn6"]
    if str(m2012_t) in dN: m2012_varies += 1
    dL = {int(e): Fr(c) for e, c in pr["dL6"].items()}
    act = [t for t in NEWSET if dN.get(str(t), 0) != 0]
    for t in act: nonzero_terms[t] += 1
    if len(act) == 1: isol[act[0]] += 1
    if predict(dN, NEWSET) != dL: fails += 1
    for t in act:
        if predict(dN, [u for u in NEWSET if u != t]) != dL:
            dropfail[t] += 1
log("total agreeing pairs:", len(pairs))
log("reduced formula (varying terms only) failures:", fails)
log("pairs where Delta N_{K3,3-e} != 0:", m2012_varies)
for t in NEWSET:
    log(f"  term {describe(types[6][t], 6)}: varies on {nonzero_terms[t]} pairs,"
        f" isolated on {isol[t]}, drop-one failures {dropfail[t]}")

# Delta-relation analysis: rational span of Delta(new) vectors; relations
# sum_t c_t DeltaN_t = 0 holding on every agreeing pair.
seen = set(); vecs = []
for pr in pairs:
    v = tuple(pr["dN_conn6"].get(str(t), 0) for t in NEWSET)
    if v not in seen: seen.add(v); vecs.append(v)
log("distinct Delta(new) vectors:", len(vecs))
rows = [list(map(Fr, v)) for v in vecs]
pivots = []; r = 0
for c in range(len(NEWSET)):
    piv = next((i for i in range(r, len(rows)) if rows[i][c] != 0), None)
    if piv is None: continue
    rows[r], rows[piv] = rows[piv], rows[r]
    pv = rows[r][c]; rows[r] = [x / pv for x in rows[r]]
    for i in range(len(rows)):
        if i != r and rows[i][c] != 0:
            f = rows[i][c]; rows[i] = [a - f * b for a, b in zip(rows[i], rows[r])]
    pivots.append(c); r += 1
    if r == len(rows): break
log("rank of Delta(new) span:", r, "of", len(NEWSET))
relations = []
for fc in [c for c in range(len(NEWSET)) if c not in pivots]:
    rel = [Fr(0)] * len(NEWSET); rel[fc] = Fr(1)
    for i, pc in enumerate(pivots):
        rel[pc] = -rows[i][fc]
    relations.append({describe(types[6][NEWSET[i]], 6): str(rel[i])
                      for i in range(len(NEWSET)) if rel[i]})
    log("  relation:", relations[-1])

# distribution of N_{K3,3-e} over the pools (is the census vacuous?)
pi2012 = pat_index[(6, by_mask[2012])]
dist = {}
for bn, grec in res["graphs"].items():
    nz = sum(1 for g in grec if g["N"].get(str(pi2012), 0) > 0)
    mx = max(g["N"].get(str(pi2012), 0) for g in grec)
    dist[bn] = {"graphs_with_N>0": nz, "of": len(grec), "max": mx}
    log("N_{K3,3-e} distribution", bn, dist[bn])

out = {"pairs": len(pairs), "reduced_formula_failures": fails,
       "m2012_distribution": dist,
       "m2012_varies_pairs": m2012_varies,
       "per_term": {describe(types[6][t], 6): {"varies": nonzero_terms[t],
                    "isolated": isol[t], "drop_one_failures": dropfail[t]} for t in NEWSET},
       "delta_span_rank": r, "delta_relations": relations}
(HERE / "vol6_final_check.json").write_text(json.dumps(out, indent=1))
(HERE / "vol6_final_check.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_final_check.json")
