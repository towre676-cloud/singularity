"""P29: the retained census manifest reconstructs and reconciles independently."""

from hashlib import sha256
from itertools import permutations
import importlib.util
import json
from math import factorial
from pathlib import Path
import unittest

from singularity.graph import Graph

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("census", ROOT / "scripts/census.py")
census = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(census)


def isomorphic(g, h):
    """Brute-force decision, independent of canonical_code."""
    if g.n != h.n or len(g.edges) != len(h.edges):
        return False
    target = set(h.edges)
    return any(all(tuple(sorted((p[u], p[v]))) in target for u, v in g.edges) for p in permutations(range(g.n)))


class CensusManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "results/census_manifest.json").read_text(encoding="utf-8"))

    def test_counts_reconcile(self):
        orders = self.manifest["orders"]
        self.assertEqual([o["connected_labeled_graphs"] for o in orders], [1, 1, 4, 38, 728, 26704])
        self.assertEqual([o["isomorphism_classes"] for o in orders], [1, 1, 2, 6, 21, 112])
        for order in orders:
            self.assertEqual(order["recurrence_connected_labeled"], order["connected_labeled_graphs"])
            self.assertEqual(sum(c["labeled_copies"] for c in order["classes"]), order["connected_labeled_graphs"])
            self.assertEqual(order["orbit_stabilizer_total"], order["connected_labeled_graphs"])

    def test_reconstruct_every_graph(self):
        for order in self.manifest["orders"]:
            for record in order["classes"]:
                graph = Graph(record["n"], record["edges"])
                source = {"n": graph.n, "edges": [list(e) for e in graph.edges]}
                self.assertEqual(source["edges"], record["edges"])
                self.assertTrue(graph.connected)
                self.assertEqual(sha256(json.dumps(source, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), record["sha256"])
                self.assertEqual(census.canonical_code(graph), record["canonical_code"])
                self.assertEqual(sorted(graph.degrees), record["degrees"])

    def test_automorphisms_and_uniqueness_through_five_vertices(self):
        for order in self.manifest["orders"][:5]:
            graphs = [Graph(c["n"], c["edges"]) for c in order["classes"]]
            for record, graph in zip(order["classes"], graphs):
                self.assertEqual(record["automorphism_group_order"] * record["labeled_copies"], factorial(graph.n))
            for i in range(len(graphs)):
                for j in range(i + 1, len(graphs)):
                    self.assertFalse(isomorphic(graphs[i], graphs[j]))

    def test_relabeled_copies_and_equal_degree_graphs(self):
        prism = Graph(6, [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (0, 3), (1, 4), (2, 5)])
        k33 = Graph(6, [(i, j) for i in range(3) for j in range(3, 6)])
        self.assertEqual(sorted(prism.degrees), sorted(k33.degrees))
        self.assertNotEqual(census.canonical_code(prism), census.canonical_code(k33))
        for permutation in ((1, 0, 2, 3, 4, 5), (1, 3, 5, 0, 2, 4)):
            copy = prism.relabel(permutation)
            self.assertEqual(census.canonical_code(copy), census.canonical_code(prism))
            self.assertNotEqual(copy.edges, prism.edges)
        codes = {c["canonical_code"] for c in self.manifest["orders"][5]["classes"]}
        self.assertIn(census.canonical_code(prism), codes)
        self.assertIn(census.canonical_code(k33), codes)

    def test_manifest_is_the_census_population(self):
        summary = json.loads((ROOT / "results/small_census.json").read_text(encoding="utf-8"))
        for order, record in zip(self.manifest["orders"], summary["orders"]):
            self.assertEqual([(c["canonical_code"], c["edges"]) for c in order["classes"]],
                             [(g["canonical_code"], g["edges"]) for g in record["graphs"]])

    def test_reserialization_is_deterministic(self):
        text = (ROOT / "results/census_manifest.json").read_text(encoding="utf-8")
        self.assertEqual(json.dumps(json.loads(text), indent=1, sort_keys=True) + "\n", text)


if __name__ == "__main__":
    unittest.main()
