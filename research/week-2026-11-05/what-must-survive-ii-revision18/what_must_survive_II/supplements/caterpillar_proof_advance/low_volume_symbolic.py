"""All-parameter exact x-volume expansion via a five-site spine transfer."""
from collections import defaultdict
from math import factorial
from pathlib import Path
import json
from sympy.polys.rings import ring
from sympy import QQ
R,z=ring('s',QQ)
ROOT=Path(__file__).resolve().parent

def partitions(k,j=1):
    if k==0:yield ()
    for a in range(j,k+1):
        for p in partitions(k-a,a):yield (a,)+p

def local(p,volume):
    a,b=p;pp=a*z+b;out=[]
    for h in range(volume+1):
      for part in partitions(volume-h):
        ell=len(part);coeff=R.one
        for i in range(ell):coeff*=pp-i
        for j in set(part):coeff=coeff.quo_ground(factorial(part.count(j)))
        alpha=a*h*h;beta=b*h*h+sum(j*j-2*j*h for j in part)
        if coeff:out.append((h,alpha,beta,coeff))
    return out

def series(p,V):
    kernel=[[local(w,v) for v in range(V+1)] for w in p]
    # key (used volume,last spine height,energy slope,energy constant)
    dp={(0,-1,0,0):R.one}
    for i in range(len(p)):
      nxt={}
      for (v,last,aa,bb),c in dp.items():
       for t in range(V-v+1):
        for h,a,b,coef in kernel[i][t]:
            key=(v+t,h,aa+a,bb+b+(0 if last<0 else (last-h)**2))
            nxt[key]=nxt.get(key,R.zero)+c*coef
      dp={k:v for k,v in nxt.items() if v}
    out=[{} for _ in range(V+1)]
    for (v,last,a,b),c in dp.items():out[v][(a,b)]=out[v].get((a,b),R.zero)+c
    return out

if __name__=='__main__':
    P=[(1,0),(1,1),(1,-1),(2,1),(1,2)];Q=[(1,0),(2,1),(1,1),(1,-1),(1,2)]
    A=series(P,4);B=series(Q,4);out={}
    for V in range(1,5):
        d={k:A[V].get(k,R.zero)-B[V].get(k,R.zero) for k in A[V].keys()|B[V].keys()};d={k:v for k,v in d.items() if v}
        out[V]=[{'energy_s':a,'energy_constant':b,'coefficient':str(c)} for (a,b),c in sorted(d.items())]
        print('volume',V,'difference terms',len(d),out[V],flush=True)
    (ROOT/'low_volume_symbolic.json').write_text(json.dumps(out,indent=2)+'\n')
