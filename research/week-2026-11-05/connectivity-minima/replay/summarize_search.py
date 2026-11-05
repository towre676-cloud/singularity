#!/usr/bin/env python3
"""Validate regenerated full direct searches against the observed run summary."""
from pathlib import Path
import json
from verify_advance import decode,vector,connectivity
from vol8_law import rref
HERE=Path(__file__).resolve().parent

def main():
    expected=json.loads((HERE/'observed_run_summary.json').read_text());rows=[];first={}
    names=('Q0','Q1','S8_10','S8_11','Theta223','closed_diamond')
    for index,n in enumerate(expected['orders']):
        s=json.loads((HERE/f'search{n}.json').read_text());G=[decode(x)[1] for x in (HERE/f'cubic{n}.g6').read_text().splitlines()]
        assert s['graphs']==len(G)==expected['catalogue_counts'][index]
        assert len(s['pairs'])==expected['nonzero_reference_counts'][index]
        vv={1:[],2:[],3:[]};cache={}
        for p in s['pairs']:
            v=vector({int(e):a for e,a in p['delta'].items()})
            for i,a in enumerate(v):
                if a:first.setdefault(names[i],n)
            for j in (p['A'],p['B']):
                if j not in cache:cache[j]=next(k for k in (3,2,1) if connectivity(n,G[j],k))
            for k in range(1,min(cache[p['A']],cache[p['B']])+1):vv[k].append(v)
        ranks=[len(rref(vv[k],6)[0]) for k in (1,2,3)]
        assert ranks==[expected[x][index] for x in ('connected_ranks','bridgeless_ranks','three_edge_ranks')]
        rows.append({'n':n,'graphs':len(G),'nonzero_reference_pairs':len(s['pairs']),'ranks':ranks})
        print(rows[-1],flush=True)
    first['S8_11']=20
    assert first==expected['coordinate_first_orders']
    (HERE/'regenerated_full_search_certificate.json').write_text(json.dumps({'rows':rows,'first_exposures':first},indent=2)+'\n')

if __name__=='__main__':main()
