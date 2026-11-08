#!/usr/bin/env python3
"""Exact connected realization certificates; stdlib only. No network required."""
from collections import Counter, deque
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
from hashlib import sha256
import argparse, json
from vol8_lib import (degrees_of, edges_of, connected_types, count_patterns,
                     canonical, mask_from_edges, connected_mask, height_series)
from vol8_law import rref
from vol8_reader import factors, invert
from vol8_completion import girth12_graph, girth, connected_subset_counts

HERE = Path(__file__).resolve().parent
KEEP = (0, 1, 2, 3, 5, 6)

def distances(n, es, starts):
    adj = [set() for _ in range(n)]
    for a,b in es: adj[a].add(b); adj[b].add(a)
    d = {v:0 for v in starts}; q = deque(starts)
    while q:
        v = q.popleft()
        for w in adj[v]:
            if w not in d: d[w]=d[v]+1; q.append(w)
    return d

def validate(n, es):
    assert all(0<=a<b<n for a,b in es)
    assert len(set(es))==len(es)
    assert Counter(v for e in es for v in e)==Counter({v:3 for v in range(n)})
    assert len(distances(n,es,[0]))==n

def independent_cores(k,m):
    """Independent edge-subset enumeration, with no spanning-pattern cache."""
    es = edges_of(m,k); out=Counter()
    for bits in range(1,1<<len(es)):
        sub=[e for i,e in enumerate(es) if bits>>i&1]
        ds=Counter(v for e in sub for v in e)
        if min(ds.values())<2: continue
        vs=sorted(ds); rename={v:i for i,v in enumerate(vs)}
        mm=mask_from_edges(len(vs),[(rename[a],rename[b]) for a,b in sub])
        if connected_mask(mm,len(vs)):out[(len(vs),canonical(mm,len(vs)))]+=1
    return out

def port_certificate():
    n,es=girth12_graph(); cut=es[0]
    d=distances(n,es,cut)
    site=next(e for e in es if min(d[v] for v in e)>=4)
    validate(n,es)
    assert girth(n,es)==12
    assert len(distances(n,[e for e in es if e!=cut],[0]))==n
    return {'n':n,'edges':es,'cut':cut,'site':site,
            'girth':12,'site_to_cut_distance':min(d[v] for v in site)}

def recipe(w):
    sides=[]
    for sign in (1,-1):
        seeds=[];K=D=0
        for h,v in sorted(w['signed_components'].items()):
            if h=='0:0' or v*sign<=0:continue
            k,m=map(int,h.split(':')); mult=abs(v)
            assert min(degrees_of(m,k))<3
            K+=k*mult;D+=(3*k-2*m.bit_count())*mult
            seeds.append({'k':k,'mask':m,'multiplicity':mult})
        sides.append({'seeds':seeds,'seed_vertices':K,'attachment_sites':D})
    # Original equal-order completion certificate implies this congruence.
    assert (sides[0]['seed_vertices']+sides[0]['attachment_sites']-
            sides[1]['seed_vertices']-sides[1]['attachment_sites'])%126==0
    base=[s['seed_vertices']+s['attachment_sites'] for s in sides]
    N=max(base[i]+126*max(2,sides[i]['attachment_sites']) for i in range(2))
    for i,s in enumerate(sides):
        assert (N-base[i])%126==0
        s['reservoir_blocks']=(N-base[i])//126;s['order']=N
        assert s['reservoir_blocks']>=max(2,s['attachment_sites'])
    return {'name':w['isolated_observable'],'scale':w['scale'],
            'delta_A_minus_B':{r:p for r,p in w['delta_log_coefficients'].items()},
            'sides':sides}

def materialize(s,port):
    K=s['seed_vertices'];t=s['reservoir_blocks'];es=[];stubs=[];n=0
    for h in s['seeds']:
        k,m=h['k'],h['mask']
        for _ in range(h['multiplicity']):
            es.extend((n+a,n+b) for a,b in edges_of(m,k))
            for v,d in enumerate(degrees_of(m,k)):stubs.extend([n+v]*(3-d))
            n+=k
    assert n==K and len(stubs)==s['attachment_sites']
    cut=tuple(port['cut']);site=tuple(port['site']);D=len(stubs)
    for i in range(t):
        off=K+126*i
        for a,b in port['edges']:
            if (a,b)==cut:continue
            if i<D and (a,b)==site:continue
            es.append((off+a,off+b))
        es.append((off+cut[1],K+126*((i+1)%t)+cut[0]))
        if i<D:
            x=K+126*t+i
            es.extend([(off+site[0],x),(off+site[1],x),(stubs[i],x)])
    es=sorted(tuple(sorted(e)) for e in es);n=K+126*t+D
    assert n==s['order'];validate(n,es)
    return n,es

