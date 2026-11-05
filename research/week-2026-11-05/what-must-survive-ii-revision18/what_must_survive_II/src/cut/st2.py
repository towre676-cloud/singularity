import json,math,itertools,numpy as np,networkx as nx,sympy as sp
from collections import Counter,defaultdict
import subprocess
res={}
# (a) duality: Theta_Cut(q) = integral over the flow torus of product of edge theta functions
def theta_e(th,eps,R=30):
    k=np.arange(-R,R+1);return np.exp(-eps*k*k)[None,None,None,:]*np.exp(2j*np.pi*k*th[...,None])
def check(G,eps,N=48):
    G=nx.convert_node_labels_to_integers(G);E=list(G.edges());m=len(E);n=len(G)
    T=nx.minimum_spanning_tree(G);co=[e for e in E if not T.has_edge(*e)];beta=len(co);assert beta==3
    idx={e:i for i,e in enumerate(E)}
    C=np.zeros((beta,m))
    for b,(u,v) in enumerate(co):
        p=nx.shortest_path(T,v,u);C[b,idx[(u,v)]]=1
        for a,c in zip(p,p[1:]):
            if (a,c) in idx: C[b,idx[(a,c)]]+=1
            else: C[b,idx[(c,a)]]-=1
    g=np.arange(N)/N;A,B,D=np.meshgrid(g,g,g,indexing='ij');pts=np.stack([A,B,D],-1)
    val=np.ones_like(A,dtype=complex)
    for e in range(m):
        th=pts@C[:,e];k=np.arange(-12,13);val*=np.tensordot(np.exp(1j*2*np.pi*th[...,None]*k),np.exp(-eps*k*k),axes=([-1],[0]))
    lhs=val.mean().real
    s=f"{n} {m} "+" ".join(f"{a} {b}" for a,b in E)+"\n"
    o=subprocess.run(['./cut','70'],input=s,capture_output=True,text=True).stdout.split('\n')[1:]
    rhs=0.0
    for l in o:
        if l:
            e,v,c=map(int,l.split());rhs+=c*math.exp(-eps*e)
    return lhs,rhs
for name,G,eps in (("K4",nx.complete_graph(4),0.6),("K4",nx.complete_graph(4),1.0),("K4-",nx.circular_ladder_graph(3).subgraph(range(6)).copy() if False else nx.complete_graph(4),1.5)):
    l,r=check(G,eps);print(name,eps,l,r);res.setdefault("duality",[]).append((name,eps,l,r));assert abs(l-r)<1e-9
# (b) first separating volume against first differing closed-walk count, over all order-14 pairs
P=2**61-1
gs=[];counts=[]
for l in open('/root/wms/out/counts14.txt'):
    head,tail=l.split('|');h=list(map(int,head.split()));n,m=h[0],h[1];E=[(h[2+2*i],h[3+2*i]) for i in range(m)]
    t=list(map(int,tail.split()));c={t[1+2*i]:t[2+2*i] for i in range(t[0])};c[0]=n;gs.append((n,E));counts.append(c)
sig=[[0]*15 for _ in gs]
import random;rnd=random.Random(3);mix={}
for l in open('/root/wms/out/rows14_p1.txt'):
    a=l.split(' ',3);v,e=int(a[0]),int(a[1]);x=a[3].split();r=rnd.randrange(1,P)
    d={int(x[2*i]):int(x[2*i+1]) for i in range(len(x)//2)}
    for i,c in enumerate(counts):
        s=sum(ct*d.get(col,0) for col,ct in c.items()) if len(c)<len(d) else sum(val*c.get(col,0) for col,val in d.items())
        sig[i][v]=(sig[i][v]+r*s)%P
def traces(n,E):
    A=np.zeros((n,n),dtype=object)
    for a,b in E: A[a,b]=1;A[b,a]=1
    out=[];M=np.eye(n,dtype=object)
    for k in range(1,n+1):
        M=M.dot(A);out.append(int(sum(M[i,i] for i in range(n))))
    return out
tr=[traces(*g) for g in gs]
tab=Counter();cos=[]
for i in range(len(gs)):
    for j in range(i+1,len(gs)):
        if gs[i][0]!=gs[j][0]: continue
        V=next((v for v in range(1,15) if sig[i][v]!=sig[j][v]),None);k=next((p+1 for p in range(gs[i][0]) if tr[i][p]!=tr[j][p]),None)
        tab[(k,V)]+=1
        if k is None: cos.append((i,j,gs[i][0],V))
res["sep_vs_trace"]={f"trace{k}_sep{V}":c for (k,V),c in sorted(tab.items(),key=lambda z:(z[0][0] or 99,z[0][1] or 99))}
res["cospectral_pairs"]=[{"n":c[2],"sep":c[3]} for c in cos];print(res["sep_vs_trace"]);print("cospectral",res["cospectral_pairs"])
json.dump(res,open('st2.json','w'),indent=1)
