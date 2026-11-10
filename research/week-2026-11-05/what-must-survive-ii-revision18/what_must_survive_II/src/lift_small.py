# Exact lifts for k=11..17 (V=15..21): solve the row k+3 principal-part system from invariants of real patterns at size k.
import sys,json,random,itertools,lzma
from lift import *
from analyze import pats
from flint import fmpq_mat,fmpq
Q=pats('/root/wms/out/rows14_p1.txt.pats');rnd=random.Random(11)
census={}
for q in Q: census.setdefault(q[0],[]).append((q[0],q[1],tuple(map(tuple,q[3]))))
def simple(ed): return len({tuple(sorted(e)) for e in ed})==len(ed)
def conn_leafless(k,ed):
    deg=[0]*k;adj=[[] for _ in range(k)]
    for a,b in ed: deg[a]+=1;deg[b]+=1;adj[a].append(b);adj[b].append(a)
    if min(deg)<2 or max(deg)>3: return False
    s=[0];seen={0}
    while s:
        for w_ in adj[s.pop()]:
            if w_ not in seen: seen.add(w_);s.append(w_)
    return len(seen)==k
def subdivide(q):
    k,E,ed=q;ed=list(ed);i=rnd.randrange(E);a,b=ed[i];ed[i]=(a,k);ed.append((k,b));return (k+1,E+1,tuple(ed))
def chord(q):
    k,E,ed=q;deg=[0]*k
    for a,b in ed: deg[a]+=1;deg[b]+=1
    two=[v for v in range(k) if deg[v]==2];s={tuple(sorted(e)) for e in ed}
    rnd.shuffle(two)
    for a,b in itertools.combinations(two,2):
        if tuple(sorted((a,b))) not in s: return (k,E+1,tuple(ed)+((a,b),))
    return None
def family(k,n=2500):
    if k in census: return census[k]
    out=[];base=census[14]
    for _ in range(n):
        q=rnd.choice(base)
        while q[0]<k: q=subdivide(q)
        for _ in range(rnd.randrange(0,8)):
            c=chord(q)
            if c is None: break
            q=c
        out.append(q)
    return out
def solve(k):
    reps={}
    for q in family(k):
        I=inv(q);key=(q[1],)+tuple(sorted(I.items()))
        reps.setdefault(key,(q,I))
    reps=list(reps.values());Es=sorted({r[0][1] for r in reps})
    # one variable per representative, restrict to low edge counts first
    for span in (8,10,14,20,40):
        use=[r for r in reps if r[0][1]<=k+span]
        n=len(use);rows=[];rhs=[]
        Eset=sorted({r[0][1] for r in use})
        for E in Eset:
            rows.append([1 if r[0][1]==E else 0 for r in use]);rhs.append(0)
        ppcols=[pp_of(r[1],r[0][1]) for r in use]
        for o in range(-20,0):
            row=[p.get(o,0) for p in ppcols]
            if any(row): rows.append(row);rhs.append(0)
        ucoef=[{}]*n
        ser=[]
        for r in use:
            E=r[0][1];P=sp.Poly(sp.expand((u-1)**(E+1)),u);ser.append([r[1]["A"]*P.coeff_monomial(u**j) for j in range(4)])
        for j in range(3): rows.append([s[j] for s in ser]);rhs.append(0)
        rows.append([s[3] for s in ser]);rhs.append(1)
        M=fmpq_mat(len(rows),n+1,[fmpq(int(sp.Rational(x).p),int(sp.Rational(x).q)) for row,b in zip(rows,rhs) for x in list(row)+[b]])
        R,rk=M.rref();piv=[];ri=0
        for c in range(n+1):
            if ri<rk and R[ri,c]!=0: piv.append(c);ri+=1
        if n in piv: continue
        sol=[fmpq(0)]*n
        for i,c in enumerate(piv): sol[c]=R[i,n]
        s={i:sp.Rational(int(v.p),int(v.q)) for i,v in enumerate(sol) if v!=0}
        res=[{"pattern":use[i][0][2],"k":use[i][0][0],"E":use[i][0][1],"coef":str(c),"inv":use[i][1]} for i,c in s.items()]
        return {"k":k,"V":k+4,"representatives":n,"support":len(res),"edge_counts":sorted({r["E"] for r in res}),"witness":res}
    return {"k":k,"V":k+4,"infeasible":True,"representatives":len(reps)}
out={}
for k in range(11,18):
    r=solve(k);out[k]=r;print(k,{a:b for a,b in r.items() if a!='witness'},flush=True)
json.dump(out,open(sys.argv[1],'w'),indent=1)
