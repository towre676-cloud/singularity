"""Model-free independent reconstruction of the deployment confirmation."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("independent_deployment_evidence", ROOT / "scripts/verify_deployment_confirmation.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class DeploymentEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directories = sorted({path.parent for name in ("results.json", "calibration_failure.json")
                                  for path in VERIFY.DEFAULT.glob("**/" + name)})
        cls.completed = [path for path in cls.directories if (path / "results.json").exists()]
        if not cls.directories:
            raise AssertionError("required deployment confirmation evidence is missing")

    def test_population_has_float_and_real_int8_targets(self):
        targets = {VERIFY.read(path / "protocol.json")["target"] for path in self.directories}
        self.assertGreaterEqual(len(self.directories), 2)
        self.assertTrue({"float32", "dynamic_int8"} <= targets)

    def test_independent_full_replay(self):
        for directory in self.directories:
            with self.subTest(evidence=directory.name):
                self.assertTrue(VERIFY.verify_directory(directory)["verified"])

    def test_rejects_forged_kernel_execution(self):
        if not self.completed:
            self.skipTest("all declared targets failed clean calibration; no kernel receipts claimed")
        directory = self.completed[0]
        frozen, result = VERIFY.read(directory / "protocol.json"), VERIFY.read(directory / "results.json")
        forged = copy.deepcopy(result)
        sdpa = next(row for row in forged["execution_receipts"] if row["attention_backend"] == "sdpa")
        sdpa["sdpa_calls"] = 0
        with self.assertRaisesRegex(ValueError, "kernel not proved"):
            VERIFY.verify_execution(frozen, forged)

    def test_rejects_forged_speed_ratio(self):
        if not self.completed:
            self.skipTest("all declared targets failed clean calibration; no speed claim")
        directory = self.completed[0]
        frozen, result = VERIFY.read(directory / "protocol.json"), VERIFY.read(directory / "results.json")
        forged = copy.deepcopy(result)
        forged["timing"]["amortization"]["exact"]["full_pool_over_panel"] += .1
        with self.assertRaisesRegex(ValueError, "speed ratio differs"):
            VERIFY.verify_timing(frozen, forged)

    def test_contract_refinement_cannot_widen_frozen_numerical_tolerance(self):
        refinements = [path for path in self.completed
                       if "parent_calibration_failure_file_sha256" in VERIFY.read(path / "protocol.json")["protocol"]]
        if not refinements:
            self.skipTest("no completed post-calibration contract refinement")
        directory = refinements[0]
        frozen, result = VERIFY.read(directory / "protocol.json"), VERIFY.read(directory / "results.json")
        forged = copy.deepcopy(frozen)
        forged["protocol"]["tolerance"]["floor"] *= 100
        with self.assertRaisesRegex(ValueError, "changed fixed scientific setting: tolerance"):
            VERIFY.verify_refinement(directory, forged, result)

    def test_rejects_modified_shard_bytes(self):
        if not self.completed:
            self.skipTest("all declared targets failed clean calibration; no completed observation shards")
        directory = self.completed[0]
        manifest = VERIFY.read(directory / "observations_manifest.json")
        first = manifest["entries"][0]
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            shard = target / first["file"]
            shard.parent.mkdir(parents=True)
            shard.write_bytes((directory / first["file"]).read_bytes() + b" ")
            (target / "observations_manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "shard bytes differ"):
                VERIFY.load_observations(target)


if __name__ == "__main__":
    unittest.main()
