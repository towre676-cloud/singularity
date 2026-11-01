#!/usr/bin/env python3
"""Independent source-row, witness, enumeration, and adversarial reader checks."""
import json
from fractions import Fraction as F
from pathlib import Path
from vol8_reader import (PANEL, OPTIMAL_PANEL, NAMES, factors, matrix, invert, extract, log_series,
                         reconstruct, sensitivity, add, mul, optimize)
from vol8_law import rref
from vol8_observation import new_observations

HERE = Path(__file__).resolve().parent


def record(series, kind='log'):
    return {'schema': 'singularity.height-calculation.v1', 'kind': kind,
            'graph_class': 'finite_simple_cubic', 'q_convention': 'vol8_lib',
            'coefficients': {str(r): {str(e): str(x) for e, x in p.items()}
                             for r, p in series.items()}}


def rejected(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError('Invalid input accepted')


def check_sources():
    saved = json.loads((HERE/'vol8_law.json').read_text())
    c = {int(r): {(x['k'], x['mask']): {int(e): F(a) for e, a in x['polynomial'].items()}
                  for x in data} for r, data in saved['reduced_coefficients'].items()}
    keys = sorted({h for data in c.values() for h in data})
    low = [[c[r].get(h, {}).get(e, 0) for h in keys] for r in range(1, 8)
           for e in sorted({e for p in c[r].values() for e in p})]
    rr, piv = rref(low, len(keys))
    natural = saved['natural_observation_basis'][17:]
    coords = [{(x['k'], x['mask']): F(x['coefficient']) for x in n['coordinates']}
              for n in natural]
    # Independently compare every exact source row, modulo the lower observation span.
    for e in sorted({e for p in c[8].values() for e in p} | {e for p in factors() for e in p}):
        row = [c[8].get(h, {}).get(e, 0) -
               sum(p.get(e, 0)*v.get(h, 0) for p, v in zip(factors(), coords)) for h in keys]
        for base, j in zip(rr, piv):
            scale = row[j]
            row = [x-scale*y for x, y in zip(row, base)]
        assert not any(row), e
    inv, det = invert(matrix())
    assert det == 224000
    assert max(abs(x) for row in inv for x in row) == 6
    assert inv[5][-2:] == (F(-1), F(-6))
    assert inv[6][-2:] == (F(1), F(5))
    for i in range(7):
        for j in range(7):
            assert sum(inv[i][k]*matrix()[k][j] for k in range(7)) == (i == j)
    return {'panel': list(PANEL), 'matrix': [[str(x) for x in row] for row in matrix()],
            'inverse': [[str(x) for x in row] for row in inv], 'determinant': str(det),
            'inverse_infinity_norm': str(max(sum(map(abs, row)) for row in inv)),
            'source_row_quotient_check': True, 'lower_rank': len(rr)}


def check_witnesses():
    data = json.loads((HERE/'vol8_observation.json').read_text())
    records = list(data['isolated_eight_core_witnesses'].values()) + data['seven_isolated_observation_witnesses']
    zero = record({r: {} for r in range(1, 9)})
    for witness in records:
        series = {int(r): p for r, p in witness['delta_log_coefficients'].items()}
        other = record({r: {int(e): F(x) for e, x in p.items()} for r, p in series.items()})
        vector = {tuple(map(int, key.split(':'))): x for key, x in witness['core_differences'].items()}
        got = extract(zero, other)['invariant_differences']
        assert list(got.values()) == new_observations(vector)
        assert extract(zero, other, OPTIMAL_PANEL)['invariant_differences'] == got
        assert list(extract(other, zero)['invariant_differences'].values()) == [-x for x in new_observations(vector)]
    weld = json.loads((HERE/'vol8_weld.json').read_text())
    calculations = [record({r: {int(e): F(x) for e, x in g['L'][r].items()}
                            for r in range(9)}, 'height') for g in weld['graphs']]
    got = extract(*calculations)['invariant_differences']
    vector = {tuple(map(int, key.split(':'))): x for key, x in weld['delta_leafless_core_counts'].items()}
    assert list(got.values()) == new_observations(vector)
    return len(records)


def check_graph_pairs():
    from vol7_witnesses import coefficient, coefficient_support
    from vol8_witnesses import motif_data
    count = 0
    for pair in json.loads((HERE/'vol8_witnesses.json').read_text())['pairs']:
        n = pair['n']
        series = []
        for side in ('A', 'B'):
            edges = pair[side]['edges']
            h = {r: {int(e): F(x) for e, x in coefficient(n, edges, r).items()} for r in range(1, 9)}
            assert h[8] == {int(e): F(x) for e, x in coefficient_support(n, edges, 8).items()}
            h[0] = {0: F(1)}
            series.append(record(h, 'height'))
        got = extract(*series)['invariant_differences']
        direct = motif_data(n, pair['A']['edges'], pair['B']['edges'])['delta_leafless_core_counts']
        vector = {tuple(map(int, key.split(':'))): x for key, x in direct.items()}
        assert list(got.values()) == new_observations(vector)
        count += 1
    return count


def check_contracts():
    zero = record({r: {} for r in range(1, 9)})
    for i in range(7):
        v = [int(j == i) for j in range(7)]
        other = record({**{r: {} for r in range(1, 8)}, 8: reconstruct(v)})
        assert list(extract(zero, other)['invariant_differences'].values()) == v
    bad = json.loads(json.dumps(zero)); bad['coefficients']['7'] = {'0': '1'}
    rejected(lambda: extract(zero, bad))
    bad = json.loads(json.dumps(zero)); del bad['coefficients']['3']
    rejected(lambda: extract(zero, bad))
    bad = json.loads(json.dumps(zero)); bad['coefficients']['8'] = {'31': '1'}
    rejected(lambda: extract(zero, bad))
    bad = json.loads(json.dumps(zero)); bad['coefficients']['8'] = {'2': 1.0}
    rejected(lambda: extract(zero, bad))
    bad = record({**{r: {} for r in range(1, 8)}, 8: reconstruct([F(1, 2)]+[0]*6)})
    rejected(lambda: extract(zero, bad))
    # A nontrivial H=exp(L) formal-series round trip audits height/log conversion.
    log = {r: {r: F((-1)**r, r+1)} for r in range(1, 9)}
    h = {0: {0: F(1)}}
    for n in range(1, 9):
        p = {}
        for k in range(1, n+1):
            p = add(p, mul(log[k], h[n-k]), k)
        h[n] = {e: x/n for e, x in p.items()}
    assert log_series(record(h, 'height')) == log
    out = sensitivity([0]*7, [1]*7)
    assert out['status'] == 'numerical_estimate_only'
    assert out['coordinates']['Theta223']['measurement_error_bound_estimate'] == 7
    rejected(lambda: sensitivity([0]*7, [-1]*7))
    rejected(lambda: sensitivity([float('nan')]*7, [1]*7))
    rejected(lambda: invert(matrix((0, 1, 2, 3, 4, 5, 6))))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--enumerate', action='store_true', help='Independently enumerate retained cubic pair heights')
    parser.add_argument('--optimize', action='store_true', help='Repeat exhaustive panel search')
    args = parser.parse_args()
    cert = check_sources()
    cert['witnesses_checked'] = check_witnesses()
    check_contracts()
    if args.enumerate:
        cert['independently_enumerated_pairs'] = check_graph_pairs()
    if args.optimize:
        assert optimize() == json.loads((HERE/'vol8_reader_optimization.json').read_text())
    print(json.dumps(cert, indent=2))


if __name__ == '__main__':
    main()
