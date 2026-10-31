#!/usr/bin/env python3
"""Independent exact checks of the volume-seven connected-support law.

The numerical paths differ from vol7_lib: stars-and-bars enumeration,
the power-series definition of log, vertex-subset inclusion-exclusion,
and injective edge-preserving embeddings divided by automorphisms.
"""
from collections import Counter
from fractions import Fraction as Q
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, permutations
from math import comb
from pathlib import Path
import json

import vol7_lib as lib
from vol7_reduction import normal_form

HERE = Path(__file__).resolve().parent
R = 7


def weak_compositions(total, parts):
    if parts == 0:
        if total == 0:
            yield ()
        return
    for bars in combinations(range(total + parts - 1), parts - 1):
        points = (-1,) + bars + (total + parts - 1,)
        yield tuple(points[i + 1] - points[i] - 1 for i in range(parts))


def multiply(a, b):
    out = Counter()
    for i, x in a.items():
        for j, y in b.items():
            out[i + j] += x * y
    return {i: x for i, x in out.items() if x}


def add(a, b, scale=1):
    out = dict(a)
    for i, x in b.items():
        out[i] = out.get(i, Q(0)) + scale * x
    return {i: x for i, x in out.items() if x}


def log_by_powers(series):
    """The definition log(1+u)=sum (-1)^(j+1)u^j/j."""
    u = [{}] + series[1:]
    power = [{0: Q(1)}] + [{} for _ in range(R)]
    result = [{} for _ in range(R + 1)]
    for j in range(1, R + 1):
        power = [
            sum_polys(multiply(power[s], u[r - s]) for s in range(r + 1))
            for r in range(R + 1)
        ]
        for r in range(1, R + 1):
            result[r] = add(result[r], power[r], Q((-1) ** (j + 1), j))
    return result


def sum_polys(polys):
    result = {}
    for poly in polys:
        result = add(result, poly)
    return result


def enumerate_heights(n, edges, ambient=False):
    result = [{0: 1}] + [{} for _ in range(R)]
    for r in range(1, R + 1):
        for h in weak_compositions(r, n):
            if ambient:
                energy = 3 * sum(t * t for t in h) - 2 * sum(h[a] * h[b] for a, b in edges)
            else:
                energy = sum((h[a] - h[b]) ** 2 for a, b in edges)
            result[r][energy] = result[r].get(energy, 0) + 1
        assert sum(result[r].values()) == comb(n + r - 1, r)
    return result


@lru_cache(None)
def local_log(mask, k):
    return log_by_powers(enumerate_heights(k, lib.edges_of(mask, k), ambient=True))


@lru_cache(None)
def kernel_by_inclusion(mask, k):
    """Boolean vertex inversion, rather than proper-support recursion."""
    result = [{} for _ in range(R + 1)]
    for s in range(1, k + 1):
        for vertices in combinations(range(k), s):
            m = lib.canonical(lib.induced_mask(mask, k, vertices), s)
            ell = local_log(m, s)
            for r in range(1, R + 1):
                result[r] = add(result[r], ell[r], (-1) ** (k - s))
    return tuple(result)


def beta_by_raw_edge_inclusion(mask, k):
    edges = lib.edges_of(mask, k)
    result = [{} for _ in range(R + 1)]
    for subset in range(1 << len(edges)):
        m = lib.mask_from_edges(k, (e for i, e in enumerate(edges) if subset >> i & 1))
        if not lib.connected_mask(m, k):
            continue
        phi = kernel_by_inclusion(lib.canonical(m, k), k)
        for r in range(1, R + 1):
            result[r] = add(result[r], phi[r], (-1) ** (len(edges) - subset.bit_count()))
    return tuple(result)


def component_count_after_delete(mask, k, removed):
    remaining = set(range(k)) - {removed}
    edges = lib.edges_of(mask, k)
    result = 0
    while remaining:
        reached = {next(iter(remaining))}
        stack = list(reached)
        while stack:
            v = stack.pop()
            for a, b in edges:
                w = b if a == v else a if b == v else removed
                if w != removed and w not in reached:
                    reached.add(w)
                    stack.append(w)
        remaining -= reached
        result += 1
    return result


