from pathlib import Path
from fractions import Fraction as F
from math import lcm,gcd
import json
r=Path(__file__).parent
w=json.load(open(r/'input/witness17_V13.json'));ids=sorted(map(int,w['coeffs']));coeff=[int(w['coeffs'][str(i)]) for i in ids]
prior=set();target=None;original_rows=0
for line in (r/'rows14_exact.txt').read_text().splitlines():
 s=line.split();v,e,nz=map(int,s[:3])
 if v>13:continue
 row={int(s[3+3*j])-1:F(int(s[4+3*j]),int(s[5+3*j])) for j in range(nz)}
 a=[row.get(i,F(0)) for i in ids];L=1
 for x in a:L=lcm(L,x.denominator)
 z=[int(x*L) for x in a]
 if v<13:
  original_rows+=1;g=0
  for x in z:g=gcd(g,abs(x))
  if g:
   z=[x//g for x in z]
   if next(x for x in z if x)!=abs(next(x for x in z if x)):z=[-x for x in z]
   prior.add(tuple(z))
 elif e==73:target=z
assert target is not None
p=lambda a:'['+', '.join(str(x) if x>=0 else '('+str(x)+')' for x in a)+']'
code='''import CertificateKernel
set_option maxRecDepth 1000000
set_option maxHeartbeats 0
namespace HeightWitness17
open HeightCertificates
'''
code+='def coefficients : List Int := '+p(coeff)+'\n'
code+='def earlier : List (List Int) := [\n'+',\n'.join(p(x) for x in sorted(prior))+']\n'
code+='def target : List Int := '+p(target)+'\n'
code+='''theorem shapes : earlier.all (fun r => r.length == coefficients.length) = true ∧ target.length = coefficients.length := by decide
 theorem certificateAccepted : accepted earlier target coefficients = true := by decide
 theorem earlierRowsVanish : ∀ r ∈ earlier, dot r coefficients = 0 :=
   (accepted_sound earlier target coefficients certificateAccepted).1
 theorem targetSurvives : dot target coefficients ≠ 0 :=
   (accepted_sound earlier target coefficients certificateAccepted).2
end HeightWitness17
#print axioms HeightWitness17.certificateAccepted
#print axioms HeightWitness17.earlierRowsVanish
#print axioms HeightWitness17.targetSurvives
'''
(r/'Witness17.lean').write_text(code)
(r/'lean_witness_input.json').write_text(json.dumps({'variables':len(ids),'original_earlier_rows':original_rows,'nonzero_distinct_primitive_rows':len(prior),'normalization':'each earlier row multiplied to primitive integral form; zero and duplicate rows removed','source_target_energy':73,'original_unscaled_dot':-56},indent=2))
print(len(prior),'rows',len(code),'bytes')
