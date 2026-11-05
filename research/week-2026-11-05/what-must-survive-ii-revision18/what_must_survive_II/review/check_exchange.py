"""Exact finite-height verification of the two-terminal identity and Gram inequality."""
from fractions import Fraction as F
from itertools import product
from functools import lru_cache
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
x,q=F(2,7),F(3,11)
leaf=();chain=(leaf,)

def check(mid,U,V,C,D,height):
    @lru_cache(None)
    def G(f,a):
        val=F(1)
        for t in f:val*=sum(x**b*q**((a-b)**2)*G(t,b) for b in range(height+1))
        return val
    def K(a,b):
        state={a:x**a*G(mid[0],a)}
        for i in range(1,len(mid)):
            state={h:sum(w*q**((h-k)**2) for k,w in state.items())*x**h*G(mid[i],h) for h in ([b] if i==len(mid)-1 else range(height+1))}
        return state[b]
    def graph(L,R):
        edges=[(i,i+1) for i in range(len(mid)-1)];n=len(mid)
        def att(f,parent):
            nonlocal n
            for t in f:
                v=n;n+=1;edges.append((parent,v));att(t,v)
        for i,f in enumerate(mid):att(f,i)
        att(L,0);att(R,len(mid)-1);return n,edges
    def brute(L,R):
        n,E=graph(L,R)
        return sum(x**sum(h)*q**sum((h[a]-h[b])**2 for a,b in E) for h in product(range(height+1),repeat=n))
    wedge=lambda A,B,a,b:G(A,a)*G(B,b)-G(A,b)*G(B,a)
    delta=brute(U+C,V+D)-brute(U+D,V+C)
    bil=F(0);n1=F(0);n2=F(0)
    for a in range(height+1):
      for b in range(height+1):
        w=K(a,b)/2;A=wedge(U,V,a,b);B=wedge(C,D,a,b)
        bil+=w*A*B;n1+=w*A*A;n2+=w*B*B
    assert delta==bil and delta*delta<=n1*n2
    return {'height_cap':height,'middle_vertices':len(mid),'vertices':graph(U+C,V+D)[0],'identity':True,'gram_cauchy_bound':True,'difference_sign':(delta>0)-(delta<0),'difference_exact':str(delta)}

if __name__=='__main__':
    rows=[check(((),()),(leaf,),(chain,),(leaf,),(chain,),2),check(((),()),(leaf,),(chain,),(chain,),(leaf,),2),check(((),(leaf,),()),(leaf,),(chain,),(leaf,leaf),(chain,),1)]
    assert rows[0]['difference_sign']==1 and rows[1]['difference_sign']==-1
    (ROOT/'exchange_checks.json').write_text(json.dumps({'x':str(x),'q':str(q),'cases':rows,'scope':'finite-height restrictions checked exactly; general identity follows by symmetrization, not by these finite tests'},indent=2)+'\n')
    print('Two-terminal identity passed; generic mixed exchanges attain both signs.')
