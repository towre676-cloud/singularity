#!/usr/bin/env python3
"""Singularity height series at volume 6: exact enumerator library.

Extends vol5_lib.py (volume 5) to MAXV = 6 and graph sizes k <= 6.
Exact arithmetic only (int / fractions.Fraction).  Stdlib only.

Differences from vol5_lib:
  * types / patterns / subgraphs for k = 6 (156 types, 112 connected);
    canonicalisation at k=6 is memoised and restricted to max-degree<=3
    masks (the only ones that occur inside cubic graphs), with the full
    720-permutation min taken over a precomputed bit-source table.
  * cumulant coefficients c_tau = [x^r] Phi_tau for r <= 6, all connected
    types on <= 6 vertices (ambient weights w_v = 3, as in vol5).
  * height_series_fast: incremental-energy enumerator (the scheme of
    singularity_extension.py) returning L through x^6; cross-checked
    against vol5_lib.height_series at volumes <= 5.
  * sub_matrix6: sub_Y(tau) for connected Y, tau on 6 vertices (the block
    needed for the size-6 raw identity and for N_Y of connected Y).
"""
import json, sys, time
from fractions import Fraction as Fr
from itertools import combinations, permutations
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXT = HERE.parent.parent / "improvements_next" / "singularity_extension"
MAXV = 6
KMAX = 6

# ----------------------------------------------------------------------
# A.  Type tables on k <= 6 vertices
# ----------------------------------------------------------------------
PAIRS = {k: [(i, j) for i in range(k) for j in range(i + 1, k)] for k in range(KMAX + 1)}
PIDX = {k: {p: i for i, p in enumerate(PAIRS[k])} for k in range(KMAX + 1)}
PERMS = {k: list(permutations(range(k))) for k in range(KMAX + 1)}
# PERM_SRC[k][pi][p] = source bit index: relabelled bit p comes from this bit
PERM_SRC = {}
for k in range(KMAX + 1):
    tbl = []
    for perm in PERMS[k]:
        src = []
        for (i, j) in PAIRS[k]:
            a, b = perm[i], perm[j]
            if a > b: a, b = b, a
            src.append(PIDX[k][(a, b)])
        tbl.append(tuple(src))
    PERM_SRC[k] = tbl

def relabel(mask, k, pi):
    src = PERM_SRC[k][pi]
    out = 0
    for p in range(len(src)):
        if mask >> src[p] & 1:
            out |= 1 << p
    return out

_canon_memo = {k: {} for k in range(KMAX + 1)}
def canonical(mask, k):
    memo = _canon_memo[k]
    c = memo.get(mask)
    if c is None:
        c = min(relabel(mask, k, pi) for pi in range(len(PERMS[k])))
        memo[mask] = c
    return c

def edges_of(mask, k):
    return [PAIRS[k][p] for p in range(len(PAIRS[k])) if mask >> p & 1]

def degrees_of(mask, k):
    d = [0] * k
    for (i, j) in edges_of(mask, k):
        d[i] += 1; d[j] += 1
    return d

def connected_mask(mask, k):
    if k == 1: return True
    adj = [[] for _ in range(k)]
    for (i, j) in edges_of(mask, k):
        adj[i].append(j); adj[j].append(i)
    seen, stack = {0}, [0]
    while stack:
        v = stack.pop()
        for w in adj[v]:
            if w not in seen: seen.add(w); stack.append(w)
    return len(seen) == k

# types[k]: list of canonical masks; type_id[k][canonical mask] -> index
types, type_id = {}, {}
for k in range(1, KMAX + 1):
    ids, tl = {}, []
    if k <= 5:
        masks = range(1 << len(PAIRS[k]))
    else:
        # generate all 6-vertex types by adding one vertex to each 5-type
        cand = set()
        for m5 in types[5]:
            base = 0
            for (a, b) in edges_of(m5, 5):
                base |= 1 << PIDX[6][(a, b)]
            for sub in range(1 << 5):
                m = base
                for v in range(5):
                    if sub >> v & 1:
                        m |= 1 << PIDX[6][(v, 5)]
                cand.add(m)
        masks = cand
    for mask in masks:
        c = canonical(mask, k)
        if c not in ids:
            ids[c] = len(tl); tl.append(c)
    types[k] = tl; type_id[k] = ids

