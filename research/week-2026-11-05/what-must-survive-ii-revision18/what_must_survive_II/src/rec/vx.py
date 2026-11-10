exec(open('ex.py').read().split("res={}")[0])
import json,random
def path(m):
    t=()
    for _ in range(m):t=(t,)
    return t
def spider(a,b):
    return (tuple(sorted((path(a-1),path(b-1)),reverse=True)),)
out={}
def vols(line,Vm):
    v=list(map(int,line.split()));n=v[0];adj=[[] for _ in range(n)]
    for i in range(1,n):adj[i].append(v[1+i]);adj[v[1+i]].append(i)
    r={}
    for V in range(1,Vm+1):
        c=Counter()
        for ms in itertools.combinations_with_replacement(range(n),V):
            h=Counter(ms);E=0
            for u,a in h.items():
                for w in adj[u]:
                    if w in h:
                        if u<w:E+=(a-h[w])**2
                    else:E+=a*a
            c[E]+=1
        r[V]=c
    return r
rows=[]
for V in (1,2):
    A,B=(spider(V+1,V+1),),(spider(V+2,V),)
    A,B=spider(V+1,V+1),spider(V+2,V)
    T,S=enc(A+A,B+B),enc(A+B,A+B);a,b=vols(T,V+1),vols(S,V+1)
    first=next((k for k in a if a[k]!=b[k]),None)
    rows.append(dict(V=V,n=len(T.split())-1,first_differing_volume=first));print(rows[-1],flush=True)
out['explicit_direct']=rows
# fingerprint through larger V, explicit family
P=(1<<61)-1
for V in range(5,10):
    qv=random.Random(V).randrange(2,P)
    def tr(m,a,memo={}):
        # leg of m vertices attached at height a, series mod x^{V+1}
        k=(m,a,V)
        if k in memo:return memo[k]
        r=[0]*(V+1)
        for b in range(V+1):
            w=pow(qv,(a-b)**2,P);sub=tr(m-1,b) if m>1 else [1]+[0]*V
            for j,u in enumerate(sub):
                if b+j<=V:r[b+j]=(r[b+j]+w*u)%P
        memo[k]=r;return r
    def mul(a,b):
        c=[0]*(V+1)
        for i,u in enumerate(a):
            for j,v in enumerate(b):
                if i+j<=V:c[i+j]=(c[i+j]+u*v)%P
        return c
    ok=all(mul(tr(V+1,a),tr(V+1,a))[:V+1-a]==mul(tr(V+2,a),tr(V,a))[:V+1-a] for a in range(V+1))
    # root vertex: W=single rooted tree attached: arm height b, root contributes x^b
    print('V',V,'leg identity',ok,flush=True);out[f'leg_{V}']=ok
json.dump(out,open('vx.json','w'),indent=1)
