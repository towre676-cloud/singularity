#!/usr/bin/env python3
"""Deterministic receipt for the operator and experiment layer.

Covers closure and its certificate replay, length-filtered ranks, the R=7
formal invisible direction, the top-volume corank bound, minimum-cost
witnesses, quotient transport, graph assembly against direct enumeration,
the exact metric identities and the periodic sector.  With --check the
retained JSON and the portable R=4 certificate must match exactly.
Timings and interpreter versions are printed, not retained.
"""
import argparse
import json
import platform
import sys
import time
from fractions import Fraction as F
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from singularity.contexts import orbit_groups  # noqa: E402
from singularity.experiment_design import (integral_inner_product,  # noqa: E402
                                           orthogonal_polynomial_basis)
from singularity.graph import Graph  # noqa: E402
from singularity.graph_experiments import BoundaryExperimentSystem  # noqa: E402
from singularity.heights import local_coefficients  # noqa: E402
from singularity.observability import (OperatorSystem, apply_word, certificate_bundle,  # noqa: E402
                                       experiment, minimum_distinguishing_experiment,
                                       observable_closure, quotient_output, quotient_state,
                                       quotient_update, replay_bundle, verify_certificate)
from singularity.periodic import (PeriodicModel, compare_models, compare_models_reduced,  # noqa: E402
                                  direct_coefficients, effective_modulus, is_palindromic,
                                  odd_vertex_count, periodic_cutoff, residue_numerator,
                                  series_from_numerator)
from singularity.terminal_moves import OrderedMoveSystem  # noqa: E402

HALF = F(1, 2)
PATH = Graph(3, ((0, 1), (1, 2)))
CERTIFICATE = ROOT / 'results' / 'operator_closure_certificate.json'
REPORT = ROOT / 'results' / 'operator_experiments.json'


def s(x):
    return str(x)


def evaluate(row, q):
    return sum((F(c) * q ** e for e, c in row.items()), F(0))


def r4_closure(timings):
    t = time.time()
    replayed_system, replayed = replay_bundle(json.loads(CERTIFICATE.read_text()))
    timings['replay_retained_R4'] = time.time() - t
    t = time.time()
    system = BoundaryExperimentSystem(4, HALF)
    operators = system.operator_system()
    cert = observable_closure(operators)
    timings['discover_R4'] = time.time() - t
    assert verify_certificate(operators, cert)
    return {
        'max_volume': 4, 'q': '1/2', 'contexts': [a.name for a in system.attachments],
        'dimension': system.dimension, 'rank': cert.rank,
        'rank_by_word_length': [sum(e.cost <= k for e in cert.basis) for k in range(9)],
        'retained_certificate_replays': replayed.rank == cert.rank and replayed_system == operators,
        'fresh_bundle_equals_retained': certificate_bundle(operators, cert) == json.loads(CERTIFICATE.read_text()),
        'basis_words': [[e.observation, list(e.word)] for e in cert.basis],
    }, operators, cert


def r7_invisible(timings):
    t = time.time()
    system = BoundaryExperimentSystem(7, HALF)
    operators = system.operator_system()
    cert = observable_closure(operators)
    timings['discover_R7'] = time.time() - t
    assert verify_certificate(operators, cert)
    (kernel,) = cert.nullspace
    support = {f'{system.coordinates[i]}': s(x) for i, x in enumerate(kernel) if x}
    eigen = []
    for op in system.operators:
        image = tuple(sum((a * b for a, b in zip(row, kernel)), F(0)) for row in op)
        ratio = {image[i] / kernel[i] for i in range(len(kernel)) if kernel[i]}
        assert len(ratio) == 1 and all(image[i] == 0 for i in range(len(kernel)) if not kernel[i])
        eigen.append(s(ratio.pop()))
    # Quotient transport on the two path placements, words of length <= 3.
    first, second = system.compile_graph(PATH, (0, 2)), system.compile_graph(PATH, (0, 1))
    transports = 0
    for v in (first, second):
        for word in (w for m in range(4) for w in product(range(2), repeat=m)):
            y = quotient_state(operators, cert, v)
            for i in word:
                y = quotient_update(cert, i, y)
            moved = apply_word(operators, v, word)
            assert y == quotient_state(operators, cert, moved)
            assert quotient_output(cert, y) == system.observe(moved)
            transports += 1
    return {
        'max_volume': 7, 'dimension': system.dimension, 'rank': cert.rank,
        'invisible_direction': support, 'generator_eigenvalues': eigen,
        'outputs_annihilate_direction': not any(system.observe(kernel)),
        'quotient_transport_checks': transports,
        'scope': 'Formal interface ambiguity in the declared coordinate space; no pair of graph states realizing it is asserted.',
    }


