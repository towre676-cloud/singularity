#!/usr/bin/env python3
"""Independent MIMII replay: masked Euclidean vectors and finite enumeration.

This checker imports neither acquisition nor study implementation. CRC/SHA
receipts establish source identity, not authentication or physical generality.
Numerical model replay and exact rational finite-table checks are separate.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FULL = 255
OBJECTIVES = ('nominal', 'nuisance', 'robust', 'erasure_1', 'erasure_2')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_text())


def verify_hashes(root, lock):
    """Verify a recorded hash map; reject omitted or changed payloads."""
    mapping = {
        'protocol_sha256': 'protocol.json', 'features_sha256': 'features.npz',
        'selector_sha256': 'run_study.py', 'script_sha256': 'run_study.py',
        'selection_snapshot_sha256': 'selection_snapshot.json',
        'selection_predictions_sha256': 'selection_predictions.npz',
    }
    required = ['protocol_sha256', 'features_sha256',
                'selection_snapshot_sha256', 'selection_predictions_sha256']
    for name in required:
        require(name in lock, f'Missing lock digest {name}')
    require('selector_sha256' in lock or 'script_sha256' in lock,
            'Lock omits selector source digest')
    for name, file in mapping.items():
        if name in lock:
            require(lock[name] == sha(Path(root)/file), f'Changed locked bytes: {file}')


def check_manifest(protocol, plan, indexes, receipts=None):
    """Audit identity grouping and hash-ranking without acquisition helpers."""
    rows = plan['records']
    types = protocol['machine_types']
    snrs = set(protocol['snr_db'])
    ids_by_split = {phase: set(protocol[phase+'_ids'])
                    for phase in ['train', 'selection', 'confirmation']}
    for a, b in itertools.combinations(ids_by_split, 2):
        require(not ids_by_split[a] & ids_by_split[b], 'Machine ID overlaps splits')
    ids = set().union(*ids_by_split.values())
    require(len(rows) == protocol['expected_recordings'], 'Wrong source recording count')
    seen, groups, strata = set(), defaultdict(set), Counter()
    archive_maps = {}
    available = defaultdict(dict)
    for archive in indexes['archives']:
        archive_maps[archive['archive']] = {m['name']: m for m in archive['members']}
        match = re.fullmatch(r'(-?\d+)_dB_(fan|pump|slider|valve)\.zip', archive['archive'])
        require(match is not None, 'Unrecognized original archive name')
        snr, machine_type = int(match[1]), match[2]
        for member in archive['members']:
            match_member = re.fullmatch(r'(fan|pump|slider|valve)/id_(\d\d)/(normal|abnormal)/([^/]+\.wav)', member['name'])
            if match_member:
                ty, identity, state, stem = match_member.groups()
                require(ty == machine_type, 'Archive machine type mismatch')
                available[(ty, identity, state)].setdefault(snr, set()).add(stem)
    chosen = {}
    for ty, identity, state in itertools.product(types, sorted(ids), protocol['states']):
        key = (ty, identity, state)
        sets = available[key]
        require(snrs <= sets.keys(), 'Missing SNR inventory')
        common = set.intersection(*(sets[s] for s in sorted(snrs)))
        def rank(stem):
            text = '|'.join([protocol['selection_namespace'], ty, identity, state, stem])
            return hashlib.sha256(text.encode('utf-8')).hexdigest(), stem
        require(len(common) >= protocol['stems_per_class_id'], 'Insufficient common source stems')
        chosen[key] = set(sorted(common, key=rank)[:protocol['stems_per_class_id']])
    for row in rows:
        ty, identity, state = row['machine_type'], str(row['id']), row['state']
        stem, snr = row['stem'], int(row['snr_db'])
        require(ty in types and identity in ids and state in protocol['states'] and snr in snrs,
                'Invalid source stratum')
        canonical = '|'.join([ty, identity, state, stem])
        require(row['recording_group'] == canonical, 'Recording group does not preserve identity')
        require(row['name'] == f'{ty}/id_{identity}/{state}/{stem}', 'Source path does not match labels')
        require(stem in chosen[(ty, identity, state)], 'Member violates frozen SHA256 sampling')
        identity_key = (canonical, snr)
        require(identity_key not in seen, 'Repeated recording/SNR identity')
        seen.add(identity_key)
        groups[canonical].add(snr)
        strata[(ty, identity, state, snr)] += 1
        member = archive_maps[row['archive']][row['name']]
        for field in ['header', 'compressed', 'size', 'crc32', 'compression', 'flags']:
            require(row[field] == member[field], f'Member directory mismatch: {field}')
    require(len(groups) == protocol['expected_stem_groups'], 'Wrong source stem-group count')
    require(all(v == snrs for v in groups.values()), 'Related SNR mixtures omitted')
    expected_strata = set(itertools.product(types, sorted(ids), protocol['states'], sorted(snrs)))
    require(set(strata) == expected_strata, 'Missing source strata')
    require(all(v == protocol['stems_per_class_id'] for v in strata.values()), 'Unbalanced frozen subset')
    require(sum(r['compressed'] for r in rows) <= protocol['maximum_signal_compressed_bytes'], 'Compressed budget exceeded')
    require(sum(r['size'] for r in rows) <= protocol['maximum_uncompressed_bytes'], 'Raw budget exceeded')
    if receipts is not None:
        require(len(receipts['records']) == len(rows), 'Missing physical-source receipts')
        for planned, actual in zip(rows, receipts['records']):
            require(all(actual[k] == v for k, v in planned.items()), 'Receipt changed frozen member identity')
            for key in ['raw_sha256', 'compressed_sha256']:
                require(re.fullmatch('[0-9a-f]{64}', actual.get(key, '')) is not None,
                        f'Invalid source receipt {key}')
            fmt = actual['wav_format']
            expected = {'channels': 8, 'sample_rate_hz': 16000,
                        'sample_width_bytes': 2, 'frames': 160000, 'compression': 'NONE'}
            require(all(fmt[k] == v for k, v in expected.items()), 'Invalid original WAV format receipt')
    return {'recordings': len(rows), 'stem_groups': len(groups),
            'hash_ranked_strata': len(strata), 'all_snr_mixtures_grouped': True}


def verify_raw_receipts(root, receipts):
    """Optional independent raw/compressed byte, CRC and WAV-format audit."""
    import io
    import wave
    import zlib
    cache = Path(root).parent/'mimii_data'
    transferred = 0
    for row in receipts['records']:
        compressed = (cache/row['compressed_path']).read_bytes()
        require(len(compressed) == row['compressed'], 'Compressed member length mismatch')
        require(hashlib.sha256(compressed).hexdigest() == row['compressed_sha256'], 'Compressed SHA256 mismatch')
        raw = zlib.decompress(compressed, -15) if row['compression'] == 8 else compressed
        require(len(raw) == row['size'], 'Raw member length mismatch')
        require(zlib.crc32(raw) == row['crc32'], 'Raw member CRC32 mismatch')
        require(hashlib.sha256(raw).hexdigest() == row['raw_sha256'], 'Raw SHA256 mismatch')
        require((cache/row['wav_path']).read_bytes() == raw, 'Extracted WAV differs from official member')
        with wave.open(io.BytesIO(raw), 'rb') as wav:
            require((wav.getnchannels(), wav.getframerate(), wav.getsampwidth(), wav.getnframes(), wav.getcomptype())
                    == (8, 16000, 2, 160000, 'NONE'), 'Raw original WAV format mismatch')
        transferred += len(compressed)
    return {'all_raw_and_compressed_members_rechecked': True,
            'members': len(receipts['records']), 'compressed_member_bytes': transferred,
            'whole_archive_publisher_md5_verified': False}


def binary_score(truth, predicted, positions=None, label=None):
    if positions is None:
        positions = range(len(truth))
    positions = list(positions)
    labels = [label] if label is not None else [0, 1]
    values = []
    for c in labels:
        use = [i for i in positions if int(truth[i]) == c]
        require(bool(use), 'Metric cell has no declared class')
        values.append(Fraction(sum(int(predicted[i]) == c for i in use), len(use)))
    return sum(values)/len(values)


def cell_definitions(types, snrs, metadata):
    """All 41 frozen cells, identified by descriptive keys."""
    n = len(metadata['y'])
    cells = [('pooled/balanced_accuracy', tuple(range(n)), None)]
    for ty in types:
        use = tuple(i for i in range(n) if str(metadata['machine_type'][i]) == ty)
        cells.append((ty+'/balanced_accuracy', use, None))
    for ty in types:
        for snr in snrs:
            use = tuple(i for i in range(n) if str(metadata['machine_type'][i]) == ty
                        and int(metadata['snr_db'][i]) == snr)
            cells.append((f'{ty}/snr{snr}/balanced_accuracy', use, None))
            cells.append((f'{ty}/snr{snr}/recall_normal', use, 0))
            cells.append((f'{ty}/snr{snr}/recall_abnormal', use, 1))
    return cells


def rational_scores(truth, predictions, cells):
    return [[binary_score(truth, p, inds, label) for _, inds, label in cells]
            for p in predictions]


def survivor_masks(mask, erasures):
    """Independent submask scan, including an empty survivor when reachable."""
    require(isinstance(mask, int) and mask >= 0, 'Invalid mask')
    return [s for s in range(mask+1)
            if s & mask == s and (mask ^ s).bit_count() <= erasures]


def active_columns(cells, objective):
    if objective == 'nominal':
        return [i for i, (name, _, _) in enumerate(cells) if '/snr' not in name]
    if objective == 'nuisance':
        return [i for i, (name, _, _) in enumerate(cells) if '/recall_' not in name]
    require(objective in ['robust', 'erasure_1', 'erasure_2'], 'Unknown objective')
    return list(range(len(cells)))


def solve_finite(scores, columns, margin, erasures=0, channel_count=8):
    """Exact cardinality oracle with an independently specified greedy path.

    No upward-closed feasibility assumption is made. Greedy is a comparator;
    pruning scans every submask even when its terminal mask is infeasible.
    """
    full = (1 << channel_count)-1
    require(len(scores) == full, 'Incomplete nonempty-mask score table')
    thresholds = [scores[full-1][c]-margin for c in columns]
    feasible, losses = [], {}
    for mask in range(1, full+1):
        survivors = survivor_masks(mask, erasures)
        losses[mask] = sum((Fraction(1) if survivor == 0 else
                           max(Fraction(0), bound-scores[survivor-1][column]))
                          for survivor in survivors for column, bound in zip(columns, thresholds))
        if 0 not in survivors and losses[mask] == 0:
            feasible.append(mask)
    ordered = sorted(feasible, key=lambda m: (m.bit_count(), m))
    exact = ordered[0] if ordered else None
    terminal, path = 0, []
    while terminal not in feasible and terminal != full:
        options = {terminal | (1 << c) for c in range(channel_count) if not terminal & (1 << c)}
        terminal = min(options, key=lambda m: (losses[m], m))
        path.append(terminal)
    prunable = [m for m in ordered if m & terminal == m]
    return {'exact_mask': exact, 'minimum_cost': None if exact is None else exact.bit_count(),
            'feasible_masks': feasible, 'feasible_count': len(feasible),
            'greedy_mask': terminal, 'greedy_feasible': terminal in feasible,
            'greedy_steps': path, 'pruned_greedy_mask': prunable[0] if prunable else None,
            'all_minimum_cost_masks': [m for m in feasible if exact is not None and m.bit_count() == exact.bit_count()],
            'feasibility_bits': [m in feasible for m in range(1, full+1)]}


def trace_classes(predictions):
    classes = {}
    for mask, row in enumerate(predictions, start=1):
        signature = tuple(int(v) for v in row)
        classes.setdefault(signature, []).append(mask)
    return sorted(classes.values(), key=lambda v: v[0])


def verify_observability(root, data, protocol):
    """Rebuild empirical interval separations and all 256 coverage panels."""
    import numpy as np
    path = Path(root)/'observability.json'
    if not path.exists():
        return False
    saved = load(path)
    X, y = data['X'], data['y']
    use_ids = protocol['train_ids']+protocol['selection_ids']
    separates = [[] for _ in range(8)]
    for ty in protocol['machine_types']:
        for snr in protocol['snr_db']:
            inds = [i for i in range(len(y)) if str(data['machine_id'][i]) in use_ids
                    and str(data['machine_type'][i]) == ty and int(data['snr_db'][i]) == snr]
            for channel in range(8):
                disjoint = False
                for feature in range(13):
                    normal = [float(X[i, channel, feature]) for i in inds if int(y[i]) == 0]
                    abnormal = [float(X[i, channel, feature]) for i in inds if int(y[i]) == 1]
                    if max(normal) < min(abnormal) or max(abnormal) < min(normal):
                        disjoint = True
                separates[channel].append(disjoint)
    require(saved['separates'] == separates, 'Empirical box separation changed')
    for count in [1, 2, 3]:
        eligible = []
        for mask in range(256):
            if all(sum(bool(mask & (1 << channel)) and separates[channel][d]
                       for channel in range(8)) >= count for d in range(12)):
                eligible.append(mask)
        outcome = saved['outcomes'][str(count)]
        require(outcome['feasible'] == bool(eligible), 'Empirical-box feasibility wrong')
        if eligible:
            best_cost = min(m.bit_count() for m in eligible)
            require(Fraction(outcome['minimum_cost']) == best_cost, 'Empirical-box optimum wrong')
            mask = sum(1 << protocol['channels'].index(label) for label in outcome['panel'])
            require(mask in eligible and mask.bit_count() == best_cost, 'Empirical-box witness wrong')
        else:
            deficient = [saved['distinctions'][d] for d in range(12)
                         if sum(separates[channel][d] for channel in range(8)) < count]
            require(outcome['deficient_distinctions'] == deficient, 'Empirical-box deficiency list wrong')
    return True


def replay_predictions(data, protocol, phase):
    """Masked flattened Euclidean arrays, independent of channel decomposition."""
    import numpy as np
    X, truth = data['X'], data['y']
    train = np.flatnonzero(np.isin(data['machine_id'], protocol['train_ids']))
    query = np.flatnonzero(np.isin(data['machine_id'], protocol[phase+'_ids']))
    predictions = np.empty((FULL, len(query)), dtype=np.uint8)
    for ty in protocol['machine_types']:
        refs = train[data['machine_type'][train] == ty]
        local = np.flatnonzero(data['machine_type'][query] == ty)
        asks = query[local]
        mean = X[refs].mean(axis=0)
        scale = np.maximum(X[refs].std(axis=0, ddof=0),
                           protocol['features']['standard_deviation_floor'])
        R, Q = (X[refs]-mean)/scale, (X[asks]-mean)/scale
        # Choose channels by combinations, rather than the study mask loop.
        for size in range(1, 9):
            for chosen in itertools.combinations(range(8), size):
                mask = sum(2**c for c in chosen)
                reference = R[:, chosen, :].reshape(len(refs), -1)
                queries = Q[:, chosen, :].reshape(len(asks), -1)
                distance = np.sum((queries[:, None, :]-reference[None, :, :])**2, axis=2)
                predictions[mask-1, local] = truth[refs][np.argmin(distance, axis=1)]
    return query, predictions


def compare_predictions(expected, actual, label):
    import numpy as np
    require(expected.shape == actual.shape, f'{label} prediction shape differs')
    mismatch = np.argwhere(expected != actual)
    require(len(mismatch) == 0,
            f'{label} prediction mismatch at {mismatch[:5].tolist()}')


def verify(root=ROOT, selection_only=False, raw=False):
    import numpy as np
    root = Path(root)
    protocol = load(root/'protocol.json')
    freeze = load(root/'freeze_receipt.json')
    require(sha(root/'protocol.json') == freeze['protocol_sha256'], 'Protocol freeze mismatch')
    plan = load(root/'source_subset_manifest.json')
    require(plan['protocol_sha256'] == sha(root/'protocol.json'), 'Plan protocol mismatch')
    require(plan['central_indexes_sha256'] == sha(root/'central_indexes.json'), 'Inventory hash mismatch')
    receipts_path = root/'source_receipts.json'
    if not receipts_path.exists():
        receipts_path = root/'acquisition_manifest.json'
    receipts = load(receipts_path)
    provenance = check_manifest(protocol, plan, load(root/'central_indexes.json'), receipts)
    require(receipts['protocol_sha256'] == sha(root/'protocol.json'), 'Source receipt protocol mismatch')
    require(receipts['selected_source_manifest_sha256'] == sha(root/'source_subset_manifest.json'),
            'Source receipt frozen plan mismatch')
    if raw:
        provenance.update(verify_raw_receipts(root, receipts))
    data = np.load(root/'features.npz', allow_pickle=False)
    n = protocol['expected_recordings']
    require(data['X'].shape == (n, 8, 13), 'Feature dimensions differ')
    require(np.isfinite(data['X']).all(), 'Nonfinite features')
    # Identity alignment is checked by original member identity, not classifier output.
    records_by_identity = {(r['name'], int(r['snr_db'])): r for r in receipts['records']}
    seen = set()
    for i in range(n):
        identity = (str(data['name'][i]), int(data['snr_db'][i]))
        require(identity not in seen and identity in records_by_identity, 'Feature identity mismatch')
        seen.add(identity)
        row = records_by_identity[identity]
        for field, source in [('machine_type', 'machine_type'), ('machine_id', 'id'),
                              ('state', 'state'), ('stem', 'stem'), ('group', 'recording_group')]:
            require(str(data[field][i]) == str(row[source]), f'Feature {field} changed')
        require(int(data['y'][i]) == int(row['state'] == 'abnormal'), 'Feature label mismatch')
    feature_provenance = load(root/'feature_provenance.json')
    require(feature_provenance['features_sha256'] == sha(root/'features.npz'), 'Feature provenance hash mismatch')
    require(feature_provenance['protocol_sha256'] == sha(root/'protocol.json'), 'Feature provenance protocol mismatch')
    lock = load(root/'selection_lock.json')
    verify_hashes(root, lock)
    snapshot = load(root/'selection_snapshot.json')
    require(snapshot['protocol_sha256'] == sha(root/'protocol.json'), 'Selection protocol mismatch')
    saved = np.load(root/'selection_predictions.npz', allow_pickle=False)
    rows, predictions = replay_predictions(data, protocol, 'selection')
    require(np.array_equal(rows, saved['rows']), 'Selection row identity differs')
    compare_predictions(predictions, saved['predictions'], 'selection')
    metadata = {k: data[k][rows] for k in ['y', 'machine_type', 'snr_db']}
    cells = cell_definitions(protocol['machine_types'], protocol['snr_db'], metadata)
    scores = rational_scores(data['y'][rows], predictions, cells)
    # The saved constraint order can differ; compare by explicit cell names.
    require(set(snapshot['constraint_names']) == {x[0] for x in cells}, 'Wrong frozen metric cells')
    order = {name: i for i, (name, _, _) in enumerate(cells)}
    require(len(snapshot['all_mask_constraint_values_exact']) == FULL, 'Incomplete saved score table')
    for m, saved_values in enumerate(snapshot['all_mask_constraint_values_exact']):
        require(len(saved_values) == len(cells), 'Incomplete saved metric vector')
        require(all(Fraction(value) == scores[m][order[name]]
                    for name, value in zip(snapshot['constraint_names'], saved_values)),
                f'Wrong exact selection metric for mask {m+1}')
    require(snapshot['selection_observational_equivalence']['prediction_equivalence_classes']
            == trace_classes(predictions), 'Wrong frozen selection equivalence classes')
    choices = {}
    for objective in OBJECTIVES:
        erasures = {'erasure_1': 1, 'erasure_2': 2}.get(objective, 0)
        result = solve_finite(scores, active_columns(cells, objective),
                              Fraction(protocol['margin']), erasures)
        saved_result = snapshot['objectives'][objective]
        for field, value in result.items():
            require(saved_result[field] == value, f'{objective} {field} not independently reproduced')
        expected_thresholds = [max(Fraction(0), scores[FULL-1][c]-Fraction(protocol['margin']))
                               for c in active_columns(cells, objective)]
        by_name = {name: Fraction(value) for name, value in zip(
            [snapshot['constraint_names'][i] for i in range(len(saved_result['thresholds_exact']))],
            saved_result['thresholds_exact'])}
        require(all(by_name[cells[c][0]] == threshold for c, threshold in zip(
            active_columns(cells, objective), expected_thresholds)), 'Wrong fixed full-array thresholds')
        choices[objective] = result['exact_mask']
    report = {'passed': True, 'scope': 'feature-level independent numerical replay and exact finite selection',
              'protocol_sha256': sha(root/'protocol.json'), 'features_sha256': sha(root/'features.npz'),
              'independent_method': 'masked flattened Euclidean differences; cardinality combination enumeration; rational metric and submask oracle; no study/acquisition imports',
              'source_audit': provenance, 'all_255_selection_predictions_recomputed': True,
              'all_41_metric_cells_recomputed': True, 'five_exact_greedy_pruned_objectives_reproduced': True,
              'exact_masks': choices, 'confirmation_checked': False,
              'selection_prediction_equivalence_classes_recomputed': True,
              'empirical_box_coverage_independently_recomputed': verify_observability(root, data, protocol)}
    if not selection_only:
        saved_all = np.load(root/'predictions.npz', allow_pickle=False)
        confirmation_rows, confirmation = replay_predictions(data, protocol, 'confirmation')
        require(np.array_equal(confirmation_rows, saved_all['confirmation_rows']), 'Confirmation row mismatch')
        require(np.array_equal(rows, saved_all['selection_rows']), 'Combined selection row mismatch')
        compare_predictions(predictions, saved_all['selection_predictions'], 'combined selection')
        compare_predictions(confirmation, saved_all['confirmation_predictions'], 'confirmation')
        results = load(root/'results.json')
        require(results['protocol_sha256'] == sha(root/'protocol.json'), 'Results protocol hash mismatch')
        require(results['features_sha256'] == sha(root/'features.npz'), 'Results feature hash mismatch')
        require(results['selection_lock_sha256'] == sha(root/'selection_lock.json'), 'Results lock hash mismatch')
        require(results['predictions_sha256'] == sha(root/'predictions.npz'), 'Results predictions hash mismatch')
        cm = {k: data[k][confirmation_rows] for k in ['y', 'machine_type', 'snr_db']}
        confirmation_cells = cell_definitions(protocol['machine_types'], protocol['snr_db'], cm)
        confirmation_scores = rational_scores(data['y'][confirmation_rows], confirmation, confirmation_cells)
        cf_order = {name: i for i, (name, _, _) in enumerate(confirmation_cells)}
        require(set(results['constraint_names']) == set(cf_order), 'Wrong confirmation metric cells')
        for m, values in enumerate(results['confirmation_all_mask_constraint_values_exact']):
            require(all(Fraction(v) == confirmation_scores[m][cf_order[name]]
                        for name, v in zip(results['constraint_names'], values)),
                    f'Wrong confirmation metric vector at mask {m+1}')
        for name, panel in results['panels'].items():
            m = panel['mask']
            observed = binary_score(data['y'][confirmation_rows], confirmation[m-1])
            require(Fraction(panel['balanced_accuracy_exact']) == observed,
                    f'Wrong confirmation score: {name}')
            recall_columns = [i for i, (cell_name, _, _) in enumerate(confirmation_cells) if '/recall_' in cell_name]
            require(panel['absolute_recall_floor_met'] == all(confirmation_scores[m-1][c] >= Fraction(1, 2)
                                                            for c in recall_columns),
                    f'Wrong absolute recall floor claim: {name}')
            for objective in OBJECTIVES:
                columns = active_columns(confirmation_cells, objective)
                erased = {'erasure_1': 1, 'erasure_2': 2}.get(objective, 0)
                survivors = survivor_masks(m, erased)
                passes = 0 not in survivors and all(
                    confirmation_scores[s-1][c] >= confirmation_scores[FULL-1][c]-Fraction(protocol['margin'])
                    for s in survivors for c in columns)
                require(panel['confirmation_contracts_pass'][objective] == passes,
                        f'Wrong confirmation preservation claim: {name} {objective}')
            for ty in protocol['machine_types']:
                inds = [i for i in range(len(confirmation_rows)) if str(cm['machine_type'][i]) == ty]
                require(Fraction(panel['by_machine_type'][ty]['balanced_accuracy_exact']) ==
                        binary_score(cm['y'], confirmation[m-1], inds), 'Wrong type score')
                for snr in protocol['snr_db']:
                    use = [i for i in inds if int(cm['snr_db'][i]) == snr]
                    saved_cell = panel['by_type_snr'][f'{ty}/snr{snr}']
                    require(Fraction(saved_cell['balanced_accuracy_exact']) ==
                            binary_score(cm['y'], confirmation[m-1], use), 'Wrong type/SNR score')
                    require([Fraction(v) for v in saved_cell['class_recall_exact']] ==
                            [binary_score(cm['y'], confirmation[m-1], use, c) for c in [0, 1]],
                            'Wrong class-specific recall')
        frontier = {(Fraction(row['margin_exact']), row['objective']): row
                    for row in results['margin_sensitivity']}
        expected_frontier = {(Fraction(margin), objective) for margin in protocol['sensitivity']['margins']
                             for objective in OBJECTIVES}
        require(set(frontier) == expected_frontier and len(results['margin_sensitivity']) == len(expected_frontier),
                'Incomplete or repeated sensitivity frontier')
        infinity = float('inf')
        def cost_value(row):
            return infinity if row['minimum_cost'] is None else row['minimum_cost']
        for objective in OBJECTIVES:
            costs = [cost_value(frontier[(margin, objective)])
                     for margin in sorted(Fraction(v) for v in protocol['sensitivity']['margins'])]
            require(all(a >= b for a, b in zip(costs, costs[1:])), 'Cost increases when margin is relaxed')
        for margin in [Fraction(v) for v in protocol['sensitivity']['margins']]:
            costs = [cost_value(frontier[(margin, objective)]) for objective in OBJECTIVES]
            require(all(a <= b for a, b in zip(costs, costs[1:])), 'Cost decreases under a stronger contract')
        for row in results['margin_sensitivity']:
            objective, margin = row['objective'], Fraction(row['margin_exact'])
            oracle = solve_finite(scores, active_columns(cells, objective), margin,
                                  {'erasure_1': 1, 'erasure_2': 2}.get(objective, 0))
            for field in ['exact_mask', 'minimum_cost', 'feasible_count']:
                require(row[field] == oracle[field], 'Wrong margin-sensitivity selection')
        require(len(results['selection_equivalence_classes_on_confirmation']) == len(trace_classes(predictions)),
                'Missing selection-equivalence class')
        for item, equivalent in zip(results['selection_equivalence_classes_on_confirmation'], trace_classes(predictions)):
            require(item['selection_equivalent_masks'] == equivalent, 'Changed frozen equivalence class')
            sub = trace_classes([confirmation[m-1] for m in equivalent])
            subclasses = [[equivalent[i-1] for i in local] for local in sub]
            require(item['confirmation_subclasses'] == subclasses, 'Wrong confirmation alias splitting')
            require(item['split_on_confirmation'] == (len(subclasses) > 1), 'Wrong alias split flag')
        report['confirmation_checked'] = True
        report['all_255_confirmation_predictions_recomputed'] = True
        report['all_reported_confirmation_panel_scores_recomputed'] = True
        report['all_255_confirmation_41_cell_scores_recomputed'] = True
        report['all_reported_preservation_contracts_recomputed'] = True
        report['all_20_margin_sensitivity_optima_recomputed'] = True
        report['nested_robustness_and_margin_cost_frontiers_verified'] = True
        report['all_selection_alias_splits_recomputed'] = True
    path = root/('independent_selection_verification.json' if selection_only else 'independent_verification.json')
    path.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(report, indent=2, sort_keys=True))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--raw', action='store_true', help='Also independently decompress and hash all cached official WAV members')
    parser.add_argument('--selection-only', action='store_true',
                        help='Audit sealed development selection without opening confirmation outcomes')
    args = parser.parse_args()
    verify(args.root, args.selection_only, args.raw)
