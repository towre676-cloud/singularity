"""Exact reconstruction on caterpillars with <=4 canonical spine vertices."""
from collections import Counter
from itertools import product
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent

def weights(n,m):
    if m==1:
        yield (n,);return
    def rec(left,w):
        i=len(w);lo=2 if i in (0,m-1) else 1
        if i==m-1:
            if left>=lo:yield w+(left,)
            return
        minrest=(m-i-2)+2
        for a in range(lo,left-minrest+1):yield from rec(left-a,w+(a,))
    yield from rec(n,())

def moments(n,cut):
    m=len(cut)+1;ell=n-m;out=[]
    for r in (2,3):
        v=sum((b-a)**r for i,a in enumerate(cut) for b in cut[i+1:])
        for i,a in enumerate(cut,1):v+=(a-i)*(a-1)**r+(ell-a+i)*(n-a-1)**r
        v+=ell*(ell-1)//2*(n-2)**r;out.append(v)
    return tuple(out)

def candidates(n,radii):
    k=len(radii);out=set()
    for sign in product((0,1),repeat=k):
        a=sorted(r if not sg else n-r for r,sg in zip(radii,sign))
        if len(set(a))!=k or (a and (a[0]<2 or a[-1]>n-2)):continue
        w=tuple(y-x for x,y in zip([0]+a,a+[n]));out.add(min(w,w[::-1]))
    return out

def main():
    total=0;counts={}
    for n in range(4,41):
        count=0
        for m in range(2,min(4,n-2)+1):
            seen=set()
            for w in weights(n,m):
                w=min(w,w[::-1])
                if w in seen:continue
                seen.add(w);cuts=[];u=0
                for v in w[:-1]:u+=v;cuts.append(u)
                radii=sorted(min(a,n-a) for a in cuts);target=moments(n,cuts)
                poss=[]
                for v in candidates(n,radii):
                    a=[];u=0
                    for t in v[:-1]:u+=t;a.append(u)
                    if moments(n,a)==target:poss.append(v)
                assert poss==[w] or (len(poss)==1 and poss[0]==w),(n,w,poss)
                count+=1
        counts[n]=count;total+=count
    result={'orders':'4 through 40','canonical_spine_sizes':'2,3,4; stars handled directly in proof','exact_reconstruction_checks':total,'counts_by_order':counts}
    (ROOT/'short_spine_checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Recovered',total,'short-spine caterpillars exactly.')
if __name__=='__main__':main()
