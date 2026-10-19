"""Causal gates: exact likelihood identities, state order and independent replay."""
from fractions import Fraction
import importlib.util
import itertools
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from singularity.training.repetition_blend import (
    REPETITION_POLICIES, ProtectedRepetitionBlend, count_target_probability,
    gate_enabled, repetition_feature,
)
from singularity.training.token_experts import AdaptiveTokenCounts

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gating_study_tests", ROOT / "scripts/confirm_pretrained_gating.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class RepetitionBlendTests(unittest.TestCase):
    def test_exact_rational_protection_and_normalization_all_binary_sequences(self):
        policy = {"id": "repeat", "min_order": 1, "min_support": 1, "alpha": .5}
        prior = (Fraction(19, 20), Fraction(1, 20))
        total_joint = Fraction(0)
        for targets in itertools.product((0, 1), repeat=5):
            state = ProtectedRepetitionBlend((policy,))
            component_joint = [Fraction(1), Fraction(1)]
            online_joint = Fraction(1)
            counts = AdaptiveTokenCounts(2, 1)
            counts.reset((0,))
            for target in targets:
                feature = repetition_feature(counts)
                neural = (Fraction(2, 3), Fraction(1, 3))
                # Independent exact rational implementation of Witten--Bell.
                count_probs = [Fraction(1, 2), Fraction(1, 2)]
                for order in (0, 1):
                    context = counts.history[-order:] if order else ()
                    row = counts.tables[order].get(context)
                    if row:
                        distinct, total = len(row), sum(row.values())
                        count_probs = [(row.get(y, 0) + distinct * count_probs[y]) / (total + distinct) for y in (0, 1)]
                alpha = Fraction(1, 2) if gate_enabled(policy, feature) else Fraction(0)
                policy_probs = [(1 - alpha) * neural[y] + alpha * count_probs[y] for y in (0, 1)]
                evidence = sum(p * ll for p, ll in zip(prior, component_joint))
                posterior = [p * ll / evidence for p, ll in zip(prior, component_joint)]
                predicted = [posterior[0] * neural[y] + posterior[1] * policy_probs[y] for y in (0, 1)]
                self.assertEqual(sum(predicted), Fraction(1))
                weight = state.predict_weight(feature)
                self.assertAlmostEqual(weight, float(posterior[1] * alpha), places=14)
                actual_loss = state.observe(float(neural[target]), float(count_probs[target]))
                self.assertAlmostEqual(actual_loss, -math.log(float(predicted[target])), places=13)
                component_joint[0] *= neural[target]
                component_joint[1] *= policy_probs[target]
                online_joint *= predicted[target]
                self.assertEqual(online_joint, sum(p * ll for p, ll in zip(prior, component_joint)))
                self.assertGreaterEqual(online_joint, prior[0] * component_joint[0])
                counts.update(target)
            total_joint += online_joint
            audit = state.guarantee()
            self.assertAlmostEqual(audit["online_cumulative_nll"], -math.log(float(online_joint)), places=13)
            self.assertGreaterEqual(audit["neural_protection_slack_nats"], -1e-12)
        self.assertEqual(total_joint, Fraction(1))

    def test_scalar_count_probability_matches_full_normalized_distribution(self):
        counts = AdaptiveTokenCounts(7, 4)
        counts.reset((2,))
        for target in (2, 4, 2, 4, 2, 4, 2, 1, 4, 4, 2):
            feature = repetition_feature(counts)
            probabilities = counts.probabilities()
            self.assertAlmostEqual(sum(count_target_probability(counts, y) for y in range(7)), 1., places=14)
            for y in range(7):
                self.assertAlmostEqual(count_target_probability(counts, y), probabilities[y], places=15)
            # Indexing any target cannot alter the prefix feature.
            self.assertEqual(feature, repetition_feature(counts))
            counts.update(target)

    def test_future_targets_cannot_change_prefix_predictions(self):
        def run(targets):
            counts, state, weights, losses = AdaptiveTokenCounts(3, 4), ProtectedRepetitionBlend(), [], []
            counts.reset((1,))
            for target in targets:
                weights.append(state.predict_weight(repetition_feature(counts)))
                losses.append(state.observe((.3, .5, .2)[target], count_target_probability(counts, target)))
                counts.update(target)
            return weights, losses
        left = run((0, 1, 0, 1, 0, 1, 0))
        right = run((0, 1, 0, 1, 2, 2, 2))
        self.assertEqual(left[0][:5], right[0][:5])
        self.assertEqual(left[1][:4], right[1][:4])

    def test_independent_closed_form_study_replay_matches_streaming_module(self):
        counts = AdaptiveTokenCounts(5, 4)
        counts.reset((1,))
        rows = []
        targets = (2, 1, 2, 1, 2, 1, 2, 1, 4, 3, 1, 2, 1)
        for index, target in enumerate(targets):
            rows.append({"target": target, "feature": repetition_feature(counts),
                         "neural_nll_hex": (-math.log(.1 + (index % 3) / 10)).hex(),
                         "count_nll_hex": (-math.log(count_target_probability(counts, target))).hex()})
            counts.update(target)
        replay = study.replay_rows(rows)
        for policies, name in ((REPETITION_POLICIES, "hierarchy_protected"), *(([p], p["id"]) for p in REPETITION_POLICIES)):
            state = ProtectedRepetitionBlend(policies)
            for index, row in enumerate(rows):
                weight = state.predict_weight(row["feature"])
                if name != "hierarchy_protected":
                    self.assertAlmostEqual(weight, float.fromhex(replay["prior_to_target_count_weights_hex"][name][index]), places=13)
                loss = state.observe(math.exp(-float.fromhex(row["neural_nll_hex"])), math.exp(-float.fromhex(row["count_nll_hex"])))
                self.assertAlmostEqual(loss, float.fromhex(replay["losses_hex"][name][index]), places=12)
            self.assertAlmostEqual(state.guarantee()["online_cumulative_nll"], float.fromhex(replay["arms"][name]["loss_sum_nats_hex"]), places=12)

    def test_contract_and_invalid_state_rejected(self):
        feature = {"longest_order": 1, "support": 1, "distinct": 1}
        state = ProtectedRepetitionBlend()
        with self.assertRaises(RuntimeError):
            state.observe(.2, .3)
        state.predict_weight(feature)
        with self.assertRaises(RuntimeError):
            state.predict_weight(feature)
        with self.assertRaises(RuntimeError):
            state.guarantee()
        for probabilities in ((-1, 1), (math.nan, .5), (.5, 2)):
            with self.assertRaises(ValueError):
                state.observe(*probabilities)
        state.observe(.2, .3)
        with self.assertRaises(ValueError):
            state.predict_weight({"longest_order": 1, "support": 1, "distinct": 2})
        for policies in (({"id": "bad", "alpha": .5, "min_order": True, "min_support": 1},),
                         ({"id": "bad", "alpha": math.nan, "min_order": 1, "min_support": 1},)):
            with self.assertRaises(ValueError):
                ProtectedRepetitionBlend(policies)
        for prior in (0, 1, math.nan):
            with self.assertRaises(ValueError):
                ProtectedRepetitionBlend(neural_prior=prior)
        pure = ProtectedRepetitionBlend(())
        self.assertEqual(pure.predict_weight(feature), 0.)
        pure.observe(.4, .9)
        self.assertEqual(pure.guarantee()["neural_extra_loss_ceiling_nats"], 0.)

    def test_chunked_retention_binds_target_order_and_derived_outputs(self):
        counts = AdaptiveTokenCounts(3, 4)
        tokens = [1] + [0, 1, 0, 1, 2] * 30
        counts.reset(tokens[:1])
        rows = []
        for target in tokens[1:]:
            rows.append({"target": target, "feature": repetition_feature(counts),
                         "neural_nll_hex": (-math.log(.2)).hex(),
                         "count_nll_hex": (-math.log(count_target_probability(counts, target))).hex()})
            counts.update(target)
        record = {"targets": len(rows), "target_rows": rows, **study.replay_rows(rows)}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            path = output / "documents/000.json"
            study.retain_record(output, path, record)
            self.assertTrue(all(p.stat().st_size <= 65536 for p in output.rglob("*.json")))
            reconstructed = study.load_record(output, path)
            study.verify_trace(reconstructed, {"token_ids": tokens}, 3)
            reconstructed["target_rows"][1]["feature"]["support"] += 1
            with self.assertRaises(ValueError):
                study.verify_trace(reconstructed, {"token_ids": tokens}, 3)

    def test_development_selection_is_frozen_once_and_rejects_existing_holdout(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            source_path = output / "source.json"
            study.write_json(source_path, {"source": "synthetic unit-test fixture"})
            tokens = [1] + [0, 1] * 40
            entries = []
            for index in (0, 1):
                path = output / "tokens" / f"{index}.json"
                encoded = {"document": index, "token_ids": tokens}
                study.write_json(path, encoded)
                entries.append({"document": index, "encoding_path": str(path.relative_to(output)),
                                "encoding_sha256": study.file_sha(path), "token_ids_sha256": study.sha(study.canonical(tokens))})
            identity_path = output / "identity.json"
            study.write_json(identity_path, {"encoded_documents": entries})
            protocol = {"source_path": str(source_path), "source_sha256": study.file_sha(source_path),
                        "documents": [{"document": 0, "split": "development"}, {"document": 1, "split": "heldout"}],
                        "dependency_sha256": {}, "policies": list(REPETITION_POLICIES),
                        "models": {"toy": {"identity_path": "identity.json", "sha256": study.file_sha(identity_path)}},
                        "selection": "minimum development loss then lexical ID"}
            study.write_json(output / "protocol.json", protocol)
            counts, rows = AdaptiveTokenCounts(3, 4), []
            counts.reset(tokens[:1])
            for target in tokens[1:]:
                rows.append({"target": target, "feature": repetition_feature(counts),
                             "neural_nll_hex": (-math.log(.2)).hex(),
                             "count_nll_hex": (-math.log(count_target_probability(counts, target))).hex()})
                counts.update(target)
            record = {"document": 0, "domain": "toy", "name": "development fixture", "targets": len(rows),
                      "target_rows": rows, "protocol_sha256": study.file_sha(output / "protocol.json"),
                      "selection_sha256": None, **study.replay_rows(rows)}
            path = output / "models/toy/development/documents/000.json"
            study.retain_record(output, path, record)
            relative = str(path.relative_to(output))
            report = {"protocol_sha256": record["protocol_sha256"], "selection_sha256": None,
                      "vocabulary_size": 3, "documents": [{"document": 0, "path": relative, "sha256": study.file_sha(path)}],
                      "trace_files_sha256": {relative: study.file_sha(path)}, "aggregate": study.summarize([record])}
            study.write_json(output / "models/toy/development/results.json", report)
            args = SimpleNamespace(output=output, name="toy")
            forbidden = output / "models/toy/heldout/unselected.json"
            study.write_json(forbidden, {})
            with self.assertRaises(FileExistsError):
                study.select(args)
            forbidden.unlink()
            selection = study.select(args)
            self.assertFalse(selection["heldout_scored_before_selection"])
            self.assertIn(selection["selected_arm"], ["neural", *(p["id"] for p in REPETITION_POLICIES)])
            self.assertEqual(selection["development_results_sha256"], study.file_sha(output / "models/toy/development/results.json"))
            with self.assertRaises(FileExistsError):
                study.select(args)


@unittest.skipUnless(importlib.util.find_spec("torch"), "optional Torch unavailable")
class GatingForwardTests(unittest.TestCase):
    def test_full_available_prefix_and_target_alignment(self):
        import torch

        class CausalToy:
            def __call__(self, input_ids, **kwargs):
                total = input_ids.cumsum(1).to(torch.float64)
                logits = torch.stack([torch.sin(total + k) for k in range(5)], dim=-1)
                return SimpleNamespace(logits=logits)
        tokens = [1, 2, 1, 2, 1, 2, 1, 2, 3, 4]
        record = study.score_document(CausalToy(), tokens, 5)
        for index, target in enumerate(tokens[1:]):
            logits = [math.sin(sum(tokens[:index + 1]) + k) for k in range(5)]
            expected = math.log(sum(math.exp(v) for v in logits)) - logits[target]
            self.assertAlmostEqual(float.fromhex(record["target_rows"][index]["neural_nll_hex"]), expected, places=14)
        other = study.score_document(CausalToy(), tokens[:7] + [4, 4, 4], 5)
        self.assertEqual(record["target_rows"][:6], other["target_rows"][:6])
        study.verify_trace(record, {"token_ids": tokens}, 5)


if __name__ == "__main__":
    unittest.main()
