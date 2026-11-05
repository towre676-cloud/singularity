"""Exact ninth-order cubic law; checkpoint each support size."""
from pathlib import Path
import json,time,sys
from collections import Counter
from fractions import Fraction as Q
from itertools import combinations
from functools import lru_cache
import pynauty as pn
import vol8_lib as lib
import vol8_reduction as red
from vol8_offdiagonal import first_off_diagonal,second_off_diagonal
from vol8_law import rref
HERE=Path(__file__).resolve().parent
lib.PAIRS[9]=tuple(combinations(range(9),2))
lib.PIDX[9]={p:i for i,p in enumerate(lib.PAIRS[9])}

def nauty_graph(k,es):
    adj={i:[] for i in range(k)}
    for u,v in es:adj[u].append(v);adj[v].append(u)
    return pn.Graph(k,adjacency_dict=adj)

@lru_cache(None)
def canonical9(mask):
    es=lib.edges_of(mask,9)
    order=pn.canon_label(nauty_graph(9,es))
    inv={v:i for i,v in enumerate(order)}
    return lib.mask_from_edges(9,[(inv[u],inv[v]) for u,v in es])

oldcanon=red.canonical
oldaut=red.automorphisms
def canon(k,m):return canonical9(m) if k==9 else oldcanon(k,m)
def aut(k,m):
    if k<9:return oldaut(k,m)
    _,a,b,_,_=pn.autgrp(nauty_graph(k,lib.edges_of(m,k)))
    assert a==int(a)
    return int(a)*10**b
red.canonical=canon
red.automorphisms=aut

def parse_g6(line):
    data=line.strip().encode();n=data[0]-63
    bits=[(b-63>>shift)&1 for b in data[1:] for shift in range(5,-1,-1)]
    es=[];i=0
    for v in range(1,n):
        for u in range(v):
            if bits[i]:es.append((u,v))
            i+=1
    return n,es

def catalogue9():
    path=HERE/'catalogue9.json'
    if path.exists():return json.loads(path.read_text())['masks']
    # First route: nauty's canonical augmentation catalogue.
    external=set()
    for line in (HERE/'subcubic9.g6').read_text().splitlines():
        n,es=parse_g6(line);assert n==9
        external.add(canonical9(lib.mask_from_edges(9,es)))
    # Second route: extend every connected eight-vertex subcubic type.
    grown=set();raw=0
    for m in lib.connected_types(8):
        es=lib.edges_of(m,8);eligible=[v for v,d in enumerate(lib.degrees_of(m,8)) if d<3]
        for t in range(1, min(3,len(eligible))+1):
            for vs in combinations(eligible,t):
                mask=lib.mask_from_edges(9,es+tuple((v,8) for v in vs))
                grown.add(canonical9(mask));raw+=1
    assert external==grown,(len(external),len(grown))
    masks=sorted(external,key=lambda m:(m.bit_count(),m))
    hist=Counter(m.bit_count() for m in masks)
    core=Counter(m.bit_count() for m in masks if min(lib.degrees_of(m,9))>=2)
    data={'masks':masks,'connected_types':len(masks),'edge_histogram':dict(hist),
          'leafless_histogram':dict(core),'growth_candidates':raw,'two_route_agreement':True}
    path.write_text(json.dumps(data,indent=2)+'\n')
    print('catalogue9',len(masks),'leafless',dict(core),flush=True)
    return masks

def load_coeffs():
    saved=json.loads((HERE/'vol8_law.json').read_text())
    return {int(r):{(x['k'],x['mask']):{int(e):Q(c) for e,c in x['polynomial'].items()}
                   for x in data} for r,data in saved['reduced_coefficients'].items()}

def rows(coeffs,R,keys):
    labels=[];out=[]
    for r in range(1,R+1):
        for e in sorted({e for p in coeffs[r].values() for e in p}):
            row=[coeffs[r].get(h,{}).get(e,0) for h in keys]
            if any(row):labels.append((r,e));out.append(row)
    return labels,out

def encode(data):
    return [{'k':k,'mask':m,'polynomial':{str(e):str(c) for e,c in sorted(p.items())}}
            for(k,m),p in sorted(data.items()) if p]

def main():
    start=time.time();cat9=catalogue9();c=load_coeffs()
    six={x['mask']:{int(e):Q(a) for e,a in x['polynomial'].items()}
         for x in json.loads((HERE/'defect_certificate.json').read_text())['examples'] if x['k']==6}
    total={};nfs=[]
    for k in range(1,10):
        cp=HERE/f'contribution{k}.json'
        if cp.exists():
            data=json.loads(cp.read_text())
            contribution={(x['k'],x['mask']):{int(e):Q(v) for e,v in x['polynomial'].items()}
                          for x in data['coefficients']}
            nfs+=data['normal_forms']
        else:
            contribution={};forms=[]
            for m in (cat9 if k==9 else lib.connected_types(k)):
                if k<=5:p=lib.beta_coeffs(m,k,9)[9]
                elif k==6:p=six[m]
                elif k==7:p=second_off_diagonal(m,k)
                elif k==8:p=first_off_diagonal(m,k)
                else:p=lib.expected_top_beta(m,k)
                nf=red.normal_form(k,m)
                # Preserve the source convention on all sizes <= 8.
                nf={(s,lib.canonical(t,s) if s<9 else t):a for(s,t),a in nf.items()}
                forms.append({'k':k,'mask':m,'normal_form':[[s,t,str(a)] for(s,t),a in sorted(nf.items())]})
                for h,a in nf.items():contribution[h]=lib.padd(contribution.get(h,{}),p,a)
            cp.write_text(json.dumps({'coefficients':encode(contribution),'normal_forms':forms},indent=2)+'\n')
            nfs+=forms
        for h,p in contribution.items():total[h]=lib.padd(total.get(h,{}),p)
        print('size',k,'terms',len(contribution),'seconds',round(time.time()-start,2),flush=True)
    c[9]={h:p for h,p in total.items() if p}
    keys=sorted({h for data in c.values() for h in data})
    labs,lo=rows(c,8,keys);rr,piv,trans=rref(lo,len(keys),True)
    assert len(rr)==24
    residual={};elimination=[]
    for e in sorted({e for h,p in c[9].items() if h[0]<9 for e in p}):
        row=[c[9].get(h,{}).get(e,0) if h[0]<9 else 0 for h in keys]
        witness={}
        for base,j,tr in zip(rr,piv,trans):
            f=row[j]
            if f:
                row=[a-f*b for a,b in zip(row,base)]
                witness=lib.padd(witness,tr,f)
        elimination.append({'qexp':e,'lower_rows':[[*labs[i],str(a)] for i,a in sorted(witness.items())]})
        for h,a in zip(keys,row):
            if a:residual.setdefault(h,{})[e]=a
    _,allrows=rows(c,9,keys)
    rank=len(rref(allrows,len(keys))[0])
    out={'schema':'singularity.volume9.law/1','base_commit':'17f033ea9a1e6d93224e946a341f7a0e545ee64a',
         'coefficient_rows':{str(r):encode(data) for r,data in c.items()},
         'lower_rank':24,'total_rank':rank,'new_rank':rank-24,'core_keys':keys,
         'ninth_lower_support_residual':encode(residual),'lower_elimination':elimination,
         'normal_forms':nfs,'seconds':time.time()-start}
    (HERE/'vol9_law.json').write_text(json.dumps(out,indent=2)+'\n')
    print('RANK',rank,'NEW',rank-24,'RESIDUAL',len(residual),flush=True)
    for h,p in residual.items():print(h,p,flush=True)

if __name__=='__main__':main()
