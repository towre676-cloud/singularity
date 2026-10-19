"""General-D Pell counts, fast global access, signed populations and global minima."""
import hashlib
import json
from math import isqrt
from .checked_box import _hash,_integer
from .checked_family import check_rebuilt
from .checked_population import _compile_queries,_emit_queries,_tree
from .divisor_square import WorkLimit


def fundamental_seed(D,budget):
    a0=isqrt(D)
    if a0*a0==D:raise ValueError('D must be nonsquare')
    m=0;den=1;a=a0;p0=0;p1=1;q0=1;q1=0
    for _ in range(4096):
        A=a*p1+p0;B=a*q1+q0
        if A.bit_length()>4096 or B.bit_length()>4096:raise WorkLimit('fundamental seed exceeds 4096 bits')
        if A*A-D*B*B==1:
            if B>budget:raise WorkLimit('fundamental minimality certificate exceeds seed_budget')
            gaps=[isqrt(D*y*y+1) for y in range(B)]
            if any(gaps[y]**2==D*y*y+1 for y in range(1,B)):raise ValueError('seed is not fundamental')
            return A,B,gaps
        p0,p1=p1,A;q0,q1=q1,B;m=den*a-m;den=(D-m*m)//den;a=(a0+m)//den
    raise WorkLimit('continued-fraction producer exceeds 4096 steps')


def power(D,A,B,k):
    r=(1,0);b=(A,B)
    def mul(p,q):
        x=p[0]*q[0]+D*p[1]*q[1];y=p[0]*q[1]+p[1]*q[0]
        if max(x.bit_length(),y.bit_length())>4096:raise WorkLimit('Pell point exceeds 4096 bits')
        return x,y
    while k:
        if k&1:r=mul(r,b)
        k//=2
        if k:b=mul(b,b)
    return [r[1],r[0]]


def cutoff_count(D,A,B,N):
    low=0;high=1
    while power(D,A,B,high)[0]<=N:low=high;high*=2
    while low+1<high:
        mid=(low+high)//2
        if power(D,A,B,mid)[0]<=N:low=mid
        else:high=mid
    return high


def _positive(e):
    if type(e) is int:return e>=0
    if e in ('x','y'):return True
    if isinstance(e,list) and e:
        return _positive(e[1]) and (e[0]=='pow' or _positive(e[2]))
    return False


