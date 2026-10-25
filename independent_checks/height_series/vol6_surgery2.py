#!/usr/bin/env python3
"""Volume 6, K3,3 surgery v2: like vol6_surgery but (a) B may be
disconnected -- the objective adds a large penalty for every K3,3 or
prism component of B (those are the only way N_K3,3 / N_prism can be
nonzero), (b) double-switch proposals, (c) reheating on stagnation.
Target: I5(B) = I5(K3,3 (+) H), H = the same n=18 pool graph as v1."""
import json, random, sys, time
from fractions import Fraction as Fr
from math import comb
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vol6_lib import *
HERE = Path(__file__).resolve().parent
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)

INV5 = ['N3_triangle', 'N4_square', 'Ndia', 'NK4',
        'N5_pentagon', 'NK23', 'N_theta123', 'NK23_plus_e']
TGT = {}
for nm in INV5:
    pi = NAMED[nm]; (k, t, m) = patterns[pi]
    TGT.setdefault(k, []).append((nm, t))

def i5_of(n, edges):
    s = induced_counts(n, edges, 5)
    N = subgraph_counts_all(s)
    return tuple(N.get(NAMED[x], 0) for x in INV5)

def conn_sets_through(x, y, adj, kmax=5):
    start = frozenset((x, y))
    seen = {start}; frontier = [start]; out = [start]
    while frontier:
        nxt = []
        for S in frontier:
            if len(S) >= kmax: continue
            cand = set()
            for v in S: cand |= adj[v]
            cand -= S
            for w in cand:
                S2 = frozenset(set(S) | {w})
                if S2 not in seen:
                    seen.add(S2); out.append(S2); nxt.append(S2)
        frontier = nxt
    return out

def contrib(S, adj):
    vs = sorted(S); k = len(vs)
    pos = {v: i for i, v in enumerate(vs)}
    mask = 0
    for v in vs:
        for w in adj[v]:
            if w in pos and pos[v] < pos[w]:
                mask |= 1 << PIDX[k][(pos[v], pos[w])]
    t = type_of(mask, k)
    row = sub_matrix[(k, t)]
    vec = {}
    for (nm, tt) in TGT.get(k, []):
        c = row.get(pat_index[(k, tt)], 0)
        if c: vec[nm] = c
    return vec

def multi_switch_delta(adj, removed, added):
    adjB = [set(s) for s in adj]
    for (x, y) in removed:
        adjB[x].discard(y); adjB[y].discard(x)
    for (x, y) in added:
        adjB[x].add(y); adjB[y].add(x)
    sets = set()
    for (x, y) in list(removed) + list(added):
        for S in conn_sets_through(x, y, adj): sets.add(S)
        for S in conn_sets_through(x, y, adjB): sets.add(S)
    d = {}
    for S in sets:
        cb = contrib(S, adj); ca = contrib(S, adjB)
        for nm in set(cb) | set(ca):
            dv = ca.get(nm, 0) - cb.get(nm, 0)
            if dv: d[nm] = d.get(nm, 0) + dv
    return d

def edges_to_adj(n, edges):
    adj = [set() for _ in range(n)]
    for (u, v) in edges:
        adj[u].add(v); adj[v].add(u)
    return adj
def adj_to_edges(adj):
    return sorted((u, v) for u in range(len(adj)) for v in adj[u] if u < v)

def bad_components(adj):
    """# components that are K3,3 or prism (6 vertices, 9 edges)."""
    n = len(adj); seen = [False] * n; bad = 0
    for s0 in range(n):
        if seen[s0]: continue
        comp = []; stack = [s0]; seen[s0] = True
        while stack:
            v = stack.pop(); comp.append(v)
            for w in adj[v]:
                if not seen[w]: seen[w] = True; stack.append(w)
        if len(comp) == 6:
            m = sum(len(adj[v]) for v in comp) // 2
            if m == 9: bad += 1
    return bad

