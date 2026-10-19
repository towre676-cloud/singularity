"""Independent small fixtures for the post-training stdlib byte references."""

import copy
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "byte_reference_baselines.py"
SPEC = importlib.util.spec_from_file_location("byte_reference_baselines", SOURCE)
reference = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reference)


class ByteReferenceTests(unittest.TestCase):
    def test_window_boundary_forbids_previous_window_context(self):
        self.assertEqual(list(reference.events(b"ABCD", sequence_length=2)),
                         [(b"A", ord("B")), (b"AB", ord("C")), (b"C", ord("D"))])
        model = reference.fit_counts(b"ABCD", sequence_length=2)
        self.assertEqual(model["tables"][2], {b"AB": {ord("C"): 1}})
        self.assertEqual(model["train_targets"], 3)

    def test_smoothing_normalizes_and_unseen_context_is_uniform(self):
        model = reference.fit_counts(b"ABAC")
        total = sum(reference.probability(model, 2, 1., b"A", byte) for byte in range(256))
        self.assertAlmostEqual(total, 1., places=12)
        self.assertEqual(reference.probability(model, 2, 1., b"A", ord("D")), 1 / 258)
        self.assertEqual(reference.probability(model, 2, .01, b"Z", ord("D")), 1 / 256)
        self.assertAlmostEqual(reference.score(model, b"AD", 2, 1.)["nll_nats_per_byte"],
                               math.log(258), places=12)

    def test_scoring_preserves_training_counts_and_every_tail_target(self):
        model = reference.fit_counts(b"ABCABC", sequence_length=2)
        frozen = copy.deepcopy(model)
        result = reference.score(model, b"XYZWQ", 3, .1)
        self.assertEqual(result["valid_targets"], 4)
        self.assertEqual(result["targets_by_available_history_length"], {1: 2, 2: 2})
        self.assertEqual(model, frozen)

    def test_alpha_selected_from_tune_before_one_test_score_per_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpora = {"train": b"AAAAB", "tune": b"CCCC", "test": b"BBBB"}
            for name, raw in corpora.items():
                (Path(tmp) / (name + ".txt")).write_bytes(raw)
            real_score = reference.score
            calls = []

            def recording_score(model, raw, order, alpha):
                calls.append((raw, order, alpha))
                return real_score(model, raw, order, alpha)

            with patch.object(reference, "score", side_effect=recording_score):
                report = reference.build_report(tmp)
            self.assertEqual(report["references"][0]["selected_alpha"], 1.)
            # A TEST-driven choice for the observed B would prefer .01 instead.
            model = reference.fit_counts(corpora["train"])
            self.assertEqual(reference.select_alpha(model, corpora["test"], 1)["selected_alpha"], .01)
            self.assertEqual([raw for raw, _, _ in calls[:9]], [corpora["tune"]] * 9)
            self.assertEqual([raw for raw, _, _ in calls[9:]], [corpora["test"]] * 3)
            self.assertEqual(len(calls), 12)
            self.assertTrue(all(row["test_scoring_calls"] == 1 for row in report["references"]))


if __name__ == "__main__":
    unittest.main()
