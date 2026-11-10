import networkx as nx,json,subprocess,itertools,random
from collections import Counter,defaultdict
res={}
# first separating volume, all connected graphs through 7 vertices
def sig(G,VM):
    n=len(G);nodes=sorted(G);ix={v:i for i,v in enumerate(nodes)};E=[(ix[a],ix[b]) for a,b in G.edges()];adj=[[] for _ in range(n)]
    for a,b in E: adj[max(a,b)].append(min(a,b))
    out=[];h=[0]*n
    for V in range(1,VM+1):
        c=Counter()
        def rec(i,left,e):
            if i==n-1:
                h[i]=left;c[e+sum((left-h[w])**2 for w in adj[i])]+=1;return
            for a in range(left+1):
                h[i]=a;rec(i+1,left-a,e+sum((a-h[w])**2 for w in adj[i]))
        rec(0,V,0);out.append(tuple(sorted(c.items())))
    return out
tot=Counter();maxv={}
for n in range(2,8):
    Gs=[G for G in nx.graph_atlas_g() if len(G)==n and nx.is_connected(G)];sg=[sig(G,6) for G in Gs];un=0;fs=Counter()
    for i,j in itertools.combinations(range(len(Gs)),2):
        V=next((k+1 for k in range(6) if sg[i][k]!=sg[j][k]),None);fs[V]+=1
    res[f"atlas_n{n}"]={"graphs":len(Gs),"first_separation":{str(k):v for k,v in sorted(fs.items(),key=lambda z:(z[0] or 99))}};print(n,res[f"atlas_n{n}"],flush=True)
# twist pair
def side(seed,k):
    rnd=random.Random(seed)
    while True:
        # k vertices, ports a,c have degree 2, others 3
        deg=[2,2]+[3]*(k-2);st=[v for v,d in enumerate(deg) for _ in range(d)];rnd.shuffle(st);E=set();ok=True
        for i in range(0,len(st),2):
            a,b=st[i],st[i+1]
            if a==b or (min(a,b),max(a,b)) in E: ok=False;break
            E.add((min(a,b),max(a,b)))
        if not ok: continue
        G=nx.Graph(list(E))
        if not nx.is_connected(G) or len(G)!=k: continue
        # no automorphism swapping ports
        H=G.copy();nx.set_node_attributes(H,{v:(0 if v==0 else 1 if v==1 else 2) for v in H},'c')
        H2=G.copy();nx.set_node_attributes(H2,{v:(1 if v==0 else 0 if v==1 else 2) for v in H2},'c')
        if not nx.is_isomorphic(H,H2,node_match=lambda a,b:a['c']==b['c']): return G
for s1 in range(1,400):
    X=side(s1,8);Y=side(s1+1000,8);G=nx.disjoint_union(X,Y);T=nx.disjoint_union(X,Y);G.add_edges_from([(0,8),(1,9)]);T.add_edges_from([(0,9),(1,8)])
    if not nx.is_isomorphic(G,T): break
a,b=sig(G,7),sig(T,7);res["twist16_first_volume"]=next((k+1 for k in range(7) if a[k]!=b[k]),None);print("twist first vol",res["twist16_first_volume"])
json.dump(res,open('marks.json','w'),indent=1)
