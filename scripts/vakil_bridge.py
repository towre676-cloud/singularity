#!/usr/bin/env python3
"""Replay the exact triangle observation and symmetry experiments (no CAS)."""
import argparse
from fractions import Fraction as F
from itertools import permutations
import json
from pathlib import Path

from singularity.edge_factors import (
    edge_factor_coefficients, edge_factor_moments, evaluate_factors, factor_gradient,
)
from singularity.graph import Graph

ROOT = Path(__file__).resolve().parents[1]


def rank(rows):
    a = [list(map(F, row)) for row in rows]
    r = 0
    for j in range(len(a[0]) if a else 0):
        pivot = next((k for k in range(r,len(a)) if a[k][j]), None)
        if pivot is None:
            continue
        a[r],a[pivot] = a[pivot],a[r]
        d = a[r][j]
        a[r] = [v/d for v in a[r]]
        for k in range(len(a)):
            if k != r:
                d = a[k][j]
                a[k] = [v-d*w for v,w in zip(a[k],a[r])]
        r += 1
    return r


def det3(a):
    ans = F(0)
    for p in permutations(range(3)):
        inversions = sum(p[i]>p[j] for i in range(3) for j in range(i+1,3))
        ans += (-1)**inversions * a[0][p[0]] * a[1][p[1]] * a[2][p[2]]
    return ans


def experiment():
    graph = Graph(3,[(0,1),(0,2),(1,2)])
    ordinary = edge_factor_coefficients(graph,8)
    moments = edge_factor_moments(graph,8)
    probes = [moments[k,k*k] for k in (1,2,3)]
    labeled_probes = [{(1,1,0):1}, {(1,0,1):1}, {(0,1,1):1}]
    points = {'distinct':(F(1,2),F(1,3),F(1,5)),
              'two_equal':(F(1,2),F(1,2),F(1,3)),
              'all_equal':(F(1,2),)*3}
    strata = {}
    for name,point in points.items():
        strata[name] = {
            'edge_factors':list(map(str,point)),
            'three_moment_probe_rank':rank([factor_gradient(p,point) for p in probes]),
            'labeled_one_unit_probe_rank':rank([factor_gradient(p,point) for p in labeled_probes]),
            'labeled_probe_determinant':str(det3([factor_gradient(p,point) for p in labeled_probes])),
            'ordinary_prefix_ranks':[
                rank([factor_gradient(p,point) for p in ordinary[:R+1]]) for R in range(1,9)],
            'moment_prefix_rank_at_8':rank([factor_gradient(p,point) for p in moments.values()]),
        }
    assert [strata[s]['three_moment_probe_rank'] for s in points] == [3,2,1]
    assert all(strata[s]['labeled_one_unit_probe_rank'] == 3 for s in points)
    for point in points.values():
        A,B,C = [evaluate_factors(p,point) for p in labeled_probes]
        assert (A*B/C,A*C/B,B*C/A) == tuple(t*t for t in point)
    generic = points['distinct']
    raw_det = det3([factor_gradient(p,generic) for p in ordinary[1:4]])
    assert raw_det == F(-229387106779,1230187500000000)
    symmetric = points['all_equal']
    assert all(sum(x*y for x,y in zip(factor_gradient(p,symmetric),(1,-1,0)))==0
               for p in moments.values())
    response = []
    for e in (F(1,10),F(1,100),F(1,1000)):
        t = F(1,2)
        point = (t+e,t-e,t)
        difference = evaluate_factors(ordinary[1],point)-evaluate_factors(ordinary[1],symmetric)
        assert difference == -e*e
        response.append({'epsilon':str(e),'first_coefficient_change':str(difference),
                         'moment_probe_determinant':str(det3([factor_gradient(p,point) for p in probes]))})
    return {'schema':'singularity.vakil-bridge/1',
            'source':'https://math.stanford.edu/~vakil/216blog/FOAGjun1113public.pdf',
            'scope':'Exact finite experiment through volume 8. All-depth and all-positive-parameter statements are proved in docs/research/VAKIL_BRIDGES.md; no effective Noetherian cutoff is computed.',
            'triangle_edges':[list(e) for e in graph.edges],
            'ordinary_volume_1_2_3_jacobian_determinant':str(raw_det),
            'moment_volume_1_2_3_jacobian_determinant':str(det3([factor_gradient(p,generic) for p in probes])),
            'strata':strata,'near_symmetry':response,
            'checked_profiles_through_volume_8':165}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    path = ROOT/'results'/'vakil_bridge.json'
    payload = experiment()
    if args.check:
        if not path.exists() or json.loads(path.read_text()) != payload:
            raise SystemExit('retained Vakil bridge experiment is missing or stale')
        print('Exact Vakil bridge experiment matches retained report')
    else:
        path.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
        print(json.dumps(payload,indent=2,sort_keys=True))


if __name__ == '__main__':
    main()
