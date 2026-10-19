"""Saved-artifact checker rejects changed and nonlocal manifest entries."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_deployment_package", ROOT / "scripts/check_deployment_package.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class DeploymentArtifactCheckerTests(unittest.TestCase):
    def test_hash_validation_accepts_original_and_rejects_changed_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "graph.pt").write_bytes(b"original graph")
            files = {"graph.pt": {"bytes": 14, "sha256": CHECK.file_digest(path / "graph.pt")}}
            receipt = {"artifacts": files, "artifact_manifest_sha256": CHECK.digest(files)}
            CHECK.validate_artifact_files(path, receipt)
            (path / "graph.pt").write_bytes(b"replaced graph")
            with self.assertRaisesRegex(ValueError, "artifact file changed"):
                CHECK.validate_artifact_files(path, receipt)

    def test_receipt_paths_and_digest_are_checked_before_loading(self):
        files = {"../outside.pt": {"bytes": 0, "sha256": "unused"}}
        with self.assertRaisesRegex(ValueError, "nonlocal path"):
            CHECK.validate_artifact_files(Path("."), {"artifacts": files, "artifact_manifest_sha256": CHECK.digest(files)})
        with self.assertRaisesRegex(ValueError, "manifest digest"):
            CHECK.validate_artifact_files(Path("."), {"artifacts": files, "artifact_manifest_sha256": "changed"})

    def test_outside_int8_extent_is_measurement_only_even_without_observed_drift(self):
        for verdict in ("unchanged", "changed"):
            report = {"verdict": verdict, "contract_mismatches": [], "interpretation": "original"}
            CHECK.annotate_envelope(report, "dynamic_int8", 3, 0)
            self.assertEqual(report["verdict"], verdict)
            self.assertEqual(report["deployment_status"], "outside_calibration")
            self.assertEqual(report["exit_code"], 3)
            self.assertIn("does not classify", report["interpretation"])

    def test_contract_mismatch_overrides_outside_extent_and_in_envelope_drift_is_changed(self):
        report = {"verdict": "changed", "contract_mismatches": [{"key": "tokenizer"}], "interpretation": "original"}
        CHECK.annotate_envelope(report, "dynamic_int8", 3, 2)
        self.assertEqual(report["deployment_status"], "contract_mismatch")
        self.assertEqual(report["exit_code"], 2)

    def test_sdpa_is_outside_the_eager_int8_contract_even_at_batch_one(self):
        report = {"verdict": "unchanged", "contract_mismatches": [], "interpretation": "original"}
        CHECK.annotate_envelope(report, "dynamic_int8", 1, 0, backend="sdpa",
                               approved={"attention_backends": ["eager"], "batch_size": 1, "cache_execution": "full prefill"})
        self.assertEqual(report["deployment_status"], "outside_calibration")
        self.assertEqual(report["exit_code"], 3)

    def test_losing_all_coverage_is_inconclusive_but_does_not_hide_a_positive_flag(self):
        report = {"verdict": "unchanged", "contract_mismatches": [], "construction_faults_still_separated": {"fault": False}}
        CHECK.annotate_envelope(report, "float32", 1, 0)
        self.assertEqual(report["deployment_status"], "inconclusive_missing_results")
        self.assertEqual(report["exit_code"], 4)
        report["verdict"] = "changed"
        CHECK.annotate_envelope(report, "float32", 1, 0)
        self.assertEqual(report["deployment_status"], "behavioral_change")
        self.assertEqual(report["exit_code"], 2)
        report = {"verdict": "changed", "contract_mismatches": [], "interpretation": "original"}
        CHECK.annotate_envelope(report, "dynamic_int8", 1, 0)
        self.assertEqual(report["deployment_status"], "behavioral_change")
        self.assertEqual(report["exit_code"], 2)


if __name__ == "__main__":
    unittest.main()
