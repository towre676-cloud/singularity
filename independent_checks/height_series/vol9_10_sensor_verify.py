"""Replay the certificates with standard-library rational arithmetic alone."""
import json
from fractions import Fraction
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
CASES = {(9, 'general'), (9, 'connected'), (10, 'general'), (10, 'connected')}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact(value):
    require(type(value) in (int, str), 'Expected an exact rational')
    return Fraction(value)


def dot(row, column):
    return sum(a * b for a, b in zip(row, column, strict=True))


def multiply(left, right):
    columns = list(zip(*right, strict=True))
    return [[dot(row, column) for column in columns] for row in left]


def gain(matrix):
    return max(sum(map(abs, row)) for row in matrix)


def square(entries, size):
    require(len(entries) == size and all(len(row) == size for row in entries),
            'Expected a square matrix of the model dimension')
    return [list(map(exact, row)) for row in entries]


def verify_case(case, model):
    degrees = sorted({int(e) for poly in model['basis'] for e, a in poly.items() if exact(a)})
    rows = {e: [exact(p.get(str(e), 0)) for p in model['basis']] for e in degrees}
    size = len(model['names'])
    identity = [[int(i == j) for j in range(size)] for i in range(size)]
    require(case['coefficient_degrees'] == degrees and case['coordinate_names'] == model['names'],
            'Certificate must cover the complete model in its original basis')
    require(case['original_panel'] == model['degrees'], 'Wrong baseline panel')

    original_decoder = square(case['original_decoder'], size)
    original_matrix = [rows.get(e, [0] * size) for e in model['degrees']]
    require(multiply(original_decoder, original_matrix) == identity, 'Baseline inverse failed')
    require(gain(original_decoder) == exact(case['original_gain']), 'Baseline gain failed')

    require(len(case['sensors']) == size, 'Wrong sensor count')
    sensor_matrix = []
    for sensor in case['sensors']:
        weights = {int(e): exact(a) for e, a in sensor.items()}
        require(len(weights) == len(sensor) and weights.keys() <= rows.keys(),
                'Sensor degree outside model support or repeated')
        require(sum(map(abs, weights.values())) <= 1, 'Sensor cost exceeds one')
        sensor_matrix.append([sum(a * rows[e][i] for e, a in weights.items())
                              for i in range(size)])

    decoder = square(case['decoder'], size)
    require(multiply(decoder, sensor_matrix) == identity, 'Coordinate reconstruction failed')
    polynomial_decoder = multiply(list(rows.values()), decoder)
    require(multiply(polynomial_decoder, sensor_matrix) == list(rows.values()),
            'Full polynomial reconstruction failed')

    dual = list(map(exact, case['dual']))
    values = {e: dot(row, dual) for e, row in rows.items()}
    require(all(abs(a) <= 1 for a in values.values()), 'Infeasible dual')
    critical = case['critical_coordinate']
    require(type(critical) is int and 0 <= critical < size, 'Invalid dual coordinate')
    optimum = exact(case['gain'])
    require(optimum == gain(decoder) == dual[critical], 'Primal and dual gains differ')

    if (case['volume'], case['mode']) == (9, 'general'):
        panel = case['critical_panel']
        tight = [e for e, value in values.items() if abs(value) == 1]
        require(panel == tight and len(tight) == size, 'Unexpected tight coefficient set')
        critical_inverse = square(case['critical_panel_decoder'], size)
        require(multiply(critical_inverse, [rows[e] for e in panel]) == identity,
                'Tight coefficient matrix inverse failed')
        require(all(critical_inverse[critical]), 'Critical row lacks full support')
        require(sum(map(abs, critical_inverse[critical])) == optimum,
                'Tight panel critical row does not saturate the bound')
        require(gain(critical_inverse) > optimum, 'Tight panel itself attains the optimum')


def verify(report, model_path=HERE / 'vol9_10_reader_models.json'):
    require(report['schema'] == 'singularity.higher-volume.l1-sensor-certificates.v1',
            'Unsupported certificate schema')
    models = {(m['volume'], m['mode']): m for m in json.loads(model_path.read_text())}
    cases = report['cases']
    require(len(cases) == len(CASES) and {(c['volume'], c['mode']) for c in cases} == CASES,
            'Missing or duplicate certificate case')
    for case in cases:
        verify_case(case, models[case['volume'], case['mode']])


if __name__ == '__main__':
    verify(json.loads(Path(sys.argv[1]).read_text()))
    print('Verified four exact global optima and full-polynomial reconstructions.')
