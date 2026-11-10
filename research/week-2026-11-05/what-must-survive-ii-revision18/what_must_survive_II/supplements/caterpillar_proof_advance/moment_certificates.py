"""Exact symbolic certificates for the four-spine proof."""
from pathlib import Path
from itertools import combinations
import sympy as s,json
from four_spine_moments import moment,candidates,n,a,b,c
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    expected={(0,1):2*(n-2*c)*(a+b-2),(0,2):2*((a-2)*(n-2*b)+b*(n-2*c)+2*(c-b)),(0,3):4*(a-1)*(n-b-c),(1,2):4*(a-1)*(c-b),(2,3):-2*(b-a)*(n-2*c)}
    for (i,j),f in expected.items():assert s.expand(moment(candidates[i],2)-moment(candidates[j],2)-f)==0
    d2=moment(candidates[1],2)-moment(candidates[3],2);d3=moment(candidates[1],3)-moment(candidates[3],3)
    assert s.expand(d3-s.Rational(3,2)*(n-a-b)*d2+6*(a-1)*(b-1)*(b-c))==0
    (ROOT/'moment_certificates.json').write_text(json.dumps({'exact_polynomial_identities':True,'mu2_differences':{str(k):str(v) for k,v in expected.items()},'critical_relation':'delta3 = 3/2*(n-a-b)*delta2 - 6*(a-1)*(b-1)*(b-c)'},indent=2)+'\n')
    print('All symbolic short-spine moment identities passed.')
