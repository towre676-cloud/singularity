from pathlib import Path
import json,math
from collections import Counter
import sympy as s
from caterpillar import build,positions,data,h3,predicted_shell3
from exact_tree import full_shells,diff
from family_symbolic import symbolic_h3,z
ROOT=Path(__file__).resolve().parent

def sequences(n):
    def compositions(left,p):
        if left==0:
            if len(p)>=2 and p[0]>=1 and p[-1]>=1 and p<=p[::-1]:yield p
            return
        for c in range(left):yield from compositions(left-c-1,p+(c,))
    yield from compositions(n,())

def main():
    count=0;counts={}
    for n in range(4,13):
        k=0
        for p in sequences(n):
            T=build(p);S=full_shells(T,3);assert S[3]==predicted_shell3(p)
            A,B,C,D=data(p);assert A==S[1]
            # Check Theorem 25 directly using polynomial convolution.
            pred=Counter()
            for a,ca in A.items():
             for b,cb in A.items():pred[a+b]+=ca*cb
            for a,ca in A.items():pred[2*a]-=ca
            assert all(c%2==0 for c in pred.values())
            pred=Counter({e:c//2 for e,c in pred.items()});pred[n]-=n-1
            for e,c in B.items():pred[e]+=c;pred[e+n]-=c
            assert all(pred[e]==S[2][e] for e in pred.keys()|S[2].keys())
            # Pendant symmetrization and rank-weighted identity.
            _,ell,a=positions(p);m=len(p);x=s.Symbol('x');pol=lambda c:sum(v*x**e for e,v in c.items())
            Sp=sum(x**u+x**(n-u) for u in a);R=sum(i*x**u+(m-i)*x**(n-u) for i,u in enumerate(a,1))
            assert s.expand(pol(C)-s.diff(Sp,x)+R/x)==0
            lhs=pol(C)+sum(c*x**(n-2-e) for e,c in C.items())
            assert s.expand(lhs-ell*Sp/x)==0
            count+=1;k+=1
        counts[n]=k;print(n,k,flush=True)
    family=[]
    P=[z,z+1,z-1,2*z+1,z+2];Q=[z,2*z+1,z+1,z-1,z+2]
    hp,_=symbolic_h3(P);hq,_=symbolic_h3(Q)
    for v in (1,2,3,4,5):
        pp=[int(a.subs(z,v)) for a in P];qq=[int(a.subs(z,v)) for a in Q]
        a,b=build(pp),build(qq);sa,sb=full_shells(a,3),full_shells(b,3)
        assert sa[1]==sb[1] and sa[2]==sb[2] and sa[3]!=sb[3]
        for seq,H in [(pp,hp),(qq,hq)]:
            numeric=Counter()
            for (aa,bb),c in H.items():numeric[aa*v+bb]+=int(c.subs(z,v))
            assert +numeric==+h3(seq)[0]
        family.append({'s':v,'n':len(a),'first_separating_energy':3,'delta_shell3':diff(sa[3],sb[3])})
        print('Family',v,'passed',flush=True)
    (ROOT/'exact_checks.json').write_text(json.dumps({'all_caterpillars_checked':count,'counts_by_order':counts,'max_order':12,'max_energy':3,'family':family},indent=2)+'\n')
if __name__=='__main__':main()
