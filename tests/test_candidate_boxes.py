"""Candidate-specific closed boxes (NX01-A, NX01-B).

Independent checks: interval endpoints are computed inline from raw readings
and radii (never via production mask helpers); optimization is compared with
a full subset scan over product-box intersections and a cover-state
Dijkstra search, both in ``candidate_box_oracles``, which does not import the
production module.
"""
import random
import unittest
from fractions import Fraction as F
from itertools import product

from singularity.candidate_box_oracles import (cost_bounded_box_panel, cover_state_dijkstra,
                                               exhaustive_box_panel)
from singularity.candidate_boxes import (
    CandidateBoxPool, box_pool, candidate_box_ambiguity, candidate_box_consistent,
    candidate_box_masks, candidate_box_receipt, candidate_box_separates, candidate_box_targets,
    common_envelope, from_diagnostic_pool, interval, minimum_candidate_box_panel, panel_cost,
    rational_json, required_pairs, separation_margin, uncoverable_pairs)
from singularity.panels import (coverage_masks, minimum_cost_panel, reading_pool)


def raw(pool):
    return pool.pool.costs, pool.pool.readings, pool.radii, pool.target_labels


def endpoint_separated(readings, radii, e, a, b):
    """Disjointness of closed intervals by endpoints, independent of margins."""
    lo_a, hi_a = readings[e][a] - radii[e][a], readings[e][a] + radii[e][a]
    lo_b, hi_b = readings[e][b] - radii[e][b], readings[e][b] + radii[e][b]
    return hi_a < lo_b or hi_b < lo_a


def random_box_pool(rng, k=None, size=None, targets=False, zero_bias=False):
    k = k or rng.randint(2, 4)
    size = rng.randint(0, 7) if size is None else size
    costs = [rng.randint(0, 5) for _ in range(size)]
    readings = [[F(rng.randint(-4, 4), rng.choice((1, 2))) for _ in range(k)] for _ in range(size)]
    radii = [[F(0) if zero_bias and rng.random() < .4 else F(rng.randint(0, 3), rng.choice((2, 4)))
              for _ in range(k)] for _ in range(size)]
    labels = [rng.choice("xy") for _ in range(k)] if targets else None
    return box_pool(costs, readings, radii, candidates=k, target_labels=labels)


