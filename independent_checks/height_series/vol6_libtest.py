#!/usr/bin/env python3
"""Self-tests for vol6_lib: type tables, cumulant identities, the size-6
alpha decomposition, height enumerators, SNG-F55 at volume 6."""
import json, sys, time
from fractions import Fraction as Fr
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
t0 = time.time()
from vol6_lib import *
HERE = Path(__file__).resolve().parent
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)

log("import + tables built in", round(time.time() - t0, 1), "s")
for k in range(1, 7):
    log(f"k={k}: types {len(types[k])} connected {len(ctypes[k])}")
assert [len(types[k]) for k in range(1, 7)] == [1, 2, 4, 11, 34, 156]
assert [len(ctypes[k]) for k in range(1, 7)] == [1, 1, 2, 6, 21, 112]
log("type counts OK (1,2,4,11,34,156 / 1,1,2,6,21,112)")

# max-degree<=3 connected types on 6 vertices
log("connected 6-types with maxdeg<=3:", len(CONN6), "of", len(ctypes[6]))

# multilinear identity [x^k] Phi_tau = a^k P(tau), and Phi vanishes below k
for k in range(1, 7):
    for t in ctypes[k]:
        pred = {}
        for j, c in P_poly[(k, t)].items():
            for s in range(j + 1):
                e = 3 * k - 2 * s
                pred[e] = pred.get(e, Fr(0)) + c * comb(j, s) * (-1) ** (j - s)
        got = cumulants[(k, t)][k]
        assert got == {e: c for e, c in pred.items() if c}, (k, t)
        for r in range(k):
            assert not cumulants[(k, t)][r], (k, t, r)
    log(f"multilinear identity + vanishing below k: k={k} OK")

# size-6 alpha identity: P_j(tau) = sum_{Y conn, e(Y)=j} sub_Y(tau)
by_e = {}
for Y in ctypes[6]:
    by_e.setdefault(len(edges_of(types[6][Y], 6)), []).append(Y)
bad = 0
for tau in ctypes[6]:
    for j in range(0, 16):
        lhs = P_poly[(6, tau)].get(j, 0)
        rhs = sum(sub_matrix6[tau].get(Y, 0) for Y in by_e.get(j, []))
        if lhs != rhs: bad += 1
assert bad == 0
log("size-6 alpha identity P_j(tau) = sum_{Y conn, e(Y)=j} sub_Y(tau): OK for all 112 connected types")

# subgraph matrix ranks at sizes <= 5 (invertibility)
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
for k in (2, 3, 4, 5):
    Tk = list(range(len(types[k])))
    Mk = [[Fr(sub_matrix[(k, tau)].get(pat_index[(k, Y)], 0)) for Y in Tk] for tau in Tk]
    rk = rank(Mk)
    assert rk == len(Tk), (k, rk)
    log(f"size-{k} subgraph matrix rank {rk} of {len(Tk)} (invertible)")

# height enumerators agree; totals; SNG-F55 at volume 6 on sample graphs
import importlib.util
spec = importlib.util.spec_from_file_location("orig_ext", EXT / "singularity_extension.py")
orig = importlib.util.module_from_spec(spec); spec.loader.exec_module(orig)

def check_graph(n, edges, name):
    Lf = height_series_fast(n, edges)
    Ls = height_series_slow(n, edges, R=5)
    for r in range(6):
        assert Lf[r] == Ls[r], (name, r)
    for r in range(7):
        assert sum(Lf[r].values()) == comb(n + r - 1, r), (name, r)
    ell = series_log([{e: Fr(c) for e, c in p.items()} for p in Lf], MAXV)
    sc = induced_counts(n, edges)
    for r in (5, 6):
        pred = {}
        for (k, t), s in sc.items():
            if s == 0 or (k, t) not in cumulants: continue
            for e, c in cumulants[(k, t)][r].items():
                pred[e] = pred.get(e, Fr(0)) + s * c
        pred = {e: c for e, c in pred.items() if c}
        assert pred == ell[r], (name, r)
    log(f"graph {name}: fast==slow (r<=5), totals r<=6, ell_5 and ell_6 SNG-F55 identities OK")

check_graph(8, orig.cube_edges(), "cube_Q3")
check_graph(8, orig.mobius_ladder(8), "mobius_M8")
check_graph(10, orig.petersen(), "petersen")
check_graph(6, [(i, 3 + j) for i in range(3) for j in range(3)], "K3,3")
check_graph(6, [(0,1),(1,2),(2,0),(3,4),(4,5),(5,3),(0,3),(1,4),(2,5)], "prism")
log("ALL LIB TESTS PASSED in", round(time.time() - t0, 1), "s")
(HERE / "vol6_libtest.log").write_text("\n".join(LOG) + "\n")
