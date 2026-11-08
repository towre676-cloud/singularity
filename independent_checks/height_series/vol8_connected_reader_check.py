#!/usr/bin/env python3
"""Connected reader regressions and retained-certificate replay; stdlib only."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction as F

import vol8_reader as reader
import vol8_connected_replay as replay
from vol8_lib import height_series, connected_types, degrees_of, edges_of
from vol8_reader_check import record

HERE = Path(__file__).resolve().parent
CERT = json.loads((HERE/'connected_volume8/connected_certificate.json').read_text())


def graph_record(graph, series=None, kind='log'):
    n, edges = graph
    if series is None:
        series = {r: {} for r in range(1, 9)}
        series[1] = {3: F(n)}
    out = record(series, kind)
    out.update(connected=True, graph={'n': n, 'edges': [list(e) for e in edges]})
    return out


class ConnectedReader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = replay.port_certificate()
        cls.theta = next(w for w in CERT['six_connected_witness_recipes'] if w['name'] == 'Theta223')
        cls.graphs = [replay.materialize(side, cls.port) for side in cls.theta['sides']]

    def test_matrix_matches_retained_certificate(self):
        inv, det = reader.invert(reader.matrix(mode='connected'))
        self.assertEqual(str(det), CERT['panel']['determinant'])
        self.assertEqual([[str(x) for x in row] for row in inv], CERT['panel']['inverse'])
        self.assertEqual(max(sum(map(abs, row)) for row in inv), F(44191, 19786))
        self.assertEqual(reader.CONNECTED_NAMES, tuple(CERT['coordinates']))

    def test_source_rows_and_small_order_exception(self):
        _, keys, ranks = replay.source_check()
        self.assertEqual(ranks['new_rank'], 6)
        self.assertEqual(ranks['connected_large_lower_rank'], 15)
        self.assertEqual(ranks['connected_large_total_rank'], 21)
        self.assertEqual(replay.small_check(), CERT['small_graph_check'])
        self.assertEqual(replay.realization_basis_check(keys), CERT['universal_core_realization'])

    def test_six_retained_recipe_differences_both_modes_and_signs(self):
        # Formal difference fixtures exercise conditional extraction, not absolute
        # graph calculations. Real connected topology is supplied explicitly.
        a = graph_record(self.graphs[0])
        for i, witness in enumerate(CERT['six_connected_witness_recipes']):
            delta = {int(e): -F(x) for e, x in witness['delta_A_minus_B']['8'].items()}
            b = copy.deepcopy(a)
            b['coefficients']['8'] = {str(e): str(x) for e, x in delta.items()}
            got = reader.extract(a, b, mode='connected')['invariant_differences']
            expected = {name: -witness['scale']*int(j == i) for j, name in enumerate(reader.CONNECTED_NAMES)}
            self.assertEqual(got, expected)
            general = reader.extract(a, b)['invariant_differences']
            self.assertEqual(general.pop('S8_12'), 0)
            self.assertEqual(general, got)
            self.assertEqual(reader.extract(b, a, mode='connected')['invariant_differences'],
                             {name: -x for name, x in expected.items()})

    def test_connected_theta_absolute_source_law_calculations(self):
        source, _, _ = replay.source_check()
        records = []
        for graph, side in zip(self.graphs, self.theta['sides']):
            n, edges = graph
            counts = replay.connected_subset_counts(n, edges, 8, root_limit=side['seed_vertices'])
            counts = {h: x for h, x in counts.items() if min(degrees_of(h[1], h[0])) >= 2}
            counts[(1, 0)] = n
            series = {}
            for r in range(1, 9):
                p = {}
                for h, x in counts.items():
                    p = reader.add(p, source[r].get(h, {}), x)
                series[r] = p
            records.append(graph_record(graph, series))
        got = reader.extract(*records, mode='connected')
        self.assertEqual(got['invariant_differences']['Theta223'], -1)
        self.assertEqual(sum(abs(x) for x in got['invariant_differences'].values()), 1)
        self.assertEqual(got['delta'], 'B-A')
        self.assertTrue(got['connected_topology_verified'])
        self.assertEqual(got['omitted_invariant_differences'], {'S8_12': 0})
        general = reader.extract(*records)['invariant_differences']
        self.assertEqual(general.pop('S8_12'), 0)
        self.assertEqual(general, got['invariant_differences'])

    def test_all_small_graphs_actual_height_log_and_zero(self):
        for n in (4, 6, 8):
            for mask in connected_types(n):
                if set(degrees_of(mask, n)) != {3}:
                    continue
                graph = (n, edges_of(mask, n))
                h = height_series(*graph, 8)
                a = graph_record(graph, dict(enumerate(h)), 'height')
                b = graph_record(graph, reader.log_series(a))
                self.assertEqual(set(reader.extract(a, b, mode='connected')['invariant_differences'].values()), {0})

    def test_retained_order12_pair_by_direct_height_enumeration(self):
        from vol7_witnesses import coefficient, coefficient_support
        pair = json.loads((HERE/'vol8_witnesses.json').read_text())['pairs'][0]
        records = []
        for side in ('A', 'B'):
            n, edges = pair['n'], pair[side]['edges']
            h = {r: coefficient(n, edges, r) for r in range(1, 9)}
            self.assertEqual(h[8], coefficient_support(n, edges, 8))
            h[0] = {0: F(1)}
            records.append(graph_record((n, edges), h, 'height'))
        connected = reader.extract(*records, mode='connected')['invariant_differences']
        general = reader.extract(*records)['invariant_differences']
        self.assertEqual(general.pop('S8_12'), 0)
        self.assertEqual(connected, general)
        self.assertTrue(any(connected.values()))

    def test_applicability_and_topology_rejections(self):
        a = graph_record(self.graphs[0])
        for field, value in [('connected', None), ('connected', False), ('connected', 1), ('graph', None)]:
            bad = copy.deepcopy(a); bad[field] = value
            with self.assertRaises(ValueError):
                reader.extract(a, bad, mode='connected')
        k4 = list(edges_of(63, 4))
        disconnected = graph_record((12, k4 + [(x+4,y+4) for x,y in k4] + [(x+8,y+8) for x,y in k4]))
        self.assertEqual(set(reader.extract(disconnected, disconnected)['invariant_differences'].values()), {0})
        with self.assertRaisesRegex(ValueError, 'connected'):
            reader.extract(disconnected, disconnected, mode='connected')
        for edges in [k4+[(0,1)], k4+[(0,0)], k4[:-1], k4+[(0,4)], k4+[(False,2)]]:
            bad = graph_record((4, edges))
            with self.assertRaises(ValueError):
                reader.extract(bad, bad, mode='connected')

    def test_disconnected_seventh_coordinate_cannot_be_dropped(self):
        # Retained general-class witness isolates S8_12 and is incompatible
        # with the connected reduction even if a caller supplies false metadata.
        obs = json.loads((HERE/'vol8_observation.json').read_text())
        w = obs['seven_isolated_observation_witnesses'][4]
        a = graph_record(self.graphs[0]); b = copy.deepcopy(a)
        b['coefficients']['8'] = w['delta_log_coefficients']['8']
        self.assertNotEqual(reader.extract(a, b)['invariant_differences']['S8_12'], 0)
        with self.assertRaisesRegex(ValueError, '6-coordinate'):
            reader.extract(a, b, mode='connected')

    def test_inconsistent_data_rejections(self):
        a = graph_record(self.graphs[0])
        for r in range(1, 8):
            b = copy.deepcopy(a); b['coefficients'][str(r)] = {'3': '1'}
            with self.assertRaises(ValueError):
                reader.extract(a, b, mode='connected')
        b = copy.deepcopy(a); del b['coefficients']['4']
        with self.assertRaises(ValueError):
            reader.extract(a, b, mode='connected')
        for p in [{31: 1}, {0: 1}, reader.reconstruct([F(1,2),0,0,0,0,0], mode='connected')]:
            b = copy.deepcopy(a); b['coefficients']['8'] = {str(e): str(x) for e,x in p.items()}
            with self.assertRaises(ValueError):
                reader.extract(a, b, mode='connected')
        for p in [{'6': 1.0}, {'6': True}, {'06': '1'}, {'-1': '1'}]:
            b = copy.deepcopy(a); b['coefficients']['8'] = p
            with self.assertRaises(ValueError):
                reader.extract(a, b, mode='connected')
        for mode, panel in [('invalid', None), ('connected', (0,1,2,3,4,5)),
                            ('connected', reader.PANEL), ('connected', (6,6,14,18,24,26)),
                            ('connected', ('6',10,14,18,24,26))]:
            with self.assertRaises(ValueError):
                reader.extract(a, a, panel, mode=mode)
        small = graph_record((4, edges_of(63, 4)))
        bad = copy.deepcopy(small)
        bad['coefficients']['8'] = {str(e):str(x) for e,x in reader.factors('connected')[0].items()}
        with self.assertRaisesRegex(ValueError, 'order eight'):
            reader.extract(small, bad, mode='connected')

    def test_cli_defaults_and_unsupported_combinations(self):
        a = graph_record(self.graphs[0])
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'input.json'; p.write_text(json.dumps({'A': a, 'B': a}))
            cmd = [sys.executable, str(HERE/'vol8_reader.py'), str(p)]
            for mode, expected in [('general', reader.PANEL), ('connected', reader.CONNECTED_PANEL)]:
                out = subprocess.run(cmd+['--mode',mode], capture_output=True, text=True, check=True)
                self.assertEqual(json.loads(out.stdout)['panel'], list(expected))
            for extra in [['--panel','tail'], ['--sensitivity']]:
                out = subprocess.run(cmd+['--mode','connected']+extra, capture_output=True, text=True)
                self.assertNotEqual(out.returncode, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