class WorkedExamples(unittest.TestCase):
    def test_packet_example_gain_from_sharper_radii(self):
        pool = box_pool((3,), ((0, 1),), ((F(1, 10), F(1, 2)),))
        self.assertEqual(interval(pool, 0, 0), (F(-1, 10), F(1, 10)))
        self.assertEqual(interval(pool, 0, 1), (F(1, 2), F(3, 2)))
        self.assertEqual(separation_margin(pool, 0, 0, 1), F(2, 5))
        self.assertTrue(candidate_box_separates(pool, (0,)))
        self.assertIsNone(candidate_box_ambiguity(pool, (0,)))
        best = minimum_candidate_box_panel(pool)
        self.assertEqual((best.status, best.panel, best.cost), ("optimal", (0,), 3))
        envelope = common_envelope(pool)
        self.assertEqual(envelope.radii, ((F(1, 2), F(1, 2)),))
        self.assertEqual(separation_margin(envelope, 0, 0, 1), 0)
        self.assertFalse(candidate_box_separates(envelope, (0,)))
        witness = candidate_box_ambiguity(envelope, (0,))
        self.assertEqual((witness.a, witness.b, witness.observed), (0, 1, (F(1, 2),)))
        self.assertEqual(candidate_box_consistent(envelope, (0,), witness.observed), (0, 1))
        self.assertEqual(minimum_candidate_box_panel(envelope).status, "infeasible")

    def test_difference_equal_to_radius_sum_is_rejected(self):
        pool = box_pool((1,), ((0, F(3, 5)),), ((F(1, 5), F(2, 5)),))
        self.assertEqual(separation_margin(pool, 0, 0, 1), 0)
        self.assertEqual(candidate_box_masks(pool), (0,))
        self.assertEqual(uncoverable_pairs(pool), ((0, 1),))
        witness = candidate_box_ambiguity(pool, (0,))
        self.assertEqual(witness.observed, (F(1, 5),))
        self.assertEqual(candidate_box_consistent(pool, (0,), (F(1, 5),)), (0, 1))
        result = minimum_candidate_box_panel(pool)
        self.assertEqual((result.status, result.panel, result.cost, result.uncoverable),
                         ("infeasible", None, None, ((0, 1),)))

    def test_zero_radius_mixtures(self):
        # zero and positive radius, touching: not separated; slightly apart: separated
        touch = box_pool((1,), ((0, F(1, 3)),), ((0, F(1, 3)),))
        self.assertFalse(candidate_box_separates(touch, (0,)))
        self.assertEqual(candidate_box_ambiguity(touch, (0,)).observed, (F(0),))
        apart = box_pool((1,), ((0, F(1, 2)),), ((0, F(1, 3)),))
        self.assertTrue(candidate_box_separates(apart, (0,)))
        # both exact: any difference separates, equality does not
        exact = box_pool((1, 1), ((0, F(1, 10**9)), (5, 5)), ((0, 0), (0, 0)))
        self.assertEqual(candidate_box_masks(exact), (1, 0))
        self.assertEqual(candidate_box_consistent(exact, (0, 1), (0, 5)), (0,))
        # mixed exact/noisy rows in one pool (the common backend refuses zero eps)
        mixed = box_pool((2, 1), ((0, 1, 2), (0, 0, 3)),
                         ((0, 0, 0), (F(1, 2), F(1, 2), 1)))
        self.assertEqual(minimum_candidate_box_panel(mixed).cost, 2)
        with self.assertRaises(ValueError):
            coverage_masks(mixed.pool, (F(0), F(1)))

    def test_identical_centers_distinct_ids_never_separated(self):
        pool = box_pool((1, 1), ((7, 7, 9), (7, 7, 0)), ((0, F(1, 2), 0), (F(1, 9), 0, 1)),
                        candidate_ids=("left", "right", "other"))
        self.assertEqual(required_pairs(pool), ((0, 1), (0, 2), (1, 2)))
        self.assertEqual(uncoverable_pairs(pool), ((0, 1),))
        witness = candidate_box_ambiguity(pool, (0, 1))
        self.assertEqual((witness.a, witness.b), (0, 1))
        self.assertEqual(witness.observed, (F(7), F(7)))
        self.assertEqual(candidate_box_consistent(pool, (0, 1), witness.observed), (0, 1))
        self.assertEqual(minimum_candidate_box_panel(pool).status, "infeasible")
        # a shared target makes the identical pair irrelevant; identities are retained
        merged = box_pool((1, 1), ((7, 7, 9), (7, 7, 0)), ((0, F(1, 2), 0), (F(1, 9), 0, 1)),
                          candidate_ids=("left", "right", "other"), target_labels=("t", "t", "u"))
        self.assertEqual(required_pairs(merged), ((0, 2), (1, 2)))
        best = minimum_candidate_box_panel(merged)
        self.assertEqual((best.status, best.cost), ("optimal", 1))
        self.assertEqual(merged.candidate_ids, ("left", "right", "other"))
        self.assertEqual(candidate_box_consistent(merged, best.panel, (7,) * len(best.panel)), (0, 1))
        self.assertEqual(candidate_box_targets(merged, best.panel, (7,) * len(best.panel)), ("t",))


