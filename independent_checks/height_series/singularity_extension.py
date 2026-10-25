"""Extend the Singularity volume-4 factorisation test beyond 8 vertices.

Background (from the Singularity repository, cloned alongside this work):
  L_G(x, q) = sum_{h in N^{V(G)}} x^{sum_v h_v} q^{sum_{uv in E} (h_u-h_v)^2}
(README.md and docs/chapters/02_graphs_lattices.md of that repository).

The earlier 8-vertex work found, for labelled connected cubic graphs on
8 vertices that agree with the cube through volume 3, that the volume-4
discrepancy against the cube equals
    (N_4(first) - N_4(second)) * q^4 * (1 - q^2)^4,
where N_4 counts 4-cycles (squares).

The repository itself contains a theorem behind the girth >= 4 case:
Theorem SNG-F56 ("the first cycle a budget sees",
docs/chapters/10_inverse_problems.md, docs/papers/locality.md eq. (8)):
for d-regular graphs of the same order, both of girth at least g,
    [x^g] (L_H - L_H') = (N_g(H) - N_g(H')) * q^{(d-2) g} (1 - q^2)^g.
For d = 3, g = 4 that is exactly the formula above, and for d = 3, g = 3
it predicts a volume-3 discrepancy (N_3 diff) * q^3 (1 - q^2)^3 for ANY
pair of cubic graphs of the same order (girth is always at least 3).

This script therefore tests two distinct statements at n = 10 (main)
and n = 12 (secondary), plus an n = 8 control reproducing the earlier
result with the same seed and sampling method:

  (A) Girth >= 4 form: for a pair of cubic graphs of the same order,
      both triangle-free, the series agree through volume 3 and the
      volume-4 discrepancy is (N_4 diff) * q^4 (1 - q^2)^4.
      (This is the case SNG-F56 already proves; the computation is an
      independent exact check of that theorem at new orders, not a
      new proof.)

  (B) Naive form: "any pair agreeing through volume 3 satisfies the
      volume-4 square formula", with no girth hypothesis. Pairs of
      graphs with equal, nonzero triangle counts agree through
      volume 3 whenever the volume-3 coefficient depends only on N_3
      (itself tested below for every sampled pair), but their
      volume-4 discrepancy is NOT expected to be governed by squares
      alone. Counterexamples, if found, are reported explicitly:
      they show the girth hypothesis in (A) cannot simply be dropped.

  (C) Corrected candidate for (B): in the first run of this script,
      every (B)-failure had unequal diamond counts (pairs of triangles
      sharing an edge) and every (B)-success had equal ones, and the
      residual of a failing pair was exactly (diamond difference)
      times q^2 (1 - q^2)^5. The script therefore also tests, for
      every pair, the two-term candidate
        [x^4](L_A - L_B) = (N_4 diff) q^4 (1-q^2)^4
                           + (N_diamond diff) q^2 (1-q^2)^5,
      both among pairs agreeing through volume 3 and among all pairs.
      This candidate is a conjecture fitted from computed residuals
      and checked here at n = 8, 10, 12; it is NOT proved, and the
      repository's own girth-three discussion (its normalised series
      involves N_4, diamonds and K_4 terms) is the nearest stated
      relative. (In a connected cubic graph on n > 4 vertices a K_4
      subgraph would be a whole component, so no K_4 term can arise
      in the classes sampled here.)

Method: exact enumeration of all labelled height assignments of total
volume 0..4 (integers only, no floating point, no sampling of heights).
Graphs are sampled as DISTINCT LABELLED connected cubic graphs by the
configuration model (random pairing of 3n stubs, rejecting loops,
multi-edges and disconnected results), with fixed seeds stated in the
output. Named graphs (Petersen, prisms, Mobius ladders, a generalized
Petersen graph) are included as deterministic anchors.

Totals check: the number of assignments of volume v on n vertices must
equal binom(n + v - 1, v); this is asserted for every graph computed.

Outputs (written next to this script): singularity_extension.json and
a printed summary. No absolute paths are used.
"""

import json
import random
import sys
import time
from collections import Counter
from math import comb
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
MAX_VOLUME = 4

