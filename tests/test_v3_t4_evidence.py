"""The uploaded real T4 evidence must remain replayable and honestly scoped."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_real_v3_t4", ROOT / "scripts/verify_v3_t4_evidence.py")
REPLAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPLAY)


class ActualT4EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = REPLAY.replay()

    def test_source_bound_replay_matches_retained_receipt(self):
        self.assertEqual(self.report, json.loads((REPLAY.RUN / "verification.json").read_text()))

    def test_unique_optimum_has_a_tight_disjoint_group_lower_bound(self):
        bound = self.report["independent_tight_lower_bound"]
        self.assertEqual(bound["cost"], 379)
        self.assertTrue(bound["unique_optimum"])
        self.assertEqual(sorted(r["minimum_cost"] for r in bound["terms"].values()), [43, 80, 256])
        self.assertEqual(self.report["panel_costs"], {"exact": 379, "pruned_greedy": 379, "greedy": 557,
                                                   "representative": 286, "representative_completed": 665})
        self.assertFalse(self.report["panel_feasible"]["representative"])
        self.assertTrue(self.report["all_integer_caps_1_127_have_two_shape_witnesses"])

    def test_clean_controls_and_measured_truncation_family_pass(self):
        self.assertEqual(list(self.report["full_pool_clean_validation_flags"].values()), [0]*4)
        e = self.report["exact_evaluation"]
        self.assertFalse(e["false_alarms"])
        for key, count in e["separators"].items():
            if key.startswith(("construction/", "family_check/")):
                self.assertGreaterEqual(count, 2, key)
            if key.startswith("known_v2_retest/"):
                self.assertGreaterEqual(count, 1, key)
        self.assertEqual(e["separators"]["new_heldout/alternating_attention_mask"], 6)
        self.assertEqual(e["separators"]["new_heldout/output_vocabulary_permutation"], 6)
        self.assertEqual(e["separators"]["diagnostic/positions_not_offset_for_left_padding"], 0)
        self.assertEqual(self.report["health_nonfinite_values"], 2116)

    def test_uniform_shift_is_reported_as_numerical_sensitivity(self):
        shift = self.report["uniform_translation"]
        self.assertEqual(shift["full_pool_flags"], 10)
        self.assertEqual(len(shift["selected_flag_reports"]), 1)
        row = shift["selected_flag_reports"][0]
        self.assertEqual(row["id"], "uni_ligature")
        self.assertFalse(row["length_mismatch"])
        self.assertEqual(row["discrete_mismatches"], 0)
        self.assertGreater(row["max_abs"]["entropy"], row["tolerance"]["entropy"])
        self.assertIn("not evidence of semantic change", shift["classification"])


if __name__ == "__main__":
    unittest.main()
