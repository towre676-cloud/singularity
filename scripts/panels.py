#!/usr/bin/env python3
"""Deterministic receipt for shared experiment panels (OE08).

Graph instance: BoundaryExperimentSystem(3, 1/2), attachment costs (2, 1),
six 3-vertex two-terminal candidates, the complete pool of experiments of
cost <= 4.  Every pool reading is rechecked by direct height enumeration
on the assembled glued graph.  Also retains the seeded comparison of
branch and bound with the exhaustive oracle and the greedy gaps, and the
exact equality and l2-versus-box examples.  With --check the retained
results/panels.json must match exactly.  Timings are printed, not retained.
"""
import argparse
import json
import platform
import random
import sys
import time
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from singularity.graph import Graph  # noqa: E402
from singularity.graph_experiments import BoundaryExperimentSystem  # noqa: E402
from singularity.panels import (ambiguous_reading, candidate_pairs,  # noqa: E402
                                certifies_identification, consistent_candidates,
                                exhaustive_minimum_panel, experiment_pool, greedy_panel,
                                l2_ambiguous_reading, l2_certifies, minimum_cost_l2_panel,
                                minimum_cost_panel, pairwise_cheapest_witnesses, reading_pool)

REPORT = ROOT / 'results' / 'panels.json'
R, Q, COSTS, BUDGET = 3, F(1, 2), (2, 1), 4
P3 = Graph(3, ((0, 1), (1, 2)))
K3 = Graph(3, ((0, 1), (0, 2), (1, 2)))
EI = Graph(3, ((0, 1),))
FAMILY = [('path 0-1-2, terminals (0,2)', P3, (0, 2)),
          ('path 0-1-2, terminals (0,1)', P3, (0, 1)),
          ('path 0-1-2, terminals (1,2)', P3, (1, 2)),
          ('triangle, terminals (0,1)', K3, (0, 1)),
          ('edge 01 + isolated 2, terminals (0,1)', EI, (0, 1)),
          ('edge 01 + isolated 2, terminals (0,2)', EI, (0, 2))]


def s(x):
    return None if x is None else str(x)


def describe(pool, result, names):
    if not result.feasible:
        return {'feasible': False, 'uncoverable_pairs': [[names[a], names[b]] for a, b in result.uncoverable]}
    return {'feasible': True, 'cost': s(result.cost), 'nodes': result.nodes,
            'root_lower_bound': s(result.root_lower_bound),
            'panel': [{'observation_volume': pool.labels[i][0], 'word': list(pool.labels[i][1]),
                       'cost': s(pool.costs[i])} for i in result.panel]}


def graph_instance(timings):
    t = time.time()
    system = BoundaryExperimentSystem(R, Q)
    ops = system.operator_system(list(COSTS))
    states = [system.compile_graph(g, term) for _, g, term in FAMILY]
    names = [n for n, _, _ in FAMILY]
    pool = experiment_pool(ops, states, BUDGET)
    timings['compile_and_pool'] = time.time() - t
    t = time.time()
    direct, checked = {}, 0
    for e, (j, w) in enumerate(pool.labels):
        for c, (_, g, term) in enumerate(FAMILY):
            if (c, w) not in direct:
                direct[c, w] = system.direct_observations(g, term, w)
            assert pool.readings[e][c] == direct[c, w][j]
            checked += 1
    timings['direct_enumeration'] = time.time() - t
    witnesses = pairwise_cheapest_witnesses(ops, states, BUDGET)
    full = minimum_cost_panel(pool)
    keep = [i for i in range(len(FAMILY)) if i != 2]
    kept_names = [names[i] for i in keep]
    pool5 = experiment_pool(ops, [states[i] for i in keep], BUDGET)
    exact = minimum_cost_panel(pool5)
    greedy_exact = greedy_panel(pool5)
    thresholds = {f'{kept_names[a]} | {kept_names[b]}':
                  s(max(abs(r[a] - r[b]) for r in pool5.readings) / 2)
                  for a, b in candidate_pairs(len(keep))}
    star = min(max(abs(r[a] - r[b]) for r in pool5.readings) / 2 for a, b in candidate_pairs(len(keep)))
    robust = {}
    for eps in (F(1, 64), F(1, 16), F(1, 8), star):
        r = minimum_cost_panel(pool5, eps)
        g = greedy_panel(pool5, eps)
        entry = describe(pool5, r, kept_names)
        entry['greedy_cost'] = s(g.cost)
        if r.feasible:
            assert certifies_identification(pool5, r.panel, eps)
            for tr in range(len(keep)):   # noiseless and extreme box corners
                for sign in (-1, 0, 1):
                    y = [pool5.readings[e][tr] + sign * eps for e in r.panel]
                    assert consistent_candidates(pool5, r.panel, y, eps) == (tr,)
        else:
            a, b, y = ambiguous_reading(pool5, range(pool5.size), eps)
            entry['ambiguous_pair_whole_pool'] = [kept_names[a], kept_names[b]]
        robust[str(eps)] = entry
    ops1 = system.operator_system(list(COSTS), [1] * (R + 1))
    pool_obs1 = experiment_pool(ops1, [states[i] for i in keep], BUDGET)
    return {
        'system': {'max_volume': R, 'q': str(Q), 'contexts': [a.name for a in system.attachments],
                   'attachment_costs': list(COSTS), 'observation_costs': [0] * (R + 1),
                   'dimension': system.dimension, 'budget': BUDGET},
        'candidates': names,
        'pool_size': pool.size,
        'readings_checked_by_direct_enumeration': checked,
        'direct_enumerations': len(direct),
        'direct_observation_vectors': {names[c]: [s(x) for x in system.direct_observations(g, term)]
                                       for c, (_, g, term) in enumerate(FAMILY)},
        'cheapest_witnesses_SNG_O03': [{'pair': [names[a], names[b]], 'status': st, 'cost': s(cost),
                                        'witness': None if w is None else [w[0], list(w[1])]}
                                       for a, b, st, cost, w in witnesses],
        'full_family_exact_panel': describe(pool, full, names),
        'reduced_family': kept_names,
        'reduced_exact_panel': describe(pool5, exact, kept_names),
        'reduced_exact_greedy_cost': s(greedy_exact.cost),
        'robust_threshold_per_pair': thresholds,
        'robust_threshold_uniform_eps': s(star),
        'robust_panels': robust,
        'observation_cost_one_variant': describe(pool_obs1, minimum_cost_panel(pool_obs1), kept_names),
    }


