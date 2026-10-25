#!/usr/bin/env python3
"""Volume 6, K3,3 test by surgery: hill-climb (edge switches) a connected
cubic graph B on 24 vertices with I5(B) = I5(K3,3 (+) H) exactly, where
H is a stored n=18 pool graph.  Then A = K3,3 (+) H vs B is an agreeing
pair with Delta N_{K3,3} = -1, and the full formula-variant test runs.
I5 deltas under a switch are computed EXACTLY by enumerating connected
vertex sets of size <=5 through the changed edges."""
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
# target pattern type ids per size
TGT = {}
for nm in INV5:
    pi = NAMED[nm]; (k, t, m) = patterns[pi]
    TGT.setdefault(k, []).append((nm, t))

def i5_of(n, edges):
    s = induced_counts(n, edges, 5)
    N = subgraph_counts_all(s)
    return tuple(N.get(NAMED[x], 0) for x in INV5)

def conn_sets_through(x, y, adj, kmax=5):
    """All connected vertex sets of size 2..kmax containing both x and y
    (connectivity w.r.t. adj)."""
    start = frozenset((x, y))
    seen = {start}; frontier = [start]
    out = [start]
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
    """Vector over INV5 of sum_Y sub_Y(type(S)) for the pattern sizes in S."""
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

def delta_i5(adj, pairs):
    """Exact Delta of the I5 pattern counts when the adjacency changes are
    confined to edges with both endpoints among the given pairs: evaluate
    BEFORE with current adj; the caller evaluates AFTER separately."""
    sets = set()
    for (x, y) in pairs:
        for S in conn_sets_through(x, y, adj):
            sets.add(S)
    tot = {}
    for S in sets:
        for nm, c in contrib(S, adj).items():
            tot[nm] = tot.get(nm, 0) + c
    return tot

def sets_union(pairs, adjA, adjB):
    sets = set()
    for (x, y) in pairs:
        for adj in (adjA, adjB):
            for S in conn_sets_through(x, y, adj):
                sets.add(S)
    return sets

def switch_delta(adj, e1, e2, f1, f2):
    """Delta I5 of removing e1,e2 and adding f1,f2 (adj not mutated)."""
    adjB = [set(s) for s in adj]
    for (x, y) in (e1, e2):
        adjB[x].discard(y); adjB[y].discard(x)
    for (x, y) in (f1, f2):
        adjB[x].add(y); adjB[y].add(x)
    sets = set()
    for (x, y) in (e1, e2, f1, f2):
        for S in conn_sets_through(x, y, adj):
            sets.add(S)
        for S in conn_sets_through(x, y, adjB):
            sets.add(S)
    d = {}
    for S in sets:
        cb = contrib(S, adj)
        ca = contrib(S, adjB)
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

def connected(adj):
    seen = {0}; stack = [0]
    while stack:
        v = stack.pop()
        for w in adj[v]:
            if w not in seen: seen.add(w); stack.append(w)
    return len(seen) == len(adj)

# ---------- self-test of the delta machinery ----------
import os
if os.environ.get("SELFTEST"):
    rng0 = random.Random(7)
    ned = [(i, (i + 1) % 12) for i in range(12)] + [(i, i + 6) for i in range(6)]
    adj = edges_to_adj(12, ned)
    base = i5_of(12, adj_to_edges(adj))
    bad = 0
    for trial in range(300):
        edges = adj_to_edges(adj)
        e1, e2 = rng0.sample(edges, 2)
        (a, b), (c, dd) = e1, e2
        if len({a, b, c, dd}) < 4: continue
        f1, f2 = ((a, c), (b, dd)) if trial % 2 else ((a, dd), (b, c))
        if f1[1] in adj[f1[0]] or f2[1] in adj[f2[0]]: continue
        d = switch_delta(adj, e1, e2, f1, f2)
        adj[a].discard(b); adj[b].discard(a); adj[c].discard(dd); adj[dd].discard(c)
        adj[f1[0]].add(f1[1]); adj[f1[1]].add(f1[0]); adj[f2[0]].add(f2[1]); adj[f2[1]].add(f2[0])
        new = i5_of(12, adj_to_edges(adj))
        pred = tuple(base[k] + d.get(INV5[k], 0) for k in range(8))
        if pred != new:
            bad += 1
            print("MISMATCH", trial, pred, new)
        base = new
    print("selftest done, mismatches:", bad)
    sys.exit(0)

# ---------- target ----------
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
log("H =", H["name"], "I5(H) =", H["I5"], "| target I5(A) =", T)

