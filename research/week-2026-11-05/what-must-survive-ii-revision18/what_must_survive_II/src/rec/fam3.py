import networkx as nx,sys,json,itertools,warnings
warnings.filterwarnings("ignore")
from collections import defaultdict
src=open('rs.py').read().split("out={}")[0];exec(src)
exec(open('r.py').read().split("if __name__")[0])
def parse(I):
    v=list(map(int,I.split()));n=v[0];G=nx.Graph([(i,v[1+i]) for i in range(1,n)]);return G
A0=parse('16 0 0 1 2 2 1 5 1 7 0 9 10 0 0 0 0');B0=parse('16 0 0 1 2 2 1 5 1 1 0 9 10 0 12 0 0')
def internal(G):
    J=G.subgraph([u for u in G if G.degree(u)>1]);return nx.convert_node_labels_to_integers(J,label_attribute='o')
Ia,Ib=internal(A0),internal(B0)
pa0=[A0.degree(Ia.nodes[v]['o'])-Ia.degree(v) for v in Ia];pb0=[B0.degree(Ib.nodes[v]['o'])-Ib.degree(v) for v in Ib]
print('a',sorted(Ia.edges()),pa0);print('b',sorted(Ib.edges()),pb0)
def build(I,p):
    G=nx.Graph(I.edges());k=len(I)
    for v,c in enumerate(p):
        for _ in range(c):G.add_edge(v,k);k+=1
    return G
sa,sb=setup(Ia),setup(Ib);m=7;res=[];Nmax=int(sys.argv[1])
for n in range(9,Nmax+1):
    cl=defaultdict(lambda:[[],[]])
    for idx,(I,st) in enumerate(((Ia,sa),(Ib,sb))):
        lo=[1 if I.degree(v)==1 else 0 for v in range(m)]
        for p in comps(n-m,m,lo):cl[sig(st,p)][idx].append(tuple(p))
    hits=[]
    for v in cl.values():
        if v[0] and v[1]:
            for p in v[0]:
                Hp=None
                for q in v[1]:
                    G,H=build(Ia,p),build(Ib,q)
                    if Hp is None:Hp=ABH(G)[2]
                    d=Counter(Hp);d.subtract(ABH(H)[2])
                    if not any(d.values()):
                        if not nx.is_isomorphic(G,H):hits.append((p,q))
    print(n,len(hits),hits[:6],flush=True);res.append((n,hits))
    json.dump(res,open('fam3.json','w'))
