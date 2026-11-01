#!/usr/bin/env python3
"""Volume-6 driver: pools (stored n=8/10/12 + fresh n=14/16), height
series through x^6, SNG-F55 checks at volume 6, agreeing-through-volume-5
pairs, raw-formula test, and the variation census over the 29
non-vacuous connected 6-patterns."""
import json, sys, time, random
from fractions import Fraction as Fr
from itertools import combinations
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol6_lib import *
import importlib.util
HERE = Path(__file__).resolve().parent
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)

def pser(p):
    return {str(e): (c.numerator if isinstance(c, Fr) and c.denominator == 1 else str(c))
            for e, c in sorted(p.items()) if c}

spec = importlib.util.spec_from_file_location("orig_ext", EXT / "singularity_extension.py")
orig = importlib.util.module_from_spec(spec); spec.loader.exec_module(orig)

t00 = time.time()
out = {"checks": {}, "pools": {}, "pairs": {}}

# ---------------- pools ----------------
pools = {}
data = json.loads((EXT / "singularity_extension.json").read_text())
for bn in ("n10", "n12"):
    blk = data["blocks"][bn]
    recs = [{"name": r["name"], "edges": [tuple(e) for e in r["edges"]],
             "stored": r} for r in blk["named_graphs"] + blk["random_sample_records"]]
    pools[bn] = (blk["n"], recs)
sampled8, _ = orig.sample_records(8, 60, 20261024, "n8_g")
recs8 = [{"name": "cube_Q3", "edges": [tuple(e) for e in orig.cube_edges()], "stored": None},
         {"name": "mobius_M8", "edges": [tuple(e) for e in orig.mobius_ladder(8)], "stored": None}]
recs8 += [{"name": r["name"], "edges": [tuple(e) for e in r["edges"]], "stored": None}
          for r in sampled8]
pools["n8"] = (8, recs8)

def fresh_pool(n, count, seed, prefix):
    rng = random.Random(seed)
    seen, recs = set(), []
    while len(recs) < count:
        edges = orig.random_cubic(rng, n)
        key = tuple(edges)
        if key in seen: continue
        seen.add(key)
        recs.append({"name": f"{prefix}{len(recs)}", "edges": [tuple(e) for e in edges],
                     "stored": None})
    return recs

pools["n14"] = (14, fresh_pool(14, 3000, 20261027, "n14_g"))
pools["n16"] = (16, fresh_pool(16, 2000, 20261028, "n16_g"))
log("pools:", {k: len(v[1]) for k, v in pools.items()}, round(time.time() - t00, 1), "s")

INV5 = ['N3_triangle', 'N4_square', 'Ndia', 'NK4',
        'N5_pentagon', 'NK23', 'N_theta123', 'NK23_plus_e']
def inv5(g):
    return tuple(g["N"][NAMED[nm]] for nm in INV5)

def a6f(e):
    """a^6 f^e as q-poly: q^{18-2e} (1-q^2)^e."""
    outp = {}
    for s in range(e + 1):
        outp[18 - 2 * e + 2 * s] = Fr(comb(e, s)) * (-1) ** s
    return outp

def pdiff(A, B):
    outp = dict(A)
    for e, c in B.items(): outp[e] = outp.get(e, Fr(0)) - c
    return {e: c for e, c in outp.items() if c}

def padd(A, B, scale=1):
    outp = dict(A)
    for e, c in B.items(): outp[e] = outp.get(e, Fr(0)) + scale * c
    return {e: c for e, c in outp.items() if c}

graphs = {}
for bn, (n, recs) in pools.items():
    t0 = time.time(); grec = []
    for r in recs:
        edges = sorted(set(tuple(sorted(e)) for e in r["edges"]))
        L = height_series_fast(n, edges)
        ell = series_log([{e: Fr(c) for e, c in p.items()} for p in L], MAXV)
        sc = induced_counts(n, edges)
        N = subgraph_counts_all(sc)
        # S_{<=5}^{(6)} and size-6 part, per graph
        S5 = {}
        for (k, t), s in sc.items():
            if k <= 5 and s and (k, t) in cumulants:
                for e, c in cumulants[(k, t)][6].items():
                    S5[e] = S5.get(e, Fr(0)) + s * c
        S5 = {e: c for e, c in S5.items() if c}
        T6 = {}
        for (k, t), s in sc.items():
            if k == 6 and s and (k, t) in cumulants:
                for e, c in cumulants[(k, t)][6].items():
                    T6[e] = T6.get(e, Fr(0)) + s * c
        T6 = {e: c for e, c in T6.items() if c}
        grec.append({"name": r["name"], "edges": edges, "L": L, "ell": ell,
                     "s": sc, "N": N, "S5": S5, "T6": T6, "stored": r["stored"]})
    graphs[bn] = grec
    log(bn, "computed", len(grec), "graphs in", round(time.time() - t0, 1), "s")

