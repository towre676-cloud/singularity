from pathlib import Path
src=(Path(__file__).parent/'quartic_exact.py').read_text().replace('self.q=F(q);q=self.q;H=6;M=6','self.q=q;q=self.q;H=6;M=6')
ns={};exec(compile(src,'quartic_symbolic','exec'),ns)
from sympy.polys.fields import field
from sympy.polys.domains import QQ
import json
K,q=field('q',QQ);E=ns['FourthJet'](q)
def pole(c,j):
 if not c:return None
 return (c.numer.degree()-c.denom.degree()-3*j)/2
G={ab:E.local(ab,((0,1),)) for ab in ((2,2),(2,3),(3,3))}
S={d:E.local((d,),()) for d in (2,3)}
LP=ns['log'](E.pi);LF=ns['log'](E.phi)
# B_j(k,E)=k*a_j + E*b_j, after eliminating n2,n3,e23,e33.
a=[];b=[];gamma=[]
for j in range(5):
 a.append(LP[j]+3*S[2][j]-2*S[3][j]+6*G[2,3][j]-6*G[3,3][j])
 b.append(LF[j]-2*S[2][j]+2*S[3][j]-4*G[2,3][j]+5*G[3,3][j])
 gamma.append(G[2,2][j]-2*G[2,3][j]+G[3,3][j])
res={'base_a_poles':[pole(a[j],j) for j in range(5)],'base_b_poles':[pole(b[j],j) for j in range(5)],'gamma_poles':[pole(gamma[j],j) for j in range(5)],'gamma':[str(z) for z in gamma]}
assert max(pole(a[1],1),pole(b[1],1))<=3
assert max(pole(a[2],2),pole(b[2],2))<=9
assert pole(gamma[2],2)<=3 and pole(gamma[3],3)<=9 and pole(gamma[4],4)==18
print(res)
json.dump(res,open(Path(__file__).parent/'carry_bounds.json','w'),indent=2)
