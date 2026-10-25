#!/usr/bin/env python3
"""Singularity height series at volume 5: computation, cumulants, fits.

Exact arithmetic only (int / fractions.Fraction).  Stdlib only.

Phases
  A  type tables for all graphs on <=5 vertices (canonical forms, spanning
     polynomials P(tau), subgraph-count matrix sub_X(tau)).
  B  cumulant coefficients c_tau = [x^5] Phi_tau for every connected type
     on <=5 vertices, from the definition Phi_S = sum_T (-1)^... log Z_T
     with ambient cubic weights w_v = 3.
  C  pool graphs (n=8 regenerated sampler pool + cube/Mobius; n=10, n=12
     stored pools): height series L through x^5, log coefficients,
     induced type counts s_tau, subgraph counts N_X.
  D  checks: totals, stored counts, ell_5 = sum_tau s_tau c_tau.
  E  agreeing-through-volume-4 pairs: Delta L_5 fits and decomposition.
"""
import json, sys, time
from fractions import Fraction as Fr
from itertools import combinations, permutations
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXT = HERE  # stored pools live beside these scripts (singularity_extension.json, added by the height-series extension change)
MAXV = 5

# ----------------------------------------------------------------------
# A.  Type tables on k <= 5 vertices
# ----------------------------------------------------------------------
PAIRS = {k: [(i, j) for i in range(k) for j in range(i + 1, k)] for k in range(6)}
PIDX = {k: {p: i for i, p in enumerate(PAIRS[k])} for k in range(6)}
PERMS = {k: list(permutations(range(k))) for k in range(6)}

def relabel(mask, k, perm):
    """perm[new_label] = old vertex; returns mask in new labels."""
    out = 0
    for p, (i, j) in enumerate(PAIRS[k]):
        a, b = perm[i], perm[j]
        if a > b: a, b = b, a
        if mask >> PIDX[k][(a, b)] & 1:
            out |= 1 << p
    return out

def canonical(mask, k):
    return min(relabel(mask, k, p) for p in PERMS[k])

# types[k]: list of canonical masks; type_id[k][mask] -> index
types, type_id, mask_type = {}, {}, {}
for k in range(1, 6):
    ids, tl = {}, []
    for mask in range(1 << len(PAIRS[k])):
        c = canonical(mask, k)
        if c not in ids:
            ids[c] = len(tl); tl.append(c)
    types[k] = tl; type_id[k] = ids
    mask_type[k] = [ids[canonical(m, k)] for m in range(1 << len(PAIRS[k]))]

def edges_of(mask, k):
    return [PAIRS[k][p] for p in range(len(PAIRS[k])) if mask >> p & 1]

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

def aut_count(mask, k):
    return sum(1 for p in PERMS[k] if relabel(mask, k, p) == mask)

# connected types (the support types of SNG-F55)
ctypes = {k: [t for t, m in enumerate(types[k]) if connected_mask(m, k)] for k in range(1, 6)}

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

def sub_count(xmask, xk, tmask, tk):
    """# subgraphs of the graph (tmask on tk vertices) isomorphic to
    (xmask on xk vertices), xk <= tk.  Injective maps / |Aut(X)|."""
    if xk > tk: return 0
    cnt = 0
    for inj in permutations(range(tk), xk):
        ok = True
        for (i, j) in edges_of(xmask, xk):
            a, b = inj[i], inj[j]
            if a > b: a, b = b, a
            if not (tmask >> PIDX[tk][(a, b)]) & 1: ok = False; break
        if ok: cnt += 1
    return cnt // aut_count(xmask, xk)

# pattern list: all graphs on <=5 vertices (as potential subgraph patterns)
patterns = []          # (k, type_index, canonical_mask)
for k in range(1, 6):
    for t, m in enumerate(types[k]):
        patterns.append((k, t, m))
pat_index = {(k, t): i for i, (k, t, m) in enumerate(patterns)}

# sub_matrix[(k,t)] : dict pattern_index -> count, for ALL host types t
# (pattern X ranges over all graphs on xk <= k vertices)
sub_matrix = {}
P_poly = {}
for k in range(1, 6):
    for t in range(len(types[k])):
        m = types[k][t]
        row = {}
        for pi, (xk, xt, xm) in enumerate(patterns):
            if xk > k: continue
            c = sub_count(xm, xk, m, k)
            if c: row[pi] = c
        sub_matrix[(k, t)] = row
    for t in ctypes[k]:
        P_poly[(k, t)] = spanning_poly(types[k][t], k)

