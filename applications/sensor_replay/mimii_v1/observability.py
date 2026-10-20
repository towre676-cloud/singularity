#!/usr/bin/env python3
"""Conditional empirical-box observability using Singularity's existing core.

The box certificate is a separate sufficient model. It does not characterize
nearest-reference fusion, and box overlap is not physical nonidentifiability.
Only training and selection identities enter these observed-data envelopes.
"""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2] / 'src'))
from singularity.robust_coverage import (coverage_problem, minimum_robust_panel,
    exhaustive_robust_panel, greedy_robust_panel, survives_erasures)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(root=ROOT):
    root = Path(root)
    protocol = json.loads((root/'protocol.json').read_text())
    if digest(root/'protocol.json') != json.loads((root/'freeze_receipt.json').read_text())['protocol_sha256']:
        raise ValueError('Changed frozen protocol')
    data = np.load(root/'features.npz', allow_pickle=False)
    X, y = data['X'], data['y']
    development = np.isin(data['machine_id'], protocol['train_ids'] + protocol['selection_ids'])
    if set(data['machine_id'][development]) & set(protocol['confirmation_ids']):
        raise ValueError('Confirmation leaked into envelopes')
    distinctions, boxes, witnesses = [], [], []
    separating = [[] for _ in range(8)]
    for kind in protocol['machine_types']:
        for snr in protocol['snr_db']:
            context = development & (data['machine_type'] == kind) & (data['snr_db'] == snr)
            lo, hi = [], []
            for label in [0, 1]:
                values = X[context & (y == label)]
                if len(values) == 0:
                    raise ValueError('Empty development class')
                lo.append(values.min(axis=0))
                hi.append(values.max(axis=0))
            label = f'{kind}/snr{snr}/normal-vs-abnormal'
            distinctions.append(label)
            boxes.append({'distinction': label, 'class_min': [v.tolist() for v in lo],
                          'class_max': [v.tolist() for v in hi],
                          'development_rows': np.flatnonzero(context).tolist()})
            for channel in range(8):
                coordinates = np.flatnonzero((hi[0][channel] < lo[1][channel]) |
                                             (hi[1][channel] < lo[0][channel]))
                separating[channel].append(bool(len(coordinates)))
                if len(coordinates):
                    witnesses.append({'distinction': label, 'channel': channel+1,
                                      'strictly_disjoint_coordinates': coordinates.tolist()})
    problem = coverage_problem([1]*8, separating, protocol['channels'], distinctions)
    outcomes = {}
    for requirement in [1, 2, 3]:
        exact = minimum_robust_panel(problem, requirement)
        oracle = exhaustive_robust_panel(problem, requirement)
        greedy = greedy_robust_panel(problem, requirement)
        if (exact.feasible, exact.cost) != (oracle.feasible, oracle.cost):
            raise ValueError('Core and independent exhaustive coverage oracle disagree')
        outcomes[str(requirement)] = {
            'erasures': requirement-1, 'feasible': exact.feasible,
            'minimum_cost': str(exact.cost) if exact.feasible else None,
            'panel': [protocol['channels'][c] for c in exact.panel] if exact.feasible else None,
            'greedy_cost': str(greedy.cost) if greedy.feasible else None,
            'deficient_distinctions': [distinctions[i] for i in exact.deficient],
            'independent_core_oracle_agrees': True,
            'direct_erasure_enumeration': (survives_erasures(problem, exact.panel, requirement-1)
                                          if exact.feasible else None)}
    report = {
        'schema': 'singularity.mimii-observability/1',
        'protocol_sha256': digest(root/'protocol.json'),
        'features_sha256': digest(root/'features.npz'),
        'script_sha256': digest(__file__),
        'development_ids': protocol['train_ids']+protocol['selection_ids'],
        'distinctions': distinctions, 'separates': separating,
        'boxes': boxes, 'coordinate_witnesses': witnesses, 'outcomes': outcomes,
        'boundary': 'Observed min/max envelopes only; no calibrated physical bound. '
                    'Overlap means this sufficient coordinate-box certificate fails. '
                    'It does not establish physical equivalence. Additive-classifier '
                    'erasure robustness is independently enumerated, not inferred from multicover.'}
    (root/'observability.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(outcomes, indent=2))
    return report


if __name__ == '__main__':
    run()
