"""P03 acceptance matrix: malformed, non-canonical and altered certificates."""

import copy
import json
from pathlib import Path
import unittest
from unittest import mock

from singularity import certificates
from singularity.certificates import VERSION, build_certificate, parse_certificate, replay_certificate
from singularity.examples import GRAPHS
from singularity.graph import Graph

ROOT = Path(__file__).resolve().parents[1]


def mutated(base, path, value):
    packet = copy.deepcopy(base)
    target = packet
    for key in path[:-1]:
        target = target[key]
    if value is DELETE:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return packet


DELETE = object()


class CertificateMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pair = build_certificate(
            GRAPHS["spectral_g"], 3, GRAPHS["spectral_h"], "spectral",
            {"coefficient": "2", "monomial": 2, "factors": [[1, 2], [2, 1]]},
        )
        cls.single = build_certificate(Graph(3, [(0, 1), (1, 2)]), 4, label="path")

    def assert_rejected(self, packet, fragment):
        self.assertTrue(any(fragment in e for e in parse_certificate(packet)), parse_certificate(packet))
        report = replay_certificate(packet)
        self.assertFalse(report["valid"])
        self.assertTrue(any(fragment in e for e in report["errors"]), report["errors"])

    def test_built_packets_are_well_formed(self):
        self.assertEqual(parse_certificate(self.pair), [])
        self.assertEqual(parse_certificate(self.single), [])
        report = replay_certificate(self.pair)
        self.assertTrue(report["valid"], report)
        # Both routes ran on both graphs: 120 compositions and 120 chains each.
        self.assertEqual(report["checks"]["profiles_recomputed"], 240)
        self.assertEqual(report["checks"]["chain_profiles_recomputed"], 240)

    def test_invalid_edges_in_every_graph_field(self):
        cases = {
            "loop": [[1, 1]], "outside": [[0, 3]], "negative": [[-1, 2]],
            "reversed": [[1, 0]], "duplicate": [[0, 1], [0, 1]], "unsorted": [[1, 2], [0, 1]],
            "boolean": [[False, 1]], "triple": [[0, 1, 2]], "float": [[0, 1.0]],
        }
        expected = {
            "loop": "loop", "outside": "outside", "negative": "outside", "reversed": "(min, max)",
            "duplicate": "duplicated", "unsorted": "duplicated", "boolean": "pair of integers",
            "triple": "pair of integers", "float": "pair of integers",
        }
        for name, edges in cases.items():
            with self.subTest(field="graph", case=name):
                self.assert_rejected(mutated(self.single, ["graph", "edges"], edges), expected[name])
            with self.subTest(field="comparison", case=name):
                bad = mutated(self.pair, ["comparison", "graph", "n"], 3)
                bad = mutated(bad, ["comparison", "graph", "edges"], edges)
                self.assert_rejected(bad, expected[name])
        for n in (0, True, 2.0, "3"):
            with self.subTest(n=n):
                self.assert_rejected(mutated(self.single, ["graph", "n"], n), "n must be a positive integer")
        self.assert_rejected(mutated(self.single, ["graph", "label"], "x"), "exactly n and edges")

    def test_malformed_degrees_and_duplicate_terms(self):
        rows = self.single["local_coefficients"]
        cases = [
            (["local_coefficients", 2], [[-1, 1]] + rows[2], "negative energy"),
            (["local_coefficients", 2], rows[2] + rows[2][:1], "duplicate or unsorted energy"),
            (["local_coefficients", 2], list(reversed(rows[2])), "duplicate or unsorted energy"),
            (["normalized_coefficients", 1], [[1, 0]], "counts must be positive"),
            (["normalized_coefficients", 1], [[1, True]], "integer pairs"),
            (["local_coefficients", 1], [[1.0, 2]], "integer pairs"),
            (["local_coefficients"], rows[:-1], "expected 5 volume rows"),
            (["comparison", "local_coefficients", 0], [[0, 1], [0, 1]], "duplicate or unsorted energy"),
        ]
        for path, value, fragment in cases:
            base = self.pair if path[0] == "comparison" else self.single
            with self.subTest(path=path, value=value):
                self.assert_rejected(mutated(base, path, value), fragment)
        marked = self.single["marked_coefficients"]
        for value, fragment in [
            (marked + marked[-1:], "duplicate or unsorted key"),
            (list(reversed(marked)), "duplicate or unsorted key"),
            (marked + [[5, 0, 1, 1]], "invalid term"),
            (marked[:-1] + [marked[-1][:3] + [True]], "integers"),
        ]:
            with self.subTest(marked=value[-1]):
                self.assert_rejected(mutated(self.single, ["marked_coefficients"], value), fragment)

    def test_malformed_rational_polynomials(self):
        euler = self.single["euler_exponents"]
        for value, fragment in [
            ([[1, 2, 1], [1, 3, 1]], "duplicate or unsorted degree"),
            ([[2, 1, 1], [1, 1, 1]], "duplicate or unsorted degree"),
            ([[-1, 1, 1]], "negative degree"),
            ([[1, 1, 0]], "nonpositive denominator"),
            ([[1, 0, 1]], "zero numerator"),
            ([[1, 2, 4]], "lowest terms"),
            ([[1, True, 1]], "integers"),
        ]:
            with self.subTest(value=value):
                self.assert_rejected(mutated(self.single, ["euler_exponents", 1], value), fragment)
        self.assert_rejected(mutated(self.single, ["euler_exponents"], euler[:-1]), "expected 5 polynomials")
        bad = mutated(self.pair, ["comparison", "first_difference", "polynomial"], [[2, 2, 1], [2, -4, 1]])
        self.assert_rejected(bad, "duplicate or unsorted degree")
        bad = mutated(self.pair, ["comparison", "first_difference", "volume"], 9)
        self.assert_rejected(bad, "out of range")
        bad = mutated(self.pair, ["comparison", "factorization", "factors"], [[1, 2, 3]])
        self.assert_rejected(bad, "integer pairs")

    def test_fields_types_and_format_names(self):
        self.assert_rejected(mutated(self.single, ["format"], "relational-height/1"), "superseded roadmap name")
        self.assert_rejected(mutated(self.single, ["format"], "singularity.certificate/2"), "unrecognized")
        self.assert_rejected(mutated(self.single, ["extra"], 1), "unknown field extra")
        self.assert_rejected(mutated(self.single, ["identities"], DELETE), "missing field identities")
        self.assert_rejected(mutated(self.single, ["max_volume"], True), "max_volume")
        self.assert_rejected(mutated(self.single, ["profile_count"], True), "profile_count")
        self.assert_rejected(mutated(self.single, ["graph_sha256"], "A" * 64), "hexadecimal")
        self.assert_rejected(mutated(self.single, ["label"], 3), "label must be text")
        self.assertEqual(parse_certificate([]), ["certificate must be a JSON object"])

    def test_altered_counts_rejected_with_digest_and_flags_unchanged(self):
        # Each alteration is well formed, keeps the digest and identity flags,
        # and must be caught by recomputation alone.
        cases = [
            (["local_coefficients", 2, 0, 1], "local coefficients mismatch"),
            (["normalized_coefficients", 2, 0, 1], "normalized coefficients mismatch"),
            (["marked_coefficients", 3, 3], "marked coefficients mismatch"),
        ]
        for path, fragment in cases:
            packet = copy.deepcopy(self.single)
            target = packet
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] += 1
            with self.subTest(path=path):
                self.assertEqual(parse_certificate(packet), [])
                report = replay_certificate(packet)
                self.assertFalse(report["valid"])
                self.assertIn(fragment, report["errors"])
        packet = copy.deepcopy(self.pair)
        packet["comparison"]["local_coefficients"][2][0][1] += 1
        self.assertIn("comparison local coefficients mismatch", replay_certificate(packet)["errors"])
        packet = copy.deepcopy(self.pair)
        packet["comparison"]["first_difference"]["polynomial"][0][1] = 3
        self.assertIn("first difference mismatch", replay_certificate(packet)["errors"])
        packet = copy.deepcopy(self.single)
        packet["identities"]["nested_threshold_energy"] = False
        self.assertIn("identity declarations mismatch", replay_certificate(packet)["errors"])

    def test_chain_route_disagreement_is_reported(self):
        original = certificates.chain_marked_coefficients

        def broken(graph, max_volume):
            result = dict(original(graph, max_volume))
            result[(1, 1, 1)] = result.get((1, 1, 1), 0) + 1
            return result

        with mock.patch.object(certificates, "chain_marked_coefficients", broken):
            report = replay_certificate(self.pair)
        self.assertIn("level-chain and composition replay routes disagree", report["errors"])
        self.assertIn("comparison level-chain and composition replay routes disagree", report["errors"])

    def test_budget_counts_both_routes(self):
        # Path P3, M=4: 35 compositions + (35 - 4) = 31 chains.
        self.assertTrue(replay_certificate(self.single, max_profiles=66)["valid"])
        refused = replay_certificate(self.single, max_profiles=65)
        self.assertFalse(refused["valid"])
        self.assertIn("66 profiles and chains", refused["errors"][0])


