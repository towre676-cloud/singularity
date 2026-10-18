import importlib.util
import json
import unittest
from pathlib import Path

from singularity.graph import Graph

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("collision_cases", ROOT / "scripts/collision_cases.py")
collision_cases = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collision_cases)


class TwistSearchTests(unittest.TestCase):
    def test_finds_known_switches(self):
        # Positive control: retained straight/twisted gluings are found by the separator twist search.
        pairs = json.loads((ROOT / "results/whitney_switches.json").read_text())["pairs"]
        found = 0
        for record in pairs:
            if record["isomorphic"]:
                continue
            a = Graph(record["straight"]["n"], record["straight"]["edges"])
            b = Graph(record["twisted"]["n"], record["twisted"]["edges"])
            if a.n > 7:
                continue
            self.assertTrue(any(collision_cases.isomorphic(t, b) for _, t in collision_cases.twists(a)))
            found += 1
            if found == 5:
                break
        self.assertEqual(found, 5)

    def test_isomorphism_check(self):
        path = Graph(4, [(0, 1), (1, 2), (2, 3)])
        self.assertTrue(collision_cases.isomorphic(path, Graph(4, [(2, 0), (0, 3), (3, 1)])))
        self.assertFalse(collision_cases.isomorphic(path, Graph(4, [(0, 1), (0, 2), (0, 3)])))


if __name__ == "__main__":
    unittest.main()
