"""V3 quantified truncation coverage, independent optimality, and raw replay."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from singularity.model_audit.truncation import (threshold_intervals, specification, compare, certificate,
                                               verify_certificate, independent_optimum, digest)
from singularity.robust_coverage import coverage_problem, exhaustive_robust_panel

ROOT = Path(__file__).resolve().parents[1]

def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def probe(name, n, cost=None):
    return {"id": name, "tokens": n, "cost": n if cost is None else cost}


class ShapeFamilyTests(unittest.TestCase):
    def test_every_cap_is_represented_with_strict_real_length_boundary(self):
        lengths = [5, 10, 72, 76]
        intervals = threshold_intervals(lengths, 80)
        represented = []
        for interval in intervals:
            for cap in range(interval["first"], interval["last"] + 1):
                represented.append(cap)
                self.assertEqual(interval["separates"], [n > cap for n in lengths])
        self.assertEqual(represented, list(range(1, 81)))
        # These are actual v2 encoder semantics, not output-value assumptions.
        base = module("encoder_v3_test", "colab_deployment_audit_v2.py")
        tokenizer = lambda text, **kw: {"input_ids": list(range(int(text)))}
        for n in lengths:
            for cap in range(1, 81):
                got = base.encode(tokenizer, str(n), {"truncate_to": cap})
                self.assertEqual(len(got) != n, n > cap)

    def test_padding_generation_and_duplicate_probes_cannot_create_witnesses(self):
        pool = [probe("short", 5, 300), probe("long", 80)]
        outcome = compare(specification(pool, {"f": [True, True]}, 72))
        self.assertFalse(outcome["feasible"])
        self.assertTrue(any(n == 1 for k, n in outcome["deficient"].items() if k.startswith("shape/")))
        with self.assertRaises(ValueError):
            specification([probe("a", 8), probe("a", 9)], {}, 7)
        for x in [0, -1, True, 1.5]:
            with self.assertRaises(ValueError):
                threshold_intervals([5, 8], x)

    def test_unobservable_construction_is_never_silently_dropped(self):
        spec = specification([probe("a", 80), probe("b", 90)], {"invisible": [False, False]}, 72)
        result = compare(spec)
        self.assertFalse(result["feasible"])
        self.assertEqual(result["deficient"], {"construction/invisible": 0})
        self.assertTrue(verify_certificate(certificate(spec, result)))

    def test_exact_pruning_and_all_four_selectors_share_requirements(self):
        rng = random.Random(30017)
        for _ in range(24):
            pool = [probe(str(e), rng.randrange(2, 12), 12 + rng.randrange(9)) for e in range(7)]
            faults = {str(j): [rng.random() < .6 for _ in pool] for j in range(3)}
            spec = specification(pool, faults, 5)
            result = compare(spec, ["0", "1"])
            self.assertTrue(verify_certificate(certificate(spec, result)))
            columns = spec["columns"]
            problem = coverage_problem([p["cost"] for p in pool], [[v[e] for v in columns.values()] for e in range(len(pool))])
            oracle = exhaustive_robust_panel(problem, 2)
            self.assertEqual(result["feasible"], oracle.feasible)
            if result["feasible"]:
                p = result["panels"]
                self.assertEqual(p["exact"]["cost"], oracle.cost)
                self.assertLessEqual(p["exact"]["cost"], p["pruned_greedy"]["cost"])
                self.assertLessEqual(p["pruned_greedy"]["cost"], p["greedy"]["cost"])

    def test_rehashed_certificate_mutations_fail_independent_checks(self):
        spec = specification([probe("a", 8), probe("b", 9), probe("c", 10)], {"f": [True]*3}, 7)
        original = certificate(spec, compare(spec, ["a"]))
        for mutation in (lambda c: c["comparison"]["panels"]["exact"].update(cost=0),
                         lambda c: c["specification"]["columns"]["shape/caps_1_7"].__setitem__(0, False),
                         lambda c: c["comparison"]["panels"]["exact"]["indices"].append(0),
                         lambda c: c["specification"].update(observability="last token only"),
                         lambda c: c["comparison"]["panels"].pop("greedy")):
            tampered = copy.deepcopy(original)
            mutation(tampered)
            tampered["sha256"] = digest({k: v for k, v in tampered.items() if k != "sha256"})
            self.assertFalse(verify_certificate(tampered))

    def test_pruned_panel_must_be_a_subset_of_the_greedy_output(self):
        pool = [probe(str(e), 8, 10) for e in range(3)]
        spec = specification(pool, {"f": [True]*3}, 7)
        cert = certificate(spec, compare(spec))
        row = cert["comparison"]["panels"]["pruned_greedy"]
        row["indices"], row["probe_ids"] = [0, 2], ["0", "2"]
        cert["sha256"] = digest({k: v for k, v in cert.items() if k != "sha256"})
        self.assertFalse(verify_certificate(cert))

    def test_no_universal_guarantee_for_last_token_or_fabricated_shapes(self):
        from singularity.model_audit.core import deviation, flags
        # An observer may return the same final token despite losing context.
        expected = {"argmax": [7]}
        self.assertFalse(flags(deviation({"argmax": [7]}, expected), {}))
        # Even all-position outputs cannot expose a fault that fabricates them.
        expected = {"argmax": [7]*80}
        self.assertFalse(flags(deviation(copy.deepcopy(expected), expected), {}))


class RetrospectiveTests(unittest.TestCase):
    def test_source_bound_frontier_replay_and_v2_identity(self):
        m = module("retrospective_v3_test", "confirm_truncation_v3.py")
        before = {p.name: p.read_bytes() for p in m.SOURCE.iterdir() if p.is_file()}
        report = m.evaluate()
        retained = json.loads((m.OUTPUT / "results.json").read_text())
        self.assertEqual(report, retained)
        self.assertEqual(before, {p.name: p.read_bytes() for p in m.SOURCE.iterdir() if p.is_file()})
        self.assertEqual(report["two_witness_shape_frontier"], 71)
        panels = report["certificate"]["comparison"]["panels"]
        self.assertEqual([panels[k]["cost"] for k in ("exact", "pruned_greedy", "greedy", "representative")], [271, 271, 301, 286])
        self.assertFalse(panels["representative"]["satisfies_requirement"])
        self.assertEqual(report["extra_cost_at_two_witness_frontier"], 10)
        repair = report["conservative_72_design"]
        self.assertTrue(verify_certificate(repair))
        self.assertEqual(repair["comparison"]["panels"]["exact"]["cost"], 269)
        self.assertEqual(repair["comparison"]["panels"]["pruned_greedy"]["cost"], 269)
        projected = report["conservative_127_design"]
        self.assertTrue(verify_certificate(projected))
        self.assertEqual(projected["comparison"]["panels"]["exact"]["cost"], 379)
        self.assertEqual(projected["comparison"]["panels"]["pruned_greedy"]["cost"], 379)
        self.assertEqual(projected["comparison"]["panels"]["greedy"]["cost"], 557)
        self.assertEqual(projected["comparison"]["panels"]["representative_completed"]["cost"], 665)
        self.assertEqual(report["panel_replay"]["exact"]["known_72_retest_witnesses"], 2)
        self.assertFalse(report["panel_replay"]["exact"]["false_alarms"])
        self.assertEqual(report["panel_replay"]["exact"]["genuinely_new_heldout_evaluations"], 0)
        self.assertEqual([x["shape_changes"] for x in report["observed_72_signals"]], [True, False])


class RunnerContractTests(unittest.TestCase):
    def setUp(self):
        self.m = module("prospective_v3_test", "colab_deployment_audit_v3.py")

    def protocol(self):
        m = self.m
        pool = [dict(probe("a", 80), text="a"), dict(probe("b", 90), text="b")]
        protocol = {"schema": m.SCHEMA, "version": 3, "probes": pool, "model": "test-double", "local_test": False,
                    "maximum_cap": 72, "requirement": 2, "tolerance": m.base.TOLERANCE,
                    "code_sha256": m.bindings(), "frozen_at_utc": m.base.now(), "representative_ids": ["a", "b"],
                    "construction_variants": {"changed": {}}, "calibration_clean_runs": {"c": {}},
                    "known_v2_retests": {}, "family_implementation_checks": {"cap72": {"truncate_to": 72}},
                    "new_heldout_variants": {"novel": {"test_change": True}},
                    "validation_clean_runs": {"clean": {}}, "diagnostic_variants": {},
                    "candidate_configurations": {"bad": {"unhealthy": True}}, "claim_boundary": "test double, no model evidence"}
        protocol["protocol_sha256"] = m.base.sha(m.base.canonical(protocol))
        return protocol

    def test_full_phase_order_raw_replay_and_health_recount_without_gpu(self):
        m, protocol = self.m, self.protocol()
        class Deployment:
            def contract(self): return {"test_double": True}
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            m.write(out / "protocol.json", protocol)
            def observed(deployment, probes, change):
                frozen = (out / "frozen_panels.json").exists()
                # Construction call is the third capture (reference + calibration).
                observed.calls += 1
                is_construction = observed.calls == 3
                if observed.calls > 3:
                    self.assertTrue(frozen)
                else:
                    self.assertFalse(frozen)
                rows = []
                for p in probes:
                    n = min(p["tokens"], change.get("truncate_to", p["tokens"]))
                    rows.append({"argmax": [2 if is_construction or change.get("test_change") else 1]*n,
                                 "top_gap": [1.]*n, "top_logprob": [-1.]*n, "entropy": [.5]*n})
                if change.get("unhealthy"):
                    rows[0]["entropy"][0] = float("nan")
                return rows
            observed.calls = 0
            with patch.object(m.base, "deployment_for", return_value=Deployment()), patch.object(m, "capture", side_effect=observed):
                m.run(out)
            self.assertTrue(m.verify(out))
            result = json.loads((out / "results.json").read_text())
            self.assertEqual(result["evaluation"]["exact"]["candidate_status"]["candidate/bad"], "not_approved_numerical_health")
            result["numerical_health"] = {}
            m.write(out / "results.json", result)
            with self.assertRaisesRegex(ValueError, "numerical-health"):
                m.verify(out)

    def test_nonfinite_or_misaligned_clean_data_cannot_calibrate(self):
        p = self.protocol()
        rows = [{"argmax": [1]*x["tokens"], "entropy": [.5]*x["tokens"], "top_logprob": [-1.]*x["tokens"], "top_gap": [1.]*x["tokens"]} for x in p["probes"]]
        observed = {"reference/reference": rows, "calibration/c": copy.deepcopy(rows)}
        observed["calibration/c"][0]["entropy"][0] = float("inf")
        with self.assertRaises(self.m.base.NumericalHealthFailure):
            self.m.calibrated(p, observed)
        observed["calibration/c"][0]["entropy"][0] = .5
        observed["calibration/c"][0]["argmax"].pop()
        with self.assertRaisesRegex(ValueError, "shape"):
            self.m.calibrated(p, observed)


@unittest.skipUnless(importlib.util.find_spec("torch") and importlib.util.find_spec("transformers"),
                     "optional pretrained dependencies unavailable")
class RealCPUIntegration(unittest.TestCase):
    def test_random_qwen_end_to_end_freeze_run_and_independent_verify(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "prospective"
            command = [sys.executable, str(ROOT / "scripts/colab_deployment_audit_v3.py"),
                       "--local-test", "--output", str(out)]
            env = {**os.environ, "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
            run = subprocess.run(command, capture_output=True, text=True, timeout=300, env=env)
            self.assertEqual(run.returncode, 0, run.stderr[-5000:])
            result = json.loads((out / "results.json").read_text())
            protocol = json.loads((out / "protocol.json").read_text())
            self.assertTrue(result["local_test"])
            self.assertEqual(protocol["maximum_cap"], 127)
            self.assertTrue(result["comparison"]["panels"]["exact"]["satisfies_requirement"])
            self.assertFalse(result["evaluation"]["exact"]["false_alarms"])
            self.assertGreaterEqual(sum(p["tokens"] > 127 for p in protocol["probes"]), 2)
            replay = subprocess.run([sys.executable, str(ROOT / "scripts/colab_deployment_audit_v3.py"),
                                     "--phase", "verify", "--output", str(out)],
                                    capture_output=True, text=True, timeout=120, env=env)
            self.assertEqual(replay.returncode, 0, replay.stderr[-5000:])
            again = subprocess.run(command, capture_output=True, text=True, timeout=60, env=env)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("new empty directory", again.stderr)


if __name__ == "__main__":
    unittest.main()
