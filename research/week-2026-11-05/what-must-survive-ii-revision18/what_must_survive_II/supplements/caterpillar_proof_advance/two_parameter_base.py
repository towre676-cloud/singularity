from collections import defaultdict
from itertools import combinations
from pathlib import Path
import sympy as s,json
A,B=s.symbols('a b',integer=True);ROOT=Path(__file__).resolve().parent

def data(p):
    m=len(p);ell=s.expand(sum(p));n=ell+m;pos=[];v=0;out=[defaultdict(lambda:s.Integer(0)) for _ in range(2)]
    def add(j,e,c=1):
        e=s.Poly(s.expand(e),A,B);key=tuple(int(e.coeff_monomial(t)) for t in (A,B,1));out[j][key]+=s.expand(c)
    for w in p[:-1]:v=s.expand(v+w+1);pos.append(v)
    add(0,1,ell);add(0,n-1,ell)
    for i,v in enumerate(pos,1):
        add(0,v);add(0,n-v);L=v-i;add(1,v-1,L);add(1,n-v-1,ell-L)
    for u,v in combinations(pos,2):add(1,v-u)
    add(1,n-2,ell*(ell-1)/2)
    return [{e:s.expand(c) for e,c in d.items() if s.expand(c)} for d in out]
if __name__=='__main__':
    p=[A,B,A-1,A+B,B+1];q=[A,A+B,B,A-1,B+1]
    assert data(p)==data(q)
    (ROOT/'two_parameter_base.json').write_text(json.dumps({'parameter_domain':'a>=1, b>=0 integers','n':'3a+3b+5','A_equal':True,'B_equal':True,'nonisomorphic_iff':'a != b+1','nonleaf_degrees':'a+1,b+2,a+1,a+b+2,b+2; same multiset in either graph'},indent=2)+'\n')
    print('Two-parameter A and B identities passed.')
