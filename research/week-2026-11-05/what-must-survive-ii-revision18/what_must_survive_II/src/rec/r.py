import networkx as nx,itertools,warnings,sys
warnings.filterwarnings("ignore")
from collections import Counter,defaultdict
def data(T):
    n=len(T);# root at a centroid
    def sizes(r):
        E=list(nx.bfs_edges(T,r));o=[r]+[w for u,w in E];par={w:u for u,w in E};s={v:1 for v in T}
        for v in reversed(o[1:]):s[par[v]]+=s[v]
        return o,par,s
    o,par,s=sizes(0);c=min(T,key=lambda v:max([s[w] for w in T[v] if par.get(w)==v]+[n-s[v]]))
    o,par,s=sizes(c);anc={c:[]}
    for v in o[1:]:anc[v]=anc[par[v]]+[par[v]] if par[v]!=c else []
    return n,c,o,par,s,anc
def ABH(T):
    n,c,o,par,s,anc=data(T);ed=o[1:];A=Counter();B=Counter();H=Counter()
    for v in ed:A[s[v]]+=1;A[n-s[v]]+=1
    isanc=lambda u,v:u in anc[v]
    for e,f in itertools.combinations(ed,2):
        if isanc(e,f):B[s[e]-s[f]]+=1
        elif isanc(f,e):B[s[f]-s[e]]+=1
        else:B[n-s[e]-s[f]]+=1
    for tri in itertools.combinations(ed,3):
        chain=sorted(tri,key=lambda v:-s[v]);a,b,g=chain
        ab=isanc(a,b);ag=isanc(a,g);bg=isanc(b,g)
        rel=[(a,b,ab),(a,g,ag),(b,g,bg)]
        cnt=sum(1 for u,v in itertools.permutations(tri,2) if isanc(u,v))
        def path(p,q,r_,t):
            for e_ in (p+r_,q+t,p+2*q+r_,q+2*r_+t):H[e_]+=1
        def star(w,p,q,r_):
            for e_ in (w,w+n,w+2*p,w+2*q,w+2*r_):H[e_]+=1
        if cnt==0:star(n-s[a]-s[b]-s[g],s[a],s[b],s[g])
        elif cnt==3:path(n-s[a],s[a]-s[b],s[b]-s[g],s[g])
        elif cnt==2:
            top=[u for u in tri if sum(isanc(u,v) for v in tri)==2][0];oth=[v for v in tri if v!=top]
            star(s[top]-s[oth[0]]-s[oth[1]],n-s[top],s[oth[0]],s[oth[1]])
        else:
            u,v=next((u,v) for u,v in itertools.permutations(tri,2) if isanc(u,v));h=[w for w in tri if w not in(u,v)][0]
            path(s[h],n-s[h]-s[u],s[u]-s[v],s[v])
    return A,B,H
def is_cat(T):
    I=T.subgraph([v for v in T if T.degree(v)>1])
    return len(I)<=1 or max(d for _,d in I.degree())<=2
key=lambda c:tuple(sorted((k,v) for k,v in c.items() if v))
if __name__=='__main__':
  stat=Counter();ex=[]
  for n in range(10,int(sys.argv[1])+1):
    g=defaultdict(list)
    for T in nx.nonisomorphic_trees(n):
        d=data(T);n_,c,o,par,s,anc=d;A=Counter();B=Counter()
        for v in o[1:]:A[s[v]]+=1
        ed=o[1:]
        for e,f in itertools.combinations(ed,2):
            B[s[e]-s[f] if e in anc[f] else s[f]-s[e] if f in anc[e] else n-s[e]-s[f]]+=1
        g[(key(A),key(B))].append(T)
    mix=[v for v in g.values() if len(v)>1 and any(is_cat(T) for T in v) and not all(is_cat(T) for T in v)]
    for v in mix:
        cat=[T for T in v if is_cat(T)][0];non=[T for T in v if not is_cat(T)]
        hc=ABH(cat)[2]
        for N_ in non:
            d=Counter(hc);d.subtract(ABH(N_)[2]);d={k:b for k,b in d.items() if b}
            deg=sorted(dict(cat.degree()).values())!=sorted(dict(N_.degree()).values())
            stat[(n,'deg-sep' if deg else 'deg-same')]+=1
            if len(ex)<40 and (not deg or n<=14):ex.append((n,'top',max(d),d[max(d)],'low',min(d),d[min(d)],'deg',deg,'cat',sorted(dict(cat.degree()).values())[-4:],'non',sorted(dict(N_.degree()).values())[-4:]))
  print(stat)
  for e in ex:print(e)
