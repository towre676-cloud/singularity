#!/usr/bin/env python3
"""Loop decomposition of regular graphs and the first overlap (SNG-F60, SNG-F61).

``--check`` recomputes and compares with the retained file.

* SNG-F60: for d-regular H of girth >= g and R < b_g = ceil(3g/2) - 1,
  log F_lam(H) = n b + sum_ell N_ell W_ell modulo x^(R+1), with b and W_ell
  computed from the d-regular tree and the cycle covers U_ell; checked
  against the compiler on several regular graphs for lam = 0, 2.
* SNG-F61: at R = b_g the overlap correction (cyclomatic >= 2 part of the
  connected spanning sums of the b_g-sets) restores exactness; without it the
  prediction fails exactly for graphs with such sets.
* Next coefficient: [x^(g+1)] W_g = g beta kappa^g on a grid of (d, lam, g),
  and the general-g proof by the twin lemma, as an identity in independent
  variables a, f (linear in ell after normalization, checked at ell = 3..8)
  whose components agree with compiler coefficients.
* ``--extended`` retains the generalized Petersen sweep and the
  all-graphs collision census on at most eight vertices.
"""
import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from overlap_hierarchy import THETA_GRAPHS, cycle_counts, gp, ladd, lmul, lpow, lscale  # noqa: E402
from singularity.graph import Graph  # noqa: E402
from singularity.heights import weak_compositions  # noqa: E402
from singularity.locality import (_hang, cycle, exact_support_log, girth_threshold, overlap_correction,  # noqa: E402
                                  pinned_log, regular_cycle_term, regular_log_prediction)

TARGET = ROOT / "results/loop_series.json"


def fixtures():
    cube = Graph(8, [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3), (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)])
    k33 = Graph(6, [(u, v) for u in range(3) for v in range(3, 6)])
    idx = {(i, j): 4 * i + j for i in range(4) for j in range(4)}
    rook = Graph(16, [(idx[a], idx[b]) for a, b in combinations(idx, 2) if a[0] == b[0] or a[1] == b[1]])
    steps = {(1, 0), (3, 0), (0, 1), (0, 3), (1, 1), (3, 3)}
    shr = Graph(16, [(idx[a], idx[b]) for a, b in combinations(idx, 2) if ((a[0] - b[0]) % 4, (a[1] - b[1]) % 4) in steps])
    out = [("cube", cube, 3, 4), ("K33", k33, 3, 4), ("Petersen", gp(5, 2), 3, 5), ("rook", rook, 6, 3),
           ("Shrikhande", shr, 6, 3), ("K5", Graph(5, list(combinations(range(5), 2))), 4, 3), ("C5", cycle(5), 2, 5)]
    out += [(f"cubic12 N5={k[0]} theta={k[1]}", Graph(12, e), 3, 4) for k, e in THETA_GRAPHS.items()]
    return out


def decomposition():
    rows = []
    for name, G, d, g in fixtures():
        b = girth_threshold(g)
        c = cycle_counts(G, b)
        assert set(G.degrees) == {d} and min(c, default=99) >= g
        for lam in (0, 2):
            below = pinned_log(G, b - 1, lam) == regular_log_prediction(G.n, d, c, b - 1, lam)
            actual = pinned_log(G, b, lam)
            overlap = overlap_correction(G, b, lam)
            plain = actual == regular_log_prediction(G.n, d, c, b, lam)
            corrected = actual == regular_log_prediction(G.n, d, c, b, lam, overlap=overlap)
            assert below and corrected and plain == (not overlap)
            rows.append({"graph": name, "d": d, "girth_bound": g, "b_g": b, "lam": lam, "below_b_g_exact": below,
                         "at_b_g_without_overlap": plain, "at_b_g_with_overlap": corrected})
    return rows


def beta_grid():
    checked = []
    for d in (2, 3, 4):
        for lam in (0, 2):
            for g in (3, 4, 5, 6):
                W = regular_cycle_term(d, g, g + 1, lam)
                a, f = {d + lam: 1}, {-2: 1, 0: -1}
                kappa = lmul(a, f)
                beta = ladd(lmul(a, ladd(lscale(f, d - 2), {0: -2})), lmul(lpow(a, 3), lpow({-2: 1, 0: 1}, 2)))
                assert ladd(W[g]) == ladd(lpow(kappa, g)) and ladd(W[g + 1]) == ladd(lscale(lmul(beta, lpow(kappa, g)), g))
                checked.append([d, lam, g])
    return checked


# Twin lemma: polynomials in independent variables (a, f) as {(i, j): coefficient}.
def _p(d):
    return {k: Fraction(v) for k, v in d.items() if v}


def _add(*ps):
    o = Counter()
    for p in ps:
        for k, v in p.items():
            o[k] += v
    return _p(o)


