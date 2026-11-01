#!/usr/bin/env python3
"""Volume 6: the K3,3-e (mask 2012) determination problem.
N_{K3,3-e} never varies on agreeing pairs, but no formula over
{n^a * I5 : a<=3} fits it.  Try wider bases:
 (A) n^a (a<=5) * I5, plus pairwise products of I5 entries;
 (B) original basis + the 8 new size-6 invariants (linear);
 (C) n^a (a<=5) * I5 alone (higher n-degree);
and verify the three n-only size<=5 pattern identities."""
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
INV5 = ['N3_triangle', 'N4_square', 'Ndia', 'NK4',
        'N5_pentagon', 'NK23', 'N_theta123', 'NK23_plus_e']
graphs = []
for bn, grec in res["graphs"].items():
    for g in grec:
        N = {int(pi): v for pi, v in g["N"].items()}
        for pi in range(len(patterns)): N.setdefault(pi, 0)
        graphs.append({"bn": bn, "n": g["n"], "N": N})
sample = []
for bn in ("n8", "n10", "n12", "n14", "n16"):
    sample += [g for g in graphs if g["bn"] == bn][:80]

def solve_span(basis_cols, target):
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

t2012 = [t for t in ctypes[6] if types[6][t] == 2012][0]
pi2012 = pat_index[(6, t2012)]
NEW_MASKS = [1880, 1881, 956, 1884, 5907, 1916, 5948, 5941]
pi_new = [pat_index[(6, [t for t in ctypes[6] if types[6][t] == m][0])] for m in NEW_MASKS]

def try_fit(name, row_fn, col_names):
    cols = list(zip(*[row_fn(g) for g in sample]))
    sol = solve_span([list(c) for c in cols], [Fr(g["N"][pi2012]) for g in sample])
    if sol is None:
        log(name, ": no fit on sample"); return None
    bad = 0
    for g in graphs:
        if sum(s * x for s, x in zip(sol, row_fn(g))) != g["N"][pi2012]: bad += 1
    log(name, ": fit on sample; full-data failures:", bad)
    if bad == 0:
        return {col_names[i]: str(sol[i]) for i in range(len(sol)) if sol[i] != 0}
    return "sample-only"

def base9(g):
    return [Fr(1)] + [Fr(g["N"][NAMED[nm]]) for nm in INV5]

# (C) higher n-degree
namesC = [f"n^{a}*{b}" for a in range(6) for b in ["1","N3","N4","Ndia","NK4","N5","NK23","NTh","NK23e"]]
fitC = try_fit("(C) n^a a<=5 x I5", lambda g: [x * g["n"]**a for a in range(6) for x in base9(g)], namesC)
# (A) products
def rowA(g):
    b = base9(g)
    row = [x * g["n"]**a for a in range(4) for x in b]
    row += [b[i] * b[j] for i in range(1, 9) for j in range(i, 9)]
    return row
namesA = namesC[:36] + [f"P{i}x{j}" for i in range(1, 9) for j in range(i, 9)]
fitA = try_fit("(A) n^a a<=3 x I5 + I5 products", rowA, namesA)
# (B) + new invariants
def rowB(g):
    b = base9(g)
    row = [x * g["n"]**a for a in range(4) for x in b]
    row += [Fr(g["N"][p]) * g["n"]**a for a in range(2) for p in pi_new]
    return row
namesB = namesC[:36] + [f"n^{a}*new{m}" for a in range(2) for m in NEW_MASKS]
fitB = try_fit("(B) n^a a<=3 x I5 + new8 (a<=1)", rowB, namesB)

# n-only size<=5 identities
chk = {"C(n,4)": 0, "C(n,5)": 0, "m*C(n-2,3)": 0}
for g in graphs:
    n = g["n"]
    for pi, (xk, xt, xm) in enumerate(patterns):
        if describe(xm, xk) == "k4_e0_deg0000_m0":
            if g["N"][pi] != comb(n, 4): chk["C(n,4)"] += 1
        if describe(xm, xk) == "k5_e0_deg00000_m0":
            if g["N"][pi] != comb(n, 5): chk["C(n,5)"] += 1
        if describe(xm, xk) == "k5_e1_deg11000_m1":
            if g["N"][pi] != (3 * n // 2) * comb(n - 2, 3): chk["m*C(n-2,3)"] += 1
log("n-only identity failures:", chk)

out = {"fitC": fitC, "fitA": fitA, "fitB": fitB, "n_only_failures": chk}
(HERE / "vol6_m2012.json").write_text(json.dumps(out, indent=1, default=str))
(HERE / "vol6_m2012.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_m2012.json")
