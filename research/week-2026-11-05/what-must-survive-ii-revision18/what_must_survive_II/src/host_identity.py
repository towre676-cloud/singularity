# Exact identity certificate: certified rows times subgraph counts equal log L_G from direct integer enumeration.
import sys,json,subprocess
from fractions import Fraction as Fr
from collections import defaultdict
from analyze import load
rows=load(sys.argv[1]);VM=max(r[0] for r in rows);byve=defaultdict(dict)
for v,e,d in rows: byve[v][e]=d
res=[]
for l in open(sys.argv[2]):
    head,tail=l.split('|');h=head.split();n=int(h[0]);graph=" ".join(h)+"\n";t=list(map(int,tail.split()));cnt={t[1+2*i]:t[2+2*i] for i in range(t[0])};cnt[0]=n
    Vuse=min(VM,13) if n<=14 else 10
    o=subprocess.run(['./hist',str(Vuse)],input=graph,capture_output=True,text=True).stdout.split('\n')[1:]
    Z=[{} for _ in range(Vuse+1)]
    for x in o:
        if x: a,b,c=map(int,x.split());Z[a][b]=c
    # log series exact
    lg=[{} for _ in range(Vuse+1)]
    for t_ in range(1,Vuse+1):
        s=defaultdict(Fr)
        for e,c in Z[t_].items(): s[e]+=Fr(c*t_)
        for k in range(1,t_):
            for e1,c1 in lg[k].items():
                for e2,c2 in Z[t_-k].items(): s[e1+e2]-=c1*k*c2
        lg[t_]={e:c/t_ for e,c in s.items() if c}
    ok=True
    for V in range(1,Vuse+1):
        pred=defaultdict(Fr)
        for e,d in byve[V].items():
            val=sum(x*cnt.get(c,0) for c,x in d.items())
            if val: pred[e]=val
        if dict(pred)!=lg[V]: ok=False;print("FAIL",n,V)
    res.append({"n":n,"V":Vuse,"ok":ok})
print(res);assert all(r['ok'] for r in res);json.dump(res,open(sys.argv[3],'w'),indent=1)
