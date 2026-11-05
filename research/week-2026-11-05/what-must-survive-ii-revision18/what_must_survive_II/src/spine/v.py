import itertools,json,sympy as sp,networkx as nx,warnings
warnings.filterwarnings("ignore")
from collections import Counter
from functools import reduce
res={}
def cat(p):
    G=nx.path_graph(len(p));k=len(p)
    for i,c in enumerate(p):
        for _ in range(c):G.add_edge(i,k);k+=1
    return G
exec(open('chk.py').read().split("key=lambda")[0].split('warnings.filterwarnings("ignore")')[1].split('res={}')[0].replace('from collections import Counter,defaultdict',''))
key=lambda c:tuple(sorted(c.items()))
def S(T,E_max=3):
    # exact shells via signs on edge subsets
    n=len(T);ed=list(nx.bfs_edges(T,0));order=[0]+[w for u,w in ed];par={w:u for u,w in ed};out={}
    for e in range(1,E_max+1):
        c=Counter()
        for F in itertools.combinations(order[1:],e):
            for sg in itertools.product((-1,1),repeat=e):
                z=dict(zip(F,sg));h={0:0}
                for v in order[1:]:h[v]=h[par[v]]+z.get(v,0)
                vals=list(h.values());c[sum(vals)-n*min(vals)]+=1
        out[e]=c
    return out
def vol(T,Vm=4):
    # M coefficient in x^V, q^E: heights >=0, sum=V (min 0 automatic)
    vs=list(T);out={}
    def edges_energy(h):
        seen=0
        for v,a in h.items():
            for w in T[v]:
                b=h.get(w,0)
                if w in h:
                    if v<w: seen+=(a-b)**2
                else: seen+=a*a
        return seen
    for V in range(1,Vm+1):
        c=Counter()
        for part in [p for p in sp.utilities.iterables.partitions(V)]:
            parts=[k for k,m in part.items() for _ in range(m)]
            for S_ in itertools.permutations(vs,len(parts)) if False else []: pass
        # multisets
        for ms in itertools.combinations_with_replacement(vs,V):
            h=Counter(ms);c[edges_energy(h)]+=1
        out[V]=c
    return out
# seven-vertex imbalance counterexample
ce=None
g={}
for T in nx.nonisomorphic_trees(7):
    A,B,N=AB(T);k=key(A)
    for U,bu,nu in g.get(k,[]):
        if nu!=N and not ce: ce=dict(T1=sorted(T.edges()),T2=sorted(U.edges()),A=dict(A),B1=dict(B),B2=dict(bu),N1=dict(N),N2=dict(nu))
    g.setdefault(k,[]).append((T,B,N))
res['imbalance_7']=ce;print('7v',ce)
# linked marginals
okl=True
for n in range(3,14):
    g={}
    for T in nx.nonisomorphic_trees(n):
        A,B,N=AB(T);k=key(A);m=Counter(B)
        J=Counter()
        for b,c in B.items():J[abs(n-b)]+=0
        sig=Counter()
        for b,c in B.items():sig[n-b]+=c
        for d,c in N.items():sig[d]+=c
        if k in g:okl&=g[k]==sig
        g[k]=sig
res['sum_of_marginals_fixed_by_A']=okl;print('linked',okl)
# balanced theorem check
ok=True;sep=True;s3=[];cnt=0
for h in range(5,13):
    n=2*h
    for u in range(1,h):
        for v in range(u,h):
            c=h-3-u-v
            if c<0:continue
            C=cat([u,h-2-u,h-2-v,v])
            St=nx.Graph();St.add_edges_from([('z',1),('z',2),('z',3)]);k=10
            for hub,num in (('z',c),(1,u),(2,v),(3,h-1)):
                for _ in range(num):St.add_edge(hub,k);k+=1
            St=nx.convert_node_labels_to_integers(St)
            assert len(C)==n and len(St)==n and nx.is_tree(St)
            a1,b1,_=AB(C);a2,b2,_=AB(St);ok&=(a1==a2 and b1==b2);cnt+=1
            sep&=sorted(dict(C.degree()).values())!=sorted(dict(St.degree()).values())
            if n<=14:
                s1,s2=S(C)[3],S(St)[3];s3.append(s1!=s2)
print('balanced',cnt,ok,'deg-sep',sep,'s3 sep',all(s3),len(s3));res['balanced']=dict(count=cnt,AB_equal=ok,degree_separates=sep,s3=all(s3),s3_cases=len(s3))
# two-parameter family: volumes
rows=[]
for a in range(1,6):
    for b in range(0,6):
        P=[a,b,a-1,a+b,b+1];Q=[a,a+b,b,a-1,b+1]
        G,H=cat(P),cat(Q);iso=nx.is_isomorphic(G,H);A1,B1,_=AB(G);A2,B2,_=AB(H)
        vg,vh=vol(G),vol(H)
        rows.append(dict(a=a,b=b,iso=iso,pred=a==b+1,AB=A1==A2 and B1==B2,eq3=all(vg[i]==vh[i] for i in (1,2,3)),eq4=vg[4]==vh[4],d4={k:vg[4][k]-vh[4][k] for k in set(vg[4])|set(vh[4]) if vg[4][k]!=vh[4][k]}))
print('two-param all AB',all(r['AB'] for r in rows),'iso pred',all(r['iso']==r['pred'] for r in rows),'eq<=3',all(r['eq3'] for r in rows),'eq4 iff iso',all(r['eq4']==r['iso'] for r in rows))
res['two_param']=rows
print(rows[1])
json.dump(res,open('v.json','w'),default=str,indent=0)
