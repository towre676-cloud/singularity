#!/usr/bin/env python3
"""Reproduce retained finite research results with no third-party packages."""
import argparse
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from singularity import __version__
from singularity.certificates import build_certificate, replay_certificate
from singularity.conductor import CyclotomicRing, remote_coefficient, residue_numerator
from singularity.euler import euler_exponents, first_difference, recompose_euler
from singularity.examples import GRAPHS
from singularity.graph import Graph
from singularity.chains import chain_local_coefficients, chain_marked_coefficients
from singularity.heights import local_coefficients, marked_coefficients
from singularity.parameters import parameter_strata
from singularity.lowvolume import low_volume_local, low_volume_marked, pattern_sectors, regular_low_volume_local
from singularity.invariants import binary_cut_profile, laplacian_characteristic_polynomial
from singularity.polynomials import evaluate, polynomial_to_json, verify_factorization

ROOT = Path(__file__).resolve().parents[1]


def record_pair(left, right, depth, factorization):
    a = local_coefficients(left, depth)
    b = local_coefficients(right, depth)
    found = first_difference(a, b)
    assert found is not None and found[0] == depth
    r, polynomial = found
    assert verify_factorization(polynomial, Fraction(factorization['coefficient']), factorization['monomial'], factorization['factors'])
    q_half = evaluate(polynomial, Fraction(1, 2))
    exponents = euler_exponents(a)
    assert recompose_euler(exponents, depth) == [{e:Fraction(c) for e,c in row.items()} for row in a]
    marked_a, marked_b = marked_coefficients(left, depth), marked_coefficients(right, depth)
    spans = sorted({h for (m,e,h) in set(marked_a) | set(marked_b) if m == depth and marked_a.get((m,e,h),0) != marked_b.get((m,e,h),0)})
    return {
        'left_graph':left.to_dict(), 'right_graph':right.to_dict(),
        'degrees_equal':sorted(left.degrees)==sorted(right.degrees),
        'binary_census_equal':binary_cut_profile(left)==binary_cut_profile(right),
        'laplacian_spectrum_equal':laplacian_characteristic_polynomial(left)==laplacian_characteristic_polynomial(right),
        'left_laplacian_polynomial':list(laplacian_characteristic_polynomial(left)),
        'right_laplacian_polynomial':list(laplacian_characteristic_polynomial(right)),
        'first_difference_volume':r,'difference':polynomial_to_json(polynomial),
        'factorization':factorization, 'q_half_difference':str(q_half),
        'first_difference_spans':spans,
        'analytic_interpretation':{'real_ratio_singularity_location':str(Fraction(1,r)), 'power_exponent_at_q_half':str(q_half), 'status':'finite hypotheses checked; analytic transfer is proved in manuscript'},
    }


def marked_difference(left, right):
    keys = sorted(set(left) | set(right))
    return [[*key, left.get(key, 0) - right.get(key, 0)] for key in keys if left.get(key, 0) != right.get(key, 0)]


def edge_degree_types(graph):
    counts = {}
    for u, v in graph.edges:
        key = tuple(sorted((graph.degrees[u], graph.degrees[v])))
        counts[key] = counts.get(key, 0) + 1
    return [[a, b, c] for (a, b), c in sorted(counts.items())]


def pair_acceptance(left, right, depth, certificate_replay):
    """P04/P05 receipt: formulas, two enumerators, binary census and certificate."""
    record = {'depth': depth, 'graphs': [left.to_dict(), right.to_dict()]}
    for side, graph in (('left', left), ('right', right)):
        composition, chains = marked_coefficients(graph, depth), chain_marked_coefficients(graph, depth)
        assert composition == chains == {k: c for k, c in low_volume_marked(graph).items() if k[0] <= depth}
        assert local_coefficients(graph, depth) == chain_local_coefficients(graph, depth) == low_volume_local(graph)[:depth + 1]
        record[side] = {
            'degrees': list(graph.degrees),
            'edge_degree_types': edge_degree_types(graph),
            'pattern_sectors': {k: [[e, c] for e, c in v.items()] for k, v in pattern_sectors(graph).items()},
            'binary_cut_profile': [[r, cut, c] for (r, cut), c in binary_cut_profile(graph).items()],
        }
    by_compositions = marked_difference(marked_coefficients(left, depth), marked_coefficients(right, depth))
    by_chains = marked_difference(chain_marked_coefficients(left, depth), chain_marked_coefficients(right, depth))
    assert by_compositions == by_chains
    record['marked_difference'] = by_chains
    record['first_marked_difference_volume'] = min(row[0] for row in by_chains)
    record['marked_difference_spans'] = sorted({row[2] for row in by_chains})
    record['binary_census_equal'] = binary_cut_profile(left) == binary_cut_profile(right)
    record['enumerators_agree'] = {'weak_compositions': True, 'level_chains': True, 'closed_formulas_through_volume_3': True}
    record['certificate_replay_valid'] = certificate_replay['valid']
    return record


