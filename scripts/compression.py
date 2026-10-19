#!/usr/bin/env python3
"""Exact receipt for family compression of graph states (OE10, SNG-O13/O14).

For budgets R = 1..7 at q = 1/2 it records the formal dimension, the formal
quotient rank, the SNG-O13 cyclicity certificate, the alpha-star family span
against the bound (R+1)(R+2)/2 and its observable part, and the exact star
reconstruction verified on held-out alpha.  Krylov reachable dimensions are
recomputed for R <= 4.  With --check the retained JSON must match.
"""
import argparse
import json
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from singularity.compression import (cyclicity_certificate, independent_star,  # noqa: E402
                                     observable_dimension, reachable_subspace,
                                     star_function_dimension, star_reconstruction)
from singularity.graph_experiments import BoundaryExperimentSystem  # noqa: E402
from singularity.observability import observable_closure  # noqa: E402

REPORT = ROOT / 'results' / 'compression.json'


def rank(rows, n):
    a = [list(r) for r in rows]
    k = 0
    for c in range(n):
        p = next((i for i in range(k, len(a)) if a[i][c]), None)
        if p is None:
            continue
        a[k], a[p] = a[p], a[k]
        for i in range(len(a)):
            if i != k and a[i][c]:
                f = a[i][c] / a[k][c]
                a[i] = [u - f * w for u, w in zip(a[i], a[k])]
        k += 1
    return k


def experiment():
    budgets = []
    for R in range(1, 8):
        system = BoundaryExperimentSystem(R, F(1, 2))
        operators = system.operator_system()
        rows = observable_closure(operators).rows
        d = star_function_dimension(R)
        states = [system.compile_graph(independent_star(a), (0, 1)) for a in range(d + 3)]
        star_reconstruction(system)
        entry = {'max_volume': R, 'formal_dimension': system.dimension, 'formal_quotient': len(rows),
                 'cyclicity_certificate': cyclicity_certificate(system)['full_block_algebra'],
                 'star_bound': d, 'star_span': rank(states, system.dimension),
                 'star_observable': observable_dimension(rows, states),
                 'star_reconstruction_verified_through_alpha': d + 4,
                 'saving_over_formal_quotient': len(rows) - observable_dimension(rows, states)}
        if R <= 4:
            entry['krylov_reachable_from_seeds'] = sorted({len(reachable_subspace(operators, (
                system.compile_graph(independent_star(*seed), (0, 1)),))) for seed in
                [(0, 0, 0, 0, False), (1, 0, 0, 0, False), (0, 2, 1, 0, True)]})
        budgets.append(entry)
    return {'schema': 'singularity.family-compression/1', 'q': '1/2',
            'contexts': ['pendant_leaf_pair', 'shared_neighbor'],
            'family': 'independent stars: alpha leaves at terminal 0 (initial-state family, not attachment-closed)',
            'scope': ('Exact finite receipts. SNG-O13 and SNG-O14 are proved in Chapter 15; equality of the star '
                      'span with its bound is checked here for R <= 7 only.'),
            'budgets': budgets}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    payload = experiment()
    if args.check:
        if not REPORT.exists() or json.loads(REPORT.read_text()) != payload:
            raise SystemExit('retained compression report is missing or stale')
        print('Family compression receipt matches the retained report')
    else:
        REPORT.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
        print(json.dumps([[b['max_volume'], b['formal_dimension'], b['formal_quotient'], b['star_span'],
                           b['star_observable'], b['cyclicity_certificate']] for b in payload['budgets']]))


if __name__ == '__main__':
    main()