def small_check():
    out=[]
    for n in (4,6,8):
        seen={};count=0
        for m in connected_types(n):
            if set(degrees_of(m,n))!={3}:continue
            hs=height_series(n,edges_of(m,n),7)
            sig=tuple(tuple(sorted(p.items())) for p in hs)
            assert sig not in seen, (n,m,seen.get(sig))
            seen[sig]=m;count+=1
        out.append({'n':n,'connected_cubic_types':count,'lower_collision_pairs':0})
    assert [r['connected_cubic_types'] for r in out]==[1,2,5]
    return out

def source_check():
    s=json.loads((HERE/'vol8_law.json').read_text())
    c={int(r):{(x['k'],x['mask']):{int(e):F(a) for e,a in x['polynomial'].items()}
       for x in data} for r,data in s['reduced_coefficients'].items()}
    keys=sorted({h for d in c.values() for h in d})
    unsat=[h for h in keys if h==(1,0) or min(degrees_of(h[1],h[0]))<3]
    rows=lambda rs:[[c[r].get(h,{}).get(e,0) for h in unsat] for r in rs
                   for e in sorted({e for p in c[r].values() for e in p})]
    ranks=[len(rref(rows(range(1,r+1)),len(unsat))[0]) for r in (7,8)]
    assert ranks==[15,21]
    # Verify every source coefficient modulo lower rows and the six factors.
    rr,piv=rref(rows(range(1,8)),len(unsat))
    natural=s['natural_observation_basis'][17:]
    coords=[{(x['k'],x['mask']):F(x['coefficient']) for x in nn['coordinates']} for nn in natural]
    ff=factors()
    for e in sorted({e for p in c[8].values() for e in p}|{e for p in ff for e in p}):
        row=[c[8].get(h,{}).get(e,0)-sum(ff[i].get(e,0)*coords[i].get(h,0) for i in KEEP) for h in unsat]
        for b,j in zip(rr,piv):
            a=row[j];row=[x-a*y for x,y in zip(row,b)]
        assert not any(row)
    return c,unsat,{'connected_large_lower_rank':15,'connected_large_total_rank':21,'new_rank':6,
          'forbidden_saturated_cores':[list(h) for h in keys if h not in unsat]}

def realization_basis_check(keys):
    C=sorted((h for h in keys if h!=(1,0)),key=lambda h:(h[0],h[1].bit_count(),h[1]));rows={};isolators={}
    for h in C:
        row=independent_cores(*h);rows[h]=row
        assert row[h]==1 and all(j==h or C.index(j)<C.index(h) for j in row)
        relation=Counter({h:1})
        for j,v in row.items():
            if j==h:continue
            for g,a in isolators[j].items():relation[g]-=v*a
        isolators[h]={g:a for g,a in relation.items() if a}
        assert all(sum(a*rows[g].get(j,0) for g,a in isolators[h].items())==int(j==h) for j in C)
    assert len(C)==92
    return {'nonsaturated_core_count':len(C),'seed_count_matrix_determinant':1,
            'integer_unit_isolators_verified':len(isolators),
            'universal_realization_scale':63,
            'meaning':'Every integer vector of 92 nonsaturated core differences, multiplied by 63, is realized by an equal-order connected cubic pair.'}

