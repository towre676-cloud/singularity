#!/usr/bin/env python3
"""Retain or independently replay the FR04 exact affine-theta receipt."""
from __future__ import annotations

import argparse
import itertools
import json
from fractions import Fraction
from pathlib import Path

from singularity.graph import Graph
from singularity.pinned_theta import (
    affine_lift_enclosure, affine_boundary_enclosure,
    boundary_enclosure, coefficient_decay_bounds, pinned_coefficient,
    scaled_pinned_coefficient, theta_enclosure,
)

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / 'results' / 'fr04_pinned_theta.json'


def build_receipt():
    graph = Graph(3, [(0, 1), (1, 2)])
    pinning, t = 2, Fraction(3, 4)
    q = t ** (graph.n*graph.n)
    oracle_checks = 0
    for volume in range(5):
        oracle = sum((q ** (sum((h[a]-h[b])**2 for a, b in graph.edges)
                           + pinning*sum(a*a for a in h))
                      for h in itertools.product(range(volume+1), repeat=graph.n)
                      if sum(h) == volume), Fraction())
        assert oracle == pinned_coefficient(graph, volume, pinning, q)
        oracle_checks += 1
    residues = []
    for residue in range(graph.n):
        sequence = [scaled_pinned_coefficient(graph, residue+k*graph.n, pinning, t)
                    for k in range(3)]
        assert sequence[0] < sequence[1] < sequence[2]
        lattice = theta_enclosure(graph, pinning, t, residue, 2)
        boundary = boundary_enclosure(graph, residue+2*graph.n, pinning, t)
        assert lattice.lower <= boundary.upper and boundary.lower <= lattice.upper
        residues.append({'residue': residue,
                         'volumes': [residue+k*graph.n for k in range(3)],
                         'scaled_coefficients': list(map(str, sequence)),
                         'theta_window': lattice.to_dict(),
                         'boundary_interval': boundary.to_dict()})
    reflected = theta_enclosure(graph, pinning, t, 1, 2)
    assert reflected.lower == theta_enclosure(graph, pinning, t, 2, 2).lower
    complete = Graph(3, [(0, 1), (1, 2), (0, 2)])
    path_theta = theta_enclosure(graph, pinning, t, 0, 2)
    complete_theta = theta_enclosure(complete, pinning, t, 0, 2)
    assert complete_theta.upper < path_theta.lower
    decay = coefficient_decay_bounds(graph, 6, pinning, t)
    raw = pinned_coefficient(graph, 6, pinning, q)
    assert decay.lower <= raw <= decay.upper
    half_q = Fraction(1, 2)
    disconnected = Graph(3, [(0, 1)])
    half_path = affine_lift_enclosure(graph, pinning, half_q, 0, 3)
    half_disconnected = affine_lift_enclosure(disconnected, pinning, half_q, 0, 3)
    assert half_path.upper < half_disconnected.lower
    half_residues = []
    for residue in range(graph.n):
        window = affine_lift_enclosure(graph, pinning, half_q, residue, 3)
        boundary = affine_boundary_enclosure(graph, residue+3*graph.n, pinning, half_q)
        assert window.lower <= boundary.upper and boundary.lower <= window.upper
        half_residues.append({'residue': residue, 'window': window.to_dict(),
                              'boundary': boundary.to_dict()})
    assert (affine_lift_enclosure(graph, pinning, half_q, 2, 3).lower
            == half_q**pinning*affine_lift_enclosure(graph, pinning, half_q, 1, 3).lower)
    return {'schema': 'singularity.frontier.pinned-theta/1',
            'graph': graph.to_dict(), 'pinning': pinning, 't': str(t), 'q': str(q),
            'exact_parameter_contract': 'centered q=t^(n^2); affine lifts any rational q',
            'working_q_half_affine_lifts': {
                'q': str(half_q), 'residue_classes': half_residues,
                'equal_order_connected_disconnected_separation': {
                    'path_interval': half_path.to_dict(),
                    'disconnected_graph': disconnected.to_dict(),
                    'disconnected_interval': half_disconnected.to_dict(),
                    'path_upper_below_disconnected_lower': True}},
            'independent_product_box_oracle_checks': oracle_checks,
            'residue_classes': residues,
            'reflection_1_2_exact': True,
            'full_series_inequivalence_certificate': {
                'other_graph': complete.to_dict(), 'residue': 0,
                'other_theta': complete_theta.to_dict(),
                'strictly_below_path_lower_endpoint': True},
            'coefficient_6_decay_bounds': decay.to_dict(),
            'claims': ['necessary_full_series_order_invariant',
                       'residue_affine_theta_limits', 'exact_gaussian_boundary_enclosures'],
            'nonclaims': ['fixed_pinning_completeness', 'full_series_collision',
                          'finite_prefix_equality_implies_full_series_equality']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    receipt = build_receipt()
    if args.check:
        stored = json.loads(RECEIPT.read_text())
        if stored != receipt:
            raise SystemExit('FR04 receipt differs from exact recomputation')
        print('FR04 exact pinned-theta receipt matches')
    else:
        RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        print(f'Wrote {RECEIPT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
