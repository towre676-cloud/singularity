"""Generate exact arbitrary-sensor certificates in the established reader bases."""
import json
from fractions import Fraction
from itertools import product

from perfectjet.observation_design import (
    certify_l1_sensor_global_optimum,
    coefficient_matrix,
    inverse_infinity_norm,
    invert_with_determinant,
)
from vol9_10_reader import reader_model


V9_CRITICAL_PANEL = (3, 9, 11, 15, 17, 19, 21, 25, 31, 35)
V9_REPLACEMENTS = {
    0: (5, 9, 11, 13, 15, 19, 25, 27, 31, 33),
    1: (5, 9, 13, 15, 17, 21, 25, 27, 29, 35),
    8: (3, 9, 11, 15, 17, 21, 25, 27, 31, 33),
}
V10_OPTIMAL_PANEL = (2, 6, 10, 14, 16, 20, 22, 24, 28, 30, 32, 36, 38, 44)
CONNECTED_DUALS = {
    9: ((3, 9, 11, 15, 17, 21, 25, 27, 31, 35),
        (1, 1, 1, -1, -1, 1, -1, -1, 1, -1)),
    10: ((4, 6, 10, 12, 16, 18, 22, 24, 28, 30, 34, 40),
         (1, -1, 1, 1, -1, -1, 1, 1, -1, -1, 1, -1)),
}


def invert_panel(basis, panel):
    return invert_with_determinant(coefficient_matrix(basis, panel))[0]


def dual_from_signs(inverse, signs):
    return [sum(a * b for a, b in zip(row, signs)) for row in inverse]


def generate(volume, mode):
    original, names, basis, original_inverse, _ = reader_model(volume, mode)
    basis = list(basis)
    dimension = len(names)
    degrees = sorted(set().union(*basis))
    result = {
        'volume': volume,
        'mode': mode,
        'coordinate_names': list(names),
        'coefficient_degrees': degrees,
        'original_panel': list(original),
        'original_decoder': [[str(x) for x in row] for row in original_inverse],
        'original_gain': str(inverse_infinity_norm(original_inverse)),
    }

    if mode == 'connected':
        panel, signs = CONNECTED_DUALS[volume]
        dual = dual_from_signs(invert_panel(basis, panel), signs)
        sensors = [{e: '1'} for e in original]
        decoder = original_inverse
        critical = 1
    elif volume == 10:
        critical = 1
        proof = certify_l1_sensor_global_optimum(
            basis, V10_OPTIMAL_PANEL, critical, names)
        dual = list(map(Fraction, proof['dual_vector']))
        sensors = [{e: '1'} for e in V10_OPTIMAL_PANEL]
        decoder = invert_panel(basis, V10_OPTIMAL_PANEL)
    else:
        critical = 2
        inverse = invert_panel(basis, V9_CRITICAL_PANEL)
        signs = [(x > 0) - (x < 0) for x in inverse[critical]]
        dual = dual_from_signs(inverse, signs)
        sensors, decoder = [], []
        for i in range(dimension):
            panel = V9_REPLACEMENTS.get(i, V9_CRITICAL_PANEL)
            row = invert_panel(basis, panel)[i] if i in V9_REPLACEMENTS else inverse[i]
            cost = sum(map(abs, row))
            sensors.append({e: str(x / cost) for e, x in zip(panel, row) if x})
            decoder.append([cost if i == j else Fraction(0) for j in range(dimension)])
        result['critical_panel'] = list(V9_CRITICAL_PANEL)
        result['critical_panel_decoder'] = [[str(x) for x in row] for row in inverse]

    result.update(
        sensors=sensors,
        decoder=[[str(x) for x in row] for row in decoder],
        gain=str(inverse_infinity_norm(decoder)),
        critical_coordinate=critical,
        dual=[str(x) for x in dual],
    )
    return result


def report():
    return {
        'schema': 'singularity.higher-volume.l1-sensor-certificates.v1',
        'cases': [generate(v, mode) for v, mode in
                  product((9, 10), ('general', 'connected'))],
    }


if __name__ == '__main__':
    print(json.dumps(report(), indent=2))
