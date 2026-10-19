"""Complete generalized Pell populations from checked finite orbit representatives."""
import hashlib
import json
from math import isqrt
from .checked_box import _hash, _integer
from .checked_family import check_rebuilt
from .checked_population import _compile_queries, _emit_queries, _tree
from .checked_pell_family import fundamental_seed, power
from .divisor_square import WorkLimit


def orbit_point(D,A,B,s,k):
    v,u=power(D,A,B,k)
    X,Y=s
    p=[u*Y+v*X,u*X+D*v*Y]
    if max(abs(c).bit_length() for c in p)>4096:
        raise WorkLimit('orbit coordinate exceeds 4096 bits')
    return p


def orbit_length(D,A,B,s,cutoff):
    if s[1]>cutoff:return 0
    low=0;high=1
    while orbit_point(D,A,B,s,high)[0]<=cutoff:low=high;high*=2
    while low+1<high:
        mid=(low+high)//2
        if orbit_point(D,A,B,s,mid)[0]<=cutoff:low=mid
        else:high=mid
    return high


def pell_orbits_certificate(D,norm,cutoff,queries=None,*,domain='integer',
                            global_ranks=None,seed_budget=4096,work_limit=4096):
    D=_integer(D,'D');norm=_integer(norm,'norm');cutoff=_integer(cutoff,'cutoff')
    if not 2<=D<=10**6 or cutoff<0:raise ValueError('D in 2..1000000 and nonnegative cutoff required')
    if domain not in ('integer','nonnegative','positive'):raise ValueError('invalid Pell domain')
    if type(seed_budget) is not int or not 1<=seed_budget<=65536:raise ValueError('invalid seed_budget')
    if type(work_limit) is not int or not 1<=work_limit<=65536:raise ValueError('invalid work_limit')
    A,B,_=fundamental_seed(D,seed_budget)
    bound=abs(norm)*A*A
    Xcap=isqrt(bound+abs(norm));Ycap=isqrt(bound//D)
    area=Xcap*(Ycap+1)+abs(norm)+1
    if area>work_limit:raise WorkLimit('complete orbit seed box exceeds work_limit')
    seeds=[]
    for Y in range(Ycap+1):
        value=norm+D*Y*Y
        if value<=0:continue
        X=isqrt(value)
        if X*X==value and (A*X-D*B*Y<=0 or A*Y-B*X<0):seeds.append([X,Y])
    seeds.sort()
    lengths=[orbit_length(D,A,B,s,cutoff) for s in seeds]
    if sum(lengths)>work_limit:raise WorkLimit('orbit output exceeds work_limit')
    base={tuple(orbit_point(D,A,B,s,k)) for s,L in zip(seeds,lengths) for k in range(L)}
    if norm<=0 and (-norm)%D==0:
        y=isqrt((-norm)//D)
        if D*y*y==-norm and y<=cutoff:base.add((y,0))
    if domain=='integer':points=sorted({(sx*x,sy*y) for x,y in base for sx in (-1,1) for sy in (-1,1)})
    elif domain=='positive':points=sorted(p for p in base if p[0]>0 and p[1]>0)
    else:points=sorted(base)
    points=[list(p) for p in points]
    normalized,plans=_compile_queries(points,[{}] if queries is None else queries)
    ranks=[] if global_ranks is None else global_ranks
    if not isinstance(ranks,list) or len(ranks)>64 or any(not isinstance(r,dict) or set(r)!={'orbit','rank'} or
        type(r['orbit']) is not int or not 0<=r['orbit']<len(seeds) or
        type(r['rank']) is not int or not 0<=r['rank']<=10**6 for r in ranks):
        raise ValueError('at most 64 valid orbit/rank selections required')
    spec=dict(D=D,norm=norm,cutoff=cutoff,queries=normalized,domain=domain,global_ranks=ranks,seed_budget=seed_budget,work_limit=work_limit)
    name='PerfectPower.CheckedPellOrbits_'+_hash(spec)[:16]
    seed_literal='['+','.join(f'(({x}),({y}))' for x,y in seeds)+']'
    count_literal='['+','.join(f'((({x}),({y})),{L})' for (x,y),L in zip(seeds,lengths))+']'
    literal='['+','.join(f'(({x}),({y}))' for x,y in points)+']'
    dc,_=_tree(True if domain!='positive' else ['and',['le',1,'x'],['le',1,'y']],condition=True)
    lean=f'''import PerfectPower.PellOrbitPopulation
namespace {name}
open PerfectPower.QueryNative PerfectPower.PellOrbitCore PerfectPower.PellOrbitPopulation
def unit := PerfectPower.PellFamily.seed ({D}) ({A}) ({B}) (by decide +kernel)
def seedList : List (Int × Int) := {seed_literal}
def seedSet := seedList.toFinset
def lengths (s : Int × Int) : Nat := ({count_literal} : List ((Int × Int) × Nat)).lookup s |>.getD 0
theorem seeds_checked : seeds ({D}) ({A}) ({B}) ({norm}) {Xcap} {Ycap}=seedSet := by decide +kernel
theorem seeds_complete (p : Int × Int) : p ∈ seedSet ↔ 0<p.1 ∧ 0≤p.2 ∧ p.1^2-({D})*p.2^2=({norm}) ∧ terminal ({D}) ({A}) ({B}) p := by
  rw [← seeds_checked]
  exact seed_complete (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel)
    (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel) p
'''
    for j,(s,L) in enumerate(zip(seeds,lengths)):
        fuel=L.bit_length();sx,sy=s
        lean+=f'''theorem boundary_{j} : ({cutoff}) < (unitOrbit ({D}) ({A}) ({B}) (({sx}),({sy})) {L}).2 := by
  have he := fastOrbit_eq unit (({sx}),({sy})) {fuel} {L} (by decide +kernel)
  change fastOrbit unit (({sx}),({sy})) {fuel} {L} = unitOrbit ({D}) ({A}) ({B}) (({sx}),({sy})) {L} at he
  rw [← he]
  decide +kernel
'''
    boundary='''  simp only [seedSet,seedList,List.mem_toFinset,List.mem_cons,List.not_mem_nil,or_false] at hs
'''
    if seeds:
        boundary+='  rcases hs with '+('h' if len(seeds)==1 else ' | '.join('h' for _ in seeds))+'\n'
        for j in range(len(seeds)):boundary+=f'  · subst s\n    simpa only [lengths,List.lookup] using boundary_{j}\n'
    lean+=f'''theorem boundaries (s : Int × Int) (hs : s ∈ seedSet) : ({cutoff}) < (unitOrbit ({D}) ({A}) ({B}) s (lengths s)).2 := by
'''+boundary+f'''def positivePoints := positivePopulation ({D}) ({A}) ({B}) ({cutoff}) seedSet lengths
theorem positive_points_complete (p : Int × Int) : p ∈ positivePoints ↔ 0≤p.1 ∧ 0<p.2 ∧ p.1≤({cutoff}) ∧ p.2^2-({D})*p.1^2=({norm}) :=
  positive_complete (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel) seedSet lengths seeds_complete boundaries p
def nonnegativePoints := positivePoints ∪ zeroPopulation ({D}) ({norm}) ({cutoff})
theorem nonnegative_points_complete (p : Int × Int) : p ∈ nonnegativePoints ↔ 0≤p.1 ∧ 0≤p.2 ∧ p.1≤({cutoff}) ∧ p.2^2-({D})*p.1^2=({norm}) :=
  nonnegative_complete positivePoints positive_points_complete (by decide +kernel) p
'''
    if domain=='integer':
        lean+='def computed := signedPopulation nonnegativePoints\n'
        pred=f'|p.1|≤({cutoff}) ∧ p.2^2-({D})*p.1^2=({norm})'
        lean+=f'theorem computed_complete (p : Int × Int) : p ∈ computed ↔ {pred} := signed_complete nonnegativePoints nonnegative_points_complete p\n'
    else:
        lean+='def computed := nonnegativePoints\n'
        pred=f'0≤p.1 ∧ 0≤p.2 ∧ p.1≤({cutoff}) ∧ p.2^2-({D})*p.1^2=({norm})'
        lean+=f'theorem computed_complete (p : Int × Int) : p ∈ computed ↔ {pred} := nonnegative_points_complete p\n'
    lean+=f'''def domainCondition := {dc}
def allPoints : List (Int × Int) := {literal}
theorem points_checked : computed.filter (fun p => domainCondition.test p = true) = allPoints.toFinset := by decide +kernel
def sourcePoints := allPoints
def original (p : Int × Int) : Prop := ({pred}) ∧ domainCondition.holds p
theorem source_complete (p : Int × Int) : p ∈ sourcePoints ↔ original p := by
  change p ∈ allPoints ↔ original p
  rw [← List.mem_toFinset,← points_checked,Finset.mem_filter,computed_complete,test_correct]
  rfl
'''
    selections=[]
    for j,r in enumerate(ranks):
        s=seeds[r['orbit']];k=r['rank'];p=orbit_point(D,A,B,s,k);fuel=k.bit_length()
        selections.append(dict(**r,point=p,seed=s))
        lean+=f'''theorem orbit_selection_{j} : unitOrbit ({D}) ({A}) ({B}) (({s[0]}),({s[1]})) {k}=(({p[1]}),({p[0]})) := by
  have he := fastOrbit_eq unit (({s[0]}),({s[1]})) {fuel} {k} (by decide +kernel)
  change fastOrbit unit (({s[0]}),({s[1]})) {fuel} {k}=unitOrbit ({D}) ({A}) ({B}) (({s[0]}),({s[1]})) {k} at he
  rw [← he]
  decide +kernel
theorem orbit_rank_{j} (k : Nat) : (unitOrbit ({D}) ({A}) ({B}) (({s[0]}),({s[1]})) k).2=({p[0]}) ↔ k={k} := by
  have h := orbit_input_strictMono (D := ({D})) (A := ({A})) (B := ({B}))
    (by decide +kernel) (by decide +kernel) (by decide +kernel) (({s[0]}),({s[1]})) (by decide +kernel) (by decide +kernel)
  have he : (unitOrbit ({D}) ({A}) ({B}) (({s[0]}),({s[1]})) {k}).2=({p[0]}) := congrArg Prod.snd orbit_selection_{j}
  rw [← he]
  exact h.injective.eq_iff
'''
    lean,results=_emit_queries(lean,name,points,normalized,plans)
    lean+=f'#print axioms {name}.seeds_complete\n'
    lean+=''.join(f'#print axioms {name}.orbit_{kind}_{j}\n' for j in range(len(ranks)) for kind in ('selection','rank'))
    return dict(schema='pp-checked-pell-orbits/1',specification=spec,seeds=seeds,orbit_lengths=lengths,
        source_points=points,source_count=len(points),global_selections=selections,results=results,
        seed_box=[Xcap,Ycap],seed_work=area,unit=[B,A],lean=lean,namespace=name,
        specification_sha256=_hash(spec),source_sha256=hashlib.sha256(lean.encode()).hexdigest(),
        proof_status='emitted',execution_verified=False,
        scope='complete declared-domain solutions of y²-D*x²=norm within the absolute input cutoff; global ranks are within the named seed orbit')


MODULES=('BoundedNative','QueryNative','PellFamily','PellOrbitCore','PellOrbitPopulation')
AUDITS=('PellOrbitCore.terminal_exhaust','PellOrbitCore.terminal_bound','PellOrbitPopulation.positive_complete','PellOrbitPopulation.signed_complete','PellOrbitPopulation.fastOrbit_eq')


def check_pell_orbits(packet,**options):
    try:expected=pell_orbits_certificate(**packet['specification'])
    except (KeyError,TypeError,ValueError,WorkLimit) as error:return dict(accepted=False,reason='invalid specification: '+str(error))
    if packet!=expected:return dict(accepted=False,reason='packet differs from reconstructed orbit query')
    return check_rebuilt(expected,MODULES,AUDITS,**options)


def add_commands(sub):
    p=sub.add_parser('checked-pell-orbits',help='complete generalized Pell populations and per-orbit fast ranks')
    for key in ('D','norm','cutoff'):p.add_argument('--'+key,required=True,type=int)
    p.add_argument('--queries',type=json.loads);p.add_argument('--global-ranks',type=json.loads)
    p.add_argument('--domain',choices=('integer','nonnegative','positive'),default='integer')
    p.add_argument('--seed-budget',type=int,default=4096);p.add_argument('--work-limit',type=int,default=4096)
    p.add_argument('--check',action='store_true')


def cli(args):
    if args.command!='checked-pell-orbits':return False
    p=pell_orbits_certificate(args.D,args.norm,args.cutoff,args.queries,domain=args.domain,
        global_ranks=args.global_ranks,seed_budget=args.seed_budget,work_limit=args.work_limit)
    out=dict(packet=p)
    if args.check:out['acceptance']=check_pell_orbits(p)
    print(json.dumps(out,sort_keys=True))
    if args.check and not out['acceptance']['accepted']:raise SystemExit(1)
    return True
