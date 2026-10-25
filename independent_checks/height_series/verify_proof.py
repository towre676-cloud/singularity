#!/usr/bin/env python3
"""Verification for the diamond-correction proof (PROOF.md).

Independent, stdlib-only checks of every finite step of the proof:

  A. Brute-force enumeration of connected graphs on 4 vertices:
     exactly 6 isomorphism types, with the labelled counts claimed.
  B. For each type, brute force over spanning edge subsets gives the
     multilinear polynomial P(type) = sum_{E' spanning connected} f^|E'|.
  C. Moment functionals per type (edges, edge pairs, triangles,
     4-cycles, diamond pairs, K4, paw incidences), by brute force.
  D. The polynomial identity P = f^3 * r0 + f^4 * u_paw + f^4 * t,
     t = sq + f*dia + f^2*k4, and the rational identity expressing
     r0 through the universal moment functionals.
  E. Bell/log transfer: L_4 - (l_1 l_3 + l_2^2/2 + l_1^2 l_2/2 + l_1^4/24)
     equals l_4, checked numerically at a rational q0.
  F. The proved formula against the stored computational data of
     singularity_extension.json (n = 10 and n = 12 blocks, all pairs;
     n = 8 pool regenerated with the original sampler, all checks
     recomputed here), including the stored squares-only
     counterexamples.
  G. A disconnected test of the K4 term: A = K4 + K_{3,3} against a
     stored n = 10 graph with the same triangle count.

Run: python3 verify_proof.py
Writes verify_results.json beside itself and prints a summary.
"""

import itertools
import json
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The stored sample data and the original extension script live beside
# this file (added by the height-series extension change).
DATA = HERE / "singularity_extension.json"
ORIG_SCRIPT = HERE / "singularity_extension.py"

RESULTS = {}


# ---------------------------------------------------------------- A/B/C
def canonical_key(edges, n):
    """Isomorphism-invariant key for a small graph: min edge tuple
    over all vertex permutations."""
    best = None
    for perm in itertools.permutations(range(n)):
        mapped = tuple(sorted(tuple(sorted((perm[a], perm[b])))
                              for a, b in edges))
        if best is None or mapped < best:
            best = mapped
    return best


def edge_list_from_bits(bits, pairs):
    return [pairs[i] for i in range(len(pairs)) if bits >> i & 1]


def connected(edges, n):
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    seen, stack = set(), [0]
    while stack:
        v = stack.pop()
        if v not in seen:
            seen.add(v)
            stack.extend(adj[v])
    return len(seen) == n


def spanning_connected_polynomial(edges, n):
    """Coeff list in f: sum over spanning connected edge subsets E'
    of f^|E'|."""
    coeff = defaultdict(int)
    m = len(edges)
    for mask in range(1 << m):
        sub = [edges[i] for i in range(m) if mask >> i & 1]
        if len({v for e in sub for v in e}) < n:
            continue
        if connected(sub, n):
            coeff[len(sub)] += 1
    return coeff


