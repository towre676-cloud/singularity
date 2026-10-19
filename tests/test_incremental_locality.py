"""NX16: weighted locality contract, incremental updates and their independent checks.

Oracles: ``direct_series`` (every height in a box, edge-difference energy),
``support_contribution_by_definition`` (inclusion-exclusion of directly
enumerated restricted partition functions), ``heights.local_coefficients``,
``weighted.weighted_coefficients`` and the unweighted connected-support
compiler ``locality.pinned_log``; none of them calls the incremental code.
"""
import itertools
import random
import unittest
from fractions import Fraction

import singularity.incremental_locality as il
from singularity.graph import Graph
from singularity.heights import local_coefficients
from singularity.incremental_locality import (LocalChange, WeightedSpec, apply_changes_to_spec, apply_local_changes,
                                              compile_locality, connected_sets_meeting, connected_sets_through,
                                              direct_series, edge_change, from_graph, from_rational_weights,
                                              pin_change, support_contribution_by_definition, verify_local_update)
from singularity.locality import pinned_log
from singularity.polynomials import add, evaluate, normalize, scale, sub
from singularity.weighted import WeightedGraph, weighted_coefficients

F = Fraction
PAIRS4 = list(itertools.combinations(range(4), 2))


def spec4(ws, pins=None):
    return WeightedSpec(4, [(u, v, w) for (u, v), w in zip(PAIRS4, ws)], pins)


def random_spec(rng, n, wmax=2, pmax=1):
    return WeightedSpec(n, [(u, v, rng.randint(0, wmax)) for u, v in itertools.combinations(range(n), 2)],
                        [rng.randint(0, pmax) for _ in range(n)])


def connected(S, spec):
    adj = {v: set() for v in S}
    for u, v, _ in spec.weights:
        if u in S and v in S:
            adj[u].add(v)
            adj[v].add(u)
    start = next(iter(S))
    seen, stack = {start}, [start]
    while stack:
        for w in adj[stack.pop()]:
            if w not in seen:
                seen.add(w)
                stack.append(w)
    return len(seen) == len(S)


def series_sum(parts, R):
    total = [{} for _ in range(R + 1)]
    for sign, s in parts:
        total = [add(a, scale(b, sign)) for a, b in zip(total, s)]
    return [normalize(t) for t in total]


