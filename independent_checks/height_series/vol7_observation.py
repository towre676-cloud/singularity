#!/usr/bin/env python3
"""Replay exact constructed observation witnesses and the rank gain at seven."""
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
from vol7_lib import encode_poly, padd, pmul
from vol7_law import reduced_coefficients, quotient_data, rref
from vol7_completion import isolation_data, realize_core_vector, key

HERE=Path(__file__).resolve().parent

def log_difference(coeffs,vector,r):
    out={}
    for h,mult in vector.items(): out=padd(out,coeffs[r].get(h,{}),mult)
    return out

def pair_record(vector,coeffs):
    relation,scale=realize_core_vector(vector)
    C,rows,_=isolation_data()
    actual={h:sum(mult*rows.get(g,{}).get(h,0) for g,mult in relation.items()) for h in C}
    assert all(actual[h]==scale*vector.get(h,0) for h in C)
    d=[{}]+[log_difference(coeffs,actual,r) for r in range(1,8)]
    assert not any(d[1:7])
    assert d[7]
    def order(g): return 30 if g==(0,0) else 94*g[0]-62*g[1].bit_count()
    nA=sum(mult*order(g) for g,mult in relation.items() if mult>0)
    nB=sum(-mult*order(g) for g,mult in relation.items() if mult<0)
    assert nA==nB
    return {'signed_components':{key(g):v for g,v in sorted(relation.items())},
            'equal_vertex_order':nA,'scale':scale,
            'core_differences':{key(h):v for h,v in actual.items() if v},
            'delta_log_coefficients':{str(r):encode_poly(d[r]) for r in range(1,8)},
            'delta_L7':encode_poly(d[7])}

def main():
    coeffs=reduced_coefficients()
    C,_,_=isolation_data()
    # Seven-core differences are supported beyond every lower coefficient.
    isolated={key(h):pair_record({h:1},coeffs) for h in C if h[0]==7}
    # This difference is invisible through six despite changing the house.
    house=(5,221);k23=(5,126)
    hidden=pair_record({house:1,k23:-1},coeffs)
    assert hidden['scale']==1 and hidden['equal_vertex_order']==354
    kappa7={7:Fraction(1),9:Fraction(-7),11:Fraction(21),13:Fraction(-35),
            15:Fraction(35),17:Fraction(-21),19:Fraction(7),21:Fraction(-1)}
    expected=pmul(kappa7,{2:Fraction(3),4:Fraction(3),6:Fraction(1)})
    assert hidden['delta_L7']==encode_poly(expected)
    rank=[]
    for R in range(1,8):
        keys=sorted({h for r in range(1,R+1) for h in coeffs[r]})
        rows=[]
        for r in range(1,R+1):
            for exp in sorted({e for p in coeffs[r].values() for e in p}):
                rows.append([coeffs[r].get(h,{}).get(exp,0) for h in keys])
        reduced,_=rref(rows,len(keys))
        rank.append(len(reduced))
    assert rank==[1,1,2,5,8,12,17]
    out={'schema':'singularity.volume7.observation-witness.v1',
         'dependency_head':'517d6cf1d2fdd2f5369011db55a1e4bb2b51c7fd',
         'definition':'positive signed components form A; negative components form B; delta=A-B',
         'components':'k:mask means deterministic completion in vol7_completion.py; 0:0 means girth8 padding graph',
         'cumulative_observation_ranks':rank,'seventh_rank_gain':5,
         'hidden_house_witness':hidden,'isolated_seven_core_witnesses':isolated}
    target=HERE/'vol7_observation.json'
    target.write_text(json.dumps(out,indent=2)+'\n')
    print('Verified21 isolated seven-core pairs,354-vertex hidden-house pair; ranks',rank)

if __name__=='__main__':main()
