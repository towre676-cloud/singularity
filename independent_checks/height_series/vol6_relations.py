#!/usr/bin/env python3
"""Volume 6, relations phase:
 (1) beta-decomposition of the volume-6 cumulant coefficients at sizes
     <=5 over the subgraph functionals sub_Y (the Lemma-A mechanism);
 (2) determination tests: every pattern count N_Y (|Y|<=5) and the
     size-<=5 part S5^{(6)} itself must be constant on (n, I5)-classes;
 (3) formula fits for all size<=5 patterns and for the non-varying
     connected 6-patterns, over the basis n^a * (I5 monomials);
 (4) S5^{(6)} = sum_Y beta_Y N_Y verified per graph."""
import json, sys, time
from fractions import Fraction as Fr
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol6_lib import *
HERE = Path(__file__).resolve().parent
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)

def solve_square(M, b):
    n = len(b)
    A = [row[:] + [b[i]] for i, row in enumerate(M)]
    for c in range(n):
        piv = next(i for i in range(c, n) if A[i][c] != 0)
        A[c], A[piv] = A[piv], A[c]
        pv = A[c][c]; A[c] = [x / pv for x in A[c]]
        for i in range(n):
            if i != c and A[i][c] != 0:
                f = A[i][c]; A[i] = [a - f * bb for a, bb in zip(A[i], A[c])]
    return [A[i][n] for i in range(n)]

def solve_span(basis_cols, target):
    """basis_cols: list of columns (each a list over rows); target: list.
    Returns coefficients or None.  Rational, exact."""
    n = len(target); cols = len(basis_cols)
    A = [[basis_cols[c][i] for c in range(cols)] + [target[i]] for i in range(n)]
    pivrow = {}; r = 0
    for c in range(cols):
        piv = next((i for i in range(r, n) if A[i][c] != 0), None)
        if piv is None: continue
        A[r], A[piv] = A[piv], A[r]
        pv = A[r][c]; A[r] = [x / pv for x in A[r]]
        for i in range(n):
            if i != r and A[i][c] != 0:
                f = A[i][c]; A[i] = [a - f * b for a, b in zip(A[i], A[r])]
        pivrow[c] = r; r += 1
        if r == n: break
    for i in range(r, n):
        if A[i][cols] != 0: return None
    sol = [Fr(0)] * cols
    for c, i in pivrow.items(): sol[c] = A[i][cols]
    return sol

res = json.loads((HERE / "vol6_results.json").read_text())
t00 = time.time()
out = {}

# rebuild per-graph invariant vectors and count dicts
INV5 = ['N3_triangle', 'N4_square', 'Ndia', 'NK4',
        'N5_pentagon', 'NK23', 'N_theta123', 'NK23_plus_e']
graphs = []
for bn, grec in res["graphs"].items():
    for g in grec:
        N = {int(pi): v for pi, v in g["N"].items()}
        for pi in range(len(patterns)):
            N.setdefault(pi, 0)
        graphs.append({"bn": bn, "name": g["name"], "n": g["n"], "N": N,
                       "S5": {int(e): Fr(c) for e, c in g["S5"].items()},
                       "edges": g["edges"]})
def inv5(g):
    return tuple(g["N"][NAMED[nm]] for nm in INV5)
log("loaded", len(graphs), "graphs")

# ---------- (1)+(4) beta decomposition at sizes <=5 ----------
beta_all = {}
predS5_fail = 0
for k in (2, 3, 4, 5):
    Tk = list(range(len(types[k])))
    M = [[Fr(sub_matrix[(k, tau)].get(pat_index[(k, Y)], 0)) for Y in Tk] for tau in Tk]
    cvec = []
    for tau in Tk:
        if tau in ctypes[k]:
            c6 = cumulants[(k, tau)][6]
            cvec.append(c6)
        else:
            cvec.append({})
    # beta is a vector of q-polys: solve per q-exponent
    exps = sorted({e for c in cvec for e in c})
    beta = {}
    for e in exps:
        b = [c.get(e, Fr(0)) for c in cvec]
        sol = solve_square(M, b)
        for Y, v in zip(Tk, sol):
            if v: beta.setdefault(Y, {})[e] = v
    beta_all[k] = {describe(types[k][Y], k): {str(e): str(v) for e, v in d.items()}
                   for Y, d in beta.items()}
    log(f"size {k}: beta support on {len(beta)} patterns")
out["beta"] = beta_all
# verify S5 = sum_k sum_Y beta_Y N_Y on every graph
for g in graphs:
    pred = {}
    for k in (2, 3, 4, 5):
        Tk = list(range(len(types[k])))
        # recompute beta numerically per exponent from stored description? use matrices again
    # (done below in one pass with matrices rebuilt)
    pass
