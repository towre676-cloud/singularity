#!/usr/bin/env python3
"""Moments, cycle overlaps and slice interpolation (SNG-F58 to SNG-F60).

``--check`` compares with the retained file.

* Moment series P_H(x, u, q): compiler against enumeration, specialization
  to every pinning, recovery from C(R,2) + 1 pinnings at q = 1/2, and the
  extremal strata (S = j: binary cuts by size; S = j^2: degrees).
* Rook 4x4 against Shrikhande (same spectrum, triangles, squares): first
  difference 8 q^(12 + 4 lam) (1 - q^2)^6 at volume 4, the K_4 count.
* The coefficient one volume past the first cycle,
  Delta N_(g+1) kappa^(g+1) + Delta N_g kappa^g (g beta + n a), as an exact
  Laurent identity on seven pairs of regular graphs of girth >= 5.
* Theta experiment: three cubic 12-vertex graphs with six squares; the
  volume-5 difference is kappa^5 (Delta N_5 + f Delta N_theta), and two
  temperatures q = 1/2, 1/3 recover both counts.
* Slice interpolation: extreme Laurent coefficients of the boundary
  determinant, injectivity at q = 1/2, the exceptional factorization for
  j = 3, d = 1, l = 0, and the realizable separation bounds.
"""
import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path

from singularity.contexts import boundary_determinant, interface_status, interpolation_rank, lower_degree_condition
from singularity.graph import Graph
from singularity.invariants import binary_cut_profile
from singularity.locality import (cycle, disjoint_union, moment_series, moment_series_by_enumeration, moments_from_pinnings,
                                  pinned_series, pinned_series_by_enumeration, specialize_moments)
from singularity.polynomials import normalize, polynomial_to_json, sub

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "results/overlap_hierarchy.json"


def lmul(a, b):
    out = Counter()
    for e1, c1 in a.items():
        for e2, c2 in b.items():
            out[e1 + e2] += c1 * c2
    return {e: c for e, c in out.items() if c}


def ladd(*terms):
    out = Counter()
    for t in terms:
        for e, c in t.items():
            out[e] += c
    return {e: Fraction(c) for e, c in out.items() if c}


def lscale(a, k):
    return {e: c * k for e, c in a.items() if c * k}


def lpow(a, n):
    out = {0: 1}
    for _ in range(n):
        out = lmul(out, a)
    return out


def gp(n, k):
    return Graph(2 * n, [(i, (i + 1) % n) for i in range(n)] + [(i, n + i) for i in range(n)]
                 + [(n + i, n + (i + k) % n) for i in range(n)])


