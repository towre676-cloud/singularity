from quartic_exact import FourthJet,F
from pathlib import Path
import json,time
root=Path(__file__).parent
pats=[]
for l in (root/'rows14_p1.txt.pats').read_text().splitlines():
 w=list(map(int,l.split()));pats.append((w[0],w[1],tuple((w[3+2*i],w[4+2*i]) for i in range(w[1]))))
w15=json.load(open(root/'input/witness15_V14.json'))
ids=[i for i,p in enumerate(pats) if p[0]<=6]+list(map(int,w15['coeffs']))
ids=sorted(set(ids));vals={}
q=F(3,2);t0=time.time();E=FourthJet(q)
for z,i in enumerate(ids):
 k,m,ed=pats[i];vals[i]=E.bjet(k,ed)
 print('evaluated',z+1,'/',len(ids),'pattern',i,'k',k,'seconds',round(time.time()-t0,1),flush=True)
# Compare full exact rows at a rational q, with no modular reconstruction in this verifier.
bad=[];checks=0
# streaming again with accumulation
actual={(i,j):F(0) for i in vals for j in range(5) if pats[i][0]+j<=14}
for l in (root/'rows14_exact.txt').read_text().splitlines():
 w=l.split();V,e,nz=int(w[0]),int(w[1]),int(w[2]);qe=q**e
 for j in range(nz):
  i=int(w[3+3*j])-1
  key=i,V-pats[i][0] if i>=0 else -999
  if key in actual:actual[key]+=F(int(w[4+3*j]),int(w[5+3*j]))*qe
for (i,j),v in actual.items():
 checks+=1
 if vals[i][j]!=v:bad.append((i,j))
res={'q':str(q),'patterns':len(vals),'jet_coefficients':checks,'failures':bad,'seconds':round(time.time()-t0,2),'includes_height_5':True,'includes_repeated_pair_and_triple_polymers':True}
json.dump(res,open(root/'quartic_verification.json','w'),indent=2);print(res)
assert not bad
