#!/usr/bin/env python3
"""Reproduce retained finite research results with no third-party packages."""
import argparse
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from singularity import __version__
from singularity.certificates import build_certificate, replay_certificate
from singularity.conductor import remote_coefficient
from singularity.euler import euler_exponents, first_difference, recompose_euler
from singularity.examples import GRAPHS
from singularity.graph import Graph
from singularity.heights import local_coefficients, marked_coefficients
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
    }
    replays={name:replay_certificate(packet) for name,packet in certificates.items()}
    assert all(r['valid'] for r in replays.values())
    graph_sources={**GRAPHS,'cube':cube,'mobius_ladder':mobius}
    files={
        'results/exact_examples.json':{'schema':'singularity.reproduction/1','version':__version__,'pairs':pairs,'certificate_replays':replays},
        **{f'data/graphs/{name}.json':graph.to_dict() for name,graph in graph_sources.items()},
        **{f'results/certificates/{name}.json':packet for name,packet in certificates.items()},
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
    print('Exact examples, three graph comparisons, three independent packet replays and remote conductor coefficient '+('match retained outputs.' if args.check else 'written.'))


if __name__=='__main__':
    main()
