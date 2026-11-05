import sys,json
from analyze import load,pats,P
from flint import nmod_mat
from collections import deque,defaultdict
fn=sys.argv[1];rows=load(fn);Q=pats(fn+'.pats');Vm=max(r[0] for r in rows)
def girth(n,ed):
    adj=defaultdict(list)
    for a,b in ed: adj[a].append(b);adj[b].append(a)
    best=99
    for s in range(n):
        d={s:0};par={s:-1};q=deque([s])
        while q:
            u=q.popleft()
            for w in adj[u]:
                if w not in d: d[w]=d[u]+1;par[w]=u;q.append(w)
                elif par[u]!=w: best=min(best,d[u]+d[w]+1)
    return best
G=[girth(q[0],q[3]) for q in Q];out={}
for g in (3,4,5,6,7):
    cols=[0]+[j+1 for j in range(len(Q)) if G[j]>=g];ci={c:i for i,c in enumerate(cols)};seq=[]
    for V in range(1,Vm+1):
        R=[r for r in rows if r[0]<=V];M=[0]*(len(R)*len(cols))
        for i,(v,e,d) in enumerate(R):
            for c,x in d.items():
                if c in ci: M[i*len(cols)+ci[c]]=x.numerator*pow(x.denominator,-1,P)%P
        seq.append(int(nmod_mat(len(R),len(cols),M,P).rank()))
    out[g]={"ranks":seq,"new":[seq[0]]+[seq[i]-seq[i-1] for i in range(1,len(seq))],"columns":len(cols)};print(g,out[g],flush=True)
json.dump(out,open(sys.argv[2],'w'),indent=1)
