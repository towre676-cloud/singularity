import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("perfectjet_height_bridge", HERE/"perfectjet_observation_bridge.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


class PerfectJetObservationBridgeTests(unittest.TestCase):
    def test_general_reader_replay(self):
        report = B.compare("general")
        self.assertEqual(report["perfectjet"]["optimal_panel"], [4, 8, 12, 14, 18, 24, 26])
        self.assertEqual(report["perfectjet"]["inverse_infinity_norm"], "93093/14165")

    def test_connected_reader_replay(self):
        report = B.compare("connected")
        self.assertEqual(report["perfectjet"]["optimal_panel"], [6, 10, 14, 18, 24, 26])
        self.assertEqual(report["perfectjet"]["inverse_infinity_norm"], "44191/19786")
        self.assertEqual(report["perfectjet"]["optimal_determinant"], "74791080")

    def test_retained_certificate(self):
        self.assertTrue(B.receipt()["retained_connected_certificate_replayed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