class Contracts(unittest.TestCase):
    def test_empty_pool_and_all_equal_targets(self):
        empty = box_pool((), (), (), candidates=3)
        self.assertEqual(empty.size, 0)
        self.assertEqual(uncoverable_pairs(empty), ((0, 1), (0, 2), (1, 2)))
        self.assertEqual(minimum_candidate_box_panel(empty).status, "infeasible")
        same = box_pool((), (), (), candidates=3, target_labels=(1, 1, 1))
        best = minimum_candidate_box_panel(same)
        self.assertEqual((best.status, best.panel, best.cost), ("optimal", (), 0))
        self.assertTrue(candidate_box_separates(same, ()))
        self.assertEqual(candidate_box_targets(same, (), ()), (1,))
        with self.assertRaises(ValueError):
            box_pool((), (), ())

    def test_duplicate_ids_and_malformed_shapes(self):
        base = ((1, 2), ((0, 1, 2), (3, 4, 5)))
        good = ((0, 0, 0), (1, 1, 1))
        with self.assertRaises(ValueError):
            box_pool(*base, good, candidate_ids=("a", "a", "b"))
        for bad in (((0, 0, 0),), ((0, 0), (1, 1)), ((0, 0, 0), (1, 1)), ((0, 0, 0), (1, 1, 1), (2, 2, 2)),
                    ((0, 0, -1), (1, 1, 1))):
            with self.assertRaises(ValueError):
                box_pool(*base, bad)
        for bad in (((0, 0, .5), (1, 1, 1)), ((0, 0, True), (1, 1, 1)), ((0, 0, "1"), (1, 1, 1)),
                    "radii", 3):
            with self.assertRaises(TypeError):
                box_pool(*base, bad)
        with self.assertRaises(ValueError):
            box_pool(*base, good, target_labels=("x", "y"))
        with self.assertRaises(TypeError):
            box_pool(*base, good, target_labels=("x", "y", 1.5))
        with self.assertRaises(TypeError):
            box_pool(*base, good, candidate_ids=("x", True, "z"))
        with self.assertRaises(TypeError):
            CandidateBoxPool(object(), good)
        pool = box_pool(*base, good)
        with self.assertRaises(ValueError):
            candidate_box_consistent(pool, (0, 1), (0,))
        with self.assertRaises(TypeError):
            candidate_box_consistent(pool, (0,), (0.0,))
        with self.assertRaises(ValueError):
            candidate_box_separates(pool, (2,))
        with self.assertRaises(ValueError):
            interval(pool, 0, 3)
        with self.assertRaises(TypeError):
            minimum_candidate_box_panel(pool, max_nodes=1.0)
        with self.assertRaises(TypeError):
            from_diagnostic_pool(pool)
        with self.assertRaises(TypeError):
            rational_json(0.5)

    def test_asymmetric_square_radius_matrix_axis(self):
        # E = K = 2; the transpose has the same shape but a different meaning.
        readings = ((0, 1), (0, 1))
        radii = ((F(3, 4), F(1, 2)), (0, 0))
        pool = box_pool((1, 1), readings, radii)
        self.assertEqual(candidate_box_masks(pool), (0, 1))
        transposed = box_pool((1, 1), readings, tuple(zip(*radii)))
        self.assertEqual(candidate_box_masks(transposed), (1, 1))
        for e in range(2):
            self.assertEqual(bool(candidate_box_masks(pool)[e]),
                             endpoint_separated(readings, radii, e, 0, 1))

    def test_masks_decoder_and_witnesses_against_endpoints(self):
        rng = random.Random(1101)
        for trial in range(250):
            pool = random_box_pool(rng, targets=trial % 3 == 0, zero_bias=trial % 2 == 0)
            costs, r, rho, t = raw(pool)
            pairs = [(a, b) for a in range(pool.candidates) for b in range(a + 1, pool.candidates)
                     if t[a] != t[b]]
            masks = candidate_box_masks(pool)
            for e in range(pool.size):
                for p, (a, b) in enumerate(pairs):
                    self.assertEqual(bool(masks[e] >> p & 1), endpoint_separated(r, rho, e, a, b))
            panel = tuple(e for e in range(pool.size) if rng.random() < .5)
            covers = all(any(endpoint_separated(r, rho, e, a, b) for e in panel) for a, b in pairs)
            self.assertEqual(candidate_box_separates(pool, panel), covers)
            witness = candidate_box_ambiguity(pool, panel)
            self.assertEqual(witness is None, covers)
            if witness is not None:
                self.assertNotEqual(t[witness.a], t[witness.b])
                for e, y in zip(panel, witness.observed):
                    for c in (witness.a, witness.b):
                        self.assertLessEqual(r[e][c] - rho[e][c], y)
                        self.assertLessEqual(y, r[e][c] + rho[e][c])
                self.assertLessEqual({witness.a, witness.b},
                                     set(candidate_box_consistent(pool, panel, witness.observed)))
            # every corner of every candidate box decodes to the true target iff covered
            if len(panel) <= 3:
                for truth in range(pool.candidates):
                    for signs in product((-1, 1), repeat=len(panel)):
                        y = tuple(r[e][truth] + s * rho[e][truth] for e, s in zip(panel, signs))
                        found = candidate_box_consistent(pool, panel, y)
                        expect = tuple(c for c in range(pool.candidates)
                                       if all(r[e][c] - rho[e][c] <= ye <= r[e][c] + rho[e][c]
                                              for e, ye in zip(panel, y)))
                        self.assertEqual(found, expect)
                        self.assertIn(truth, found)
                        if covers:
                            self.assertEqual(candidate_box_targets(pool, panel, y), (t[truth],))

    def test_common_envelope_masks_are_included(self):
        rng = random.Random(1102)
        for _ in range(200):
            pool = random_box_pool(rng, size=rng.randint(1, 6))
            envelope = [max(row) for row in pool.radii]
            hetero = candidate_box_masks(pool)
            env_masks = candidate_box_masks(common_envelope(pool))
            for h, m in zip(hetero, env_masks):
                self.assertEqual(h & m, m)
            if all(x > 0 for x in envelope):
                self.assertEqual(coverage_masks(pool.pool, envelope), env_masks)
            hb = minimum_candidate_box_panel(pool)
            eb = minimum_candidate_box_panel(common_envelope(pool))
            if eb.feasible:
                self.assertTrue(hb.feasible)
                self.assertLessEqual(hb.cost, eb.cost)
                self.assertTrue(candidate_box_separates(pool, eb.panel))