class WeightedContractTests(unittest.TestCase):
    """NX16-A."""

    def test_two_vertex_example_exact(self):
        R = 2
        q = F(1, 2)
        iso = compile_locality(WeightedSpec(2), R)
        self.assertEqual(iso.series(), [{0: 1}, {0: 2}, {0: 3}])
        self.assertEqual(iso.log, [{}, {0: 2}, {0: 1}])
        edge, record = apply_local_changes(iso, [edge_change(0, 1, 0, 1)])
        self.assertEqual(edge.series(), [{0: 1}, {1: 2}, {0: 1, 4: 2}])
        self.assertEqual(edge.log, [{}, {1: 2}, {0: 1, 2: -2, 4: 2}])
        singleton = [{}, {1: 1}, {4: 1, 2: F(-1, 2)}]
        pair = [{}, {}, {0: 1, 2: -1}]
        for S, expected in (([0], singleton), ([1], singleton), ([0, 1], pair)):
            self.assertEqual(support_contribution_by_definition(edge.spec, S, R), normalize_series(expected))
        rows = {tuple(r["support"]): r for r in record["supports"]}
        self.assertEqual(set(rows), {(0,), (1,), (0, 1)})  # the singletons are invalidated too
        self.assertIsNone(rows[(0, 1)]["old"])
        delta = [evaluate(a, q) - evaluate(b, q) for a, b in zip(edge.log, iso.log)]
        self.assertEqual(delta, [0, -1, F(-3, 8)])
        self.assertEqual([evaluate(c, q) for c in edge.series()], [1, 1, F(9, 8)])
        back, _ = apply_local_changes(edge, [edge_change(0, 1, 1, 0)])
        self.assertEqual(back.state_signature(), iso.state_signature())
        self.assertEqual(verify_local_update(record, oracle_budget=100)["supports"], 3)

    def test_zero_weight_is_absence(self):
        with_zero = WeightedSpec(3, [(0, 1, 0), (1, 2, 2)])
        self.assertEqual(with_zero, WeightedSpec(3, [(1, 2, 2)]))
        dropped, _ = apply_local_changes(compile_locality(WeightedSpec(3, [(0, 1, 1), (1, 2, 2)]), 3),
                                         [edge_change(0, 1, 1, 0)], record=False)
        self.assertEqual(dropped.state_signature(), compile_locality(with_zero, 3).state_signature())

    def test_compiler_matches_independent_oracles(self):
        rng = random.Random(1601)
        for _ in range(30):
            n, R = rng.randint(1, 5), rng.randint(0, 3)
            spec = random_spec(rng, n)
            series = compile_locality(spec, R).series()
            self.assertEqual(series, direct_series(spec, R))
            for row in series:  # ordinary nonnegative integral q exponents, integral counts
                self.assertTrue(all(type(e) is int and e >= 0 and c.denominator == 1 for e, c in row.items()))
        for _ in range(12):  # positive weights, no pinning: the existing weighted enumerator
            n, R = rng.randint(1, 4), rng.randint(1, 4)
            triples = [(u, v, rng.randint(1, 3)) for u, v in itertools.combinations(range(n), 2) if rng.random() < .6]
            spec = WeightedSpec(n, triples)
            expected = weighted_coefficients(WeightedGraph((1,) * n, tuple(triples)), R)
            self.assertEqual(compile_locality(spec, R).series(), [{e: F(c) for e, c in r.items()} for r in expected])
        for _ in range(12):  # unit weights: heights.local_coefficients and the unweighted compiler
            n, R = rng.randint(1, 5), rng.randint(1, 4)
            g = Graph(n, [e for e in itertools.combinations(range(n), 2) if rng.random() < .5])
            self.assertEqual(compile_locality(from_graph(g), R).series(),
                             [{e: F(c) for e, c in r.items()} for r in local_coefficients(g, R)])
            for lam in (0, 2):
                self.assertEqual(compile_locality(from_graph(g, lam), R).log, pinned_log(g, R, lam))

    def test_support_contributions_vanish_off_connected_sets(self):
        rng = random.Random(1602)
        for _ in range(6):
            spec = random_spec(rng, 4)
            R = 3
            comp = compile_locality(spec, R)
            for k in range(1, 5):
                for S in itertools.combinations(range(4), k):
                    phi = support_contribution_by_definition(spec, S, R)
                    if k > R or not connected(S, spec):
                        self.assertFalse(any(phi), (spec, S))
                        self.assertNotIn(frozenset(S), comp.support_index)
                    else:
                        self.assertTrue(all(not phi[j] for j in range(k)))  # O(x^|S|)
                        self.assertEqual(il._phi(comp.support_index[frozenset(S)], R, {}, il.Counter()), phi)

    def test_union_difference_identity_and_naive_filters(self):
        R = 3
        path = WeightedSpec(4, [(0, 1, 1), (1, 2, 1), (2, 3, 1)])
        cases = {"deletion": (path, [edge_change(1, 2, 1, 0)]), "insertion": (path, [edge_change(0, 3, 0, 1)]),
                 "reweight": (path, [edge_change(1, 2, 1, 2)]), "pin": (path, [pin_change(2, 0, 1)])}
        failures = {"new_only": set(), "old_only": set(), "both_endpoints": set()}
        for name, (old, changes) in cases.items():
            new = apply_changes_to_spec(old, changes)
            true = [normalize(sub(a, b)) for a, b in
                    zip(il.series_log(direct_series(new, R), R), il.series_log(direct_series(old, R), R))]
            D = {v for ch in changes for v in ch.endpoints}
            terms = {}
            for k in range(1, R + 1):
                for S in itertools.combinations(range(4), k):
                    if set(S) & D:
                        terms[S] = [normalize(sub(a, b)) for a, b in zip(support_contribution_by_definition(new, S, R),
                                                                         support_contribution_by_definition(old, S, R))]
            union = lambda S: connected(S, new) or connected(S, old)
            self.assertEqual(series_sum([(1, t) for S, t in terms.items() if union(S)], R), true, name)
            ends = set(changes[0].endpoints)
            for label, keep in (("new_only", lambda S: connected(S, new)), ("old_only", lambda S: connected(S, old)),
                                ("both_endpoints", lambda S: union(S) and ends <= set(S))):
                if series_sum([(1, t) for S, t in terms.items() if keep(S)], R) != true:
                    failures[label].add(name)
        self.assertIn("deletion", failures["new_only"])
        self.assertIn("insertion", failures["old_only"])
        # a one-vertex pin change makes "contains every endpoint" coincide with "meets D";
        # for every edge change the singleton ambient-degree terms are missed
        self.assertEqual(failures["both_endpoints"], {"deletion", "insertion", "reweight"})

    def test_rational_weights_need_a_declared_unit(self):
        spec = from_rational_weights(3, [(0, 1, F(1, 2)), (1, 2, F(3, 4))], [0, F(1, 4), 0])
        self.assertEqual(spec.energy_unit, F(1, 4))
        self.assertEqual(spec.weights, ((0, 1, 2), (1, 2, 3)))
        rows = direct_series(spec, 3)
        for h in itertools.product(range(4), repeat=3):
            if sum(h) <= 3:
                energy = F(1, 2) * (h[0] - h[1]) ** 2 + F(3, 4) * (h[1] - h[2]) ** 2 + F(1, 4) * h[1] ** 2
                self.assertIn(energy / spec.energy_unit, rows[sum(h)])
        self.assertEqual(compile_locality(spec, 3).series(), rows)
        with self.assertRaises(TypeError):
            from_rational_weights(2, [(0, 1, 0.5)])

    def test_validation(self):
        for bad in (True, 1.0, "1"):
            with self.assertRaises(TypeError):
                WeightedSpec(2, [(0, 1, bad)])
            with self.assertRaises(TypeError):
                WeightedSpec(bad)
            with self.assertRaises(TypeError):
                compile_locality(WeightedSpec(2), bad)
            with self.assertRaises(TypeError):
                edge_change(0, 1, 0, bad)
        with self.assertRaises(TypeError):
            WeightedSpec(2, energy_unit=0.5)
        for args in ((2, [(0, 1, -1)]), (2, [(0, 0, 1)]), (2, [(0, 2, 1)]), (2, [(0, 1, 1), (1, 0, 2)]),
                     (2, [(0, 1)]), (2, (), [0])):
            with self.assertRaises(ValueError):
                WeightedSpec(*args)
        with self.assertRaises(ValueError):
            WeightedSpec(2, energy_unit=0)
        with self.assertRaises(ValueError):
            LocalChange("vertex", 0, 0, 1)
        with self.assertRaises(ValueError):
            edge_change(1, 1, 0, 1)
        with self.assertRaises(ValueError):
            direct_series(WeightedSpec(10), 4, max_profiles=1000)


