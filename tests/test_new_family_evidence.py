"""Apply the unchanged independent audit oracle to the new model family."""
import importlib.util
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("original_pretrained_evidence_for_transfer", ROOT / "tests/test_pretrained_evidence.py")
EVIDENCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVIDENCE)
TRANSFER = ROOT / "applications/training_lab/results/new_family_audit/qwen2.5-1.5b"


class NewFamilyAuditEvidence(EVIDENCE.PretrainedAuditEvidence):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        result = TRANSFER / "results.json"
        if not result.is_file():
            raise AssertionError("required independent model-family confirmation is missing")
        cls.completed = sorted({*cls.completed, result})

    def test_fresh_process_cli_reports_clean_target(self):
        receipt = json.loads((TRANSFER / "cli_check.json").read_text())
        package = json.loads((TRANSFER / "package.json").read_text())
        self.assertEqual(receipt["exit_code"], 0)
        self.assertEqual(receipt["report"]["verdict"], "unchanged")
        self.assertEqual(receipt["report"]["contract_mismatches"], [])
        self.assertEqual(receipt["report"]["flagged_probes"], [])
        self.assertEqual(receipt["report"]["package_sha256"], package["package_sha256"])

    def test_posthoc_optimal_pruning_of_greedy(self):
        record = EVIDENCE.read(TRANSFER / "pruned_greedy_posthoc.json")
        result = EVIDENCE.read(TRANSFER / "results.json")
        protocol, observations, reports = self.tables(TRANSFER)
        self.assertIn("post hoc", record["analysis_status"])
        self.assertEqual(record["result_sha256"], hashlib.sha256((TRANSFER / "results.json").read_bytes()).hexdigest())
        self.assertEqual(record["observations_sha256"], hashlib.sha256((TRANSFER / "observations.json").read_bytes()).hexdigest())
        self.assertEqual(record["protocol_sha256"], protocol["protocol_sha256"])
        self.assertEqual(record["greedy_indices"], result["selection"]["greedy"]["indices"])
        self.assertEqual(record["eligible_faults"], result["selection"]["eligible_faults"])
        self.assertEqual(record["requirement"], 2)
        greedy, probes = record["greedy_indices"], protocol["probes"]
        self.assertEqual(record["subsets_checked"], 1 << len(greedy))
        recomputed = []
        for mask in range(1 << len(greedy)):
            members = [index for bit, index in enumerate(greedy) if mask >> bit & 1]
            coverage = {name: sum(reports[name][index]["flags"] for index in members) for name in record["eligible_faults"]}
            recomputed.append({"subset": mask, "indices": members, "cost": sum(probes[index]["cost"] for index in members),
                               "construction_coverage": coverage, "feasible": all(count >= 2 for count in coverage.values())})
        self.assertEqual(record["all_subsets"], recomputed)
        best = min((row for row in recomputed if row["feasible"]), key=lambda row: (row["cost"], row["indices"]))
        self.assertEqual(record["optimally_pruned_greedy"], {key: best[key] for key in ("indices", "cost", "construction_coverage")})
        self.assertEqual(record["exact_cost"], result["selection"]["exact"]["cost"])
        self.assertAlmostEqual(record["exact_saving_percent_over_pruned_greedy"],
                               100 * (best["cost"] - record["exact_cost"]) / best["cost"], places=12)


if __name__ == "__main__":
    unittest.main()
