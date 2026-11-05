"""Independent checks of Theorems 34/35 against the recovered spine formula and direct shells."""
from pathlib import Path
import sys,json,random
from collections import Counter,defaultdict
from fractions import Fraction
ROOT=Path(__file__).resolve().parent;PKG=ROOT.parent
sys.path.insert(0,str(PKG/'supplements/caterpillar_proof_advance'))
from caterpillar import positions,data,h3,build
from exact_tree import full_shells
from verify import sequences

def polykey(C):return tuple(sorted((a,b) for a,b in C.items() if b))
def delta(a,b):return {k:a[k]-b[k] for k in a.keys()|b.keys() if a[k]!=b[k]}
def mul(a,b):
    c=Counter()
    for i,u in a.items():
        for j,v in b.items():c[i+j]+=u*v
    return c

def plus(c,d,k=1):
    for a,b in d.items():c[a]+=k*b

def g(p):return Counter({-p:1,0:-1})
def h(p,N):
    c=Counter({p:1});c[N-p]-=1;return c
def sym(p,N):
    c=Counter({p:1});c[N-p]+=1;return c
def predict(T,U,N):
    sig=lambda T:{min(t,N-t):(1 if 2*t<N else -1) for t in T if 2*t!=N and N-t not in T}
    sa,sb=sig(T),sig(U);F=[min(t,N-t) for t in T];out=Counter();sites=sorted(sa)
    for i,p in enumerate(sites):
      nu=sum(r<p for r in F);lam=Counter({0:1,N-2*p:-1});plus(lam,h(p,N),-(2*p+1-nu))
      for r in F:
        if r<p:
            plus(lam,h(r,N),-1);lam[r-p]+=1;lam[p-r]-=1
            for e,c in g(p).items():lam[e-2]+=c
            for e,c in g(r).items():lam[e-2]-=c
      for q in sites[i+1:]:
        tau=sa[p]*sa[q]-sb[p]*sb[q]
        if not tau:continue
        pi=Counter()
        for r in F:
            if r>q:
                for e,c in sym(q,N).items():pi[e-2]+=c
                for e,c in sym(r,N).items():pi[e-2]-=c
        plus(pi,mul(sym(q,N),h(q,N)),-1)
        plus(out,mul(h(q,N),lam),tau);plus(out,mul(g(p),pi),tau)
    return {e:c for e,c in out.items() if c}

def cutset(p):return {a-1 for a in positions(p)[2]}
def p_of(T,N):
    a=[0]+sorted(T)+[N];c=[v-u for u,v in zip(a,a[1:])]
    return tuple([c[0]]+[z-1 for z in c[1:-1]]+[c[-1]])
def check(p,q,direct=False):
    n=positions(p)[0];N=n-2;T,U=cutset(p),cutset(q)
    A,B,*_=data(p);AA,BB,*_=data(q);assert A==AA and B==BB
    ka,_=h3(p);kb,_=h3(q);kd=delta(ka,kb);assert kd
    pr=predict(T,U,N);actual={e-1:4*c for e,c in kd.items()};assert pr==actual
    spin=lambda T:{min(t,N-t):(1 if 2*t<N else -1) for t in T if 2*t!=N and N-t not in T}
    sa,sb=spin(T),spin(U);r1=min(sa)
    if sb[r1]!=sa[r1]:sb={r:-z for r,z in sb.items()}
    qs=min(r for r in sa if sa[r]!=sb[r]);nu=sum(min(t,N-t)<r1 for t in T)
    degree=3*n-3-qs-r1;coefficient=Fraction(sa[r1]*sa[qs]*(2*r1-nu),2)
    topk=max(kd);assert topk+n==degree and -kd[topk]==coefficient
    if direct:
        a,b=full_shells(build(p),3),full_shells(build(q),3)
        assert a[1]==b[1] and a[2]==b[2]
        sdelta=delta(a[3],b[3]);pred=Counter(kd)
        for e,c in kd.items():pred[e+n]-=c
        assert sdelta=={e:c for e,c in pred.items() if c}
        assert max(sdelta)==degree and sdelta[degree]==coefficient
    return {'n':n,'r1':r1,'qstar':qs,'nu':nu,'top_degree':degree,'top_coefficient':int(coefficient),'direct':direct}

def main():
    count=0;rows=[];byorder={}
    for n in range(4,19):
        groups=defaultdict(list);k=0
        for p in sequences(n):
            A,B,*_=data(p);groups[(polykey(A),polykey(B))].append(p);count+=1;k+=1
        for group in groups.values():
            for p in group[1:]:rows.append(check(group[0],p,True))
        byorder[n]=k;print('caterpillars',n,k,'pairs checked',len(rows),flush=True)
    rnd=random.Random(20261105);aug=[]
    for s in range(1,5):
      p=(s,s+1,s-1,2*s+1,s+2);q=(s,2*s+1,s+1,s-1,s+2);N=6*s+6
      T,U=cutset(p),cutset(q);available=[r for r in range(1,(N+1)//2) if r not in T and N-r not in T]
      for _ in range(12):
        neutral=set()
        for r in available:
            if rnd.randrange(2):neutral|={r,N-r}
        if N%2==0 and N//2 not in T and rnd.randrange(2):neutral.add(N//2)
        aug.append(check(p_of(T|neutral,N),p_of(U|neutral,N)))
    out={'nonstar_caterpillars_checked':count,'counts_by_order':byorder,'all_collision_pairs_direct':rows,'augmented_neutral_tests':aug,'scope':'exact counters, no hashes; no claim of a new general proof by enumeration'}
    (ROOT/'caterpillar_checks.json').write_text(json.dumps(out,indent=2)+'\n');print('Theorems 34/35 checks passed.',flush=True)
if __name__=='__main__':main()
