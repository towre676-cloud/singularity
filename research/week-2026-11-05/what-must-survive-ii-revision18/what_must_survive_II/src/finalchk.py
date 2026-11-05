import json,sys,subprocess
from fractions import Fraction as Fr
from collections import defaultdict
rows=[]
for l in open('/root/wms/out/rows14_exact.txt'):
    w=l.split();v,e,nz=int(w[0]),int(w[1]),int(w[2]);rows.append((v,e,{int(w[3+3*i]):Fr(int(w[4+3*i]),int(w[5+3*i])) for i in range(nz)}))
byve=defaultdict(dict)
for v,e,d in rows: byve[v][e]=d
res={"hosts":[]}
for l in open('/root/wms/out/counts_id14.txt'):
    head,tail=l.split('|');h=head.split();n=int(h[0]);t=list(map(int,tail.split()));cnt={t[1+2*i]:t[2+2*i] for i in range(t[0])};cnt[0]=n
    o=subprocess.run(['./hist','14'],input=" ".join(h)+"\n",capture_output=True,text=True).stdout.split('\n')[1:]
    Z=[{} for _ in range(15)]
    for x in o:
        if x:a,b,c=map(int,x.split());Z[a][b]=c
    lg=[{} for _ in range(15)]
    for T in range(1,15):
        s=defaultdict(Fr)
        for e,c in Z[T].items(): s[e]+=Fr(c*T)
        for k in range(1,T):
            for e1,c1 in lg[k].items():
                for e2,c2 in Z[T-k].items(): s[e1+e2]-=c1*k*c2
        lg[T]={e:c/T for e,c in s.items() if c}
    ok=True
    for V in range(1,15):
        pred={}
        for e,d in byve[V].items():
            val=sum(x*cnt.get(c,0) for c,x in d.items())
            if val: pred[e]=val
        ok&=pred==lg[V]
    res["hosts"].append({"n":n,"ok":ok})
print(res);assert all(x['ok'] for x in res['hosts'])
w=json.load(open('/root/wms/receipts/witness15_V14.json'));col={int(k)+1:Fr(v) for k,v in w['coeffs'].items()}
bad=0;R={}
for v,e,d in rows:
    s=sum(c*d.get(k,0) for k,c in col.items())
    if v<14 and s: bad+=1
    if v==14 and s:R[e]=s
res["witness15_certified_rows"]={"earlier_violations":bad,"top_e":max(R),"top":str(R[max(R)])};print(res["witness15_certified_rows"])
json.dump(res,open('/root/wms/receipts/final_V14_checks.json','w'),indent=1)
