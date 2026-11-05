"""All-parameter exact identity: four weighted path contractions against four."""
from collections import Counter
from itertools import product
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
# Weights are a*m+b, m>=0.
TERMS=[(1,(1,1,(1,4),4)),(-1,(1,1,(1,5),3)),(-1,(1,2,(1,2),5)),(1,(1,2,(1,5),2)),(1,(1,3,(1,1),5)),(-1,(1,3,(1,4),2)),(-1,(1,4,(1,1),4)),(1,(1,4,(1,2),3))]
def aff(w):return (0,w) if isinstance(w,int) else w
def add(a,b):return (a[0]+b[0],a[1]+b[1])
def canon3(w):return min(tuple(w),tuple(reversed(w)))
def boundary_path(w):
    a,b,c,d=map(aff,w)
    return Counter([canon3((add(a,b),c,d)),canon3((a,add(b,c),d)),canon3((a,b,add(c,d)))])
def shell_path(w):
    w=list(map(aff,w));out=Counter()
    for z in product((-1,1),repeat=3):
        h=[0]
        for v in z:h.append(h[-1]+v)
        lo=min(h)
        out[(sum(a*(h0-lo) for (a,b),h0 in zip(w,h)),sum(b*(h0-lo) for (a,b),h0 in zip(w,h)))]+=1
    return out
if __name__=='__main__':
    bs=Counter();ss=Counter()
    for c,w in TERMS:
        for k,v in boundary_path(w).items():bs[k]+=c*v
        for k,v in shell_path(w).items():ss[k]+=c*v
    bs={str(k):v for k,v in bs.items() if v};ss={str(k):v for k,v in ss.items() if v}
    assert not bs and not ss
    out={'parameter':'m >= 0, total weight n=m+10','terms':[{'coefficient':c,'path_weights':w} for c,w in TERMS],'boundary_residual':bs,'unit_shell3_residual':ss,'positive_mass':4,'negative_mass':4}
    (ROOT/'all_parameter_relation.json').write_text(json.dumps(out,indent=2)+'\n')
    print('All-parameter identity passed: shell residual = 0, contraction-boundary residual = 0.')
