import sys
from functools import lru_cache
sys.setrecursionlimit(100000)
R=int(sys.argv[1])
trees={1:[()]}  # weight -> list of sorted tuples of child ids
ids={};lst=[];W=[]
def add(k,w):
    if k not in ids:
        ids[k]=len(lst);lst.append(k);W.append(w)
add((),1);byw={1:[0]}
def multisets(w,maxid):
    # multisets of tree ids total weight w, ids nonincreasing <=maxid
    if w==0:yield ();return
    for i in range(maxid,-1,-1):
        if W[i]<=w:
            for r in multisets(w-W[i],i):yield (i,)+r
for w in range(2,R+1):
    n0=len(lst)
    for k in multisets(w-1,n0-1):add(k,w)
print(len(lst))
for k,w in zip(lst,W):print(w,len(k),*k)
