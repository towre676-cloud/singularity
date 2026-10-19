"""Recognize exact polynomial reductions and retain the original equation in proofs."""
import hashlib
import json
from math import isqrt
from .checked_box import _hash,_integer
from .checked_family import check_rebuilt
from .checked_family_population import family_population_certificate,SOURCES
from .checked_pell_orbits import pell_orbits_certificate,MODULES,AUDITS
from .checked_population import _compile_queries,_emit_queries,_tree
from .checked_nonlinear_population import _multiply
from .resources import runtime_root
from .divisor_square import WorkLimit


def _power(cs,e):
    out=[1]
    for _ in range(e):out=_multiply(out,cs)
    return out


def _integer_root(n,e):
    if n<0 and e%2==0:return None
    sign=-1 if n<0 else 1;n=abs(n)
    low=0;high=1 << ((n.bit_length()+e-1)//e)
    while low+1<high:
        mid=(low+high)//2
        if mid**e<=n:low=mid
        else:high=mid
    return sign*low if low**e==n else None


def power_plus_constant(cs,e):
    """Triangular coefficient extraction; exact expansion confirms the result."""
    degree=len(cs)-1
    if degree%e:return None
    n=degree//e;a=_integer_root(cs[-1],e)
    if not a:return None
    u=[0]*n+[a]
    denominator=e*a**(e-1)
    for j in range(n-1,-1,-1):
        index=(e-1)*n+j
        difference=cs[index]-_power(u,e)[index]
        if difference%denominator:return None
        u[j]=difference//denominator
    expanded=_power(u,e)
    if expanded[1:]!=cs[1:]:return None
    return u,cs[0]-expanded[0]


def automatic_population_certificate(coefficients,queries=None,*,cutoff=None,
                                      domain='integer',work_limit=4096,seed_budget=4096):
    if not isinstance(coefficients,list) or not 2<=len(coefficients)<=33:raise ValueError('2..33 ascending integer coefficients required')
    cs=[_integer(c,'coefficient') for c in coefficients]
    while len(cs)>1 and cs[-1]==0:cs.pop()
    if len(cs)<2:raise ValueError('nonconstant input polynomial required')
    if domain not in ('integer','nonnegative','positive'):raise ValueError('invalid input domain')
    if type(seed_budget) is not int or not 1<=seed_budget<=65536:raise ValueError('invalid seed_budget')
    if cutoff is not None:
        cutoff=_integer(cutoff,'cutoff')
        if cutoff<0:raise ValueError('nonnegative absolute input cutoff required')
    route=None;reduction=None;child=None
    for e in (2,3):
        match=power_plus_constant(cs,e)
        if match is None:continue
        u,k=match
        if e==2 and k:
            family='square_plus_constant'
        elif e==3:
            family=next((name for name,data in SOURCES.items() if -data[0]==k),None)
            if family is None and any(r['k']==k for r in json.loads((runtime_root()/'data/mordell_descent_sources.json').read_text())['rows']):family='mordell_descent'
            if family is None:continue
        else:continue
        child=family_population_certificate(u,[{}],family=family,offset=k,domain='integer',work_limit=work_limit)
        route='power_pullback';reduction=dict(exponent=e,inner_coefficients=u,offset=k,family=family)
        points=child['source_points'];break
    if route is None and len(cs)==3 and cs[2]>0:
        c,b,a=cs
        r=isqrt(a)
        if r*r==a:
            k=4*a*c-b*b
            if not k:raise ValueError('degenerate rational-square quadratic requires an infinite-family route')
            child=family_population_certificate([b,2*a],[{}],offset=k,work_limit=work_limit)
            route='scaled_square';reduction=dict(output_scale=2*r,inner_coefficients=[b,2*a],offset=k)
            points=[[x,z//(2*r)] for x,z in child['source_points'] if z%(2*r)==0]
        else:
            if cutoff is None:raise ValueError('infinite Pell-type quadratic requires an absolute input cutoff')
            cap=isqrt(a*cutoff**2+abs(b)*cutoff+abs(c))
            child=pell_orbits_certificate(4*a,b*b-4*a*c,cap,[{}],work_limit=work_limit,seed_budget=seed_budget)
            route='quadratic_norm';reduction=dict(D=4*a,norm=b*b-4*a*c,affine_scale=2*a,affine_shift=b,root_cutoff=cap)
            points=[[(z-b)//(2*a),y] for y,z in child['source_points'] if (z-b)%(2*a)==0]
    if route is None:raise ValueError('no supported complete reduction recognized; no bounded scan is silently substituted')
    points=sorted({tuple(p) for p in points if (cutoff is None or abs(p[0])<=cutoff) and
        (domain=='integer' or p[0]>=(0 if domain=='nonnegative' else 1))})
    points=[list(p) for p in points]
    normalized,plans=_compile_queries(points,[{}] if queries is None else queries)
    spec=dict(coefficients=cs,queries=normalized,cutoff=cutoff,domain=domain,work_limit=work_limit,seed_budget=seed_budget)
    name='PerfectPower.AutomaticPopulation_'+_hash(spec)[:16]
    condition=True if domain=='integer' else ['le',0 if domain=='nonnegative' else 1,'x']
    if cutoff is not None:condition=['and',condition,['and',['le',-cutoff,'x'],['le','x',cutoff]]]
    dc,_=_tree(condition,condition=True)
    literal='['+','.join(f'(({x}),({y}))' for x,y in points)+']'
    childns=child['namespace']
    lean='import PerfectPower.AutomaticReduction\n'+child['lean']+f'''namespace {name}
open PerfectPower.QueryNative PerfectPower.AutomaticReduction
def domainCondition := {dc}
def original (p : Int × Int) : Prop := p.2^2=PerfectPower.BoundedNative.horner {cs} p.1 ∧ domainCondition.holds p
'''
    if route=='power_pullback':
        lean+=f'''def computed := ({childns}.sourcePoints.toFinset).filter fun p => domainCondition.test p=true
theorem computed_complete (p : Int × Int) : p ∈ computed ↔ original p := by
  unfold computed
  rw [Finset.mem_filter,List.mem_toFinset,{childns}.source_complete,{childns}.expanded_original,test_correct]
  simp only [{childns}.domainCondition,Condition.holds,original,true_and,and_true]
'''
    elif route=='scaled_square':
        scale=2*r
        lean+=f'''def transformed := outputPullback {childns}.sourcePoints.toFinset ({scale})
def computed := transformed.filter fun p => domainCondition.test p=true
theorem computed_complete (p : Int × Int) : p ∈ computed ↔ original p := by
  unfold computed
  unfold transformed
  rw [Finset.mem_filter,outputPullback_complete _ _ (by decide +kernel),List.mem_toFinset,{childns}.source_complete]
  simp only [{childns}.original,{childns}.coefficients,PerfectPower.BoundedNative.horner,{childns}.domainCondition,Condition.holds,true_and,and_true,test_correct,mul_zero,add_zero]
  change ((({scale})*p.2)^2=(({b})+p.1*({2*a}))^2+({k})) ∧ domainCondition.holds p ↔ original p
  unfold original
  simp only [PerfectPower.BoundedNative.horner]
  constructor <;> rintro ⟨h,hd⟩ <;> exact ⟨by nlinarith,hd⟩
'''
    else:
        cap=reduction['root_cutoff']
        lean+=f'''def transformed := affinePullback {childns}.sourcePoints.toFinset ({2*a}) ({b})
def computed := transformed.filter fun p => domainCondition.test p=true
theorem computed_complete (p : Int × Int) : p ∈ computed ↔ original p := by
  unfold computed
  unfold transformed
  rw [Finset.mem_filter,affinePullback_complete _ _ _ (by decide +kernel),List.mem_toFinset,{childns}.source_complete]
  simp only [{childns}.original,{childns}.domainCondition,Condition.holds,true_and,and_true,test_correct,mul_zero,add_zero]
  change (|p.2|≤({cap}) ∧ (({2*a})*p.1+({b}))^2-({4*a})*p.2^2=({b*b-4*a*c})) ∧ domainCondition.holds p ↔ original p
  constructor
  · rintro ⟨⟨hb,hn⟩,hd⟩
    have he := (quadratic_norm ({a}) ({b}) ({c}) p.1 p.2 (by decide +kernel)).mpr (by norm_num at hn ⊢; exact hn)
    exact ⟨by simp only [PerfectPower.BoundedNative.horner,mul_zero,add_zero]; nlinarith [he],hd⟩
  · rintro ⟨he,hd⟩
    have he' : p.2^2=({a})*p.1^2+({b})*p.1+({c}) := by
      simp only [PerfectPower.BoundedNative.horner,mul_zero,add_zero] at he
      nlinarith
    have hcut : |p.1|≤({cutoff}) := by
      simp only [domainCondition,Condition.holds,Expr.eval] at hd
      exact abs_le.mpr (by tauto)
    exact ⟨⟨quadratic_root_bound ({a}) ({b}) ({c}) ({cutoff}) ({cap}) p.1 p.2
      (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel) hcut he',
      by
        have h := (quadratic_norm ({a}) ({b}) ({c}) p.1 p.2 (by decide +kernel)).mp he'
        norm_num at h ⊢
        exact h⟩,hd⟩
'''
    lean+=f'''def sourcePoints : List (Int × Int) := {literal}
theorem points_checked : computed=sourcePoints.toFinset := by decide +kernel
theorem source_complete (p : Int × Int) : p ∈ sourcePoints ↔ original p := by
  rw [← List.mem_toFinset,← points_checked]
  exact computed_complete p
'''
    lean,results=_emit_queries(lean,name,points,normalized,plans)
    return dict(schema='pp-automatic-population/1',specification=spec,route=route,reduction=reduction,
        source_count=len(points),source_points=points,results=results,child_specification=child['specification'],
        child_namespace=childns,lean=lean,namespace=name,specification_sha256=_hash(spec),
        source_sha256=hashlib.sha256(lean.encode()).hexdigest(),proof_status='emitted',execution_verified=False,
        scope='complete original square equation in the declared input domain'+(' and absolute input cutoff' if cutoff is not None else ', globally over all input coordinates'))


def check_automatic_population(packet,**options):
    try:expected=automatic_population_certificate(**packet['specification'])
    except (KeyError,TypeError,ValueError,WorkLimit) as error:return dict(accepted=False,reason='invalid specification: '+str(error))
    if packet!=expected:return dict(accepted=False,reason='packet differs from reconstructed automatic reduction')
    if expected['route']=='quadratic_norm':
        modules=list(MODULES)+['PolynomialFibre','FastDivisors','IntegerPolynomialFibres'];audits=list(AUDITS)
    else:
        from .checked_family_population import SOURCES
        modules=['BoundedNative','QueryNative','PolynomialFibre','FastDivisors','IntegerPolynomialFibres']
        family=expected['reduction'].get('family','square_plus_constant')
        if family=='square_plus_constant':modules+=['DivisorPopulation']
        elif family=='mordell_descent':modules+=['MordellDescentCore','MordellDescentMask']
        else:
            _,_,module,core,_=SOURCES[family]
            if family in ('mordell_minus5','mordell_minus6','mordell_minus13'):
                modules+=['ClassTwoCore','MordellMinus5Core','MordellMinus6Core','MordellMinus13Core','AdditionalMordellPopulations']
            else:modules+=['AffinePopulation',core,module]
        audits=['IntegerPolynomialFibres.complete']
        # AutomaticReduction imports the orbit libraries for the quadratic route.
        modules+=['PellFamily','PellOrbitCore','PellOrbitPopulation']
    modules+=['AutomaticReduction'];audits+=['AutomaticReduction.affinePullback_complete','AutomaticReduction.outputPullback_complete','AutomaticReduction.quadratic_norm']
    return check_rebuilt(expected,tuple(dict.fromkeys(modules)),tuple(audits),**options)


def add_commands(sub):
    p=sub.add_parser('checked-auto-population',help='recognize complete polynomial reductions and query original coordinates')
    p.add_argument('--coefficients',required=True,type=json.loads);p.add_argument('--queries',type=json.loads)
    p.add_argument('--cutoff',type=int);p.add_argument('--domain',choices=('integer','nonnegative','positive'),default='integer')
    p.add_argument('--work-limit',type=int,default=4096);p.add_argument('--seed-budget',type=int,default=4096)
    p.add_argument('--check',action='store_true')


def cli(args):
    if args.command!='checked-auto-population':return False
    p=automatic_population_certificate(args.coefficients,args.queries,cutoff=args.cutoff,domain=args.domain,
        work_limit=args.work_limit,seed_budget=args.seed_budget)
    out=dict(packet=p)
    if args.check:out['acceptance']=check_automatic_population(p)
    print(json.dumps(out,sort_keys=True))
    if args.check and not out['acceptance']['accepted']:raise SystemExit(1)
    return True
