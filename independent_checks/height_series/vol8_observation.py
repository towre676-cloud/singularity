#!/usr/bin/env python3
"""Exact cubic pairs isolating the60 eighth cores and seven new observations."""
from fractions import Fraction
import json
from pathlib import Path
from vol8_lib import encode_poly,padd,pmul
from vol8_law import reduced_coefficients,rref,coefficient_rows
from vol8_completion import isolation_data,realize_core_vector,key
HERE=Path(__file__).resolve().parent


def pair_record(vector,coeffs):
    relation,scale=realize_core_vector(vector)
    C,rows,_=isolation_data()
    actual={h:sum(mult*rows.get(g,{}).get(h,0) for g,mult in relation.items()) for h in C}
    assert all(actual[h]==scale*vector.get(h,0) for h in C)
    diff={}
    for r in range(1,9):
        p={}
        for h,mult in actual.items():p=padd(p,coeffs[r].get(h,{}),mult)
        diff[r]=p
    assert not any(diff[r] for r in range(1,8)) and diff[8]
    def order(g):return 126 if g==(0,0) else 382*g[0]-254*g[1].bit_count()
    na=sum(mult*order(g) for g,mult in relation.items() if mult>0)
    nb=sum(-mult*order(g) for g,mult in relation.items() if mult<0)
    assert na==nb
    return {'signed_components':{key(g):v for g,v in sorted(relation.items())},
      'equal_vertex_order':na,'scale':scale,
      'core_differences':{key(h):v for h,v in actual.items() if v},
      'delta_log_coefficients':{str(r):encode_poly(diff[r]) for r in range(1,9)},
      'delta_L8':encode_poly(diff[8])}


def new_observations(vector):
    s={e:sum(v for (k,m),v in vector.items() if k==8 and m.bit_count()==e) for e in range(8,13)}
    return [s[8]+vector.get((6,6355),0),s[9]-2*vector.get((6,5941),0)+vector.get((6,17142),0),s[10],s[11],s[12],vector.get((6,956),0),vector.get((6,17142),0)]


def main():
    from math import comb
    c=reduced_coefficients();C,_,_=isolation_data()
    top={key(h):pair_record({h:1},c) for h in C if h[0]==8}
    assert len(top)==60
    e_reps={e:next(h for h in C if h[0]==8 and h[1].bit_count()==e) for e in range(8,13)}
    vectors=[{e_reps[e]:1} for e in range(8,13)]
    vectors += [{(6,956):1,(6,1881):-1},
                {(6,17142):1,(6,5941):-1,e_reps[9]:-3}]
    labels=['Q0','Q1','S8_10','S8_11','S8_12','Theta223','closed_diamond']
    independent=[]
    kappa8={8+2*j:Fraction((-1)**j*comb(8,j)) for j in range(9)}
    f={-2:Fraction(1),0:Fraction(-1)};a={2:Fraction(3),4:Fraction(3),6:Fraction(1)}
    weights=[{0:Fraction(1)},f,pmul(f,f),pmul(pmul(f,f),f),pmul(pmul(f,f),pmul(f,f)),{e:-v for e,v in a.items()},pmul(f,a)]
    for i,(label,v) in enumerate(zip(labels,vectors)):
        assert new_observations(v)==[int(j==i) for j in range(7)]
        rec=pair_record(v,c)
        rec['isolated_observable']=label
        assert rec['delta_L8']==encode_poly({e:rec['scale']*x for e,x in pmul(kappa8,weights[i]).items()})
        independent.append(rec)
    ranks=[]
    for r in range(1,9):
        keys,rows,_=coefficient_rows(c,r);ranks.append(len(rref(rows,len(keys))[0]))
    assert ranks==[1,1,2,5,8,12,17,24]
    out={'schema':'singularity.volume8.observation-witness.v1',
      'dependency_head':'facb4506d1e9b1667b877815777566296572a4fb',
      'definition':'positive signed components form A; negative form B; delta=A-B',
      'components':'k:mask denotes girth12 cubic completion;0:0 denotes126-vertex girth12 padding graph',
      'cumulative_observation_ranks':ranks,'eighth_rank_gain':7,
      'isolated_eight_core_witnesses':top,'seven_isolated_observation_witnesses':independent}
    (HERE/'vol8_observation.json').write_text(json.dumps(out,indent=2)+'\n')
    print('Verified60 isolated eighth-core pairs and7 isolated observation pairs; ranks',ranks)
    print('Delayed observation pair orders:',[(r['isolated_observable'],r['equal_vertex_order']) for r in independent[5:]])

if __name__=='__main__':main()
