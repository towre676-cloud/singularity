#!/usr/bin/env python3
"""Volume-5 driver: pools, series, checks, agreeing pairs, fits."""
import json, sys, time
from fractions import Fraction as Fr
from itertools import combinations
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol5_lib import *

HERE = Path(__file__).resolve().parent
EXT = HERE  # stored pools live beside these scripts (singularity_extension.json, added by the height-series extension change)
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)

def pser(p):
    return {str(e): (c.numerator if c.denominator == 1 else f"{c.numerator}/{c.denominator}")
            for e, c in sorted(p.items()) if c}

t00 = time.time()
out = {"checks": {}, "types": {}, "blocks": {}}

# ---------------- type tables summary ----------------
for k in range(1, 6):
    occ = [t for t in ctypes[k]
           if max(d for d in
                  [sum(1 for (a, b) in edges_of(types[k][t], k) if a == v or b == v)
                   for v in range(k)]) <= 3]
    out["types"][f"k{k}"] = {
        "all_graphs": len(types[k]),
        "connected": len(ctypes[k]),
        "connected_maxdeg_le_3": len(occ),
        "P_polys": {describe(types[k][t], k): {str(j): c for j, c in sorted(P_poly[(k, t)].items())}
                    for t in ctypes[k]},
        "cumulant_x5": {describe(types[k][t], k): pser(cumulants[(k, t)][5])
                        for t in ctypes[k]},
        "cumulant_xk_equals_aP": {},
    }
    # check [x^k] Phi_tau == a^k P(tau)  (multilinear coefficient)
    for t in ctypes[k]:
        pred = {}
        for j, c in P_poly[(k, t)].items():
            # a^k f^j = q^{3k} (q^-2 - 1)^j
            for s in range(j + 1):
                e = 3 * k - 2 * s
                pred[e] = pred.get(e, Fr(0)) + c * comb(j, s) * (-1) ** (j - s)
        got = cumulants[(k, t)][k]
        assert got == {e: c for e, c in pred.items() if c}, (k, t, got, pred)
    out["checks"][f"multilinear_identity_k{k}"] = True
    # Phi vanishes below volume k
    for t in ctypes[k]:
        for r in range(k):
            assert not cumulants[(k, t)][r], (k, t, r)
    out["checks"][f"phi_vanishes_below_k{k}"] = True
log("type tables + cumulants done", round(time.time() - t00, 1), "s")

# occurring connected types in cubic graphs (max degree <= 3)
occ_types = {}
for k in range(1, 6):
    occ_types[k] = []
    for t in ctypes[k]:
        degs = [0] * k
        for (a, b) in edges_of(types[k][t], k): degs[a] += 1; degs[b] += 1
        if max(degs) <= 3: occ_types[k].append(t)

# ---------------- pools ----------------
sys.path.insert(0, str(EXT))
import importlib.util
spec = importlib.util.spec_from_file_location("orig_ext", EXT / "singularity_extension.py")
orig = importlib.util.module_from_spec(spec); spec.loader.exec_module(orig)

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
log("pools loaded:", {k: len(v[1]) for k, v in pools.items()})

graphs = {}
for bn, (n, recs) in pools.items():
    t0 = time.time(); grec = []
    for r in recs:
        edges = sorted(set(tuple(sorted(e)) for e in r["edges"]))
        L = height_series(n, edges)
        ell = series_log([{e: Fr(c) for e, c in p.items()} for p in L], MAXV)
        sc = induced_counts(n, edges)
        N = full_subgraph_counts(sc)
        grec.append({"name": r["name"], "edges": edges, "L": L, "ell": ell,
                     "s": sc, "N": N, "stored": r["stored"]})
    graphs[bn] = grec
    log(bn, "computed", len(grec), "graphs in", round(time.time() - t0, 1), "s")

