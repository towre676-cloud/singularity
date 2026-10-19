"""The optional experiment CLI remains discoverable without PyTorch."""
import os
from pathlib import Path
import subprocess
import sys
import unittest


class TrainingCliTests(unittest.TestCase):
    def invoke_without_torch(self, arguments):
        source = Path(__file__).resolve().parents[1] / "src"
        script = """
import importlib.abc
import runpy
import sys

class MissingTorch(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "torch" or fullname.startswith("torch."):
            raise ModuleNotFoundError("PyTorch deliberately unavailable", name="torch")

sys.meta_path.insert(0, MissingTorch())
sys.argv = ["singularity-train", *sys.argv[1:]]
runpy.run_module("singularity.training.cli", run_name="__main__")
"""
        environment = dict(os.environ, PYTHONPATH=str(source))
        return subprocess.run(
            [sys.executable, "-c", script, *arguments],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )

    def test_help_works_without_optional_framework(self):
        result = self.invoke_without_torch(["--help"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--config", result.stdout)
        self.assertIn("--output", result.stdout)
        self.assertNotIn("PyTorch deliberately unavailable", result.stderr)

    def test_training_reports_optional_dependency(self):
        result = self.invoke_without_torch(
            ["--config", "unused.json", "--output", "unused"]
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("training requires PyTorch", result.stderr)
        self.assertIn('pip install -e ".[training]"', result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
