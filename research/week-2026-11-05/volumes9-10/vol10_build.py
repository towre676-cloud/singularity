"""Tenth-order extension using fixed-excess kernels and exact leaf reduction."""
from pathlib import Path
from itertools import combinations
from functools import lru_cache
from fractions import Fraction as Q
from collections import Counter
import json,time
import pynauty as pn
import vol9_build as old
from vol9_build import lib,red,parse_g6,nauty_graph,rows,encode
from vol8_offdiagonal import first_off_diagonal,second_off_diagonal
from vol8_law import rref
from defect_kernel import defect_kernel
P=Path(__file__).resolve().parent
for k in (10,):
 lib.PAIRS[k]=tuple(combinations(range(k),2));lib.PIDX[k]={p:i for i,p in enumerate(lib.PAIRS[k])}
@lru_cache(None)
def canon10(m):
 es=lib.edges_of(m,10);order=pn.canon_label(nauty_graph(10,es));inv={v:i for i,v in enumerate(order)}
 return lib.mask_from_edges(10,[(inv[u],inv[v]) for u,v in es])
basecanon=red.canonical;baseaut=red.automorphisms
red.canonical=lambda k,m:canon10(m) if k==10 else basecanon(k,m)
def auto(k,m):
 if k<10:return baseaut(k,m)
 _,a,b,_,_=pn.autgrp(nauty_graph(k,lib.edges_of(m,k)));assert a==int(a);return int(a)*10**b
red.automorphisms=auto

def catalogue10():
 path=P/'catalogue10.json'
 if path.exists():return json.loads(path.read_text())['masks']
 external=set()
 for s in (P/'subcubic10.g6').read_text().splitlines():
  k,es=parse_g6(s);assert k==10;external.add(canon10(lib.mask_from_edges(k,es)))
 grown=set();candidates=0
 for m in old.catalogue9():
  es=lib.edges_of(m,9);eligible=[v for v,d in enumerate(lib.degrees_of(m,9)) if d<3]
  for t in range(1,min(3,len(eligible))+1):
   for vs in combinations(eligible,t):
    grown.add(canon10(lib.mask_from_edges(10,es+tuple((v,9) for v in vs))));candidates+=1
 assert external==grown
 masks=sorted(external,key=lambda m:(m.bit_count(),m))
 hist=Counter(m.bit_count() for m in masks if min(lib.degrees_of(m,10))>=2)
 path.write_text(json.dumps({'masks':masks,'connected_types':len(masks),'leafless_histogram':dict(hist),'growth_candidates':candidates,'two_route_agreement':True},indent=2)+'\n')
 print('catalogue10',len(masks),dict(hist),flush=True);return masks

def main():
 start=time.time();cat=catalogue10();total={};forms=[]
 for k in range(1,11):
  path=P/f'v10_contribution{k}.json'
  if path.exists():
   d=json.loads(path.read_text());co={(x['k'],x['mask']):{int(e):Q(a) for e,a in x['polynomial'].items()} for x in d['coefficients']};forms+=d['normal_forms']
  else:
   co={};nfdata=[]
   masks=cat if k==10 else old.catalogue9() if k==9 else lib.connected_types(k)
   for m in masks:
    if k<=6:p=lib.beta_coeffs(m,k,10)[10]
    elif k==7:p=defect_kernel(k,lib.edges_of(m,k),3)
    elif k==8:p=second_off_diagonal(m,k)
    elif k==9:p=first_off_diagonal(m,k)
    else:p=lib.expected_top_beta(m,k)
    nf=red.normal_form(k,m);nf={(s,lib.canonical(t,s) if s<9 else t):a for(s,t),a in nf.items()}
    nfdata.append({'k':k,'mask':m,'normal_form':[[s,t,str(a)] for(s,t),a in sorted(nf.items())]})
    for h,a in nf.items():co[h]=lib.padd(co.get(h,{}),p,a)
   path.write_text(json.dumps({'coefficients':encode(co),'normal_forms':nfdata},indent=2)+'\n');forms+=nfdata
  for h,p in co.items():total[h]=lib.padd(total.get(h,{}),p)
  print('size',k,'seconds',round(time.time()-start,2),flush=True)
 saved=json.loads((P/'vol9_law.json').read_text());c={int(r):{(x['k'],x['mask']):{int(e):Q(a) for e,a in x['polynomial'].items()} for x in xs} for r,xs in saved['coefficient_rows'].items()}
 c[10]={h:p for h,p in total.items() if p};keys=sorted({h for d in c.values() for h in d});lab,lo=rows(c,9,keys);rr,piv,trans=rref(lo,len(keys),True);assert len(rr)==34
 residual={};elim=[]
 for e in sorted({e for h,p in c[10].items() if h[0]<10 for e in p}):
  row=[c[10].get(h,{}).get(e,0) if h[0]<10 else 0 for h in keys];w={}
  for base,j,tr in zip(rr,piv,trans):
   a=row[j]
   if a:
    row=[x-a*y for x,y in zip(row,base)];w=lib.padd(w,tr,a)
  elim.append({'qexp':e,'lower_rows':[[*lab[j],str(a)] for j,a in sorted(w.items())]})
  for h,a in zip(keys,row):
   if a:residual.setdefault(h,{})[e]=a
 _,ar=rows(c,10,keys);rank=len(rref(ar,len(keys))[0])
 out={'schema':'singularity.volume10.law/1','base_commit':saved['base_commit'],'coefficient_rows':{str(r):encode(d) for r,d in c.items()},'lower_rank':34,'total_rank':rank,'new_rank':rank-34,'core_keys':keys,'tenth_lower_support_residual':encode(residual),'lower_elimination':elim,'normal_forms':forms,'seconds':time.time()-start}
 (P/'vol10_law.json').write_text(json.dumps(out,indent=2)+'\n');print('RANK',rank,'NEW',rank-34,'RESIDUAL',len(residual),flush=True)
if __name__=='__main__':main()
