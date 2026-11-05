# For caterpillars in shell-2 collision classes: can any impostor exist (gather feasible)? slack = xi+eta+1-w at doubled sizes with no single above.
from collections import Counter
import sys
def sizes(p):
    n=len(p)+sum(p);t=0;a=[]
    for i in range(len(p)-1):t+=1+p[i];a.append(t)
    return n,a
def slack(p):
    n,a=sizes(p);left=[x for x in a if 2*x<n];right=[n-x for x in a if 2*x>n];bal=[x for x in a if 2*x==n]
    # chains from root downward (largest first)
    L=sorted(left,reverse=True);R=sorted(right,reverse=True);best=None
    if bal:
        w=n/2;x=L[0] if L else 0;y=R[0] if R else 0
        if x and y:best=x+y+1-w
    i=j=0
    while i<len(L) and j<len(R) and L[i]==R[j]:
        w=L[i];x=L[i+1] if i+1<len(L) else 0;y=R[j+1] if j+1<len(R) else 0
        if x and y:
            s=x+y+1-w;best=s if best is None else min(best,s)
        i+=1;j+=1
    return best
res={}
for n in range(8,31):
    H=Counter();tot=0;mn=None;ex=None
    for l in open(f'/root/wms/spine/d{n}.txt'):
        if not l.startswith('S2'):continue
        for x in l.split()[1:]:
            p=tuple(map(int,x.strip(',').split(',')));tot+=1;s=slack(p)
            if s is not None and (mn is None or s<mn):mn=s;ex=p
    if tot:print(n,'cats in classes',tot,'min slack',mn,ex,flush=True)
