"""Exact queries over a globally generated nonnegative Pell population."""
import hashlib
import json

from .checked_box import _hash, _integer
from .checked_family import check_rebuilt
from .checked_population import _compile_queries, _emit_queries
from .divisor_square import WorkLimit


def _next(p):
    n,m=p
    return [2*m+3*n,3*m+4*n]


def pell_population_certificate(cutoff, queries, *, global_ranks=None):
    """Complete nonnegative solutions of y²=2x²+1 with x≤cutoff.

    Global ranks index the increasing input recurrence starting at (0,1).
    Queries, minima and local ranks concern only the exact cutoff population.
    """
    cutoff=_integer(cutoff,'cutoff')
    if cutoff<0 or cutoff.bit_length()>128:raise ValueError('nonnegative cutoff of at most 128 bits required')
    ranks=[] if global_ranks is None else global_ranks
    if not isinstance(ranks,list) or len(ranks)>64 or any(type(i) is not int or not 0<=i<=128 for i in ranks):
        raise ValueError('at most 64 global ranks in 0..128 required')
    points=[];p=[0,1]
    while p[0]<=cutoff:
        points.append(p);p=_next(p)
    sequence=points+[p]
    while len(sequence)<=max(ranks,default=0):sequence.append(_next(sequence[-1]))
    normalized,plans=_compile_queries(points,queries)
    spec=dict(cutoff=cutoff,queries=normalized,global_ranks=ranks)
    name='PerfectPower.CheckedPellPopulation_'+_hash(spec)[:16]
    length=len(points)
    lean=f'''import PerfectPower.PellPopulation
namespace {name}
open PerfectPower.QueryNative PerfectPower.PellPopulation
def sourcePoints := populationPrefix {length}
def original (p : Int × Int) : Prop := 0 ≤ p.1 ∧ 0 ≤ p.2 ∧ p.1 ≤ ({cutoff}) ∧ p.2^2 = 2*p.1^2+1
theorem source_complete (p : Int × Int) : p ∈ sourcePoints ↔ original p :=
  prefix_complete {length} ({cutoff}) (by decide +kernel) (by decide +kernel) p
'''
    global_selections=[]
    for j,i in enumerate(ranks):
        x,y=sequence[i];global_selections.append(dict(rank=i,point=[x,y]))
        lean+=f'''theorem global_selection_{j} : point {i} = (({x}),({y})) := by decide +kernel
theorem global_rank_{j} (k : Nat) : point k = (({x}),({y})) ↔ k = {i} := by
  rw [← global_selection_{j}]
  exact point_injective.eq_iff
'''
    lean,results=_emit_queries(lean,name,points,normalized,plans)
    lean+=''.join(f'#print axioms {name}.{kind}_{j}\n' for j in range(len(ranks)) for kind in ('global_selection','global_rank'))
    return dict(schema='pp-checked-pell-population/1',specification=spec,source_count=len(points),
                source_points=points,next_point=p,global_selections=global_selections,
                results=results,lean=lean,namespace=name,specification_sha256=_hash(spec),
                source_sha256=hashlib.sha256(lean.encode()).hexdigest(),proof_status='emitted',
                execution_verified=False,scope='complete nonnegative Pell solutions up to the declared input cutoff; global ranks follow the increasing recurrence')


def check_pell_population(packet, **options):
    try:expected=pell_population_certificate(**packet['specification'])
    except (KeyError,TypeError,ValueError,WorkLimit) as error:
        return dict(accepted=False,reason='invalid specification: '+str(error))
    if packet!=expected:return dict(accepted=False,reason='packet differs from reconstructed Pell query')
    return check_rebuilt(expected,('BoundedNative','QueryNative','PellPopulation'),
                         ('PellPopulation.global_complete','PellPopulation.input_strictMono','PellPopulation.prefix_complete'),**options)


def add_commands(sub):
    p=sub.add_parser('checked-pell-population',help='exact cutoff queries and global Pell selections')
    p.add_argument('--cutoff',required=True,type=int)
    p.add_argument('--queries',required=True,type=json.loads)
    p.add_argument('--global-ranks',type=json.loads,default=[])
    p.add_argument('--check',action='store_true')


def cli(args):
    if args.command!='checked-pell-population':return False
    packet=pell_population_certificate(args.cutoff,args.queries,global_ranks=args.global_ranks)
    output=dict(packet=packet)
    if args.check:output['acceptance']=check_pell_population(packet)
    print(json.dumps(output,sort_keys=True))
    if args.check and not output['acceptance']['accepted']:raise SystemExit(1)
    return True
