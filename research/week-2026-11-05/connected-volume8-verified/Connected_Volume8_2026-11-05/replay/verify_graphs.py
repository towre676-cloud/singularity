#!/usr/bin/env python3
"""Independent direct-height replay of the twelve 20-vertex graphs.
Requires a C++17 compiler. The height enumeration uses no core source law.
"""
import json, subprocess, tempfile
from pathlib import Path
from collections import Counter, deque
from fractions import Fraction as F
from vol8_reader import factors, invert
HERE=Path(__file__).resolve().parent

def check_graph(n,es):
    assert len(es)==3*n//2 and len({tuple(sorted(e)) for e in es})==len(es)
    assert all(0<=a<b<n for a,b in es)
    assert Counter(v for e in es for v in e)==Counter({v:3 for v in range(n)})
    for removed in [None]+list(map(tuple,es)):
        adj=[[] for _ in range(n)]
        for a,b in es:
            if (a,b)!=removed:adj[a].append(b);adj[b].append(a)
        seen={0};q=deque([0])
        while q:
            for v in adj[q.popleft()]:
                if v not in seen:seen.add(v);q.append(v)
        assert len(seen)==n

def encode(n,es):
    edges=set(map(tuple,es));bits=[int((i,j) in edges) for j in range(1,n) for i in range(j)]
    bits += [0]*((-len(bits))%6)
    return chr(n+63)+''.join(chr(63+sum(bits[i+j]<<(5-j) for j in range(6))) for i in range(0,len(bits),6))

def main():
    s=json.loads((HERE.parent/'fixed20_certificate.json').read_text())
    ff=[factors()[i] for i in (0,1,2,3,5,6)]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);exe=td/'direct'
        subprocess.run(['g++','-O3','-std=c++17',str(HERE/'direct_search.cpp'),'-o',str(exe)],check=True)
        for i,p in enumerate(s['pairs']):
            for key in ('A_edges','B_edges'):check_graph(20,p[key])
            inp=td/'graphs.g6';out=td/'out.json'
            inp.write_text('\n'.join(encode(20,p[k]) for k in ('A_edges','B_edges'))+'\n')
            subprocess.run([str(exe),str(inp),str(out)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            d=json.loads(out.read_text());assert len(d['pairs'])==1
            actual={int(e):F(a) for e,a in d['pairs'][0]['delta'].items()}
            expected=Counter()
            for a,f in zip(p['coordinates_B_minus_A'],ff):
                for e,b in f.items():expected[e]+=a*b
            assert actual=={e:a for e,a in expected.items() if a}
            print('direct height + bridgeless check',i,p['coordinates_B_minus_A'])
            if i==2:
                # Five independent observation rows, all blind to this pure Q0 pair.
                panel=(2,4,6,28,30)
                from vol8_law import rref
                assert len(rref([[f.get(e,0) for f in ff] for e in panel],6)[0])==5
                assert all(actual.get(e,0)==0 for e in panel)
                demo={'n':20,'panel':panel,'panel_rank':5,'delta_convention':'B minus A',
                      'A_edges':p['A_edges'],'B_edges':p['B_edges'],
                      'coordinates':p['coordinates_B_minus_A'],
                      'delta_eighth':{str(e):str(a) for e,a in actual.items()}}
                (HERE/'explicit_five_panel_collision.json').write_text(json.dumps(demo,indent=2)+'\n')
    inv,det=invert([p['coordinates_B_minus_A'] for p in s['pairs']]);assert det==1
    print('Six realized difference vectors: determinant 1. Explicit rank-five panel collision passed.')
if __name__=='__main__':main()
