#!/usr/bin/env python3
"""Replay exact volume-eight connected-support and edge-Mobius certificates."""
import argparse, json
from collections import Counter
from pathlib import Path
from vol8_lib import (catalogue,full_catalogue,connected_types,edges_of,degrees_of,connected_mask,
    cumulant_coeffs,beta_coeffs,expected_top_beta,spanning_subgraphs,
    padd,encode_poly)


def run():
    rows=[]
    for k in range(1,9):
        for mask in connected_types(k):
            phi=cumulant_coeffs(mask,k,8)
            beta=beta_coeffs(mask,k,8)
            assert all(not phi[r] and not beta[r] for r in range(k))
            assert beta[k] == expected_top_beta(mask,k),(k,mask,'top coefficient')
            inversion=[{} for _ in range(9)]
            for sub,count in spanning_subgraphs(mask,k).items():
                small=beta_coeffs(sub,k,8)
                for r in range(1,9): inversion[r]=padd(inversion[r],small[r],count)
            assert tuple(inversion)==phi,(k,mask,'Mobius inversion')
            rows.append({'vertices':k,'mask':mask,'edges':[list(e) for e in edges_of(mask,k)],
                'edge_count':mask.bit_count(),'degree_sequence':list(sorted(degrees_of(mask,k),reverse=True)),
                'phi8':encode_poly(phi[8]),'beta8':encode_poly(beta[8])})
    counts={str(k):{'all_subcubic':len(catalogue(k)),'connected_subcubic':len(connected_types(k))} for k in range(1,9)}
    edge_census={str(e):count for e,count in sorted(Counter(m.bit_count() for m in connected_types(8)).items())}
    full=full_catalogue(8)
    full_connected=[m for m in full if connected_mask(m,8)]
    assert {m for m in full if max(degrees_of(m,8))<=3}==set(catalogue(8))
    full_census={'all_simple_types':len(full),'connected_simple_types':len(full_connected),
        'connected_subcubic_types':len(connected_types(8)),
        'connected_types_vacuous_in_cubic_hosts':sum(max(degrees_of(m,8))>3 for m in full_connected)}
    previous=json.loads(Path(__file__).with_name('vol7_kernel_check.json').read_text())
    previous_rows={(x['vertices'],x['mask']):x for x in previous['patterns']}
    for k in range(1,8):
        for mask in connected_types(k):
            old=previous_rows[(k,mask)]
            assert old['phi7']==encode_poly(cumulant_coeffs(mask,k,8)[7])
            assert old['beta7']==encode_poly(beta_coeffs(mask,k,8)[7])
    preserved={'seventh_order_kernels_replayed':len(previous_rows),'coefficient_failures':0}
    return {'schema':'singularity-volume8-kernels-v1','arithmetic':'exact Fraction; Laurent q-polynomials',
        'catalogue':counts,'full_eight_census':full_census,'preserved_volume7':preserved,'connected_eight_by_edges':edge_census,
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