# (1 - q^2)^4 = 1 - 4 q^2 + 6 q^4 - 4 q^6 + q^8; times q^4:
SQ_FORMULA = {4: 1, 6: -4, 8: 6, 10: -4, 12: 1}
# (1 - q^2)^3 = 1 - 3 q^2 + 3 q^4 - q^6; times q^3:
TRI_FORMULA = {3: 1, 5: -3, 7: 3, 9: -1}
# Candidate diamond correction, found from the residuals of the
# triangle-pair failures in a first run of this script (see REPORT.md):
# q^2 (1 - q^2)^5 = q^2 - 5 q^4 + 10 q^6 - 10 q^8 + 5 q^10 - q^12.
DIA_FORMULA = {2: 1, 4: -5, 6: 10, 8: -10, 10: 5, 12: -1}


# ---------------------------------------------------------------- graphs

def adjacency(edges, n):
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return adj


def is_connected(edges, n):
    adj = adjacency(edges, n)
    seen, stack = set(), [0]
    while stack:
        v = stack.pop()
        if v in seen:
            continue
        seen.add(v)
        stack.extend(adj[v])
    return len(seen) == n


def random_cubic(rng, n):
    """One connected simple cubic graph on vertices 0..n-1, labelled,
    by the configuration model (same method as the 8-vertex scripts)."""
    while True:
        stubs = []
        for v in range(n):
            stubs.extend([v] * 3)
        rng.shuffle(stubs)
        edges, ok = set(), True
        for i in range(0, len(stubs), 2):
            a, b = stubs[i], stubs[i + 1]
            if a == b:
                ok = False
                break
            e = (min(a, b), max(a, b))
            if e in edges:
                ok = False
                break
            edges.add(e)
        if ok and is_connected(sorted(edges), n):
            return sorted(edges)


def count_cycles(edges, n, length):
    """Number of simple cycles of the given length (canonicalised by
    rotation/reversal), generalising the 8-vertex counter."""
    adj = [set() for _ in range(n)]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    cycles = set()

    def rotations(t):
        return [tuple(t[i:] + t[:i]) for i in range(len(t))]

    def dfs(start, current, path, visited):
        if len(path) == length:
            if start in adj[current]:
                cyc = tuple(path)
                rev = (cyc[0],) + tuple(reversed(cyc[1:]))
                cycles.add(min(rotations(cyc) + rotations(rev)))
            return
        for nxt in adj[current]:
            if nxt not in visited:
                dfs(start, nxt, path + [nxt], visited | {nxt})

    for s in range(n):
        dfs(s, s, [s], {s})
    return len(cycles)


def triangles_fast(edges, n):
    adj = [set() for _ in range(n)]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    total = 0
    for a in range(n):
        for b in adj[a]:
            if b > a:
                total += sum(1 for c in adj[a] & adj[b] if c > b)
    return total


def is_bipartite(edges, n):
    adj = adjacency(edges, n)
    color = {}
    for s in range(n):
        if s in color:
            continue
        color[s] = 0
        stack = [s]
        while stack:
            v = stack.pop()
            for w in adj[v]:
                if w not in color:
                    color[w] = 1 - color[v]
                    stack.append(w)
                elif color[w] == color[v]:
                    return False
    return True


# ------------------------------------------------------------ named graphs

def cube_edges():
    verts = [(a, b, c) for a in (0, 1) for b in (0, 1) for c in (0, 1)]
    index = {v: i for i, v in enumerate(verts)}
    edges = []
    for v in verts:
        for k in range(3):
            w = list(v)
            w[k] ^= 1
            w = tuple(w)
            if index[v] < index[w]:
                edges.append((index[v], index[w]))
    return sorted(edges)


