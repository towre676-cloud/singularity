"""Integration tests across the presentation boundary, not algorithm copies."""
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from perfectjet.observatory.examples import example_catalog
from perfectjet.observatory.workbench import evaluate, make_server


class WorkbenchTests(unittest.TestCase):
    def test_original_coordinates_and_action_names_survive_every_adapter(self):
        catalog = example_catalog()
        lab = catalog['branching-lab']['model']
        compiled = evaluate({'model': lab})
        self.assertLess(compiled['reduced_states'], compiled['original_states'])
        request = {'model': lab, 'operation': 'history', 'horizon': '2',
                   'word': '["route", "inspect alpha"]'}
        history = evaluate(request)
        self.assertEqual(history['word'], ['route', 'inspect alpha'])
        self.assertEqual(history['count'], '1')
        self.assertEqual(history['observations'], ['unread', 'alpha', 'bit 0'])
        sample = evaluate({**request, 'word': None, 'sample': True})
        self.assertEqual(sample['word'], history['word'])
        plan = evaluate({'model': lab, 'operation': 'adaptive', 'belief': '0,1,2,3'})
        self.assertEqual((plan['status'], plan['worst_cost']), ('finite', 2))
        pair = evaluate({'model': lab, 'operation': 'pair', 'x': '0', 'y': '1'})
        self.assertEqual((pair['status'], pair['cost']), ('finite', 2))
        for name in ('series', 'closure'):
            out = evaluate({'model': lab, 'operation': name, 'index': '2', 'modulus': '35'})
            self.assertTrue(out['identity_verified'])

    def test_http_session_and_error_contract(self):
        server = make_server(0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(url) as response:
                page = response.read().decode()
            self.assertIn('Exact Observatory', page)
            token = page.split("token='")[1].split("'")[0]
            with self.assertRaises(HTTPError) as denied:
                urlopen(url + '/api/examples')
            self.assertEqual(denied.exception.code, 404)
            request = Request(url + '/api/examples', headers={'X-Observatory-Token': token})
            with urlopen(request) as response:
                catalog = json.load(response)
            model = catalog['irreversible-button']['model']
            headers = {'X-Observatory-Token': token, 'Content-Type': 'application/json'}
            request = Request(url + '/api/evaluate', json.dumps({'operation': 'history',
                              'model': model, 'horizon': 2, 'rank': '999'}).encode(), headers)
            with self.assertRaises(HTTPError) as bad:
                urlopen(request)
            self.assertEqual(bad.exception.code, 400)
            self.assertIn('rank outside population', json.load(bad.exception)['error'])
            request = Request(url + '/api/evaluate', b'{}', {'Content-Type': 'application/json'})
            with self.assertRaises(HTTPError) as denied:
                urlopen(request)
            self.assertEqual(denied.exception.code, 403)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_prefix_destruction_and_pell_original_coordinate_bridge(self):
        catalog = example_catalog()
        model = catalog['irreversible-button']['model']
        request = {'model': model, 'operation': 'adaptive', 'belief': '0,1'}
        self.assertEqual(evaluate({**request, 'prefix': '["reset"]'})['status'], 'infinite')
        after_inspect = evaluate({**request, 'prefix': '["inspect"]'})
        self.assertEqual((after_inspect['worst_cost'], after_inspect['worst_remaining_cost']), (3, 0))
        out = evaluate({'model': catalog['pell-orbit']['model'], 'operation': 'pell-point',
                        'index': str(10**100), 'modulus': '1000000007'})
        self.assertEqual((out['x'], out['y']), ('366654601', '394441112'))
        self.assertTrue(out['norm_preserved'])
        with self.assertRaisesRegex(ValueError, 'JSON object'):
            evaluate({'model': None, 'operation': 'pell-point'})
        large = {'transitions': [[0]*16], 'observations': [0]}
        with self.assertRaisesRegex(ValueError, 'supply a modulus'):
            evaluate({'model': large, 'operation': 'series', 'index': '4000'})

    def test_remote_queries_and_input_guard(self):
        model = example_catalog()['interferometer']['model']
        out = evaluate({'model': model, 'operation': 'series', 'index': str(10**100),
                        'modulus': '1000000007'})
        self.assertEqual(out['coefficient'], '976449876')
        with self.assertRaisesRegex(ValueError, 'supply a modulus'):
            evaluate({'model': model, 'operation': 'series', 'index': str(10**100)})
        with self.assertRaises(ValueError):
            evaluate({'model': model, 'operation': 'history', 'horizon': True})
        with self.assertRaisesRegex(ValueError, 'unknown operation'):
            evaluate({'model': model, 'operation': 'unknown'})


if __name__ == '__main__':
    unittest.main()
