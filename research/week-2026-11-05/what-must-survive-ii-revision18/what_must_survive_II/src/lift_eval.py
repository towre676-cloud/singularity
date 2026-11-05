# Lift check from raw evaluations. build: write index list. check: solve y's, test all lower rows, interpolate the top row.
import sys,json
from fractions import Fraction as Fr
from analyze import pats
from flint import nmod_mat
P=2**61-1
mode,k=sys.argv[1],int(sys.argv[2]);V=k+4;L=json.load(open('/root/wms/receipts/lift_small.json'))[str(k)]
PF=sys.argv[3]
lines=[list(map(int,l.split())) for l in open(PF)]
pat=[(w[0],tuple(sorted(tuple(sorted((w[2+2*i],w[3+2*i]))) for i in range(w[1])))) for w in lines]
key={p:i for i,p in reversed(list(enumerate(pat)))}
sup={key[(x["k"],tuple(sorted(tuple(sorted(e)) for e in x["pattern"])))]:Fr(x["coef"]) for x in L["witness"]}
rep={K:{} for K in (k+2,k+3)}
for i,w in enumerate(lines):
    if w[0] in rep: rep[w[0]].setdefault(w[1],i)
if mode=="build":
    with open(sys.argv[4],'w') as o: o.write(" ".join(map(str,sorted(set(sup)|{i for K in rep for i in rep[K].values()}))))
    print(len(sup),{K:len(v) for K,v in rep.items()});sys.exit()
vals={};qs={}
for l in open(sys.argv[4]):
    w=list(map(int,l.split()));vals[(w[0],w[2])]=w[3:];qs[w[0]]=w[1]
W=sorted(qs);z={i:c.numerator*pow(c.denominator,-1,P)%P for i,c in sup.items()}
def row(zz,v,w_): return sum(c*vals[(w_,i)][v] for i,c in zz.items())%P
bad=sum(1 for w_ in W for v in range(k+2) if row(z,v,w_))
def solve(K,zz):
    Es=sorted(rep[K]);m=len(Es);A=[[vals[(w_,rep[K][E])][K] for E in Es]+[(-row(zz,K,w_))%P] for w_ in W]
    M=nmod_mat(len(W),m+1,[x for r in A for x in r],P);R,rk=M.rref()
    piv=[next(c for c in range(m+1) if int(R[i,c])) for i in range(rk)]
    assert m not in piv,"row K not solvable by top patterns"
    out=dict(zz)
    for i,c in enumerate(piv):
        y=int(R[i,m])
        if y: out[rep[K][Es[c]]]=(out.get(rep[K][Es[c]],0)+y)%P
    return out
z2=solve(k+2,z);z3=solve(k+3,z2)
badall=sum(1 for w_ in W for v in range(V) if row(z3,v,w_))
# top row: P=q^e0 (t-1)^V U(t), degree U = (3V+30-e0)/2 - V
e0=V%2;D=(3*V+30-e0)//2-V;n=D+1
A=[]
for w_ in W:
    q=qs[w_];t=q*q%P;sc=pow(q,e0,P)*pow((t-1)%P,V,P)%P;c=1;r=[]
    for j in range(n): r.append(sc*c%P);c=c*t%P
    A.append(r+[row(z3,V,w_)])
M=nmod_mat(len(W),n+1,[x for r in A for x in r],P);R,rk=M.rref()
piv=[next(c for c in range(n+1) if int(R[i,c])) for i in range(rk)]
consistent=n not in piv;top=None
if consistent:
    top=int(R[piv.index(n-1),n]) if n-1 in piv else 0
    top=top if top<P//2 else top-P
res={"k":k,"V":V,"points":len(W),"support":len(sup),"lower_rows_nonzero_before_y":bad,"all_rows_below_V_nonzero":badall,"degree_model_unknowns":n,"slack_points":len(W)-n,"degree_model_consistent":consistent,"coefficient_at_energy":3*V+30,"top_coefficient":top,"predicted":2}
print(res);json.dump(res,open(sys.argv[5],'w'),indent=1)
