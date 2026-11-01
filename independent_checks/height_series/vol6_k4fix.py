#!/usr/bin/env python3
"""Volume 6: N_K4 corrections to fitted determination identities.
The random pools are connected (n>=8), hence N_K4 = 0 throughout and any
K4-component correction is invisible there.  Audit graphs with K4
components exposed corrections in 6 of the 19 size-6 identities.  This
script (a) verifies the corrected size-6 identities on all pool graphs
and all audit graphs, and (b) audits every fitted size<=5 pattern
formula on the audit graphs, deriving and verifying any N_K4
correction the same way."""
import json, sys
from fractions import Fraction as Fr
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol6_lib import *
HERE = Path(__file__).resolve().parent
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)

BASE_KEYS = {"1": None, "N3": 'N3_triangle', "N4": 'N4_square', "Ndia": 'Ndia',
             "NK4": 'NK4', "N5": 'N5_pentagon', "NK23": 'NK23',
             "NTheta": 'N_theta123', "NK23e": 'NK23_plus_e'}
def eval_fit(fit, n, N, extra_k4=Fr(0)):
    tot = Fr(0)
    for key, val in fit.items():
        a_part, b = key.split("*")
        a = int(a_part[2:])
        bv = Fr(1) if b == "1" else Fr(N.get(NAMED[BASE_KEYS[b]], 0))
        tot += Fr(val) * (n ** a) * bv
    return tot + extra_k4 * N.get(NAMED['NK4'], 0)

# audit graphs
res = json.loads((HERE / "vol6_results.json").read_text())
rel = json.loads((HERE / "vol6_relations.json").read_text())
pm_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["Nprism"]][0]
km_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["NK33"]][0]
K4_edges = [(i, j) for i in range(4) for j in range(i + 1, 4)]
def counts_of(n, edges):
    s = induced_counts(n, edges, 6)
    return subgraph_counts_all(s)
def union(parts):
    n = 0; ed = []
    for (pn, pe) in parts:
        ed += [(u + n, v + n) for (u, v) in pe]; n += pn
    return n, ed
cube_e = pet_e = None
for bn, grec in res["graphs"].items():
    for g in grec:
        if g["name"] == "cube": cube_e = (g["n"], [tuple(e) for e in g["edges"]])
        if g["name"] == "petersen": pet_e = (g["n"], [tuple(e) for e in g["edges"]])
audit = {}
parts_map = {"K4": [(4, K4_edges)], "K33": [(6, edges_of(types[6][km_t], 6))],
             "prism": [(6, edges_of(types[6][pm_t], 6))],
             "K4+K4": [(4, K4_edges), (4, K4_edges)],
             "K4+K33": [(4, K4_edges), (6, edges_of(types[6][km_t], 6))],
             "K33+prism": [(6, edges_of(types[6][km_t], 6)), (6, edges_of(types[6][pm_t], 6))]}
if cube_e: parts_map["K4+cube"] = [(4, K4_edges), cube_e]
if pet_e: parts_map["prism+petersen"] = [(6, edges_of(types[6][pm_t], 6)), pet_e]
if cube_e: parts_map["K33+cube"] = [(6, edges_of(types[6][km_t], 6)), cube_e]
for nm, parts in parts_map.items():
    n, ed = union(parts)
    audit[nm] = (n, counts_of(n, ed))
log("audit graphs:", list(audit))

pool_graphs = []
for bn, grec in res["graphs"].items():
    for g in grec:
        N = {int(pi): v for pi, v in g["N"].items()}
        for pi in range(len(patterns)): N.setdefault(pi, 0)
        pool_graphs.append((g["n"], N))

out = {}
# (a) size-6 identities with corrections
CORR6 = {"k6_e6_deg332211_m633": 12, "k6_e6_deg332211_m694": 24,
         "k6_e7_deg333311_m758": -6, "k6_e7_deg333221_m1780": -24,
         "k6_e6_deg332211_m693": 12, "k6_e6_deg333111_m691": 8}
fits6 = rel["conn6_pattern_fits_I5basis"]
bad6 = {}
for desc, fit in fits6.items():
    if fit in (None, "FIT_FAILED_ON_FULL") or fit == {}: continue
    t = [t for t in ctypes[6] if describe(types[6][t], 6) == desc][0]
    pi = pat_index[(6, t)]
    c = Fr(CORR6.get(desc, 0))
    fails = 0
    for (n, N) in pool_graphs:
        if eval_fit(fit, n, N, c) != N.get(pi, 0): fails += 1
    for nm, (n, N) in audit.items():
        if eval_fit(fit, n, N, c) != N.get(pi, 0): fails += 1
    bad6[desc] = fails
    log("conn6 identity", desc, "K4-correction", CORR6.get(desc, 0), "failures:", fails)
out["conn6_corrected_failures"] = bad6

# (b) size<=5 fits audit
fits5 = rel["size_le5_pattern_fits"]
corr5 = {}
bad5 = {}
for desc, fit in fits5.items():
    if fit in (None, "FIT_FAILED_ON_FULL"): continue
    pi = next(i for i, (xk, xt, xm) in enumerate(patterns) if describe(xm, xk) == desc)
    # raw audit
    raw_bad = [nm for nm, (n, N) in audit.items() if eval_fit(fit, n, N) != N.get(pi, 0)]
    c = Fr(0)
    if raw_bad:
        n1, N1 = audit["K4"]
        diff = Fr(N1.get(pi, 0)) - eval_fit(fit, n1, N1)   # N_K4(K4) = 1
        c = diff
        corr5[desc] = str(c)
    fails_pool = sum(1 for (n, N) in pool_graphs if eval_fit(fit, n, N, c) != N.get(pi, 0))
    fails_audit = sum(1 for nm, (n, N) in audit.items() if eval_fit(fit, n, N, c) != N.get(pi, 0))
    bad5[desc] = {"raw_audit_violations": raw_bad, "k4_correction": str(c),
                  "pool_failures": fails_pool, "audit_failures": fails_audit}
    if raw_bad or fails_pool or fails_audit:
        log("size<=5", desc, "raw violations:", raw_bad, "correction:", c,
            "pool fails:", fails_pool, "audit fails:", fails_audit)
log("size<=5 patterns needing K4 correction:", corr5)
out["size_le5"] = bad5
(HERE / "vol6_k4fix.json").write_text(json.dumps(out, indent=1, default=str))
(HERE / "vol6_k4fix.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_k4fix.json")
