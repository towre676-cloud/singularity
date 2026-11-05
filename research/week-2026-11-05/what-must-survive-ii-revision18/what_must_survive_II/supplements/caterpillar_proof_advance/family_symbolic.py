"""Exact all-parameter H3 for Revision 9's shell-two collision family."""
from collections import defaultdict
from itertools import combinations
from pathlib import Path
import sympy as s,json
ROOT=Path(__file__).resolve().parent
z=s.Symbol('s',integer=True,positive=True)

def symbolic_h3(p):
    m=len(p);ell=s.expand(sum(p));n=s.expand(m+ell);a=[];u=s.Integer(0)
    for w in p[:-1]:u=s.expand(u+1+w);a.append(u)
    out=defaultdict(lambda:s.Integer(0));parts=[defaultdict(lambda:s.Integer(0)) for _ in range(4)]
    def add(r,e,c=1):
        e=s.Poly(s.expand(e),z);key=(int(e.coeff_monomial(z)),int(e.coeff_monomial(1)))
        parts[r][key]+=s.expand(c)
    C2=lambda a:s.expand(a*(a-1)/2)
    C3=lambda a:s.expand(a*(a-1)*(a-2)/6)
    for u,v,w in combinations(a,3):
        for e in (u-v+w,n-u+v-w,-u+v+w,n-u-v+w):add(0,e)
    for (i,u),(j,v) in combinations(enumerate(a,1),2):
        d=v-u;M=d-(j-i);Lj=v-j;Ri=ell-u+i
        for e,c in [(d+1,ell),(n+d-1,ell),(n-d-1,ell-M),(d-1,M),(u+v-1,Lj),(2*n-u-v-1,Ri)]:add(1,e,c)
    for i,u in enumerate(a,1):
        L=u-i;R=ell-L
        for e,c in [(u-2,C2(L)),(n-u-2,C2(R)),(u,(ell-1)*L),(n-u,(ell-1)*R),(n+u-2,C2(ell)),(2*n-u-2,C2(ell))]:add(2,e,c)
    for e,c in [(n-3,1),(2*n-3,1),(n-1,3)]:add(3,e,c*C3(ell))
    for d in parts:
        for e,c in d.items():out[e]+=c
    return {e:s.factor(c) for e,c in out.items() if s.expand(c)},parts

def main():
    P=[z,z+1,z-1,2*z+1,z+2];Q=[z,2*z+1,z+1,z-1,z+2]
    a,_=symbolic_h3(P);b,_=symbolic_h3(Q);d={e:s.factor(a.get(e,0)-b.get(e,0)) for e in a.keys()|b.keys() if s.expand(a.get(e,0)-b.get(e,0))}
    # For a finite set of affine exponent functions, all coincidences are explicit.
    bad=set()
    for (aa,bb),(cc,dd) in combinations(d,2):
        if aa!=cc:
            v=s.Rational(dd-bb,aa-cc)
            if v.q==1 and v>=1:bad.add(int(v))
    print('Terms',len(d),'collision parameters',sorted(bad),flush=True)
    top=max(d);print('lexicographic top',top,'coefficient',d[top],flush=True)
    cutoff=max(bad,default=0)+1
    leading=max(d,key=lambda e:e[0]*cutoff+e[1]);print('top beyond collision cutoff',cutoff,leading,d[leading],flush=True)
    special={}
    for v in range(1,cutoff):
        poly=defaultdict(lambda:s.Integer(0))
        for (aa,bb),c in d.items():poly[aa*v+bb]+=c.subs(z,v)
        pp={e:int(c) for e,c in poly.items() if c};assert pp
        special[v]={'lowest_exponent':min(pp),'lowest_coefficient':pp[min(pp)],'highest_exponent':max(pp),'highest_coefficient':pp[max(pp)]}
    out={'variable':'s, a positive integer','delta_h3':[{'exponent_s':a,'exponent_constant':b,'coefficient':str(c)} for (a,b),c in sorted(d.items())],'exponent_collision_parameters':sorted(bad),'tail_cutoff':cutoff,'tail_extreme_exponent':leading,'tail_extreme_coefficient':str(d[leading]),'special_checks':special}
    (ROOT/'family_symbolic.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