# ---------------- per-graph checks ----------------
for bn, grec in graphs.items():
    n = pools[bn][0]
    for g in grec:
        for r in range(7):
            assert sum(g["L"][r].values()) == comb(n + r - 1, r), (g["name"], r)
        # SNG-F55 at volume 6: ell_6 = S_{<=5} + T_6 exactly
        assert pdiff(g["ell"][6], padd(g["S5"], g["T6"])) == {}, g["name"]
        # raw identity per graph: T6 = a^6 sum_Y N_Y f^{e(Y)} (connected Y, size 6)
        pred = {}
        for t in ctypes[6]:
            pi = pat_index[(6, t)]
            if g["N"][pi]:
                e = len(edges_of(types[6][t], 6))
                pred = padd(pred, a6f(e), Fr(g["N"][pi]))
        assert pdiff(g["T6"], pred) == {}, g["name"]
        st = g["stored"]
        if st is not None:
            assert g["N"][NAMED['N3_triangle']] == st["triangles_N3"], g["name"]
            assert g["N"][NAMED['N4_square']] == st["squares_N4"], g["name"]
            assert g["N"][NAMED['Ndia']] == st["diamonds_Ndia"], g["name"]
            assert g["N"][NAMED['N5_pentagon']] == st["pentagons_N5"], g["name"]
    out["checks"][f"totals_ell6_identity_raw_identity_stored_{bn}"] = True
    log(bn, "per-graph checks passed: totals, ell6 = S<=5 + T6, T6 raw identity, stored counts")

# direct brute-force spot checks of new size-6 counts
rng = random.Random(11)
for bn in ("n8", "n10", "n14"):
    g = graphs[bn][3]
    for nm in ("N6_hexagon", "NK33", "Nprism"):
        pi = NAMED[nm]
        direct = count_in_pattern(pools[bn][0], g["edges"], pi)
        assert direct == g["N"][pi], (bn, nm, direct, g["N"][pi])
out["checks"]["direct_subgraph_count_spot_checks_size6"] = True
log("direct brute-force spot checks for C6 / K3,3 / prism counts passed")

# ---------------- agreeing-through-volume-5 pairs ----------------
conn6_by_e = {}
for t in CONN6:
    conn6_by_e.setdefault(len(edges_of(types[6][t], 6)), []).append(t)

pair_summary = {}
all_pair_rows = {}
for bn, grec in graphs.items():
    n = pools[bn][0]
    groups = {}
    for g in grec: groups.setdefault(inv5(g), []).append(g)
    npairs = 0
    raw_fails = 0
    vary = {t: 0 for t in CONN6}
    nonzero_dL6 = 0
    rows = []
    for key, grp in groups.items():
        # agreement through volume 5 must hold exactly inside a group
        ref = grp[0]
        for g in grp[1:]:
            assert all(g["L"][r] == ref["L"][r] for r in range(6)), (bn, ref["name"], g["name"])
        for A, B in combinations(grp, 2):
            npairs += 1
            dL = pdiff(A["L"][6], B["L"][6])
            dell = pdiff(A["ell"][6], B["ell"][6])
            assert dL == dell, (bn, A["name"], B["name"])  # Bell bridge at vol 6
            # raw formula over ALL connected 6-patterns
            pred = {}
            dN = {}
            for t in ctypes[6]:
                pi = pat_index[(6, t)]
                d = A["N"][pi] - B["N"][pi]
                if d:
                    dN[t] = d
                    e = len(edges_of(types[6][t], 6))
                    pred = padd(pred, a6f(e), Fr(d))
            if pdiff(dell, pred): raw_fails += 1
            if dL: nonzero_dL6 += 1
            for t in CONN6:
                pi = pat_index[(6, t)]
                if A["N"][pi] != B["N"][pi]: vary[t] += 1
            rows.append({"a": A["name"], "b": B["name"],
                         "dL6": pser(dL),
                         "dN_conn6": {str(t): dN[t] for t in dN}})
    pair_summary[bn] = {
        "graphs": len(grec), "groups": len(groups), "agreeing_pairs": npairs,
        "raw_formula_failures": raw_fails, "pairs_with_dL6_nonzero": nonzero_dL6,
        "variation": {describe(types[6][t], 6): vary[t] for t in CONN6},
    }
    all_pair_rows[bn] = rows
    log(bn, "agreeing-through-5 pairs:", npairs, "| raw formula failures:", raw_fails,
        "| pairs with dL6 != 0:", nonzero_dL6)
    for t in CONN6:
        if vary[t]:
            log("   varies:", describe(types[6][t], 6), "on", vary[t], "pairs")
out["pairs"] = pair_summary

# save per-graph data for the relations/search phases
gdata = {}
for bn, grec in graphs.items():
    gdata[bn] = [{"name": g["name"], "n": pools[bn][0],
                  "N": {str(pi): v for pi, v in g["N"].items() if v},
                  "S5": pser(g["S5"]),
                  "L6": pser(g["L"][6]), "ell6": pser(g["ell"][6]),
                  "edges": [list(e) for e in g["edges"]]} for g in grec]
out["graphs"] = gdata
out["pair_rows"] = all_pair_rows
out["runtime_seconds"] = round(time.time() - t00, 1)
(HERE / "vol6_results.json").write_text(json.dumps(out, indent=1))
(HERE / "vol6_run.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_results.json in", out["runtime_seconds"], "s")