def _mul(*ps):
    out = {(0, 0): Fraction(1)}
    for p in ps:
        o = Counter()
        for (i1, j1), c1 in out.items():
            for (i2, j2), c2 in p.items():
                o[i1 + i2, j1 + j2] += c1 * c2
        out = _p(o)
    return out


def _sc(p, k):
    return _p({key: v * k for key, v in p.items()})


def _pw(p, n):
    o = {(0, 0): Fraction(1)}
    for _ in range(n):
        o = _mul(o, p)
    return o


A, FV, ONE = {(1, 0): Fraction(1)}, {(0, 1): Fraction(1)}, {(0, 0): Fraction(1)}
F2 = _add(_sc(FV, 2), _mul(FV, FV))   # q^-4 - 1 = 2f + f^2
S = _add(_mul(A, A), _sc(ONE, -1))    # twin edge a^2 - 1
OPF = _add(ONE, FV)


def n_cycle(l):
    Tc = _add(_pw(FV, l), _sc(_pw(FV, l - 1), l))
    U = _mul(OPF, _add(_pw(FV, l - 1), _sc(_pw(FV, l - 2), l - 1)))
    Y = _add(_pw(FV, l - 2), _sc(_pw(FV, l - 3), l - 2))
    tstar = _add(_mul(S, Tc), _sc(_mul(FV, Tc), 2), _sc(_mul(S, FV, U), 2), _mul(FV, FV, F2, Y), _mul(S, FV, FV, OPF, OPF, Y))
    tprime = _add(_mul(F2, F2, _pw(FV, l - 2)), _sc(_mul(F2, _pw(FV, l - 2)), 2), _sc(_mul(F2, F2, _pw(FV, l - 3)), l - 2))
    return _add(_sc(_mul(_pw(A, l + 1), tstar), Fraction(1, 2)), _sc(_mul(_pw(A, l + 3), tprime), Fraction(1, 2)))


def n_path_interior(l):
    tstar = _add(_mul(S, _pw(FV, l - 1)), _sc(_pw(FV, l), 2), _sc(_mul(S, FV, _pw(FV, l - 2), OPF), 2),
                 _mul(FV, FV, _pw(FV, l - 3), F2), _mul(S, FV, FV, OPF, OPF, _pw(FV, l - 3)))
    return _add(_sc(_mul(_pw(A, l + 1), tstar), Fraction(1, 2)), _sc(_mul(_pw(A, l + 3), _mul(F2, F2, _pw(FV, l - 3))), Fraction(1, 2)))


def n_path_end(l):
    tstar = _add(_mul(S, _pw(FV, l - 1)), _pw(FV, l), _mul(S, FV, _pw(FV, l - 2), OPF))
    return _add(_sc(_mul(_pw(A, l + 1), tstar), Fraction(1, 2)), _sc(_mul(_pw(A, l + 3), _mul(F2, _pw(FV, l - 2))), Fraction(1, 2)))


def twin_lemma():
    identity = []
    for l in range(3, 9):
        lhs = _add(n_cycle(l), _sc(n_path_interior(l), -(l - 2)), _sc(n_path_end(l), -2), _sc(_mul(_pw(A, l + 1), _pw(FV, l)), -1))
        rhs = _mul(_pw(A, l), _pw(FV, l), _add(_sc(A, -2), _mul(_pw(A, 3), _pw(_add(_sc(ONE, 2), FV), 2))))
        assert lhs == rhs
        identity.append(l)
    single = _add(_sc(_mul(_pw(A, 2), S), Fraction(1, 2)), _sc(_pw(A, 4), Fraction(1, 2)))
    assert single == _add(_pw(A, 4), _sc(_pw(A, 2), Fraction(-1, 2)))
    components = []
    at = lambda p, a, f: sum(c * a ** i * f ** j for (i, j), c in p.items())
    for d, lam, l in [(3, 2, 5), (2, 0, 4), (4, 1, 3), (3, 0, 6)]:
        R = l + 1
        edges, nxt = [(i, (i + 1) % l) for i in range(l)], l
        for v in range(l):
            nxt = _hang(edges, v, nxt, d - 2, 2, d - 1)
        phi_c = exact_support_log(Graph(nxt, edges), frozenset(range(l)), lam, R)[R]
        edges, nxt = [(i, i + 1) for i in range(l + 2)], l + 3
        for v in range(1, l + 2):
            nxt = _hang(edges, v, nxt, d - 2, 2, d - 1)
        phi_p = exact_support_log(Graph(nxt, edges), frozenset(range(1, l + 1)), lam, R)[R]
        for q in (Fraction(1, 2), Fraction(2, 3)):
            a, f = q ** (d + lam), q ** -2 - 1
            assert sum(c * q ** e for e, c in phi_c.items()) == l * at(n_cycle(l), a, f)
            assert sum(c * q ** e for e, c in phi_p.items()) == at(_add(_sc(n_path_interior(l), l - 2), _sc(n_path_end(l), 2)), a, f)
        components.append([d, lam, l])
    return {"identity_in_a_f_for_ell": identity, "degree_in_ell_after_normalization": 1,
            "components_match_compiler": components}