def pell_family_certificate(D,cutoff,queries=None,*,domain='nonnegative',global_ranks=None,
                            global_objective=None,seed_budget=4096):
    D=_integer(D,'D');N=_integer(cutoff,'cutoff')
    if not 2<=D<=10**6:raise ValueError('D must be 2..1000000')
    if N<0:raise ValueError('cutoff must be nonnegative')
    if type(seed_budget) is not int or not 1<=seed_budget<=65536:raise ValueError('seed_budget must be 1..65536')
    if domain not in ('nonnegative','integer','positive'):raise ValueError('invalid Pell domain')
    ranks=[] if global_ranks is None else global_ranks
    if not isinstance(ranks,list) or len(ranks)>64 or any(type(k) is not int or not 0<=k<=10**6 for k in ranks):raise ValueError('at most 64 ranks in 0..1000000 required')
    A,B,gaps=fundamental_seed(D,seed_budget);count=cutoff_count(D,A,B,N)
    direct=queries is None or queries==[]
    if direct and domain!='nonnegative':queries=[{}];direct=False
    base=[] if direct else [power(D,A,B,k) for k in range(count)]
    if domain=='integer':
        points=[]
        for x,y in base:
            points.extend([[0,y],[0,-y]] if x==0 else [[x,y],[-x,y],[x,-y],[-x,-y]])
    elif domain=='positive':points=[p for p in base if p[0]>0]
    else:points=base
    if direct:normalized=[];plans=[]
    else:normalized,plans=_compile_queries(points,queries)
    optimum=None;oe=None
    if global_objective is not None:
        if domain!='nonnegative':raise ValueError('global objectives currently require the nonnegative quadrant')
        oe,evaluate=_tree(global_objective)
        if global_objective==['mul',-1,'x']:optimum=dict(status='unbounded_below')
        elif _positive(global_objective):optimum=dict(status='minimum',value=evaluate([0,1]),witness=[0,1],ties='all original solutions with objective equal to this value; may be infinite')
        else:raise ValueError('global objective needs nonnegative constants or must be -x')
    spec=dict(D=D,cutoff=N,queries=normalized,domain=domain,global_ranks=ranks,global_objective=global_objective,seed_budget=seed_budget)
    name='PerfectPower.CheckedPellFamily_'+_hash(spec)[:16]
    lean=f'''import PerfectPower.PellFamily
namespace {name}
open PerfectPower.QueryNative PerfectPower.PellFamily
def unit := seed ({D}) ({A}) ({B}) (by decide +kernel)
theorem unit_fundamental : Pell.IsFundamental unit :=
  fundamental ({D}) ({A}) ({B}) (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel) {gaps} (by decide +kernel)
'''
    audits=['unit_fundamental']
    def boundary(label,k,comparison):
        nonlocal lean
        fuel=k.bit_length()
        lean+=f'''theorem {label} : {comparison} := by
  rw [← fastPoint_eq unit {fuel} {k} (by decide +kernel)]
  decide +kernel
'''
        audits.append(label)
    boundary('last_inside',count-1,f'(point unit {count-1}).1 ≤ ({N})')
    boundary('next_outside',count,f'({N}) < (point unit {count}).1')
    lean+=f'''theorem cutoff_rank_iff (k : Nat) : (point unit k).1 ≤ ({N}) ↔ k < {count} :=
  cutoff_rank unit unit_fundamental {count} ({N}) (by decide +kernel) last_inside next_outside k
''';audits.append('cutoff_rank_iff')
    if direct:
        lean+=f'''def original (p : Int × Int) : Prop := 0 ≤ p.1 ∧ 0 ≤ p.2 ∧ p.1 ≤ ({N}) ∧ p.2^2 = ({D})*p.1^2+1
theorem source_complete (p : Int × Int) : p ∈ cutoffFinset unit {count} ↔ original p :=
  cutoffFinset_complete unit unit_fundamental {count} ({N}) (by decide +kernel) last_inside next_outside p
theorem exact_count : (cutoffFinset unit {count}).card = {count} := cutoffFinset_card unit unit_fundamental {count}
''';audits+=['source_complete','exact_count']
    else:
        if domain=='integer':pred=f'|p.1| ≤ ({N}) ∧ p.2^2 = ({D})*p.1^2+1';prefix='signedPrefix';theorem='signed_prefix_complete'
        else:pred=f'0 ≤ p.1 ∧ 0 ≤ p.2 ∧ p.1 ≤ ({N}) ∧ p.2^2 = ({D})*p.1^2+1';prefix='populationPrefix';theorem='prefix_complete'
        condition=True if domain!='positive' else ['le',1,'x'];dc,_=_tree(condition,condition=True)
        literal='['+','.join(f'(({x}),({y}))' for x,y in (points if domain=='integer' else base))+']'
        lean+=f'''def allPoints : List (Int × Int) := {literal}
theorem prefix_checked : {prefix} unit {count} = allPoints := by decide +kernel
theorem all_complete (p : Int × Int) : p ∈ allPoints ↔ {pred} := by
  rw [← prefix_checked]
  exact {theorem} unit unit_fundamental {count} ({N}) (by decide +kernel) last_inside next_outside p
def domainCondition := {dc}
def sourcePoints := restrict allPoints domainCondition
def original (p : Int × Int) : Prop := ({pred}) ∧ domainCondition.holds p
theorem source_complete (p : Int × Int) : p ∈ sourcePoints ↔ original p :=
  restrict_complete allPoints _ all_complete domainCondition p
'''
    selections=[]
    for j,k in enumerate(ranks):
        p=power(D,A,B,k);selections.append(dict(rank=k,point=p));fuel=k.bit_length()
        lean+=f'''theorem fast_selection_{j} : fastPoint unit {fuel} {k} = (({p[0]}),({p[1]})) := by decide +kernel
theorem global_selection_{j} : point unit {k} = (({p[0]}),({p[1]})) := by
  rw [← fastPoint_eq unit {fuel} {k} (by decide +kernel)]
  exact fast_selection_{j}
theorem global_rank_{j} (k : Nat) : point unit k = (({p[0]}),({p[1]})) ↔ k = {k} := by
  rw [← global_selection_{j}]
  exact (point_injective unit unit_fundamental).eq_iff
''';audits+=[f'fast_selection_{j}',f'global_selection_{j}',f'global_rank_{j}']
    if optimum is not None:
        if optimum['status']=='minimum':
            lean+=f'''def globalObjective := {oe}
theorem global_minimum_value (p : Int × Int)
    (hp : 0 ≤ p.1 ∧ 0 ≤ p.2 ∧ p.2^2 = ({D})*p.1^2+1) : ({optimum['value']}) ≤ globalObjective.eval p := by
  have h := global_minimum unit unit_fundamental globalObjective (by decide +kernel) p hp
  have he : globalObjective.eval (0,1) = ({optimum['value']}) := by decide +kernel
  simpa only [he] using h
theorem global_minimum_attained : globalObjective.eval (0,1) = ({optimum['value']}) := by decide +kernel
theorem global_witness_is_solution : (0: Int) ≤ 0 ∧ (0: Int) ≤ 1 ∧ (1: Int)^2 = ({D})*0^2+1 := by decide +kernel
''';audits+=['global_minimum_value','global_minimum_attained','global_witness_is_solution']
        else:
            lean+=f'''theorem global_unbounded_below (bound : Int) : ∃ p : Int × Int,
    (0 ≤ p.1 ∧ 0 ≤ p.2 ∧ p.2^2 = ({D})*p.1^2+1) ∧ -p.1 < bound :=
  negative_input_unbounded unit unit_fundamental bound
''';audits+=['global_unbounded_below']
    if direct:results=[];lean+=f'end {name}\n'
    else:lean,results=_emit_queries(lean,name,points,normalized,plans)
    lean+=''.join(f'#print axioms {name}.{t}\n' for t in audits)
    return dict(schema='pp-checked-pell-family/1',specification=spec,fundamental_seed=[B,A],source_count=count if direct else len(points),
                source_points=None if direct else points,cutoff_orbit_count=count,next_point=power(D,A,B,count),
                global_selections=selections,global_optimum=optimum,results=results,lean=lean,namespace=name,
                specification_sha256=_hash(spec),source_sha256=hashlib.sha256(lean.encode()).hexdigest(),proof_status='emitted',
                execution_verified=False,scope='complete declared-domain solutions of y²=D*x²+1 within the absolute input cutoff; global ranks refer to the nonnegative orbit')