def off_diagonal_formula(mask, k):
    """The proved all-order coefficient beta_H at volume |H|+1."""
    e = mask.bit_count()
    result = {}
    for degree in lib.degrees_of(mask, k):
        for t in range(degree + 1):
            for j in range(e + 1):
                exponent = 3 * k + 9 - 2 * (t + j)
                coefficient = comb(degree, t) * comb(e, j) * (-1) ** (e - j)
                result = add(result, {exponent: Q(coefficient)})
    weight = sum(Q(2) ** (component_count_after_delete(mask, k, v) - 1) for v in range(k))
    for j in range(e + 1):
        result = add(result, {3 * k + 3 - 2 * j: -weight * comb(e, j) * (-1) ** (e - j)})
    return result


def embeddings(pattern_k, pattern_edges, host_n, host_edges):
    """Independent injective homomorphisms; no induced-subset counting."""
    pattern_adj = [set() for _ in range(pattern_k)]
    host_adj = [set() for _ in range(host_n)]
    for a, b in pattern_edges:
        pattern_adj[a].add(b)
        pattern_adj[b].add(a)
    for a, b in host_edges:
        host_adj[a].add(b)
        host_adj[b].add(a)
    order = []
    while len(order) < pattern_k:
        candidates = set(range(pattern_k)) - set(order)
        order.append(max(candidates, key=lambda v: (len(pattern_adj[v] & set(order)), len(pattern_adj[v]), -v)))
    image = {}
    used = set()

    def visit(index):
        if index == pattern_k:
            return 1
        v = order[index]
        previous = pattern_adj[v] & image.keys()
        options = set(range(host_n)) - used
        for w in previous:
            options &= host_adj[image[w]]
        total = 0
        for target in options:
            if len(host_adj[target]) < len(pattern_adj[v]):
                continue
            image[v] = target
            used.add(target)
            total += visit(index + 1)
            used.remove(target)
            del image[v]
        return total

    return visit(0)


def direct_pattern_counts(n, edges):
    out = {}
    for k in range(1, min(n, R) + 1):
        for mask in lib.connected_types(k):
            es = lib.edges_of(mask, k)
            automorphisms = embeddings(k, es, k, es)
            count, remainder = divmod(embeddings(k, es, n, edges), automorphisms)
            assert remainder == 0
            if count:
                out[k, mask] = count
    return out