def corank_bound():
    out = []
    for R in range(1, 11):
        groups = [[list(o) for o in g] for g in orbit_groups(R).values() if len(g) > 1]
        out.append({'max_volume': R, 'colliding_orbit_classes': groups,
                    'corank_lower_bound': sum(len(g) - 1 for g in groups)})
    return out


def path_fixture(timings):
    t = time.time()
    system = BoundaryExperimentSystem(1, HALF)
    operators = system.operator_system(attachment_costs=(2, 1))
    cert = observable_closure(operators)
    first, second = system.compile_graph(PATH, (0, 2)), system.compile_graph(PATH, (0, 1))
    d = tuple(a - b for a, b in zip(first, second))
    witness = minimum_distinguishing_experiment(operators, d, cert)
    readings = {}
    for terminals in ((0, 2), (0, 1)):
        for i, a in enumerate(system.attachments):
            graph, _ = system.attached_graph(PATH, terminals, (i,))
            readings[f'{terminals}:{a.name}'] = s(evaluate(local_coefficients(graph, 1)[1], HALF))
    words_checked = 0
    big = BoundaryExperimentSystem(3, HALF)
    for terminals in ((0, 2), (0, 1)):
        state = big.compile_graph(PATH, terminals)
        for word in (w for m in range(4) for w in product(range(2), repeat=m)):
            assert big.observe(state, word) == big.direct_observations(PATH, terminals, word)
            words_checked += 1
    timings['path_fixture'] = time.time() - t
    return {
        'direct_observations': [s(x) for x in system.observe(first)],
        'direct_observations_equal': system.observe(first) == system.observe(second),
        'attachment_costs': {'pendant_leaf_pair': '2', 'shared_neighbor': '1'},
        'volume_one_readings_by_enumeration': readings,
        'cheapest_witness': {'word': list(witness.word), 'observation_volume': witness.observation,
                             'cost': s(witness.cost),
                             'discrepancy': s(sum((a * b for a, b in zip(witness.row, d)), F(0)))},
        'words_checked_against_enumeration_R3': words_checked,
    }


def amplification():
    system = OperatorSystem(1, (((2,),),), ((1,),))
    cert = observable_closure(system)
    witness = minimum_distinguishing_experiment(system, (1,), cert)
    return {'observation': '1', 'generator': '2', 'rank': cert.rank,
            'cheapest_witness_word': list(witness.word), 'cheapest_signal': s(witness.row[0]),
            'signal_after_three_attachments': s(experiment(system, 0, (0, 0, 0)).row[0]),
            'meaning': 'minimum cost is not maximum margin; pruned extensions amplify'}


def word_order():
    system = OperatorSystem(2, (((1, 1), (0, 1)), ((1, 0), (1, 1))), ((1, 0),))
    v = (F(0), F(1))
    return {'state_after_word_0_1': [s(x) for x in apply_word(system, v, (0, 1))],
            'state_after_word_1_0': [s(x) for x in apply_word(system, v, (1, 0))],
            'row_of_word_0_1': [s(x) for x in experiment(system, 0, (0, 1)).row],
            'closure_words': [list(e.word) for e in observable_closure(system).basis]}


def metrics():
    delta = (0, -1, 2, -1)
    basis = orthogonal_polynomial_basis(3)
    coords = basis.coordinates(delta)
    return {'discrepancy': '-q(1-q)^2', 'coefficients': list(delta),
            'integral_square_on_0_1': s(integral_inner_product(delta, delta)),
            'coefficient_dot_product': s(sum(c * c for c in delta)),
            'orthogonal_coordinates': [s(c) for c in coords],
            'orthogonal_norms_squared': [s(n) for n in basis.norms_squared],
            'parseval': s(sum((c * c * n for c, n in zip(coords, basis.norms_squared)), F(0)))}


def periodic(timings):
    t = time.time()
    path, split = Graph(3, ((0, 1), (1, 2))), Graph(3, ((0, 1),))
    examples = {}
    for M in (2, 3):
        a, b = PeriodicModel(path, M), PeriodicModel(split, M)
        c = compare_models(a, b)
        examples[f'M={M}'] = {
            'cutoff': c.cutoff, 'certified_equal': c.equal, 'first_difference': c.first_difference,
            'path_numerator': [list(x) for x in residue_numerator(a)],
            'edge_plus_isolated_numerator': [list(x) for x in residue_numerator(b)],
            'direct_agreement_through_14': direct_coefficients(a, 14) == direct_coefficients(b, 14)}
    models = 0
    for n in (1, 2, 3):
        pairs = [(u, v) for u in range(n) for v in range(u + 1, n)]
        for mask in range(1 << len(pairs)):
            edges = [p for i, p in enumerate(pairs) if mask >> i & 1]
            graph = Graph(n, edges)
            for M in (1, 2, 3, 4):
                for exps in product((-1, 0, 1, 2), repeat=len(edges)):
                    model = PeriodicModel(graph, M, dict(zip(edges, exps)))
                    P = residue_numerator(model)
                    assert is_palindromic(P) and len(P) == model.K + 1
                    bound = model.K + 2 * M + 1
                    assert series_from_numerator(model, P, bound) == direct_coefficients(model, bound)
                    models += 1
    timings['periodic'] = time.time() - t
    return {'examples': examples, 'exhausted_models': models,
            'population': 'all graphs on n <= 3 labelled vertices, M in 1..4, edge exponents in {-1,0,1,2}',
            'identity_checked_through': 'K + 2M + 1', 'cutoff_formula': 'floor(n(M-1)/2)',
            'cutoff_examples': {f'n={n},M={M}': periodic_cutoff(n, M) for n in (3, 4) for M in (2, 3)}}


