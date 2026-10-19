"""A backend-envelope repair cannot change tolerances or selection targets."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("confirm_int8_contract", ROOT / "scripts/confirm_int8_contract.py")
CONTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACT)


class Int8ContractProfileTests(unittest.TestCase):
    def test_repair_preserves_scientific_problem_and_records_post_calibration_origin(self):
        value = CONTRACT.repaired_protocol("parent-hash", "failure-hash")
        original = CONTRACT.BASE_PROTOCOL
        for key in ("pool", "construction_faults", "heldout_faults", "tolerance", "selection", "timing", "reference"):
            self.assertEqual(value[key], original[key])
        self.assertIn("POST-CALIBRATION", value["status"])
        self.assertEqual(value["parent_protocol_file_sha256"], "parent-hash")
        self.assertEqual(value["parent_calibration_failure_file_sha256"], "failure-hash")
        self.assertEqual(value["approved_int8_execution"]["attention_backends"], ["eager"])
        self.assertEqual(original["calibration"]["dynamic_int8"][0]["attention_backend"], "sdpa")

    def test_backend_moves_to_independent_transfer_without_widening_tolerances(self):
        value = CONTRACT.repaired_protocol("parent", "failure")
        controls = value["calibration"]["dynamic_int8"]
        self.assertEqual([c["threads"] for c in controls], [1, 2])
        self.assertTrue(all(c["attention_backend"] == "eager" and c["batch_size"] == 1 for c in controls))
        self.assertEqual(value["clean_heldout"]["sdpa_batch1_threads2_reverse"]["attention_backend"], "sdpa")
        self.assertEqual(value["tolerance"], {"factor": 4., "floor": 1e-5, "tie_margin": 1e-3})

    def test_package_metadata_carries_the_approved_contract_before_checks(self):
        value = CONTRACT.repaired_protocol("parent", "failure")
        metadata = CONTRACT.envelope_metadata(value)
        self.assertTrue(metadata["post_calibration_refinement"])
        self.assertEqual(metadata["original_failure_file_sha256"], "failure")
        self.assertEqual(metadata["calibration_envelope"], {"attention_backends": ["eager"], "batch_size": 1, "cache_execution": "full prefill"})


if __name__ == "__main__":
    unittest.main()
