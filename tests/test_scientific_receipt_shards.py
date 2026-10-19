"""Publication packaging must preserve exact original scientific receipts."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SHARD = load("shard_scientific_receipts", "scripts/shard_scientific_receipts.py")
RESTORE = load("materialize_for_shard_tests", "scripts/materialize_pretrained_evidence.py")


class ScientificReceiptShardTests(unittest.TestCase):
    def source(self, root, indent=1):
        value = {"schema": "a-scientific-receipt", "metadata": {"source": "public", "nothing": None},
                 "observations": {"fault": [{"ids": list(range(40)), "values": [i / 7 for i in range(40)]}
                                             for _ in range(6)], "empty": []},
                 "unicode": "caf\u00e9"}
        source = root / "nested" / "observations.json"
        source.parent.mkdir()
        source.write_bytes((json.dumps(value, indent=indent, sort_keys=True, allow_nan=False) + "\n").encode())
        return source

    def test_nested_lists_and_dicts_restore_both_supported_serializations_byte_exactly(self):
        for indent in (1, 2):
            with self.subTest(indent=indent), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = self.source(root, indent)
                original = source.read_bytes()
                report = SHARD.shard_receipt(source, results_root=root, max_shard_bytes=1024)
                self.assertEqual(source.read_bytes(), original)
                self.assertTrue(report["original_retained"])
                self.assertLessEqual(report["max_shard_bytes"], 1024)
                manifest = json.loads(Path(report["manifest"]).read_bytes())
                self.assertEqual(manifest["base"]["metadata"]["nothing"], None)
                self.assertTrue(any(any(isinstance(part, int) for part in entry["path"]) for entry in manifest["shards"]))
                source.unlink()
                self.assertEqual(RESTORE.restore_json_shards(root), ["nested/observations.json"])
                self.assertEqual(source.read_bytes(), original)

    def test_tampered_shard_is_rejected_by_existing_restorer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.source(root)
            report = SHARD.shard_receipt(source, results_root=root, max_shard_bytes=1024)
            manifest_path = Path(report["manifest"])
            entry = json.loads(manifest_path.read_bytes())["shards"][0]
            path = manifest_path.parent / entry["file"]
            path.write_bytes(path.read_bytes() + b" ")
            source.unlink()
            with self.assertRaisesRegex(ValueError, "differs from manifest"):
                RESTORE.restore_json_shards(root)
            self.assertFalse(source.exists())

    def test_idempotent_export_refuses_conflicting_existing_packaging(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self.source(root)
            first = SHARD.shard_receipt(source, results_root=root, max_shard_bytes=1024)
            self.assertEqual(first, SHARD.shard_receipt(source, results_root=root, max_shard_bytes=1024))
            with self.assertRaises(FileExistsError):
                SHARD.shard_receipt(source, results_root=root, max_shard_bytes=2048)

    def test_noncanonical_or_indivisibly_large_scalar_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "receipt.json"
            source.write_text('{"a":1}')
            with self.assertRaisesRegex(ValueError, "canonical"):
                SHARD.shard_receipt(source)
            source.write_bytes((json.dumps({"large": "x" * 2000}, indent=1, sort_keys=True) + "\n").encode())
            with self.assertRaisesRegex(ValueError, "scalar subtree exceeds"):
                SHARD.shard_receipt(source, max_shard_bytes=1024, max_manifest_bytes=1024)
            self.assertFalse(source.with_name("receipt.shards").exists())


if __name__ == "__main__":
    unittest.main()
