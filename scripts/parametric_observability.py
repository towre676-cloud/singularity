#!/usr/bin/env python3
"""Deterministic receipt for parameter-aware observability (OE09).

For the standard two-context graph language at budgets R = 1..4 it computes,
with q symbolic: the generic rank over Q(q), the determinantal divisor D_r of
the matrix of all experiment rows of length <= n-1 (from a Hermite basis of
its Q[q]-row module), the factorization of D_r over Q with irreducibility
certificates, the exceptional parameters in (0,1) and in R, and exact replays
with observable_closure at every rational exceptional value.  It also checks
the q = 1/2 specialization against BoundaryExperimentSystem, ranks at sampled
parameters, and two synthetic systems: one whose generic basis drops rank at
q = 0 while the true rank does not, and one with an irrational exceptional
parameter certified over a number field.

With --check the retained JSON must match exactly.  Timings and interpreter
versions are printed, not retained.
"""
import argparse
import json
import platform
import sys
import time
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from singularity.graph_experiments import BoundaryExperimentSystem  # noqa: E402
from singularity.observability import observable_closure  # noqa: E402
from singularity.parametric import (PolynomialOperatorSystem, factor_over_q,  # noqa: E402
                                    observation_module, parametric_observability,
                                    polynomial_json, rank_at_rational, symbolic_boundary_system,
                                    _determinantal_divisor_dense, _poly_str, _from_dict)

REPORT = ROOT / 'results' / 'parametric_observability.json'
BUDGETS = (1, 2, 3, 4)
BASIS_DIVISOR_BUDGET = 3  # D_r of the generic basis matrix is costly at R = 4
SAMPLES = (F(-2), F(-1), F(-1, 2), F(0), F(1, 3), F(1, 2), F(2, 3), F(1), F(2))


def s(x):
    return f'{x.numerator}/{x.denominator}'


def graph_budget(R, timings):
    t = time.time()
    coordinates, system = symbolic_boundary_system(R)
    report = parametric_observability(system, basis_divisor=R <= BASIS_DIVISOR_BUDGET)
    timings[f'R{R}_analysis'] = time.time() - t
    t = time.time()
    half = BoundaryExperimentSystem(R, F(1, 2))
    special = system.specialize(F(1, 2))
    reference = half.operator_system()
    matrices_identical = (special.operators == reference.operators
                          and special.observations == reference.observations
                          and special.dimension == reference.dimension)
    rank_half = observable_closure(reference).rank
    module = observation_module(system)
    W = module.at_length_bound
    D = _determinantal_divisor_dense(W, len(W))
    samples = []
    for q0 in SAMPLES:
        closure_rank = observable_closure(system.specialize(q0)).rank
        d_zero = sum(c * q0 ** k for k, c in enumerate(D)) == 0
        samples.append({'q': s(q0), 'closure_rank': closure_rank, 'module_rank': rank_at_rational(W, q0),
                        'D_r_vanishes': d_zero,
                        'consistent': (closure_rank == report['generic_rank']) == (not d_zero)})
    timings[f'R{R}_crosscheck'] = time.time() - t
    report.update({
        'budget': R,
        'coordinates': [[list(o), v] for o, v in coordinates],
        'D_r_coefficients': polynomial_json(D),
        'q_half_matrices_identical_to_BoundaryExperimentSystem': matrices_identical,
        'q_half_closure_rank': rank_half,
        'sampled_specializations': samples,
    })
    return report


def basis_drop_example():
    """Generic basis {L1, L2} has D_2(B) = q, but L1 M restores rank 2 at q = 0."""
    system = PolynomialOperatorSystem(2, [[[0, 1], [0, 0]]], [[1, 0], [0, {1: 1}]])
    report = parametric_observability(system)
    zero = observable_closure(system.specialize(0))
    return {'system': 'n=2, L1=(1,0), L2=(0,q), M=[[0,1],[0,0]]',
            'generic_rank': report['generic_rank'],
            'generic_basis_words': report['generic_basis_words'],
            'generic_basis_D_r_factors': report['generic_basis_D_r_factors'],
            'D_r_factors': report['D_r_factors'],
            'spurious': report['generic_basis_spurious_factors'],
            'closure_at_q0_rank': zero.rank,
            'closure_at_q0_words': [[e.observation, list(e.word)] for e in zero.basis]}


def algebraic_example():
    """D_2 = (2q-1)(q^2+q-1): exceptional at 1/2 and at (sqrt 5 - 1)/2 in (0,1)."""
    entry = {0: 1, 1: -3, 2: 1, 3: 2}  # (2q - 1)(q^2 + q - 1) = 2q^3 + q^2 - 3q + 1
    system = PolynomialOperatorSystem(2, [[[0, entry], [0, 0]]], [[1, 0]])
    report = parametric_observability(system)
    lead, factors = factor_over_q(entry)
    return {'system': 'n=2, L=(1,0), M=[[0,(2q-1)(q^2+q-1)],[0,0]]',
            'generic_rank': report['generic_rank'],
            'D_r_factors': report['D_r_factors'],
            'exceptional_open_unit': report['exceptional_open_unit'],
            'exceptional_real': report['exceptional_real'],
            'factor_check': [[_poly_str(_from_dict(g)), i] for g, i, _ in factors] + [s(lead)]}


def payload(timings):
    graphs = [graph_budget(R, timings) for R in BUDGETS]
    for g in graphs:
        assert g['q_half_matrices_identical_to_BoundaryExperimentSystem']
        assert g['q_half_closure_rank'] == g['generic_rank']
        assert all(x['consistent'] and x['closure_rank'] == x['module_rank'] for x in g['sampled_specializations'])
        assert all(x.get('rank_drop_confirmed') for x in g['exceptional_real'])
    return {
        'schema': 'singularity.parametric-observability/1',
        'contexts': 'standard_attachments(): pendant_leaf_pair, shared_neighbor; unit attachment costs',
        'budgets': list(BUDGETS),
        'graph': graphs,
        'basis_drop_example': basis_drop_example(),
        'algebraic_example': algebraic_example(),
        'scope': ('exact computation over the declared finite population (standard contexts, R <= 4); '
                  'rank statements at all q follow from the determinantal-divisor theorem, not from sampling'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    timings = {}
    data = payload(timings)
    print(f'python {platform.python_version()}; seconds ' + ', '.join(f'{k}={v:.2f}' for k, v in timings.items()))
    for g in data['graph']:
        print(f"R={g['budget']}: n={g['dimension']} generic rank {g['generic_rank']}, deg D_r {g['D_r_degree']}, "
              f"exceptional in (0,1): {len(g['exceptional_open_unit'])}, real: "
              f"{[x.get('value', x.get('isolating_interval')) for x in g['exceptional_real']]}")
    if args.check:
        if not REPORT.exists() or json.loads(REPORT.read_text()) != data:
            raise SystemExit('retained parametric observability report is missing or stale')
        print('Parametric observability matches the retained report')
    else:
        REPORT.write_text(json.dumps(data, indent=1, sort_keys=True) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
