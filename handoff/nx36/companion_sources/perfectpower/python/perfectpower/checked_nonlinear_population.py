"""Globally complete nonlinear pullbacks of proved integer source populations."""
import hashlib
import json

from .checked_box import _hash, _integer
from .checked_family import check_rebuilt
from .checked_population import _compile_queries, _emit_queries, _tree
from .divisor_square import WorkLimit

FAMILIES={
    'mordell_minus2': (2,[(3,-5),(3,5)],'GlobalMordellPopulation','MordellMinus2Core','MordellMinus2'),
    'mordell_minus4': (4,[(2,-2),(2,2),(5,-11),(5,11)],'GlobalMordellMinus4Population','MordellMinus4Core','MordellMinus4'),
}


def _multiply(a,b):
    c=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):c[i+j]+=x*y
    return c


def _eval(cs,x):
    value=0
    for c in reversed(cs):
        value=c+x*value
        if value.bit_length()>4096:raise WorkLimit('polynomial evaluation exceeds 4096 bits')
    return value


def nonlinear_population_certificate(coefficients, queries, *, family='mordell_minus2',
                                       domain='integer', work_limit=4096):
    """All integer solutions of y²=U(x)³-k, for k=2 or 4.

    U uses ascending integer coefficients. Its nonzero leading coefficient and
    positive degree are required; the complete input bound is proved in Lean.
    Every returned query refers to original x and y. Work limits bound proof
    generation and never silently truncate the mathematical population.
    """
    if type(family) is not str or family not in FAMILIES:raise ValueError('unsupported globally proved family')
    if not isinstance(coefficients,list) or not 2<=len(coefficients)<=33:
        raise ValueError('2..33 ascending coefficients required')
    cs=[_integer(c,'coefficient') for c in coefficients]
    if any(c.bit_length()>128 for c in cs):raise WorkLimit('coefficients exceed 128 bits')
    if cs[-1]==0:raise ValueError('nonzero leading coefficient required')
    if domain not in ('integer','nonnegative','positive'):raise ValueError('invalid input domain')
    if type(work_limit) is not int or not 1<=work_limit<=65536:raise ValueError('work_limit must be 1..65536')
    k,source,module,core,namespace=FAMILIES[family]
    height=sum(abs(c) for c in cs)
    bounds={x:height+abs(x)+1 for x,_ in source}
    cost=sum(2*b+1 for b in bounds.values())*len(cs)
    if cost>work_limit:raise WorkLimit('proved polynomial fibres exceed work_limit')
    condition=True if domain=='integer' else ['le',0 if domain=='nonnegative' else 1,'x']
    dc,de=_tree(condition,condition=True)
    fibres={v:[x for x in range(-b,b+1) if _eval(cs,x)==v] for v,b in bounds.items()}
    points=[[x,y] for v,y in source for x in fibres[v] if de([x,y])]
    normalized,plans=_compile_queries(points,queries)
    spec=dict(coefficients=cs,queries=normalized,family=family,domain=domain,work_limit=work_limit)
    name='PerfectPower.CheckedNonlinearPopulation_'+_hash(spec)[:16]
    expanded=_multiply(_multiply(cs,cs),cs);expanded[0]-=k
    lean=f'''import PerfectPower.{module}
import PerfectPower.PolynomialFibre
namespace {name}
open PerfectPower.QueryNative
def coefficients : List Int := {cs}
def domainCondition := {dc}
def sourcePoints := restrict (PerfectPower.PolynomialFibre.pullback PerfectPower.{module}.points coefficients) domainCondition
def original (p : Int × Int) : Prop := p.2^2 = (PerfectPower.BoundedNative.horner coefficients p.1)^3-{k} ∧ domainCondition.holds p
theorem source_complete (p : Int × Int) : p ∈ sourcePoints ↔ original p :=
  restrict_complete _ _ (PerfectPower.PolynomialFibre.pullback_complete PerfectPower.{module}.points _ PerfectPower.{module}.complete coefficients (by decide +kernel) (by decide +kernel)) domainCondition p
theorem expanded_original (p : Int × Int) : original p ↔
    p.2^2 = PerfectPower.BoundedNative.horner {expanded} p.1 ∧ domainCondition.holds p := by
  have he : (PerfectPower.BoundedNative.horner coefficients p.1)^3-{k} = PerfectPower.BoundedNative.horner {expanded} p.1 := by
    simp only [coefficients, PerfectPower.BoundedNative.horner]
    ring
  simp only [original, he]
'''
    lean,results=_emit_queries(lean,name,points,normalized,plans)
    lean+=f'#print axioms {name}.expanded_original\n'
    return dict(schema='pp-checked-nonlinear-population/1',specification=spec,source_count=len(points),
                source_points=points,original_coefficients=expanded,proved_fibre_bounds={str(v):b for v,b in bounds.items()},
                results=results,lean=lean,namespace=name,specification_sha256=_hash(spec),
                source_sha256=hashlib.sha256(lean.encode()).hexdigest(),proof_status='emitted',
                execution_verified=False,scope='complete globally for all integer coordinates in the declared domain')


def check_nonlinear_population(packet, **options):
    try:expected=nonlinear_population_certificate(**packet['specification'])
    except (KeyError,TypeError,ValueError,WorkLimit) as error:
        return dict(accepted=False,reason='invalid specification: '+str(error))
    if packet!=expected:return dict(accepted=False,reason='packet differs from reconstructed nonlinear query')
    _,_,module,core,namespace=FAMILIES[expected['specification']['family']]
    return check_rebuilt(expected,('BoundedNative','QueryNative','AffinePopulation',core,module,'PolynomialFibre'),
                         (namespace+'.points',module+'.complete','PolynomialFibre.pullback_complete'),**options)


def add_commands(sub):
    p=sub.add_parser('checked-nonlinear-population',help='global nonlinear proved-family queries')
    p.add_argument('--coeff',required=True,type=json.loads)
    p.add_argument('--queries',required=True,type=json.loads)
    p.add_argument('--family',choices=tuple(FAMILIES),default='mordell_minus2')
    p.add_argument('--domain',choices=('integer','nonnegative','positive'),default='integer')
    p.add_argument('--work-limit',type=int,default=4096)
    p.add_argument('--check',action='store_true')


def cli(args):
    if args.command!='checked-nonlinear-population':return False
    packet=nonlinear_population_certificate(args.coeff,args.queries,family=args.family,domain=args.domain,work_limit=args.work_limit)
    output=dict(packet=packet)
    if args.check:output['acceptance']=check_nonlinear_population(packet)
    print(json.dumps(output,sort_keys=True))
    if args.check and not output['acceptance']['accepted']:raise SystemExit(1)
    return True