def periodic_reduction():
    path, split = Graph(3, ((0, 1), (1, 2))), Graph(3, ((0, 1),))
    four = [PeriodicModel(g, 4) for g in (path, split, Graph(3, ((0, 1), (1, 2), (0, 2))))]
    worst = {}
    for n in (2, 3, 4):
        pairs = [(u, v) for u in range(n) for v in range(u + 1, n)]
        reps = {}
        for mask in range(1 << len(pairs)):
            m = PeriodicModel(Graph(n, [p for i, p in enumerate(pairs) if mask >> i & 1]), 4)
            reps.setdefault(tuple(direct_coefficients(m, 3 * n + 8)), m)
        reps = list(reps.values())
        worst[str(n)] = max((compare_models_reduced(a, b).first_difference
                             for i, a in enumerate(reps) for b in reps[i + 1:]), default=None)
    return {'effective_modulus_M4': [effective_modulus(m) for m in four],
            'reduced_cutoff_M4_n3': compare_models_reduced(four[0], four[1]).cutoff,
            'worst_first_difference_M4_exponent1_by_n': worst,
            'M2_odd_vertex_counts': {'path': odd_vertex_count(PeriodicModel(path, 2)),
                                     'edge_plus_isolated': odd_vertex_count(PeriodicModel(split, 2))}}


def terminal_moves():
    system = OrderedMoveSystem(2, HALF)
    operators = system.operator_system(attachment_costs=(2, 1, 1, 1))
    cert = observable_closure(operators)
    d = tuple(a - b for a, b in zip(system.compile_graph(PATH, (0, 1)), system.compile_graph(PATH, (1, 2))))
    witness = minimum_distinguishing_experiment(operators, d, cert)
    checked = 0
    for terminals in ((0, 2), (0, 1), (1, 0)):
        state = system.compile_graph(PATH, terminals)
        for word in (w for m in range(4) for w in product(range(4), repeat=m)):
            assert system.observe(state, word) == system.direct_observations(PATH, terminals, word)
            checked += 1
    return {'max_volume': 2, 'moves': [m if isinstance(m, str) else m.name for m in system.moves],
            'ordered_dimension': system.dimension, 'ordered_rank': cert.rank,
            'symmetric_blind_pair': 'path(0,1) vs path(1,2)',
            'witness': {'word': [system.moves[i] if isinstance(system.moves[i], str) else system.moves[i].name
                                 for i in witness.word], 'cost': s(witness.cost),
                        'observation_volume': witness.observation},
            'words_checked_against_enumeration': checked}


def experiment_report(timings):
    r4, operators, cert = r4_closure(timings)
    return {'schema': 'singularity.operator-experiments/1',
            'scope': ('Exact finite receipts. Closure is fixed-budget formal closure; it does not '
                      'prove an untruncated rational generating function, minimality on '
                      'graph-realizable states, or maximum-margin experiments.'),
            'closure_R4': r4, 'closure_R7': r7_invisible(timings), 'top_volume_corank_bound': corank_bound(),
            'path_fixture': path_fixture(timings), 'amplification_counterexample': amplification(),
            'word_order': word_order(), 'metrics': metrics(), 'periodic': periodic(timings),
            'periodic_reduction': periodic_reduction(), 'terminal_moves': terminal_moves()}, operators, cert


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    timings = {}
    if not args.check:
        system = BoundaryExperimentSystem(4, HALF).operator_system()
        CERTIFICATE.write_text(json.dumps(certificate_bundle(system), indent=2, sort_keys=True) + '\n')
    payload, _, _ = experiment_report(timings)
    print(f'python {platform.python_version()}; seconds ' + ', '.join(f'{k}={v:.2f}' for k, v in timings.items()))
    if args.check:
        if not REPORT.exists() or json.loads(REPORT.read_text()) != payload:
            raise SystemExit('retained operator experiment report is missing or stale')
        if not payload['closure_R4']['fresh_bundle_equals_retained']:
            raise SystemExit('retained R=4 certificate differs from fresh discovery')
        print('Operator experiments match the retained report; R=4 certificate replays')
    else:
        REPORT.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
        print(f'wrote {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