# mask_type[k][mask] -> type index.  For k=6 only max-degree<=3 masks are
# tabulated (others never occur as induced subgraphs of cubic graphs);
# use type_of() which falls back to canonicalisation.
mask_type = {}
for k in range(1, KMAX + 1):
    if k <= 5:
        mask_type[k] = [type_id[k][canonical(m, k)] for m in range(1 << len(PAIRS[k]))]
    else:
        mt = {}
        for m in range(1 << len(PAIRS[k])):
            if max(degrees_of(m, k)) <= 3:
                mt[m] = type_id[k][canonical(m, k)]
        mask_type[k] = mt

def type_of(mask, k):
    mt = mask_type[k]
    if k <= 5:
        return mt[mask]
    t = mt.get(mask)
    if t is None:
        t = type_id[k][canonical(mask, k)]
        mt[mask] = t
    return t

def aut_count(mask, k):
    return sum(1 for pi in range(len(PERMS[k])) if relabel(mask, k, pi) == mask)

ctypes = {k: [t for t, m in enumerate(types[k]) if connected_mask(m, k)] for k in range(1, KMAX + 1)}

def spanning_poly(mask, k):
    """P(H) = sum over connected spanning edge subsets E' of f^|E'|,
    as dict fpow -> int."""
    E = edges_of(mask, k)
    out = {}
    for sub in range(1 << len(E)):
        submask = 0
        for i, (a, b) in enumerate(E):
            if sub >> i & 1: submask |= 1 << PIDX[k][(a, b)]
        if connected_mask(submask, k):
            out[bin(sub).count("1")] = out.get(bin(sub).count("1"), 0) + 1
    return out

def tri_count(mask, k):
    E = set(edges_of(mask, k))
    c = 0
    for a, b, cc in combinations(range(k), 3):
        if (a, b) in E and (b, cc) in E and (a, cc) in E: c += 1
    return c

def sub_count(xmask, xk, tmask, tk):
    """# subgraphs of (tmask,tk) isomorphic to (xmask,xk), xk <= tk.
    Injective maps / |Aut(X)|, with edge/triangle pruning."""
    if xk > tk: return 0
    xe = edges_of(xmask, xk)
    if len(xe) > len(edges_of(tmask, tk)): return 0
    if xk == tk and tri_count(xmask, xk) > tri_count(tmask, tk): return 0
    tset = set(edges_of(tmask, tk))
    cnt = 0
    for inj in permutations(range(tk), xk):
        ok = True
        for (i, j) in xe:
            a, b = inj[i], inj[j]
            if a > b: a, b = b, a
            if (a, b) not in tset: ok = False; break
        if ok: cnt += 1
    return cnt // aut_count(xmask, xk)

# pattern list: all graphs on <=6 vertices
patterns = []
for k in range(1, KMAX + 1):
    for t, m in enumerate(types[k]):
        patterns.append((k, t, m))
pat_index = {(k, t): i for i, (k, t, m) in enumerate(patterns)}

# sub_matrix[(k,t)]: pattern_index -> count, patterns X of size exactly k,
# for k <= 5 (all patterns) -- as in vol5.
sub_matrix = {}
for k in range(1, 6):
    for t in range(len(types[k])):
        m = types[k][t]
        row = {}
        for pi, (xk, xt, xm) in enumerate(patterns):
            if xk != k: continue
            c = sub_count(xm, xk, m, k)
            if c: row[pi] = c
        sub_matrix[(k, t)] = row

# sub_matrix6[(tau, Y)]: connected Y in connected tau on 6 vertices.
sub_matrix6 = {}
for tau in ctypes[6]:
    mt = types[6][tau]
    row = {}
    for Y in ctypes[6]:
        c = sub_count(types[6][Y], 6, mt, 6)
        if c: row[Y] = c
    sub_matrix6[tau] = row

P_poly = {}
for k in range(1, KMAX + 1):
    for t in ctypes[k]:
        P_poly[(k, t)] = spanning_poly(types[k][t], k)

def describe(mask, k):
    e = len(edges_of(mask, k))
    degs = degrees_of(mask, k)
    return f"k{k}_e{e}_deg{''.join(map(str, sorted(degs, reverse=True)))}_m{mask}"

# ----------------------------------------------------------------------
# polynomial helpers: dict qexp -> Fr
# ----------------------------------------------------------------------
def pmul(A, B):
    out = {}
    for ea, ca in A.items():
        for eb, cb in B.items():
            out[ea + eb] = out.get(ea + eb, Fr(0)) + ca * cb
    return {e: c for e, c in out.items() if c}

