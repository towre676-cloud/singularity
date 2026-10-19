"""Version-2 deployment audit: calibration envelope, numerical health, candidates."""
import argparse
import importlib.util
import json
import math
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

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/colab_deployment_audit_v2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("deployment_audit_v2", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def observation(continuation, logprobs, argmax=(1, 2), gap=(1., 1.)):
    return {"argmax": list(argmax), "top_logprob": [-.1, -.2], "top_gap": list(gap), "entropy": [.5, .5],
            "continuation": list(continuation), "continuation_logprob": list(logprobs)}


class StabilizationTests(unittest.TestCase):
    def setUp(self):
        self.audit = load_module()

    def test_continuations_are_compared_on_the_prefix_shared_with_calibration(self):
        reference = [observation([5, 6, 7, 8], [-1., -1., -1., -1.])]
        uncached = [observation([5, 6, 9, 9], [-1.001, -1.0, -2., -2.])]
        stable, ties, prefixes = self.audit.stabilize(reference, [uncached], .02)
        self.assertEqual(prefixes, {0: 2})
        self.assertEqual(stable[0]["continuation"], [5, 6])
        shown = self.audit.view(observation([5, 6, 1, 1], [-1., -1., -5., -5.]), stable[0])
        self.assertEqual(shown["continuation"], [5, 6])
        self.assertEqual(len(shown["continuation_logprob"]), 2)
        # A changed first token is still visible after stabilization.
        self.assertEqual(self.audit.view(observation([4, 6, 7, 8], [-1.] * 4), stable[0])["continuation"], [4, 6])

    def test_disagreement_on_the_first_token_removes_the_continuation(self):
        reference = [observation([5, 6], [-1., -1.])]
        stable, _, prefixes = self.audit.stabilize(reference, [[observation([4, 6], [-1., -1.])]], .02)
        self.assertEqual(prefixes, {0: 0})
        self.assertNotIn("continuation", stable[0])
        self.assertNotIn("continuation", self.audit.view(observation([5, 6], [-1., -1.]), stable[0]))

    def test_calibration_argmax_flips_become_ties(self):
        reference = [observation([], [], argmax=(1, 2), gap=(.5, .5))]
        stable, ties, _ = self.audit.stabilize(reference, [[observation([], [], argmax=(1, 3))]], .02)
        self.assertEqual((ties, stable[0]["top_gap"]), (1, [.5, 0.]))

    def test_nonfinite_values_are_counted_per_probe_and_made_to_flag(self):
        rows = [observation([1], [math.nan]), observation([1], [-1.])]
        rows[0]["entropy"][0] = math.inf
        self.assertEqual(self.audit.nonfinite_by_probe(rows), [2, 0])
        self.assertTrue(all(math.isfinite(v) for v in rows[0]["entropy"] + rows[0]["continuation_logprob"]))


@unittest.skipIf(torch is None or transformers is None, "optional transformers unavailable")
class VersionTwoRunTests(unittest.TestCase):
    def run_local(self, directory, poison):
        audit = load_module()
        original = audit.run_change

        def patched(deployment, probes, change):
            rows = original(deployment, probes, change)
            if rows is not None and poison(change):
                rows[0]["top_logprob"][0] = math.nan
            return rows

        audit.run_change = patched
        args = argparse.Namespace(local_test=True, model=None, skip_cold=True)
        output = Path(directory) / "out"
        audit.freeze(args, output)
        return audit, output, args

    def test_nonfinite_candidate_is_not_approved_and_reported_as_health_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            audit, output, args = self.run_local(directory, lambda change: change.get("attention") == "eager")
            results = audit.run(args, output)
            candidate = results["candidates"]["eager_attention"]
            self.assertEqual(candidate["status"], "not_approved_numerical_health_failure")
            self.assertEqual(candidate["nonfinite_values"], 1)
            self.assertIn("candidate/eager_attention", results["numerical_health_failures"])
            self.assertEqual(results["panels"]["exact"]["false_alarms"], [])
            self.assertTrue(results["package"]["verification"]["verified"])
            self.assertEqual(results["variant_status"]["prefix_token_injected"], "new_in_v2")
            self.assertEqual(results["variant_status"]["crlf_newlines"], "retest_from_v1")

    def test_nonfinite_calibration_aborts_instead_of_widening_tolerances(self):
        with tempfile.TemporaryDirectory() as directory:
            audit, output, args = self.run_local(directory, lambda change: change.get("use_cache") is False)
            with self.assertRaises(audit.NumericalHealthFailure):
                audit.run(args, output)
            status = json.loads((output / "results.json").read_text())
            self.assertEqual(status["status"], "numerical_health_failure")
            self.assertEqual(status["failed_run"], "calibration/uncached_batch_size_1")

    def test_command_line_run_completes_and_refuses_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "out"
            command = [sys.executable, str(SCRIPT), "--local-test", "--skip-cold", "--output", str(output)]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=900)
            self.assertEqual(completed.returncode, 0, completed.stderr[-3000:])
            protocol = json.loads((output / "protocol.json").read_text())
            results = json.loads((output / "results.json").read_text())
            self.assertEqual((protocol["version"], results["status"]), (2, "completed"))
            self.assertEqual(set(protocol["calibration_clean_runs"]) & set(protocol["validation_clean_runs"]), set())
            exact = results["panels"]["exact"]
            self.assertEqual(exact["cost"], results["independent_enumeration"]["minimum_cost"])
            self.assertLessEqual(exact["cost"], results["panels"]["pruned_greedy"]["cost"])
            again = subprocess.run(command, capture_output=True, text=True, timeout=300)
            self.assertIn("already exists", again.stderr)


if __name__ == "__main__":
    unittest.main()
