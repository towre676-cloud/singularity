#!/usr/bin/env python3
"""Exact ninth- and tenth-order height-series readers. Differences are B - A."""

import argparse
from fractions import Fraction
from functools import lru_cache
import json
from math import comb
from pathlib import Path

from vol8_reader import add, invert, mul, polynomial, rational


def model_key(volume, mode):
    if type(volume) is not int or volume not in (9, 10):
        raise ValueError('Volume must be 9 or 10')
    if mode not in ('general', 'connected'):
        raise ValueError('Mode must be general or connected')
    return volume, mode


@lru_cache(maxsize=4)
def reader_model(volume, mode):
    path = Path(__file__).with_name('vol9_10_reader_models.json')
    model = next(m for m in json.loads(path.read_text())
                 if (m['volume'], m['mode']) == (volume, mode))
    degrees = tuple(model['degrees'])
    names = tuple(model['names'])
    basis = tuple(polynomial(p) for p in model['basis'])
    matrix = [[p.get(e, 0) for p in basis] for e in degrees]
    inverse, determinant = invert(matrix)
    if len(degrees) != len(basis) or len(names) != len(basis) or determinant != Fraction(model['determinant']):
        raise RuntimeError('Invalid built-in height reader model')
    return degrees, names, basis, inverse, determinant


def reconstruct(volume, observations, *, mode='general'):
    """Reconstruct B-A from ordered exact samples, assuming full lower agreement.

    This algebraic entry point has no graph records and cannot check applicability.
    """
    degrees, names, basis, inverse, det = reader_model(*model_key(volume, mode))
    if not isinstance(observations, (tuple, list)) or len(observations) != len(degrees):
        raise ValueError(f'Supply {len(degrees)} ordered coefficient observations')
    try:
        samples = tuple(rational(x) for x in observations)
    except ZeroDivisionError as exc:
        raise ValueError('Observation denominator cannot be zero') from exc
    coordinates = [sum(a * b for a, b in zip(row, samples)) for row in inverse]
    delta = {}
    for value, weight in zip(coordinates, basis):
        delta = add(delta, weight, value)
    return {
        'schema': 'singularity.higher-volume.reconstruction.v1',
        'volume': volume,
        'mode': mode,
        'delta': 'B-A',
        'panel': list(degrees),
        'determinant': str(det),
        'coordinate_basis': 'research' if mode == 'general' else 'measured_coefficients',
        'coordinate_differences': dict(zip(names, map(str, coordinates))),
        'difference_polynomial': {e: str(a) for e, a in sorted(delta.items())},
        'status': 'conditional_panel_reconstruction',
    }


def connected_order(record):
    if record.get('connected') is not True or not isinstance(record.get('graph'), dict):
        raise ValueError('Connected mode requires connected=true and a graph edge list')
    graph = record['graph']
    n, edges = graph.get('n'), graph.get('edges')
    if (type(n) is not int or n < 4 or n % 2 or not isinstance(edges, list)
            or 2 * len(edges) != 3 * n):
        raise ValueError('Invalid finite simple cubic graph')
    adj = [set() for _ in range(n)]
    for edge in edges:
        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            raise ValueError('Edges must be endpoint pairs')
        u, v = edge
        if (type(u) is not int or type(v) is not int or not 0 <= u < n
                or not 0 <= v < n or u == v or v in adj[u]):
            raise ValueError('Invalid endpoint, loop or duplicate edge')
        adj[u].add(v)
        adj[v].add(u)
    if any(len(row) != 3 for row in adj):
        raise ValueError('Graph must be cubic')
    seen, pending = {0}, [0]
    while pending:
        for v in adj[pending.pop()] - seen:
            seen.add(v)
            pending.append(v)
    if len(seen) != n:
        raise ValueError('Graph must be connected')
    return n


def check_population(p, n, r):
    total = comb(n + r - 1, r) if n else int(r == 0)
    if any(c < 0 or c.denominator != 1 for c in p.values()) or sum(p.values()) != total:
        raise ValueError(f'Invalid height population at volume {r}')


