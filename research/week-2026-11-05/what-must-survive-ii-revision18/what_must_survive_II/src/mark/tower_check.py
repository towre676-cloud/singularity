import networkx as nx,subprocess,json
from collections import Counter,defaultdict
res={}
# (1) stability against direct histograms
def hist(g,V):
    n=len(g);nodes=sorted(g);ix={v:i for i,v in enumerate(nodes)};E=[(ix[a],ix[b]) for a,b in g.edges()];c=Counter();h=[0]*n
    def rec(i,left):
        if i==n-1:
            h[i]=left;c[sum((h[a]-h[b])**2 for a,b in E)]+=1;return
        for a in range(left+1): h[i]=a;rec(i+1,left-a)
    rec(0,V);return c
for name,g,V,R in (("K4",nx.complete_graph(4),30,5),("K33",nx.complete_bipartite_graph(3,3),22,4),("Petersen",nx.petersen_graph(),13,2)):
    nodes=sorted(g);ix={v:i for i,v in enumerate(nodes)};s=f"{len(g)} {g.number_of_edges()} "+" ".join(f"{ix[a]} {ix[b]}" for a,b in g.edges())+"\n"
    o=subprocess.run(['./tower',str(R),'p'],input=s,capture_output=True,text=True).stdout.split('\n')[1:];T=Counter()
    for l in o:
        if l:
            r,k,nu,c=map(int,l.split());T[(k,nu)]+=c
    H=hist(g,V);bad=0;tested=0;Kmax=6*(R+1)-1
    # energies above 3V^2-Kmax*V+... : all configurations with kappa<=Kmax have rest<=R
    pred=Counter()
    for (k,nu),c in T.items():
        if k<=Kmax: pred[3*V*V-k*V+nu]+=c
    # any configuration with kappa>Kmax has energy at most 3V^2-kappa*V+kappa^2/6, decreasing in kappa while kappa<3V
    cut=3*V*V-(Kmax+1)*V+(Kmax+1)**2/6
    for e in sorted(set(H)|set(pred)):
        if e>cut:
            tested+=1
            if H.get(e,0)!=pred.get(e,0): bad+=1
    res[name]={"V":V,"energies_tested":tested,"mismatches":bad,"top":[(e,H[e]) for e in sorted(H,reverse=True)[:4]]};print(name,res[name],flush=True)
# (2) separating power on all connected cubic graphs to 14 vertices
hs=open('/root/wms/out/hosts14.txt').read()
o=subprocess.run(['./tower','6'],input=hs,capture_output=True,text=True).stdout.strip().split('\n')
rows=[l.split() for l in o];lines=hs.strip().split('\n')
tab={}
for R in range(0,7):
    g=defaultdict(list)
    for w in rows: g[(w[2],tuple(w[3:4+R]))].append(int(w[1]))
    tab[R]={"collision_classes":sum(1 for v in g.values() if len(v)>1),"graphs":sum(len(v) for v in g.values() if len(v)>1)}
res["cubic_separation_by_tower_level"]=tab;print(tab)
# late pair
up=open('/root/wms/out/unsep.txt').read().strip().split('\n');o2=subprocess.run(['./tower','6'],input="\n".join(up)+"\n",capture_output=True,text=True).stdout.strip().split('\n');a,b=[x.split()[3:] for x in o2]
res["late_pair_first_level"]=next((i for i,(p,q) in enumerate(zip(a,b)) if p!=q),None);print("late pair first differing tower level r =",res["late_pair_first_level"])
json.dump(res,open('tower_check.json','w'),indent=1)
