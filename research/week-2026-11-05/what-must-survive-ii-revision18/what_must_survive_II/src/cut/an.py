import networkx as nx,json,sys,itertools
from collections import defaultdict
gs=[]
for l in open('hosts.txt'):
    w=list(map(int,l.split()));gs.append((w[0],[(w[2+2*i],w[3+2*i]) for i in range(w[1])]))
T=[];cur=None
for l in open('t20.txt'):
    if l[0]=='G': cur={};T.append(cur);continue
    e,v,c=map(int,l.split());cur[(e,v)]=c
def tau(n,E):
    import sympy as sp
    G=nx.Graph(E);L=sp.Matrix(nx.laplacian_matrix(G,nodelist=sorted(G)).toarray().tolist());return int(L[:-1,:-1].det())
import numpy as np
inv=[]
for (n,E),t in zip(gs,T):
    th=defaultdict(int);gr=defaultdict(int)
    for (e,v),c in t.items(): th[e]+=c;gr[(e,v%n)]+=c
    inv.append((tuple(sorted(th.items())),tuple(sorted(gr.items())),tuple(sorted(t.items()))))
# Whitney-twist orbit classes
def twists(n,E):
    G=nx.Graph(E);out=[]
    for a,b in itertools.combinations(E,2):
        H=G.copy();H.remove_edges_from([a,b])
        if nx.is_connected(H): continue
        X=nx.node_connected_component(H,a[0])
        u,w=a if a[0] in X else a[::-1];c,d=b if b[0] in X else b[::-1]
        if u not in X or c not in X or w in X or d in X: continue
        if u==c or w==d or H.has_edge(u,d) or H.has_edge(c,w): continue
        H2=H.copy();H2.add_edge(u,d);H2.add_edge(c,w);out.append(H2)
    return out
par=list(range(len(gs)))
def fd(x):
    while par[x]!=x: par[x]=par[par[x]];x=par[x]
    return x
idx=defaultdict(list)
for i,(n,E) in enumerate(gs): idx[(n,nx.weisfeiler_lehman_graph_hash(nx.Graph(E),iterations=4))].append(i)
for i,(n,E) in enumerate(gs):
    for H in twists(n,E):
        for j in idx[(n,nx.weisfeiler_lehman_graph_hash(H,iterations=4))]:
            if nx.is_isomorphic(H,nx.Graph(gs[j][1])): par[fd(i)]=fd(j)
cls=lambda f:defaultdict(list)
res={}
for name,key in (("theta_x1",0),("graded_vol_mod_n",1),("full_e_vol",2)):
    g=defaultdict(list)
    for i,(n,E) in enumerate(gs): g[(n,inv[i][key])].append(i)
    coll=[v for v in g.values() if len(v)>1]
    within=sum(1 for v in coll if len({fd(i) for i in v})==1);res[name]={"collision_classes":len(coll),"graphs_involved":sum(map(len,coll)),"all_inside_one_twist_orbit":within,"examples":[v for v in coll][:6]}
tw=defaultdict(list)
for i in range(len(gs)): tw[fd(i)].append(i)
res["twist_orbits_nontrivial"]=sum(1 for v in tw.values() if len(v)>1)
bad=[v for v in tw.values() if len(v)>1 and len({inv[i][0] for i in v})>1];res["twist_orbits_with_unequal_theta"]=len(bad)
print(json.dumps(res,indent=0)[:1500])
up=open('/root/wms/out/unsep.txt').read().strip().split('\n')
def m(l):
    w=list(map(int,l.split()));return nx.Graph([(w[2+2*i],w[3+2*i]) for i in range(w[1])])
A,B=m(up[0]),m(up[1]);print("late pair: edge conn",nx.edge_connectivity(A),nx.edge_connectivity(B),"girth-ish triangles",sum(nx.triangles(A).values())/3,sum(nx.triangles(B).values())/3)
ia=[i for i,(n,E) in enumerate(gs) if n==14 and nx.is_isomorphic(nx.Graph(E),A)][0];ib=[i for i,(n,E) in enumerate(gs) if n==14 and nx.is_isomorphic(nx.Graph(E),B)][0]
print("late pair same twist orbit",fd(ia)==fd(ib),"theta equal",inv[ia][0]==inv[ib][0],"graded equal",inv[ia][1]==inv[ib][1],"full equal",inv[ia][2]==inv[ib][2]);print("tau",tau(14,gs[ia][1]),tau(14,gs[ib][1]))
json.dump(res,open('an.json','w'),indent=1)
