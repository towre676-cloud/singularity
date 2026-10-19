"""Independent replays of the 0.8.0 retained evidence (no model inference)."""
import base64
import gzip
import hashlib
import json
import math
from pathlib import Path
import unittest

from singularity.model_audit import load_package, verify_package

try:
    import numpy as np
except ImportError:
    np = None

RESULTS = Path(__file__).resolve().parents[1] / "applications/training_lab/results"
CROSS, AUDIT = RESULTS / "cross_domain", RESULTS / "robust_audit"
SEEDS = ("1000", "1001", "1002")
SEEDED = ("neural", "calibrated_fixed_blend", "online_blend", "online_adaptive_blend")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class CrossDomainReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((CROSS / "protocol.json").read_text())
        cls.results = json.loads((CROSS / "results.json").read_text())
        cls.sums = json.loads((CROSS / "document_loss_sums.json").read_text())["sums"]
        cls.documents = json.loads(gzip.decompress((CROSS / "documents.json.gz").read_bytes()))["documents"]

    def total(self, index, arm, seed=None):
        key = f"doc{index}_{arm}_seed_{seed}" if arm in SEEDED else f"doc{index}_{arm}"
        record = self.sums[key]
        return float.fromhex(record["sum_nats"]), record["targets"]

    def test_documents_follow_the_frozen_hash_rule_and_identity(self):
        self.assertEqual(sha((CROSS / "documents.json.gz").read_bytes()), self.protocol["documents_sha256"])
        salt = "singularity-0.8.0-cross-domain"
        for domain, spec in self.protocol["protocol"]["domains"].items():
            members = [d for d in self.documents if d["domain"] == domain]
            self.assertEqual(len(members), spec["documents"])
            keys = [sha(f"{salt}/{domain}/{d['name']}".encode()) for d in members]
            self.assertEqual(keys, sorted(keys))
            for document in members:
                raw = base64.b64decode(document["base64"])
                self.assertEqual((sha(raw), len(raw)), (document["sha256"], document["bytes"]))
                self.assertTrue(2048 <= len(raw) <= 32768)

    def test_domain_means_replay_from_document_sums(self):
        rows = self.results["documents"]
        for domain, summary in self.results["domains"].items():
            members = [r["document"] for r in rows if r["domain"] == domain]
            for arm, value in summary["arms"].items():
                if arm in SEEDED:
                    per = [math.fsum(self.total(i, arm, s)[0] for i in members) /
                           sum(self.total(i, arm, s)[1] for i in members) for s in SEEDS]
                    replay = sum(per) / 3
                else:
                    replay = math.fsum(self.total(i, arm)[0] for i in members) / sum(self.total(i, arm)[1] for i in members)
                self.assertAlmostEqual(replay, value["nll_nats_per_byte"], places=9)
            self.assertEqual(summary["seeds_where_online_beats_neural"], 3)

    @unittest.skipIf(np is None, "optional numpy unavailable")
    def test_document_cluster_intervals_replay(self):
        rows = self.results["documents"]
        for domain, summary in self.results["domains"].items():
            members = [r["document"] for r in rows if r["domain"] == domain]
            sizes = np.array([rows[i]["targets"] for i in members], dtype=np.float64)

            def averaged(arm, i):
                return (sum(self.total(i, arm, s)[0] for s in SEEDS) / 3) if arm in SEEDED else self.total(i, arm)[0]

            for left, right in (("online_blend", "neural"), ("online_blend", "calibrated_fixed_blend"), ("adaptive_count", "count")):
                sums = np.array([averaged(left, i) - averaged(right, i) for i in members])
                draws = np.random.default_rng(80023).integers(0, len(sums), size=(10000, len(sums)))
                interval = np.quantile(sums[draws].sum(1) / sizes[draws].sum(1), [.025, .975])
                reported = summary["paired"][f"{left}_minus_{right}"]
                np.testing.assert_allclose(interval, reported["percentile_95_interval"], rtol=0, atol=1e-8)
                self.assertLess(reported["percentile_95_interval"][1], 0)

    def test_bound_equivalence_and_runtime_claims_are_recorded(self):
        self.assertLessEqual(self.results["reference_loop_max_abs_difference_nats"], 1e-9)
        for row in self.results["documents"]:
            for seed in SEEDS:
                self.assertLessEqual(row["seeds"][seed]["online_regret_nats"], math.log(21) + 1e-6)
        timing = self.results["timing"]
        self.assertTrue(timing["meets_2x_target"])
        self.assertGreater(timing["reference_over_fast"], 1)
        attempts = json.loads((CROSS / "execution_attempts.json").read_text())["attempts"]
        self.assertEqual(attempts[0]["revision"], 1)
        self.assertEqual(self.protocol["protocol"]["revision"]["number"], 2)


class RobustAuditReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.construction = json.loads((AUDIT / "construction.json").read_text())
        cls.audit = json.loads((AUDIT / "audit.json").read_text())
        cls.protocol = json.loads((AUDIT / "protocol.json").read_text())["protocol"]

    def test_minimum_cost_by_independent_bitmask_scan(self):
        costs = {p["id"]: p["cost"] for p in self.protocol["probes"]}
        ids = list(self.construction["separation_table"])
        table = [self.construction["separation_table"][i] for i in ids]
        masks = [sum(1 << e for e in range(len(ids)) if table[e][p]) for p in range(len(table[0]))]
        best = min(sum(costs[ids[e]] for e in range(len(ids)) if subset >> e & 1)
                   for subset in range(1 << len(ids))
                   if all(bin(subset & mask).count("1") >= 2 for mask in masks))
        self.assertEqual(best, self.construction["exact"]["cost"])
        chosen = sum(1 << ids.index(i) for i in self.construction["exact"]["probe_ids"])
        self.assertTrue(all(bin(chosen & mask).count("1") >= 2 for mask in masks))
        self.assertGreater(self.construction["comparators"]["greedy"]["cost"], best)

    def test_shipped_package_verifies_without_a_model(self):
        package = load_package(AUDIT / "seed_1002_package.json")
        self.assertTrue(verify_package(package)["verified"])
        self.assertEqual(sorted(p["id"] for p in package["probes"]), sorted(self.construction["exact"]["probe_ids"]))
        self.assertNotIn("weights", json.dumps(package))
        checks = self.audit["seed_1002_package"]["checks"]
        for fault in list(self.protocol["construction_faults"]) + list(self.protocol["heldout_faults"]):
            self.assertEqual(checks[fault]["verdict"], "changed", fault)
        for clean in self.protocol["false_alarm_clean_runs"]:
            self.assertEqual(checks[clean]["verdict"], "unchanged", clean)
        self.assertFalse(self.audit["panels_selected_using_audit"])


if __name__ == "__main__":
    unittest.main()
