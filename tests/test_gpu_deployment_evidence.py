"""Independent replay of the retained version-2 GPU deployment audit (no model).

Recomputes the calibration rule, tolerances, every separation, the exact
two-probe minimum and the false-alarm counts from raw observations. The
stabilization rule is reimplemented here rather than imported from the script.
"""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from singularity.model_audit.core import deviation, flags, load_package, tolerances_from_clean, verify_package

RUN = Path(__file__).resolve().parents[1] / "applications/training_lab/results/gpu_deployment_audit/v2_t4_qwen2.5-1.5b"


def stable_reference(reference, calibration, tie_margin):
    stable = copy.deepcopy(reference)
    for e, expected in enumerate(stable):
        for run in calibration:
            for i, (a, b) in enumerate(zip(run[e]["argmax"], expected["argmax"])):
                if a != b and expected["top_gap"][i] > tie_margin:
                    expected["top_gap"][i] = 0.
        if "continuation" in expected:
            keep = min([len(expected["continuation"])] + [
                next((i for i, (a, b) in enumerate(zip(run[e]["continuation"], expected["continuation"])) if a != b),
                     min(len(run[e]["continuation"]), len(expected["continuation"]))) for run in calibration])
            for key in ("continuation", "continuation_logprob"):
                expected[key] = expected[key][:keep]
            if not keep:
                del expected["continuation"], expected["continuation_logprob"]
    return stable


def restrict(row, expected):
    out = {k: v for k, v in row.items() if k not in ("continuation", "continuation_logprob")}
    if "continuation" in expected:
        n = len(expected["continuation"])
        out["continuation"], out["continuation_logprob"] = row["continuation"][:n], row["continuation_logprob"][:n]
    return out


class VersionTwoT4Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((RUN / "protocol.json").read_text())
        cls.results = json.loads((RUN / "results.json").read_text())
        cls.observed = json.loads((RUN / "observations.json").read_text())
        spec = cls.protocol["tolerance"]
        reference = cls.observed["reference/reference"]
        calibration_raw = [cls.observed[f"calibration/{n}"] for n in cls.protocol["calibration_clean_runs"]]
        cls.stable = stable_reference(reference, calibration_raw, spec["tie_margin"])
        calibration = [[restrict(r, s) for r, s in zip(run, cls.stable)] for run in calibration_raw]
        cls.tolerances, _ = tolerances_from_clean(cls.stable, calibration, spec["factor"], spec["floor"], spec["tie_margin"])

        def separation(rows):
            return [flags(deviation(restrict(o, s), s, spec["tie_margin"]), t)
                    for o, s, t in zip(rows, cls.stable, cls.tolerances)]

        cls.tables = {k: separation(v) for k, v in cls.observed.items()
                      if k.split("/")[0] in ("construction", "heldout", "validation", "candidate")}

    def test_protocol_integrity_and_order(self):
        body = {k: v for k, v in self.protocol.items() if k not in ("frozen_at_utc", "protocol_sha256")}
        digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(digest, self.protocol["protocol_sha256"])
        self.assertEqual(self.results["protocol_sha256"], digest)
        self.assertLess(self.protocol["frozen_at_utc"], self.results["created_at_utc"])
        self.assertTrue(verify_package(load_package(RUN / "package.json"))["verified"])

    def test_tolerances_and_separators_replay(self):
        for got, want in zip(self.tolerances, self.results["tolerances"]):
            for key in want:
                self.assertAlmostEqual(got[key], want[key], places=12)
        self.assertEqual({k: sum(v) for k, v in self.tables.items()}, self.results["full_pool_separators"])

    def test_exact_minimum_and_baselines_replay(self):
        ids = [p["id"] for p in self.protocol["probes"]]
        costs = [p["cost"] for p in self.protocol["probes"]]
        coverable = [k for k, v in self.tables.items() if k.startswith("construction/") and sum(v) >= 2]
        self.assertEqual(sorted(k.split("/", 1)[1] for k in coverable), sorted(self.results["coverable"]))
        masks = [sum(1 << e for e in range(len(ids)) if self.tables[k][e]) for k in coverable]
        best = min(sum(costs[e] for e in range(len(ids)) if s >> e & 1) for s in range(1 << len(ids))
                   if all(bin(s & m).count("1") >= 2 for m in masks))
        self.assertEqual(best, 261)
        self.assertEqual(self.results["panels"]["exact"]["cost"], best)
        self.assertEqual(self.results["panels"]["pruned_greedy"]["cost"], best)
        self.assertEqual(self.results["panels"]["greedy"]["cost"], 272)

    def test_clean_validation_and_detection_replay(self):
        panel = [p["id"] for p in self.protocol["probes"]]
        exact = [panel.index(i) for i in self.results["panels"]["exact"]["probe_ids"]]
        for name in self.protocol["validation_clean_runs"]:
            self.assertFalse(any(self.tables[f"validation/{name}"]), name)
        missed = [k for k in self.tables if k.startswith("heldout/") and not any(self.tables[k][e] for e in exact)]
        self.assertEqual(missed, ["heldout/truncate_to_72"])
        self.assertEqual(self.results["candidates"]["eager_attention"]["status"], "not_approved_numerical_health_failure")
        self.assertEqual(sum(self.results["numerical_health_failures"]["candidate/eager_attention"].values()), 1348)


if __name__ == "__main__":
    unittest.main()
