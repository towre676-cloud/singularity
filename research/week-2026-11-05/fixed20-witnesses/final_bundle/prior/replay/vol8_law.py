#!/usr/bin/env python3
"""Exact cubic-core normal form and height-agreement quotient through order 8."""
from collections import defaultdict
from fractions import Fraction
from functools import lru_cache
import json
from pathlib import Path
from vol8_lib import (connected_types,beta_coeffs,canonical,padd,encode_poly,degrees_of,expected_top_beta)
from vol8_reduction import normal_form

@lru_cache(None)
def reduced_coefficients(R=8):
    """Return {volume: {(core_k,core_mask): {qexp:Fraction}}} for log L."""
    result={r:{} for r in range(1,R+1)}
    for k in range(1,R+1):
        for m in connected_types(k):
            beta=({R:expected_top_beta(m,k)} if k==R else dict(enumerate(beta_coeffs(m,k,R))))
            nf={(ck,canonical(cm,ck)):c for (ck,cm),c in normal_form(k,m).items()}
            for r in range(k,R+1):
                if not beta[r]: continue
                for key,c in nf.items():
                    result[r][key]=padd(result[r].get(key,{}),beta[r],c)
    return {r:{key:p for key,p in data.items() if p} for r,data in result.items()}

def rref(rows,ncols,with_transforms=False):
    rows=[list(map(Fraction,row)) for row in rows if any(row)]
    transforms=[{i:Fraction(1)} for i in range(len(rows))]
    pivot_cols=[]; r=0
    for c in range(ncols):
        pivot=next((i for i in range(r,len(rows)) if rows[i][c]),None)
        if pivot is None: continue
        rows[r],rows[pivot]=rows[pivot],rows[r]
        transforms[r],transforms[pivot]=transforms[pivot],transforms[r]
        scale=rows[r][c]; rows[r]=[v/scale for v in rows[r]]
        transforms[r]={j:v/scale for j,v in transforms[r].items()}
        for i in range(len(rows)):
            if i!=r and rows[i][c]:
                f=rows[i][c]; rows[i]=[a-f*b for a,b in zip(rows[i],rows[r])]
                transforms[i]=padd(transforms[i],transforms[r],-f)
        pivot_cols.append(c);r+=1
        if r==len(rows):break
    return (rows[:r],pivot_cols,transforms[:r]) if with_transforms else (rows[:r],pivot_cols)

def quotient_data(coeffs,R=8):
    keys=sorted({key for r,data in coeffs.items() if r<R for key in data})
    idx={key:i for i,key in enumerate(keys)}
    rows=[];labels=[]
    for r in range(1,R):
        exps=sorted({e for p in coeffs[r].values() for e in p})
        for e in exps:
            row=[coeffs[r].get(key,{}).get(e,Fraction(0)) for key in keys]
            if any(row):rows.append(row);labels.append((r,e))
    reduced,pivots,transforms=rref(rows,len(keys),True)
    residual={};elimination={}
    for e in sorted({e for key,p in coeffs[R].items() if key[0]<R for e in p}):
        row=[coeffs[R].get(key,{}).get(e,Fraction(0)) for key in keys]
        for rr,p,transform in zip(reduced,pivots,transforms):
            f=row[p]
            if f:
                row=[a-f*b for a,b in zip(row,rr)]
                for source,c in transform.items():
                    label=labels[source]
                    elimination.setdefault(label,{})[e]=elimination.setdefault(label,{}).get(e,Fraction(0))+f*c
        for key,c in zip(keys,row):
            if c:residual.setdefault(key,{})[e]=c
    return {'keys':keys,'lower_rank':len(pivots),'lower_rref':reduced,'pivots':pivots,'eighth_lower_support_residual':residual,'row_labels':labels,'rref_transforms':transforms,
            'eighth_elimination':{key:{e:c for e,c in p.items() if c} for key,p in elimination.items() if any(p.values())}}


def coefficient_rows(coeffs,R,keys=None):
    if keys is None:keys=sorted({key for r,data in coeffs.items() if r<=R for key in data})
    rows=[];labels=[]
    for r in range(1,R+1):
        for e in sorted({e for p in coeffs[r].values() for e in p}):
            row=[coeffs[r].get(key,{}).get(e,Fraction(0)) for key in keys]
            if any(row):rows.append(row);labels.append((r,e))
    return keys,rows,labels


