"""Exact reconstruction of spider arm lengths from energy shell one."""
from collections import Counter
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent

def partitions(n,lo=1):
    if n==0:yield ()
    for a in range(lo,n+1):
        for p in partitions(n-a,a):yield (a,)+p

def shell1(arms):
    n=1+sum(arms);c=Counter()
    for a in arms:
        for k in range(1,a+1):c[k]+=1;c[n-k]+=1
    return c

def recover(n,c):
    h=n//2;f={k:c[k] for k in range(1,h+1)}
    if n%2==0:
        assert f[h]%2==0;f[h]//=2
    jumps=[k for k in range(2,h+1) if f[k]>f[k-1]]
    out=[]
    if not jumps:
        f[h+1]=0
        for k in range(1,h+1):out += [k]*(f[k]-f[k+1])
    else:
        assert len(jumps)==1
        s=jumps[0];out=[n-s]
        b={k:c[k]-1 for k in range(1,s)};assert b[s-1]==0
        for k in range(1,s-1):out += [k]*(b[k]-b[k+1])
    return tuple(sorted(out))

if __name__=='__main__':
    counts={};examples=[]
    for n in range(4,26):
        count=0
        for arms in partitions(n-1):
            if len(arms)<3:continue
            assert recover(n,shell1(arms))==arms
            count+=1
        counts[n]=count
    for arms in ((1,1,7),(1,3,5),(2,3,4)):
        n=1+sum(arms);examples.append({'n':n,'arms':arms,'shell1':dict(shell1(arms)),'recovered':recover(n,shell1(arms))})
    result={'all_spiders_checked_orders':'4 through 25','counts_by_order':counts,'total':sum(counts.values()),'exact_integer_checks':True,'examples':examples}
    (ROOT/'spider_reconstruction_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Exactly recovered',sum(counts.values()),'spiders on 4 through 25 vertices.')