TYPE_NAMES = {
    # (k, canonical mask) -> human name where classical
}

def describe(mask, k):
    e = len(edges_of(mask, k))
    degs = [0] * k
    for (i, j) in edges_of(mask, k): degs[i] += 1; degs[j] += 1
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
    """A: list over volumes 0..R of q-polys (dicts), A[0] = {0:1}.
    Returns B = log A (list of dicts), exact."""
    B = [{0: Fr(1)}] + [dict() for _ in range(R)]
    # t*A[t] = sum_{j=1..t} j*B[j]*A[t-j]  (ordinary series, x-derivative)
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
# B.  Cumulants for connected types on <=5 vertices
# ----------------------------------------------------------------------
def cumulant_coeffs(mask, k, R=MAXV):
    """Phi_H for the representative graph H = (mask,k): returns list over
    volumes 0..R of q-polys [x^r]Phi_H (ambient weights w=3)."""
    E = edges_of(mask, k)
    verts = list(range(k))
    logZ = {}
    for T in range(1 << k):
        Tv = [v for v in verts if T >> v & 1]
        ET = [(a, b) for (a, b) in E if a in Tv and b in Tv]
        A = [{0: Fr(1)}] + [dict() for _ in range(R)]
        if Tv:
            for tot in range(1, R + 1):
                for h in compositions(tot, len(Tv)):
                    en = 3 * sum(x * x for x in h)
                    for (a, b) in ET:
                        en -= 2 * h[Tv.index(a)] * h[Tv.index(b)]
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
for k in range(1, 6):
    for t in ctypes[k]:
        cumulants[(k, t)] = cumulant_coeffs(types[k][t], k)

# ----------------------------------------------------------------------
# C.  Graph computations
# ----------------------------------------------------------------------
def height_series(n, edges, R=MAXV):
    adj = [[0] * n for _ in range(n)]
    for a, b in edges: adj[a][b] = adj[b][a] = 1
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

def induced_counts(n, edges):
    adj = [set() for _ in range(n)]
    for a, b in edges: adj[a].add(b); adj[b].add(a)
    counts = {}
    for k in range(1, 6):
        for S in combinations(range(n), k):
            mask = 0
            for p, (i, j) in enumerate(PAIRS[k]):
                if S[j] in adj[S[i]]: mask |= 1 << p
            t = mask_type[k][mask]
            counts[(k, t)] = counts.get((k, t), 0) + 1
    return counts

def subgraph_counts(s_counts):
    """N_X for all patterns from induced counts."""
    N = {}
    for (k, t), s in s_counts.items():
        if s == 0: continue
        for pi, c in sub_matrix[(k, t)].items():
            if patterns[pi][0] == k:      # subgraphs on exactly |X|=k verts
                N[pi] = N.get(pi, 0) + s * c
    # patterns on fewer vertices: counted via types of their own size
    return N

def full_subgraph_counts(s_counts):
    """N_X(G) for every pattern X: sum over types tau with |tau|=|X|."""
    N = {}
    by_k = {}
    for (k, t), s in s_counts.items(): by_k.setdefault(k, {})[t] = s
    for pi, (xk, xt, xm) in enumerate(patterns):
        tot = 0
        for t, s in by_k.get(xk, {}).items():
            c = sub_matrix[(xk, t)].get(pi, 0)
            if c: tot += s * c
        N[pi] = tot
    return N

def cycle_count(n, edges, length):
    adj = [set() for _ in range(n)]
    for a, b in edges: adj[a].add(b); adj[b].add(a)
    cnt = 0
    def dfs(start, v, path):
        nonlocal cnt
        if len(path) == length:
            if start in adj[v]: cnt += 1
            return
        for w in adj[v]:
            if w > start and w not in path:
                dfs(start, w, path + [w])
    for s in range(n): dfs(s, s, [s])
    return cnt // 2

def count_in_pattern(n, edges, pi):
    """Direct subgraph count of pattern pi in G (brute force, for checks)."""
    xk, xt, xm = patterns[pi]
    adj = [set() for _ in range(n)]
    for a, b in edges: adj[a].add(b); adj[b].add(a)
    cnt = 0
    for inj in permutations(range(n), xk):
        if all(inj[j] in adj[inj[i]] for (i, j) in edges_of(xm, xk)): cnt += 1
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
