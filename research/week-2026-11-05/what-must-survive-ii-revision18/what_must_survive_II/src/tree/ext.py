import networkx as nx,subprocess,json,warnings,sys,itertools,math
warnings.filterwarnings("ignore")
from collections import Counter,defaultdict
exec(open('tr.py').read().split("# (A) two-edge")[0].split("res={}")[1])
res={}
for n in (15,16,17,18):
    Ts=list(nx.nonisomorphic_trees(n));o=subprocess.run(['./shell','3'],input="\n".join(enc(T) for T in Ts)+"\n",capture_output=True,text=True).stdout.strip().split('\n')
    w=[l.split() for l in o];row={}
    for E in (1,2,3):
        g=Counter(tuple(x[2:2+E]) for x in w);row[E]=sum(c-1 for c in g.values())
    g=defaultdict(list)
    for i,x in enumerate(w): g[tuple(x[2:5])].append(i)
    left=[v for v in g.values() if len(v)>1]
    res[n]={"trees":len(Ts),"unseparated_through_energy":row,"survivor_edges":[[list(Ts[i].edges()) for i in v] for v in left][:6]};print(n,len(Ts),row,flush=True)
    for v in left[:6]:
        for E in (4,5,6):
            a=[subprocess.run(['./shell',str(E)],input=enc(Ts[i])+"\n",capture_output=True,text=True).stdout.split()[1:] for i in v]
            if len({tuple(x) for x in a})>1:
                print("  survivor class size",len(v),"separated at energy",E);res[n].setdefault("survivor_sep",[]).append(E);break
# 18-vertex survivors through volume 7
Ts=list(nx.nonisomorphic_trees(18))
o=subprocess.run(['/root/wms/mark/tree','7'],input="\n".join(enc(T) for T in Ts)+"\n",capture_output=True,text=True).stdout.strip().split('\n');g=defaultdict(list)
for i,l in enumerate(o): g[l].append(i)
sv=[v for v in g.values() if len(v)>1];res["volume7_survivors"]=[]
for v in sv:
    tabs=[table(Ts[i],5) for i in v];sep=next((e for e in range(1,6) if tabs[0][e]!=tabs[1][e]),None);d=None
    if sep:
        d=sorted((k,tabs[0][sep][k]-tabs[1][sep][k]) for k in set(tabs[0][sep])|set(tabs[1][sep]) if tabs[0][sep][k]!=tabs[1][sep][k])
    prof=[sorted(profiles(Ts[i])) for i in v]
    r={"pair":[list(Ts[i].edges()) for i in v],"first_energy":sep,"difference_by_volume":d,"profiles_equal":prof[0]==prof[1]};res["volume7_survivors"].append(r);print("V7 survivor: energy",sep,"diff",d,"profiles equal",r["profiles_equal"],flush=True)
# (D) x->infinity product law
def theta(y,q,R=60): return sum(y**z*q**(z*z) for z in range(-R,R+1))
out=[]
for T in (nx.path_graph(6),nx.star_graph(5),list(nx.nonisomorphic_trees(9))[20]):
    n=len(T);q=0.35;prof=profiles(T)
    # exact M by enumeration in z
    E=list(nx.bfs_edges(T,list(T)[0]));ord_=[list(T)[0]]+[w for u,w in E];par={w:u for u,w in E}
    def M(x):
        tot=0;h={ord_[0]:0}
        def rec(i,w):
            nonlocal tot
            if i==n:
                vals=list(h.values());tot+=w*x**(sum(vals)-n*min(vals));return
            v=ord_[i]
            for z in range(-7,8):
                if q**(z*z)*w<1e-40*0+0: continue
                h[v]=h[par[v]]+z;rec(i+1,w*q**(z*z))
        return tot
    if n>7: continue
    for X in (1.5,3.0,6.0):
        m=M(X);rho=[sum(s*s for s in p) for p in prof];top=max(rho);F=sum(math.prod(theta(X**s,q) for s in p) for p,r in zip(prof,rho) if r==top);Fall=sum(math.prod(theta(X**s,q) for s in p) for p in prof)
        out.append({"n":n,"x":X,"M":m,"top_product_ratio":m/F,"all_product_ratio":m/Fall})
res["x_infinity"]=out;print(out)
json.dump(res,open('ext.json','w'),indent=1)