def natural_observables(coeffs):
    """Natural J7 coordinates followed by seven new eighth observations."""
    keys,rows,labels=coefficient_rows(coeffs,8)
    rr,piv,trans=rref(rows,len(keys),True)
    definitions=[]
    for key in keys:
        if key[0]<=5:definitions.append(('N_%s_%s'%key,{key:Fraction(1)}))
    for k in(6,7):
        for e in range(k,3*k//2+1):
            definitions.append(('S_%s_%s'%(k,e),{key:Fraction(1) for key in keys if key[0]==k and key[1].bit_count()==e}))
    lower_count=len(definitions)
    assert lower_count==17
    definitions += [
      ('Q_8_0',{(8,m):Fraction(1) for m in connected_types(8) if min(degrees_of(m,8))>=2 and m.bit_count()==8}|{(6,6355):Fraction(1)}),
      ('Q_8_1',{(8,m):Fraction(1) for m in connected_types(8) if min(degrees_of(m,8))>=2 and m.bit_count()==9}|{(6,17142):Fraction(1),(6,5941):Fraction(-2)}),
    ]
    for e in(10,11,12):definitions.append(('S_8_%s'%e,{key:Fraction(1) for key in keys if key[0]==8 and key[1].bit_count()==e}))
    definitions += [('T_6_Theta223',{(6,956):Fraction(1)}),('D_6_closed_diamond',{(6,17142):Fraction(1)})]
    natural_rows=[[v.get(key,Fraction(0)) for key in keys] for name,v in definitions]
    assert rref(natural_rows,len(keys))[0]==rr and len(rr)==24
    lowkeys,lowrows,_=coefficient_rows(coeffs,7,keys)
    assert rref(natural_rows[:17],len(keys))[0]==rref(lowrows,len(keys))[0]
    certificates=[]
    for name,v in definitions:
        target=[v.get(key,Fraction(0)) for key in keys];combo={}
        for row,p,transform in zip(rr,piv,trans):
            f=target[p]
            if f:
                target=[a-f*b for a,b in zip(target,row)]
                combo=padd(combo,transform,f)
        assert not any(target)
        certificates.append({'name':name,'coordinates':[{'k':k,'mask':m,'coefficient':str(a)} for(k,m),a in sorted(v.items())],
          'coefficient_row_witness':[{'volume':labels[j][0],'qexp':labels[j][1],'coefficient':str(a)} for j,a in sorted(combo.items())]})
    ranks=[]
    for R in range(1,9):
        kk,rows,_=coefficient_rows(coeffs,R)
        ranks.append(len(rref(rows,len(kk))[0]))
    assert ranks==[1,1,2,5,8,12,17,24]
    return {'cumulative_observation_ranks':ranks,'full_core_coordinate_count':len(keys),'lower_observation_count':lower_count,
      'natural_observation_basis':certificates,'eighth_new_observation_count':7}


def main():
    import time
    t=time.time();c=reduced_coefficients();q=quotient_data(c)
    print('lower rank',q['lower_rank'],'of',len(q['keys']),flush=True)
    print('residual',q['eighth_lower_support_residual'],flush=True)
    out={'schema':'singularity-volume-eight-cubic-core-law-v1',
      'mask_convention':'vol8_lib decreasing-degree canonical',
      'reduced_coefficients':{str(r):[
        {'k':k,'mask':m,'polynomial':encode_poly(p)} for (k,m),p in sorted(data.items())]
        for r,data in c.items()},
      'lower_core_keys':q['keys'],'lower_coefficient_rank':q['lower_rank'],
      'lower_coefficient_rref':[[str(x) for x in row] for row in q['lower_rref']],
      'lower_coefficient_pivots':q['pivots'],
      'lower_coefficient_row_labels':q['row_labels'],
      'lower_rref_witnesses':[[{'volume':q['row_labels'][j][0],'qexp':q['row_labels'][j][1],'coefficient':str(x)} for j,x in sorted(row.items())] for row in q['rref_transforms']],
      'eighth_lower_elimination':[{'source_volume':r,'source_qexp':e,'multiplier_q_polynomial':encode_poly(p)} for (r,e),p in sorted(q['eighth_elimination'].items())],
      'eighth_lower_support_residual':[
        {'k':k,'mask':m,'polynomial':encode_poly(p)} for (k,m),p in sorted(q['eighth_lower_support_residual'].items())]}
    out.update(natural_observables(c))
    target=Path(__file__).with_name('vol8_law.json')
    target.write_text(json.dumps(out,indent=2)+'\n')
    print('wrote',target.name,'in',round(time.time()-t,2),'seconds',flush=True)

if __name__=='__main__':main()
