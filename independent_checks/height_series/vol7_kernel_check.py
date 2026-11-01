#!/usr/bin/env python3
"""Replay exact volume-seven connected-support and edge-Mobius certificates."""
import argparse, json
from collections import Counter
from pathlib import Path
from vol7_lib import (catalogue,full_catalogue,connected_types,edges_of,degrees_of,connected_mask,
    cumulant_coeffs,beta_coeffs,expected_top_beta,spanning_subgraphs,
    padd,encode_poly)


def run():
    rows=[]
    for k in range(1,8):
        for mask in connected_types(k):
            phi=cumulant_coeffs(mask,k,7)
            beta=beta_coeffs(mask,k,7)
            assert all(not phi[r] and not beta[r] for r in range(k))
            assert beta[k] == expected_top_beta(mask,k),(k,mask,'top coefficient')
            inversion=[{} for _ in range(8)]
            for sub,count in spanning_subgraphs(mask,k).items():
                small=beta_coeffs(sub,k,7)
                for r in range(1,8): inversion[r]=padd(inversion[r],small[r],count)
            assert tuple(inversion)==phi,(k,mask,'Mobius inversion')
            rows.append({'vertices':k,'mask':mask,'edges':[list(e) for e in edges_of(mask,k)],
                'edge_count':mask.bit_count(),'degree_sequence':list(sorted(degrees_of(mask,k),reverse=True)),
                'phi7':encode_poly(phi[7]),'beta7':encode_poly(beta[7])})
    counts={str(k):{'all_subcubic':len(catalogue(k)),'connected_subcubic':len(connected_types(k))} for k in range(1,8)}
    edge_census={str(e):count for e,count in sorted(Counter(m.bit_count() for m in connected_types(7)).items())}
    full=full_catalogue(7)
    full_connected=[m for m in full if connected_mask(m,7)]
    assert set(m for m in full if max(degrees_of(m,7))<=3)==set(catalogue(7))
    full_census={'all_simple_types':len(full),'connected_simple_types':len(full_connected),
        'connected_subcubic_types':len(connected_types(7)),
        'connected_types_vacuous_in_cubic_hosts':sum(max(degrees_of(m,7))>3 for m in full_connected)}
    return {'schema':'singularity-volume7-kernels-v1','arithmetic':'exact Fraction; Laurent q-polynomials',
        'catalogue':counts,'full_seven_census':full_census,'connected_seven_by_edges':edge_census,
        'connected_patterns_checked':len(rows),'below_support_vanishing_failures':0,
        'top_beta_formula_failures':0,'edge_mobius_inversion_failures':0,
        'identities':['beta_H=sum_F_subset_E(H) (-1)^(e(H)-e(F)) Phi_F',
            '[x^k] beta_H=q^(3k)(q^-2-1)^e(H)',
            'Phi_H=sum_connected_F_subset_E(H) beta_F'],
        'patterns':rows}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    result=run();path=Path(__file__).with_suffix('.json')
    if a.check: assert json.loads(path.read_text())==result
    else: path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='patterns'},sort_keys=True))
