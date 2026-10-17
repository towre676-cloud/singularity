"""Acceptance gates and integrity checks for the transferable research package."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("handoff_tools", ROOT / "scripts/handoff.py")
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


class HandoffTests(unittest.TestCase):
    def test_all_original_pushes_and_evidence_are_present(self):
        self.assertEqual(handoff.verify_handoff()["pushes"], 36)
        self.assertEqual(handoff.validate_ledger(handoff.read_ledger()), [])

    def test_dependency_acceptance_not_implementation_controls_readiness(self):
        ledger = {"pushes": [
            {"id": "P01", "status": "partial", "dependencies": [], "priority": 0},
            {"id": "P02", "status": "partial", "dependencies": ["P01"], "priority": 0},
            {"id": "P03", "status": "partial", "dependencies": ["P01", "P02"], "priority": 0},
            {"id": "P07", "status": "planned", "dependencies": ["P01"], "priority": 1},
        ]}
        first = handoff.next_pushes(ledger, 36)
        self.assertEqual([p["id"] for p in first], ["P01"])
        ledger["pushes"][0]["status"] = "implemented_pending_acceptance"
        self.assertEqual([p["id"] for p in handoff.next_pushes(ledger, 36)], ["P01"])
        ledger["pushes"][0]["status"] = "complete"
        ready = [p["id"] for p in handoff.next_pushes(ledger, 36)]
        self.assertIn("P02", ready)
        self.assertIn("P07", ready)
        self.assertNotIn("P03", ready)

    def test_cycles_and_unaccepted_completion_are_rejected(self):
        ledger = copy.deepcopy(handoff.read_ledger())
        ledger["pushes"][0]["dependencies"] = ["P03"]
        self.assertTrue(any("cycle" in e for e in handoff.validate_ledger(ledger)))
        ledger = copy.deepcopy(handoff.read_ledger())
        ledger["pushes"][0]["status"] = "partial"
        ledger["pushes"][1]["status"] = "complete"
        ledger["pushes"][1]["acceptance_gaps"] = []
        self.assertTrue(any("unaccepted dependencies" in e for e in handoff.validate_ledger(ledger)))

    def test_malformed_ledger_is_a_diagnostic(self):
        self.assertTrue(handoff.validate_ledger([]))
        ledger = copy.deepcopy(handoff.read_ledger())
        ledger["pushes"][0]["dependencies"] = None
        self.assertTrue(any("list of strings" in e for e in handoff.validate_ledger(ledger)))

    def test_archive_tampering_and_extra_files_are_rejected(self):
        name = "singularity-handoff/repository/example.txt"
        original = b"exact source\n"
        manifest = {
            "schema": "singularity.claude-handoff/1",
            "source_commit": "0" * 40,
            "files": [{"path": name, "bytes": len(original), "sha256": hashlib.sha256(original).hexdigest()}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.zip"
            for data, extra, should_pass in [(original, False, True), (b"altered data\n", False, False), (original, True, False)]:
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr(name, data)
                    archive.writestr("singularity-handoff/MANIFEST.json", json.dumps(manifest))
                    if extra:
                        archive.writestr("singularity-handoff/undeclared.txt", "extra")
                if should_pass:
                    self.assertEqual(handoff.verify_archive(path)["status"], "passed")
                else:
                    with self.assertRaises(ValueError):
                        handoff.verify_archive(path)

    def test_unsafe_archive_paths_are_rejected_before_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unsafe.zip"
            for name in ("../outside.txt", "/absolute.txt", "folder\\outside.txt"):
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr(name, "unexpected")
                with self.assertRaisesRegex(ValueError, "Unsafe archive"):
                    handoff.verify_archive(path)


if __name__ == "__main__":
    unittest.main()
