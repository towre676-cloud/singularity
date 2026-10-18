"""P25: visibility filtrations, refinement, witnesses and specialized domains."""

from fractions import Fraction as F
import json
from pathlib import Path
import unittest

from singularity.examples import GRAPHS
from singularity.graph import Graph
from singularity.heights import local_coefficients, marked_coefficients
from singularity.parameters import isolate_roots
from singularity.polynomials import mul, polynomial_from_json, sub
from singularity.visibility import first_split_volume, visibility_filtration

ROOT = Path(__file__).resolve().parents[1]


def cube():
    return Graph(8, ((i, i ^ (1 << b)) for i in range(8) for b in range(3) if i < i ^ (1 << b)))


def mobius_ladder():
    return Graph(8, tuple((i, (i + 1) % 8) for i in range(8)) + tuple((i, i + 4) for i in range(4)))


class VisibilityTests(unittest.TestCase):
    def test_reference_pairs_split_at_their_depths(self):
        cases = [("spectral_g", "spectral_h", 2), ("binary_g", "binary_h", 3)]
        for left, right, depth in cases:
            a, b = local_coefficients(GRAPHS[left], 4), local_coefficients(GRAPHS[right], 4)
            self.assertEqual(first_split_volume(a, b), depth)
            filtration = visibility_filtration({left: a, right: b})
            self.assertEqual([s["volume"] for s in filtration["splits"]], [depth])
        a, b = local_coefficients(cube(), 5), local_coefficients(mobius_ladder(), 5)
        self.assertEqual(first_split_volume(a, b), 4)
        self.assertIsNone(first_split_volume(a[:4], b))  # unresolved through 3, not equal
        filtration = visibility_filtration({"cube": a[:4], "mobius": b[:4]})
        self.assertEqual(filtration["unresolved_at_bound"], [{"members": ["cube", "mobius"], "status": "agreement through volume 3 only"}])

    def test_refinement_is_monotone_on_the_census(self):
        manifest = json.loads((ROOT / "results/census_manifest.json").read_text(encoding="utf-8"))
        for order in manifest["orders"][:5]:
            graphs = {str(c["canonical_code"]): Graph(c["n"], c["edges"]) for c in order["classes"]}
            for domain, series in (("polynomial", {k: local_coefficients(g, 5) for k, g in graphs.items()}),
                                   ("marked", {k: marked_coefficients(g, 5) for k, g in graphs.items()})):
                levels = visibility_filtration(series, domain, 5)["levels"]
                for coarse, fine in zip(levels, levels[1:]):
                    parent = {m: c["id"] for c in coarse["classes"] for m in c["members"]}
                    for cls in fine["classes"]:
                        self.assertEqual(len({parent[m] for m in cls["members"]}), 1)

    def test_witness_lower_coefficients_agree_and_signs(self):
        a, b = local_coefficients(GRAPHS["binary_g"], 4), local_coefficients(GRAPHS["binary_h"], 4)
        split = visibility_filtration({"g": a, "h": b})["splits"][0]
        self.assertEqual(a[:3], b[:3])
        self.assertEqual(polynomial_from_json(split["discrepancy_left_minus_right"]["polynomial"]), sub(a[3], b[3]))
        swapped = visibility_filtration({"a": b, "b": a})["splits"][0]
        self.assertEqual(polynomial_from_json(swapped["discrepancy_left_minus_right"]["polynomial"]), sub(b[3], a[3]))

    def test_duplicates_and_relabelings_share_classes(self):
        graph = GRAPHS["spectral_g"]
        series = {
            "original": local_coefficients(graph, 4),
            "relabeled": local_coefficients(graph.relabel((6, 5, 4, 3, 2, 1, 0)), 4),
            "duplicate": local_coefficients(graph, 4),
            "other": local_coefficients(GRAPHS["spectral_h"], 4),
        }
        final = visibility_filtration(series)["levels"][-1]["classes"]
        self.assertEqual([c["members"] for c in final], [["duplicate", "original", "relabeled"], ["other"]])

    def test_specialization_merges_symbolic_classes(self):
        series = {name: local_coefficients(GRAPHS[name], 3) for name in ("spectral_g", "spectral_h", "binary_g", "binary_h")}
        symbolic = visibility_filtration(series)
        self.assertEqual(len(symbolic["levels"][-1]["classes"]), 4)
        # q = 1 forgets energy: every seven-vertex series is the same.
        self.assertEqual(len(visibility_filtration(series, F(1))["levels"][-1]["classes"]), 1)
        # q = 1/2 keeps the separations, with exact values recorded.
        half = visibility_filtration(series, F(1, 2))
        self.assertEqual(len(half["levels"][-1]["classes"]), 4)
        self.assertTrue(all("value" in s["discrepancy_left_minus_right"] for s in half["splits"]))

    def test_algebraic_parameter_domain(self):
        f = {0: F(1, 5), 1: -1, 2: 1}  # interior roots (5 +- sqrt 5)/10
        left = [{0: 1}, f, mul(f, {1: 1})]
        right = [{0: 1}, {}, {}]
        root = isolate_roots(f)[0]
        domain = {"defining": f, "root": root}
        self.assertEqual(visibility_filtration({"l": left, "r": right}, domain)["unresolved_at_bound"][0]["members"], ["l", "r"])
        self.assertEqual(first_split_volume(left, right), 1)
        self.assertIsNone(first_split_volume(left, right, domain))
        self.assertEqual(first_split_volume(left, right, F(1, 2)), 1)

    def test_unequal_lengths_and_bounds(self):
        a, b = local_coefficients(Graph(3, [(0, 1)]), 5), local_coefficients(Graph(3, [(0, 1), (1, 2)]), 2)
        self.assertEqual(visibility_filtration({"a": a, "b": b})["bound"], 2)
        with self.assertRaises(ValueError):
            visibility_filtration({"a": a, "b": b}, bound=3)
        with self.assertRaises(ValueError):
            visibility_filtration({"a": marked_coefficients(Graph(2), 2)}, "marked")
        with self.assertRaises(ValueError):
            visibility_filtration({})
        with self.assertRaises(TypeError):
            visibility_filtration({"a": a}, True)


if __name__ == "__main__":
    unittest.main()