def conductor_fixtures():
    """P18 receipt: numerators and their agreement with direct specialization."""
    graphs = {
        'path3': Graph(3, ((0, 1), (1, 2))),
        'edge_plus_isolated': Graph(3, ((0, 1),)),
        'triangle': Graph(3, ((0, 1), (1, 2), (0, 2))),
        'star4': Graph(4, ((0, 1), (0, 2), (0, 3))),
    }
    bound, records = 12, []
    for name, graph in graphs.items():
        local = local_coefficients(graph, bound)
        for order in (1, 2, 3, 4, 6):
            ring, numerator = residue_numerator(graph, order)
            direct = []
            for polynomial in local:
                value = ring.zero
                for energy, count in polynomial.items():
                    value = ring.add(value, ring.scale(ring.phase(energy), count))
                direct.append(value)
            remote = [remote_coefficient(graph, order, index) for index in range(bound + 1)]
            assert remote == direct
            records.append({'graph': name, 'source': graph.to_dict(), 'order': order,
                            'cyclotomic_modulus_constant_first': list(ring.modulus),
                            'numerator_constant_first': [list(e) for e in numerator],
                            'specialized_coefficients_agree_through_volume': bound})
    return {'schema': 'singularity.conductor-fixtures/1',
            'theorem': 'SNG-F28: L_G(x,w)=N_{G,m}(x)/(1-x^m)^n in Z[t]/Phi_m(t)',
            'oracle': 'direct specialization of weak-composition coefficients, each energy e mapped to t^(e mod m)',
            'fixtures': records}


def gauss_fixtures():
    """P19 receipt: rank, discriminant class and agreement of the two Gauss-sum routes."""
    from singularity.gauss import gauss_sum_direct, gauss_sum_formula, laplacian_invariants
    graphs = {'triangle': Graph(3, ((0, 1), (1, 2), (0, 2))), 'path3': Graph(3, ((0, 1), (1, 2))),
              'two_edges_one_point': Graph(5, ((0, 1), (2, 3))), 'spectral_g': GRAPHS['spectral_g'],
              'binary_g': GRAPHS['binary_g'], 'binary_h': GRAPHS['binary_h']}
    records = []
    for name, graph in graphs.items():
        polynomial = laplacian_characteristic_polynomial(graph)
        trees = abs(polynomial[-2]) // graph.n if graph.connected else 0
        for p in (3, 5):
            info = laplacian_invariants(graph, p)
            direct, formula = gauss_sum_direct(graph, p), gauss_sum_formula(graph, p)
            assert direct == formula
            records.append({'graph': name, 'source': graph.to_dict(), 'prime': p, 'spanning_trees': trees,
                            'prime_divides_spanning_trees': trees % p == 0, 'rank': info['rank'],
                            'diagonal': info['diagonal'], 'basis_columns': info['basis_columns'],
                            'discriminant_character': info['discriminant_character'],
                            'gauss_sum_constant_first': list(direct)})
    return {'schema': 'singularity.gauss-fixtures/1', 'theorem': 'SNG-F30',
            'ring': 'Z[t]/Phi_p(t), t = exp(2 pi i/p)', 'fixtures': records}


def census_visibility():
    """P25 receipt: symbolic, marked and q=1/2 filtrations of the CENSUS-v1 population."""
    from singularity.visibility import visibility_filtration
    manifest = json.loads((ROOT / 'results/census_manifest.json').read_text())
    orders = []
    for order in manifest['orders']:
        graphs = {f"n{c['n']}:{c['canonical_code']}": Graph(c['n'], c['edges']) for c in order['classes']}
        local = {k: local_coefficients(g, 6) for k, g in graphs.items()}
        orders.append({'n': order['n'],
                       'polynomial': visibility_filtration(local),
                       'marked': visibility_filtration({k: marked_coefficients(g, 6) for k, g in graphs.items()}, 'marked', 6),
                       'q_one_half': visibility_filtration(local, Fraction(1, 2))})
    return {'schema': 'singularity.visibility-filtration/1', 'theorem': 'SNG-F33',
            'population': 'results/census_manifest.json (connected graphs, n <= 6)', 'bound': 6,
            'interpretation': 'finite agreement or separation through volume 6 on this population only', 'orders': orders}


