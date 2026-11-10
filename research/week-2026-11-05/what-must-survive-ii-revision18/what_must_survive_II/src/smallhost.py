# Do small hosts (order <= V) in classes k=1,2,3 ever need more than the window panels? Exact test on all connected cubic graphs of order <=12.
import sys,json,networkx as nx
from analyze import load
from collections import defaultdict
rows=load(sys.argv[1]);w=json.load(open(sys.argv[2]));VM=max(r[0] for r in rows)
hosts=[]
for l in open(sys.argv[3]):
    head,tail=l.split('|');h=list(map(int,head.split()));n,m=h[0],h[1];E=[(h[2+2*i],h[3+2*i]) for i in range(m)]
    t=list(map(int,tail.split()));c={t[1+2*i]:t[2+2*i] for i in range(t[0])};c[0]=n
    hosts.append((n,nx.edge_connectivity(nx.Graph(E)),c))
print(len(hosts))
val=[{} for _ in hosts]
for v,e,d in rows:
    for i,(n,kc,c) in enumerate(hosts):
        val[i][(v,e)]=sum(x*c.get(col,0) for col,x in d.items())
res={}
for k in '123':
    panel=set()
    tests=0;fail=[];ambig=0
    for rec in w[k]:
        V=rec['V']
        if rec['new']:
            for e in range(rec['emin'],rec['emax']+1,2): panel.add((V,e))
        for i in range(len(hosts)):
            if hosts[i][1]<int(k) or hosts[i][0]>V: continue
            for j in range(i+1,len(hosts)):
                if hosts[j][1]<int(k) or hosts[j][0]!=hosts[i][0]: continue
                if all(val[i][p]==val[j][p] for p in panel):
                    tests+=1
                    d=[(v,e) for (v,e) in val[i] if v<=V and val[i][(v,e)]!=val[j][(v,e)]]
                    if d: fail.append((V,hosts[i][0],d[:3]))
    res[k]={"pairs_with_equal_panel":tests,"failures":[str(f) for f in fail[:10]],"n_failures":len(fail)};print(k,res[k])
# distinguishing power among all small pairs: panel separates all?
json.dump(res,open(sys.argv[4],'w'),indent=1)
