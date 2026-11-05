import subprocess,collections,itertools,networkx as nx,json,warnings
warnings.filterwarnings("ignore")
exec(open('sw.py').read().split("out={}")[0])
from collections import Counter
def gen(G,root,forbid):
    # sizes of edges in arms at root avoiding neighbors in forbid
    return None
def analyse(T,S):
    """find swap and test: U,V weights equal; middle symmetric under automorphism swapping u,v"""
    res=[]
    for u,v in itertools.combinations(T,2):
        P=nx.shortest_path(T,u,v);du=[w for w in T[u] if w!=P[1]];dv=[w for w in T[v] if w!=P[-2]]
        if len(du)>7 or len(dv)>7:continue
        def comp(root,c):
            H=T.copy();H.remove_edge(root,c);return nx.node_connected_component(H,c)
        for r in range(0,len(du)+1):
            for Cu in itertools.combinations(du,r):
                for r2 in range(0,len(dv)+1):
                    if r==0 and r2==0:continue
                    for Cv in itertools.combinations(dv,r2):
                        wu=sum(len(comp(u,c)) for c in Cu);wv=sum(len(comp(v,c)) for c in Cv)
                        if wu!=wv:continue
                        G=T.copy()
                        for c in Cu:G.remove_edge(u,c);G.add_edge(v,c)
                        for c in Cv:G.remove_edge(v,c);G.add_edge(u,c)
                        if not(nx.faster_could_be_isomorphic(G,S) and nx.is_isomorphic(G,S)):continue
                        # remaining arms
                        Ru=[w for w in du if w not in Cu];Rv=[w for w in dv if w not in Cv]
                        wRu=sum(len(comp(u,c)) for c in Ru);wRv=sum(len(comp(v,c)) for c in Rv)
                        Mid=T.copy()
                        for c in list(Ru)+list(Cu):Mid.remove_nodes_from(comp(u,c))
                        for c in list(Rv)+list(Cv):Mid.remove_nodes_from(comp(v,c))
                        M1=Mid.copy();nx.set_node_attributes(M1,{w:(1 if w==u else 2 if w==v else 0) for w in M1},'m')
                        M2=Mid.copy();nx.set_node_attributes(M2,{w:(2 if w==u else 1 if w==v else 0) for w in M2},'m')
                        sym=nx.is_isomorphic(M1,M2,node_match=lambda a,b:a['m']==b['m'])
                        res.append(dict(dist=len(P)-1,wc=wu,wU=wRu,wV=wRv,sym=bool(sym),mid=len(Mid)))
    return res
out={}
for n in (20,21):
    inp=subprocess.run(['python3','/root/wms/cat/genp.py',str(n)],capture_output=True,text=True).stdout
    o=subprocess.run(['/root/wms/tree/shell','3'],input=inp,capture_output=True,text=True).stdout.strip().split('\n');I=inp.strip().split('\n')
    cl=collections.defaultdict(list)
    for L,i in zip(o,I):cl[tuple(L.split()[1:])].append(i)
    col=[v for v in cl.values() if len(v)>1];c=collections.Counter()
    for v in col:
        r=analyse(parse(v[0]),parse(v[1]))
        good=[d for d in r if d['sym'] and d['wU']==d['wV']]
        c['explained' if good else 'unexplained']+=1
        if not good:print("UNEXPL",n,v)
    print(n,len(col),dict(c),flush=True);out[n]=dict(c)
json.dump(out,open("chkm2.json","w"))