def compute():
    factors_a={'coefficient':'2','monomial':2,'factors':[[1,2],[2,1]]}
    factors_b={'coefficient':'1','monomial':3,'factors':[[1,1],[3,2],[4,2]]}
    cube=Graph(8, ((i,i^(1<<bit)) for i in range(8) for bit in range(3) if i<(i^(1<<bit))))
    mobius=Graph(8, tuple((i,(i+1)%8) for i in range(8))+tuple((i,i+4) for i in range(4)))
    pairs={
        'spectral':record_pair(GRAPHS['spectral_g'],GRAPHS['spectral_h'],2,factors_a),
        'binary_census':record_pair(GRAPHS['binary_g'],GRAPHS['binary_h'],3,factors_b),
        'regular_cube_mobius':record_pair(cube,mobius,4,{'coefficient':'2','monomial':4,'factors':[[2,4]]}),
    }
    certificates={
        'spectral':build_certificate(GRAPHS['spectral_g'],4,GRAPHS['spectral_h'],'spectral-pair',factors_a),
        'binary_census':build_certificate(GRAPHS['binary_g'],4,GRAPHS['binary_h'],'binary-census-pair',factors_b),
        'translation':build_certificate(Graph(3,((0,1),(1,2))),5,label='translation-crossing'),
        'regular_cube_mobius':build_certificate(cube,4,mobius,'cube-mobius-pair',{'coefficient':'2','monomial':4,'factors':[[2,4]]}),
    }
    replays={name:replay_certificate(packet) for name,packet in certificates.items()}
    assert all(r['valid'] for r in replays.values())
    regular=regular_low_volume_local(8,3,0)
    assert local_coefficients(cube,3)==local_coefficients(mobius,3)==regular
    acceptance={
        'schema':'singularity.pair-acceptance/1',
        'scope':'fixed labeled pairs; closed formulas (lowvolume.py), weak compositions (heights.py) and level chains (chains.py) through the stated depth',
        'spectral':pair_acceptance(GRAPHS['spectral_g'],GRAPHS['spectral_h'],2,replays['spectral']),
        'binary_census':pair_acceptance(GRAPHS['binary_g'],GRAPHS['binary_h'],3,replays['binary_census']),
        'regular_cube_mobius_through_volume_3':{'n':8,'degree':3,'triangles':[0,0],'local_coefficients':[[[e,c] for e,c in row.items()] for row in regular],'agree':True},
    }
    graph_sources={**GRAPHS,'cube':cube,'mobius_ladder':mobius}
    files={
        'results/exact_examples.json':{'schema':'singularity.reproduction/1','version':__version__,'pairs':pairs,'certificate_replays':replays},
        **{f'data/graphs/{name}.json':graph.to_dict() for name,graph in graph_sources.items()},
        **{f'results/certificates/{name}.json':packet for name,packet in certificates.items()},
        'results/pair_acceptance.json':acceptance,
        'results/conductor_fixtures.json':conductor_fixtures(),
        'results/gauss_fixtures.json':gauss_fixtures(),
        'results/visibility_filtration.json':census_visibility(),
        'results/parameter_strata.json':{'schema':'singularity.parameter-strata/1','theorem':'SNG-F31',
            'spectral':parameter_strata(local_coefficients(GRAPHS['spectral_g'],4),local_coefficients(GRAPHS['spectral_h'],4)),
            'binary_census':parameter_strata(local_coefficients(GRAPHS['binary_g'],4),local_coefficients(GRAPHS['binary_h'],4)),
            'regular_cube_mobius':parameter_strata(local_coefficients(cube,5),local_coefficients(mobius,5))},
        'results/conductor_example.json':{'schema':'singularity.conductor-example/1','graph':Graph(3,((0,1),(1,2))).to_dict(),'conductor':3,'index':str(10**100),'coefficient':list(remote_coefficient(Graph(3,((0,1),(1,2))),3,10**100)),'ring':'Z[t]/(t^2+t+1)'},
    }
    return files


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    failures=[]
    for relative, content in compute().items():
        target=ROOT/relative
        serialized=json.dumps(content,indent=2,sort_keys=True)+'\n'
        if args.check:
            if not target.exists() or target.read_text()!=serialized:
                failures.append(relative)
        else:
            target.parent.mkdir(parents=True,exist_ok=True); target.write_text(serialized)
    if failures:
        raise SystemExit('Retained outputs differ: '+', '.join(failures))
    print('Exact examples, three graph comparisons, four independent packet replays and remote conductor coefficient '+('match retained outputs.' if args.check else 'written.'))


if __name__=='__main__':
    main()
