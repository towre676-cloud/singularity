import sys,json,itertools
from analyze import load,pats
from collections import defaultdict
fn=sys.argv[1];rows=load(fn);Q=pats(fn+'.pats');Vm=max(r[0] for r in rows)
col=defaultdict(dict)
for v,e,d in rows:
    for c,x in d.items(): col[c][(v,e)]=x
def leafless_conn(edges):
    deg=defaultdict(int)
    for a,b in edges: deg[a]+=1;deg[b]+=1
    if min(deg.values())<2: return False
    adj=defaultdict(list)
    for a,b in edges: adj[a].append(b);adj[b].append(a)
    s=[edges[0][0]];seen={edges[0][0]}
    while s:
        for w in adj[s.pop()]:
            if w not in seen: seen.add(w);s.append(w)
    return len(seen)==len(deg)
def dcount(ed):
    # unordered pairs (A,B) of connected leafless subgraphs, A cup B = Q, sharing exactly one edge
    m=len(ed);cnt=0
    for i in range(m):
        rest=[j for j in range(m) if j!=i]
        for mask in range(1<<len(rest)):
            A=[ed[i]]+[ed[rest[t]] for t in range(len(rest)) if mask>>t&1]
            B=[ed[i]]+[ed[rest[t]] for t in range(len(rest)) if not mask>>t&1]
            if len(A)<3 or len(B)<3: continue
            VA={v for e in A for v in e};VB={v for e in B for v in e}
            if len(VA&VB)!=2: continue
            if leafless_conn(A) and leafless_conn(B): cnt+=1
    return cnt//2
res={}
seen={};bad=0;tested=0;classes=defaultdict(set)
for j,(k,E,cm,ed) in enumerate(Q):
    if k+2>Vm: continue
    deg=[0]*k
    for a,b in ed: deg[a]+=1;deg[b]+=1
    e22=sum(1 for a,b in ed if deg[a]==2 and deg[b]==2)
    inv=(k,E,e22,dcount(ed))
    key=tuple(sorted((ve,x) for ve,x in col[j+1].items() if ve[0]<=k+2))
    tested+=1;classes[k].add(inv)
    if inv in seen and seen[inv]!=key: bad+=1
    seen.setdefault(inv,key)
res={"patterns_tested":tested,"violations":bad,"invariant_classes_by_k":{k:len(v) for k,v in classes.items()}}
print(res);json.dump(res,open(sys.argv[2],'w'),indent=1)
