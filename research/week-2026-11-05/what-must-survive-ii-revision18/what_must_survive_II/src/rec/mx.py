import networkx as nx,itertools,json,warnings,sys
warnings.filterwarnings("ignore")
from collections import defaultdict,Counter
exec(open('r.py').read().split("if __name__")[0])
def AB2(T):
    n,c,o,par,s,anc=data(T);A=Counter();B=Counter();ed=o[1:]
    for v in ed:A[min(s[v],n-s[v])]+=1
    for e,f in itertools.combinations(ed,2):
        B[s[e]-s[f] if e in anc[f] else s[f]-s[e] if f in anc[e] else n-s[e]-s[f]]+=1
    return key(A),key(B)
def exch(T,S):
    "single exchange with equal weights and symmetric middle"
    Sd=sorted(d for _,d in S.degree())
    for u,v in itertools.combinations([w for w in T if T.degree(w)>1],2):
        P=nx.shortest_path(T,u,v);du=[w for w in T[u] if w!=P[1]];dv=[w for w in T[v] if w!=P[-2]]
        def cs(root,c):
            H=T.copy();H.remove_edge(root,c);return len(nx.node_connected_component(H,c))
        wu={c:cs(u,c) for c in du};wv={c:cs(v,c) for c in dv}
        # pendants are interchangeable: group by (weight); enumerate multisets via distinct arms up to leaves
        lu=[c for c in du if wu[c]==1];lv=[c for c in dv if wv[c]==1];nu=[c for c in du if wu[c]>1];nv=[c for c in dv if wv[c]>1]
        for a in range(len(lu)+1):
            for b in range(len(lv)+1):
                for r in range(len(nu)+1):
                    for Cu in itertools.combinations(nu,r):
                        for r2 in range(len(nv)+1):
                            for Cv in itertools.combinations(nv,r2):
                                c1=list(lu[:a])+list(Cu);c2=list(lv[:b])+list(Cv)
                                if not c1 and not c2:continue
                                if sum(wu[c] for c in c1)!=sum(wv[c] for c in c2):continue
                                G=T.copy()
                                for c in c1:G.remove_edge(u,c);G.add_edge(v,c)
                                for c in c2:G.remove_edge(v,c);G.add_edge(u,c)
                                if nx.faster_could_be_isomorphic(G,S) and nx.is_isomorphic(G,S):
                                    Ru=[c for c in du if c not in c1];Rv=[c for c in dv if c not in c2]
                                    if sum(wu[c] for c in Ru)!=sum(wv[c] for c in Rv):continue
                                    Mid=T.copy()
                                    for root,arms in ((u,du),(v,dv)):
                                        for c in arms:
                                            H=T.copy();H.remove_edge(root,c);Mid.remove_nodes_from(nx.node_connected_component(H,c))
                                    M1=Mid.copy();nx.set_node_attributes(M1,{w:(1 if w==u else 2 if w==v else 0) for w in M1},'m')
                                    M2=Mid.copy();nx.set_node_attributes(M2,{w:(2 if w==u else 1 if w==v else 0) for w in M2},'m')
                                    if nx.is_isomorphic(M1,M2,node_match=lambda a,b:a['m']==b['m']):return True
    return False
res={}
for n in range(10,int(sys.argv[1])+1):
    g=defaultdict(list)
    for T in nx.nonisomorphic_trees(n):g[AB2(T)].append(T)
    c=Counter();ex=None
    for v in g.values():
        cats=[T for T in v if is_cat(T)];non=[T for T in v if not is_cat(T)]
        if cats and non:
            for S in non:
                ok=any(exch(T,S) for T in cats)
                c['one exchange' if ok else 'not one']+=1;I=S.subgraph([w for w in S if S.degree(w)>1]);c[('branch',sum(1 for _,d in I.degree() if d>=3),max(d for _,d in I.degree()))]+=1
                if not ok and ex is None:ex=(sorted(cats[0].edges()),sorted(S.edges()))
    print(n,dict(c),ex if ex else '',flush=True);res[n]={str(a):b for a,b in c.items()}
json.dump(res,open('mx.json','w'))
