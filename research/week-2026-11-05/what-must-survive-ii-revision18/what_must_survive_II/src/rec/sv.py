import subprocess,collections,json,networkx as nx
def show(I):
    v=list(map(int,I.split()));n=v[0];p=v[1:];G=nx.Graph([(i,p[i]) for i in range(1,n)])
    J=G.subgraph([u for u in G if G.degree(u)>1])
    bal=0
    for e in list(G.edges()):
        H=G.copy();H.remove_edge(*e)
        if 2*len(nx.node_connected_component(H,e[0]))==n:bal+=1
    return dict(internal=len(J),maxint=max(d for _,d in J.degree()),branch=sum(1 for _,d in J.degree() if d>=3),balanced=bal,diam=nx.diameter(G),pend=sorted((G.degree(u)-J.degree(u)) for u in J)[-5:])
for n in (16,17,18,19):
    inp=subprocess.run(['python3','/root/wms/cat/genp.py',str(n)],capture_output=True,text=True).stdout
    o=subprocess.run(['/root/wms/tree/shell','3'],input=inp,capture_output=True,text=True).stdout.strip().split('\n');I=inp.strip().split('\n')
    cl=collections.defaultdict(list)
    for L,i in zip(o,I):cl[tuple(L.split()[1:])].append(i)
    col=[v for v in cl.values() if len(v)>1]
    print(n,len(col))
    for v in col[:4 if n>17 else 2]:
        print('  ',[show(i) for i in v]);print('   parents',[i for i in v])
    st=collections.Counter()
    for v in col:
        st[(tuple(sorted(show(i)['branch'] for i in v)),show(v[0])['balanced']>0)]+=1
    print('  branch/balanced',dict(st))
