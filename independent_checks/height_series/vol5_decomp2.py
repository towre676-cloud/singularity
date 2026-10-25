#!/usr/bin/env python3
"""Volume 5, phase 2b: correct decomposition over ALL 34 types on 5 vertices.

For each f-power j, the vector P_j (P-poly coefficient on connected types,
0 on disconnected types) is expressed in the basis of pattern functionals
g_Y(tau) = sub_Y(tau), Y over all 34 graphs on 5 vertices.  The subgraph /
induced-count matrix is invertible (triangular in edge count, diagonal 1),
so the coefficients alpha_{Y,j} are UNIQUE and
   sum_tau s_tau P_j(tau) = sum_Y alpha_{Y,j} N_Y(G)
holds for every graph G.  Same method at size 4 and <=3 for the
determination statements."""
import json, sys
from fractions import Fraction as Fr
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol5_lib import *
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

def rank(rows):
    rows = [list(r) for r in rows]
    if not rows: return 0
    m, n = len(rows), len(rows[0]); r = 0
    for c in range(n):
        piv = next((i for i in range(r, m) if rows[i][c] != 0), None)
        if piv is None: continue
        rows[r], rows[piv] = rows[piv], rows[r]
        pv = rows[r][c]; rows[r] = [x / pv for x in rows[r]]
        for i in range(m):
            if i != r and rows[i][c] != 0:
                f = rows[i][c]; rows[i] = [a - f * b for a, b in zip(rows[i], rows[r])]
        r += 1
        if r == m: break
    return r

out = {}
# ---- size 5: M[tau][Y] = sub_Y(tau), tau,Y over all 34 types on 5 vertices
T5 = list(range(len(types[5])))
M5 = [[Fr(sub_matrix[(5, tau)].get(pat_index[(5, Y)], 0)) for Y in T5] for tau in T5]
out["M5_rank"] = rank(M5)
log("size-5 subgraph matrix rank:", out["M5_rank"], "of", len(T5))
alpha = {}
for j in range(0, 11):
    b = [Fr(P_poly[(5, tau)].get(j, 0)) if tau in ctypes[5] else Fr(0) for tau in T5]
    if all(x == 0 for x in b): continue
    sol = solve_square(M5, b)
    # verify
    for tau in T5:
        assert sum(M5[tau][Y] * sol[Y] for Y in T5) == b[tau]
    alpha[j] = {Y: sol[Y] for Y in T5 if sol[Y] != 0}
    log(f"f^{j}: support", {describe(types[5][Y], 5): str(c) for Y, c in alpha[j].items()})
out["alpha_P"] = {str(j): {describe(types[5][Y], 5): str(c) for Y, c in a.items()}
                  for j, a in alpha.items()}
inv_named = {v: k for k, v in NAMED.items()}
out["alpha_P_named"] = {str(j): {inv_named.get(pat_index[(5, Y)], describe(types[5][Y], 5)): str(c)
                                 for Y, c in a.items()} for j, a in alpha.items()}

# ---- size 4: same basis argument for the doubled coefficients d_tau.
# First: the 11 four-vertex pattern counts are old-determined; verify the
# explicit formulas on every pool graph (done in verify script); here just
# record the matrix rank (invertibility) at sizes 4,3,2.
for k in (4, 3, 2):
    Tk = list(range(len(types[k])))
    Mk = [[Fr(sub_matrix[(k, tau)].get(pat_index[(k, Y)], 0)) for Y in Tk] for tau in Tk]
    out[f"M{k}_rank"] = rank(Mk)
    log(f"size-{k} subgraph matrix rank:", out[f"M{k}_rank"], "of", len(Tk))

# ---- which alphas survive: group by pattern across j
bysupport = {}
for j, a in alpha.items():
    for Y, c in a.items():
        bysupport.setdefault(Y, {})[j] = c
out["patterns_in_raw_formula"] = {
    inv_named.get(pat_index[(5, Y)], describe(types[5][Y], 5)):
    {str(j): str(c) for j, c in v.items()} for Y, v in bysupport.items()}
log("raw formula patterns:", out["patterns_in_raw_formula"])

(HERE / "vol5_decomp2.json").write_text(json.dumps(out, indent=1))
(HERE / "vol5_decomp2.log").write_text("\n".join(LOG) + "\n")
log("wrote vol5_decomp2.json")
