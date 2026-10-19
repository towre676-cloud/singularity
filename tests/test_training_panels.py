"""Independent finite-cover checks of the frozen-prediction adapter."""
from copy import deepcopy
import hashlib
from itertools import combinations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from singularity.training_panels import INPUT_SCHEMA, training_panel_report


def fixture():
    ids = ["a", "b", "c", "d", "a-copy"]
    columns = [(0, 0, 4, 4, 0), (0, 4, 0, 4, 0), (0, 1, 2, 3, 0)]
    return {
        "schema": INPUT_SCHEMA,
        "candidates": [{"id": ident, "label": ident} for ident in ids],
        "construction": {"split_id": "construction-fixture", "probes": [
            {"id": f"p{i}", "cost": cost,
             "counts": {ident: {"correct_count": correct, "total_count": 4}
                        for ident, correct in zip(ids, column)}}
            for i, (cost, column) in enumerate(zip((2, 2, 3), columns))]},
    }


class TrainingPanelTests(unittest.TestCase):
    def test_independent_exhaustive_cover_and_real_discovery_cost(self):
        table = fixture()
        report = training_panel_report(table)
        # Independent enumeration of every subset, without panels.py masks,
        # planner, quotient helper, or exhaustive_minimum_panel.
        probes = table["construction"]["probes"]
        representatives = ["a", "b", "c", "d"]
        valid = []
        for size in range(len(probes) + 1):
            for subset in combinations(range(len(probes)), size):
                if all(any(probes[e]["counts"][a]["correct_count"] !=
                           probes[e]["counts"][b]["correct_count"] for e in subset)
                       for a, b in combinations(representatives, 2)):
                    valid.append((sum(probes[e]["cost"] for e in subset), subset))
        self.assertEqual(min(valid), (3, (2,)))
        self.assertEqual(report["selected_probe_ids"], ["p2"])
        self.assertEqual(report["selected_panel_cost"], [3, 1])
        self.assertEqual(report["greedy"]["cost"], [4, 1])
        self.assertEqual(report["full_panel_cost"], [7, 1])
        self.assertEqual(report["discovery_cost_examples"], 60)
        self.assertEqual(report["construction_uncoverable_pairs"], [["a", "a-copy"]])
        self.assertFalse(report["all_original_candidates_discriminated"])
        self.assertEqual(len(report["construction_pair_witnesses"]), 9)
        self.assertTrue(report["exhaustive_reference"]["matches_optimal_cost"])

    def test_audit_cannot_change_selection_and_can_fail_to_transfer(self):
        table = fixture()
        base = training_panel_report(table)
        audit = deepcopy(table["construction"])
        audit["split_id"] = "separate-audit"
        # The selected construction probe becomes completely uninformative.
        for cell in audit["probes"][2]["counts"].values():
            cell["correct_count"] = 0
        audit["probes"].reverse()  # Alignment must use IDs, not positions.
        table["audit"] = audit
        report = training_panel_report(table)
        self.assertEqual(report["selected_probe_ids"], base["selected_probe_ids"])
        self.assertEqual(report["exact"], base["exact"])
        self.assertFalse(report["audit"]["used_for_selection"])
        self.assertFalse(report["audit"]["all_original_candidates_separated"])
        self.assertEqual(report["audit"]["construction_distinct_pairs_still_separated"], 0)
        self.assertEqual(len(report["audit"]["full_signature_classes"]), 4)

    def test_rational_costs_and_all_equal_empty_pool(self):
        table = fixture()
        table["construction"]["probes"][2]["cost"] = [1, 2]
        report = training_panel_report(table)
        self.assertEqual(report["selected_panel_cost"], [1, 2])
        table["construction"]["probes"] = []
        report = training_panel_report(table)
        self.assertEqual(report["quotient_class_count"], 1)
        self.assertEqual(report["selected_probe_ids"], [])
        self.assertEqual(report["selected_panel_cost"], [0, 1])
        self.assertEqual(report["discovery_cost_examples"], 0)
        self.assertEqual(len(report["construction_uncoverable_pairs"]), 10)

    def test_fractional_readings_identify_equal_accuracy_signatures(self):
        table = fixture()
        # Equal accuracy, not equal raw count, defines observational equality.
        # Denominators may differ across probes, but must agree per candidate.
        for cell in table["construction"]["probes"][0]["counts"].values():
            cell["correct_count"] *= 2
            cell["total_count"] *= 2
        report = training_panel_report(table)
        self.assertEqual(report["construction_readings"][0],
                         [[0, 1], [0, 1], [1, 1], [1, 1], [0, 1]])
        self.assertEqual(report["selected_panel_cost"], [3, 1])

    def test_rejects_invalid_counts_costs_and_split_reuse(self):
        for replacement in (True, 0.5, "1/2", [1, 0], [-1, 2]):
            table = fixture()
            table["construction"]["probes"][0]["cost"] = replacement
            with self.assertRaises((TypeError, ValueError)):
                training_panel_report(table)
        table = fixture()
        table["construction"]["probes"][0]["counts"]["a"]["total_count"] = 3
        with self.assertRaises(ValueError):
            training_panel_report(table)
        table = fixture()
        table["construction"]["probes"][0]["counts"]["a"]["correct_count"] = 5
        with self.assertRaises(ValueError):
            training_panel_report(table)
        table = fixture()
        table["audit"] = deepcopy(table["construction"])
        with self.assertRaises(ValueError):
            training_panel_report(table)

    def test_cli_binds_output_to_input_bytes(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "training_panels.py"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "predictions.json"
            output = Path(directory) / "report.json"
            raw = (json.dumps(fixture(), indent=2) + "\n").encode()
            source.write_bytes(raw)
            subprocess.run([sys.executable, str(script), str(source), "--output", str(output)],
                           check=True, capture_output=True, text=True)
            report = json.loads(output.read_text())
            self.assertEqual(report["input_file_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(report["selected_probe_ids"], ["p2"])
            self.assertEqual(source.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
