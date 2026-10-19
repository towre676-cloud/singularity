"""Executable export shape/value behavior, checked on tiny random weights."""
from pathlib import Path
import tempfile
import unittest

try:
    import torch
    from transformers import LlamaConfig, LlamaForCausalLM
except ImportError:
    torch = None

from singularity.model_audit.exported import export_causal_graph, load_causal_graph


@unittest.skipIf(torch is None, "requires optional torch and transformers")
class ExportedCausalGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        torch.manual_seed(77213)
        config = LlamaConfig(vocab_size=37, hidden_size=16, intermediate_size=32,
                             num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=1,
                             max_position_embeddings=32, use_cache=False, tie_word_embeddings=True)
        config._attn_implementation = "eager"
        cls.model = LlamaForCausalLM(config).eval()
        cls.temporary = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temporary.name) / "causal.pt"
        cls.manifest = export_causal_graph(cls.model, cls.path, max_context=16, max_batch_size=3)
        cls.graph = load_causal_graph(cls.path, cls.manifest)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()
        torch.set_num_threads(cls.old_threads)

    def inputs(self, batch, width):
        ids = torch.randint(0, 37, (batch, width), dtype=torch.long)
        mask = torch.ones_like(ids)
        if width > 2:
            mask[0, :2] = 0
        positions = mask.cumsum(-1).sub(1).clamp(min=0)
        return ids, mask, positions

    def test_reloaded_graph_matches_native_eager_across_values_shapes_and_padding(self):
        with torch.inference_mode():
            for batch, width in ((1, 1), (1, 3), (2, 5), (3, 7), (2, 11), (3, 16)):
                for repeat in range(2):
                    ids, mask, positions = self.inputs(batch, width)
                    expected = self.model(input_ids=ids, attention_mask=mask, position_ids=positions,
                                          use_cache=False).logits
                    actual = self.graph(ids, mask, positions)
                    torch.testing.assert_close(actual, expected, rtol=1e-6, atol=1e-7)
                    self.assertEqual(actual.shape, (batch, width, 37))

    def test_mask_and_position_values_remain_dynamic(self):
        ids, mask, positions = self.inputs(2, 7)
        with torch.inference_mode():
            for selected_mask, selected_positions in ((torch.ones_like(mask), positions),
                                                      (mask, torch.zeros_like(positions))):
                expected = self.model(input_ids=ids, attention_mask=selected_mask,
                                      position_ids=selected_positions, use_cache=False).logits
                torch.testing.assert_close(self.graph(ids, selected_mask, selected_positions), expected)
            torch.testing.assert_close(self.graph(ids, None, positions),
                                       self.graph(ids, torch.ones_like(mask), positions))

    def test_causal_prefix_does_not_depend_on_future_token_values(self):
        ids, mask, positions = self.inputs(2, 11)
        changed = ids.clone()
        changed[:, 6:] = (changed[:, 6:] + 1) % 37
        with torch.inference_mode():
            # Fully masked padding queries use HF's finite-min mask convention
            # and are excluded from audit observations. Real causal positions
            # cannot depend on future tokens.
            real = mask[:, :6].bool()
            torch.testing.assert_close(self.graph(ids, mask, positions)[:, :6][real],
                                       self.graph(changed, mask, positions)[:, :6][real])

    def test_bounds_types_and_vocabulary_are_enforced_outside_graph(self):
        ids, mask, positions = self.inputs(1, 7)
        bad = [(ids.float(), mask, positions), (ids, mask[:, :-1], positions),
               (ids, mask + 2, positions), (ids + 37, mask, positions),
               (ids, mask, positions + 16), self.inputs(4, 7), self.inputs(1, 17)]
        for values in bad:
            with self.assertRaises(ValueError):
                self.graph(*values)

    def test_tampered_artifact_is_rejected_before_loading(self):
        changed = Path(self.temporary.name) / "tampered.pt"
        changed.write_bytes(self.path.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "does not match"):
            load_causal_graph(changed, self.manifest)

    def test_export_rejects_stale_path_training_and_out_of_scope_configuration(self):
        with self.assertRaises(FileExistsError):
            export_causal_graph(self.model, self.path, max_context=16)
        self.model.train()
        try:
            with self.assertRaisesRegex(ValueError, "eval"):
                export_causal_graph(self.model, Path(self.temporary.name) / "training.pt", max_context=16)
        finally:
            self.model.eval()
        with self.assertRaises(ValueError):
            export_causal_graph(self.model, Path(self.temporary.name) / "too-wide.pt", max_context=33)


if __name__ == "__main__":
    unittest.main()
