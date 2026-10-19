#!/usr/bin/env python3
"""Retain independent finite-population checks of threshold reconstruction."""

from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations, product
import json
from time import perf_counter
from pathlib import Path

from singularity.denominator_recovery import recovery_volume
from singularity.graph import Graph
from singularity.threshold_reconstruction import attach_universal, isolated_factor, reconstruct_threshold

ROOT = Path(__file__).resolve().parents[1]


def direct_graph(word):
    # Construct by explicit sequential attachment, independently of the API.
    edges = []
    for v in range(1, len(word)):
        if word[v]:
            for u in range(v):
                edges.append((u, v))
    return Graph(len(word), edges)


def direct_polynomials(graph, volume, shift):
    rows = []
    for r in range(volume + 1):
        counts = Counter()
        for bars in combinations(range(r + graph.n - 1), graph.n - 1):
            stops = (-1,) + bars + (r + graph.n - 1,)
            heights = tuple(stops[i + 1] - stops[i] - 1 for i in range(graph.n))
            energy = sum((heights[u] - heights[v]) ** 2 for u, v in graph.edges)
            energy += shift * sum(h * h for h in heights)
            counts[energy] += 1
        rows.append(counts)
    return rows


def evaluate(rows, q):
    return tuple(sum((count * q ** energy for energy, count in row.items()), Fraction()) for row in rows)


def build_receipt():
    pinnings = (Fraction(1, 2), Fraction(2, 3), Fraction(5, 6))
    per_order = []
    checks = graphs = 0
    first_collision = []
    target_words = ((0, 1, 0, 0, 0, 0, 1, 1), (0, 1, 1, 0, 1, 1, 1, 0))
    for n in range(1, 11):
        maximum_volume = max(recovery_volume(n, q) for q in pinnings)
        count = 0
        a1_signatures = set()
        for tail in product((0, 1), repeat=n - 1):
            word = (0,) + tail
            graph = direct_graph(word)
            for shift in (0, 2):
                polynomials = direct_polynomials(graph, maximum_volume, shift)
                for q in pinnings:
                    volume = recovery_volume(n, q)
                    prefix = evaluate(polynomials[:volume + 1], q)
                    result = reconstruct_threshold(n, q, prefix, diagonal_shift=shift)
                    if result.creation_word != word or result.graph != graph:
                        raise AssertionError((word, str(q), shift, result.to_dict()))
                    checks += 1
                    if shift == 0 and q == Fraction(1, 2):
                        a1_signatures.add(prefix[1])
                        if word in target_words:
                            first_collision.append({
                                'creation_word': list(word),
                                'degrees': list(graph.degrees),
                                'prefix': [str(value) for value in prefix],
                                'reconstruction': result.to_dict(),
                            })
            count += 1
            graphs += 1
        per_order.append({
            'order': n,
            'creation_words': count,
            'q_half_a1_signatures': len(a1_signatures),
            'recovery_volumes': {str(q): recovery_volume(n, q) for q in pinnings},
        })
    first_collision.sort(key=lambda item: item['creation_word'])
    if len(first_collision) != 2 or first_collision[0]['prefix'][1] != first_collision[1]['prefix'][1]:
        raise AssertionError('retained first-coefficient collision changed')
    from singularity.charges import closure_operator, dominating_block, recover_sequence
    from singularity.terminals import glue_graphs
    closure_examples = []
    for word in target_words:
        interior = direct_graph(word)
        block, terminals = dominating_block(interior)
        for context_name, context in (('terminal_edge', Graph(2, [(0, 1)])), ('shared_neighbor', Graph(3, [(0, 2), (1, 2)]))):
            closed, _ = glue_graphs(block, terminals, context, (0, 1))
            observed = evaluate(direct_polynomials(closed, 3, 0), Fraction(1, 2))
            operator = closure_operator(context, (0, 1), 8, 3, Fraction(1, 2))
            recovered = recover_sequence(observed, operator)
            result = reconstruct_threshold(8, Fraction(1, 2), recovered, diagonal_shift=2)
            if result.creation_word != word:
                raise AssertionError((context_name, word, 'closure inverse mismatch'))
            closure_examples.append({'context': context_name, 'closed_order': closed.n,
                'observed_raw_prefix': [str(value) for value in observed],
                'recovered_interior_A_prefix': [str(value) for value in recovered],
                'reconstructed_creation_word': list(result.creation_word)})
    return {
        'schema': 'singularity.fr05-threshold-reconstruction/1',
        'class_hypothesis': 'threshold graphs, known order',
        'series': 'sum_h x^sum(h) q^(E_G(h)+lambda*sum(h_i^2))',
        'pinnings': [str(q) for q in pinnings],
        'diagonal_shifts': [0, 2],
        'all_creation_words_through_order': 10,
        'graphs': graphs,
        'exact_reconstructions': checks,
        'independent_oracle': 'sequential graph construction, stars-and-bars heights, direct edge energy',
        'per_order': per_order,
        'first_coefficient_collision': first_collision,
        'independent_raw_closure_reconstructions': closure_examples,
        'scope': 'complete promised-class reconstruction; not unrestricted graph completeness; observation cutoff is not an acquisition-cost bound',
    }



def large_algebraic_roundtrips():
    """Machine-specific timings, deliberately separate from census evidence.

    Prefixes use forward identities, so this is an algebraic scale check and
    not a second independent height-population oracle. CI does not rerun it.
    """
    rows = []
    for n in (128, 256, 1000):
        word = (0,) + tuple(i % 2 for i in range(1, n))
        q = Fraction(1, 2)
        volume = recovery_volume(n, q)
        shift = sum(word)
        start = perf_counter()
        prefix = isolated_factor(1, q, volume, shift)
        for i in range(1, n):
            if word[i]:
                shift -= 1
                prefix = attach_universal(prefix, i + 1, 1, q, shift)
            else:
                single = isolated_factor(1, q, volume, shift)
                prefix = tuple(sum((prefix[j] * single[r - j] for j in range(r + 1)), Fraction()) for r in range(volume + 1))
        generation_seconds = perf_counter() - start
        start = perf_counter()
        result = reconstruct_threshold(n, q, prefix)
        decoding_seconds = perf_counter() - start
        if result.creation_word != word:
            raise AssertionError((n, 'large algebraic creation-word mismatch'))
        rows.append({
            'order': n, 'volume': volume, 'q': str(q),
            'generation_seconds': generation_seconds,
            'decoding_seconds': decoding_seconds,
            'maximum_numerator_bits': max(value.numerator.bit_length() for value in prefix),
            'maximum_denominator_bits': max(value.denominator.bit_length() for value in prefix),
            'peeling_steps': len(result.steps),
            'creation_word': '0 followed by alternating 1,0,1,0,...',
        })
    return {'evidence_kind': 'exact forward/inverse algebraic roundtrip, not independent population enumeration',
            'timings': 'wall-clock on this machine; not rerun by --check', 'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--benchmark', action='store_true', help='also retain large algebraic roundtrip timings')
    args = parser.parse_args()
    target = ROOT / 'results/fr05_threshold_reconstruction.json'
    result = build_receipt()
    if args.check:
        retained = json.loads(target.read_text(encoding='utf-8'))
        retained.pop('large_algebraic_roundtrips', None)
        if result != retained:
            raise SystemExit('FR05 retained receipt differs')
        print(f"FR05 checked {result['exact_reconstructions']} reconstructions on {result['graphs']} threshold graphs")
    else:
        if args.benchmark:
            result['large_algebraic_roundtrips'] = large_algebraic_roundtrips()
        target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(target)


if __name__ == '__main__':
    main()
