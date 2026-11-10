# Window panels through V=order separate every equal-order pair of connected cubic graphs (order<=14), class by class.
# Separation is tested modulo a prime: unequal residues imply unequal rationals, so it is rigorous.
import json
from collections import defaultdict
P=2**61-1
w=json.load(open('/root/wms/receipts/windows_V14.json'));import networkx as nx
hosts=[]
for l in open('/root/wms/out/counts14.txt'):
    head,tail=l.split('|');h=list(map(int,head.split()));n,m=h[0],h[1];E=[(h[2+2*i],h[3+2*i]) for i in range(m)]
    t=list(map(int,tail.split()));c={t[1+2*i]:t[2+2*i] for i in range(t[0])};c[0]=n
    hosts.append((n,nx.edge_connectivity(nx.Graph(E)),c))
panelsets={}
for k in '123':
    p=set()
    for r in w[k]:
        if r['new']:
            for e in range(r['emin'],r['emax']+1,2): p.add((r['V'],e))
    panelsets[k]=p
need=set().union(*panelsets.values());vals=[{} for _ in hosts]
for l in open('/root/wms/out/rows14_p1.txt'):
    a=l.split(' ',3);v,e=int(a[0]),int(a[1])
    if (v,e) not in need: continue
    x=a[3].split();d={int(x[2*i]):int(x[2*i+1]) for i in range(len(x)//2)}
    for i,(n,kc,c) in enumerate(hosts):
        if len(c)<len(d): vals[i][(v,e)]=sum(ct*d.get(col,0) for col,ct in c.items())%P
        else: vals[i][(v,e)]=sum(val*c.get(col,0) for col,val in d.items())%P
res={}
for k in '123':
    un=0;pairs=0;by=defaultdict(list)
    for i,(n,kc,c) in enumerate(hosts):
        if kc>=int(k):
            sig=tuple(vals[i][p] for p in sorted(panelsets[k]) if p[0]<=n);by[(n,sig)].append(i);pairs+=1
    un=sum(len(v)-1 for v in by.values());res[k]={"hosts":pairs,"unseparated":un};print(k,res[k],flush=True)
json.dump(res,open('/root/wms/receipts/small_hosts_V14.json','w'),indent=1)
