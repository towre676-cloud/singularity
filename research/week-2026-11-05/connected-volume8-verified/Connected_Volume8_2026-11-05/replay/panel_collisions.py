#!/usr/bin/env python3
"""Connected collisions for every <=5 coefficient panel; exact stdlib arithmetic.
Convention A minus B. Large graphs are finite recipes, not allocated edge lists.
"""
import json, math, argparse
from collections import Counter
from fractions import Fraction as F
from functools import reduce
from itertools import combinations
from pathlib import Path
from connected_check import KEEP, recipe, independent_cores
from vol8_reader import factors
from vol8_law import rref
HERE=Path(__file__).resolve().parent
FF=[factors()[i] for i in KEEP]
DEGREES=sorted({e for p in FF for e in p})
OBS=json.loads((HERE/'vol8_observation.json').read_text())
WS=[OBS['seven_isolated_observation_witnesses'][i] for i in KEEP]
SCALE=math.lcm(*(w['scale'] for w in WS))

def kernel(rows):
    rr,piv=rref(rows,6)
    free=next(j for j in range(6) if j not in piv)
    v=[F(0)]*6;v[free]=F(1)
    for row,j in zip(rr,piv):v[j]=-row[free]
    den=math.lcm(*(x.denominator for x in v))
    v=[int(x*den) for x in v];g=reduce(math.gcd,v)
    v=[x//g for x in v]
    assert any(v) and all(sum(a*b for a,b in zip(row,v))==0 for row in rows)
    return v,len(piv)

def signed_seeds(v):
    s=Counter()
    for a,w in zip(v,WS):
        m=a*(SCALE//w['scale'])
        for h,b in w['signed_components'].items():
            if h!='0:0':s[h]+=m*b
    return {h:a for h,a in sorted(s.items()) if a}

def polynomial(v):
    out=Counter()
    for a,p in zip(v,FF):
        for e,b in p.items():out[e]+=SCALE*a*b
    return {str(e):str(a) for e,a in sorted(out.items()) if a}

def collision(panel):
    if len(panel)>5 or len(set(panel))!=len(panel) or any(type(e)!=int or e<0 for e in panel):
        raise ValueError('Require at most five distinct nonnegative integer degrees')
    v,rank=kernel([[p.get(e,0) for p in FF] for e in panel]);s=signed_seeds(v);p=polynomial(v)
    assert p and all(F(p.get(str(e),'0'))==0 for e in panel)
    rec=recipe({'signed_components':s,'isolated_observable':'panel_kernel',
                'scale':SCALE,'delta_log_coefficients':{'8':p}})
    return {'panel':list(panel),'rank':rank,'primitive_kernel':v,
            'coordinate_difference':[SCALE*a for a in v],
            'signed_seeds':s,'delta_eighth':p,'connected_recipe':rec}

def verify_bases():
    # Independently enumerate seed edge subsets and evaluate the full inherited
    # source polynomial in every volume, not merely the observation vectors.
    src=json.loads((HERE/'vol8_law.json').read_text())
    c={int(r):{(x['k'],x['mask']):{int(e):F(a) for e,a in x['polynomial'].items()}
       for x in data} for r,data in src['reduced_coefficients'].items()}
    seeds={h for w in WS for h in w['signed_components'] if h!='0:0'}
    counts={h:independent_cores(*map(int,h.split(':'))) for h in seeds}
    for i,w in enumerate(WS):
        actual=Counter()
        for h,m in w['signed_components'].items():
            if h=='0:0':continue
            for j,a in counts[h].items():actual[j]+=m*a
        for r in range(1,9):
            out=Counter()
            for h,m in actual.items():
                for e,a in c[r].get(h,{}).items():out[e]+=m*a
            expected={} if r<8 else {e:w['scale']*a for e,a in FF[i].items()}
            assert {e:a for e,a in out.items() if a}==expected
    return len(seeds)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--panel',nargs='*',type=int)
    args=ap.parse_args();seed_count=verify_bases()
    if args.panel is not None:
        print(json.dumps(collision(args.panel),indent=2));return
    rows=[];ranks=Counter();best=None
    for pp in combinations(DEGREES,5):
        cert=collision(pp);ranks[cert['rank']]+=1
        n=cert['connected_recipe']['sides'][0]['order']
        rows.append({'panel':list(pp),'rank':cert['rank'],
                     'primitive_kernel':cert['primitive_kernel'],'common_order':n})
        if best is None or n<best['connected_recipe']['sides'][0]['order']:best=cert
    output={'schema':'singularity.connected-panel-collisions.v1',
        'delta_convention':'A minus B','scale':SCALE,'nonzero_coefficient_degrees':DEGREES,
        'verified_seed_types':seed_count,'five_panels_checked':len(rows),
        'panel_rank_counts':dict(sorted(ranks.items())),
        'coverage':'Every <=5 panel reduces to a subset of these fifteen nonzero rows and extends to a five-panel. Degrees outside them are identically zero.',
        'certificates':rows,'smallest_generated_recipe':best}
    (HERE/'panel_collisions.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('certificates','smallest_generated_recipe')},indent=2))
    print('Smallest generated order:',best['connected_recipe']['sides'][0]['order'])
if __name__=='__main__':main()
