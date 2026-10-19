"""Complete finite DFA/resource protocol populations with exact original-word ranks."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from functools import lru_cache
from math import lcm
from .dynacomp_adapter import exact

@dataclass(frozen=True)
class ProtocolAlphabet:
    identifiers: tuple
    amplitudes: tuple
    costs: tuple
    increments: tuple
    def __post_init__(self):
        n=len(self.identifiers)
        if not n or len(set(self.identifiers))!=n or any(not isinstance(s,str) or not s for s in self.identifiers):raise ValueError('distinct nonempty symbol IDs required')
        if any(len(v)!=n for v in (self.amplitudes,self.costs,self.increments)):raise ValueError('alphabet dimensions differ')
        object.__setattr__(self,'amplitudes',tuple(map(exact,self.amplitudes)));object.__setattr__(self,'costs',tuple(map(exact,self.costs)))
        if any(c<=0 for c in self.costs):raise ValueError('strictly positive per-step cost required')
        increments=tuple(tuple(row) for row in self.increments)
        if len({len(row) for row in increments})>1 or any(type(v) is not int or v<0 for row in increments for v in row):raise ValueError('matching nonnegative integer resource vectors required')
        object.__setattr__(self,'increments',increments)

@dataclass(frozen=True)
class DeterministicProtocolGrammar:
    states: tuple
    initial: str
    accepting: tuple
    transitions: tuple
    def validate(self,alphabet):
        if len(set(self.states))!=len(self.states) or not self.states or self.initial not in self.states or not set(self.accepting)<=set(self.states):raise ValueError('invalid DFA states')
        seen=set()
        for q,a,r in self.transitions:
            if q not in self.states or r not in self.states or a not in alphabet.identifiers or (q,a) in seen:raise ValueError('invalid or nondeterministic DFA transition')
            seen.add((q,a))
        return self

@dataclass(frozen=True)
class ProtocolResources:
    budget: Q
    limits: tuple
    horizon: int
    max_switches: int | None = None
    reset_cost: Q = Q(0)
    nonempty: bool = True
    def __post_init__(self):
        object.__setattr__(self,'budget',exact(self.budget));object.__setattr__(self,'reset_cost',exact(self.reset_cost))
        if self.budget<0 or self.reset_cost<0 or type(self.horizon) is not int or self.horizon<0:raise ValueError('nonnegative budgets and integer horizon required')
        if any(type(v) is not int or v<0 for v in self.limits):raise ValueError('nonnegative integer resource limits required')
        if self.max_switches is not None and (type(self.max_switches) is not int or self.max_switches<0):raise ValueError('nonnegative switch limit required')
        if type(self.nonempty) is not bool:raise TypeError('nonempty must be bool')

@dataclass(frozen=True)
class TerminalSensor:
    identifier: str
    cost: Q = Q(0)
    requires: tuple = ()
    def __post_init__(self):
        object.__setattr__(self,'cost',exact(self.cost))
        if not self.identifier or self.cost<0:raise ValueError('sensor ID/nonnegative cost required')

@dataclass(frozen=True)
class Protocol:
    identifier: str
    word: tuple
    sensor: str

class ProtocolPopulation:
    """Termination/sensor first, then alphabet-order depth-first ranking.

    A switch counts only when two consecutive symbols differ. Counting is
    pseudo-polynomial in reachable resource/cost states, not budget bit size.
    """
    def __init__(self,alphabet,grammar,resources,sensors,*,installed=(),max_scale=1000000,max_states=1000000):
        if not isinstance(alphabet,ProtocolAlphabet) or not isinstance(grammar,DeterministicProtocolGrammar) or not isinstance(resources,ProtocolResources):raise TypeError('typed alphabet, DFA and resources required')
        if any(type(v) is not int or v<1 for v in (max_scale,max_states)):raise ValueError('positive integer scale/state budgets required')
        if resources.horizon>256:raise ValueError('resource_limit: horizon exceeds recursive completion budget256')
        grammar.validate(alphabet);sensors=tuple(sensors)
        if not sensors or any(not isinstance(s,TerminalSensor) for s in sensors) or len({s.identifier for s in sensors})!=len(sensors):raise ValueError('distinct terminal sensors required')
        if len(resources.limits)!=len(alphabet.increments[0]):raise ValueError('resource dimensions differ')
        self.alphabet,self.grammar,self.resources=alphabet,grammar,resources
        self.sensors=tuple(s for s in sensors if set(s.requires)<=set(installed));self._all_sensors=sensors
        self.installed=tuple(sorted(installed));self.max_states=max_states
        values=alphabet.costs+(resources.budget,resources.reset_cost)+tuple(s.cost for s in sensors)
        scale=lcm(*(v.denominator for v in values))
        if scale>max_scale:raise ValueError('resource_limit: rational cost scale exceeds max_scale')
        self.scale=scale;self.costs=tuple(int(v*scale) for v in alphabet.costs);self.sensorcost={s.identifier:int(s.cost*scale) for s in self.sensors}
        self._trans={(q,a):r for q,a,r in grammar.transitions}
        self._root=(grammar.initial,int((resources.budget-resources.reset_cost)*scale),tuple(resources.limits),resources.horizon,None,resources.max_switches if resources.max_switches is not None else resources.horizon,0)
        self._memo={};self._entered=set()
    def _terminal(self,state,sensor=None):
        q,b,rs,h,last,sw,used=state
        if b<0 or q not in self.grammar.accepting or (self.resources.nonempty and used==0):return ()
        return tuple(s.identifier for s in self.sensors if (sensor is None or s.identifier==sensor) and self.sensorcost[s.identifier]<=b)
    def _child(self,state,index):
        q,b,rs,h,last,sw,used=state;a=self.alphabet.identifiers[index]
        nxt=self._trans.get((q,a));switch=int(last is not None and last!=a);cost=self.costs[index];inc=self.alphabet.increments[index]
        if nxt is None or h<=0 or cost>b or switch>sw or any(v>r for v,r in zip(inc,rs)):return None
        return (nxt,b-cost,tuple(r-v for r,v in zip(rs,inc)),h-1,a,sw-switch,used+1)
    def _count(self,state,sensor=None):
        key=(state,sensor)
        if key in self._memo:return self._memo[key]
        if key not in self._entered:
            if len(self._entered)>=self.max_states:raise ValueError('resource_limit: completion state budget exceeded')
            self._entered.add(key)
        total=len(self._terminal(state,sensor))
        for i in range(len(self.alphabet.identifiers)):
            child=self._child(state,i)
            if child is not None:total+=self._count(child,sensor)
        self._memo[key]=total;return total
    def _prefix_state(self,prefix):
        state=self._root
        for a in prefix:
            if a not in self.alphabet.identifiers:raise ValueError('unknown protocol symbol')
            state=self._child(state,self.alphabet.identifiers.index(a))
            if state is None:return None
        return state
    def count(self,prefix=()):
        state=self._prefix_state(tuple(prefix))
        return 0 if state is None else self._count(state)
    def conditional_count(self,prefix=(),terminal_sensor=None):
        if terminal_sensor is not None and terminal_sensor not in {s.identifier for s in self._all_sensors}:raise ValueError('unknown terminal sensor')
        state=self._prefix_state(tuple(prefix))
        return 0 if state is None else self._count(state,terminal_sensor)
    def unrank(self,index):
        if type(index) is not int or not 0<=index<self.count():raise ValueError('protocol rank out of range')
        original=index;state=self._root;word=[]
        while True:
            terminals=self._terminal(state)
            if index<len(terminals):return Protocol(f'protocol:{original}',tuple(word),terminals[index])
            index-=len(terminals)
            for i,a in enumerate(self.alphabet.identifiers):
                child=self._child(state,i)
                count=0 if child is None else self._count(child)
                if index<count:word.append(a);state=child;break
                index-=count
            else:raise ArithmeticError('completion rank exhausted unexpectedly')
    def rank(self,protocol):
        if not isinstance(protocol,Protocol):raise TypeError('Protocol required')
        state=self._root;rank=0
        for a in protocol.word:
            if a not in self.alphabet.identifiers:raise ValueError('unknown protocol symbol')
            rank+=len(self._terminal(state));selected=self.alphabet.identifiers.index(a)
            for i in range(selected):
                child=self._child(state,i)
                if child is not None:rank+=self._count(child)
            state=self._child(state,selected)
            if state is None:raise ValueError('illegal protocol')
        terminals=self._terminal(state)
        if protocol.sensor not in terminals:raise ValueError('illegal terminal observation')
        return rank+terminals.index(protocol.sensor)
    def iter_protocols(self,max_members=4096):
        count=self.count()
        if type(max_members) is not int or max_members<count:raise ValueError('resource_limit: explicit protocol population exceeds max_members')
        return (self.unrank(i) for i in range(count))
    def amplitudes(self,protocol):return tuple(self.alphabet.amplitudes[self.alphabet.identifiers.index(a)] for a in protocol.word)
    def cost(self,protocol):
        self.rank(protocol)
        return self.resources.reset_cost+sum((self.alphabet.costs[self.alphabet.identifiers.index(a)] for a in protocol.word),Q(0))+next(s.cost for s in self.sensors if s.identifier==protocol.sensor)
    def compile_pool(self,candidates,max_members=4096,*,sensor_indices=None):
        from .thermal_diagnostics import simulate_protocol
        from .panels import reading_pool
        candidates=tuple(candidates);protocols=tuple(self.iter_protocols(max_members));sensor_ids=tuple(s.identifier for s in self.sensors)
        if sensor_indices is None:
            if any(len(c.sensors)!=len(sensor_ids) for c in candidates):raise ValueError('explicit sensor_indices required for a subset of model channels')
            sensor_indices={name:i for i,name in enumerate(sensor_ids)}
        if set(sensor_indices)!=set(sensor_ids) or any(type(i) is not int or i<0 or any(i>=len(c.sensors) for c in candidates) for i in sensor_indices.values()):raise ValueError('valid explicit terminal sensor channel map required')
        readings=tuple(tuple(simulate_protocol(c,self.amplitudes(p),sensor_indices[p.sensor]) for c in candidates) for p in protocols)
        return reading_pool(tuple(self.cost(p) for p in protocols),readings,labels=tuple(p.identifier for p in protocols),candidates=len(candidates))
    def completion_certificate(self):
        total=self.count();rows=[]
        for (state,sensor),count in sorted(self._memo.items(),key=lambda item:repr(item[0])):
            if sensor is not None:continue
            children=tuple(child for i in range(len(self.alphabet.identifiers)) if (child:=self._child(state,i)) is not None)
            rows.append({'state':state,'count':count,'terminal_count':len(self._terminal(state)),'children':children})
        from dataclasses import asdict
        contract={'alphabet':asdict(self.alphabet),'grammar':asdict(self.grammar),'resources':asdict(self.resources),'sensors':tuple(asdict(s) for s in self._all_sensors),'installed':self.installed}
        return {'schema':'singularity.protocol-population/1','contract':contract,'count':total,'root':self._root,'cost_scale':self.scale,'ordering':'termination sensors in input order, then alphabet-order depth-first','initial_symbol_switch':False,'nodes':rows}


def verify_completion_certificate(population,receipt):
    expected=population.completion_certificate()
    if receipt!=expected:raise ValueError('completion certificate does not reconstruct')
    # Locally replay each DAG equation; horizon strictly decreases on edges.
    rows={tuple((s[0],s[1],tuple(s[2]),s[3],s[4],s[5],s[6])):r for r in receipt['nodes'] for s in (r['state'],)}
    for state,row in rows.items():
        total=row['terminal_count']
        for raw in row['children']:
            child=(raw[0],raw[1],tuple(raw[2]),raw[3],raw[4],raw[5],raw[6])
            if child[3]>=state[3]:raise ValueError('completion DAG does not decrease horizon')
            total+=rows[child]['count']
        if total!=row['count']:raise ValueError('invalid local completion equation')
    return True


def cheapest_robust_protocol(population,reader,candidate_ids,*,radii=0,target_labels=None,max_members=4096):
    """Complete cost-ordered search, retaining one failing pair for every cheaper row.

    The only pruning rule is cost >= incumbent: later sorted protocols cannot
    improve a strictly cheaper objective. No nominal-row dependence pruning.
    """
    ids=tuple(candidate_ids);labels=ids if target_labels is None else tuple(target_labels)
    if len(ids)<2 or len(set(ids))!=len(ids) or len(labels)!=len(ids):raise ValueError('distinct candidates/matching target labels required')
    pairs=tuple((i,j) for i in range(len(ids)) for j in range(i+1,len(ids)) if labels[i]!=labels[j])
    rows=sorted(((population.cost(p),population.rank(p),p) for p in population.iter_protocols(max_members)),key=lambda r:(r[0],r[1]))
    rejected=[];best=None;ties=[]
    for cost,rank,p in rows:
        if best is not None and cost>best:break
        values=tuple(map(exact,reader(p)))
        if len(values)!=len(ids):raise ValueError('reader candidate dimensions differ')
        radius=tuple(map(exact,radii(p))) if callable(radii) else (exact(radii),)*len(ids)
        if len(radius)!=len(ids) or any(r<0 for r in radius):raise ValueError('nonnegative candidate radii required')
        failing=next(((ids[i],ids[j]) for i,j in pairs if abs(values[i]-values[j])<=radius[i]+radius[j]),None)
        if failing is None:best=cost;ties.append({'rank':rank,'protocol':p,'readings':values})
        else:rejected.append({'rank':rank,'cost':cost,'failing_pair':failing})
    return {'status':'optimal' if best is not None else 'unseparable','cost':best,'witnesses':tuple(ties),'excluded_no_more_expensive':tuple(rejected),'population_count':population.count(),'scope':'complete supplied DFA/resource language; one scalar terminal reading'}
