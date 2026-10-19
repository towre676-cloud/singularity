"""CPU smoke test of the GPU deployment-audit script with a tiny random Qwen2."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    import torch
    import transformers
except ImportError:
    torch = transformers = None

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/colab_deployment_audit.py"


@unittest.skipIf(torch is None or transformers is None, "optional transformers unavailable")
class ColabDeploymentAuditSmoke(unittest.TestCase):
    def test_frozen_local_run_selects_verifies_and_refuses_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "out"
            command = [sys.executable, str(SCRIPT), "--local-test", "--skip-cold", "--output", str(output)]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=900)
            self.assertEqual(completed.returncode, 0, completed.stderr[-3000:])
            protocol = json.loads((output / "protocol.json").read_text())
            results = json.loads((output / "results.json").read_text())
            self.assertEqual(results["protocol_sha256"], protocol["protocol_sha256"])
            self.assertTrue(results["package"]["verification"]["verified"])
            exact = results["panels"]["exact"]
            self.assertEqual(exact["cost"], results["independent_enumeration"]["minimum_cost"])
            self.assertLessEqual(exact["cost"], results["panels"]["pruned_greedy"]["cost"])
            self.assertLessEqual(results["panels"]["pruned_greedy"]["cost"], results["panels"]["greedy"]["cost"])
            self.assertEqual(exact["construction_robust"], len(results["coverable"]))
            self.assertEqual(set(results["skipped_variants"]), {"int8_bitsandbytes", "nf4_4bit_bitsandbytes"})
            again = subprocess.run(command, capture_output=True, text=True, timeout=300)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("already exists", again.stderr)


if __name__ == "__main__":
    unittest.main()