def series_log(A, R):
    B = [{0: Fr(1)}] + [dict() for _ in range(R)]
    for t in range(1, R + 1):
        acc = {e: Fr(t) * c for e, c in A[t].items()}
        for j in range(1, t):
            term = pmul({e: Fr(j) * c for e, c in B[j].items()}, A[t - j])
            for e, c in term.items():
                acc[e] = acc.get(e, Fr(0)) - c
        B[t] = {e: c / t for e, c in acc.items() if c}
    return B

def compositions(total, parts):
    if parts == 1:
        yield (total,); return
    for v in range(total + 1):
        for rest in compositions(total - v, parts - 1):
            yield (v,) + rest

# ----------------------------------------------------------------------
# B.  Cumulants for connected types on <=6 vertices, volumes <= 6
# ----------------------------------------------------------------------
def cumulant_coeffs(mask, k, R=MAXV):
    """Phi_H for representative H=(mask,k): list over volumes 0..R of
    q-polys [x^r] Phi_H (ambient weights w=3)."""
    E = edges_of(mask, k)
    verts = list(range(k))
    logZ = {}
    for T in range(1 << k):
        Tv = [v for v in verts if T >> v & 1]
        pos = {v: i for i, v in enumerate(Tv)}
        ET = [(pos[a], pos[b]) for (a, b) in E if a in pos and b in pos]
        A = [{0: Fr(1)}] + [dict() for _ in range(R)]
        if Tv:
            nt = len(Tv)
            for tot in range(1, R + 1):
                for h in compositions(tot, nt):
                    en = 3 * sum(x * x for x in h)
                    for (a, b) in ET:
                        en -= 2 * h[a] * h[b]
                    A[tot][en] = A[tot].get(en, Fr(0)) + 1
        logZ[T] = series_log(A, R)
    Phi = [dict() for _ in range(R + 1)]
    for T in range(1 << k):
        sign = 1 if (k - bin(T).count("1")) % 2 == 0 else -1
        for r in range(R + 1):
            for e, c in logZ[T][r].items():
                Phi[r][e] = Phi[r].get(e, Fr(0)) + sign * c
    return [{e: c for e, c in p.items() if c} for p in Phi]

cumulants = {}
for k in range(1, KMAX + 1):
    for t in ctypes[k]:
        cumulants[(k, t)] = cumulant_coeffs(types[k][t], k)

# ----------------------------------------------------------------------
# C.  Graph computations
# ----------------------------------------------------------------------
def height_series_fast(n, edges, R=MAXV):
    """L through x^R by incremental-energy recursion (exact ints).
    Returns list over volumes of dict energy -> count."""
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b); adj[b].append(a)
    L = [{0: 1}] + [dict() for _ in range(R)]
    h = [0] * n
    def rec(v, rem, tot, energy):
        if v == n - 1:
            x = rem
            e = energy
            for u in adj[v]:
                if u < v:
                    d = x - h[u]; e += d * d
            L[tot][e] = L[tot].get(e, 0) + 1
            return
        for x in range(rem + 1):
            e = energy
            for u in adj[v]:
                if u < v:
                    d = x - h[u]; e += d * d
            h[v] = x
            rec(v + 1, rem - x, tot, e)
        h[v] = 0
    for tot in range(1, R + 1):
        rec(0, tot, tot, 0)
    return L

def height_series_slow(n, edges, R=MAXV):
    """vol5-style enumerator (energy from scratch), for cross-checks."""
    L = [{0: 1}] + [dict() for _ in range(R)]
    h = [0] * n
    def rec(v, rem, tot):
        if v == n - 1:
            h[v] = rem
            en = 0
            for a, b in edges:
                d = h[a] - h[b]; en += d * d
            L[tot][en] = L[tot].get(en, 0) + 1
            return
        for x in range(rem + 1):
            h[v] = x
            rec(v + 1, rem - x, tot)
    for tot in range(1, R + 1):
        rec(0, tot, tot)
    return L

