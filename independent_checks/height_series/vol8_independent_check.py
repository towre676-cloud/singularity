#!/usr/bin/env python3
"""Independent exact checks of the volume-eight connected-support law.

The numerical paths differ from vol8_lib: stars-and-bars enumeration,
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

import vol8_lib as lib
from vol8_reduction import normal_form
from vol8_offdiagonal import first_off_diagonal, second_off_diagonal, second_off_diagonal_blocks

HERE = Path(__file__).resolve().parent
R = 8


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


@lru_cache(None)
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
    if pattern_k > host_n:
        return 0
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


def replay_completed_witnesses(reduced):
    """Fresh small-core embeddings plus an independent cap-girth proof.

    A connected minimum-degree-two pattern crossing an attaching bridge
    must contain a cycle on the cap side. Girth twelve excludes this for
    every pattern here, which has at most eight vertices. Thus the counts
    obtained on the small original core equal those in its cubic
    completion. No large disjoint union needs to be materialised.
    """
    certificate = json.loads((HERE / "vol8_completion_certificate.json").read_text())
    observations = json.loads((HERE / "vol8_observation.json").read_text())
    graph = certificate["padding_graph"]
    n, edges = graph["n"], [tuple(sorted(e)) for e in graph["edges"]]
    assert n == 126 and len(set(edges)) == len(edges) == 189
    adjacency = [set() for _ in range(n)]
    for u, v in edges:
        assert 0 <= u < v < n
        adjacency[u].add(v)
        adjacency[v].add(u)
    assert all(len(neighbours) == 3 for neighbours in adjacency)
    # Shortest endpoint path after deleting each edge, rather than the
    # completion generator's breadth-first collision calculation.
    girth = n + 1
    for deleted_u, deleted_v in edges:
        distances = {deleted_u: 0}
        queue = [deleted_u]
        for v in queue:
            if v == deleted_v:
                break
            for w in adjacency[v]:
                if {v, w} == {deleted_u, deleted_v} or w in distances:
                    continue
                distances[w] = distances[v] + 1
                queue.append(w)
        assert deleted_v in distances
        girth = min(girth, distances[deleted_v] + 1)
    assert girth == 12

    core_keys = [(k, m) for k in range(3, R + 1) for m in lib.connected_types(k) if min(lib.degrees_of(m, k)) >= 2]
    assert len(core_keys) == 100
    automorphisms = {key: embeddings(key[0], lib.edges_of(key[1], key[0]), key[0], lib.edges_of(key[1], key[0])) for key in core_keys}
    fresh_rows = {}
    for host in core_keys:
        host_k, host_mask = host
        host_edges = lib.edges_of(host_mask, host_k)
        row = {}
        for pattern_k, pattern_mask in core_keys:
            if pattern_k > host_k or pattern_mask.bit_count() > host_mask.bit_count():
                continue
            key = (pattern_k, pattern_mask)
            count, remainder = divmod(embeddings(pattern_k, lib.edges_of(pattern_mask, pattern_k), host_k, host_edges), automorphisms[key])
            assert remainder == 0
            if count:
                row[key] = count
        assert row[host] == 1
        fresh_rows[host] = row

    parse_key = lambda text: tuple(map(int, text.split(":")))
    completion_rows = certificate["isolators"]
    assert len(completion_rows) == 100
    for record in completion_rows:
        key = parse_key(record["core"])
        saved = {parse_key(h): c for h, c in record["counts"].items()}
        assert fresh_rows[key] == saved

    def component_order(key):
        return 126 if key == (0, 0) else key[0] + 127 * (3 * key[0] - 2 * key[1].bit_count())

    records = list(observations["isolated_eight_core_witnesses"].items())
    assert len(records) == 60
    records += [(None, record) for record in observations["seven_isolated_observation_witnesses"]]
    assert len(records) == 67
    for isolated_core, record in records:
        components = {parse_key(h): c for h, c in record["signed_components"].items()}
        positive = sum(c * component_order(h) for h, c in components.items() if c > 0)
        negative = sum(-c * component_order(h) for h, c in components.items() if c < 0)
        assert positive == negative == record["equal_vertex_order"]
        actual = {}
        for component, multiplicity in components.items():
            for core, count in fresh_rows.get(component, {}).items():
                actual[core] = actual.get(core, 0) + multiplicity * count
        actual = {key: c for key, c in actual.items() if c}
        assert actual == {parse_key(h): c for h, c in record["core_differences"].items()}
        for r in range(1, R + 1):
            delta = sum_polys(add({}, reduced[r].get(h, {}), c) for h, c in actual.items())
            saved = {int(e): Q(c) for e, c in record["delta_log_coefficients"][str(r)].items()}
            assert delta == saved
            if r < R:
                assert not delta
            else:
                assert delta and delta == {int(e): Q(c) for e, c in record["delta_L8"].items()}
        if isolated_core is not None:
            assert actual == {parse_key(isolated_core): record["scale"]}
        else:
            edge_sums = {e: sum(c for (k, m), c in actual.items() if k == 8 and m.bit_count() == e) for e in range(8, 13)}
            coordinates = [edge_sums[8] + actual.get((6, 6355), 0), edge_sums[9] - 2 * actual.get((6, 5941), 0) + actual.get((6, 17142), 0)]
            coordinates += [edge_sums[e] for e in (10, 11, 12)]
            coordinates += [actual.get((6, 956), 0), actual.get((6, 17142), 0)]
            labels = ["Q0", "Q1", "S8_10", "S8_11", "S8_12", "Theta223", "closed_diamond"]
            selected = labels.index(record["isolated_observable"])
            assert coordinates == [record["scale"] * int(i == selected) for i in range(7)]
    return {"cap_girth": girth, "fresh_core_count_rows": len(fresh_rows), "isolated_eight_core_pairs": 60, "isolated_observation_pairs": 7, "method": "independent injective embeddings on each original core; cap transparency proved by exact girth twelve"}


def main():
    report = {"arithmetic": "exact rational", "volume": R, "kernel_checks": {}, "beta_checks": {}, "first_off_diagonal_checks": {}, "second_off_diagonal_checks": {}, "graph_checks": {}}
    # The analytic API is all-order, independent of the catalogue's cutoff.
    # For C9: U3=9b^2, U22=9a^3(z^2+1)+27a^4,
    # M=9+81a^2, D=27-9a, with a=z+1 and b=z^2+z+1.
    cycle_edges = {tuple(sorted((v, (v + 1) % 9))) for v in range(9)}
    cycle_mask = sum(1 << i for i, edge in enumerate(combinations(range(9), 2)) if edge in cycle_edges)
    aa = {0: Q(1), 1: Q(1)}
    bb = {0: Q(1), 1: Q(1), 2: Q(1)}
    a2 = multiply(aa, aa)
    a3 = multiply(a2, aa)
    a4 = multiply(a2, a2)
    expected_blocks = (
        add({}, multiply(bb, bb), 9),
        add(add({}, multiply(a3, {0: Q(1), 2: Q(1)}), 9), a4, 27),
        add({0: Q(9)}, a2, 81),
        add({0: Q(27)}, aa, -9),
    )
    assert second_off_diagonal_blocks(cycle_mask, 9) == expected_blocks
    f9 = {j: Q(comb(9, j) * (-1) ** (9 - j)) for j in range(10)}
    first_expected = add(
        {36 - 2 * j: c for j, c in multiply(f9, add({}, a2, 9)).items()},
        {30 - 2 * j: c for j, c in f9.items()}, -9,
    )
    second_expected = {}
    for block, shift, sign in zip(expected_blocks, (51, 45, 39, 33), (1, 1, -1, 1)):
        second_expected = add(second_expected, {shift - 2 * j: c for j, c in multiply(f9, block).items()}, sign)
    assert first_off_diagonal(cycle_mask, 9) == first_expected
    assert second_off_diagonal(cycle_mask, 9) == second_expected
    report["beyond_catalogue_analytic_regression"] = {"pattern": "C9", "vertices": 9, "edges": 9, "second_off_diagonal_blocks_checked": 4, "first_and_second_off_diagonal_closed_specializations": True}
    print("independent nine-cycle all-order API regression passed", flush=True)
    for k in range(1, R + 1):
        for mask in lib.connected_types(k):
            independent = kernel_by_inclusion(mask, k)
            assert independent == lib.cumulant_coeffs(mask, k, R), (k, mask, "kernel")
            assert beta_by_raw_edge_inclusion(mask, k) == lib.beta_coeffs(mask, k, R), (k, mask, "beta")
        report["kernel_checks"][str(k)] = len(lib.connected_types(k))
        report["beta_checks"][str(k)] = len(lib.connected_types(k))
        print("independent inclusion kernels and edge coefficients", k, len(lib.connected_types(k)), flush=True)
        if k + 1 <= R:
            for mask in lib.connected_types(k):
                assert first_off_diagonal(mask, k) == lib.beta_coeffs(mask, k, R)[k + 1], (k, mask, "first_off_diagonal")
            report["first_off_diagonal_checks"][str(k)] = len(lib.connected_types(k))
        if k + 2 <= R:
            for mask in lib.connected_types(k):
                assert second_off_diagonal(mask, k) == lib.beta_coeffs(mask, k, R)[k + 2], (k, mask, "second_off_diagonal")
            report["second_off_diagonal_checks"][str(k)] = len(lib.connected_types(k))

    # Independent coefficient reconstruction and forward row elimination.
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
    saved_law = json.loads((HERE / "vol8_law.json").read_text())["reduced_coefficients"]
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

    ranks = []
    for r in range(1, R):
        for e in sorted({e for p in reduced[r].values() for e in p}):
            row = reduce_row({i: reduced[r].get(key, {}).get(e, Q(0)) for i, key in enumerate(low_keys) if reduced[r].get(key, {}).get(e, Q(0))})
            if row:
                pivot = min(row)
                row_basis[pivot] = {i: x / row[pivot] for i, x in row.items()}
        ranks.append(len(row_basis))
    kappa8 = {8 + 2 * j: Q(comb(8, j) * (-1) ** j) for j in range(9)}
    f = {-2: Q(1), 0: Q(-1)}
    a = {2: Q(3), 4: Q(3), 6: Q(1)}
    compact_low = {
        (6, 6355): kappa8,
        (6, 5941): add({}, multiply(kappa8, f), -2),
        (6, 17142): multiply(multiply(kappa8, f), add({0: Q(1)}, a)),
        (6, 956): add({}, multiply(kappa8, a), -1),
    }
    exponents = {e for key, p in reduced[R].items() if key[0] < R for e in p} | {e for p in compact_low.values() for e in p}
    for e in exponents:
        row = {i: reduced[R].get(key, {}).get(e, Q(0)) - compact_low.get(key, {}).get(e, Q(0)) for i, key in enumerate(low_keys)}
        assert not reduce_row({i: x for i, x in row.items() if x}), ("compact_conditional_law", e)
    for key, poly in reduced[R].items():
        if key[0] == R:
            assert min(lib.degrees_of(key[1], R)) >= 2
            assert poly == lib.expected_top_beta(key[1], R)
    assert len(row_basis) == 17 and len(low_keys) == 41
    all_keys = sorted(set(low_keys) | set(reduced[R]))
    row_basis = {}
    full_ranks = []
    for r in range(1, R + 1):
        for e in sorted({e for p in reduced[r].values() for e in p}):
            row = reduce_row({i: reduced[r].get(key, {}).get(e, Q(0)) for i, key in enumerate(all_keys) if reduced[r].get(key, {}).get(e, Q(0))})
            if row:
                pivot = min(row)
                row_basis[pivot] = {i: x / row[pivot] for i, x in row.items()}
        full_ranks.append(len(row_basis))
    assert full_ranks == [1, 1, 2, 5, 8, 12, 17, 24]
    eight_representative = next(key for key in all_keys if key[0] == 8 and key[1].bit_count() == 9)
    delayed_vectors = [
        ({(6, 956): 1, (6, 1881): -1}, add({}, multiply(kappa8, a), -1)),
        ({(6, 17142): 1, (6, 5941): -1, eight_representative: -3}, multiply(multiply(kappa8, f), a)),
    ]
    for vector, expected in delayed_vectors:
        for r in range(1, R):
            assert not sum_polys(add({}, reduced[r].get(key, {}), c) for key, c in vector.items())
        assert sum_polys(add({}, reduced[R].get(key, {}), c) for key, c in vector.items()) == expected
    report["conditional_law_symbolic"] = {"cumulative_ranks": full_ranks, "lower_core_columns": len(low_keys), "eight_vertex_core_terms": sum(key[0] == R for key in reduced[R]), "delayed_vectors_checked": 2}
    print("independent compact law, ranks, and delayed vectors passed", flush=True)

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
        report["graph_checks"][name] = {"vertices": n, "nonzero_pattern_counts": len(counts), "height_assignments_volume8": comb(n + 7, 8)}
        print("independent graph", name, "passed", flush=True)

    witness_file = HERE / "vol8_witnesses.json"
    if witness_file.exists():
        cores = [(8, m) for m in lib.connected_types(8) if min(lib.degrees_of(m, 8)) >= 2]
        checked = 0
        for pair in json.loads(witness_file.read_text())["pairs"][:3]:
            n = pair["n"]
            aa = enumerate_heights(n, pair["A"]["edges"])
            bb = enumerate_heights(n, pair["B"]["edges"])
            assert aa[:8] == bb[:8]
            prediction = {}
            for k, mask in cores + list(compact_low):
                es = lib.edges_of(mask, k)
                aut = embeddings(k, es, k, es)
                delta, remainder = divmod(embeddings(k, es, n, pair["B"]["edges"]) - embeddings(k, es, n, pair["A"]["edges"]), aut)
                assert remainder == 0
                weight = lib.expected_top_beta(mask, k) if k == 8 else compact_low[k, mask]
                prediction = add(prediction, weight, delta)
            assert prediction == add(bb[8], aa[8], -1), ("conditional_law_direct_witness", checked)
            checked += 1
        report["conditional_law_direct_witnesses"] = checked
        print("independent conditional-law direct witnesses", checked, flush=True)

    report["completion_witnesses"] = replay_completed_witnesses(reduced)
    print("independent 60 core isolators and seven observation pairs passed", flush=True)

    report["failures"] = 0
    report["source_sha256"] = {name: sha256((HERE / name).read_bytes()).hexdigest() for name in ("vol8_lib.py", "vol8_reduction.py", "vol8_offdiagonal.py", "vol8_independent_check.py", "vol8_completion.py", "vol8_observation.py")}
    (HERE / "vol8_independent_check.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("ALL INDEPENDENT CHECKS PASSED", flush=True)


if __name__ == "__main__":
    main()