def mobius_ladder(m):
    """Cycle C_m plus diameter chords i -- i + m/2 (m even). Cubic."""
    edges = set()
    for i in range(m):
        a, b = i, (i + 1) % m
        edges.add((min(a, b), max(a, b)))
    for i in range(m // 2):
        a, b = i, i + m // 2
        edges.add((min(a, b), max(a, b)))
    return sorted(edges)


def prism(m):
    """Two m-cycles (0..m-1 and m..2m-1) plus matching spokes. Cubic."""
    edges = set()
    for i in range(m):
        a, b = i, (i + 1) % m
        edges.add((min(a, b), max(a, b)))
        a, b = m + i, m + (i + 1) % m
        edges.add((min(a, b), max(a, b)))
        edges.add((i, m + i))
    return sorted(edges)


def petersen():
    edges = set()
    for i in range(5):  # outer pentagon
        a, b = i, (i + 1) % 5
        edges.add((min(a, b), max(a, b)))
    for i in range(5):  # inner pentagram: vertex 5+i joined to 5+(i+2 mod 5)
        a, b = 5 + i, 5 + (i + 2) % 5
        edges.add((min(a, b), max(a, b)))
    for i in range(5):  # spokes
        edges.add((i, 5 + i))
    return sorted(edges)


def generalized_petersen_6_2():
    """GP(6,2): outer C6, inner two triangles, spokes. Cubic, N_3 = 2."""
    edges = set()
    for i in range(6):
        a, b = i, (i + 1) % 6
        edges.add((min(a, b), max(a, b)))
        a, b = 6 + i, 6 + (i + 2) % 6
        edges.add((min(a, b), max(a, b)))
        edges.add((i, 6 + i))
    return sorted(edges)


# ------------------------------------------------------------ height series

def height_series(edges, n, max_volume=MAX_VOLUME):
    """Return list over volumes of Counter: energy -> exact count of
    labelled height assignments. Same definition and incremental-energy
    recursion as the earlier 8-vertex calculator, generalised to n."""
    adj = adjacency(edges, n)
    result = [Counter() for _ in range(max_volume + 1)]
    heights = [0] * n

    def rec(v, remaining, volume, energy):
        if v == n - 1:
            h = remaining
            e = energy
            for u in adj[v]:
                if u < v:
                    e += (h - heights[u]) ** 2
            heights[v] = h
            result[volume][e] += 1
            heights[v] = 0
            return
        for h in range(remaining + 1):
            e = energy
            for u in adj[v]:
                if u < v:
                    e += (h - heights[u]) ** 2
            heights[v] = h
            rec(v + 1, remaining - h, volume, e)
        heights[v] = 0

    for volume in range(max_volume + 1):
        rec(0, volume, volume, 0)
        total = sum(result[volume].values())
        expected = comb(n + volume - 1, volume)
        assert total == expected, (n, volume, total, expected)
    return result


def diff_at(series_a, series_b, volume):
    out = {}
    for e in set(series_a[volume]) | set(series_b[volume]):
        d = series_a[volume].get(e, 0) - series_b[volume].get(e, 0)
        if d:
            out[e] = d
    return out


def scaled(template, coef):
    return {p: coef * c for p, c in template.items() if coef * c}


def diamond_count(edges, n):
    """Number of diamonds: pairs of triangles sharing an edge
    (equivalently K4-minus-an-edge subgraphs, 4 vertices, 5 edges)."""
    adj = [set() for _ in range(n)]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    from collections import defaultdict
    by_edge = defaultdict(int)
    for a in range(n):
        for b in adj[a]:
            if b > a:
                for c in adj[a] & adj[b]:
                    if c > b:
                        for e in ((a, b), (a, c), (b, c)):
                            by_edge[e] += 1
    return sum(v * (v - 1) // 2 for v in by_edge.values())


def graph_record(name, edges, n):
    series = height_series(edges, n)
    n3 = count_cycles(edges, n, 3)
    assert n3 == triangles_fast(edges, n)
    n4 = count_cycles(edges, n, 4)
    n5 = count_cycles(edges, n, 5)
    girth = None
    for k, ck in ((3, n3), (4, n4), (5, n5)):
        if ck:
            girth = k
            break
    return {
        "name": name,
        "edges": [list(e) for e in edges],
        "triangles_N3": n3,
        "diamonds_Ndia": diamond_count(edges, n),
        "squares_N4": n4,
        "pentagons_N5": n5,
        "girth_at_most_5": girth,  # None means no cycle of length 3, 4 or 5
        "bipartite": is_bipartite(edges, n),
        "series": series,  # internal only; stripped before JSON dump
        "totals": [sum(series[v].values()) for v in range(MAX_VOLUME + 1)],
    }


def public_record(rec):
    return {k: v for k, v in rec.items() if k != "series"}


# ------------------------------------------------------------ experiments

def pairwise_tests(records, label):
    """For every unordered pair: (i) does agreement through volume 3
    match equality of N_3, and does the volume-3 discrepancy equal
    (N_3 diff) * q^3 (1-q^2)^3 (the g = 3 case of SNG-F56, which needs
    no girth hypothesis)? (ii) Among pairs agreeing through volume 3,
    does the volume-4 square formula hold? Split by girth class."""
    stats = {
        "label": label,
        "pairs_total": 0,
        "vol3_formula_failures": 0,
        "agree03_iff_N3_equal_failures": 0,
        "agree03_pairs": 0,
        "agree03_pairs_both_girth_ge_4": 0,
        "agree03_pairs_both_girth_ge_4_formula_failures": 0,
        "agree03_pairs_with_triangles": 0,
        "agree03_pairs_with_triangles_formula_holds": 0,
        "agree03_pairs_with_triangles_formula_failures": 0,
        "agree03_pairs_corrected_diamond_formula_failures": 0,
        "all_pairs_corrected_diamond_formula_failures": 0,
        "counterexamples": [],
        "corrected_formula_counterexamples": [],
    }
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            a, b = records[i], records[j]
            stats["pairs_total"] += 1
            agree03 = all(a["series"][v] == b["series"][v] for v in range(4))
            if agree03 != (a["triangles_N3"] == b["triangles_N3"]):
                stats["agree03_iff_N3_equal_failures"] += 1
            d3 = diff_at(a["series"], b["series"], 3)
            if d3 != scaled(TRI_FORMULA, a["triangles_N3"] - b["triangles_N3"]):
                stats["vol3_formula_failures"] += 1
            # Corrected candidate: squares term + diamond term.
            d4 = diff_at(a["series"], b["series"], 4)
            corr = scaled(SQ_FORMULA, a["squares_N4"] - b["squares_N4"])
            for p, c in scaled(DIA_FORMULA, a["diamonds_Ndia"] - b["diamonds_Ndia"]).items():
                corr[p] = corr.get(p, 0) + c
                if corr[p] == 0:
                    del corr[p]
            if d4 != corr:
                stats["all_pairs_corrected_diamond_formula_failures"] += 1
            if not agree03:
                continue
            stats["agree03_pairs"] += 1
            if d4 != corr:
                stats["agree03_pairs_corrected_diamond_formula_failures"] += 1
                if len(stats["corrected_formula_counterexamples"]) < 5:
                    stats["corrected_formula_counterexamples"].append({
                        "a": a["name"], "b": b["name"],
                        "a_edges": a["edges"], "b_edges": b["edges"],
                        "diff_vol4": {str(k): v for k, v in sorted(d4.items())},
                        "corrected_prediction": {str(k): v for k, v in sorted(corr.items())},
                    })
            pred = scaled(SQ_FORMULA, a["squares_N4"] - b["squares_N4"])
            holds = d4 == pred
            if a["triangles_N3"] == 0 and b["triangles_N3"] == 0:
                stats["agree03_pairs_both_girth_ge_4"] += 1
                if not holds:
                    stats["agree03_pairs_both_girth_ge_4_formula_failures"] += 1
                    if len(stats["counterexamples"]) < 5:
                        stats["counterexamples"].append({
                            "kind": "girth_ge_4_pair_FAILED",
                            "a": a["name"], "b": b["name"],
                            "a_edges": a["edges"], "b_edges": b["edges"],
                            "diff_vol4": {str(k): v for k, v in sorted(d4.items())},
                            "predicted": {str(k): v for k, v in sorted(pred.items())},
                        })
            else:
                stats["agree03_pairs_with_triangles"] += 1
                if holds:
                    stats["agree03_pairs_with_triangles_formula_holds"] += 1
                else:
                    stats["agree03_pairs_with_triangles_formula_failures"] += 1
                    if len(stats["counterexamples"]) < 10:
                        stats["counterexamples"].append({
                            "kind": "triangle_pair_naive_formula_FAILED",
                            "a": a["name"], "b": b["name"],
                            "a_N3": a["triangles_N3"], "b_N3": b["triangles_N3"],
                            "a_N4": a["squares_N4"], "b_N4": b["squares_N4"],
                            "a_edges": a["edges"], "b_edges": b["edges"],
                            "diff_vol4": {str(k): v for k, v in sorted(d4.items())},
                            "predicted_from_squares_only": {str(k): v for k, v in sorted(pred.items())},
                        })
    return stats


def sample_records(n, n_samples, seed, prefix):
    rng = random.Random(seed)
    seen, records, attempts = set(), [], 0
    while len(records) < n_samples and attempts < 100 * n_samples:
        attempts += 1
        edges = random_cubic(rng, n)
        key = tuple(edges)
        if key in seen:
            continue
        seen.add(key)
        records.append(graph_record(f"{prefix}{len(records)}", edges, n))
    return records, attempts


def vs_reference(records, ref):
    agree, tested, passed, failures = 0, 0, 0, []
    for rec in records:
        if rec["edges"] == ref["edges"]:
            continue
        tested += 1
        if all(rec["series"][v] == ref["series"][v] for v in range(4)):
            agree += 1
            d4 = diff_at(ref["series"], rec["series"], 4)
            pred = scaled(SQ_FORMULA, ref["squares_N4"] - rec["squares_N4"])
            if d4 == pred:
                passed += 1
            else:
                failures.append({
                    "graph": rec["name"], "edges": rec["edges"],
                    "N3": rec["triangles_N3"], "N4": rec["squares_N4"],
                    "diff_vol4_ref_minus_graph": {str(k): v for k, v in sorted(d4.items())},
                    "predicted": {str(k): v for k, v in sorted(pred.items())},
                })
    return {"tested_vs_reference": tested, "agree_through_vol3": agree,
            "formula_holds_among_agreeing": passed, "failures": failures}


def run_block(n, n_samples, seed, named, ref_name, prefix):
    records, attempts = sample_records(n, n_samples, seed, prefix)
    named_records = [graph_record(name, edges, n) for name, edges in named]
    ref = next(r for r in named_records if r["name"] == ref_name)
    pool = named_records + records
    return {
        "n": n,
        "seed": seed,
        "sampling": "configuration model, distinct labelled connected cubic graphs, loops/multi-edges/disconnected rejected",
        "sampled_distinct": len(records),
        "sampling_attempts": attempts,
        "reference": public_record(ref),
        "named_graphs": [public_record(r) for r in named_records],
        "sample_N3_distribution": dict(sorted(Counter(r["triangles_N3"] for r in records).items())),
        "sample_N4_distribution": dict(sorted(Counter(r["squares_N4"] for r in records).items())),
        "vs_reference_random_sample": vs_reference(records, ref),
        "vs_reference_named": vs_reference(named_records, ref),
        "pairwise_over_named_plus_sample": pairwise_tests(pool, f"n={n}"),
        "random_sample_records": [public_record(r) for r in records],
    }


def main():
    t0 = time.time()
    results = {"definition": "L_G(x,q) = sum_h x^{sum h_v} q^{sum_{uv in E} (h_u-h_v)^2}, volumes 0..4, exact integer enumeration",
               "max_volume": MAX_VOLUME, "blocks": {}}

    # ---- control: n = 8, same seed and sampling method as the earlier work
    cube = graph_record("cube_Q3", cube_edges(), 8)
    mob = graph_record("mobius_M8", mobius_ladder(8), 8)
    d4 = diff_at(cube["series"], mob["series"], 4)
    control = {
        "cube_N4": cube["squares_N4"], "mobius_N4": mob["squares_N4"],
        "agree_through_vol3": all(cube["series"][v] == mob["series"][v] for v in range(4)),
        "diff_vol4_cube_minus_mobius": {str(k): v for k, v in sorted(d4.items())},
        "predicted_2q4_1mq2_4": {str(k): v for k, v in sorted(scaled(SQ_FORMULA, 2).items())},
        "matches_earlier_result": d4 == scaled(SQ_FORMULA, 2),
        "totals_cube": cube["totals"],
        "totals_expected_binom": [comb(8 + v - 1, v) for v in range(MAX_VOLUME + 1)],
    }
    recs8, att8 = sample_records(8, 60, 20261024, "n8_sample")
    # the earlier script excluded the cube itself from its sample
    recs8 = [r for r in recs8 if r["edges"] != cube["edges"]]
    control["random_reproduction_seed_20261024"] = {
        "sampled_distinct_excluding_cube": len(recs8),
        **vs_reference(recs8, cube),
        "earlier_reported": {"sampled": 60, "agree_through_vol3": 11, "formula_holds": 11, "failures": 0},
    }
    results["control_n8"] = control
    print(f"[n=8 control] cube vs Mobius matches earlier 2q^4(1-q^2)^4: {control['matches_earlier_result']}")
    print(f"[n=8 control] random reproduction: {control['random_reproduction_seed_20261024']}")

    # ---- main block: n = 10, reference = Petersen graph (N3 = 0, N4 = 0, girth 5)
    block10 = run_block(
        10, 300, 20261025,
        named=[("petersen", petersen()),
               ("pentagonal_prism", prism(5)),
               ("mobius_ladder_M10", mobius_ladder(10))],
        ref_name="petersen", prefix="n10_g")
    results["blocks"]["n10"] = block10
    vsr = block10["vs_reference_random_sample"]
    pw = block10["pairwise_over_named_plus_sample"]
    print(f"[n=10] sampled={block10['sampled_distinct']} vs Petersen: agree03={vsr['agree_through_vol3']} formula_holds={vsr['formula_holds_among_agreeing']} failures={len(vsr['failures'])}")
    print(f"[n=10] pairwise: pairs={pw['pairs_total']} agree03={pw['agree03_pairs']} "
          f"girth>=4 pairs={pw['agree03_pairs_both_girth_ge_4']} failures={pw['agree03_pairs_both_girth_ge_4_formula_failures']} "
          f"triangle pairs={pw['agree03_pairs_with_triangles']} holds={pw['agree03_pairs_with_triangles_formula_holds']} fails={pw['agree03_pairs_with_triangles_formula_failures']} "
          f"vol3 formula failures={pw['vol3_formula_failures']} agree03-iff-N3 failures={pw['agree03_iff_N3_equal_failures']} "
          f"corrected-diamond failures among agree03={pw['agree03_pairs_corrected_diamond_formula_failures']} among all pairs={pw['all_pairs_corrected_diamond_formula_failures']}")

    # ---- secondary block: n = 12, reference = hexagonal prism (N3 = 0, N4 = 6)
    block12 = run_block(
        12, 150, 20261026,
        named=[("hexagonal_prism", prism(6)),
               ("mobius_ladder_M12", mobius_ladder(12)),
               ("generalized_petersen_GP6_2", generalized_petersen_6_2())],
        ref_name="hexagonal_prism", prefix="n12_g")
    results["blocks"]["n12"] = block12
    vsr = block12["vs_reference_random_sample"]
    pw = block12["pairwise_over_named_plus_sample"]
    print(f"[n=12] sampled={block12['sampled_distinct']} vs hexagonal prism: agree03={vsr['agree_through_vol3']} formula_holds={vsr['formula_holds_among_agreeing']} failures={len(vsr['failures'])}")
    print(f"[n=12] pairwise: pairs={pw['pairs_total']} agree03={pw['agree03_pairs']} "
          f"girth>=4 pairs={pw['agree03_pairs_both_girth_ge_4']} failures={pw['agree03_pairs_both_girth_ge_4_formula_failures']} "
          f"triangle pairs={pw['agree03_pairs_with_triangles']} holds={pw['agree03_pairs_with_triangles_formula_holds']} fails={pw['agree03_pairs_with_triangles_formula_failures']} "
          f"vol3 formula failures={pw['vol3_formula_failures']} agree03-iff-N3 failures={pw['agree03_iff_N3_equal_failures']} "
          f"corrected-diamond failures among agree03={pw['agree03_pairs_corrected_diamond_formula_failures']} among all pairs={pw['all_pairs_corrected_diamond_formula_failures']}")

    # ---- n = 8 pairwise pool as a third size for the corrected candidate
    pw8 = pairwise_tests([cube, mob] + recs8, "n=8")
    results["control_n8"]["pairwise_over_cube_mobius_plus_sample"] = pw8
    print(f"[n=8] pairwise: pairs={pw8['pairs_total']} agree03={pw8['agree03_pairs']} "
          f"girth>=4 pairs={pw8['agree03_pairs_both_girth_ge_4']} failures={pw8['agree03_pairs_both_girth_ge_4_formula_failures']} "
          f"triangle pairs={pw8['agree03_pairs_with_triangles']} holds={pw8['agree03_pairs_with_triangles_formula_holds']} fails={pw8['agree03_pairs_with_triangles_formula_failures']} "
          f"corrected-diamond failures among agree03={pw8['agree03_pairs_corrected_diamond_formula_failures']} among all pairs={pw8['all_pairs_corrected_diamond_formula_failures']}")

    results["runtime_seconds"] = round(time.time() - t0, 3)
    with open(OUT_DIR / "singularity_extension.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"wrote singularity_extension.json in {results['runtime_seconds']}s")


if __name__ == "__main__":
    main()