def induced_counts(n, edges, kmax=KMAX):
    """s_tau for ALL types tau with |tau| <= kmax (naive subsets)."""
    adj = [set() for _ in range(n)]
    for a, b in edges: adj[a].add(b); adj[b].add(a)
    counts = {}
    for k in range(1, kmax + 1):
        Pk = PAIRS[k]; pik = PIDX[k]
        for S in combinations(range(n), k):
            mask = 0
            for p, (i, j) in enumerate(Pk):
                if S[j] in adj[S[i]]: mask |= 1 << p
            t = type_of(mask, k)
            counts[(k, t)] = counts.get((k, t), 0) + 1
    return counts

def subgraph_counts_all(s_counts):
    """N_X(G) for every pattern X on <=5 vertices, and for connected
    patterns X on 6 vertices, from induced counts s_counts."""
    N = {}
    by_k = {}
    for (k, t), s in s_counts.items(): by_k.setdefault(k, {})[t] = s
    for pi, (xk, xt, xm) in enumerate(patterns):
        if xk <= 5:
            tot = 0
            for t, s in by_k.get(xk, {}).items():
                c = sub_matrix[(xk, t)].get(pi, 0)
                if c: tot += s * c
            N[pi] = tot
    # connected 6-patterns
    for Y in ctypes[6]:
        pi = pat_index[(6, Y)]
        tot = 0
        for tau, s in by_k.get(6, {}).items():
            if tau in sub_matrix6:
                c = sub_matrix6[tau].get(Y, 0)
                if c: tot += s * c
        N[pi] = tot
    return N

def count_in_pattern(n, edges, pi):
    """Direct subgraph count of pattern pi in G (brute force, for checks)."""
    xk, xt, xm = patterns[pi]
    adj = [set() for _ in range(n)]
    for a, b in edges: adj[a].add(b); adj[b].add(a)
    xe = edges_of(xm, xk)
    cnt = 0
    for inj in permutations(range(n), xk):
        if all(inj[j] in adj[inj[i]] for (i, j) in xe): cnt += 1
    return cnt // aut_count(xm, xk)

# pattern indices of named invariants
def find_pattern(k, mask):
    return pat_index[(k, type_id[k][canonical(mask, k)])]

def mask_from_edges(k, edgelist):
    m = 0
    for (a, b) in edgelist:
        if a > b: a, b = b, a
        m |= 1 << PIDX[k][(a, b)]
    return m

NAMED = {}
NAMED['N3_triangle'] = find_pattern(3, mask_from_edges(3, [(0,1),(1,2),(0,2)]))
NAMED['N4_square'] = find_pattern(4, mask_from_edges(4, [(0,1),(1,2),(2,3),(3,0)]))
NAMED['Ndia'] = find_pattern(4, mask_from_edges(4, [(0,1),(1,2),(2,3),(3,0),(0,2)]))
NAMED['NK4'] = find_pattern(4, mask_from_edges(4, [(0,1),(1,2),(2,3),(3,0),(0,2),(1,3)]))
NAMED['N5_pentagon'] = find_pattern(5, mask_from_edges(5, [(0,1),(1,2),(2,3),(3,4),(4,0)]))
NAMED['NK23'] = find_pattern(5, mask_from_edges(5, [(0,2),(0,3),(0,4),(1,2),(1,3),(1,4)]))
NAMED['N_theta123'] = find_pattern(5, mask_from_edges(5, [(0,1),(0,2),(2,1),(0,3),(3,4),(4,1)]))
NAMED['N_bowtie'] = find_pattern(5, mask_from_edges(5, [(0,1),(1,2),(2,0),(0,3),(3,4),(4,0)]))
NAMED['NK23_plus_e'] = find_pattern(5, mask_from_edges(5, [(0,2),(0,3),(0,4),(1,2),(1,3),(1,4),(2,3)]))
NAMED['N6_hexagon'] = find_pattern(6, mask_from_edges(6, [(0,1),(1,2),(2,3),(3,4),(4,5),(5,0)]))
NAMED['NK33'] = find_pattern(6, mask_from_edges(6, [(i, 3+j) for i in range(3) for j in range(3)]))
NAMED['Nprism'] = find_pattern(6, mask_from_edges(6, [(0,1),(1,2),(2,0),(3,4),(4,5),(5,3),(0,3),(1,4),(2,5)]))

# connected 6-patterns with max degree <= 3 (non-vacuous in cubic graphs)
CONN6 = [t for t in ctypes[6] if max(degrees_of(types[6][t], 6)) <= 3]
CONN6_PI = [pat_index[(6, t)] for t in CONN6]
