"""Pretrained benchmark contracts, independent oracle and honest scope."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("confirm_pretrained_audit", ROOT / "scripts/confirm_pretrained_audit.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class CharacterTokenizer:
    def __call__(self, text, add_special_tokens):
        if add_special_tokens:
            raise AssertionError("benchmark tokenization must not insert special tokens")
        return {"input_ids": list(text.encode("utf-8"))}


class PretrainedProtocolTests(unittest.TestCase):
    def test_fixed_pool_costs_exactly_match_truncation_and_padding(self):
        probes = AUDIT.probes_for(CharacterTokenizer())
        self.assertEqual(len(probes), 18)
        self.assertEqual(len({p["id"] for p in probes}), 18)
        for probe in probes:
            tokens = list(probe["text"].encode("utf-8"))[-AUDIT.MAX_CONTEXT:]
            self.assertEqual(probe["cost"], max(len(tokens), probe.get("pad_to", 0)))
            self.assertLessEqual(probe["cost"], AUDIT.MAX_CONTEXT)
        self.assertGreaterEqual(sum(p["cost"] > 64 for p in probes), 2)

    def test_position_translation_is_held_out_and_no_detection_is_assumed(self):
        self.assertIn("position_ids_all_zero", AUDIT.CONSTRUCTION_FAULTS)
        self.assertNotIn("left_pad_absolute_positions", AUDIT.CONSTRUCTION_FAULTS)
        self.assertIn("left_pad_absolute_positions", AUDIT.HELDOUT_FAULTS)
        self.assertEqual(AUDIT.PROTOCOL["requirement"], 2)
        self.assertEqual(AUDIT.PROTOCOL["timing"]["pairs"], 3)

    def test_independent_enumeration_matches_hand_checked_minimum(self):
        rows = [[True, True], [True, False], [False, True], [True, True]]
        result = AUDIT.independent_minimum(rows, [4, 1, 1, 3])
        self.assertEqual(result["minimum_cost"], 5)
        self.assertEqual(result["minimizing_panels"], [[1, 2, 3]])
        self.assertEqual(result["subsets"], 16)

    def test_undercovered_faults_remain_reported_and_never_receive_guarantee(self):
        probes = [{"id": f"p{i}", "cost": c} for i, c in enumerate([4, 1, 1, 3])]
        flags = {"a": [True, True, False, True], "b": [True, False, True, True],
                 "invariant": [False, False, False, False], "one_only": [True, False, False, False]}
        result = AUDIT.select_panel(probes, flags)
        self.assertEqual(result["eligible_faults"], ["a", "b"])
        self.assertEqual(result["unavailable_faults"], {"invariant": 0, "one_only": 1})
        self.assertEqual(result["exact"]["cost"], 5)
        self.assertEqual(result["independent_enumeration"]["minimum_cost"], 5)
        with self.assertRaises(ValueError):
            AUDIT.select_panel(probes, {"invariant": [False] * 4})

    def test_snapshot_hashes_weights_and_tokenizer_but_ignores_download_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "model.safetensors").write_bytes(b"weights")
            (path / "tokenizer.json").write_text('{"vocabulary":{}}')
            (path / ".cache").mkdir()
            (path / ".cache" / "bookkeeping.json").write_text("{}")
            manifest = AUDIT.snapshot_manifest(path)
            self.assertEqual(set(manifest), {"model.safetensors", "tokenizer.json"})
            before = AUDIT.digest(manifest)
            (path / "model.safetensors").write_bytes(b"changed")
            self.assertNotEqual(before, AUDIT.digest(AUDIT.snapshot_manifest(path)))


if __name__ == "__main__":
    unittest.main()