def cycle_counts(G, L):
    adj = [set(G.neighbors[v]) for v in range(G.n)]
    cnt = Counter()
    for s in range(G.n):
        stack = [(s, [s])]
        while stack:
            v, path = stack.pop()
            for w in adj[v]:
                if w == s and len(path) >= 3:
                    cnt[len(path)] += 1
                elif w > s and w not in path and len(path) < L:
                    stack.append((w, path + [w]))
    return {l: c // 2 for l, c in cnt.items()}


def moments():
    graphs = [Graph(6, [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (1, 4)]), Graph(5, [(0, 1), (1, 2), (2, 3), (3, 4)]),
              Graph(4, [(0, 1), (0, 2), (0, 3), (1, 2), (2, 3), (1, 3)])]
    R, q = 5, Fraction(1, 2)
    for G in graphs:
        M = moment_series(G, R)
        assert M == moment_series_by_enumeration(G, R)
        for lam in range(4):
            assert specialize_moments(M, lam) == pinned_series(G, R, lam)
        values = {lam: [sum(c * q ** e for e, c in row.items()) for row in pinned_series(G, R, lam)] for lam in range(R * (R - 1) // 2 + 1)}
        direct = []
        for row in M:
            d = Counter()
            for (S, E), c in row.items():
                d[S] += c * q ** E
            direct.append({S: v for S, v in d.items() if v})
        assert moments_from_pinnings(values, R, q) == direct
        cuts = binary_cut_profile(G)
        for j in range(R + 1):
            assert {E: int(c) for (S, E), c in M[j].items() if S == j} == {c: k for (size, c), k in cuts.items() if size == j}
            if j:
                assert {E: int(c) for (S, E), c in M[j].items() if S == j * j} == dict(Counter(d * j * j for d in G.degrees))
    return {"graphs": len(graphs), "budget": R, "pinnings_used": R * (R - 1) // 2 + 1, "q": "1/2",
            "checks": ["compiler = enumeration", "specialization to lam = 0..3", "recovery from pinnings", "extremal strata"]}


def rook_shrikhande():
    idx = {(i, j): 4 * i + j for i in range(4) for j in range(4)}
    rook = Graph(16, [(idx[a], idx[b]) for a, b in combinations(idx, 2) if a[0] == b[0] or a[1] == b[1]])
    steps = {(1, 0), (3, 0), (0, 1), (0, 3), (1, 1), (3, 3)}
    shr = Graph(16, [(idx[a], idx[b]) for a, b in combinations(idx, 2) if ((a[0] - b[0]) % 4, (a[1] - b[1]) % 4) in steps])
    def counts(G):
        adj = [set(G.neighbors[v]) for v in range(G.n)]
        k4 = sum(1 for Q in combinations(range(G.n), 4) if all(b in adj[a] for a, b in combinations(Q, 2)))
        diamonds = sum(1 for Q in combinations(range(G.n), 4) if sum(b in adj[a] for a, b in combinations(Q, 2)) == 5)
        c = cycle_counts(G, 4)
        return {"triangles": c.get(3, 0), "squares": c.get(4, 0), "induced_diamonds": diamonds,
                "diamond_subgraphs": diamonds + 6 * k4, "K4": k4}
    stats = [counts(rook), counts(shr)]
    for key in ("triangles", "squares", "diamond_subgraphs"):
        assert stats[0][key] == stats[1][key]
    rows = []
    for lam in (0, 2):
        a, b = pinned_series(rook, 4, lam), pinned_series(shr, 4, lam)
        assert a == pinned_series_by_enumeration(rook, 4, lam) and b == pinned_series_by_enumeration(shr, 4, lam)
        d = [normalize(sub(x, y)) for x, y in zip(a, b)]
        predicted = ladd(lscale(lmul({12 + 4 * lam: 1}, lpow({0: 1, 2: -1}, 6)), 8))
        assert d[:4] == [{}] * 4 and d[4] == predicted
        rows.append({"lam": lam, "first_volume": 4, "difference": polynomial_to_json(d[4])})
    return {"pair": "4x4 rook graph - Shrikhande graph", "counts": stats, "rows": rows}


def next_coefficient():
    pet = gp(5, 2)
    pairs = [(f"2C{g} - C{2 * g}", disjoint_union(cycle(g), cycle(g)), cycle(2 * g), 2, g) for g in (5, 6, 7)]
    pairs += [("2 Petersen - dodecahedron", disjoint_union(pet, pet), gp(10, 2), 3, 5),
              ("dodecahedron - Desargues", gp(10, 2), gp(10, 3), 3, 5),
              ("2 Petersen - Desargues", disjoint_union(pet, pet), gp(10, 3), 3, 5)]
    rows = []
    f = {-2: 1, 0: -1}
    for name, A, B, d, g in pairs:
        ca, cb = cycle_counts(A, g + 1), cycle_counts(B, g + 1)
        assert min(ca, default=99) >= g and min(cb, default=99) >= g and A.n == B.n
        dNg, dNg1 = ca.get(g, 0) - cb.get(g, 0), ca.get(g + 1, 0) - cb.get(g + 1, 0)
        for lam in (0, 2):
            diff = [normalize(sub(x, y)) for x, y in zip(pinned_series(A, g + 1, lam), pinned_series(B, g + 1, lam))]
            a = {d + lam: 1}
            kappa = lmul(a, f)
            beta = ladd(lmul(a, ladd(lscale(f, d - 2), {0: -2})), lmul(lpow(a, 3), lpow({-2: 1, 0: 1}, 2)))
            predicted = ladd(lscale(lpow(kappa, g + 1), dNg1),
                             lscale(lmul(lpow(kappa, g), ladd(lscale(beta, g), lscale(a, A.n))), dNg))
            assert diff[:g] == [{}] * g and ladd(diff[g + 1]) == predicted, (name, lam)
            rows.append({"pair": name, "lam": lam, "girth_bound": g, "delta_N_g": dNg, "delta_N_g_plus_1": dNg1})
    return {"formula": "Delta N_(g+1) kappa^(g+1) + Delta N_g kappa^g (g beta + n a)", "pairs": rows, "identity": "exact Laurent"}


THETA_GRAPHS = {
    (0, 0): [(0, 3), (0, 6), (0, 8), (1, 2), (1, 10), (1, 11), (2, 5), (2, 7), (3, 9), (3, 11), (4, 5), (4, 6), (4, 8),
             (5, 10), (6, 9), (7, 9), (7, 11), (8, 10)],
    (0, 1): [(0, 1), (0, 3), (0, 4), (1, 2), (1, 11), (2, 9), (2, 10), (3, 5), (3, 8), (4, 5), (4, 11), (5, 7), (6, 7),
             (6, 9), (6, 10), (7, 11), (8, 9), (8, 10)],
    (4, 2): [(0, 6), (0, 9), (0, 10), (1, 2), (1, 7), (1, 10), (2, 3), (2, 6), (3, 7), (3, 10), (4, 5), (4, 7), (4, 8),
             (5, 9), (5, 11), (6, 11), (8, 9), (8, 11)]}


def theta():
    graphs = {k: Graph(12, e) for k, e in THETA_GRAPHS.items()}
    for (n5, nth), G in graphs.items():
        adj = [set(G.neighbors[v]) for v in range(12)]
        c = cycle_counts(G, 5)
        assert set(G.degrees) == {3} and 3 not in c and c.get(4, 0) == 6 and c.get(5, 0) == n5
        assert sum(1 for u, v in combinations(range(12), 2) if len(adj[u] & adj[v]) >= 3) == nth
    rows = []
    for (ka, A), (kb, B) in combinations(sorted(graphs.items()), 2):
        for lam in (0, 2):
            d = [normalize(sub(x, y)) for x, y in zip(pinned_series(A, 5, lam), pinned_series(B, 5, lam))]
            kappa = lmul({3 + lam: 1}, {-2: 1, 0: -1})
            dn5, dth = ka[0] - kb[0], ka[1] - kb[1]
            assert d[:5] == [{}] * 5 and ladd(d[5]) == lmul(lpow(kappa, 5), ladd({0: dn5}, lscale({-2: 1, 0: -1}, dth)))
            r = {}
            for q in (Fraction(1, 2), Fraction(1, 3)):
                k = q ** (3 + lam) * (q ** -2 - 1)
                r[q] = sum(c * q ** e for e, c in d[5].items()) / k ** 5
            recovered = ((8 * r[Fraction(1, 2)] - 3 * r[Fraction(1, 3)]) / 5, (r[Fraction(1, 3)] - r[Fraction(1, 2)]) / 5)
            assert recovered == (dn5, dth)
            rows.append({"pair": [list(ka), list(kb)], "lam": lam, "recovered_delta_N5": str(recovered[0]),
                         "recovered_delta_theta": str(recovered[1])})
    return {"graphs": {f"N5={k[0]},theta={k[1]}": e for k, e in THETA_GRAPHS.items()}, "squares": 6, "rows": rows}


def slice_interpolation():
    extremes = []
    for j in (1, 2, 3):
        for d in (1, 2, 3):
            for ell in (0, 1, 4):
                D = boundary_determinant(j, d, ell)
                assert abs(D[min(D)]) == 1 and abs(D[max(D)]) == 1
                extremes.append([j, d, ell])
    injective = []
    for j in range(1, 5):
        for d in (1, 2, 3):
            cols, rank = interpolation_rank(j, d, 0, Fraction(1, 2))
            assert rank == cols
            injective.append([j, d])
    D = boundary_determinant(3, 1, 0)
    low = min(D)
    P = [0] * (max(D) - low + 1)
    for e, c in D.items():
        P[e - low] = c
    mult = 0
    while True:
        out, r = [0] * (len(P) - 1), 0
        for i in range(len(P) - 1, 0, -1):
            r += P[i]
            out[i - 1] = r
        if P[0] + r:
            break
        P, mult = out, mult + 1
    H = lambda z: sum(c * z ** i for i, c in enumerate(P))
    lo, hi = Fraction("1.1213855316120952"), Fraction("1.1213855316120954")
    assert H(lo) * H(hi) < 0
    bounds = {}
    for kappa in (1, 2):
        first = next(R for R in range(100) if interface_status(R, kappa, "interpolated")["top_defect"])
        bounds[f"kappa_{kappa}"] = {"separated_through": first - 1, "first_possible_ambiguity": first,
                                    "exactness_condition_first_failure": lower_degree_condition(120, kappa, "interpolated")}
    return {"extreme_coefficients_unit": extremes, "injective_at_q_half": injective,
            "exceptional_j3_d1_l0": {"lowest_power": low, "multiplicity_of_z_minus_1": mult, "degree_H": len(P) - 1,
                                     "H_at_1": sum(P), "H_at_0": P[0], "leading_H": P[-1],
                                     "root_bracket_z": [str(lo), str(hi)]},
            "realizable_bounds_all_blocks": bounds}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = {"schema": "singularity.overlap-hierarchy/1", "moments": moments(), "rook_shrikhande": rook_shrikhande(),
              "next_coefficient": next_coefficient(), "theta": theta(), "slice_interpolation": slice_interpolation()}
    text = json.dumps(result, indent=1, sort_keys=True) + "\n"
    if args.check:
        if TARGET.read_text() != text:
            raise SystemExit("overlap receipt differs")
        print("Overlap receipt matches")
        return
    TARGET.write_text(text)
    print(text[:2000])


if __name__ == "__main__":
    main()