def main():
    report = {"arithmetic": "exact rational", "volume": R, "kernel_checks": {}, "beta_checks": {}, "off_diagonal_checks": {}, "graph_checks": {}}
    for k in range(1, R + 1):
        for mask in lib.connected_types(k):
            independent = kernel_by_inclusion(mask, k)
            assert independent == lib.cumulant_coeffs(mask, k, R), (k, mask, "kernel")
            assert beta_by_raw_edge_inclusion(mask, k) == lib.beta_coeffs(mask, k, R), (k, mask, "beta")
        report["kernel_checks"][str(k)] = len(lib.connected_types(k))
        report["beta_checks"][str(k)] = len(lib.connected_types(k))
        print("independent inclusion kernels", k, len(lib.connected_types(k)), flush=True)
        if k < R:
            for mask in lib.connected_types(k):
                assert off_diagonal_formula(mask, k) == lib.beta_coeffs(mask, k, R)[k + 1], (k, mask, "off_diagonal")
            report["off_diagonal_checks"][str(k)] = len(lib.connected_types(k))

    # Rebuild the core coefficient tables from the independently computed
    # edge-inverted kernels. Check the conditional quotient using forward
    # elimination, rather than vol7_law's reduced-row-echelon routine.
    reduced = {r: {} for r in range(1, R + 1)}
    normal_forms = {}
    for k in range(1, R + 1):
        for mask in lib.connected_types(k):
            beta = beta_by_raw_edge_inclusion(mask, k)
            nf = {(ck, lib.canonical(cm, ck)): c for (ck, cm), c in normal_form(k, mask).items()}
            normal_forms[k, mask] = nf
            for r in range(k, R + 1):
                for key, c in nf.items():
                    reduced[r][key] = add(reduced[r].get(key, {}), beta[r], c)
    reduced = {r: {key: p for key, p in data.items() if p} for r, data in reduced.items()}
    saved_law = json.loads((HERE / "vol7_law.json").read_text())["reduced_coefficients"]
    for r in range(1, R + 1):
        decoded = {(record["k"], record["mask"]): {int(e): Q(c) for e, c in record["polynomial"].items()} for record in saved_law[str(r)]}
        assert decoded == reduced[r], ("reduced_coefficients", r)
    low_keys = sorted({key for r in range(1, R) for key in reduced[r]})
    row_basis = {}

    def reduce_row(row):
        row = dict(row)
        for pivot in sorted(row_basis):
            c = row.get(pivot, Q(0))
            if c:
                row = add(row, row_basis[pivot], -c)
        return row

    for r in range(1, R):
        for e in sorted({e for p in reduced[r].values() for e in p}):
            row = reduce_row({i: reduced[r].get(key, {}).get(e, Q(0)) for i, key in enumerate(low_keys) if reduced[r].get(key, {}).get(e, Q(0))})
            if row:
                pivot = min(row)
                row_basis[pivot] = {i: x / row[pivot] for i, x in row.items()}
    house_key = (5, 221)
    kappa7 = {7 + 2 * j: Q(comb(7, j) * (-1) ** j) for j in range(8)}
    house_weight = multiply(kappa7, {2: Q(3), 4: Q(3), 6: Q(1)})
    exponents = {e for key, p in reduced[R].items() if key[0] < R for e in p} | set(house_weight)
    for e in exponents:
        row = {i: reduced[R].get(key, {}).get(e, Q(0)) - (house_weight.get(e, Q(0)) if key == house_key else 0) for i, key in enumerate(low_keys)}
        assert not reduce_row({i: x for i, x in row.items() if x}), ("house_residual", e)
    for key, poly in reduced[R].items():
        if key[0] == R:
            assert min(lib.degrees_of(key[1], R)) >= 2
            assert poly == lib.expected_top_beta(key[1], R)
    assert len(row_basis) == 12 and len(low_keys) == 20
    report["conditional_law_symbolic"] = {"lower_rank": len(row_basis), "lower_core_columns": len(low_keys), "house_mask": 221, "seven_vertex_core_terms": sum(key[0] == R for key in reduced[R])}
    print("independent core law and quotient passed", flush=True)

    graphs = {
        "K4": (4, tuple(combinations(range(4), 2))),
        "K33": (6, tuple((i, 3 + j) for i in range(3) for j in range(3))),
        "prism": (6, ((0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (0, 3), (1, 4), (2, 5))),
        "cube": (8, tuple((v, v ^ (1 << b)) for v in range(8) for b in range(3) if v < (v ^ (1 << b)))),
        "petersen": (10, tuple([(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)] + [(i + 5, (i + 2) % 5 + 5) for i in range(5)])),
    }
    graphs["K4_union_K33"] = (10, graphs["K4"][1] + tuple((a + 4, b + 4) for a, b in graphs["K33"][1]))
    for name, (n, edges) in graphs.items():
        a = enumerate_heights(n, edges)
        assert a == lib.height_series(n, edges, R), name
        counts = direct_pattern_counts(n, edges)
        assert counts == lib.count_patterns(n, edges, R), (name, "pattern_counts")
        for key, nf in normal_forms.items():
            assert counts.get(key, 0) == sum(c * counts.get(core, 0) for core, c in nf.items()), (name, key, "leaf_reduction")
        ell = log_by_powers(a)
        assert ell == lib.log_from_counts(counts, R), (name, "log_law")
        report["graph_checks"][name] = {"vertices": n, "nonzero_pattern_counts": len(counts), "height_assignments_volume7": comb(n + 6, 7)}
        print("independent graph", name, "passed", flush=True)

    # A deterministic witness isolates the delayed house information.
    # Count its core patterns directly in the actual completed cubic hosts
    # using the independent embedding search above (no completion-matrix
    # row or stored certificate is used to obtain these counts).
    from vol7_completion import completion
    cycle = lambda k: lib.canonical(lib.mask_from_edges(k, ((i, (i + 1) % k) for i in range(k))), k)
    recipe = [((5, 221), 1), ((4, cycle(4)), 2), ((3, cycle(3)), -1), ((5, cycle(5)), -1), ((5, 126), -1)]
    all_cores = [(k, m) for k in range(3, R + 1) for m in lib.connected_types(k) if min(lib.degrees_of(m, k)) >= 2]
    difference = Counter()
    order_difference = 0
    positive_order = 0
    for pattern, mult in recipe:
        n, edges = completion(*pattern)
        degree = Counter(v for edge in edges for v in edge)
        assert set(degree.values()) == {3} and len(degree) == n
        order_difference += mult * n
        positive_order += max(0, mult) * n
        for k, mask in all_cores:
            es = lib.edges_of(mask, k)
            count, remainder = divmod(embeddings(k, es, n, edges), embeddings(k, es, k, es))
            assert remainder == 0
            difference[k, mask] += mult * count
    difference = {key: x for key, x in difference.items() if x}
    assert order_difference == 0 and positive_order == 354
    assert difference == {(5, 221): 1, (5, 126): -1}
    for r in range(1, R):
        assert not sum_polys(add({}, reduced[r].get(key, {}), c) for key, c in difference.items())
    assert sum_polys(add({}, reduced[R].get(key, {}), c) for key, c in difference.items()) == house_weight
    report["delayed_house_witness"] = {
        "pair_order": positive_order,
        "agreement_through": 6,
        "seven_vertex_core_differences": 0,
        "house_count_difference": 1,
        "K23_count_difference": -1,
        "all_core_counts_checked_by_injective_embeddings": len(all_cores),
        "delta_L7": {str(e): str(c) for e, c in sorted(house_weight.items())},
    }
    print("independent 354-vertex delayed-house witness passed", flush=True)

    # Read retained edge lists only; redo all arithmetic and all core counts.
    witness_file = HERE / "vol7_witnesses.json"
    if witness_file.exists():
        cores = [(7, m) for m in lib.connected_types(7) if min(lib.degrees_of(m, 7)) >= 2]
        house = lib.canonical(lib.mask_from_edges(5, ((0, 1), (0, 2), (1, 2), (0, 3), (3, 4), (1, 4))), 5)
        assert house == 221 and len(cores) == 21
        kappa7 = {7 + 2 * j: Q(comb(7, j) * (-1) ** j) for j in range(8)}
        house_weight = multiply(kappa7, {2: Q(3), 4: Q(3), 6: Q(1)})
        checked = 0
        for pair in json.loads(witness_file.read_text())["pairs"][:3]:
            n = pair["n"]
            aa = enumerate_heights(n, pair["A"]["edges"])
            bb = enumerate_heights(n, pair["B"]["edges"])
            assert aa[:7] == bb[:7]
            prediction = {}
            for k, mask in cores + [(5, house)]:
                es = lib.edges_of(mask, k)
                aut = embeddings(k, es, k, es)
                delta = (embeddings(k, es, n, pair["B"]["edges"]) - embeddings(k, es, n, pair["A"]["edges"])) // aut
                weight = lib.expected_top_beta(mask, k) if k == 7 else house_weight
                prediction = add(prediction, weight, delta)
            assert prediction == add(bb[7], aa[7], -1), ("conditional_law", checked)
            checked += 1
        report["conditional_law_direct_witnesses"] = checked
        print("independent conditional-law witnesses", checked, flush=True)
    report["failures"] = 0
    report["source_sha256"] = {name: sha256((HERE / name).read_bytes()).hexdigest() for name in ("vol7_lib.py", "vol7_reduction.py", "vol7_independent_check.py")}
    (HERE / "vol7_independent_check.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("ALL INDEPENDENT CHECKS PASSED", flush=True)


if __name__ == "__main__":
    main()
