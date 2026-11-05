import networkx as nx,itertools,warnings,json
warnings.filterwarnings("ignore")
from collections import Counter
exec(open('r.py').read().split("if __name__")[0])
ok=True;cnt=0
for n in range(3,15):
    for T in nx.nonisomorphic_trees(n):
        n_,c,o,par,s,anc=data(T);ed=o[1:];B=Counter();R=Counter()
        for e,f in itertools.combinations(ed,2):
            B[s[e]-s[f] if e in anc[f] else s[f]-s[e] if f in anc[e] else n-s[e]-s[f]]+=1
            R[n-s[e]-s[f]]+=1
        def addh(a,shift,m):
            R[a+shift]+=m;R[n-a+shift]-=m
        for e in ed:addh(s[e],-1,s[e]-1)
        for f in ed:
            if s[f]<2:continue
            for e in anc[f]:
                addh(s[e],-s[f],1);addh(s[e],-1,-1)
        ok&={k:v for k,v in B.items() if v}=={k:v for k,v in R.items() if v};cnt+=1
print(cnt,ok);json.dump(dict(trees=cnt,ok=bool(ok)),open('bf.json','w'))