rng = random.Random(20261102)
def climb(adj0, i5_0, budget, t_start):
    adj = [set(s) for s in adj0]
    cur = list(i5_0)
    def dist(v): return sum(abs(v[k] - T[k]) for k in range(8))
    D = dist(cur)
    stale = 0
    for it in range(budget):
        if D == 0: return adj, cur, it
        edges = adj_to_edges(adj)
        e1, e2 = rng.sample(edges, 2)
        (a, b), (c, dd) = e1, e2
        if len({a, b, c, dd}) < 4: continue
        if rng.random() < 0.5: f1, f2 = (a, c), (b, dd)
        else: f1, f2 = (a, dd), (b, c)
        if f1[0] == f1[1] or f2[0] == f2[1]: continue
        if f1[1] in adj[f1[0]] or f2[1] in adj[f2[0]]: continue
        if len({f1[0], f1[1], f2[0], f2[1]}) < 4: continue
        d = switch_delta(adj, e1, e2, f1, f2)
        new = cur[:]
        for k, nm in enumerate(INV5):
            new[k] += d.get(nm, 0)
        Dn = dist(new)
        temp = max(0.05, 1.5 * (0.9995 ** it))
        if Dn < D or (Dn == D and rng.random() < 0.3) or rng.random() < pow(2.718281828, -(Dn - D) / temp) * 0.02:
            # connectivity check on the tentative graph
            adj[a].discard(b); adj[b].discard(a); adj[c].discard(dd); adj[dd].discard(c)
            adj[f1[0]].add(f1[1]); adj[f1[1]].add(f1[0])
            adj[f2[0]].add(f2[1]); adj[f2[1]].add(f2[0])
            if not connected(adj):
                adj[f1[0]].discard(f1[1]); adj[f1[1]].discard(f1[0])
                adj[f2[0]].discard(f2[1]); adj[f2[1]].discard(f2[0])
                adj[a].add(b); adj[b].add(a); adj[c].add(dd); adj[dd].add(c)
                continue
            cur = new; D = Dn; stale = 0
        else:
            stale += 1
        if it % 2000 == 1999:
            log(f"  climb it={it+1} D={D} elapsed={time.time()-t_start:.0f}s")
    return None, None, budget

t0 = time.time()
B_adj = None
for attempt in range(6):
    adj = edges_to_adj(24, A_ed)
    # merge components: switch one K33 edge with one H edge
    e1 = rng.choice(K33_ed)
    e2 = rng.choice(H_ed)
    e2s = (e2[0] + 6, e2[1] + 6)
    (a, b), (c, dd) = e1, e2s
    adj[a].discard(b); adj[b].discard(a); adj[c].discard(dd); adj[dd].discard(c)
    adj[a].add(c); adj[c].add(a); adj[b].add(dd); adj[dd].add(b)
    assert connected(adj)
    i5_cur = i5_of(24, adj_to_edges(adj))
    log(f"attempt {attempt}: merged, I5 = {i5_cur}, D0 = {sum(abs(i5_cur[k]-T[k]) for k in range(8))}")
    B_adj, B_i5, used = climb(adj, i5_cur, 60000, t0)
    if B_adj is not None:
        log(f"attempt {attempt}: SUCCESS after {used} proposals, total {time.time()-t0:.0f} s")
        break
    log(f"attempt {attempt}: failed, {time.time()-t0:.0f} s elapsed")

result = {"H": H["name"], "target_I5": T}
if B_adj is None:
    log("surgery FAILED to reach I5 target")
else:
    B_ed = adj_to_edges(B_adj)
    assert i5_of(24, B_ed) == T
    sB = induced_counts(24, B_ed, 6); NB = subgraph_counts_all(sB)
    assert NB.get(pat_index[(6, km_t)], 0) == 0 and NB.get(pat_index[(6, pm_t)], 0) == 0
    log("B verified: I5 matches, connected, no K3,3/prism component; N_m2012(B) =",
        NB.get(pat_index[(6, t2012)], 0))
    # full formula-variant test
    def full(n, ed):
        L = height_series_fast(n, ed, 6)
        s = induced_counts(n, ed, 6)
        return L, subgraph_counts_all(s)
    LA, NA = full(24, A_ed)
    LB, NB2 = full(24, B_ed)
    log("agree through 5:", all(LA[r] == LB[r] for r in range(1, 6)))
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
            dv = NB2.get(pi, 0) - NA.get(pi, 0)
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
        dv = NB2.get(pi, 0) - NA.get(pi, 0)
        if dv: dN[describe(types[6][t], 6)] = dv
    log("verdicts:", verdict)
    log("dN:", dN)
    result.update({"B_edges": B_ed, "A_edges": A_ed, "verdicts": verdict, "dN_conn6": dN,
                   "agree_through_5": all(LA[r] == LB[r] for r in range(1, 6))})
(HERE / "vol6_surgery.json").write_text(json.dumps(result, indent=1, default=str))
(HERE / "vol6_surgery.log").write_text("\n".join(LOG) + "\n")
log("wrote vol6_surgery.json")
