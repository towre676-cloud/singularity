# Pairs Q,Q' with identical jets J_0..J_{j-1} and different J_j give explicit elements of W(k+j,j). Report pole orders and factorizations.
import sys,json,sympy as sp
from analyze import load,pats
from collections import defaultdict
fn=sys.argv[1];rows=load(fn);Q=pats(fn+'.pats');VM=max(r[0] for r in rows)
col=defaultdict(lambda:defaultdict(dict))
for v,e,d in rows:
    for c,x in d.items(): col[c][v][e]=x
q=sp.Symbol('q');out={}
def jet(c,k,j): return col[c+1].get(k+j,{})
for j in range(2,7):
    best={};stats={}
    for k in range(3,VM-j+1):
        groups=defaultdict(list)
        for c,qq in enumerate(Q):
            if qq[0]==k:
                key=tuple(tuple(sorted(jet(c,k,i).items())) for i in range(j))
                groups[key].append(c)
        V=k+j;mx=None;cnt=0;arg=None;poles=defaultdict(int)
        for g in groups.values():
            if len(g)<2: continue
            base=g[0]
            for o in g[1:]:
                A,B=jet(base,k,j),jet(o,k,j);d={e:A.get(e,0)-B.get(e,0) for e in set(A)|set(B)};d={e:x for e,x in d.items() if x}
                if not d: continue
                cnt+=1;p=(max(d)-3*V)//2;poles[p]+=1
                if mx is None or p>mx: mx=p;arg=(base,o,d)
        if mx is not None:
            poly=sp.factor(sum(sp.Rational(x.numerator,x.denominator)*q**e for e,x in arg[2].items()))
            stats[V]={"k":k,"pairs":cnt,"max_pole":mx,"poles":dict(sorted(poles.items())),"witness":[Q[arg[0]][3],Q[arg[1]][3]],"E":Q[arg[0]][1],"poly":str(poly)}
            print(j,V,k,"pairs",cnt,"maxpole",mx,dict(sorted(poles.items())),"E",Q[arg[0]][1],flush=True)
            print("   ",str(poly)[:170],flush=True);print("   ",Q[arg[0]][3],"|",Q[arg[1]][3],flush=True)
    out[j]=stats
json.dump(out,open(sys.argv[2],'w'),indent=1)