def check_pell_family(packet,**options):
    try:expected=pell_family_certificate(**packet['specification'])
    except (KeyError,TypeError,ValueError,WorkLimit) as error:return dict(accepted=False,reason='invalid specification: '+str(error))
    if packet!=expected:return dict(accepted=False,reason='packet differs from reconstructed general Pell query')
    return check_rebuilt(expected,('BoundedNative','QueryNative','PellFamily'),
        ('PellFamily.fundamental','PellFamily.complete','PellFamily.fastPower_eq','PellFamily.signed_prefix_complete','PellFamily.global_minimum','PellFamily.negative_input_unbounded'),**options)


def add_commands(sub):
    p=sub.add_parser('checked-pell-family',help='general-D Pell counts, signed queries and fast global access')
    p.add_argument('--D',required=True,type=int);p.add_argument('--cutoff',required=True,type=int)
    p.add_argument('--queries',type=json.loads);p.add_argument('--domain',choices=('nonnegative','integer','positive'),default='nonnegative')
    p.add_argument('--global-ranks',type=json.loads,default=[]);p.add_argument('--global-objective',type=json.loads)
    p.add_argument('--seed-budget',type=int,default=4096);p.add_argument('--check',action='store_true')


def cli(args):
    if args.command!='checked-pell-family':return False
    p=pell_family_certificate(args.D,args.cutoff,args.queries,domain=args.domain,global_ranks=args.global_ranks,global_objective=args.global_objective,seed_budget=args.seed_budget)
    out=dict(packet=p)
    if args.check:out['acceptance']=check_pell_family(p)
    print(json.dumps(out,sort_keys=True))
    if args.check and not out['acceptance']['accepted']:raise SystemExit(1)
    return True
