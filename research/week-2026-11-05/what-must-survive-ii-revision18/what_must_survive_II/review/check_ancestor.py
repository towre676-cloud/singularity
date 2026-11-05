"""Independent exact checks of Theorems 44/45, including both centroid cases."""
from collections import Counter,defaultdict
from itertools import combinations
from pathlib import Path
import json,networkx as nx
ROOT=Path(__file__).resolve().parent

def is_cat(T):
    I=T.subgraph([v for v in T if T.degree(v)>1])
    return len(I)<2 or max(dict(I.degree()).values())<=2

def rooted(T,r,blocked=None):
    order=[r];parent={r:None};size={v:1 for v in T}
    for v in order:
        for w in T[v]:
            if w==parent[v] or (blocked is not None and {v,w}==set(blocked)):continue
            parent[w]=v;order.append(w)
    for v in order[:0:-1]:size[parent[v]]+=size[v]
    return order,parent,size

def invariants(T):
    n=len(T);centroids=nx.centroid(T);r=min(centroids);order,par,sz=rooted(T,r)
    edges=order[1:];anc={r:set()}
    for v in edges:anc[v]=anc[par[v]]|({par[v]} if par[v]!=r else set())
    A=Counter(min(sz[v],n-sz[v]) for v in edges);B=Counter();N=Counter()
    for u,v in combinations(edges,2):
        if u in anc[v]:a,b=u,v;B[sz[a]-sz[b]]+=1
        elif v in anc[u]:a,b=v,u;B[sz[a]-sz[b]]+=1
        else:B[n-sz[u]-sz[v]]+=1;continue
        if 2*sz[a]<n and sz[b]>=2:N[(sz[a],sz[b])]+=1
    # Direct-child groups, treating balanced endpoints as two virtual incoming edges.
    groups=defaultdict(list)
    if len(centroids)==2:
        blocked=tuple(centroids)
        for c in centroids:
            oo,pp,ss=rooted(T,c,blocked)
            for v in oo:
                if T.degree(v)<=1:continue
                child=sorted(ss[w] for w in T[v] if pp.get(w)==v and T.degree(w)>1)
                groups[ss[v]].append(child)
    else:
        for v in order:
            if T.degree(v)<=1:continue
            child=sorted(sz[w] for w in T[v] if par.get(w)==v and T.degree(w)>1)
            groups[sz[v]].append(child)
    # Theorem 44 using all edge-size pairs, including pairs not nested.
    pred=Counter(n-sz[u]-sz[v] for u,v in combinations(edges,2))
    def hterm(a,shift,c):pred[a+shift]+=c;pred[n-a+shift]-=c
    for v in edges:hterm(sz[v],-1,sz[v]-1)
    for (a,b),c in N.items():hterm(a,-b,c);hterm(a,-1,-c)
    assert all(pred[e]==B[e] for e in pred.keys()|B.keys())
    return tuple(sorted(A.items())),tuple(sorted(N.items())),B,dict(groups),len(centroids)==2

def check_pair(T,S,t,s):
    gt,gs=t[3],s[3];assert set(gt)==set(gs)
    total=0;events=[]
    for w,children in gt.items():
        other=gs[w];assert len(children)==len(other)
        flat=sorted(z for li in children for z in li);flat_s=sorted(z for li in other for z in li)
        assert flat==flat_s
        if len(children)==2 and len(flat)==2 and sorted(map(len,other))==[0,2]:
            assert sorted(map(len,children))==[1,1]
            val=2*(flat[0]-1)*(flat[1]-1);total+=val;events.append([w,*flat,val])
    actual=sum(d*d for _,d in S.degree())-sum(d*d for _,d in T.degree())
    assert actual==total
    assert is_cat(S) or actual>0
    return {'n':len(T),'balanced':t[4],'delta_degree_squares':actual,'gatherings':events}

def arm(G,parent,weight,kids,nextid):
    v=nextid[0];nextid[0]+=1;G.add_edge(parent,v)
    for w,children in kids:arm(G,v,w,children,nextid)
    for _ in range(weight-1-sum(w for w,_ in kids)):
        G.add_edge(v,nextid[0]);nextid[0]+=1

def example27():
    S=nx.Graph();T=nx.Graph()
    for G,F in [(S,[(13,[]),(13,[(6,[]),(6,[(2,[]),(3,[])])])]),(T,[(13,[(6,[(2,[])])]),(13,[(6,[(3,[])])])])]:
        nxt=[1]
        for w,k in F:arm(G,0,w,k,nxt)
    a,b=invariants(T),invariants(S);assert a[:2]==b[:2] and a[2]==b[2]
    result=check_pair(T,S,a,b);assert result['delta_degree_squares']==54
    result['edges']={'caterpillar':list(T.edges()),'impostor':list(S.edges())};return result

def main():
    checked=0;pairs=[];byorder={}
    for n in range(3,15):
        groups=defaultdict(list);count=0
        for T in nx.nonisomorphic_trees(n):
            inv=invariants(T);groups[inv[:2]].append((T,inv));checked+=1;count+=1
        for group in groups.values():
            cats=[v for v in group if is_cat(v[0])]
            if not cats:continue
            T,t=cats[0]
            for S,s in group:pairs.append(check_pair(T,S,t,s))
        byorder[n]=count;print('ancestor',n,count,flush=True)
    out={'all_trees_checked':checked,'orders':'3 through 14','counts_by_order':byorder,'cat_reference_comparisons':len(pairs),'noncat_comparisons':sum(p['delta_degree_squares']>0 for p in pairs),'balanced_comparisons':sum(p['balanced'] for p in pairs),'example27':example27()}
    (ROOT/'ancestor_checks.json').write_text(json.dumps(out,indent=2)+'\n');print(out['all_trees_checked'],'trees passed; 27-vertex difference=54.',flush=True)
if __name__=='__main__':main()