pools2 = json.loads((HERE / "vol6_pools2.json").read_text())
n18 = pools2["n18"]
med = [sorted(g["I5"][k] for g in n18)[len(n18) // 2] for k in range(8)]
H = min(n18, key=lambda g: sum(abs(g["I5"][k] - med[k]) for k in range(8)))
H_ed = [tuple(e) for e in H["edges"]]
pm_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["Nprism"]][0]
km_t = [t for t in ctypes[6] if pat_index[(6, t)] == NAMED["NK33"]][0]
t2012 = [t for t in ctypes[6] if types[6][t] == 2012][0]
K33_ed = edges_of(types[6][km_t], 6)
A_ed = K33_ed + [(u + 6, v + 6) for (u, v) in H_ed]
T = i5_of(24, A_ed)
log("H =", H["name"], "| target I5(A) =", T)
rng = random.Random(20261103)

def propose(adj):
    edges = adj_to_edges(adj)
    if rng.random() < 0.3:   # double switch
        es = rng.sample(edges, 4)
        vs = [v for e in es for v in e]
        if len(set(vs)) < 8: return None
        (a, b), (c, d), (e, f), (g, h) = es
        added = [(a, c), (b, d), (e, g), (f, h)] if rng.random() < 0.5 else \
                [(a, d), (b, c), (e, h), (f, g)]
        removed = es
    else:
        es = rng.sample(edges, 2)
        (a, b), (c, d) = es
        if len({a, b, c, d}) < 4: return None
        added = [(a, c), (b, d)] if rng.random() < 0.5 else [(a, d), (b, c)]
        removed = es
    for (x, y) in added:
        if x == y or y in adj[x]: return None
    if len({v for e in added for v in e}) < 2 * len(added): return None
    return removed, added

def apply(adj, removed, added):
    for (x, y) in removed:
        adj[x].discard(y); adj[y].discard(x)
    for (x, y) in added:
        adj[x].add(y); adj[y].add(x)
def revert(adj, removed, added):
    apply(adj, added, removed)

def climb(adj0, i5_0, budget, t_start, tag):
    adj = [set(s) for s in adj0]
    cur = list(i5_0)
    bad0 = bad_components(adj)
    def score(v, bd): return sum(abs(v[k] - T[k]) for k in range(8)) + 100 * bd
    S = score(cur, bad0); bd = bad0
    stale = 0; temp = 2.0
    for it in range(budget):
        if S == 0: return adj, cur, it
        pr = propose(adj)
        if pr is None: continue
        removed, added = pr
        d = multi_switch_delta(adj, removed, added)
        new = cur[:]
        for k, nm in enumerate(INV5): new[k] += d.get(nm, 0)
        apply(adj, removed, added)
        bd2 = bad_components(adj)
        Sn = score(new, bd2)
        if Sn <= S or rng.random() < pow(2.718281828, -(Sn - S) / temp):
            cur, S, bd = new, Sn, bd2
            stale = 0 if Sn < S else stale + 1
        else:
            revert(adj, removed, added)
            stale += 1
        temp = max(0.05, temp * 0.99985)
        if stale > 6000:
            temp = 2.0; stale = 0
            log(f"  [{tag}] reheat at it={it}, score={S}")
        if it % 4000 == 3999:
            log(f"  [{tag}] it={it+1} score={S} (D={S - 100*bd}, bad={bd}) elapsed={time.time()-t_start:.0f}s")
    return None, None, budget

t0 = time.time()
B_adj = None
for attempt in range(8):
    adj = edges_to_adj(24, A_ed)
    i5_cur = i5_of(24, A_ed)
    B_adj, B_i5, used = climb(adj, i5_cur, 50000, t0, f"a{attempt}")
    if B_adj is not None:
        log(f"attempt {attempt}: SUCCESS after {used} proposals, total {time.time()-t0:.0f} s")
        break
    log(f"attempt {attempt}: failed ({time.time()-t0:.0f} s)")

result = {"H": H["name"], "target_I5": T}
if B_adj is None:
    log("surgery v2 FAILED")
else:
    B_ed = adj_to_edges(B_adj)
    assert i5_of(24, B_ed) == T and bad_components(B_adj) == 0
    def full(n, ed):
        L = height_series_fast(n, ed, 6)
        s = induced_counts(n, ed, 6)
        return L, subgraph_counts_all(s)
    LA, NA = full(24, A_ed)
    LB, NB = full(24, B_ed)
    agree5 = all(LA[r] == LB[r] for r in range(1, 6))
    def psub(A, B):
        out = dict(A)
        for e, c in B.items():
            out[e] = out.get(e, Fr(0)) - c
            if out[e] == 0: del out[e]
        return out
    dL6 = psub(LB[6], LA[6])
    def kappa6(j):
        return {6 - 2 * j + 2 * i: Fr(comb(6 + j, i)) * (-1) ** i for i in range(6 + j + 1)}
    def fterms(termset):
        tot = {}
        for t in termset:
            pi = pat_index[(6, t)]
            dv = NB.get(pi, 0) - NA.get(pi, 0)
            if dv:
                j = bin(types[6][t]).count("1") - 6
                for e, c in kappa6(j).items():
                    tot[e] = tot.get(e, Fr(0)) + dv * c
        return {e: c for e, c in tot.items() if c}
    NEW8 = [t for t in ctypes[6] if types[6][t] in (1880, 1881, 956, 1884, 5907, 1916, 5948, 5941)]
    variants = {"reduced8": NEW8, "reduced8+f3": NEW8 + [km_t, pm_t],
                "reduced8+f2_m2012": NEW8 + [t2012],
                "full": NEW8 + [km_t, pm_t] + [t2012], "raw_all_conn6": list(CONN6)}
    verdict = {vn: (fterms(ts) == dL6) for vn, ts in variants.items()}
    dN = {}
    for t in CONN6:
        pi = pat_index[(6, t)]
        dv = NB.get(pi, 0) - NA.get(pi, 0)
        if dv: dN[describe(types[6][t], 6)] = dv
    log("agree through 5:", agree5, "| verdicts:", verdict)
    log("dN:", dN)
    result.update({"B_edges": B_ed, "A_edges": A_ed, "verdicts": verdict,
                   "dN_conn6": dN, "agree_through_5": agree5})
(HERE / "vol6_surgery2.json").write_text(json.dumps(result, indent=1, default=str))
(HERE / "vol6_surgery2.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_surgery2.json")
