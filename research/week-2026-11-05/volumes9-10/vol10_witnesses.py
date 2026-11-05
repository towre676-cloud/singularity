"""Exact seed isolators and rational-linear necessity witnesses at volume ten."""
from pathlib import Path
from collections import Counter
from fractions import Fraction as Q
from math import lcm
import json,time
import sympy as S
import vol10_build
from vol9_build import lib,rows
from vol9_verify_hosts import core_counts
from vol8_law import rref
P=Path(__file__).resolve().parent

def main():
 start=time.time();law=json.loads((P/'vol10_law.json').read_text())
 c={int(r):{(x['k'],x['mask']):{int(e):Q(a) for e,a in x['polynomial'].items()} for x in rs}
    for r,rs in law['coefficient_rows'].items()}
 classes=json.loads((P/'vol10_connectivity.json').read_text())
 allcores=sorted([tuple(h) for h in law['core_keys'] if h[0]>1],key=lambda h:(h[0],h[1].bit_count(),h[1]))
 seedrows={}
 for h in allcores:
  k,m=h;seedrows[h]={j:a for j,a in core_counts(k,lib.edges_of(m,k),k).items() if j[0]>1}
  assert seedrows[h][h]==1
  assert all(j==h or allcores.index(j)<allcores.index(h) for j in seedrows[h])
 print('all seed rows computed',round(time.time()-start,2),flush=True)
 results=[]
 for cls in classes:
  lam=cls['edge_connectivity'];keys=[tuple(h) for h in cls['keys']];C=[h for h in allcores if h in keys]
  iso={}
  for h in C:
   rel=Counter({h:1})
   for j,a in seedrows[h].items():
    if j==h:continue
    assert j in C
    for g,b in iso[j].items():rel[g]-=a*b
   iso[h]={g:a for g,a in rel.items() if a}
   assert all(sum(a*seedrows[g].get(j,0) for g,a in iso[h].items())==int(j==h) for j in C)
  _,low=rows(c,9,keys);lr,lp=rref(low,len(keys));d=len(lr)
  selected=[];matrix=[list(r) for r in lr];rank=d
  for e in sorted({e for p in c[10].values() for e in p}):
   row=[c[10].get(h,{}).get(e,0) for h in keys]
   nr=len(rref(matrix+[row],len(keys))[0])
   if nr>rank:matrix.append(row);selected.append(e);rank=nr
  assert rank==cls['total_rank'] and len(selected)==cls['new_rank']
  M=S.Matrix(matrix);piv=M.rref()[1];J=M[:,list(piv)];inverse=J.inv()
  witnesses=[]
  for ii,e in enumerate(selected):
   rhs=S.zeros(rank,1);rhs[d+ii]=1;v=inverse*rhs
   scale=lcm(*(int(a.q) for a in v));vec={keys[piv[j]]:int(a*scale) for j,a in enumerate(v) if a}
   assert vec.get((1,0),0)==0
   for r in range(1,10):
    assert not any(sum(a*c[r].get(h,{}).get(exp,0) for h,a in vec.items())
                   for exp in {exp for p in c[r].values() for exp in p})
   delta={exp:sum(a*c[10].get(h,{}).get(exp,0) for h,a in vec.items())
          for exp in {exp for p in c[10].values() for exp in p}}
   delta={exp:a for exp,a in delta.items() if a}
   assert all(delta.get(exp,0)==(scale if j==ii else 0) for j,exp in enumerate(selected))
   seeds=Counter()
   for h,a in vec.items():
    for g,b in iso[h].items():seeds[g]+=a*b
   seeds={g:a for g,a in seeds.items() if a}
   assert all(sum(a*seedrows[g].get(h,0) for g,a in seeds.items())==vec.get(h,0) for h in C)
   if lam:
    sides=[]
    for sign in (1,-1):
     ss={h:abs(a) for h,a in seeds.items() if a*sign>0}
     K=sum(k*a for(k,m),a in ss.items());D=sum((3*k-2*m.bit_count())*a for(k,m),a in ss.items())
     sides.append({'seed_vertices':K,'attachment_sites':D,'base':K+D,'singleton_fillers':0,'edge_fillers':0,
                   'seeds':[[k,m,a] for(k,m),a in sorted(ss.items())]})
    diff=sides[0]['base']-sides[1]['base'];assert diff%2==0
    small=1 if diff>0 else 0;big=1-small;n=abs(diff)
    if n==2:
     sides[small]['edge_fillers']+=1;sides[small]['base']+=6;sides[small]['seed_vertices']+=2;sides[small]['attachment_sites']+=4
     sides[big]['singleton_fillers']+=1;sides[big]['base']+=4;sides[big]['seed_vertices']+=1;sides[big]['attachment_sites']+=3
    elif n:
     b=int(n%4==2);a=(n-6*b)//4
     sides[small]['singleton_fillers']+=a;sides[small]['edge_fillers']+=b
     sides[small]['base']+=4*a+6*b;sides[small]['seed_vertices']+=a+2*b;sides[small]['attachment_sites']+=3*a+4*b
    assert sides[0]['base']==sides[1]['base']
    t=max(6,*(s['attachment_sites'] for s in sides));t+=t%2
    N=sides[0]['base']+125*t
    recipe={'construction':'125-vertex-block prism reservoir','blocks':t,'common_order':N,'sides':sides}
   else:
    # Completion order of a seed is 382k-254e. Filler components
    # C(K1), C(K2), Q have orders 382,510,126 and no small cores.
    ndiff=sum(a*(382*k-254*m.bit_count()) for(k,m),a in seeds.items());assert ndiff%2==0
    h=ndiff//2
    signed=[[k,m,a] for(k,m),a in sorted(seeds.items())]
    recipe={'construction':'disjoint girth12 cap completions',
            'signed_seed_completions':signed,'filler_C_K1':h,'filler_C_K2':-h,'filler_Q':h}
    assert ndiff+h*382-h*510+h*126==0
    N=sum(max(a,0)*(382*k-254*m.bit_count()) for k,m,a in signed)+max(h,0)*(382+126)+max(-h,0)*510
    recipe['common_order']=N
   witnesses.append({'isolated_degree':e,'scale':scale,'core_difference':[[k,m,a] for(k,m),a in sorted(vec.items())],
                     'delta10':{str(exp):str(a) for exp,a in sorted(delta.items())},'recipe':recipe})
  results.append({'edge_connectivity':lam,'seed_isolators':len(iso),'lower_rank':d,'new_dimension':len(selected),
                   'coefficient_panel':selected,'witnesses':witnesses})
  print('class',lam,'isolators',len(iso),'witnesses',len(witnesses),'orders',[w['recipe']['common_order'] for w in witnesses],flush=True)
 out={'classes':results,'seed_count_rows':[{'core':list(h),'counts':[[k,m,a] for(k,m),a in sorted(row.items())]} for h,row in seedrows.items()],
      'construction_girth_cutoff':11,'seconds':time.time()-start,'verification':'Exact seed arithmetic; large recipes not brute-force allocated'}
 (P/'vol10_witnesses.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