def panel_check(optimize):
    ff=[factors()[i] for i in KEEP]
    degrees=sorted({e for p in ff for e in p})
    best=None;full=0;total=0;ties=0
    candidates=combinations(degrees,6) if optimize else [(4,8,12,14,18,24)]
    for panel in candidates:
        total+=1
        try:inv,det=invert([[p.get(e,0) for p in ff] for e in panel])
        except ValueError:continue
        full+=1;norm=max(sum(map(abs,row)) for row in inv)
        if best is None or norm<best[0]:best=(norm,panel,inv,det);ties=1
        elif norm==best[0]:ties+=1
    assert best
    norm,panel,inv,det=best
    mat=[[p.get(e,0) for p in ff] for e in panel]
    for i in range(6):
        for j in range(6):
            assert sum(inv[i][k]*mat[k][j] for k in range(6))==int(i==j)
            assert sum(mat[i][k]*inv[k][j] for k in range(6))==int(i==j)
    return {'exhaustive':optimize,'degrees':list(panel),'determinant':str(det),
            'inverse_infinity_norm':str(norm),'inverse':[[str(x) for x in row] for row in inv],
            'subsets_checked':total,'invertible':full,'optimal_ties':ties}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--optimize',action='store_true')
    ap.add_argument('--enumerate-connected',action='store_true')
    ap.add_argument('--output-dir', type=Path, required=True, help='Replay output directory; preserved evidence is never overwritten implicitly')
    args=ap.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    port=port_certificate();c,keys,rank=source_check()
    obs=json.loads((HERE/'vol8_observation.json').read_text())
    ws=[obs['seven_isolated_observation_witnesses'][i] for i in KEEP]
    allseeds={tuple(map(int,h.split(':'))) for w in ws for h in w['signed_components'] if h!='0:0'}
    cores={h:independent_cores(*h) for h in allseeds}
    for h,counts in cores.items():
        got={j:v for j,v in count_patterns(h[0],edges_of(h[1],h[0]),8).items() if min(degrees_of(j[1],j[0]))>=2}
        assert got==counts
    recipes=[]
    for w in ws:
        actual=Counter()
        for h,mult in w['signed_components'].items():
            if h=='0:0':continue
            for j,v in cores[tuple(map(int,h.split(':')))].items():actual[j]+=mult*v
        expected={tuple(map(int,h.split(':'))):v for h,v in w['core_differences'].items()}
        assert {h:v for h,v in actual.items() if v}==expected
        for r in range(1,9):
            exps={e for h in actual for e in c[r].get(h,{})};p={}
            for e in exps:
                v=sum(v*c[r].get(h,{}).get(e,0) for h,v in actual.items())
                if v:p[str(e)]=str(v)
            assert p==w['delta_log_coefficients'][str(r)]
        recipes.append(recipe(w))
    cert={'schema':'singularity.connected-volume8.v1','base_commit':'17f033ea9a1e6d93224e946a341f7a0e545ee64a',
          'delta_convention':'A minus B','coordinates':[w['isolated_observable'] for w in ws],
          **rank,'small_graph_check':small_check(),'port_certificate':port,
          'universal_core_realization':realization_basis_check(keys),
          'independently_enumerated_seed_types':len(cores),'six_connected_witness_recipes':recipes,
          'panel':panel_check(args.optimize)}
    if args.enumerate_connected:
        rec=next(r for r in recipes if r['name']=='Theta223');got=[]
        for i,s in enumerate(rec['sides']):
            n,es=materialize(s,port)
            # Every small leafless core touches a seed; structural exclusion of
            # reservoir-only and cross-seed cores is proved in the report.
            counts=connected_subset_counts(n,es,8,root_limit=s['seed_vertices'])
            got.append({h:v for h,v in counts.items() if min(degrees_of(h[1],h[0]))>=2})
            (args.output_dir/f'connected_theta_{i}.json').write_text(json.dumps({'n':n,'edges':es},separators=(',',':'))+'\n')
        diff={h:got[0].get(h,0)-got[1].get(h,0) for h in set(got[0])|set(got[1])}
        expected=next(w for w in ws if w['isolated_observable']=='Theta223')['core_differences']
        assert {f'{k}:{m}':v for (k,m),v in diff.items() if v}==expected
        cert['connected_edge_list_replay']={'name':'Theta223','order':rec['sides'][0]['order'],
            'method':'independent connected-support enumeration rooted at every seed vertex',
            'delta_core_counts':expected}
    (args.output_dir/'connected_certificate.json').write_text(json.dumps(cert,indent=2)+'\n')
    print(json.dumps({k:v for k,v in cert.items() if k not in ('port_certificate','six_connected_witness_recipes','panel')},indent=2),flush=True)
    print('panel',cert['panel'],flush=True)

if __name__=='__main__':main()
