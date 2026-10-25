#!/usr/bin/env python3
"""Targeted search: agreeing-through-volume-4 pairs with Delta N_{K2,3+e} != 0,
to test whether the kappa^5 f^2 term is really present in Delta L_5."""
import json, sys, time
from fractions import Fraction as Fr
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol5_lib import *
import importlib.util
HERE = Path(__file__).resolve().parent
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)

spec = importlib.util.spec_from_file_location("orig_ext", EXT / "singularity_extension.py")
orig = importlib.util.module_from_spec(spec); spec.loader.exec_module(orig)

def kappa5(j):
    outp = {}
    for s in range(5 + j + 1):
        outp[5 - 2 * j + 2 * s] = Fr(comb(5 + j, s)) * (-1) ** s
    return outp

def pdiff(A, B):
    outp = dict(A)
    for e, c in B.items(): outp[e] = outp.get(e, Fr(0)) - c
    return {e: c for e, c in outp.items() if c}

out = {}
t00 = time.time()
for n, count, seed in ((12, 2000, 777001), (14, 1500, 777002)):
    t0 = time.time()
    recs, _ = orig.sample_records(n, count, seed, f"search{n}_g")
    gs = []
    for r in recs:
        edges = sorted(set(tuple(sorted(e)) for e in r["edges"]))
        L = height_series(n, edges)
        N = full_subgraph_counts(induced_counts(n, edges))
        gs.append({"name": r["name"], "L5": L[5], "N": N})
    nk = sum(1 for g in gs if g["N"][NAMED['NK23_plus_e']] > 0)
    key = lambda g: (g["N"][NAMED['N3_triangle']], g["N"][NAMED['N4_square']],
                     g["N"][NAMED['Ndia']], g["N"][NAMED['NK4']])
    groups = {}
    for g in gs: groups.setdefault(key(g), []).append(g)
    test_pairs = []
    agree = 0
    for k, grp in groups.items():
        for A, B in combinations(grp, 2):
            agree += 1
            if A["N"][NAMED['NK23_plus_e']] != B["N"][NAMED['NK23_plus_e']]:
                test_pairs.append((A, B))
    log(f"n={n}: sampled {len(gs)} graphs ({round(time.time()-t0,1)}s), "
        f"{nk} with NK23e>0, agreeing pairs {agree}, with dNK23e!=0: {len(test_pairs)}")
    results = []
    for A, B in test_pairs:
        dL = pdiff(A["L5"], B["L5"])
        def pred(f2):
            acc = {}
            terms = [("N5_pentagon", 0), ("NK23", 1), ("N_theta123", 1)]
            if f2: terms.append(("NK23_plus_e", 2))
            for nm, j in terms:
                dN = A["N"][NAMED[nm]] - B["N"][NAMED[nm]]
                if dN:
                    for e, c in kappa5(j).items(): acc[e] = acc.get(e, Fr(0)) + dN * c
            return acc
        results.append({
            "a": A["name"], "b": B["name"],
            "dNK23e": A["N"][NAMED['NK23_plus_e']] - B["N"][NAMED['NK23_plus_e']],
            "dN5": A["N"][NAMED['N5_pentagon']] - B["N"][NAMED['N5_pentagon']],
            "dNK23": A["N"][NAMED['NK23']] - B["N"][NAMED['NK23']],
            "dNTheta": A["N"][NAMED['N_theta123']] - B["N"][NAMED['N_theta123']],
            "full_formula_holds": not pdiff(dL, pred(True)),
            "reduced_formula_holds": not pdiff(dL, pred(False)),
            "dL5": {str(e): str(c) for e, c in sorted(dL.items())}})
        log("  pair", A["name"], B["name"], "dNK23e", results[-1]["dNK23e"],
            "full holds:", results[-1]["full_formula_holds"],
            "reduced holds:", results[-1]["reduced_formula_holds"])
    out[f"n{n}"] = {"sampled": len(gs), "graphs_with_NK23e_pos": nk,
                    "agreeing_pairs": agree, "test_pairs": results}
out["runtime_seconds"] = round(time.time() - t00, 1)
(HERE / "vol5_k23e_search.json").write_text(json.dumps(out, indent=1))
(HERE / "vol5_k23e_search.log").write_text("\n".join(LOG) + "\n")
log("done")