def normalize_series(series):
    return [normalize(p) for p in series]


class ConnectedEnumerationTests(unittest.TestCase):
    def test_local_enumerators_against_brute_force(self):
        rng = random.Random(1603)
        for _ in range(40):
            n = rng.randint(1, 7)
            edges = [e for e in itertools.combinations(range(n), 2) if rng.random() < .4]
            adj = {v: set() for v in range(n)}
            for u, v in edges:
                adj[u].add(v)
                adj[v].add(u)
            k = rng.randint(1, 5)
            marked = {v for v in range(n) if rng.random() < .35} or {0}
            spec = WeightedSpec(n, [(u, v, 1) for u, v in edges])
            brute = {frozenset(S) for size in range(1, k + 1) for S in itertools.combinations(range(n), size)
                     if connected(S, spec)}
            meeting = list(connected_sets_meeting(lambda v: adj[v], marked, k))
            self.assertEqual(len(meeting), len(set(meeting)))
            self.assertEqual(set(meeting), {S for S in brute if S & marked})
            through = list(connected_sets_through(lambda v: adj[v], 0, k))
            self.assertEqual(set(through), {S for S in brute if 0 in S})
            self.assertEqual(len(through), len(set(through)))


class IncrementalUpdateTests(unittest.TestCase):
    """NX16-B."""

    def test_every_single_edit_on_weighted_four_vertex_graphs(self):
        # all 3^6 weightings of K4 with weights in {0,1,2}; every edge insertion,
        # deletion and weight change; R = 3 (oracle box 4^4 = 256 heights)
        R, cache, full = 3, {}, {}

        def recompiled(ws):
            if ws not in full:
                full[ws] = compile_locality(spec4(ws), R, cache)
                self.assertEqual(full[ws].series(), direct_series(spec4(ws), R))
            return full[ws]

        edits = 0
        for ws in itertools.product(range(3), repeat=6):
            comp = recompiled(ws)
            for i, (u, v) in enumerate(PAIRS4):
                for new in range(3):
                    if new != ws[i]:
                        updated, _ = apply_local_changes(comp, [edge_change(u, v, ws[i], new)], record=False)
                        target = recompiled(ws[:i] + (new,) + ws[i + 1:])
                        self.assertEqual(updated.state_signature(), target.state_signature())
                        edits += 1
        self.assertEqual(edits, 729 * 12)

    def test_pinning_changes(self):
        R = 3
        for mask in range(64):
            ws = tuple(mask >> i & 1 for i in range(6))
            comp = compile_locality(spec4(ws), R)
            for v in range(4):
                pins = [0] * 4
                pins[v] = 2
                updated, _ = apply_local_changes(comp, [pin_change(v, 0, 2)], record=False)
                self.assertEqual(updated.series(), direct_series(spec4(ws, pins), R))
                back, _ = apply_local_changes(updated, [pin_change(v, 2, 0)], record=False)
                self.assertEqual(back.state_signature(), comp.state_signature())

    def test_sequential_batches_and_reversal(self):
        rng = random.Random(1604)
        n, R = 5, 3
        start = random_spec(rng, n)
        comp = compile_locality(start, R)
        original = comp.state_signature()
        history = []
        for step in range(14):
            batch, used = [], set()
            for _ in range(rng.randint(1, 3)):
                if rng.random() < .7:
                    u, v = sorted(rng.sample(range(n), 2))
                    if ("e", u, v) in used:
                        continue
                    used.add(("e", u, v))
                    old = comp.weight(u, v)
                    batch.append(edge_change(u, v, old, rng.choice([w for w in range(4) if w != old])))
                else:
                    v = rng.randrange(n)
                    if ("p", v) in used:
                        continue
                    used.add(("p", v))
                    old = comp.pinning(v)
                    batch.append(pin_change(v, old, rng.choice([p for p in range(3) if p != old])))
            comp, record = apply_local_changes(comp, batch, in_place=step % 2 == 0)
            history.append(batch)
            self.assertEqual(comp.state_signature(), compile_locality(comp.spec, R).state_signature())
            self.assertEqual(comp.series(), direct_series(comp.spec, R))
            verify_local_update(record)
        for batch in reversed(history):
            comp, _ = apply_local_changes(comp, [ch.inverse() for ch in batch], record=False)
        self.assertEqual(comp.state_signature(), original)

    def test_stale_and_malformed_patches_leave_state_untouched(self):
        comp = compile_locality(WeightedSpec(3, [(0, 1, 2)], [0, 1, 0]), 3)
        before = comp.state_signature()
        for batch in ([edge_change(0, 1, 1, 0)], [edge_change(1, 2, 1, 0)], [pin_change(1, 0, 2)],
                      [edge_change(1, 2, 0, 1), edge_change(0, 1, 3, 0)],
                      [edge_change(1, 2, 0, 1), edge_change(2, 1, 0, 2)], [edge_change(0, 3, 0, 1)], []):
            for in_place in (False, True):
                with self.assertRaises(ValueError):
                    apply_local_changes(comp, batch, in_place=in_place)
                self.assertEqual(comp.state_signature(), before)
        with self.assertRaises(TypeError):
            apply_local_changes(comp, [("edge", (0, 1), 2, 0)])
        with self.assertRaises(ValueError):
            apply_changes_to_spec(comp.spec, [edge_change(0, 1, 1, 0)])

    def test_cross_graph_cache_isolation(self):
        rng = random.Random(1605)
        shared = {}
        for _ in range(40):
            n, R = rng.randint(1, 5), rng.randint(1, 4)
            spec = random_spec(rng, n, wmax=3, pmax=2)
            a = compile_locality(spec, R, shared)
            self.assertEqual(a.state_signature(), compile_locality(spec, R, {}).state_signature())
        # identical support sets and unweighted shape, different weights or ambient degree
        p1 = compile_locality(WeightedSpec(3, [(0, 1, 1), (1, 2, 1)]), 3, shared)
        p2 = compile_locality(WeightedSpec(3, [(0, 1, 1), (1, 2, 2)]), 3, shared)
        p3 = compile_locality(WeightedSpec(4, [(0, 1, 1), (1, 2, 1), (2, 3, 1)]), 3, shared)
        S = frozenset({0, 1, 2})
        self.assertEqual(len({p1.support_index[S], p2.support_index[S], p3.support_index[S]}), 3)
        self.assertNotEqual(p1.log, p2.log)

    def test_labelled_fallback_keys_are_exact(self):
        rng = random.Random(1606)
        specs = [random_spec(rng, 5, wmax=1, pmax=0) for _ in range(6)]
        expected = [compile_locality(s, 4).log for s in specs]
        saved = il.CANONICAL_LIMIT
        try:
            il.CANONICAL_LIMIT = 0
            self.assertEqual([compile_locality(s, 4).log for s in specs], expected)
        finally:
            il.CANONICAL_LIMIT = saved

    def test_update_record_tampering_is_detected(self):
        spec = WeightedSpec(4, [(0, 1, 1), (1, 2, 2), (2, 3, 1)], [0, 0, 1, 0])
        comp = compile_locality(spec, 3)
        _, record = apply_local_changes(comp, [edge_change(1, 2, 2, 0), pin_change(3, 0, 1)])
        self.assertTrue(verify_local_update(record, oracle_budget=1000)["oracle"])
        import copy
        mutations = [lambda r: r["supports"].pop(),
                     lambda r: r["supports"][0].__setitem__("new", r["supports"][0]["old"]),
                     lambda r: r["result_log"][2].append([99, 1, 1]),
                     lambda r: r["changes"][0].__setitem__("old", 1),
                     lambda r: r["declared_union_edges"].pop(),
                     lambda r: r.__setitem__("affected_endpoints", [1, 2]),
                     lambda r: r["baseline"]["log"][1].append([7, 1, 1])]
        for i, mutate in enumerate(mutations):
            bad = copy.deepcopy(record)
            mutate(bad)
            with self.assertRaises(ValueError, msg=i):
                verify_local_update(bad, oracle_budget=1000)


class ScalingTests(unittest.TestCase):
    """NX16-C (small instance; the receipt script runs the full family)."""

    def test_update_work_is_independent_of_graph_size(self):
        R = 3
        profiles = []
        for m in (12, 40):
            edges = ([(i, i + 1, 1) for i in range(m - 1)] + [(m + i, m + i + 1, 1) for i in range(m - 1)]
                     + [(i, m + i, 1) for i in range(m)])
            comp = compile_locality(WeightedSpec(2 * m, edges), R)
            c = m // 2
            counts = []
            for batch in ([edge_change(c, m + c, 1, 3)], [edge_change(c, c + 1, 1, 0)],
                          [edge_change(c, m + c + 1, 0, 1)], [pin_change(c + 1, 0, 2)]):
                stats = {}
                apply_local_changes(comp, batch, in_place=True, record=False, statistics=stats)
                counts.append(stats)
            self.assertEqual(comp.log, compile_locality(comp.spec, R).log)
            profiles.append(counts)
        self.assertEqual(profiles[0], profiles[1])


if __name__ == "__main__":
    unittest.main()
