"""Contracts for exact deployed-checkpoint smoke-test panels."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("checkpoint_panels", ROOT / "scripts/confirm_checkpoint_panels.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
import sys
sys.path.insert(0, str(ROOT / "scripts"))
import check_checkpoint_smoke as consumer
try:
    import torch
except ImportError:
    torch = None


class ExactPanelContracts(unittest.TestCase):
    def test_byte_sequence_encoding_keeps_leading_zero_and_length(self):
        self.assertNotEqual(study.exact_reading([0, 1]), study.exact_reading([1]))
        self.assertNotEqual(study.exact_reading([0]), study.exact_reading([]))
        self.assertEqual(study.exact_reading([0, 255]), int.from_bytes(b"\x01\x00\xff", "big"))

    def test_minimum_panel_quotients_duplicate_complete_signatures(self):
        rows = [[0, 1, 0, 0], [0, 0, 1, 0], [0, 1, 2, 0]]
        result = study.minimum_plan(rows, [1, 1, 3])
        self.assertEqual(result["selected_blocks"], [0, 1])
        self.assertEqual(result["selected_cost_input_tokens"], 2)
        self.assertEqual(result["signature_classes"], [[0, 3], [1], [2]])
        self.assertEqual(result["independent_subsets_checked"], 8)
        self.assertEqual(result["independent_minimum_cost_input_tokens"], 2)

    def test_full_and_selected_pair_separation_reports_losses(self):
        rows = [[0, 1, 0], [0, 0, 1]]
        result = study.separation(rows, [0])
        self.assertEqual(result["full_distinct_pairs"], 3)
        self.assertEqual(result["selected_distinct_pairs"], 2)
        self.assertEqual(result["full_distinct_pairs_missed"], [[0, 2]])

    def test_consumer_selects_complete_blocks_and_reports_exact_changes(self):
        golden = bytes(range(256)) * 128
        selected = consumer.select_prediction_bytes(golden, [3])
        self.assertEqual(len(selected), 4096)
        self.assertEqual(selected, golden[12288:16384])
        self.assertTrue(consumer.compare_bytes(selected, selected)["unchanged"])
        changed = bytes([selected[0] ^ 1]) + selected[1:]
        report = consumer.compare_bytes(changed, selected)
        self.assertEqual(report["changed_prediction_count"], 1)
        self.assertEqual(report["changed_prediction_indices"], [0])
        with self.assertRaises(ValueError):
            consumer.select_prediction_bytes(golden, [1, 1])

    def test_interpolated_percentile(self):
        self.assertEqual(study.percentile([4, 1, 3, 2], .5), 2.5)
        self.assertAlmostEqual(study.percentile([4, 1, 3, 2], .9), 3.7)


@unittest.skipIf(torch is None, "optional PyTorch training dependencies not installed")
class CheckpointMutationContracts(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        from singularity.training.models import CausalTransformer
        torch.manual_seed(411)
        self.model = CausalTransformer(256, 64, d_model=8, heads=2, layers=2).eval()

    def test_clean_clone_is_independent_and_exact(self):
        clone = study.mutate_model(self.model, "clean_clone")
        for a, b in zip(self.model.parameters(), clone.parameters()):
            self.assertTrue(torch.equal(a, b))
            self.assertNotEqual(a.data_ptr(), b.data_ptr())
        x = torch.randint(256, (16, 64))
        self.assertTrue(torch.equal(study.predict(self.model, x), study.predict(clone, x)))

    def test_fake_quantization_changes_only_matrix_weights_and_not_base(self):
        baseline = {name: p.detach().clone() for name, p in self.model.named_parameters()}
        quantized = study.mutate_model(self.model, "quantize_4")
        changed = 0
        for name, p in quantized.named_parameters():
            self.assertTrue(torch.equal(dict(self.model.named_parameters())[name], baseline[name]))
            if p.ndim < 2:
                self.assertTrue(torch.equal(p, baseline[name]))
            else:
                changed += not torch.equal(p, baseline[name])
        self.assertGreater(changed, 0)

    def test_selected_contexts_are_complete_and_batch_independent(self):
        x = torch.randint(256, (48, 64))
        full = study.predict(self.model, x)
        small = study.predict(self.model, x[16:32])
        self.assertEqual(tuple(small.shape), (16, 64))
        self.assertTrue(torch.equal(full[16:32], small))

    def test_drop_and_position_variants_are_local(self):
        drop = study.mutate_model(self.model, "drop_layer_0")
        self.assertEqual(len(drop.body.layers), 1)
        self.assertEqual(len(self.model.body.layers), 2)
        pos = study.mutate_model(self.model, "no_position")
        self.assertEqual(int(pos.position.weight.count_nonzero()), 0)
        self.assertGreater(int(self.model.position.weight.count_nonzero()), 0)


if __name__ == "__main__":
    unittest.main()
