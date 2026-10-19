"""Probability mixing, byte alignment and paired-block aggregation contracts."""
import importlib.util
from pathlib import Path
import unittest

try:
    import numpy as np
except ImportError:
    np = None

if np is not None:
    _PATH = Path(__file__).resolve().parents[1]/"scripts"/"confirm_predictive_mixture.py"
    _SPEC = importlib.util.spec_from_file_location("confirm_predictive_mixture", _PATH)
    mixture = importlib.util.module_from_spec(_SPEC)
    _SPEC.loader.exec_module(mixture)


@unittest.skipIf(np is None, "optional numpy unavailable")
class PredictiveMixtureTests(unittest.TestCase):
    def test_mixture_endpoints_and_tune_selection(self):
        targets = np.array([0, 1, 0])
        neural = np.full((3, 256), .1/255)
        neural[np.arange(3), targets] = .9
        counts = np.full((3, 256), .5/255)
        counts[np.arange(3), targets] = .5
        selected = mixture.select_weight(neural, counts, targets)
        self.assertEqual(selected["count_weight"], 0.)
        selected = mixture.select_weight(counts, neural, targets)
        self.assertEqual(selected["count_weight"], 1.)
        self.assertEqual(mixture.select_weight(neural, neural, targets)["count_weight"], 0.)

    def test_count_alignment_every_target_and_reset(self):
        raw = bytes((i%11 for i in range(131)))
        refs = mixture._references()
        model = refs.fit_counts(raw)
        probabilities = mixture.count_probabilities(model, raw, .1)
        self.assertEqual(len(probabilities), len(raw)-1)
        for i, (history, target) in enumerate(refs.events(raw)):
            expected = refs.probability(model, 3, .1, history, target)
            self.assertAlmostEqual(probabilities[i, target], expected, places=14)
        histories = [history for history, _ in refs.events(raw)]
        self.assertEqual(len(histories[64]), 1)
        self.assertEqual(len(histories[65]), 2)

    def test_weighted_block_bootstrap_constant_effect(self):
        differences = np.full(32767, -.125)
        result = mixture.paired_blocks(differences)
        self.assertEqual(result["block_count"], 16)
        self.assertEqual(result["block_target_counts"][-1], 2047)
        self.assertEqual(result["percentile_95_interval"], [-.125, -.125])
        self.assertEqual(result["blocks_with_negative_mean"], 16)

    def test_invalid_probability_rejected(self):
        with self.assertRaises(ValueError):
            mixture.losses_and_metrics(np.ones((3, 256)), np.zeros(3, dtype=int))
        with self.assertRaises(ValueError):
            mixture.losses_and_metrics(np.ones((2, 256))/256, np.zeros(3, dtype=int))

    def test_neural_window_targets_exactly_once(self):
        try:
            import torch
        except ImportError:
            self.skipTest("optional torch unavailable")

        class Uniform(torch.nn.Module):
            def forward(self, x):
                return torch.zeros((*x.shape, 256))

        raw = bytes((i%251 for i in range(132)))
        probabilities, targets = mixture.infer(Uniform(), raw, batch_size=2)
        self.assertTrue(np.array_equal(targets, np.frombuffer(raw[1:], dtype=np.uint8)))
        self.assertEqual(probabilities.shape, (131, 256))
        self.assertTrue(np.all(probabilities == 1/256))


if __name__ == "__main__":
    unittest.main()
