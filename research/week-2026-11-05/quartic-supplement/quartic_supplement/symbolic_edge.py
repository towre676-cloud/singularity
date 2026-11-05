from pathlib import Path
src=(Path(__file__).parent/'quartic_exact.py').read_text().replace('self.q=F(q);q=self.q;H=6;M=6','self.q=q;q=self.q;H=6;M=6')
ns={};exec(compile(src,'quartic_symbolic','exec'),ns)
from sympy.polys.fields import field
from sympy.polys.domains import QQ
import sympy as sp,time,json
K,q=field('q',QQ);t0=time.time();E=ns['FourthJet'](q);print('series ready',time.time()-t0,flush=True)
def conn(a,b):return E.local((a,b),((0,1),))
gam=conn(2,2)[4]-2*conn(2,3)[4]+conn(3,3)[4]
# Original edge connected cumulant; its leading normalized pole is the promoted pair source.
r=sp.factor(gam.as_expr());print('gamma4',r,flush=True)
nu,de=sp.fraction(sp.cancel(r/sp.Symbol('q')**12));deg=sp.degree(nu)-sp.degree(de)
res={'gamma4':str(r),'normalized_t_pole':str(deg/2),'seconds':time.time()-t0};json.dump(res,open(Path(__file__).parent/'symbolic_edge.json','w'),indent=2)
