"""Pretrained benchmark target alignment, causal adaptation and evidence replay."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pretrained_prediction_for_tests", ROOT / "scripts/confirm_pretrained_prediction.py")
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class WindowPlanTests(unittest.TestCase):
    def test_every_target_once_and_correct_logits_row(self):
        for size in (2, 17, 257, 258, 385, 513, 1025):
            scored = []
            for row in benchmark.window_plan(size, 256, 128):
                self.assertLessEqual(row["input_stop"] - row["input_start"], 256)
                self.assertEqual(row["score_stop"] - row["score_start"], row["target_stop"] - row["target_start"])
                for local, target in zip(range(row["score_start"], row["score_stop"]),
                                         range(row["target_start"], row["target_stop"])):
                    self.assertEqual(row["input_start"] + local + 1, target)
                    scored.append(target)
            self.assertEqual(scored, list(range(1, size)))

    def test_invalid_plan(self):
        with self.assertRaises(ValueError):
            list(benchmark.window_plan(1))
        with self.assertRaises(ValueError):
            list(benchmark.window_plan(5, 4, 5))


@unittest.skipUnless(importlib.util.find_spec("torch") and importlib.util.find_spec("numpy"), "optional Torch/NumPy unavailable")
class PretrainedPredictionTests(unittest.TestCase):
    def test_manual_teacher_forcing_and_future_targets(self):
        import math
        from types import SimpleNamespace
        import numpy as np
        import torch

        class CausalToy:
            def __call__(self, input_ids, **kwargs):
                total = input_ids.cumsum(1).to(torch.float64)
                logits = torch.stack([torch.sin(total + k) for k in range(7)], dim=-1)
                return SimpleNamespace(logits=logits)

        tokens = [1, 3, 1, 3, 1, 3, 1, 2, 5, 4, 1, 1, 3]
        first = benchmark.score_document(CausalToy(), tokens, 7, 6, 3)
        expected = []
        for window in benchmark.window_plan(len(tokens), 6, 3):
            prefix = tokens[window["input_start"]:window["input_stop"]]
            for local, target in zip(range(window["score_start"], window["score_stop"]),
                                     tokens[window["target_start"]:window["target_stop"]]):
                logits = [math.sin(sum(prefix[:local + 1]) + k) for k in range(7)]
                expected.append(math.log(math.fsum(math.exp(v) for v in logits)) - logits[target])
        np.testing.assert_allclose([float.fromhex(v) for v in first["losses_hex"]["neural"]], expected, rtol=0, atol=1e-14)
        second = benchmark.score_document(CausalToy(), tokens[:8] + [6, 6, 6, 6, 6], 7, 6, 3)
        for arm in benchmark.ARMS:
            self.assertEqual(first["losses_hex"][arm][:7], second["losses_hex"][arm][:7])
        for arm in ("online_blend", "online_neural_backed"):
            self.assertEqual(first["prior_to_target_count_weights_hex"][arm][:8],
                             second["prior_to_target_count_weights_hex"][arm][:8])
            self.assertGreaterEqual(first["online_audits"][arm]["bound_slack_nats"], -1e-9)
        benchmark.validate_trace(first)

    def test_real_local_gpt2_and_loss_trace_validation(self):
        if not importlib.util.find_spec("transformers"):
            self.skipTest("optional Transformers unavailable")
        import torch
        from transformers import GPT2Config, GPT2LMHeadModel

        torch.manual_seed(39)
        model = GPT2LMHeadModel(GPT2Config(vocab_size=13, n_positions=16, n_embd=16, n_layer=1, n_head=2))
        model.eval()
        tokens = [1, 5, 2, 5, 2, 5, 2, 9, 8, 7, 1, 2, 3, 4, 5, 6, 7]
        record = benchmark.score_document(model, tokens, 13, 8, 4)
        benchmark.validate_trace(record)
        mutated = benchmark.score_document(model, tokens[:7] + [12] * 10, 13, 8, 4)
        for arm in benchmark.ARMS:
            self.assertEqual(record["losses_hex"][arm][:6], mutated["losses_hex"][arm][:6])
        record["losses_hex"]["neural"][0] = float(1).hex()
        with self.assertRaises(ValueError):
            benchmark.validate_trace(record)


if __name__ == "__main__":
    unittest.main()
