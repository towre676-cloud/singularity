#!/usr/bin/env python3
"""A connected deterministic weld pair first separated at volume eight.

A is the triangular prism with one spoke deleted; D is a diamond.
Weld their two degree-two ports in the ring orders AADD and ADAD.
Both resulting 20-vertex graphs are cubic. Exact transfer retains every
q coefficient. Direct global height enumeration independently checks
all observations through eight; no correction theorem is used by either
calculation.

For any two two-port units, write T_U=F_U J, where F_U is the unit
height kernel and J(b,c)=q^(-2bc) is a bridge. Coefficientwise finite
transfer traces satisfy the all-order identity
  L_ADAD - L_AADD = (1/2) trace([T_A,T_D]^2).
Our two units first make this ordering commutator visible at volume8.
"""
import argparse
from collections import defaultdict
from functools import lru_cache
from itertools import combinations
import json
from math import comb
from pathlib import Path

HERE=Path(__file__).resolve().parent
A_EDGES=[(0,1),(0,3),(0,5),(1,2),(1,5),(2,3),(2,4),(3,4)]
D_EDGES=[(0,1),(0,2),(0,3),(1,2),(1,3)]
UNITS={'A_prism_minus_spoke':(6,tuple(A_EDGES),(4,5)),
       'D_diamond':(4,tuple(D_EDGES),(2,3))}
WORDS=[('A_prism_minus_spoke','A_prism_minus_spoke','D_diamond','D_diamond'),
       ('A_prism_minus_spoke','D_diamond','A_prism_minus_spoke','D_diamond')]


def compositions(total,parts):
    if parts==1:yield (total,)
    else:
        for x in range(total+1):
            for tail in compositions(total-x,parts-1):yield (x,)+tail


def ring_graph(word):
    offsets=[];n=0;edges=[]
    for name in word:
        k,es,_=UNITS[name];offsets.append(n)
        edges.extend((n+a,n+b) for a,b in es);n+=k
    for i,name in enumerate(word):
        j=(i+1)%len(word)
        a=offsets[i]+UNITS[name][2][1]
        b=offsets[j]+UNITS[word[j]][2][0]
        edges.append(tuple(sorted((a,b))))
    return n,sorted(edges)


@lru_cache(None)
def unit_kernel(name,R):
    k,edges,ports=UNITS[name];out=defaultdict(int)
    for r in range(R+1):
        for h in compositions(r,k):
            energy=3*sum(x*x for x in h)-2*sum(h[a]*h[b] for a,b in edges)
            out[(r,h[ports[0]],h[ports[1]],energy)]+=1
    rows=[[] for _ in range(R+1)]
    for (r,left,right,energy),c in out.items():rows[r].append((left,right,energy,c))
    return rows


def ring_series(word,R=8):
    """Trace of the exact two-port transfer product, truncated in volume."""
    dp={}
    for r,rows in enumerate(unit_kernel(word[0],R)):
        for left,right,energy,c in rows:
            key=(r,left,right,energy);dp[key]=dp.get(key,0)+c
    for name in word[1:]:
        out=defaultdict(int);kernel=unit_kernel(name,R)
        for (r,start,previous,energy),c in dp.items():
            for t in range(R-r+1):
                for left,right,en,c2 in kernel[t]:
                    out[(r+t,start,right,energy+en-2*previous*left)]+=c*c2
        dp=out
    answer=[defaultdict(int) for _ in range(R+1)]
    for (r,start,last,energy),c in dp.items():answer[r][energy-2*start*last]+=c
    n=sum(UNITS[x][0] for x in word)
    for r,poly in enumerate(answer):assert sum(poly.values())==comb(n+r-1,r)
    return [dict(sorted(poly.items())) for poly in answer]


def difference(a,b):
    return {e:b.get(e,0)-a.get(e,0) for e in sorted(set(a)|set(b)) if a.get(e,0)!=b.get(e,0)}


def expected_difference():
    """-q^2(1-q^2)^9(1+2q^2)^2, expanded by integer arithmetic."""
    out=defaultdict(int)
    for i in range(10):
        for j,c in enumerate((1,4,4)):
            out[2+2*i+2*j]-=((-1)**i)*comb(9,i)*c
    return {e:c for e,c in sorted(out.items()) if c}



def main():
    parser=argparse.ArgumentParser();parser.add_argument('--replay',action='store_true');args=parser.parse_args()
    graphs=[ring_graph(w) for w in WORDS]
    from vol7_witnesses import coefficient, check_cubic
    for n,edges in graphs:check_cubic(n,edges)
    S=[ring_series(w) for w in WORDS]
    assert all(S[0][r]==S[1][r] for r in range(8))
    delta=difference(S[0][8],S[1][8]);assert delta==expected_difference()
    # Independent GLOBAL calculation: close each original edge directly.
    # Every weak composition of every volume<=8 is visited once.
    for i,(n,edges) in enumerate(graphs):
        for r in range(1,9):assert coefficient(n,edges,r)==S[i][r]
    from vol8_witnesses import motif_data
    motifs=motif_data(graphs[0][0],graphs[0][1],graphs[1][1])
    low={key:c for key,c in motifs['delta_leafless_core_counts'].items() if int(key.split(':')[0])<8}
    assert not low
    assert motifs['delta_eighth_core_edge_sums']=={'9':-9,'10':-6,'11':-1}
    output={'dependency_head':'facb450','definition':'delta = ADAD - AADD; q exponents as integer-polynomial keys',
            'units':{name:{'n':k,'edges':edges,'ports':ports} for name,(k,edges,ports) in UNITS.items()},
            'graphs':[{'word':w,'n':n,'edges':edges,'L':[{str(e):c for e,c in p.items()} for p in s]} for w,(n,edges),s in zip(WORDS,graphs,S)],
            'agree_through':7,'delta_L8':{str(e):c for e,c in delta.items()},
            'factorization':'-q^2 (1-q^2)^9 (1+2q^2)^2 = -kappa^8 f (f+3)^2',
            'delta_leafless_counts_through7':low,**motifs,
            'delta_eighth_core_patterns':[{'mask':int(key.split(':')[1]),'edge_count':int(key.split(':')[1]).bit_count(),'edges':__import__('vol8_lib').edges_of(int(key.split(':')[1]),8),'delta':c} for key,c in motifs['delta_leafless_core_counts'].items() if key.startswith('8:')],
            'all_order_transfer_identity':'L_ADAD - L_AADD = (1/2) trace([T_A,T_D]^2), T_U=F_U J, J(b,c)=q^(-2bc)',
            'verification':'Exact two-port transfer and independent global weak-composition enumeration, every volume1..8, both20-vertex graphs; totals binomial(n+r-1,r) checked.'}
    target=HERE/'vol8_weld.json'
    if args.replay:
        assert json.loads(target.read_text())==json.loads(json.dumps(output))
        print('Replayed20-vertex AADD/ADAD weld pair through8, independently enumerated globally.')
    else:
        target.write_text(json.dumps(output,indent=2)+'\n');print('Wrote',target)
    print('delta L8 =',output['factorization']);print('lower core delta:',low)

if __name__=='__main__':main()
