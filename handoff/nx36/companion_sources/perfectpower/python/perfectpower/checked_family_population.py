"""General square differences and divisor-based pullbacks of proved Mordell sources."""
import hashlib
import json
from math import isqrt
from .checked_box import _hash,_integer
from .checked_family import check_rebuilt
from .checked_population import _compile_queries,_emit_queries,_tree
from .checked_nonlinear_population import _eval,_multiply,FAMILIES
from .divisor_square import WorkLimit
from .resources import runtime_root

SOURCES=dict(FAMILIES,
    mordell_minus5=(5,[],'AdditionalMordellMinus5','MordellMinus5Core','MordellMinus5'),
    mordell_minus6=(6,[],'AdditionalMordellMinus6','MordellMinus6Core','MordellMinus6'),
    mordell_minus13=(13,[(17,-70),(17,70)],'AdditionalMordellMinus13','MordellMinus13Core','MordellMinus13'))


class Budget:
    def __init__(self,limit):self.limit=limit;self.used=0
    def charge(self,n):
        self.used+=n
        if self.used>self.limit:raise WorkLimit('exact divisor/fibre work exceeds work_limit')


def signed_divisors(n,budget):
    cap=isqrt(abs(n));budget.charge(cap)
    positive=set()
    for d in range(1,cap+1):
        if n%d==0:positive.update((d,abs(n)//d))
    return sorted(positive|{-d for d in positive})


def polynomial_roots(cs,budget):
    if len(cs)<=1:return []
    a=cs[0]
    if len(cs)==2:
        budget.charge(1)
        return [(-a)//cs[1]] if (-a)%cs[1]==0 else []
    if a==0:return sorted({0,*polynomial_roots(cs[1:],budget)})
    candidates=signed_divisors(a,budget);budget.charge(len(cs)*len(candidates))
    return [x for x in candidates if _eval(cs,x)==0]


def family_population_certificate(coefficients,queries,*,family='square_plus_constant',offset=None,
                                  domain='integer',work_limit=4096):
    if not isinstance(coefficients,list) or not 2<=len(coefficients)<=33:raise ValueError('2..33 ascending coefficients required')
    cs=[_integer(c,'coefficient') for c in coefficients]
    if cs[-1]==0:raise ValueError('nonconstant polynomial with nonzero leading coefficient required')
    if type(work_limit) is not int or not 1<=work_limit<=65536:raise ValueError('work_limit must be 1..65536')
    if domain not in ('integer','nonnegative','positive'):raise ValueError('invalid input domain')
    budget=Budget(work_limit)
    if family=='square_plus_constant':
        k=_integer(1 if offset is None else offset,'offset')
        if k==0:raise ValueError('offset zero is an infinite square family, not a finite population')
        base=[]
        for u in signed_divisors(k,budget):
            v=k//u
            if (v-u)%2==0 and (v+u)%2==0:base.append(((v-u)//2,(v+u)//2))
        base=sorted(set(base));exponent=2
    elif family=='mordell_descent':
        if offset is None:raise ValueError('a proved descent offset is required')
        k=_integer(offset,'offset')
        rows=json.loads((runtime_root()/'data/mordell_descent_sources.json').read_text())['rows']
        row=next((v for v in rows if v['k']==k),None)
        if row is None:raise ValueError('offset is outside the proved descent atlas')
        base=[];exponent=3
    elif type(family) is str and family in SOURCES:
        positive,base,*_=SOURCES[family];k=-positive;exponent=3
        if offset is not None and offset!=k:raise ValueError('offset does not match the proved source family')
    else:raise ValueError('unsupported proved family')
    fibres={}
    for v,_ in base:
        if v not in fibres:
            shifted=[cs[0]-v,*cs[1:]];fibres[v]=polynomial_roots(shifted,budget)
    points=sorted({(x,y) for v,y in base for x in fibres[v]
                   if domain=='integer' or x>=(0 if domain=='nonnegative' else 1)})
    points=[list(p) for p in points]
    normalized,plans=_compile_queries(points,queries)
    spec=dict(coefficients=cs,queries=normalized,family=family,offset=k,domain=domain,work_limit=work_limit)
    name='PerfectPower.CheckedFamilyPopulation_'+_hash(spec)[:16]
    dc,_=_tree(True if domain=='integer' else ['le',0 if domain=='nonnegative' else 1,'x'],condition=True)
    expanded=_multiply(cs,cs)
    if exponent==3:expanded=_multiply(expanded,cs)
    expanded[0]+=k
    # Check the complete unrestricted population, then apply the declared domain.
    allpoints=sorted({(x,y) for v,y in base for x in fibres[v]})
    all_literal='['+','.join(f'(({x}),({y}))' for x,y in allpoints)+']'
    if family=='square_plus_constant':
        imports='import PerfectPower.DivisorPopulation\n'
        definitions=f'''def computed := PerfectPower.DivisorPopulation.points coefficients ({k})
theorem computed_complete (p : Int × Int) : p ∈ computed ↔ p.2^2 = (PerfectPower.BoundedNative.horner coefficients p.1)^2+({k}) :=
  (PerfectPower.DivisorPopulation.complete coefficients ({k}) (by decide +kernel) (by decide +kernel) (by decide +kernel) p.1 p.2).symm
'''
    elif family=='mordell_descent':
        imports='import PerfectPower.IntegerPolynomialFibres\nimport PerfectPower.MordellDescentMask\n'
        definitions=f'''def baseSource : Finset (Int × Int) := ∅
theorem base_complete (p : Int × Int) : p ∈ baseSource ↔ p.2^2 = p.1^3+({k}) := by
  simp only [baseSource,Finset.not_mem_empty,false_iff]
  have h := PerfectPower.MordellDescent.no_points (D := {row['D']}) (c := {row['c']}) (b := {row['b']}) (by norm_num)
    (PerfectPower.MordellDescent.goodDivisors_of_cert (by norm_num) {row['j']} (b₁ := {row['b1']}) (u := {row['u']}) (by norm_num) (by norm_num))
    (M := {row['M']}) (by norm_num) (by norm_num)
    (PerfectPower.MordellDescentMask.congr_ok _ _ _ {row['M']} PerfectPower.MordellDescentMask.mask{row['M']} PerfectPower.MordellDescentMask.square{row['M']} (by decide +kernel)) p.1 p.2
  norm_num at h
  exact h
def computed := PerfectPower.IntegerPolynomialFibres.pullback baseSource coefficients
theorem computed_complete (p : Int × Int) : p ∈ computed ↔ p.2^2 = (PerfectPower.BoundedNative.horner coefficients p.1)^3+({k}) :=
  PerfectPower.IntegerPolynomialFibres.pullback_complete baseSource _ base_complete coefficients (by decide +kernel) (by decide +kernel) p
'''
    else:
        _,_,module,_,_=SOURCES[family]
        root='PerfectPower.'+module
        imports='import PerfectPower.IntegerPolynomialFibres\nimport PerfectPower.'+('AdditionalMordellPopulations' if family in ('mordell_minus5','mordell_minus6','mordell_minus13') else module)+'\n'
        definitions=f'''def baseSource := {root}.points.toFinset
theorem base_complete (p : Int × Int) : p ∈ baseSource ↔ p.2^2 = p.1^3+({k}) := by
  simpa [baseSource] using {root}.complete p
def computed := PerfectPower.IntegerPolynomialFibres.pullback baseSource coefficients
theorem computed_complete (p : Int × Int) : p ∈ computed ↔ p.2^2 = (PerfectPower.BoundedNative.horner coefficients p.1)^3+({k}) :=
  PerfectPower.IntegerPolynomialFibres.pullback_complete baseSource _ base_complete coefficients (by decide +kernel) (by decide +kernel) p
'''
    lean=imports+f'''namespace {name}
open PerfectPower.QueryNative
def coefficients : List Int := {cs}
'''+definitions+f'''def allPoints : List (Int × Int) := {all_literal}
theorem checked_points : computed = allPoints.toFinset := by decide +kernel
def domainCondition := {dc}
def sourcePoints := restrict allPoints domainCondition
def original (p : Int × Int) : Prop := p.2^2 = (PerfectPower.BoundedNative.horner coefficients p.1)^{exponent}+({k}) ∧ domainCondition.holds p
theorem all_complete (p : Int × Int) : p ∈ allPoints ↔ p.2^2 = (PerfectPower.BoundedNative.horner coefficients p.1)^{exponent}+({k}) :=
  PerfectPower.IntegerPolynomialFibres.literal_complete computed allPoints _ computed_complete checked_points p
theorem source_complete (p : Int × Int) : p ∈ sourcePoints ↔ original p :=
  restrict_complete allPoints _ all_complete domainCondition p
theorem expanded_original (p : Int × Int) : original p ↔ p.2^2 = PerfectPower.BoundedNative.horner {expanded} p.1 ∧ domainCondition.holds p := by
  have h : (PerfectPower.BoundedNative.horner coefficients p.1)^{exponent}+({k}) = PerfectPower.BoundedNative.horner {expanded} p.1 := by
    simp only [coefficients, PerfectPower.BoundedNative.horner]
    ring
  simp only [original,h]
'''
    lean,results=_emit_queries(lean,name,points,normalized,plans)
    lean+=f'#print axioms {name}.expanded_original\n#print axioms {name}.computed_complete\n'
    return dict(schema='pp-checked-family-population/1',specification=spec,source_count=len(points),source_points=points,
                original_coefficients=expanded,divisor_work=budget.used,results=results,lean=lean,namespace=name,
                specification_sha256=_hash(spec),source_sha256=hashlib.sha256(lean.encode()).hexdigest(),
                proof_status='emitted',execution_verified=False,scope='complete globally over all integer coordinates in the declared input domain')


def check_family_population(packet,**options):
    try:expected=family_population_certificate(**packet['specification'])
    except (KeyError,TypeError,ValueError,WorkLimit) as error:return dict(accepted=False,reason='invalid specification: '+str(error))
    if packet!=expected:return dict(accepted=False,reason='packet differs from reconstructed proved family')
    family=expected['specification']['family'];modules=['BoundedNative','QueryNative','PolynomialFibre','FastDivisors','IntegerPolynomialFibres'];audits=['IntegerPolynomialFibres.complete','IntegerPolynomialFibres.pullback_complete']
    if family=='square_plus_constant':modules+=['DivisorPopulation'];audits+=['DivisorPopulation.values_complete','DivisorPopulation.complete']
    elif family=='mordell_descent':
        modules+=['MordellDescentCore','MordellDescentMask'];audits+=['MordellDescent.no_points','MordellDescentMask.congr_ok']
    elif family in ('mordell_minus5','mordell_minus6','mordell_minus13'):
        modules+=['ClassTwoCore','MordellMinus5Core','MordellMinus6Core','MordellMinus13Core','AdditionalMordellPopulations'];audits+=['AdditionalMordellMinus13.complete','AdditionalMordellMinus5.complete','AdditionalMordellMinus6.complete']
    else:
        _,_,module,core,namespace=SOURCES[family];modules+=['AffinePopulation',core,module];audits+=[namespace+'.points',module+'.complete']
    return check_rebuilt(expected,modules,audits,**options)


def add_commands(sub):
    p=sub.add_parser('checked-family-population',help='global square differences and divisor-based Mordell pullbacks')
    p.add_argument('--coeff',required=True,type=json.loads);p.add_argument('--queries',required=True,type=json.loads)
    p.add_argument('--family',choices=('square_plus_constant','mordell_descent',*SOURCES),default='square_plus_constant')
    p.add_argument('--offset',type=int);p.add_argument('--domain',choices=('integer','nonnegative','positive'),default='integer')
    p.add_argument('--work-limit',type=int,default=4096);p.add_argument('--check',action='store_true')


def cli(args):
    if args.command!='checked-family-population':return False
    p=family_population_certificate(args.coeff,args.queries,family=args.family,offset=args.offset,domain=args.domain,work_limit=args.work_limit)
    out=dict(packet=p)
    if args.check:out['acceptance']=check_family_population(p)
    print(json.dumps(out,sort_keys=True))
    if args.check and not out['acceptance']['accepted']:raise SystemExit(1)
    return True