def complete_series(record, volume):
    if not isinstance(record, dict) or record.get('schema') != 'singularity.height-calculation.v1':
        raise ValueError('Unsupported calculation schema')
    if record.get('graph_class') != 'finite_simple_cubic' or record.get('q_convention') != 'vol8_lib':
        raise ValueError('Require finite simple cubic graphs and vol8_lib q convention')
    kind = record.get('kind')
    if kind not in ('height', 'log'):
        raise ValueError('Kind must be height or log')
    raw = record.get('coefficients')
    required = range(0 if kind == 'height' else 1, volume + 1)
    if not isinstance(raw, dict) or set(raw) != {str(r) for r in required}:
        raise ValueError(f'Supply every complete volume through {volume}, with no extra volumes')
    try:
        series = {r: polynomial(raw[str(r)]) for r in required}
    except ZeroDivisionError as exc:
        raise ValueError('Coefficient denominator cannot be zero') from exc
    order = series[1].get(3, Fraction(0))
    if (set(series[1]) - {3} or order.denominator != 1
            or order < 0 or order == 2 or order % 2):
        raise ValueError('Volume one must be n*q^3 for a valid cubic graph order n')
    n = int(order)
    for r, p in series.items():
        if any(e % 2 != r % 2 or e > 3 * r * r for e in p):
            raise ValueError(f'Invalid energy degree at volume {r}')
        if kind == 'height':
            check_population(p, n, r)
        elif sum(p.values()) != Fraction(n, r):
            raise ValueError(f'Invalid log specialization at volume {r}')
    if kind == 'log':
        # A rational log input must exponentiate to a counting series.
        height = {0: {0: Fraction(1)}}
        for r in range(1, volume + 1):
            p = {}
            for k in range(1, r + 1):
                p = add(p, mul(series[k], height[r - k]), k)
            height[r] = {e: a / r for e, a in p.items()}
            check_population(height[r], n, r)
        return series, n
    log = {}
    for r in range(1, volume + 1):
        p = {e: r * a for e, a in series[r].items()}
        for k in range(1, r):
            p = add(p, mul(log[k], series[r - k]), -k)
        log[r] = {e: a / r for e, a in p.items()}
    return log, n


def extract(volume, a, b, *, mode='general'):
    """Check complete compatible records and reconstruct their B-A difference."""
    degrees, _, _, _, _ = reader_model(*model_key(volume, mode))
    left, left_n = complete_series(a, volume)
    right, right_n = complete_series(b, volume)
    if mode == 'connected' and (connected_order(a) != left_n or connected_order(b) != right_n):
        raise ValueError('Volume one disagrees with supplied graph order')
    for r in range(1, volume):
        if left[r] != right[r]:
            raise ValueError(f'Lower-order disagreement at volume {r}')
    delta = add(right[volume], left[volume], -1)
    if mode == 'connected' and left_n <= volume and delta:
        raise ValueError('Compatible connected graphs of this small order must have zero difference')
    if any(c.denominator != 1 for c in delta.values()):
        raise ValueError('A compatible height difference must have integral coefficients')
    result = reconstruct(volume, [delta.get(e, 0) for e in degrees], mode=mode)
    if polynomial(result['difference_polynomial']) != delta:
        raise ValueError(f'Target polynomial is inconsistent with the {mode} model')
    result.update(schema='singularity.higher-volume.extraction.v1',
                  status='exact_algebraic_certificate',
                  scope='conditional on supplied complete cubic-graph calculations being correct',
                  full_polynomial_reconstructed=True)
    if mode == 'connected':
        result['connected_topology_verified'] = True
    return result


def unique_object(items):
    result = dict(items)
    if len(items) != len(result):
        raise ValueError('Duplicate JSON key')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('volume', type=int, choices=(9, 10))
    parser.add_argument('input', type=Path, help='JSON with A and B calculation records')
    parser.add_argument('--mode', choices=('general', 'connected'), default='general')
    args = parser.parse_args()
    try:
        records = json.loads(args.input.read_text(), object_pairs_hook=unique_object)
        if not isinstance(records, dict) or set(records) != {'A', 'B'}:
            raise ValueError('Input must contain exactly the records A and B')
        out = extract(args.volume, records['A'], records['B'], mode=args.mode)
    except (OSError, ValueError, ZeroDivisionError) as exc:
        parser.error(str(exc))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