class RetainedPacketTests(unittest.TestCase):
    def test_every_retained_certificate_replays(self):
        paths = sorted((ROOT / "results/certificates").glob("*.json"))
        self.assertGreaterEqual(len(paths), 4)
        for path in paths:
            packet = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(path=path.name):
                self.assertEqual(packet["format"], VERSION)
                self.assertEqual(parse_certificate(packet), [])
                report = replay_certificate(packet)
                self.assertTrue(report["valid"], report["errors"])
                self.assertEqual(report["checks"]["chain_profiles_recomputed"], report["checks"]["nested_profiles_checked"])

    def test_retained_tables_agree_with_certified_first_differences(self):
        examples = json.loads((ROOT / "results/exact_examples.json").read_text(encoding="utf-8"))
        for name in ("spectral", "binary_census", "regular_cube_mobius"):
            packet = json.loads((ROOT / f"results/certificates/{name}.json").read_text(encoding="utf-8"))
            pair = examples["pairs"][name]
            with self.subTest(pair=name):
                self.assertEqual(packet["comparison"]["first_difference"]["volume"], pair["first_difference_volume"])
                self.assertEqual(packet["comparison"]["first_difference"]["polynomial"], pair["difference"])
                self.assertEqual(packet["comparison"]["factorization"], pair["factorization"])
                self.assertEqual(examples["certificate_replays"][name]["valid"], True)
        self.assertEqual([examples["pairs"][n]["first_difference_volume"] for n in ("spectral", "binary_census", "regular_cube_mobius")], [2, 3, 4])


if __name__ == "__main__":
    unittest.main()