# rebuild numeric beta dicts
beta_num = {}
for k in (2, 3, 4, 5):
    Tk = list(range(len(types[k])))
    M = [[Fr(sub_matrix[(k, tau)].get(pat_index[(k, Y)], 0)) for Y in Tk] for tau in Tk]
    cvec = [cumulants[(k, tau)][6] if tau in ctypes[k] else {} for tau in Tk]
    exps = sorted({e for c in cvec for e in c})
    beta = {}
    for e in exps:
        sol = solve_square(M, [c.get(e, Fr(0)) for c in cvec])
        for Y, v in zip(Tk, sol):
            if v: beta.setdefault(Y, {})[e] = v
    beta_num[k] = beta
cK1 = cumulants[(1, ctypes[1][0])][6]
for g in graphs:
    pred = {}
    for e, v in cK1.items():
        pred[e] = pred.get(e, Fr(0)) + g["n"] * v
    for k, beta in beta_num.items():
        for Y, d in beta.items():
            pi = pat_index[(k, Y)]
            nv = g["N"][pi]
            if nv:
                for e, v in d.items():
                    pred[e] = pred.get(e, Fr(0)) + nv * v
    pred = {e: c for e, c in pred.items() if c}
    if pred != g["S5"]: predS5_fail += 1
out["S5_equals_beta_sum_failures"] = predS5_fail
log("S5 = sum beta_Y N_Y failures over all graphs:", predS5_fail)

# size 1 contribution: c for K1 at volume 6 is a constant (function of nothing);
# it is included via k=1: Phi_{K1} has only even structure; handle explicitly:
cK1 = cumulants[(1, ctypes[1][0])][6]
log("c_{K1}^{(6)} =", {str(e): str(c) for e, c in cK1.items()},
    "(times n; absorbed in the beta check above if size-1 included)")
# NOTE: sizes start at k=2 in beta above; the K1 part is n * cK1, a function
# of n alone, hence determined. The S5 check including it:
for g in graphs:
    pass

# ---------- (2) determination collision tests ----------
def collision_test(value_fn, label):
    seen = {}
    bad = 0
    for g in graphs:
        key = (g["n"], inv5(g))
        v = value_fn(g)
        if key in seen and seen[key] != v: bad += 1
        seen.setdefault(key, v)
    log(label, "collisions:", bad)
    return bad

out["S5_collision_test"] = collision_test(lambda g: tuple(sorted(g["S5"].items())), "S5^{(6)} on (n,I5) classes:")
pat_coll = {}
for pi, (xk, xt, xm) in enumerate(patterns):
    if xk > 5: continue
    bad = collision_test(lambda g, pi=pi: g["N"][pi], f"  N[{describe(xm, xk)}]:")
    if bad: pat_coll[describe(xm, xk)] = bad
out["size_le5_pattern_collisions"] = pat_coll
log("size<=5 patterns with collisions:", pat_coll)

# ---------- (3) formula fits ----------
BASIS_NAMES = ["1", "N3", "N4", "Ndia", "NK4", "N5", "NK23", "NTheta", "NK23e"]
def basis_row(g, npow):
    base = [Fr(1)] + [Fr(g["N"][NAMED[nm]]) for nm in INV5]
    row = []
    for a in range(npow + 1):
        row += [x * (g["n"] ** a) for x in base]
    return row
BASIS_FULL = [f"n^{a}*{b}" for a in range(4) for b in BASIS_NAMES]

def fit_pattern(pi, sample, full):
    cols = list(zip(*[basis_row(g, 3) for g in sample]))
    sol = solve_span([list(c) for c in cols], [Fr(g["N"][pi]) for g in sample])
    if sol is None: return None
    # verify on all graphs
    for g in full:
        row = basis_row(g, 3)
        if sum(s * x for s, x in zip(sol, row)) != g["N"][pi]:
            return "FIT_FAILED_ON_FULL"
    return {BASIS_FULL[i]: str(sol[i]) for i in range(len(sol)) if sol[i] != 0}

sample = []
for bn in ("n8", "n10", "n12", "n14", "n16"):
    sample += [g for g in graphs if g["bn"] == bn][:80]
fits5 = {}
for pi, (xk, xt, xm) in enumerate(patterns):
    if xk > 5: continue
    f = fit_pattern(pi, sample, graphs)
    fits5[describe(xm, xk)] = f
    log("fit", describe(xm, xk), "->", f if f in (None, "FIT_FAILED_ON_FULL") else "formula found")
out["size_le5_pattern_fits"] = fits5

# connected 6-patterns: fits over I5 basis (for the non-varying ones; the
# variation census itself is in vol6_results.json)
fits6 = {}
for t in CONN6:
    pi = pat_index[(6, t)]
    f = fit_pattern(pi, sample, graphs)
    fits6[describe(types[6][t], 6)] = f
    log("fit6", describe(types[6][t], 6), "->", f if f in (None, "FIT_FAILED_ON_FULL") else "formula found")
out["conn6_pattern_fits_I5basis"] = fits6

out["runtime_seconds"] = round(time.time() - t00, 1)
(HERE / "vol6_relations.json").write_text(json.dumps(out, indent=1))
(HERE / "vol6_relations.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_relations.json")
