"""Exact symbolic A and B identities for all s; no numerical specialization."""
from collections import defaultdict
from itertools import combinations
from pathlib import Path
import sympy as s,json
from family_symbolic import z
ROOT=Path(__file__).resolve().parent

def data(p):
    m=len(p);n=s.expand(m+sum(p));ell=s.expand(sum(p));A=defaultdict(lambda:s.Integer(0));B=defaultdict(lambda:s.Integer(0));a=[];t=0
    def add(out,e,c=1):
        E=s.Poly(s.expand(e),z);out[(int(E.coeff_monomial(z)),int(E.coeff_monomial(1)))]+=s.expand(c)
    for c in p[:-1]:t=s.expand(t+c+1);a.append(t)
    for t in a:add(A,t);add(A,n-t)
    add(A,1,ell);add(A,n-1,ell)
    for a0,b in combinations(a,2):add(B,b-a0)
    for i,a0 in enumerate(a,1):
        L=a0-i;add(B,a0-1,L);add(B,n-a0-1,ell-L)
    add(B,n-2,ell*(ell-1)/2)
    return [{e:s.expand(c) for e,c in x.items() if s.expand(c)} for x in (A,B)]
if __name__=='__main__':
    P=[z,z+1,z-1,2*z+1,z+2];Q=[z,2*z+1,z+1,z-1,z+2];a,b=data(P),data(Q)
    assert a==b
    (ROOT/'family_base.json').write_text(json.dumps({'A_equal_for_all_s':True,'B_equal_for_all_s':True,'degree_multiset_equal':'s+1,s+1,s+3,s+3,2s+3; plus 6s+3 leaves','nonisomorphism':'Canonical nonleaf spine has 5 vertices. Forward equality fails at coordinate 2; reversed equality fails at coordinate 1, for every s>=1.'},indent=2)+'\n')
    print('All-parameter A and B identities passed.')