# ---------------- checks ----------------
chk = out["checks"]
for bn, grec in graphs.items():
    n = pools[bn][0]
    for g in grec:
        for k in range(6):
            assert sum(g["L"][k].values()) == comb(n + k - 1, k), (g["name"], k)
        # ell_5 identity
        pred = {}
        for (k, t), s in g["s"].items():
            if s == 0 or (k, t) not in cumulants: continue  # Phi_S = 0 if disconnected (SNG-F55)
            for e, c in cumulants[(k, t)][5].items():
                pred[e] = pred.get(e, Fr(0)) + s * c
        pred = {e: c for e, c in pred.items() if c}
        assert pred == g["ell"][5], (bn, g["name"])
        st = g["stored"]
        if st is not None:
            assert g["N"][NAMED['N3_triangle']] == st["triangles_N3"], g["name"]
            assert g["N"][NAMED['N4_square']] == st["squares_N4"], g["name"]
            assert g["N"][NAMED['Ndia']] == st["diamonds_Ndia"], g["name"]
            assert g["N"][NAMED['N5_pentagon']] == st["pentagons_N5"], g["name"]
            assert st["totals"] == [sum(g["L"][k].values()) for k in range(5)], g["name"]
    chk[f"totals_and_ell5_identity_and_stored_counts_{bn}"] = True
log("all per-graph checks passed", round(time.time() - t00, 1), "s")

# direct brute-force subgraph count spot checks
import random
rng = random.Random(7)
for bn in ("n8", "n10"):
    g = graphs[bn][3]
    for name in ("N5_pentagon", "NK23", "N_theta123", "N_bowtie", "NK23_plus_e"):
        pi = NAMED[name]
        direct = count_in_pattern(pools[bn][0], g["edges"], pi)
        assert direct == g["N"][pi], (bn, name, direct, g["N"][pi])
chk["direct_subgraph_count_spot_checks"] = True

def kappa5(j):
    """kappa^5 f^j as q-poly dict (Fr). kappa = q(1-q^2)."""
    # q^5 (1-q^2)^5 f^j = q^{5-2j} (1-q^2)^{5+j}
    outp = {}
    for s in range(5 + j + 1):
        outp[5 - 2 * j + 2 * s] = Fr(comb(5 + j, s)) * (-1) ** s
    return outp

def pdiff(A, B):
    outp = dict(A)
    for e, c in B.items(): outp[e] = outp.get(e, Fr(0)) - c
    return {e: c for e, c in outp.items() if c}

def pdiv_kappa5(P):
    """Divide q-poly P by kappa^5 = q^5 (1-q^2)^5 in Q[f] terms:
    returns dict fpow->Fr if P = kappa^5 * (poly in f), else None.
    f = q^-2-1: work in variable y=q^2: kappa^5 f^j = q^{5-2j}(1-q^2)^{5+j}."""
    rem = dict(P)
    res = {}
    for j in range(-2, 9):
        basis = kappa5(j)
        if not rem: break
        mine = min(rem)
        # lowest exponent of kappa^5 f^j is 5-2j
        # choose j so basis lowest == mine
        # instead: peel from lowest exponent using exact basis vector
        # basis lowest term coefficient is 1 at exponent 5-2j
        jj = (5 - mine)
        if jj % 2: return None
        jj //= 2
        if jj < -2 or jj > 8: return None
        c0 = rem[mine]
        res[jj] = res.get(jj, Fr(0)) + c0
        for e, c in basis.items():
            rem[e] = rem.get(e, Fr(0)) - c0 * c
            if rem[e] == 0: del rem[e]
    return res if not rem else None

