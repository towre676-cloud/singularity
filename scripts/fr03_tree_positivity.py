#!/usr/bin/env python3
"""Retain/replay FR03 exact tree-minor evidence; standard library only."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

from singularity.graph import Graph
from singularity.tree_positivity import (
    boxed_tree_kernel, consecutive_minor_lead, distance_minor_lead, exact_determinant,
)

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / 'results' / 'fr03_tree_positivity.json'


def compositions(total, length):
    if length == 0:
        if total == 0:
            yield ()
    elif length == 1:
        yield (total,)
    else:
        for h in range(total + 1):
            for rest in compositions(total - h, length - 1):
                yield (h,) + rest


def prufer_tree(n, code):
    degrees = [1] * n
    for v in code:
        degrees[v] += 1
    edges = []
    for v in code:
        leaf = next(i for i, degree in enumerate(degrees) if degree == 1)
        edges.append((leaf, v))
        degrees[leaf] -= 1
        degrees[v] -= 1
    edges.append(tuple(i for i, degree in enumerate(degrees) if degree == 1))
    return Graph(n, edges)


def determinant_series_oracle(tree, terminals, order, budget, q):
    """No tree DP or leading-formula implementation: enumerate assignments."""
    interior = [v for v in range(tree.n) if v not in terminals]
    entries = {}
    for s, t in itertools.product(range(order), repeat=2):
        row = []
        for volume in range(budget + 1):
            value = Fraction()
            for profile in compositions(volume, len(interior)):
                heights = [0] * tree.n
                heights[terminals[0]], heights[terminals[1]] = s, t
                for v, h in zip(interior, profile):
                    heights[v] = h
                value += q ** tree.energy(heights)
            row.append(value)
        entries[s, t] = row
    determinant = [Fraction()] * (budget + 1)
    for permutation in itertools.permutations(range(order)):
        sign = (-1) ** sum(permutation[i] > permutation[j]
                           for i in range(order) for j in range(i + 1, order))
        product = [Fraction(1)] + [Fraction()] * budget
        for i, j in enumerate(permutation):
            product = [sum((product[a] * entries[i, j][r-a] for a in range(r+1)), Fraction())
                       for r in range(budget+1)]
        determinant = [a + sign*b for a, b in zip(determinant, product)]
    return determinant


def build_receipt():
    q = Fraction(1, 2)
    census = []
    digest = hashlib.sha256()
    for n in range(2, 6):
        tree_count = pair_count = 0
        for code in itertools.product(range(n), repeat=n - 2):
            tree = prufer_tree(n, code)
            tree_count += 1
            for terminals in itertools.combinations(range(n), 2):
                predicted = distance_minor_lead(tree, terminals, q)
                actual = determinant_series_oracle(tree, terminals, 2, predicted['first_volume'], q)
                if any(actual[:-1]) or actual[-1] != predicted['coefficient']:
                    raise AssertionError((tree, terminals, predicted, actual))
                digest.update(json.dumps([n, code, terminals, predicted['distance'],
                                          predicted['off_path_edges'], str(actual[-1])],
                                         separators=(',', ':')).encode())
                digest.update(b'\n')
                pair_count += 1
        census.append({'vertices': n, 'labeled_trees': tree_count, 'terminal_pairs': pair_count})
    worked = []
    for name, tree, terminals, order, q0 in [
        ('bare_path_order_2', Graph(4, [(0,1),(1,2),(2,3)]), (0,3), 2, q),
        ('branched_path_order_2', Graph(8, [(0,1),(1,2),(2,3),(0,4),(1,5),(2,6),(3,7)]),
         (0,3), 2, Fraction(2,3)),
        ('path_order_3', Graph(3, [(0,1),(1,2)]), (0,2), 3, Fraction(2,3)),
        ('path_order_4', Graph(3, [(0,1),(1,2)]), (0,2), 4, Fraction(2,3)),
    ]:
        predicted = consecutive_minor_lead(tree, terminals, q0, order)
        actual = determinant_series_oracle(tree, terminals, order, predicted['first_volume'], q0)
        if any(actual[:-1]) or actual[-1] != predicted['coefficient']:
            raise AssertionError((name, predicted, actual))
        worked.append({'name': name, 'graph': tree.to_dict(), 'terminals': list(terminals),
                       'q': str(q0), 'order': order, 'distance': predicted['distance'],
                       'off_path_edges': predicted['off_path_edges'],
                       'first_volume': predicted['first_volume'], 'coefficient': str(actual[-1])})
    tree = Graph(5, [(0,1),(1,2),(2,3),(1,4)])
    box = boxed_tree_kernel(tree, (0,3), (0,1,2), (0,1,2), 2, Fraction(1,3), q)
    box_det = exact_determinant(box)
    if box_det <= 0:
        raise AssertionError('box minor failed positivity')
    x = Fraction(1,3)
    volume_one = [[q ** (s*s+t*t) * (1+x*q*q*(q**(-2*s)+q**(-2*t)))
                   for t in (0,1)] for s in (0,1)]
    negative = exact_determinant(volume_one)
    if negative != -x*x*q*q*(1-q*q)**2 or negative >= 0:
        raise AssertionError('volume counterexample failed')
    return {
        'format': 'singularity.fr03.tree-positivity/1',
        'scope': 'ordered tree kernels; no symmetrized-interface rejection claim',
        'census': census,
        'total_labeled_trees': sum(row['labeled_trees'] for row in census),
        'total_terminal_pairs': sum(row['terminal_pairs'] for row in census),
        'ordered_census_sha256': digest.hexdigest(),
        'oracle': 'direct weak compositions and permutation determinant; independent of tree messages',
        'worked_leading_minors': worked,
        'box_minor': {'graph': tree.to_dict(), 'terminals': [0,3], 'pins': [0,1,2],
                      'height_bound': 2, 'x': str(x), 'q': str(q),
                      'matrix': [[str(v) for v in row] for row in box], 'determinant': str(box_det)},
        'negative_volume_cutoff_example': {'graph': Graph(4, [(0,1),(1,2),(2,3)]).to_dict(),
                                         'terminals': [0,3], 'pins': [0,1],
                                         'interior_volume_cutoff': 1, 'x': str(x), 'q': str(q),
                                         'determinant': str(negative)},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='recompute and compare retained JSON')
    args = parser.parse_args()
    actual = build_receipt()
    if args.check:
        retained = json.loads(RECEIPT.read_text())
        if retained != actual:
            raise SystemExit('FR03 retained receipt differs; regenerate without --check')
        print(f"FR03 verified: {actual['total_labeled_trees']} labeled trees, "
              f"{actual['total_terminal_pairs']} terminal pairs; box and higher-minor fixtures match")
    else:
        RECEIPT.write_text(json.dumps(actual, indent=2, sort_keys=True) + '\n')
        print(RECEIPT)


if __name__ == '__main__':
    main()
