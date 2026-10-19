"""Scientific contracts for portable causal byte experts and frozen blending."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

from singularity.training.byte_experts import CountByteExpert, byte_events

try:
    import torch
except ImportError:
    torch = None


class PortableByteCountTests(unittest.TestCase):
    def test_fitting_and_scoring_match_independent_reference(self):
        path = Path(__file__).resolve().parents[1] / "scripts" / "byte_reference_baselines.py"
        spec = importlib.util.spec_from_file_location("independent_byte_reference", path)
        reference = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reference)
        train, heldout = b"ABACABABADABAC", b"ABXABYABZ"
        counts = reference.fit_counts(train, 3)
        for order in (1, 2, 3):
            for alpha in (.01, .1, 1.):
                expert = CountByteExpert.fit(train, order, alpha, 3)
                for history, target in byte_events(heldout, 3):
                    self.assertAlmostEqual(expert.probabilities(history)[target],
                                           reference.probability(counts, order, alpha, history, target), places=15)

    def test_window_boundaries_are_strict_and_targets_shift_once(self):
        self.assertEqual(list(byte_events(b"ABCDE", 2)),
                         [(b"A", 66), (b"AB", 67), (b"C", 68), (b"CD", 69)])
        expert = CountByteExpert.fit(b"ABCDE", sequence_length=2)
        self.assertEqual(expert.tables[2], {b"AB": {67: 1}, b"CD": {69: 1}})
        single = CountByteExpert.fit(b"ABCDE", sequence_length=1)
        self.assertEqual(single.tables[2], {})

    def test_distributions_normalize_and_unseen_context_is_uniform(self):
        expert = CountByteExpert.fit(b"AAAAB", order=3, alpha=.01)
        for history in (b"", b"A", b"AA", b"XY"):
            probabilities = expert.probabilities(history)
            self.assertEqual(len(probabilities), 256)
            self.assertAlmostEqual(math.fsum(probabilities), 1., places=14)
            self.assertTrue(all(value > 0 for value in probabilities))
        self.assertEqual(expert.probabilities(b"XY"), (1 / 256,) * 256)

    def test_portable_serialization_roundtrip_and_evaluation_do_not_fit(self):
        expert = CountByteExpert.fit(b"ABCABCAB", order=3, alpha=.1, sequence_length=2)
        frozen = copy.deepcopy(expert.to_dict())
        for history, _ in byte_events(b"XYZXYZXYZ", 2):
            expert.probabilities(history)
        self.assertEqual(expert.to_dict(), frozen)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "counts.json"
            digest = expert.save(path)
            self.assertEqual(CountByteExpert.load(path).to_dict(), frozen)
            self.assertEqual(len(digest), 64)
            self.assertNotIn("XYZ", path.read_text())

    def test_invalid_or_duplicate_serialized_counts_are_rejected(self):
        payload = CountByteExpert.fit(b"ABCD").to_dict()
        bad = copy.deepcopy(payload)
        bad["tables"]["1"].append(bad["tables"]["1"][0])
        with self.assertRaises(ValueError):
            CountByteExpert.from_dict(bad)
        bad = copy.deepcopy(payload)
        bad["tables"]["0"][0]["counts"][0][1] += 1
        with self.assertRaises(ValueError):
            CountByteExpert.from_dict(bad)
        for kwargs in ({"alpha": 0}, {"alpha": float("nan")}, {"order": 4},
                       {"sequence_length": 0}, {"sequence_length": True}):
            with self.assertRaises(ValueError):
                CountByteExpert.fit(b"ABCD", **kwargs)


@unittest.skipIf(torch is None, "optional tensor/mixture tests require PyTorch")
class FrozenByteMixtureTests(unittest.TestCase):
    def test_convex_distribution_is_normalized_stable_and_has_exact_limits(self):
        from singularity.training.byte_experts import mixture_log_probs
        neural = torch.tensor([[1000., -1000., 0.]], dtype=torch.float64).log_softmax(-1)
        counts = torch.tensor([[.1, .2, .7]], dtype=torch.float64).log()
        self.assertTrue(torch.equal(mixture_log_probs(neural, counts, 1.), neural))
        self.assertTrue(torch.equal(mixture_log_probs(neural, counts, 0.), counts))
        result = mixture_log_probs(neural, counts, .37)
        self.assertTrue(torch.isfinite(result).all())
        self.assertTrue(torch.allclose(result.exp(), .37 * neural.exp() + .63 * counts.exp(), atol=1e-15, rtol=0))
        self.assertAlmostEqual(float(result.exp().sum()), 1., places=14)
        for weight in (-.1, 1.1, float("nan"), True):
            with self.assertRaises(ValueError):
                mixture_log_probs(neural, counts, weight)
        with self.assertRaises(ValueError):
            mixture_log_probs(neural + 1, counts, .5)

    def test_count_logits_ignore_future_tokens_and_other_window_history(self):
        from singularity.training.byte_experts import count_log_probs
        expert = CountByteExpert.fit(b"ABACABAD", sequence_length=4)
        inputs = torch.tensor([[65, 66, 67, 68], [67, 68, 69, 70]])
        original = count_log_probs(expert, inputs)
        changed = inputs.clone()
        changed[0, 3] = 255
        self.assertTrue(torch.equal(original[0, :3], count_log_probs(expert, changed)[0, :3]))
        self.assertTrue(torch.equal(original[1, 0], torch.tensor(expert.probabilities(b"C"), dtype=torch.float64).log()))
        with self.assertRaises(ValueError):
            count_log_probs(expert, inputs.float())

    def test_target_padding_every_tail_byte_and_no_count_updates(self):
        from singularity.training.byte_experts import score_frozen_mixture

        class UniformModel(torch.nn.Module):
            def forward(self, inputs):
                return torch.zeros((*inputs.shape, 256), dtype=torch.float64)

        expert = CountByteExpert.fit(b"ABACABAD", sequence_length=3)
        state = copy.deepcopy(expert.to_dict())
        model = UniformModel()
        model.train()
        raw = b"ABYACZZX"
        report = score_frozen_mixture(model, expert, raw, 0., batch_size=2, return_target_losses=True)
        self.assertTrue(model.training)
        self.assertEqual(expert.to_dict(), state)
        independent_losses = [-math.log(expert.probabilities(history)[target]) for history, target in byte_events(raw, 3)]
        self.assertEqual(report["experts"]["count"]["target_nll_nats"], independent_losses)
        for result in report["experts"].values():
            self.assertEqual(result["valid_targets"], len(raw) - 1)
            self.assertEqual(len(result["target_nll_nats"]), len(raw) - 1)
        self.assertEqual(report["experts"]["mixture"], report["experts"]["count"])
        self.assertAlmostEqual(report["experts"]["neural"]["nll_nats_per_byte"], math.log(256), places=14)

    def test_model_training_mode_restored_after_invalid_logits(self):
        from singularity.training.byte_experts import score_frozen_mixture

        class WrongModel(torch.nn.Module):
            def forward(self, inputs):
                return torch.zeros((*inputs.shape, 255))

        model = WrongModel()
        model.train()
        with self.assertRaises(ValueError):
            score_frozen_mixture(model, CountByteExpert.fit(b"ABCD", sequence_length=3), b"ABC", .5)
        self.assertTrue(model.training)


if __name__ == "__main__":
    unittest.main()