class Optimization(unittest.TestCase):
    def check(self, pool):
        oracle = exhaustive_box_panel(*raw(pool))
        dijkstra = cover_state_dijkstra(*raw(pool))
        self.assertEqual(oracle[0], dijkstra[0] is not None)
        everything = sum(pool.pool.costs, F(0))
        bounded = cost_bounded_box_panel(*raw(pool), everything)
        self.assertEqual(bounded[0], oracle[0])
        if oracle[0]:
            self.assertEqual(oracle[1], dijkstra[0])
            self.assertEqual(oracle[1], bounded[1])
            if oracle[1] > 0:
                below = cost_bounded_box_panel(*raw(pool), oracle[1] - F(1, 2))
                self.assertFalse(below[0])
        for packing in (True, False):
            for reduce in (True, False):
                result = minimum_candidate_box_panel(pool, packing=packing, reduce=reduce)
                self.assertEqual(result.feasible, oracle[0])
                if not oracle[0]:
                    self.assertEqual(result.status, "infeasible")
                    self.assertTrue(result.uncoverable)
                    continue
                self.assertEqual(result.status, "optimal")
                self.assertEqual(result.cost, oracle[1])
                self.assertEqual(result.lower_bound, oracle[1])
                self.assertEqual(panel_cost(pool, result.panel), result.cost)
                self.assertTrue(candidate_box_separates(pool, result.panel))
        return oracle[0]

    def test_seeded_tiny_rational_pools(self):
        rng = random.Random(1103)
        feasible = 0
        for trial in range(300):
            pool = random_box_pool(rng, targets=trial % 4 == 0, zero_bias=trial % 2 == 1)
            feasible += self.check(pool)
        self.assertGreater(feasible, 60)
        self.assertLess(feasible, 300)

    def test_dominated_and_zero_cost_experiments(self):
        # e0 dominates e1 (same mask, cheaper); e2 is free but separates nothing;
        # e3, e4 are free and together cover pairs that e0 needs 5 units for.
        readings = ((0, 10, 20), (0, 10, 20), (0, 0, 0), (0, 5, 5), (0, 0, 5))
        radii = ((1, 1, 1), (1, 1, 1), (0, 0, 0), (1, 1, 1), (1, 1, 1))
        pool = box_pool((5, 6, 0, 0, 0), readings, radii)
        self.check(pool)
        best = minimum_candidate_box_panel(pool)
        self.assertEqual((best.cost, best.panel), (0, (3, 4)))
        # many zero-cost duplicates: finite search, no repeated-word loop
        pool = box_pool((0,) * 12 + (1,), ((0, 0, 0),) * 12 + ((0, 3, 6),), ((1, 1, 1),) * 13)
        best = minimum_candidate_box_panel(pool)
        self.assertEqual((best.status, best.cost, best.panel), ("optimal", 1, (12,)))
        self.assertLess(best.nodes, 10)

    def test_agrees_with_common_backend_on_common_radii(self):
        rng = random.Random(1104)
        for _ in range(120):
            k, size = rng.randint(2, 4), rng.randint(1, 8)
            costs = [rng.randint(0, 5) for _ in range(size)]
            rows = [[rng.randint(-3, 3) for _ in range(k)] for _ in range(size)]
            eps = [F(rng.randint(1, 3), 2) for _ in range(size)]
            old = minimum_cost_panel(reading_pool(costs, rows), eps)
            new = minimum_candidate_box_panel(box_pool(costs, rows, [[x] * k for x in eps]))
            self.assertEqual(old.feasible, new.feasible)
            if old.feasible:
                self.assertEqual(old.cost, new.cost)

    def test_budget_exhaustion_is_inconclusive(self):
        rng = random.Random(1105)
        k, size = 6, 30
        costs = [rng.randint(1, 9) for _ in range(size)]
        rows = [[rng.randint(-6, 6) for _ in range(k)] for _ in range(size)]
        radii = [[F(rng.randint(0, 4), 2) for _ in range(k)] for _ in range(size)]
        pool = box_pool(costs, rows, radii)
        full = minimum_candidate_box_panel(pool)
        self.assertEqual(full.status, "optimal")
        dijkstra = cover_state_dijkstra(*raw(pool))
        self.assertEqual(dijkstra[0], full.cost)
        cut = minimum_candidate_box_panel(pool, max_nodes=1)
        self.assertGreater(full.nodes, 1)
        self.assertEqual(cut.status, "inconclusive")
        self.assertTrue(cut.feasible)
        self.assertTrue(candidate_box_separates(pool, cut.panel))
        self.assertLess(cut.lower_bound, full.cost)
        self.assertLessEqual(full.cost, cut.cost)

    def test_oracle_budgets_refuse(self):
        pool = box_pool((1,) * 17, ((0, 1),) * 17, ((0, 0),) * 17)
        with self.assertRaises(ValueError):
            exhaustive_box_panel(*raw(pool))
        with self.assertRaises(ValueError):
            cover_state_dijkstra(*raw(box_pool((1, 1), ((0, 1), (0, 2)), ((0, 0), (0, 0)))), max_states=0)

    def test_receipt_is_exact_and_inspectable(self):
        pool = box_pool((3, 1), ((0, 1, 2), (0, 0, 9)), ((F(1, 10), F(1, 2), 0), (0, 0, 1)),
                        candidate_ids=("a", "b", "c"))
        result = minimum_candidate_box_panel(pool)
        record = candidate_box_receipt(pool, result, oracle_cost=exhaustive_box_panel(*raw(pool))[1])
        self.assertEqual(record["schema"], "singularity.candidate-box-panel/1")
        self.assertEqual(record["radii"][0], [[1, 10], [1, 2], [0, 1]])
        self.assertEqual(record["cost"], [3, 1])
        self.assertEqual(record["independent_oracle_cost"], [3, 1])
        self.assertEqual(record["selected_margins"]["0"], [[2, 5], [19, 10], [1, 2]])
        self.assertEqual([c["covered_by"] for c in record["covered_pairs"]], [[0], [0], [0]])
        import json
        text = json.dumps(record)
        self.assertNotIn(".", text.replace("singularity.candidate", ""))