def type_functionals(edges, n):
    """Brute-force subgraph functionals of a 4-vertex graph."""
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    tris = []
    for a, b, c in itertools.combinations(range(n), 3):
        if b in adj[a] and c in adj[a] and c in adj[b]:
            tris.append((a, b, c))
    # 4-cycles: distinct edge sets of size 4 forming a simple cycle
    sq = 0
    for quad in itertools.combinations(edges, 4):
        verts = {v for e in quad for v in e}
        if len(verts) != 4:
            continue
        deg = Counter(v for e in quad for v in e)
        if all(deg[v] == 2 for v in verts) and connected(list(quad), n):
            sq += 1
    by_edge = Counter()
    for t in tris:
        for e in itertools.combinations(t, 2):
            by_edge[e] += 1
    dia = sum(v * (v - 1) // 2 for v in by_edge.values())
    paw = 0
    for t in tris:
        tset = set(t)
        for a, b in edges:
            if (a in tset) != (b in tset):
                paw += 1
    return {
        "e": len(edges),
        "epairs": comb(len(edges), 2),
        "tri": len(tris),
        "sq": sq,
        "dia": dia,
        "k4": 1 if len(edges) == 6 else 0,
        "paw": paw,
        "wedges": sum(comb(len(adj[v]), 2) for v in range(n)),
    }


def enumerate_four_vertex_types():
    pairs = list(itertools.combinations(range(4), 2))
    groups = {}
    for bits in range(1 << 6):
        edges = edge_list_from_bits(bits, pairs)
        if not connected(edges, 4):
            continue
        key = canonical_key(edges, 4)
        groups.setdefault(key, []).append(edges)
    types = {}
    for key, members in groups.items():
        rep = members[0]
        deg = tuple(sorted(len([1 for a, b in rep if a == v or b == v])
                           for v in range(4)))
        name = {(3, (1, 1, 2, 2)): "P4", (3, (1, 1, 1, 3)): "star",
                (4, (2, 2, 2, 2)): "C4", (4, (1, 2, 2, 3)): "paw",
                (5, (2, 2, 3, 3)): "diamond", (6, (3, 3, 3, 3)): "K4"}[
                    (len(rep), deg)]
        types[name] = {
            "labelled_count": len(members),
            "rep_edges": [list(e) for e in rep],
            "P": {str(k): v for k, v in
                  sorted(spanning_connected_polynomial(rep, 4).items())},
            "func": type_functionals(rep, 4),
        }
    return types


# ---------------------------------------------------------------- helpers
def poly_add(a, b, s=1):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + s * v
        if out[k] == 0:
            del out[k]
    return out


def poly_scale(a, c):
    return {k: v * c for k, v in a.items() if v * c}


def qpoly_from_f(power_poly, qshift):
    """Convert sum c_j f^j (f = q^-2 - 1) times q^qshift into a
    polynomial in q with integer coefficients, returned as a dict
    exponent -> coeff.  We instead work Laurent-style with Fraction
    exponents avoided: use the expansion in the variable y = q^2 and
    track the overall q power separately in callers.  Here we return
    (qpower, dict in y)."""
    out = defaultdict(int)
    for j, c in power_poly.items():
        # (y^-1 - 1)^j = sum_k C(j,k) (-1)^{j-k} y^{-k}; multiply later.
        for k in range(j + 1):
            out[-k] += c * comb(j, k) * (-1) ** (j - k)
    return qshift, out


def predicted_diff(dN4, dNdia, dNK4):
    """DeltaN4 q^4 (1-q^2)^4 + DeltaNdia q^2 (1-q^2)^5
       + DeltaNK4 (1-q^2)^6, as dict q-exponent -> coeff."""
    out = defaultdict(int)
    for coef, base, power in ((dN4, 4, 4), (dNdia, 2, 5), (dNK4, 0, 6)):
        if coef == 0:
            continue
        for k in range(power + 1):
            out[base + 2 * k] += coef * comb(power, k) * (-1) ** k
    return {k: v for k, v in out.items() if v}


def height_coeffs(edges, n, max_volume=4):
    """Independent enumeration: list over volumes of dicts
    energy -> count, for all labelled height assignments."""
    adj = [set() for _ in range(n)]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    result = [Counter() for _ in range(max_volume + 1)]
    heights = [0] * n

    def rec(v, remaining, volume, energy):
        if v == n - 1:
            h = remaining
            e = energy + sum((h - heights[u]) ** 2 for u in adj[v] if u < v)
            result[volume][e] += 1
            return
        for h in range(remaining + 1):
            e = energy + sum((h - heights[u]) ** 2 for u in adj[v] if u < v)
            heights[v] = h
            rec(v + 1, remaining - h, volume, e)
        heights[v] = 0

    for volume in range(max_volume + 1):
        rec(0, volume, volume, 0)
        assert sum(result[volume].values()) == comb(n + volume - 1, volume)
    return [dict(c) for c in result]


def counts_independent(edges, n):
    adj = [set() for _ in range(n)]
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    n3 = sum(1 for a, b, c in itertools.combinations(range(n), 3)
             if b in adj[a] and c in adj[a] and c in adj[b])
    # simple 4-cycles: canonical DFS as an independent implementation
    cycles = set()
    def dfs(start, cur, path, visited):
        if len(path) == 4:
            if start in adj[cur]:
                cyc = tuple(path)
                rev = (cyc[0],) + tuple(reversed(cyc[1:]))
                rots = [tuple(cyc[i:] + cyc[:i]) for i in range(4)]
                rots += [tuple(rev[i:] + rev[:i]) for i in range(4)]
                cycles.add(min(rots))
            return
        for w in adj[cur]:
            if w not in visited:
                dfs(start, w, path + [w], visited | {w})
    for s in range(n):
        dfs(s, s, [s], {s})
    by_edge = Counter()
    for a, b, c in itertools.combinations(range(n), 3):
        if b in adj[a] and c in adj[a] and c in adj[b]:
            for e in ((a, b), (a, c), (b, c)):
                by_edge[e] += 1
    ndia = sum(v * (v - 1) // 2 for v in by_edge.values())
    nk4 = sum(1 for quad in itertools.combinations(range(n), 4)
              if all(b in adj[a] for a, b in itertools.combinations(quad, 2)))
    return {"N3": n3, "N4": len(cycles), "Ndia": ndia, "NK4": nk4}


def check_pairs(records, label):
    """records: list of dicts with edges, n, series, counts."""
    stats = {"label": label, "pairs_total": 0, "agree03_pairs": 0,
             "agree03_iff_N3_failures": 0, "formula_failures": 0,
             "naive_failures_among_agree03": 0}
    for i, j in itertools.combinations(range(len(records)), 2):
        A, B = records[i], records[j]
        stats["pairs_total"] += 1
        agree = all(A["series"][v] == B["series"][v] for v in range(4))
        if agree != (A["counts"]["N3"] == B["counts"]["N3"]):
            stats["agree03_iff_N3_failures"] += 1
        if not agree:
            continue
        stats["agree03_pairs"] += 1
        actual = poly_add(A["series"][4], B["series"][4], s=-1)
        pred = predicted_diff(A["counts"]["N4"] - B["counts"]["N4"],
                              A["counts"]["Ndia"] - B["counts"]["Ndia"],
                              A["counts"]["NK4"] - B["counts"]["NK4"])
        if actual != pred:
            stats["formula_failures"] += 1
        naive = predicted_diff(A["counts"]["N4"] - B["counts"]["N4"], 0, 0)
        if actual != naive:
            stats["naive_failures_among_agree03"] += 1
    return stats


def make_record(name, edges, n):
    edges = [tuple(e) for e in edges]
    return {"name": name, "edges": edges, "n": n,
            "series": height_coeffs(edges, n),
            "counts": counts_independent(edges, n)}


# ---------------------------------------------------------------- main
def main():
    out = {}

    # A-C: enumeration of 4-vertex types
    types = enumerate_four_vertex_types()
    out["four_vertex_types"] = types
    assert set(types) == {"P4", "star", "C4", "paw", "diamond", "K4"}, types.keys()
    labelled = {k: v["labelled_count"] for k, v in types.items()}
    assert labelled == {"P4": 12, "star": 4, "C4": 3, "paw": 12,
                        "diamond": 6, "K4": 1}, labelled
    expected_P = {"P4": {"3": 1}, "star": {"3": 1},
                  "C4": {"3": 4, "4": 1}, "paw": {"3": 3, "4": 1},
                  "diamond": {"3": 8, "4": 5, "5": 1},
                  "K4": {"3": 16, "4": 15, "5": 6, "6": 1}}
    for name, exp in expected_P.items():
        assert types[name]["P"] == exp, (name, types[name]["P"], exp)
    expected_func = {  # e, epairs, tri, sq, dia, k4, paw
        "P4": (3, 3, 0, 0, 0, 0, 0), "star": (3, 3, 0, 0, 0, 0, 0),
        "C4": (4, 6, 0, 1, 0, 0, 0), "paw": (4, 6, 1, 0, 0, 0, 1),
        "diamond": (5, 10, 2, 1, 1, 0, 4), "K4": (6, 15, 4, 3, 6, 1, 12)}
    for name, exp in expected_func.items():
        f = types[name]["func"]
        got = (f["e"], f["epairs"], f["tri"], f["sq"], f["dia"],
               f["k4"], f["paw"])
        assert got == exp, (name, got, exp)

    # D: polynomial identity and r0 decomposition
    order = ["P4", "star", "C4", "paw", "diamond", "K4"]
    r0 = {"P4": 1, "star": 1, "C4": 4, "paw": 3, "diamond": 8, "K4": 16}
    for name in order:
        f = types[name]["func"]
        rhs = defaultdict(int)
        rhs[3] += r0[name]                # f^3 * r0
        rhs[4] += f["paw"]                # f^4 * u_paw
        # f^4 * t, t = sq + f*dia + f^2*k4
        rhs[4] += f["sq"]
        rhs[5] += f["dia"]
        rhs[6] += f["k4"]
        got = {int(k): v for k, v in types[name]["P"].items()}
        rhs = {k: v for k, v in rhs.items() if v}
        assert rhs == got, (name, rhs, got)
    # r0 = 4 u0 - 3 u_e + 3 u_epairs - (3/2) u_tri + (1/2) u_paw
    for name in order:
        f = types[name]["func"]
        val = (4 * 1 - 3 * f["e"] + 2 * f["epairs"]
               - Fraction(3, 2) * f["tri"] + Fraction(1, 2) * f["paw"])
        assert val == r0[name], (name, val, r0[name])
    out["identity_D"] = "verified pointwise on all six types"

    # E: Bell/log transfer.  Build L = exp(ell) for two rational
    # log-series sharing ell_1..ell_3 but differing in ell_4, and check
    # the claimed Bell identity and that Delta L_4 = Delta ell_4.
    def exp_series(ell):
        L = [Fraction(1)] + [Fraction(0)] * 4
        for r in range(1, 5):
            L[r] = sum(k * ell[k] * L[r - k] for k in range(1, r + 1)) / r
        return L
    def L4_from_ell(ell):
        return (ell[4] + ell[1] * ell[3] + ell[2] ** 2 / 2
                + ell[1] ** 2 * ell[2] / 2 + ell[1] ** 4 / 24)
    ellA = [Fraction(0), Fraction(2), Fraction(-1, 3), Fraction(5, 7),
            Fraction(11, 13)]
    ellB = list(ellA)
    ellB[4] += Fraction(5)
    LA, LB = exp_series(ellA), exp_series(ellB)
    assert L4_from_ell(ellA) == LA[4] and L4_from_ell(ellB) == LB[4]
    assert LA[:4] == LB[:4] and LB[4] - LA[4] == ellB[4] - ellA[4]
    out["bell_E"] = ("L4 = ell4 + ell1 ell3 + ell2^2/2 + ell1^2 ell2/2 "
                     "+ ell1^4/24 verified on exp-consistent rational "
                     "series; Delta L4 = Delta ell4 when ell_1..ell_3 agree")

    # F: stored data
    data = json.loads(DATA.read_text())
    blocks_out = {}
    all_records = {}
    for nkey, n in (("n10", 10), ("n12", 12)):
        block = data["blocks"][nkey]
        recs = []
        seen = set()
        for rec in block["named_graphs"] + block["random_sample_records"]:
            key = tuple(sorted(tuple(e) for e in rec["edges"]))
            if key in seen:
                continue
            seen.add(key)
            r = make_record(rec["name"], rec["edges"], n)
            # counts agree with the stored JSON?
            assert r["counts"]["N3"] == rec["triangles_N3"], (nkey, rec["name"])
            assert r["counts"]["N4"] == rec["squares_N4"], (nkey, rec["name"])
            assert r["counts"]["Ndia"] == rec["diamonds_Ndia"], (nkey, rec["name"])
            recs.append(r)
        all_records[nkey] = recs
        stats = check_pairs(recs, nkey)
        stored = block["pairwise_over_named_plus_sample"]
        stats["stored_pairs_total"] = stored["pairs_total"]
        stats["stored_agree03_pairs"] = stored["agree03_pairs"]
        stats["stored_corrected_failures"] = stored[
            "agree03_pairs_corrected_diamond_formula_failures"]
        stats["stored_naive_failures"] = stored[
            "agree03_pairs_with_triangles_formula_failures"]
        assert stats["pairs_total"] == stored["pairs_total"]
        assert stats["agree03_pairs"] == stored["agree03_pairs"]
        assert stats["formula_failures"] == 0
        assert stats["agree03_iff_N3_failures"] == 0
        assert stats["naive_failures_among_agree03"] == stored[
            "agree03_pairs_with_triangles_formula_failures"]
        blocks_out[nkey] = stats
        # stored counterexamples: squares-only fails, corrected holds
        cex = block["pairwise_over_named_plus_sample"]["counterexamples"]
        checked = 0
        by_name = {r["name"]: r for r in recs}
        for c in cex:
            A = make_record(c["a"], c["a_edges"], n)
            B = make_record(c["b"], c["b_edges"], n)
            actual = poly_add(A["series"][4], B["series"][4], s=-1)
            stored_diff = {int(k): v for k, v in c["diff_vol4"].items()}
            assert actual == stored_diff, (nkey, c["a"], c["b"])
            assert A["counts"]["N3"] == c["a_N3"] and B["counts"]["N3"] == c["b_N3"]
            pred = predicted_diff(A["counts"]["N4"] - B["counts"]["N4"],
                                  A["counts"]["Ndia"] - B["counts"]["Ndia"],
                                  A["counts"]["NK4"] - B["counts"]["NK4"])
            assert actual == pred
            naive_stored = {int(k): v for k, v in
                            c["predicted_from_squares_only"].items()}
            assert actual != naive_stored
            checked += 1
        blocks_out[nkey]["counterexamples_checked"] = checked
    out["stored_blocks"] = blocks_out

    # n = 8: cube + Mobius directly; sampled pool via the original
    # sampler (edge lists only), all checks recomputed here.
    sys.path.insert(0, str(ORIG_SCRIPT.parent))
    import importlib.util
    spec = importlib.util.spec_from_file_location("orig_ext", ORIG_SCRIPT)
    orig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(orig)
    cube = make_record("cube", orig.cube_edges(), 8)
    mob = make_record("mobius", orig.mobius_ladder(8), 8)
    assert cube["counts"]["N4"] == 6 and mob["counts"]["N4"] == 4
    d = poly_add(cube["series"][4], mob["series"][4], s=-1)
    assert d == predicted_diff(2, 0, 0) == {4: 2, 6: -8, 8: 12, 10: -8, 12: 2}
    sampled8, _ = orig.sample_records(8, 60, 20261024, "n8_g")
    recs8 = [cube, mob] + [make_record(r["name"], r["edges"], 8)
                           for r in sampled8]
    stats8 = check_pairs(recs8, "n8")
    stored8 = data["control_n8"]["pairwise_over_cube_mobius_plus_sample"]
    assert stats8["pairs_total"] == stored8["pairs_total"] == 1891
    assert stats8["agree03_pairs"] == stored8["agree03_pairs"] == 555
    assert stats8["formula_failures"] == 0
    assert stats8["naive_failures_among_agree03"] == 0
    out["n8"] = stats8

    # G: disconnected K4 test
    k4 = [(a, b) for a, b in itertools.combinations(range(4), 2)]
    k33 = [(a + 4, b + 7) for a in range(3) for b in range(3)]
    A = make_record("K4+K33", k4 + k33, 10)
    assert A["counts"]["NK4"] == 1 and A["counts"]["N3"] == 4
    B = next(r for r in all_records["n10"]
             if r["counts"]["N3"] == 4 and r["counts"]["NK4"] == 0)
    assert all(A["series"][v] == B["series"][v] for v in range(4))
    actual = poly_add(A["series"][4], B["series"][4], s=-1)
    ext = predicted_diff(A["counts"]["N4"] - B["counts"]["N4"],
                         A["counts"]["Ndia"] - B["counts"]["Ndia"],
                         A["counts"]["NK4"] - B["counts"]["NK4"])
    assert actual == ext
    naive_plus_dia = predicted_diff(A["counts"]["N4"] - B["counts"]["N4"],
                                    A["counts"]["Ndia"] - B["counts"]["Ndia"], 0)
    k4_term = predicted_diff(0, 0, 1)
    assert poly_add(actual, naive_plus_dia, s=-1) == k4_term
    out["disconnected_K4"] = {
        "A": "K4 + K_{3,3} (n=10, N3=4, NK4=1)",
        "B": B["name"] + " (N3=4, NK4=0)",
        "agree_through_vol3": True,
        "extended_formula_with_K4_term_holds": True,
        "difference_from_formula_without_K4_term": k4_term,
    }

    RESULTS.update(out)
    (HERE / "verify_results.json").write_text(json.dumps(out, indent=1,
                                                         default=str))
    print(json.dumps({k: (v if not isinstance(v, dict) else "...")
                      for k, v in out.items()}, indent=1, default=str))
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
