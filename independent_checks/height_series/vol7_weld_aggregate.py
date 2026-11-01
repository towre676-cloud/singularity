#!/usr/bin/env python3
"""A deterministic witness separating seventh motifs from their observable sum.

Two ring orders have the same multiset of six-vertex two-port units.
The first seven observations agree while two seven-vertex motif counts
change with opposite signs. Both motifs have eight edges, so the observable
correction sees their sum. This is the precise reason to avoid equating
coefficient agreement with agreement of each individual motif count.
The transfer enumerator sums all heights exactly, retaining all q powers.
"""
from collections import defaultdict
from functools import lru_cache
from itertools import combinations
import json
from math import comb
from pathlib import Path

HERE=Path(__file__).resolve().parent
UNIT_MASKS={'A_prism_minus_spoke':5941,'B_K33_minus_edge':2012,'C_prism_minus_triangle_edge':1916}


def unit(mask):
    edges=[e for b,e in enumerate(combinations(range(6),2)) if mask>>b&1]
    d=[0]*6
    for a,b in edges:d[a]+=1;d[b]+=1
    ports=[v for v in range(6) if d[v]==2]
    assert len(ports)==2 and all(x in(2,3) for x in d)
    return edges,ports


def ring_edges(word):
    edges=[]
    for i,name in enumerate(word):
        es,_=unit(UNIT_MASKS[name])
        edges.extend((6*i+a,6*i+b) for a,b in es)
    for i,name in enumerate(word):
        j=(i+1)%len(word)
        _,ports=unit(UNIT_MASKS[name]);_,nextports=unit(UNIT_MASKS[word[j]])
        edges.append(tuple(sorted((6*i+ports[1],6*j+nextports[0]))))
    return sorted(edges)


def compositions(total,parts):
    if parts==1:yield (total,)
    else:
        for x in range(total+1):
            for rest in compositions(total-x,parts-1):yield (x,)+rest


@lru_cache(None)
def kernel(name,R):
    edges,ports=unit(UNIT_MASKS[name]);out=defaultdict(int)
    for r in range(R+1):
        for h in compositions(r,6):
            energy=3*sum(x*x for x in h)-2*sum(h[a]*h[b] for a,b in edges)
            out[(r,h[ports[0]],h[ports[1]],energy)]+=1
    byvolume=[[] for _ in range(R+1)]
    for (r,left,right,energy),c in out.items():byvolume[r].append((left,right,energy,c))
    return byvolume


def ring_series(word,R=7):
    dp={}
    for r,rows in enumerate(kernel(word[0],R)):
        for left,right,energy,c in rows:
            dp[(r,left,right,energy)]=dp.get((r,left,right,energy),0)+c
    for name in word[1:]:
        out=defaultdict(int);K=kernel(name,R)
        for (r,start,previous,energy),c in dp.items():
            for t in range(R-r+1):
                for left,right,en,c2 in K[t]:
                    out[(r+t,start,right,energy+en-2*previous*left)]+=c*c2
        dp=out
    answer=[defaultdict(int) for _ in range(R+1)]
    for (r,start,last,energy),c in dp.items():answer[r][energy-2*start*last]+=c
    for r,p in enumerate(answer):assert sum(p.values())==comb(6*len(word)+r-1,r)
    return [dict(sorted(p.items())) for p in answer]


def cycle_port_profile(name,length):
    edges,ports=unit(UNIT_MASKS[name]);adj=[set() for _ in range(6)]
    for a,b in edges:adj[a].add(b);adj[b].add(a)
    counts=[]
    for p in ports:
        cycles=set()
        def rec(path):
            if len(path)==length:
                if p in adj[path[-1]]:cycles.add(tuple(sorted(tuple(sorted((path[i],path[(i+1)%length]))) for i in range(length))))
                return
            for nxt in adj[path[-1]]:
                if nxt not in path:rec(path+[nxt])
        rec([p]);counts.append(len(cycles))
    return counts


def main():
    A,B,C=UNIT_MASKS
    words=[[A,B,C,C],[A,C,B,C]]
    series=[ring_series(w) for w in words]
    for r in range(7):assert series[0][r]==series[1][r]
    d={e:series[1][7].get(e,0)-series[0][7].get(e,0) for e in set(series[0][7])|set(series[1][7])}
    d={str(e):c for e,c in sorted(d.items()) if c}
    assert not d
    from vol7_lib import count_patterns, degrees_of, edges_of
    counts=[count_patterns(24,ring_edges(w)) for w in words]
    core_delta={}
    for k,m in sorted(set(counts[0])|set(counts[1])):
        if min(degrees_of(m,k))<2:continue
        delta=counts[1].get((k,m),0)-counts[0].get((k,m),0)
        if delta:core_delta[f'{k}:{m}']={'vertices':k,'mask':m,'edges':edges_of(m,k),'edge_count':m.bit_count(),'delta':delta}
    assert {key:x['delta'] for key,x in core_delta.items()}=={'7:42418':1,'7:57777':-1}
    # Validate transfer against an independent full edge-list enumerator on
    # a 12-vertex ring. Full volume-seven verification costs only 31,824
    # weak compositions here and does not use a cumulant or reduction law.
    from vol7_witnesses import coefficient
    small=[A,B]
    ss=ring_series(small)
    for r in range(1,8):assert ss[r]==coefficient(12,ring_edges(small),r)
    profiles={name:{'ports':unit(mask)[1],'triangle_counts':cycle_port_profile(name,3),'square_counts':cycle_port_profile(name,4)} for name,mask in UNIT_MASKS.items()}
    out={'definition':'delta = second ring - first ring; q exponents as polynomial keys',
         'n':24,'units':{name:{'mask':mask,'edges':unit(mask)[0],**profiles[name]} for name,mask in UNIT_MASKS.items()},
         'rings':[{'word':w,'edges':ring_edges(w),'L':[dict((str(e),c) for e,c in p.items()) for p in S]} for w,S in zip(words,series)],
         'agree_through':7,'delta_L7':d,'delta_leafless_core_counts':core_delta,
         'triangle_square_barbell_delta':-1,'two_triangles_distance_two_delta':1,'verification':'Exact unit transfer through7; direct weak-composition cross-check through7 on12-vertex two-unit ring; all coefficient totals checked'}
    (HERE/'vol7_weld_aggregate.json').write_text(json.dumps(out,indent=2)+'\n')
    print('Weld-ring exact aggregate witness: equal L through7, two seventh motifs differ oppositely.');print('Port profiles:',profiles)

if __name__=='__main__':main()
