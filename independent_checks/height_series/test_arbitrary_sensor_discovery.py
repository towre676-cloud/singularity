import importlib.util
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("arbitrary_sensor_discovery",HERE/"arbitrary_sensor_discovery.py")
M=importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

class ArbitrarySensorTests(unittest.TestCase):
    def test_both_global_optima(self):
        report=M.replay()
        self.assertEqual(report["results"]["general"]["global_optimal_gain"],"93093/14165")
        self.assertEqual(report["results"]["connected"]["global_optimal_gain"],"44191/19786")
        for row in report["results"].values():
            self.assertTrue(row["global_optimal"])
            self.assertTrue(row["dual_feasible"])

if __name__=="__main__":
    unittest.main()
