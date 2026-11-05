"""Two-parameter extension, exact transfer in QQ[a,b]."""
from math import factorial
from pathlib import Path
from sympy.polys.rings import ring
from sympy import QQ,symbols,factor
from low_volume_symbolic import partitions
import json
R,a,b=ring('a,b',QQ);ROOT=Path(__file__).resolve().parent

def local(p,V):
    aa,bb,cc=p;pp=aa*a+bb*b+cc;out=[]
    for h in range(V+1):
      for part in partitions(V-h):
        coef=R.one
        for i in range(len(part)):coef*=pp-i
        for j in set(part):coef=coef.quo_ground(factorial(part.count(j)))
        if coef:out.append((h,aa*h*h,bb*h*h,cc*h*h+sum(j*j-2*j*h for j in part),coef))
    return out

def series(p,V):
    kernel=[[local(w,v) for v in range(V+1)] for w in p];dp={(0,-1,0,0,0):R.one}
    for i in range(len(p)):
      nxt={}
      for (v,last,x,y,z),c in dp.items():
       for t in range(V-v+1):
        for h,aa,bb,cc,coef in kernel[i][t]:
         key=(v+t,h,x+aa,y+bb,z+cc+(0 if last<0 else (last-h)**2));nxt[key]=nxt.get(key,R.zero)+c*coef
      dp={k:v for k,v in nxt.items() if v}
    out=[{} for _ in range(V+1)]
    for (v,last,x,y,z),c in dp.items():out[v][(x,y,z)]=out[v].get((x,y,z),R.zero)+c
    return out
if __name__=='__main__':
    P=[(1,0,0),(0,1,0),(1,0,-1),(1,1,0),(0,1,1)];Q=[P[0],P[3],P[1],P[2],P[4]]
    A=series(P,4);B=series(Q,4);out={};u,v,q=symbols('u v q')
    for k in range(1,5):
        d={e:A[k].get(e,R.zero)-B[k].get(e,R.zero) for e in A[k].keys()|B[k].keys()};d={e:c for e,c in d.items() if c}
        out[k]=[{'a':x,'b':y,'constant':z,'coefficient':str(c)} for (x,y,z),c in sorted(d.items())]
        poly=sum(c.as_expr()*u**x*v**y*q**z for (x,y,z),c in d.items());print('V',k,'terms',len(d),'factor',factor(poly),flush=True)
        if k==4:out['volume4_factor']=str(factor(poly))
    (ROOT/'two_parameter_volume.json').write_text(json.dumps(out,indent=2)+'\n')
