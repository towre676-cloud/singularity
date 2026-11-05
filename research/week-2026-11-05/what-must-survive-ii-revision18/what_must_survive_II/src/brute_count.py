# independent count of connected leafless subcubic graphs via networkx atlas-free labelled enumeration
import networkx as nx, itertools, sys
from networkx.algorithms.graph_hashing import weisfeiler_lehman_graph_hash as wl
def run(n):
    pairs=list(itertools.combinations(range(n),2)); seen={}
    def rec(i,deg,ed):
        if i==len(pairs):
            if min(deg)>=2:
                G=nx.Graph();G.add_nodes_from(range(n));G.add_edges_from(ed)
                if nx.is_connected(G):
                    h=wl(G,iterations=4)
                    for H in seen.setdefault(h,[]):
                        if nx.is_isomorphic(G,H):return
                    seen[h].append(G)
            return
        u,v=pairs[i]
        rec(i+1,deg,ed)
        if deg[u]<3 and deg[v]<3:
            deg[u]+=1;deg[v]+=1;ed.append((u,v));rec(i+1,deg,ed);ed.pop();deg[u]-=1;deg[v]-=1
    rec(0,[0]*n,[]); return sum(len(v) for v in seen.values())
for n in range(3,8): print(n,run(n),flush=True)