class ThermalAdapter(unittest.TestCase):
    def test_small_plate_radii_reused_and_oracles_agree(self):
        from singularity.thermal_diagnostics import (AffineCandidate, build_plate_candidates,
                                                     default_protocols, protocol_pool)
        models = build_plate_candidates(4)
        protocols = default_protocols((1, 2, 3, 4, 6, 8))[1::5][:12]
        data = protocol_pool(models, protocols, initial_radius=F(1, 100), sensor_noise=F(1, 1000))
        pool = from_diagnostic_pool(data)
        self.assertEqual(pool.radii, data.error_bounds)
        self.assertEqual(pool.candidate_ids, data.candidate_ids)
        # closed form for the positive plate: nu + rho0 (1 - lambda_c)^T
        for e, (word, _) in enumerate(protocols):
            for c, model in enumerate(models):
                decay = F(49, 50) if model.identifier == "loss_double" else F(99, 100)
                self.assertEqual(pool.radii[e][c], F(1, 1000) + F(1, 100) * decay ** len(word))
        self.assertEqual(tuple(max(row) for row in pool.radii), data.epsilon)
        self.check_against_oracles(pool)
        # Finite contrast: the common envelope cannot identify, the candidate boxes can.
        old = minimum_cost_panel(data.pool, data.panel_epsilon)
        new = minimum_candidate_box_panel(pool)
        self.assertFalse(old.feasible)
        self.assertEqual((new.status, new.cost, new.panel), ("optimal", 19, (4, 9)))
        self.assertTrue(all(3 in pair for pair in old.uncoverable))
        # fault-location target only: blocked-left vs blocked-right need not be told apart
        located = from_diagnostic_pool(data, target_labels=("ok", "k", "b", "loss", "bond", "bond"))
        self.assertNotIn((4, 5), required_pairs(located))
        self.check_against_oracles(located)
        # signed sparse model: |A| propagation gives the attained 1/20 radius
        first = AffineCandidate("signed-a", 1, ((0, 0, F(-1, 2)),), (0,), ((-2,),))
        second = AffineCandidate("signed-b", 1, ((0, 0, F(1, 2)),), (0,), ((2,),))
        signed = from_diagnostic_pool(protocol_pool((first, second), (((0, 0), 0),),
                                                    initial_radius=F(1, 10), sensor_noise=0,
                                                    sensor_costs=(1,)))
        self.assertEqual(signed.radii, ((F(1, 20), F(1, 20)),))
        self.assertEqual(minimum_candidate_box_panel(signed).status, "infeasible")

    def check_against_oracles(self, pool):
        result = minimum_candidate_box_panel(pool)
        oracle = exhaustive_box_panel(*raw(pool), max_subsets=2**12)
        self.assertEqual(result.feasible, oracle[0])
        if oracle[0]:
            self.assertEqual(result.cost, oracle[1])
            self.assertEqual(cover_state_dijkstra(*raw(pool))[0], oracle[1])


if __name__ == "__main__":
    unittest.main()
