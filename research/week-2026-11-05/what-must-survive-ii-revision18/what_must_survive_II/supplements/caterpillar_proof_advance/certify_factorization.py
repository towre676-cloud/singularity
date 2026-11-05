"""Check the displayed factorization against independently expanded transfer receipts."""
from pathlib import Path
import sympy as s,json
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    u,v,q=s.symbols('u v q');inp=json.loads((ROOT/'two_parameter_volume.json').read_text())
    raw=sum(s.sympify(t['coefficient'])*u**t['a']*v**t['b']*q**t['constant'] for t in inp['4'])
    F=q**4*u**2*v**2+q**4*u*v**2+q**4*v**2+q**3*u**2*v+q**3*u*v+q**3*v+q**2*u**2+q**2*u-q**2*v**2+q**2-q*u*v-u**2
    displayed=u*v/q*(q*q-1)**2*(q*q+1)*(u-1)*(q*v-1)*(q*v-u)*F
    assert s.cancel(raw-displayed)==0
    assert all(not inp[str(V)] for V in (1,2,3))
    old=json.loads((ROOT/'low_volume_symbolic.json').read_text())
    original=sum(s.sympify(t['coefficient'])*u**t['energy_s']*q**t['energy_constant'] for t in old['4'])
    assert s.expand(raw.subs(v,q*u)-original)==0
    (ROOT/'factorization_certificate.json').write_text(json.dumps({'displayed_factorization_equals_transfer_expansion':True,'original_one_parameter_specialization_agrees':True,'volumes_1_2_3_identically_equal':True},indent=2)+'\n')
    print('Displayed factorization and one-parameter specialization passed exactly.')
