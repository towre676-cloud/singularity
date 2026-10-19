"""Independent model-free evidence replay and causal tamper checks."""
import copy
from fractions import Fraction
import importlib.util
import itertools
import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("independent_gating_evidence", ROOT / "scripts/verify_gating_confirmation.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class GatingSyntheticEvidence(unittest.TestCase):
    def rows(self):
        tokens = [0, 1, 0, 1, 0, 1, 2, 1, 0, 1, 0, 1, 2]
        rows = list(VERIFY.count_rows(tokens, 3))
        for index, row in enumerate(rows):
            row["neural_nll_hex"] = (-math.log((.2, .4, .6)[index % 3])).hex()
        return tokens, rows

    def test_first_target_has_no_learned_counts(self):
        _, rows = self.rows()
        self.assertEqual(rows[0]["feature"], {"context": [0], "longest_order": -1, "support": 0, "distinct": 0})
        self.assertEqual(rows[0]["count_nll_hex"], (-math.log(1 / 3)).hex())
        self.assertEqual(rows[1]["feature"], {"context": [0, 1], "longest_order": 0, "support": 1, "distinct": 1})

    def test_direct_prefix_follower_counts(self):
        tokens, rows = self.rows()
        # Rebuild the longest eligible row by explicitly scanning preceding
        # edges, independently of the verifier's incrementally stored tables.
        for index, row in enumerate(rows):
            history = tokens[:index + 1][-4:]
            longest, support, distinct = -1, 0, 0
            for order in range(min(4, len(history)) + 1):
                context = history[-order:] if order else []
                followers = []
                for edge in range(1, index + 1):
                    preceding = tokens[:edge][-4:]
                    if len(preceding) >= order and (preceding[-order:] if order else []) == context:
                        followers.append(tokens[edge])
                if followers:
                    longest, support, distinct = order, len(followers), len(set(followers))
            self.assertEqual((row["feature"]["longest_order"], row["feature"]["support"], row["feature"]["distinct"]),
                             (longest, support, distinct))

    def test_every_arm_protects_and_uses_prior_prefix(self):
        tokens, rows = self.rows()
        replay = VERIFY.verify_target_rows(rows, tokens, 3)
        self.assertEqual(len(replay["prior_to_target_count_weights_hex"]), 18)
        for values in replay["prior_to_target_count_weights_hex"].values():
            self.assertEqual(float.fromhex(values[0]), 0.)
        posterior = [float.fromhex(v) for v in replay["hierarchy_prior_to_target_posterior_hex"][0]]
        self.assertAlmostEqual(posterior[0], .95, places=14)
        self.assertAlmostEqual(math.fsum(posterior), 1., places=14)
        neural = float.fromhex(replay["arms"]["neural"]["loss_sum_nats_hex"])
        for name, arm in replay["arms"].items():
            if name not in ("neural", "adaptive_count"):
                self.assertLessEqual(float.fromhex(arm["loss_sum_nats_hex"]), neural + VERIFY.CEILING + 1e-10)

    def test_rejects_target_leak_into_count_feature(self):
        tokens, rows = self.rows()
        rows[0]["feature"].update(longest_order=1, support=1, distinct=1)
        with self.assertRaisesRegex(ValueError, "pretarget feature differs"):
            VERIFY.verify_target_rows(rows, tokens, 3)

    def test_rejects_changed_count_probability(self):
        tokens, rows = self.rows()
        rows[4]["count_nll_hex"] = (float.fromhex(rows[4]["count_nll_hex"]) + .001).hex()
        with self.assertRaisesRegex(ValueError, "count probability"):
            VERIFY.verify_target_rows(rows, tokens, 3)

    def test_pcg64_known_answer_vectors(self):
        # NumPy default_rng(7102026).integers(0,n,...) known-answer vectors.
        self.assertEqual(next(VERIFY.bootstrap_indices(24))[:12], [16, 13, 1, 10, 13, 23, 4, 18, 7, 12, 18, 18])
        draws = VERIFY.bootstrap_indices(8)
        self.assertEqual(next(draws) + next(draws)[:4], [5, 4, 0, 3, 4, 7, 1, 6, 2, 4, 6, 6])
        self.assertEqual(VERIFY.quantile([0., 0., 1., 2.], .5), .5)
        self.assertAlmostEqual(VERIFY.quantile([0., 0., 1., 2.], .975), 1.925)

    def test_exact_rational_marginal_on_every_short_binary_sequence(self):
        # Enumerate all32 binary outcomes. The independent oracle scans the
        # complete prior prefix and uses exact rational likelihood products;
        # it does not use the verifier's stored tables or log accumulators.
        for outcomes in itertools.product(range(2), repeat=5):
            tokens = [0, *outcomes]
            rows = list(VERIFY.count_rows(tokens, 2))
            neural_joint = Fraction(1)
            gate_joint = {p["id"]: Fraction(1) for p in VERIFY.POLICIES}
            for index, row in enumerate(rows):
                target = outcomes[index]
                neural = Fraction(2, 3) if target == 0 else Fraction(1, 3)
                row["neural_nll_hex"] = (-math.log(float(neural))).hex()
                count = Fraction(1, 2)
                longest, support = -1, 0
                history = tokens[:index + 1][-4:]
                for order in range(min(4, len(history)) + 1):
                    context = history[-order:] if order else []
                    followers = [tokens[edge] for edge in range(1, index + 1)
                                 if edge >= order and (tokens[max(0, edge - order):edge] if order else []) == context]
                    if followers:
                        total, distinct = len(followers), len(set(followers))
                        count = (followers.count(target) + distinct * count) / (total + distinct)
                        longest, support = order, total
                neural_joint *= neural
                for policy in VERIFY.POLICIES:
                    alpha = (Fraction(str(policy["alpha"])) if longest >= policy["min_order"]
                             and support >= policy["min_support"] else Fraction(0))
                    gate_joint[policy["id"]] *= (1 - alpha) * neural + alpha * count
            replay = VERIFY.reconstruct(rows)
            for policy in VERIFY.POLICIES:
                exact = Fraction(19, 20) * neural_joint + Fraction(1, 20) * gate_joint[policy["id"]]
                self.assertGreaterEqual(exact, Fraction(19, 20) * neural_joint)
                self.assertAlmostEqual(float.fromhex(replay["arms"][policy["id"]]["loss_sum_nats_hex"]),
                                       -math.log(float(exact)), places=12)
            hierarchy = Fraction(19, 20) * neural_joint + sum(gate_joint.values(), Fraction(0)) / 360
            self.assertAlmostEqual(float.fromhex(replay["arms"]["hierarchy_protected"]["loss_sum_nats_hex"]),
                                   -math.log(float(hierarchy)), places=12)

    def test_neural_fallback_and_minimum_selection(self):
        candidates = ["neural", *(p["id"] for p in VERIFY.POLICIES)]
        losses = {name: {"loss_sum_nats_hex": (10. if name == "neural" else 10.1).hex(),
                         "nll_nats_per_token": 1. if name == "neural" else 1.01} for name in candidates}
        development = {"aggregate": losses, "created_at_utc": "2026-10-19T12:00:00+00:00"}
        protocol = {"selection": "minimum development loss, lexical ties"}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "development.json"
            path.write_text(json.dumps(development))
            selection = {"schema": "singularity.pretrained-gating-selection/1", "protocol_sha256": "protocol",
                         "development_results_sha256": VERIFY.file_sha(path), "development_candidate_losses": losses,
                         "selected_arm": "neural", "heldout_scored_before_selection": False,
                         "selection_rule": protocol["selection"], "frozen_at_utc": "2026-10-19T12:01:00+00:00"}
            self.assertEqual(VERIFY.verify_selection(protocol, "protocol", development, path, selection), "neural")
            forged = copy.deepcopy(selection)
            forged["selected_arm"] = candidates[1]
            with self.assertRaisesRegex(ValueError, "development minimum"):
                VERIFY.verify_selection(protocol, "protocol", development, path, forged)


class GatingPublishedEvidence(unittest.TestCase):
    def test_four_model_population(self):
        protocol, identities, encoded = VERIFY.check_protocol(VERIFY.DEFAULT)
        self.assertEqual(set(identities), {"gpt2", "smollm2-360m", "smollm2-1_7b", "qwen25-1_5b"})
        self.assertEqual(len(protocol["documents"]), 36)
        self.assertTrue(all(len(documents) == 36 for documents in encoded.values()))

    def test_independent_full_evidence_replay(self):
        result = VERIFY.verify_study()
        self.assertTrue(result["verified"])
        self.assertEqual(len(result["completed_splits"]), 8)
        self.assertEqual(result["verified_targets"], 4 * 36 * 512)

    def test_rejects_empty_bootstrap_interval(self):
        name = "gpt2"
        output = VERIFY.DEFAULT
        protocol = VERIFY.read(output / "protocol.json")
        heldout = VERIFY.read(output / "models" / name / "heldout/results.json")
        selection = VERIFY.read(output / "models" / name / "selection.json")
        records = [VERIFY.read(output / binding["path"]) for binding in heldout["documents"]]
        analysis = VERIFY.read(output / "models" / name / "heldout_analysis.json")
        analysis["comparisons"]["all_domains"]["primary_selected_minus_neural"]["descriptive_paired_document_bootstrap_95_interval"] = []
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            for relative in ("protocol.json", f"models/{name}/selection.json", f"models/{name}/heldout/results.json"):
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(output / relative, destination)
            (target / "models" / name / "heldout_analysis.json").write_text(json.dumps(analysis))
            with self.assertRaisesRegex(ValueError, "two endpoints"):
                VERIFY.verify_analysis(target, name, protocol, heldout, records, selection)


if __name__ == "__main__":
    unittest.main()
