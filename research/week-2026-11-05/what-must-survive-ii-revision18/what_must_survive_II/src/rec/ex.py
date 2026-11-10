import itertools,subprocess,sys,json
from collections import Counter,defaultdict
from functools import lru_cache
# rooted trees as sorted tuples of children; forest = sorted tuple of trees
@lru_cache(None)
def forests(w,maxt=None):
    # forests of total weight w, trees nonincreasing in canonical order
    if w==0:return [()]
    out=[]
    for a in range(1,w+1):
        for t in trees(a):
            for f in forests(w-a):
                if not f or t>=f[0]:out.append((t,)+f)
    return out
@lru_cache(None)
def trees(a):
    return sorted(set(tuple(f) for f in forests(a-1)))
def size(t):return 1+sum(size(c) for c in t)
def gen(F):
    c=Counter()
    def rec(t):
        c[size(t)]+=1
        for k in t:rec(k)
    for t in F:rec(t)
    return tuple(sorted(c.items()))
def enc(FX,FY):
    # edge x-y balanced; vertices 0=x,1=y. output parents with parent<child
    par=[0,0]
    def add(t,p):
        par.append(p);v=len(par)-1
        for c in t:add(c,v)
    for t in FX:add(t,0)
    for t in FY:add(t,1)
    return f"{len(par)} "+" ".join(map(str,par))
def shells(lines,E):
    o=subprocess.run(['/root/wms/tree/shell',str(E)],input="\n".join(lines)+"\n",capture_output=True,text=True).stdout.strip().split('\n')
    return [l.split()[1:] for l in o]
res={}
EM=int(sys.argv[2])
for w in range(2,int(sys.argv[1])+1):
    g=defaultdict(list)
    for F in forests(w):g[gen(F)].append(F)
    pairs=[(a,b) for v in g.values() for a,b in itertools.combinations(v,2)]
    H=Counter();ex={}
    for a,b in pairs:
        T=enc(a+a,b+b);S=enc(a+b,a+b)
        s=shells([T,S],EM);first=next((i for i,(u,v) in enumerate(zip(*s)) if u!=v),None)
        H[first]+=1;ex.setdefault(first,(a,b))
    res[w]=dict(pairs=len(pairs),first=dict(H));print(w,len(pairs),dict(H),{k:str(v)[:90] for k,v in ex.items() if k and k>=4 or k is None},flush=True)
json.dump({str(k):{'pairs':v['pairs'],'first':{str(a):b for a,b in v['first'].items()}} for k,v in res.items()},open('ex.json','w'))
