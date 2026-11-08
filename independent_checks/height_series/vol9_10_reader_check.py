"""Run with python -m unittest discover -s independent_checks/height_series -p vol9_10_reader_check.py."""

from collections import Counter
from copy import deepcopy
from fractions import Fraction as F
from itertools import combinations, product
from math import comb
import unittest

from vol9_10_reader import complete_series, extract, reconstruct, unique_object


def record(height, edges=None, n=4):
    result = {
        'schema': 'singularity.height-calculation.v1',
        'graph_class': 'finite_simple_cubic',
        'q_convention': 'vol8_lib',
        'kind': 'height',
        'coefficients': {str(r): dict(p) for r, p in enumerate(height)},
    }
    if edges is not None:
        result.update(connected=True, graph={'n': n, 'edges': list(edges)})
    return result


def tetrahedron(volume):
    edges = list(combinations(range(4), 2))
    height = [Counter() for _ in range(volume + 1)]
    for h in product(range(volume + 1), repeat=4):
        if sum(h) <= volume:
            height[sum(h)][sum((h[u] - h[v]) ** 2 for u, v in edges)] += 1
    return record(height, edges)


def formal_pair(volume, mode, delta):
    # Synthetic valid populations for the sign and model tests, with a
    # prism edge list to exercise connected metadata. These are not prism heights.
    n = 12
    edges = [(start + j, start + (j + 1) % 6) for start in (0, 6) for j in range(6)]
    edges += [(j, j + 6) for j in range(6)]
    a = record([{0: 1}, {3: n}] + [{3*r: comb(n + r - 1, r)} for r in range(2, volume + 1)],
               edges if mode == 'connected' else None, n)
    last = a['coefficients'][str(volume)]
    for e, c in delta.items():
        if c < 0:
            last[e] = last.get(e, 0) - c
    last[3*volume] += comb(n + volume - 1, volume) - sum(last.values())
    b = deepcopy(a)
    for e, c in delta.items():
        p = b['coefficients'][str(volume)]
        p[e] = p.get(e, 0) + c
    return a, b


class ReaderTests(unittest.TestCase):
    def test_panels_and_exact_rational_reconstruction(self):
        for volume, mode, panel, det in (
            (9, 'general', range(1, 20, 2), '-6'),
            (9, 'connected', range(1, 20, 2), '1'),
            (10, 'general', range(0, 27, 2), '40'),
            (10, 'connected', range(2, 25, 2), '1'),
        ):
            with self.subTest(volume=volume, mode=mode):
                observations = [F(i, 7) for i in range(len(panel))]
                result = reconstruct(volume, observations, mode=mode)
                self.assertEqual(result['panel'], list(panel))
                self.assertEqual(result['determinant'], det)
                self.assertEqual(result['delta'], 'B-A')
                self.assertEqual([F(result['difference_polynomial'].get(e, 0)) for e in panel], observations)

    def test_direct_tetrahedron_mixed_records(self):
        for volume in (9, 10):
            a = tetrahedron(volume)
            log, _ = complete_series(a, volume)
            b = deepcopy(a)
            b.update(kind='log', coefficients={str(r): p for r, p in log.items()})
            for mode in ('general', 'connected'):
                out = extract(volume, a, b, mode=mode)
                self.assertEqual(out['difference_polynomial'], {})
                self.assertTrue(out['full_polynomial_reconstructed'])

    def test_sign_and_full_reconstruction(self):
        for r in (9, 10):
            # Independently compute kappa**r, a valid direction in both modes.
            delta = {r + 2*j: (-1)**j * comb(r, j) for j in range(r + 1)}
            for mode in ('general', 'connected'):
                a, b = formal_pair(r, mode, delta)
                self.assertEqual(extract(r, a, b, mode=mode)['difference_polynomial'],
                                 {e: str(c) for e, c in delta.items()})
                self.assertEqual(extract(r, b, a, mode=mode)['difference_polynomial'],
                                 {e: str(-c) for e, c in delta.items()})

    def test_connected_tenth_model_rejects_general_direction(self):
        # kappa**10 * (q**-2-1)**5 has a nonzero constant term.
        delta = {2*j: (-1)**j * comb(15, j) for j in range(16)}
        a, b = formal_pair(10, 'connected', delta)
        self.assertEqual(extract(10, a, b)['difference_polynomial'][0], '1')
        with self.assertRaisesRegex(ValueError, 'inconsistent'):
            extract(10, a, b, mode='connected')

    def test_lower_agreement_and_target_validation(self):
        a, b = formal_pair(9, 'general', {})
        b['coefficients']['8']['24'] = b['coefficients']['8'].pop(24) - 1
        b['coefficients']['8'][26] = 1
        with self.assertRaisesRegex(ValueError, 'disagreement at volume 8'):
            extract(9, a, b)
        a, b = formal_pair(9, 'general', {241: 1, 243: -1})
        with self.assertRaisesRegex(ValueError, 'inconsistent'):
            extract(9, a, b)

    def test_connected_topology_and_order_rejection(self):
        a, b = formal_pair(10, 'connected', {})
        disjoint = [(u + start, v + start) for start in (0, 4, 8) for u, v in combinations(range(4), 2)]
        b['graph']['edges'] = disjoint
        with self.assertRaisesRegex(ValueError, 'connected'):
            extract(10, a, b, mode='connected')
        b['graph'] = tetrahedron(10)['graph']
        with self.assertRaisesRegex(ValueError, 'graph order'):
            extract(10, a, b, mode='connected')

    def test_small_order_exception_rejection(self):
        a = tetrahedron(9)
        b = deepcopy(a)
        p = a['coefficients']['9']
        p[243] -= 1
        p[241] = p.get(241, 0) + 1
        with self.assertRaisesRegex(ValueError, 'small order'):
            extract(9, a, b, mode='connected')

    def test_malformed_and_inexact_inputs(self):
        for bad in (True, 0.5, '1/0'):
            with self.assertRaises(ValueError):
                reconstruct(9, [bad] + [0]*9)
        with self.assertRaises(ValueError):
            reconstruct(9, [0]*9)
        with self.assertRaises(ValueError):
            reconstruct(True, [0]*10)
        with self.assertRaises(ValueError):
            unique_object([('7', 1), ('7', 2)])
        a = tetrahedron(9)
        b = deepcopy(a)
        del b['coefficients']['8']
        with self.assertRaisesRegex(ValueError, 'every complete volume'):
            extract(9, a, b)
        b = deepcopy(a)
        b['coefficients']['9'][True] = 1
        with self.assertRaises(ValueError):
            extract(9, a, b)
        b = deepcopy(a)
        b['coefficients']['9']['243'] = 0.5
        with self.assertRaises(ValueError):
            extract(9, a, b)
        log, _ = complete_series(a, 9)
        b.update(kind='log', coefficients={str(r): p for r, p in log.items()})
        b['coefficients']['9'][243] += F(1, 2)
        b['coefficients']['9'][241] = -F(1, 2)
        with self.assertRaisesRegex(ValueError, 'height population'):
            extract(9, a, b)


if __name__ == '__main__':
    unittest.main()
