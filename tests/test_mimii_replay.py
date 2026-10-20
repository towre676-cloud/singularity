"""Failure-oriented checks for the independent eight-channel replay verifier."""
import importlib.util
from fractions import Fraction
import hashlib
import gzip
import itertools
import http.client
from pathlib import Path
import tempfile
import unittest
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1]/'applications/sensor_replay/mimii_v1/verify_study.py'
spec = importlib.util.spec_from_file_location('independent_mimii_verifier', MODULE_PATH)
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)
ACQUIRE_PATH = MODULE_PATH.with_name('acquire.py')
acquire_spec = importlib.util.spec_from_file_location('mimii_range_adapter_under_test', ACQUIRE_PATH)
acquire = importlib.util.module_from_spec(acquire_spec)
acquire_spec.loader.exec_module(acquire)


class FinitePanelMathematics(unittest.TestCase):
    def test_nonmonotone_erasure_feasibility_does_not_require_full_to_pass(self):
        # Panel {1,2} and its singleton survivors pass. Adding microphone3
        # introduces bad survivors, so the full panel fails one-erasure safety.
        table = [[Fraction(v)] for v in [1, 1, 1, 0, 0, 0, 1]]
        result = verify.solve_finite(table, [0], Fraction(0), erasures=1, channel_count=3)
        self.assertEqual(result['exact_mask'], 3)
        self.assertNotIn(7, result['feasible_masks'])
        self.assertEqual(result['minimum_cost'], 2)

    def test_empty_survivor_fails_even_when_every_numeric_threshold_is_zero(self):
        table = [[Fraction(0)] for _ in range(7)]
        result = verify.solve_finite(table, [0], Fraction(0), erasures=1, channel_count=3)
        self.assertEqual(result['exact_mask'], 3)
        self.assertTrue(all(m.bit_count() >= 2 for m in result['feasible_masks']))
        self.assertEqual(verify.survivor_masks(1, 1), [0, 1])

    def test_two_point_class_margin_does_not_hide_one_in_sixteen_error(self):
        truth = [0]*16 + [1]*16
        predicted = truth.copy()
        predicted[0] = 1
        recall = verify.binary_score(truth, predicted, label=0)
        self.assertEqual(recall, Fraction(15, 16))
        self.assertLess(recall, Fraction(1)-Fraction(1, 50))
        self.assertEqual(verify.binary_score(truth, predicted), Fraction(31, 32))

    def test_exact_search_preserves_all_tied_optima(self):
        table = [[Fraction(1)] for _ in range(7)]
        result = verify.solve_finite(table, [0], Fraction(0), channel_count=3)
        self.assertEqual(result['exact_mask'], 1)
        self.assertEqual(result['all_minimum_cost_masks'], [1, 2, 4])
        self.assertEqual(result['pruned_greedy_mask'], 1)

    def test_trace_equivalence_does_not_collapse_equal_accuracy_traces(self):
        self.assertEqual(verify.trace_classes([[0, 1], [1, 0], [0, 1]]), [[1, 3], [2]])
        # All three predictions have one correct label under truth[0,0], but
        # only masks1 and3 are observational aliases on this finite trace.
        self.assertEqual([verify.binary_score([0, 0, 1, 1], row)
                          for row in [[0, 1, 1, 0], [1, 0, 0, 1]]], [Fraction(1, 2)]*2)

    def test_missing_class_is_rejected_instead_of_changing_denominator(self):
        with self.assertRaisesRegex(ValueError, 'no declared class'):
            verify.binary_score([0, 0], [0, 1])

    def test_gzip_inventory_fallback_preserves_original_hash_and_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'central_indexes.json'
            original = b'{"archives": [], "exact_bytes": true}\n'
            compressed = Path(str(path)+'.gz')
            compressed.write_bytes(gzip.compress(original, mtime=0))
            self.assertFalse(path.exists())
            self.assertEqual(verify.load(path), {'archives': [], 'exact_bytes': True})
            self.assertEqual(verify.sha(path), hashlib.sha256(original).hexdigest())
            self.assertEqual(verify.read_bytes(path), original)

    def test_changed_lock_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {'protocol_sha256': 'protocol.json', 'features_sha256': 'features.npz',
                     'selector_sha256': 'run_study.py',
                     'selection_snapshot_sha256': 'selection_snapshot.json',
                     'selection_predictions_sha256': 'selection_predictions.npz'}
            for file in files.values():
                (root/file).write_bytes(file.encode())
            lock = {key: verify.sha(root/file) for key, file in files.items()}
            verify.verify_hashes(root, lock)
            (root/'selection_predictions.npz').write_bytes(b'one changed prediction')
            with self.assertRaisesRegex(ValueError, 'Changed locked bytes'):
                verify.verify_hashes(root, lock)

    def test_eighth_microphone_is_included_and_uninformative_ties_use_first_reference(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest('Optional numerical application dependency unavailable')
        # Only microphone8 distinguishes training labels. All other channels
        # produce an exact reference tie and must retain the first label.
        X = np.zeros((3, 8, 13), dtype=float)
        X[1, 7, :] = 2.0
        X[2, 7, :] = 2.0
        data = {'X': X, 'y': np.array([0, 1, 1]),
                'machine_id': np.array(['00', '02', '04']),
                'machine_type': np.array(['valve']*3)}
        protocol = {'machine_types': ['valve'], 'train_ids': ['00', '02'],
                    'selection_ids': ['04'],
                    'features': {'standard_deviation_floor': 1e-9}}
        rows, predictions = verify.replay_predictions(data, protocol, 'selection')
        self.assertEqual(rows.tolist(), [2])
        self.assertEqual(predictions[:, 0].tolist(), [int(bool(m & 128)) for m in range(1, 256)])

    def test_paired_stem_bootstrap_preserves_zero_and_fixed_group_changes(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest('Optional numerical application dependency unavailable')
        truth = np.array([0, 0, 0, 1, 1, 1])
        metadata = {'machine_type': np.array(['valve']*6),
                    'group': np.array(['healthy']*3+['anomalous']*3)}
        unchanged = verify.paired_stem_bootstrap(truth, truth, truth, metadata, ['valve'], repetitions=20)
        self.assertEqual(unchanged.tolist(), [0.0, 0.0])
        # Each fixed stem loses one of its three correct mixtures, giving an
        # exact constant difference -2/6 in every grouped resample.
        reduced = np.array([1, 0, 0, 0, 1, 1])
        changed = verify.paired_stem_bootstrap(truth, reduced, truth, metadata, ['valve'], repetitions=20)
        self.assertEqual(changed.tolist(), [-1/3, -1/3])

    def test_changed_prediction_is_rejected(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest('Optional numerical application dependency unavailable')
        expected = np.array([[0, 1], [1, 0]], dtype=np.uint8)
        changed = expected.copy()
        changed[1, 0] = 0
        with self.assertRaisesRegex(ValueError, 'prediction mismatch'):
            verify.compare_predictions(expected, changed, 'fault injection')


class RecordingIdentityChecks(unittest.TestCase):
    @staticmethod
    def fixture():
        protocol = {'machine_types': ['valve'], 'snr_db': [-6, 0, 6],
                    'train_ids': ['00', '02'], 'selection_ids': ['04'], 'confirmation_ids': ['06'],
                    'states': ['normal', 'abnormal'], 'stems_per_class_id': 1,
                    'selection_namespace': 'test-mimii', 'expected_recordings': 24,
                    'expected_stem_groups': 8, 'maximum_signal_compressed_bytes': 1000,
                    'maximum_uncompressed_bytes': 1000}
        archives, rows = [], []
        for snr in [-6, 0, 6]:
            archive = f'{snr}_dB_valve.zip'
            members = []
            for identity in ['00', '02', '04', '06']:
                for state in ['normal', 'abnormal']:
                    name = f'valve/id_{identity}/{state}/00000000.wav'
                    member = {'name': name, 'header': 0, 'compressed': 1, 'size': 2,
                              'crc32': 0, 'compression': 8, 'flags': 0}
                    members.append(member)
                    rows.append(dict(member, archive=archive, machine_type='valve', id=identity,
                                     state=state, stem='00000000.wav', snr_db=snr,
                                     recording_group=f'valve|{identity}|{state}|00000000.wav'))
            archives.append({'archive': archive, 'members': members})
        return protocol, {'records': rows}, {'archives': archives}

    def test_complete_related_mixtures_are_kept_together(self):
        protocol, plan, indexes = self.fixture()
        result = verify.check_manifest(protocol, plan, indexes)
        self.assertEqual(result['stem_groups'], 8)
        self.assertTrue(result['all_snr_mixtures_grouped'])

    def test_duplicate_mixture_cannot_replace_an_unseen_recording(self):
        protocol, plan, indexes = self.fixture()
        plan['records'][-1] = dict(plan['records'][0])
        with self.assertRaisesRegex(ValueError, 'Repeated recording'):
            verify.check_manifest(protocol, plan, indexes)

    def test_relabelled_machine_cannot_cross_split_under_old_group(self):
        protocol, plan, indexes = self.fixture()
        plan['records'][0]['id'] = '06'
        with self.assertRaisesRegex(ValueError, 'does not preserve identity'):
            verify.check_manifest(protocol, plan, indexes)

    def test_machine_identity_overlap_rejected(self):
        protocol, plan, indexes = self.fixture()
        protocol['confirmation_ids'] = ['04']
        with self.assertRaisesRegex(ValueError, 'Machine ID overlaps'):
            verify.check_manifest(protocol, plan, indexes)


class StrictRangeAdapterChecks(unittest.TestCase):
    class Response:
        def __init__(self, status=206, content_range='bytes 10-13/100', length='4', body=b'abcd'):
            self.status = status
            self.headers = {'Content-Range': content_range, 'Content-Length': length}
            self.body = body
            self.read_sizes = []
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def read(self, count):
            self.read_sizes.append(count)
            return self.body

    def fetch(self, response):
        with mock.patch.object(acquire, 'rate_limit'), mock.patch.object(
                acquire.urllib.request, 'urlopen', return_value=response), mock.patch.object(
                acquire.time, 'sleep'), mock.patch.object(acquire.time, 'monotonic', side_effect=itertools.count(0, 100)):

            return acquire.ranged('https://example.invalid/official.zip', 10, 13, 100)

    def test_ignored_range_is_rejected_before_reading_archive_body(self):
        response = self.Response(status=200, content_range=None, length='100')
        with self.assertRaisesRegex(ValueError, 'requested range'):
            self.fetch(response)
        self.assertEqual(response.read_sizes, [])

    def test_shifted_range_is_rejected_before_reading_body(self):
        response = self.Response(content_range='bytes 11-14/100')
        with self.assertRaisesRegex(ValueError, 'requested range'):
            self.fetch(response)
        self.assertEqual(response.read_sizes, [])

    def test_oversized_content_length_is_rejected_before_reading_body(self):
        response = self.Response(length='10000000000')
        with self.assertRaisesRegex(ValueError, 'Content-Length'):
            self.fetch(response)
        self.assertEqual(response.read_sizes, [])

    def test_truncated_body_is_rejected_with_bounded_read(self):
        response = self.Response(body=b'ab')
        with self.assertRaisesRegex(ConnectionError, 'Short HTTP range body'):
            self.fetch(response)
        self.assertEqual(response.read_sizes, [5]*4)

    def test_short_body_retry_can_recover_with_exact_range(self):
        short = self.Response(body=b'ab')
        complete = self.Response()
        with mock.patch.object(acquire, 'rate_limit'), mock.patch.object(
                acquire.urllib.request, 'urlopen', side_effect=[short, complete]) as network, mock.patch.object(
                acquire.time, 'sleep'), mock.patch.object(acquire.time, 'monotonic', side_effect=itertools.count(0, 100)):
            self.assertEqual(acquire.ranged('https://example.invalid/a.zip', 10, 13, 100), b'abcd')
        self.assertEqual(network.call_count, 2)
        self.assertEqual(short.read_sizes, [5])
        self.assertEqual(complete.read_sizes, [5])

    def test_incomplete_read_is_retried_with_exact_range(self):
        incomplete = self.Response()
        incomplete.read = mock.Mock(side_effect=http.client.IncompleteRead(b'ab', 2))
        complete = self.Response()
        with mock.patch.object(acquire, 'rate_limit'), mock.patch.object(
                acquire.urllib.request, 'urlopen', side_effect=[incomplete, complete]) as network, mock.patch.object(
                acquire.time, 'sleep'), mock.patch.object(acquire.time, 'monotonic', side_effect=itertools.count(0, 100)):
            self.assertEqual(acquire.ranged('https://example.invalid/a.zip', 10, 13, 100), b'abcd')
        self.assertEqual(network.call_count, 2)

    def test_excess_body_is_rejected_with_bounded_read(self):
        response = self.Response(body=b'abcde')
        with self.assertRaisesRegex(ValueError, 'Oversized HTTP range body'):
            self.fetch(response)
        self.assertEqual(response.read_sizes, [5])

    def test_valid_exact_range_succeeds(self):
        response = self.Response()
        self.assertEqual(self.fetch(response), b'abcd')
        self.assertEqual(response.read_sizes, [5])

    def test_oversized_requested_range_is_refused_without_network(self):
        with mock.patch.object(acquire.urllib.request, 'urlopen') as network:
            with self.assertRaisesRegex(ValueError, 'Invalid/budgeted range'):
                acquire.ranged('https://example.invalid/a.zip', 0, acquire.MAX_RANGE, acquire.MAX_RANGE+2)
        network.assert_not_called()

    def test_zip_directory_budget_is_refused_without_network(self):
        archive = acquire.RangeArchive('https://example.invalid/a.zip', 100, budget=3)
        with mock.patch.object(acquire, 'ranged') as network:
            with self.assertRaisesRegex(ValueError, 'directory byte budget'):
                archive.read(4)
        network.assert_not_called()

    def test_unsafe_zip_paths_are_refused_without_network_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            with mock.patch.object(acquire, 'DATA', cache), mock.patch.object(acquire, 'ranged') as network:
                for name in ['../escape.wav', '/absolute.wav', 'valve/../../escape.wav']:
                    with self.subTest(name=name):
                        with self.assertRaisesRegex(ValueError, 'Unsafe archive path'):
                            acquire.acquire_one({'archive': '6_dB_valve.zip', 'name': name,
                                                 'archive_url': 'https://zenodo.org/records/3384388/files/6_dB_valve.zip?download=1'})
            network.assert_not_called()
            self.assertEqual(list(cache.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
