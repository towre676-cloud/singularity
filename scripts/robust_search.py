#!/usr/bin/env python3
"""Deterministic receipt for cost-bounded robust experiment search (OE07).

Records the amplification, non-attained supremum, dependence-pruning and
separation examples, and the path fixture at budgets 1..6 with
branch-and-bound compared against exhaustive search.  With --check the
retained JSON must match a fresh computation exactly.  Timings and the
interpreter version are printed, not retained.
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

from singularity.graph import Graph  # noqa: E402
from singularity.graph_experiments import BoundaryExperimentSystem  # noqa: E402
from singularity.observability import (OperatorSystem, minimum_distinguishing_experiment,  # noqa: E402
                                       observable_closure)
from singularity.robust_search import (bounded_margin_search, exhaustive_margin_search,  # noqa: E402
                                       margin, matrix_inf_norm)

REPORT = ROOT / 'results' / 'robust_search.json'
HALF = F(1, 2)
PATH = Graph(3, ((0, 1), (1, 2)))


def s(x):
    return None if x is None else str(x)


def summary(result):
    e = result.experiment
    return {'budget': s(result.budget), 'margin': s(result.margin),
            'observation': e.observation, 'word': list(e.word), 'cost': s(e.cost),
            'nodes': result.nodes, 'experiments': result.experiments, 'pruned': result.pruned}


def compare(system, d, noise, budget):
    bb = bounded_margin_search(system, d, noise, budget)
    ex = exhaustive_margin_search(system, d, noise, budget)
    assert bb.margin == ex.margin
    return {'branch_and_bound': summary(bb), 'exhaustive': summary(ex), 'equal_value': True}


def amplification():
    system = OperatorSystem(1, [[[2]]], [[1]])
    cert = observable_closure(system)
    witness = minimum_distinguishing_experiment(system, (1,), cert)
    rows = [compare(system, (1,), (1,), c) for c in range(9)]
    assert all(F(r['branch_and_bound']['margin']) == 2 ** c for c, r in enumerate(rows))
    return {'system': 'n=1, L=(1), M=(2), unit cost, sigma=1, d=(1)',
            'closure_basis_words': [list(e.word) for e in cert.basis],
            'cheapest_witness': {'word': list(witness.word), 'cost': s(witness.cost),
                                 'margin': s(margin(system, 0, witness.word, (1,), (1,)))},
            'bounded_optimum_formula': '2^floor(C)', 'budgets': rows,
            'unrestricted_optimum_exists': False}


def creep():
    system = OperatorSystem(2, [[[1, 1], [0, HALF]]], [[1, 0]])
    readings = [margin(system, 0, (0,) * k, (0, 1), (1,)) for k in range(21)]
    assert readings == [2 - F(2) ** (1 - k) for k in range(21)]
    assert all(r < 2 for r in readings)
    return {'system': 'M=[[1,1],[0,1/2]], L=(1,0), d=(0,1), unit cost, sigma=1',
            'reading_formula': '2 - 2^(1-k)', 'checked_k': [0, 20],
            'readings': [s(r) for r in readings], 'supremum': '2', 'attained': False,
            'matrix_inf_norm': s(matrix_inf_norm(system.operators[0])),
            'budgets': [compare(system, (0, 1), (1,), c) for c in range(7)]}


def separation():
    system = OperatorSystem(2, [[[0, 1], [1, 0]], [[1, 0], [0, 3]]], [[1, 0]])
    d = (0, 1)
    cert = observable_closure(system)
    witness = minimum_distinguishing_experiment(system, d, cert)
    best = bounded_margin_search(system, d, (1,), 2)
    basis_words = [list(e.word) for e in cert.basis]
    assert list(best.experiment.word) not in basis_words
    assert witness.word != best.experiment.word
    return {'system': 'M_0=swap, M_1=diag(1,3), L=(1,0), d=(0,1), unit costs, sigma=1',
            'closure_basis_words': basis_words,
            'cheapest_witness': {'word': list(witness.word), 'cost': s(witness.cost),
                                 'margin': s(margin(system, 0, witness.word, d, (1,)))},
            'bounded_optimum_budget_2': compare(system, d, (1,), 2),
            'optimal_row': [s(x) for x in best.experiment.row],
            'optimal_row_pruned_by_closure': True, 'words_differ': True}


def path_fixture():
    system = BoundaryExperimentSystem(1, HALF)
    ops = system.operator_system(attachment_costs=(2, 1))
    d = tuple(a - b for a, b in zip(system.compile_graph(PATH, (0, 2)), system.compile_graph(PATH, (0, 1))))
    witness = minimum_distinguishing_experiment(ops, d)
    return {'system': 'BoundaryExperimentSystem(1, 1/2), contexts (pendant_leaf_pair, shared_neighbor), '
                      'attachment costs (2, 1), observation costs 0, sigma=1',
            'difference': 'compile(P3,(0,2)) - compile(P3,(0,1))', 'd': [s(x) for x in d],
            'cheapest_witness': {'observation': witness.observation, 'word': list(witness.word),
                                 'cost': s(witness.cost)},
            'budgets': [compare(ops, d, (1, 1), c) for c in range(1, 7)],
            'observed_pattern': '1/4 - 2^-(C+2) for C=1..6 (finite check, not proved)'}


def report():
    return {'schema': 'singularity.robust-search/1',
            'scope': ('Exact finite receipts. Bounded maximum-margin search under a cost budget with '
                      'deterministic additive noise bounds; branch-and-bound uses the proved infinity-norm '
                      'bound and is compared with exhaustive search. No shared-panel optimization.'),
            'amplification': amplification(), 'supremum_not_attained': creep(),
            'dependence_pruning_and_separation': separation(), 'path_fixture': path_fixture()}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    t = time.time()
    payload = report()
    print(f'python {platform.python_version()}; seconds={time.time() - t:.2f}')
    if args.check:
        if not REPORT.exists() or json.loads(REPORT.read_text()) != payload:
            raise SystemExit('retained robust search report is missing or stale')
        print('Robust search matches the retained report')
    else:
        REPORT.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