# ---------------- agreeing pairs and candidate fits ----------------
cand_patterns = [("N5_pentagon", 0), ("NK23", 1)]  # baseline SNG-F61 shape
fit_results = {}
for bn, grec in graphs.items():
    n = pools[bn][0]
    key = lambda g: (g["N"][NAMED['N3_triangle']], g["N"][NAMED['N4_square']],
                     g["N"][NAMED['Ndia']], g["N"][NAMED['NK4']])
    pairs = []
    for i, j in combinations(range(len(grec)), 2):
        A, B = grec[i], grec[j]
        if key(A) == key(B):
            assert all(A["L"][r] == B["L"][r] for r in range(5)), (A["name"], B["name"])
            assert all(A["ell"][r] == B["ell"][r] for r in range(5))
            pairs.append((A, B))
    npairs = len(pairs)
    # candidates to test
    def test(formula, label):
        fails = []
        for (A, B) in pairs:
            dL = pdiff(A["L"][5], B["L"][5])
            pred = formula(A, B)
            if pdiff(dL, pred):
                fails.append((A["name"], B["name"]))
        return {"label": label, "pairs": npairs, "failures": len(fails),
                "first_failures": fails[:5]}
    def mk(terms):
        def f(A, B):
            acc = {}
            for name, j in terms:
                dN = A["N"][NAMED[name]] - B["N"][NAMED[name]]
                if dN:
                    for e, c in kappa5(j).items():
                        acc[e] = acc.get(e, Fr(0)) + dN * c
            return acc
        return f
    res = {"agreeing_pairs": npairs}
    res["zero"] = test(mk([]), "0")
    res["squares_analogue_k5_dN5"] = test(mk([("N5_pentagon", 0)]), "kappa^5 dN5")
    res["F61_girth4_formula"] = test(mk([("N5_pentagon", 0), ("NK23", 1)]),
                                     "kappa^5 (dN5 + f dNK23)")
    res["F61_plus_theta_bowtie"] = test(mk([("N5_pentagon", 0), ("NK23", 1),
                                            ("N_theta123", 1), ("N_bowtie", 1)]),
                                        "kappa^5 (dN5 + f(dNK23+dTheta123+dBowtie))")
    res["F61_plus_theta_bowtie_K23e"] = test(mk([("N5_pentagon", 0), ("NK23", 1),
                                                 ("N_theta123", 1), ("N_bowtie", 1),
                                                 ("NK23_plus_e", 2)]),
                                             "kappa^5 (dN5 + f(dNK23+dTheta+dBowtie) + f^2 dNK23e)")
    fit_results[bn] = res
    log(bn, "agreeing pairs:", npairs,
        "| failures: zero", res["zero"]["failures"],
        "N5-only", res["squares_analogue_k5_dN5"]["failures"],
        "F61", res["F61_girth4_formula"]["failures"],
        "F61+th+bow", res["F61_plus_theta_bowtie"]["failures"],
        "F61+th+bow+K23e", res["F61_plus_theta_bowtie_K23e"]["failures"])
out["fits"] = fit_results

# girth>=4 subfamily under F61 formula (all n pooled)
g4pairs = g4fail = 0
for bn, grec in graphs.items():
    key = lambda g: (g["N"][NAMED['N3_triangle']], g["N"][NAMED['N4_square']],
                     g["N"][NAMED['Ndia']], g["N"][NAMED['NK4']])
    for i, j in combinations(range(len(grec)), 2):
        A, B = grec[i], grec[j]
        if key(A) == key(B) and A["N"][NAMED['N3_triangle']] == 0:
            g4pairs += 1
            dL = pdiff(A["L"][5], B["L"][5])
            acc = {}
            for name, jj in (("N5_pentagon", 0), ("NK23", 1)):
                dN = A["N"][NAMED[name]] - B["N"][NAMED[name]]
                for e, c in kappa5(jj).items(): acc[e] = acc.get(e, Fr(0)) + dN * c
            if pdiff(dL, acc): g4fail += 1
out["checks"]["F61_on_triangle_free_agreeing_pairs"] = {"pairs": g4pairs, "failures": g4fail}
log("triangle-free agreeing pairs:", g4pairs, "F61 failures:", g4fail)

# save per-pair difference data for the algebraic fit phase
pairdata = {}
for bn, grec in graphs.items():
    key = lambda g: (g["N"][NAMED['N3_triangle']], g["N"][NAMED['N4_square']],
                     g["N"][NAMED['Ndia']], g["N"][NAMED['NK4']])
    rows = []
    for i, j in combinations(range(len(grec)), 2):
        A, B = grec[i], grec[j]
        if key(A) == key(B):
            rows.append({"a": A["name"], "b": B["name"],
                         "dL5": pser(pdiff(A["L"][5], B["L"][5])),
                         "dN": {nm: A["N"][pi] - B["N"][pi] for nm, pi in NAMED.items()},
                         "dN_all": {str(pi): A["N"][pi] - B["N"][pi]
                                    for pi in range(len(patterns)) if A["N"][pi] != B["N"][pi]}})
    pairdata[bn] = rows
out["pairdata"] = pairdata

# series for named graphs (for the report)
out["named_series_vol5"] = {}
for bn, grec in graphs.items():
    out["named_series_vol5"][bn] = {g["name"]: pser(g["L"][5]) for g in grec[:3]}

out["runtime_seconds"] = round(time.time() - t00, 1)
(HERE / "vol5_results.json").write_text(json.dumps(out, indent=1))
(HERE / "vol5_run.log").write_text("\n".join(LOG) + "\n")
log("wrote vol5_results.json")
