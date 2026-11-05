"""Connectivity ranks, girth ranks, and direct-host checks at volume ten."""
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter
import json,time
import vol10_build
from vol9_build import lib,rows
from vol9_connectivity import capacity
from vol9_girth import girth
from vol8_law import rref
from vol9_verify_hosts import core_counts,coefficients_from_counts,direct_core_counts
P=Path(__file__).resolve().parent

def main():
 start=time.time();d=json.loads((P/'vol10_law.json').read_text())
 c={int(r):{(x['k'],x['mask']):{int(e):Q(a) for e,a in x['polynomial'].items()} for x in rr}
    for r,rr in d['coefficient_rows'].items()}
 keys=[tuple(h) for h in d['core_keys']];caps={h:capacity(*h) for h in keys if h[0]>1};gs={h:girth(*h) for h in caps}
 classes=[]
 for lam in range(4):
  kk=[h for h in keys if h==(1,0) or caps[h]>=lam]
  _,low=rows(c,9,kk);_,high=rows(c,10,kk)
  a=len(rref(low,len(kk))[0]);b=len(rref(high,len(kk))[0])
  classes.append({'edge_connectivity':lam,'keys':kk,'admissible_core_count':len(kk)-1,'lower_rank':a,'total_rank':b,'new_rank':b-a})
  print('class',lam,'cores',len(kk)-1,'ranks',a,b,'new',b-a,flush=True)
 (P/'vol10_connectivity.json').write_text(json.dumps(classes,indent=2)+'\n')
 gg=[]
 for g in range(4,12):
  kk=[h for h in keys if h==(1,0) or gs[h]>=g]
  _,low=rows(c,9,kk);_,high=rows(c,10,kk);a=len(rref(low,len(kk))[0]);b=len(rref(high,len(kk))[0])
  # Check pure top-size formula separately; record any lower residual.
  lr,lp=rref(low,len(kk));residual_exps=[]
  for e in {e for h,p in c[10].items() if h[0]<10 for e in p}:
   row=[c[10].get(h,{}).get(e,0) if h[0]<10 else 0 for h in kk]
   for base,j in zip(lr,lp):
    z=row[j];row=[x-z*y for x,y in zip(row,base)]
   if any(row):residual_exps.append(e)
  gg.append({'girth_at_least':g,'lower_rank':a,'total_rank':b,'new_rank':b-a,'lower_support_cancels':not residual_exps,
              'top_edge_histogram':dict(Counter(m.bit_count() for k,m in kk if k==10))})
 (P/'vol10_girth.json').write_text(json.dumps(gg,indent=2)+'\n')
 direct=json.loads((P/'direct10.json').read_text());checked=0
 for i,h in enumerate(direct):
  n,E=vol10_build.parse_g6(h['g6']);counts=core_counts(n,E,10);Z=coefficients_from_counts(counts,c)
  for r in range(11):assert Z[r]=={int(e):Q(a) for e,a in h['coefficients'][str(r)].items()},(i,n,r)
  checked+=1
  if checked%20==0:print('direct hosts',checked,flush=True)
 # The exceptional small connected graphs up to order ten have distinct lower signatures.
 small={}
 for n in (4,6,8,10):
  sigs=[tuple(tuple(sorted(h['coefficients'][str(r)].items())) for r in range(10)) for h in direct if vol10_build.parse_g6(h['g6'])[0]==n]
  assert len(sigs)==len(set(sigs));small[n]=len(sigs)
 out={'direct_height_hosts':checked,'through_volume':10,'coefficients_checked':11*checked,'small_order_distinct_lower_signatures':small,'failures':0,'seconds':time.time()-start}
 (P/'vol10_host_checks.json').write_text(json.dumps(out,indent=2)+'\n');print('PASSED',out,flush=True)
if __name__=='__main__':main()
