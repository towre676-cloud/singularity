from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import unittest

from vol9_10_reader import reader_model, reconstruct
from vol9_10_sensor_design import report
from vol9_10_sensor_verify import dot, verify


class SensorDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).with_name('vol9_10_sensor_certificates.json')
        cls.certificates = json.loads(path.read_text())

    def test_regeneration_and_independent_replay(self):
        self.assertEqual(json.loads(json.dumps(report())), self.certificates)
        verify(self.certificates)
        self.assertEqual(
            [(c['original_gain'], c['gain']) for c in self.certificates['cases']],
            [('3218423', '2283261919/403723320'), ('1', '1'),
             ('2006752078/5', '1073461009715/22189301316'), ('1', '1')],
        )

    def test_signed_full_polynomial_matches_established_reader(self):
        for case in self.certificates['cases']:
            volume, mode = case['volume'], case['mode']
            with self.subTest(volume=volume, mode=mode):
                panel, names, basis, _, _ = reader_model(volume, mode)
                coords = [Fraction((-1)**i * (i + 2), i + 3) for i in range(len(names))]
                polynomial = {e: dot([p.get(e, 0) for p in basis], coords)
                              for e in case['coefficient_degrees']}
                observations = [sum(Fraction(a) * polynomial[int(e)] for e, a in sensor.items())
                                for sensor in case['sensors']]
                recovered = [dot(list(map(Fraction, row)), observations)
                             for row in case['decoder']]
                actual = {e: str(dot([p.get(e, 0) for p in basis], recovered))
                          for e, value in polynomial.items() if value}
                original = reconstruct(volume, [polynomial.get(e, 0) for e in panel], mode=mode)
                self.assertEqual(recovered, coords)
                self.assertEqual(actual, original['difference_polynomial'])

    def test_rejects_corrupt_certificates(self):
        for field, value, message in (
            ('gain', '0', 'Primal and dual gains differ'),
            ('dual', ['0'] * 10, 'Primal and dual gains differ'),
            ('dual', ['1000'] * 10, 'Infeasible dual'),
            ('critical_panel', [], 'Unexpected tight coefficient set'),
        ):
            with self.subTest(field=field, value=value):
                altered = deepcopy(self.certificates)
                altered['cases'][0][field] = value
                with self.assertRaisesRegex(ValueError, message):
                    verify(altered)

        altered = deepcopy(self.certificates)
        altered['cases'][0]['sensors'][0] = {'5': '2'}
        with self.assertRaisesRegex(ValueError, 'Sensor cost exceeds one'):
            verify(altered)
        altered = deepcopy(self.certificates)
        altered['cases'][0]['decoder'][0][0] = '0'
        with self.assertRaisesRegex(ValueError, 'Coordinate reconstruction failed'):
            verify(altered)