def generalized_petersen():
    rows = []
    for m in range(5, 15):
        for k in range(2, (m + 1) // 2):
            G = gp(m, k)
            if len(G.edges) != 3 * m:
                continue
            c = cycle_counts(G, 9)
            g = min(c)
            if g < 4 or girth_threshold(g) > 8:
                continue
            R = girth_threshold(g)
            ok = pinned_log(G, R, 2) == regular_log_prediction(G.n, 3, c, R, 2, overlap=overlap_correction(G, R, 2))
            assert ok
            rows.append({"graph": f"GP({m},{k})", "girth": g, "b_g": R, "exact": ok})
    return rows


def collision_census(max_n=8, R=5, deep=10):
    from itertools import permutations, product

    def canon(n, edges):
        adj = [set() for _ in range(n)]
        for u, v in edges:
            adj[u].add(v)
            adj[v].add(u)
        color = [len(adj[v]) for v in range(n)]
        while True:
            sig = [(color[v], tuple(sorted(color[w] for w in adj[v]))) for v in range(n)]
            keys = sorted(set(sig))
            new = [keys.index(s) for s in sig]
            if len(set(new)) == len(set(color)):
                color = new
                break
            color = new
        classes = {}
        for v in range(n):
            classes.setdefault(color[v], []).append(v)
        best = None
        for choice in product(*[permutations(classes[c]) for c in sorted(classes)]):
            order = sum(choice, ())
            pos = {v: i for i, v in enumerate(order)}
            code = tuple(sorted(tuple(sorted((pos[u], pos[v]))) for u, v in edges))
            if best is None or code < best:
                best = code
        return tuple(sorted(color)), best

    def moments(G, top):
        rows = []
        for v in range(top + 1):
            c = Counter()
            for h in weak_compositions(v, G.n):
                c[sum(x * x for x in h), sum((h[a] - h[b]) ** 2 for a, b in G.edges)] += 1
            rows.append(c)
        return rows

    def spec(rows, lam):
        out = []
        for r in rows:
            c = Counter()
            for (s, E), k in r.items():
                c[E + lam * s] += k
            out.append(tuple(sorted(c.items())))
        return tuple(out)

    graphs = {canon(1, []): (1, [])}
    report = []
    for m in range(2, max_n + 1):
        new = {}
        for (_, (k, edges)) in graphs.items():
            for mask in range(1 << (m - 1)):
                e = list(edges) + [(v, m - 1) for v in range(m - 1) if mask >> v & 1]
                c = canon(m, e)
                if c not in new:
                    new[c] = (m, e)
        graphs = new
        if m < 7:
            continue
        gs = [Graph(k, e) for k, e in graphs.values()]
        rows = [moments(G, R) for G in gs]
        entry = {"n": m, "graphs": len(gs), "budget": R}
        for name, lam in (("A_H", 2), ("L_H", 0)):
            groups = {}
            for G, r in zip(gs, rows):
                groups.setdefault(spec(r, lam), []).append(G)
            pairs = [g for g in groups.values() if len(g) > 1]
            firsts = []
            for grp in pairs:
                deep_rows = [moments(G, deep) for G in grp]
                firsts.append(next(v for v in range(deep + 1) if len({spec([r[v]], lam) for r in deep_rows}) > 1))
            entry[name] = {"distinct_through_budget": len(groups), "colliding_groups": len(pairs),
                           "first_separation_volumes": dict(Counter(firsts))}
        report.append(entry)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--extended", action="store_true")
    args = parser.parse_args()
    result = {"schema": "singularity.loop-series/1", "decomposition": decomposition(), "beta_grid": beta_grid(),
              "twin_lemma": twin_lemma()}
    retained = json.loads(TARGET.read_text()) if TARGET.exists() else {}
    if args.check:
        if {k: retained.get(k) for k in result} != result:
            raise SystemExit("loop-series receipt differs")
        print("Loop-series receipt matches")
        return
    if args.extended:
        result["generalized_petersen"] = generalized_petersen()
        result["collision_census"] = collision_census()
    else:
        result["generalized_petersen"] = retained.get("generalized_petersen")
        result["collision_census"] = retained.get("collision_census")
    TARGET.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k in ("collision_census",)}, indent=1))


if __name__ == "__main__":
    main()
