import networkx as nx,subprocess
def enc(G):
    E=list(nx.bfs_edges(G,0));o=[0]+[v for u,v in E];ix={v:i for i,v in enumerate(o)};p=[0]*len(o)
    for u,v in E:p[ix[v]]=ix[u]
    return f"{len(o)} "+" ".join(map(str,p))
def build(ed,p):
    G=nx.Graph(ed);k=len(p)
    for v,c in enumerate(p):
        for _ in range(c):G.add_edge(v,k);k+=1
    return G
a=[(0,1),(0,5),(1,2),(1,3),(1,4),(5,6)];b=[(0,1),(0,4),(0,6),(1,2),(1,3),(4,5)]
L=[];K=list(range(8,41))
for k in K:
    L+= [enc(build(a,[4,0,1,1,k-6,k-8,1])),enc(build(b,[2,2,1,k-6,k-8,1,1]))]
o=subprocess.run(['./fast','6'],input="\n".join(L)+"\n",capture_output=True,text=True).stdout.split();print(set(o),len(o))
