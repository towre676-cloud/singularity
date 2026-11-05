import networkx as nx,itertools,json,warnings,sys
warnings.filterwarnings("ignore")
from collections import defaultdict,Counter
exec(open('r.py').read().split("if __name__")[0])
def AB2(T):
    n,c,o,par,s,anc=data(T);A=Counter();B=Counter();ed=o[1:];N=Counter()
    for v in ed:A[min(s[v],n-s[v])]+=1
    for e,f in itertools.combinations(ed,2):
        if e in anc[f]:B[s[e]-s[f]]+=1;N[(s[e],s[f])]+=(s[f]>1)
        elif f in anc[e]:B[s[f]-s[e]]+=1;N[(s[f],s[e])]+=(s[e]>1)
        else:B[n-s[e]-s[f]]+=1
    # drop balanced rows and zero entries
    N={k:v for k,v in N.items() if v and 2*k[0]!=n}
    return (key(A),key(B)),N
res={}
for n in range(8,int(sys.argv[1])+1):
    g=defaultdict(list)
    for T in nx.nonisomorphic_trees(n):
        k,N=AB2(T);g[k].append((is_cat(T),N,T))
    c=Counter();ex=None
    for v in g.values():
        if len(v)<2:continue
        for (a,Na,Ta),(b,Nb,Tb) in itertools.combinations(v,2):
            ty='cc' if a and b else 'mix' if a or b else 'nn'
            eq=Na==Nb;c[(ty,eq)]+=1
            if ty=='mix' and not eq and ex is None:ex=(sorted(Ta.edges()),sorted(Tb.edges()),Na,Nb)
    print(n,{str(k):z for k,z in c.items()},ex or '',flush=True);res[n]={str(k):z for k,z in c.items()}
json.dump(res,open('nn.json','w'))
