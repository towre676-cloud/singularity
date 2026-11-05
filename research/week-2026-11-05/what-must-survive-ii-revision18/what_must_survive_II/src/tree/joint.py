import networkx as nx,subprocess,json,warnings,itertools,math
warnings.filterwarnings("ignore")
from collections import Counter,defaultdict
exec(open('tr.py').read().split("# (A) two-edge")[0].split("res={}")[1])
res={}
def triples(T):
    # multiset of (b,{a,c}) for all edge pairs, using rooted sizes
    r=list(T)[0];E=list(nx.bfs_edges(T,r));par={w:u for u,w in E};order=[r]+[w for u,w in E];n=len(T)
    sz=Counter({v:1 for v in T})
    for v in reversed(order[1:]): sz[par[v]]+=sz[v]
    anc={r:set()}
    for v in order[1:]: anc[v]=anc[par[v]]|{par[v]}
    out=Counter()
    vs=order[1:]
    for u,v in itertools.combinations(vs,2):
        # edges above u and v
        if u in anc[v] or v in anc[u]:
            top,bot=(u,v) if u in anc[v] else (v,u)
            a=n-sz[top];b=sz[top]-sz[bot];c=sz[bot]
        else:
            a=sz[u];c=sz[v];b=n-a-c
        out[(b,min(a,c),max(a,c))]+=1
    return tuple(sorted(out.items()))
rows={}
for n in range(7,18):
    Ts=list(nx.nonisomorphic_trees(n));o=subprocess.run(['./shell','3'],input="\n".join(enc(T) for T in Ts)+"\n",capture_output=True,text=True).stdout.strip().split('\n');w=[l.split() for l in o]
    tr=[triples(T) for T in Ts]
    s2=defaultdict(list);s3=defaultdict(list);tg=defaultdict(list)
    for i,x in enumerate(w): s2[tuple(x[2:4])].append(i);s3[tuple(x[2:5])].append(i);tg[tr[i]].append(i)
    c2=[v for v in s2.values() if len(v)>1]
    split=sum(1 for v in c2 if len({tr[i] for i in v})>1)
    tc=[v for v in tg.values() if len(v)>1]
    t3=sum(1 for v in tc if len({tuple(w[i][2:5]) for i in v})>1)
    s3x=[v for v in s3.values() if len(v)>1];t_in_s3=sum(1 for v in s3x if len({tr[i] for i in v})>1)
    rows[n]={"trees":len(Ts),"shell12_collision_classes":len(c2),"of_which_triples_differ":split,"triple_collision_classes":len(tc),"triple_classes_split_by_shell3":t3,"shell123_collision_classes":len(s3x),"of_which_triples_differ":split,"shell123_classes_triples_differ":t_in_s3};print(n,rows[n],flush=True)
    if n==10:
        for v in c2:
            A,B=Ts[v[0]],Ts[v[1]];ta,tb=table(A,3),table(B,3);res["n10_pair"]={"edges":[list(A.edges()),list(B.edges())],"shell3_difference":sorted((k,ta[3][k]-tb[3][k]) for k in set(ta[3])|set(tb[3]) if ta[3][k]!=tb[3][k]),"triples_equal":tr[v[0]]==tr[v[1]]};print(res["n10_pair"])
res["rows"]=rows
# (D) product law
def theta(y,q,R=40): return sum(y**z*q**(z*z) for z in range(-R,R+1))
out=[]
for name,T in (("path6",nx.path_graph(6)),("star6",nx.star_graph(5))):
    n=len(T);q=0.35;prof=profiles(T);E=list(nx.bfs_edges(T,0));ord_=[0]+[w for u,w in E];par={w:u for u,w in E}
    def M(x):
        tot=[0.0];h={0:0}
        def rec(i,w):
            if i==n:
                vals=list(h.values());tot[0]+=w*x**(sum(vals)-n*min(vals));return
            v=ord_[i]
            for z in range(-6,7):
                h[v]=h[par[v]]+z;rec(i+1,w*q**(z*z))
        rec(1,1.0);return tot[0]
    rho=[sum(s*s for s in p) for p in prof];top=max(rho)
    for X in (1.5,3.0,6.0,12.0):
        m=M(X);F=sum(math.prod(theta(X**s,q) for s in p) for p,r in zip(prof,rho) if r==top)
        out.append({"tree":name,"x":X,"ratio_M_over_top_products":m/F,"top_vertices":sum(r==top for r in rho)})
res["product_law"]=out;print(out)
json.dump(res,open('joint.json','w'),indent=1)