def seeded_comparison():
    rng = random.Random(20261018)
    rows = []
    for n in range(80):
        k, size = rng.randint(2, 4), rng.randint(1, 10)
        costs = [rng.randint(0, 5) for _ in range(size)]
        readings = [[rng.randint(-2, 2) for _ in range(k)] for _ in range(size)]
        if n % 8 == 0:
            for r in readings:
                r[1] = r[0]
        pool = reading_pool(costs, readings)
        eps = None if n % 2 == 0 else F(rng.randint(1, 3), 2)
        bb, ex, gr = minimum_cost_panel(pool, eps), exhaustive_minimum_panel(pool, eps), greedy_panel(pool, eps)
        assert bb.feasible == ex.feasible == gr.feasible and bb.uncoverable == ex.uncoverable
        rows.append((bb.feasible, bb.cost == ex.cost, None if not gr.feasible else gr.cost - ex.cost,
                     None if not ex.feasible else ex.cost, bb.nodes))
    feasible = [r for r in rows if r[0]]
    gaps = [r[2] for r in feasible]
    ratios = [(r[2] + r[3]) / r[3] for r in feasible if r[3]]
    return {'instances': len(rows), 'infeasible': len(rows) - len(feasible),
            'branch_and_bound_equals_exhaustive': all(r[1] for r in feasible),
            'greedy_positive_gap_instances': sum(1 for g in gaps if g > 0),
            'greedy_max_absolute_gap': s(max(gaps)),
            'greedy_max_ratio_positive_optimum': s(max(ratios)),
            'max_nodes': max(r[4] for r in feasible),
            'population': ('seed 20261018; k in 2..4 candidates; 1..10 experiments; costs 0..5; '
                           'readings -2..2; every 8th instance forces readings of candidates 0 and 1 '
                           'equal; odd instances use uniform box epsilon in {1/2, 1, 3/2}')}


def abstract_examples():
    eq = reading_pool([1], [[0, 1]])
    l2 = reading_pool([1, 1], [[0, 1], [0, 1]])
    eps = F(3, 5)
    return {
        'equality_case': {'readings': [[0, 1]], 'epsilon': '1/2',
                          'certified': certifies_identification(eq, (0,), F(1, 2)),
                          'ambiguous_reading': s(ambiguous_reading(eq, (0,), F(1, 2))[2][0]),
                          'consistent': list(consistent_candidates(eq, (0,), [F(1, 2)], F(1, 2)))},
        'l2_versus_box': {'readings': [[0, 1], [0, 1]], 'epsilon': str(eps),
                          'box_panel_feasible': minimum_cost_panel(l2, eps).feasible,
                          'l2_single_certifies': l2_certifies(l2, (0,), eps),
                          'l2_pair_certifies': l2_certifies(l2, (0, 1), eps),
                          'l2_min_panel_cost': s(minimum_cost_l2_panel(l2, eps).cost),
                          'l2_single_ambiguous_reading': [s(x) for x in l2_ambiguous_reading(l2, (0,), eps)[2]]},
        'greedy_gadget': {'readings': [[0, 0, 1, 1], [0, 1, 0, 1], [0, 1, 2, 3]], 'costs': ['1', '1', '19/10'],
                          'greedy_cost': s(greedy_panel(reading_pool([1, 1, F(19, 10)],
                                           [[0, 0, 1, 1], [0, 1, 0, 1], [0, 1, 2, 3]])).cost),
                          'optimum': '19/10'},
    }


def report(timings):
    return {'schema': 'singularity.panels/1',
            'scope': ('Exact finite receipts over declared pools. Weighted set cover is NP-hard in '
                      'general; branch and bound is worst-case exponential. Greedy is a heuristic. '
                      'No statement beyond the declared budget, volume truncation and family.'),
            'graph_instance': graph_instance(timings), 'seeded_comparison': seeded_comparison(),
            'abstract_examples': abstract_examples()}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    timings = {}
    t = time.time()
    payload = report(timings)
    timings['total'] = time.time() - t
    print(f'python {platform.python_version()}; seconds ' + ', '.join(f'{k}={v:.2f}' for k, v in timings.items()))
    if args.check:
        if not REPORT.exists() or json.loads(REPORT.read_text()) != payload:
            raise SystemExit('retained panel report is missing or stale')
        print('Panel receipts match the retained report')
    else:
        REPORT.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
