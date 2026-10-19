"""Exact finite experiment/fidelity/setup selection with replayable envelopes."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import product
import hashlib
import json
from .dynacomp_adapter import exact, bundled_adapter


def _digest(value):
    def encode(v):
        if isinstance(v,Q):return [v.numerator,v.denominator]
        if isinstance(v,(tuple,list)):return [encode(x) for x in v]
        if isinstance(v,dict):return {k:encode(x) for k,x in v.items()}
        return v
    return hashlib.sha256(json.dumps(encode(value),sort_keys=True,separators=(',',':')).encode()).hexdigest()


@dataclass(frozen=True)
class BoundedReading:
    center: Q
    physical_radius: Q
    computational_radius: Q
    source_ids: tuple
    units: str = 'model_output'
    horizon: int = 0
    domain_id: str = 'zero-reset-fixed-input'
    def __post_init__(self):
        for name in ('center','physical_radius','computational_radius'):
            object.__setattr__(self,name,exact(getattr(self,name)))
        if self.physical_radius<0 or self.computational_radius<0:raise ValueError('nonnegative radii required')
        if type(self.horizon) is not int or self.horizon<0:raise ValueError('nonnegative horizon required')
        object.__setattr__(self,'source_ids',tuple(self.source_ids))
        if not self.source_ids or any(not isinstance(s,str) or not s for s in self.source_ids):raise ValueError('source IDs required')
        if not self.units or not self.domain_id:raise ValueError('units and domain required')
    @property
    def radius(self):return self.physical_radius+self.computational_radius
    @property
    def lower(self):return self.center-self.radius
    @property
    def upper(self):return self.center+self.radius


def compose_reading_contract(center,physical_radius,*,source_error=0,transformation_error=0,reduction_error=0,execution_error=0,source_ids,units='model_output',horizon=0,domain_id='zero-reset-fixed-input'):
    errors=tuple(map(exact,(source_error,transformation_error,reduction_error,execution_error)))
    if any(v<0 for v in errors):raise ValueError('nonnegative individual error bounds required')
    return BoundedReading(center,physical_radius,sum(errors,Q(0)),tuple(source_ids),units,horizon,domain_id)


@dataclass(frozen=True)
class EvaluatorOption:
    identifier: str
    candidate_id: str
    sensor_ids: tuple
    domain_id: str
    arithmetic_protocol: str
    rank: int
    setup_key: str
    setup_cost: Q
    run_cost: Q
    bound_receipt: dict
    reading: BoundedReading
    def __post_init__(self):
        for name in ('identifier','candidate_id','domain_id','setup_key'):
            if not isinstance(getattr(self,name),str) or not getattr(self,name):raise ValueError('nonempty binding labels required')
        if self.arithmetic_protocol not in ('exact_rational','binary64_exact_dot','binary64_sequential'):
            raise ValueError('unsupported executable arithmetic protocol')
        if type(self.rank) is not int or self.rank<1:raise ValueError('positive rank required')
        for name in ('setup_cost','run_cost'):
            object.__setattr__(self,name,exact(getattr(self,name)))
            if getattr(self,name)<0:raise ValueError('nonnegative accounting costs required')
        if not isinstance(self.reading,BoundedReading) or self.reading.domain_id!=self.domain_id:raise ValueError('reading/domain mismatch')
        receipt=self.bound_receipt
        required={'source_id','candidate_id','sensor_ids','domain_id','horizon','units','arithmetic_protocol','rank','setup_binding'}
        if not isinstance(receipt,dict) or not required<=receipt.keys():raise ValueError('complete bound-source binding required')
        if receipt['source_id'] not in self.reading.source_ids or receipt['candidate_id']!=self.candidate_id or tuple(receipt['sensor_ids'])!=tuple(self.sensor_ids) or receipt['domain_id']!=self.domain_id or receipt['horizon']!=self.reading.horizon or receipt['units']!=self.reading.units or receipt['arithmetic_protocol']!=self.arithmetic_protocol or receipt['rank']!=self.rank:
            raise ValueError('stale or incompatible bound receipt')
        if not isinstance(receipt['setup_binding'],str) or not receipt['setup_binding']:raise ValueError('setup fingerprint required')


def bind_evaluator(option,source):
    if not isinstance(option,EvaluatorOption):raise TypeError('EvaluatorOption required')
    if option.bound_receipt['source_id']!=source.get('source_id'):raise ValueError('orphaned source ID')
    for key in ('candidate_id','sensor_ids','domain_id','horizon','units'):
        a=option.bound_receipt[key];b=source.get(key)
        if key=='sensor_ids':a,b=tuple(a),tuple(b or ())
        if a!=b:raise ValueError('source contract mismatch: '+key)
    return option


@dataclass(frozen=True)
class FidelityExperiment:
    identifier: str
    physical_cost: Q
    options: tuple
    protocol: tuple = ()
    def __post_init__(self):
        object.__setattr__(self,'physical_cost',exact(self.physical_cost))
        if not self.identifier or self.physical_cost<0:raise ValueError('identifier/nonnegative physical cost required')
        if not self.options or any(not group for group in self.options):raise ValueError('one nonempty evaluator menu per candidate required')


@dataclass(frozen=True)
class FidelityPanelResult:
    status: str
    total_cost: Q | None
    installation_cost: Q | None
    repeated_cost: Q | None
    selected: tuple
    separated_pairs: tuple
    nodes: int
    tied_plans: tuple
    scope: str = 'finite supplied menu and declared accounting horizon'


def minimum_fidelity_panel(experiments,candidate_ids,*,target_labels=None,deployments=1,max_nodes=1000000,adapter=None):
    experiments=tuple(experiments);ids=tuple(candidate_ids);labels=ids if target_labels is None else tuple(target_labels)
    if len(set(ids))!=len(ids) or len(ids)<2 or len(labels)!=len(ids):raise ValueError('distinct candidates and matching targets required')
    if type(deployments) is not int or deployments<1 or type(max_nodes) is not int or max_nodes<1:raise ValueError('positive deployment and node budgets required')
    if len({e.identifier for e in experiments})!=len(experiments):raise ValueError('duplicate experiment ID')
    pairs=tuple((a,b) for a in range(len(ids)) for b in range(a+1,len(ids)) if labels[a]!=labels[b]);full=(1<<len(pairs))-1
    setups={};variants=[];checked_upstream=set()
    for e in experiments:
        if len(e.options)!=len(ids):raise ValueError('candidate menu dimensions differ')
        for i,group in enumerate(e.options):
            for o in group:
                if isinstance(o,EvaluatorOption):
                    o.__post_init__()
                    if 'upstream' in o.bound_receipt and id(o) not in checked_upstream:
                        replay_dynacomp_option(o,adapter)
                        checked_upstream.add(id(o))
                if not isinstance(o,EvaluatorOption) or o.candidate_id!=ids[i]:raise ValueError('evaluator/candidate mismatch')
                value=(o.setup_cost,o.bound_receipt['setup_binding'])
                if o.setup_key in setups and setups[o.setup_key]!=value:raise ValueError('incompatible shared setup key')
                setups[o.setup_key]=value
        rows=[]
        for assignment in product(*e.options):
            if len({tuple(o.sensor_ids) for o in assignment})!=1:raise ValueError('one physical experiment requires matching sensor identities')
            readings=tuple(o.reading for o in assignment)
            if len({(r.units,r.horizon,r.domain_id) for r in readings})!=1:raise ValueError('incompatible reading units/horizon/domain')
            mask=sum(1<<k for k,(a,b) in enumerate(pairs) if abs(readings[a].center-readings[b].center)>readings[a].radius+readings[b].radius)
            if mask:rows.append((mask,assignment,e.physical_cost+sum((o.run_cost for o in assignment),Q(0))))
        variants.append(tuple(rows))
    nodes=0;exhausted=False;best=None;ties=[]
    def search(i,mask,keys,run,selected):
        nonlocal nodes,exhausted,best,ties
        if nodes>=max_nodes:exhausted=True;return
        nodes+=1;setup=sum((setups[k][0] for k in keys),Q(0));cost=setup+deployments*run
        if best is not None and cost>best:return
        if mask==full:
            plan=(tuple(selected),setup,run)
            if best is None or cost<best:best=cost;ties=[plan]
            elif cost==best and plan not in ties:ties.append(plan)
            return
        if i==len(experiments):return
        search(i+1,mask,keys,run,selected)
        for added,assignment,price in variants[i]:
            search(i+1,mask|added,keys|{o.setup_key for o in assignment},run+price,selected+[(experiments[i].identifier,tuple(o.identifier for o in assignment))])
    search(0,0,set(),Q(0),[])
    if best is None:return FidelityPanelResult('resource_limit' if exhausted else 'unseparable',None,None,None,(),(),nodes,())
    ties.sort(key=lambda p:p[0]);selected,setup,run=ties[0]
    return FidelityPanelResult('optimality_unresolved' if exhausted else 'optimal',best,setup,deployments*run,selected,tuple((ids[a],ids[b]) for a,b in pairs),nodes,tuple(p[0] for p in ties))


def replay_fidelity_result(experiments,candidate_ids,result,**kwargs):
    fresh=minimum_fidelity_panel(experiments,candidate_ids,**kwargs)
    if result!=fresh:raise ValueError('fidelity plan does not replay')
    return True


def certify_dynacomp_option(candidate,sensor,word,rank,*,arithmetic_protocol='exact_rational',physical_radius=0,setup_cost=0,run_cost=0,adapter=None,force_full=False):
    """Rebuild the actual candidate/sensor/input certificate; no transplanted bound.

    Rank is a maximum requested enrichment rank. The retained actual rank is
    authoritative. Rejected upstream tolerances remain in the evidence.
    """
    adapter=adapter or bundled_adapter();word=tuple(map(exact,word));n=candidate.dimension
    if type(sensor) is not int or not 0<=sensor<len(candidate.sensors):raise ValueError('valid sensor required')
    if arithmetic_protocol not in ('exact_rational','binary64_exact_dot'):raise ValueError('this adapter supports exact and exact-dot binary64 only')
    uniform=adapter.module('uniform');r=adapter.module('rational')
    spec={'n':n,'entries':[[i,j,str(v)] for i,j,v in candidate.entries], 'B':[[str(v)] for v in candidate.heater], 'C':[[str(v) for v in candidate.sensors[sensor]]]}
    model=uniform.SparseLinearModel.from_spec(spec)
    zeros=(Q(0),)*n;centers=tuple((v,) for v in word);radii=((Q(0),),)*len(word)
    if type(force_full) is not bool:raise TypeError('force_full must be bool')
    if force_full and rank!=n:raise ValueError('full exact source requires rank equal to source dimension')
    seeds=tuple(tuple(Q(int(i==j)) for j in range(n)) for i in range(n)) if force_full else None
    reduction=uniform.uniform_enrichment(model,zeros,zeros,radii,Q(0),input_centers=centers,max_rank=rank,strategy='prefix',seed_rows=seeds)
    uniform.replay_uniform(reduction)
    E,G,H,D=map(r.matrix,(reduction[k] for k in ('E','G','H','D')))
    z=r.mv(E,zeros)
    for u in centers:z=r.addv(r.mv(G,z),r.mv(H,u))
    center=r.mv(D,z)[0];execution_error=Q(0);execution=None
    if arithmetic_protocol=='binary64_exact_dot':
        machine=adapter.module('machine');binary=adapter.module('binary64')
        execution=machine.certify_execution(E,G,H,D,zeros,zeros,radii,Q(1),centers)
        machine.replay_execution(execution)
        bits=machine.Binary64Runtime(execution).simulate_bits(tuple(binary.round_bits(v) for v in zeros),tuple(tuple(binary.round_bits(v) for v in row) for row in centers))
        center=binary.exact(bits[-1][0]);execution_error=Q(execution['output_error_upper'][-1][0])
    reduction_error=Q(reduction['certificate']['output_bounds'][-1][0])
    domain_id='fixed-input:'+_digest((zeros,zeros,word,radii))
    source_id=_digest((spec,domain_id,adapter.binding()))
    reading=compose_reading_contract(center,physical_radius,reduction_error=reduction_error,execution_error=execution_error,source_ids=(source_id,),horizon=len(word),domain_id=domain_id)
    binding={'source_id':source_id,'candidate_id':candidate.identifier,'sensor_ids':(str(sensor),),'domain_id':domain_id,'horizon':len(word),'units':'model_output','arithmetic_protocol':arithmetic_protocol,'rank':reduction['rank'],'setup_binding':_digest((spec,reduction['E'],arithmetic_protocol,domain_id,adapter.binding())), 'upstream':adapter.binding(),'source_spec':spec,'word':tuple(str(v) for v in word),'reduction':reduction,'execution':execution,'reduction_error':str(reduction_error),'execution_error':str(execution_error),'source_error':'0','transformation_error':'0','force_full':force_full}
    identifier=f'{candidate.identifier}:s{sensor}:r{reduction["rank"]}:{arithmetic_protocol}'
    return EvaluatorOption(identifier,candidate.identifier,(str(sensor),),domain_id,arithmetic_protocol,reduction['rank'],binding['setup_binding'],setup_cost,run_cost,binding,reading)


def replay_dynacomp_option(option,adapter=None):
    adapter=adapter or bundled_adapter();p=option.bound_receipt
    if adapter.binding()!=p['upstream']:raise ValueError('source-pinned DynaComp mismatch')
    adapter.module('uniform').replay_uniform(p['reduction'])
    if p['execution'] is not None:adapter.module('machine').replay_execution(p['execution'])
    # Recompute the complete option including centres, domains and exact envelope.
    from .thermal_diagnostics import AffineCandidate
    spec=p['source_spec'];candidate=AffineCandidate(option.candidate_id,spec['n'],tuple((i,j,Q(v)) for i,j,v in spec['entries']),tuple(Q(row[0]) for row in spec['B']),(tuple(Q(v) for v in spec['C'][0]),))
    fresh=certify_dynacomp_option(candidate,0,tuple(Q(v) for v in p['word']),p['reduction']['max_rank'],arithmetic_protocol=option.arithmetic_protocol,physical_radius=option.reading.physical_radius,setup_cost=option.setup_cost,run_cost=option.run_cost,adapter=adapter,force_full=p.get('force_full',False))
    # Sensor label in source is a provenance label; fresh single-output model uses 0.
    comparable=dict(p);reconstructed=dict(fresh.bound_receipt)
    for item in (comparable,reconstructed):item.pop('sensor_ids',None)
    if comparable!=reconstructed or option.reading!=fresh.reading:raise ValueError('fidelity option does not reconstruct')
    return True
