"""Finite residue experiments for declared quadratic-unit seed populations.

No completeness statement about global Pell seeds is made. Stable original
seed IDs survive both modular collisions and behavioral quotienting.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from math import isqrt
from .observability import OperatorSystem, observable_closure, minimum_distinguishing_experiment


def _int(x):
    if isinstance(x,bool) or not isinstance(x,int):raise TypeError('integer required')
    return x


def _q(x):
    if isinstance(x,bool) or not isinstance(x,(int,Fraction)):raise TypeError('exact rational required')
    return Fraction(x)


def _mm(A,B,m):return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(2))%m for j in range(2)) for i in range(2))

def _mpow(A,k,m):
    R=((1%m,0),(0,1%m))
    while k:
        if k&1:R=_mm(R,A,m)
        A=_mm(A,A,m);k//=2
    return R


@dataclass(frozen=True)
class QuadraticUnit:
    D:int
    a:int
    b:int
    def __post_init__(self):
        for v in (self.D,self.a,self.b):_int(v)
        if self.D<=0 or isqrt(self.D)**2==self.D:raise ValueError('D must be positive nonsquare')
        if self.a*self.a-self.D*self.b*self.b!=1:raise ValueError('unit must have norm one')
    @property
    def matrix(self):return ((self.a,self.D*self.b),(self.b,self.a))
    def apply(self,v):
        x,y=tuple(_int(z) for z in v)
        return (self.a*x+self.D*self.b*y,self.b*x+self.a*y)
    def norm(self,v):
        x,y=tuple(_int(z) for z in v);return x*x-self.D*y*y
    def inverse(self):return QuadraticUnit(self.D,self.a,-self.b)


class ResidueOrbitSystem:
    """Orbit closure of supplied seed images under explicitly legal actions.

    ``seeds`` is a mapping stable ID -> original integer pair. Actions are
    named QuadraticUnit objects or ``'conjugation'``; conjugation requires
    ``signed_states=True``. Sensors are x, y or norm, read modulo modulus.
    Every sensor output symbol gets an exact indicator observation row.
    """
    def __init__(self,unit,modulus,seeds,*,actions=None,observations=('y',),
                 action_costs=None,observation_costs=None,signed_states=False,
                 max_states=512,max_dense_states=128,provenance='user-declared finite seeds'):
        if not isinstance(unit,QuadraticUnit):raise TypeError('certified unit required')
        self.unit=unit;self.modulus=_int(modulus)
        if self.modulus<1:raise ValueError('positive modulus required')
        if not isinstance(seeds,dict) or not seeds:raise ValueError('nonempty stable-ID seed map required')
        self.seeds={}
        for sid,v in seeds.items():
            if not isinstance(sid,str) or not sid:raise ValueError('nonempty string seed IDs required')
            v=tuple(_int(z) for z in v)
            if len(v)!=2:raise ValueError('seed pair required')
            self.seeds[sid]=v
        self.actions=dict({'unit':unit} if actions is None else actions)
        if not self.actions:raise ValueError('at least one action required')
        for name,a in self.actions.items():
            if not isinstance(name,str) or not name:raise ValueError('named actions required')
            if a=='conjugation':
                if not signed_states:raise ValueError('conjugation requires signed-state contract')
            elif not isinstance(a,QuadraticUnit) or a.D!=unit.D:raise ValueError('actions must be units in the same quadratic field')
        if type(signed_states) is not bool:raise TypeError('signed_states must be a bool')
        self.action_names=tuple(self.actions);self.signed_states=signed_states
        self.observations=tuple(observations)
        if any(s not in ('x','y','norm') for s in self.observations):raise ValueError('unknown residue sensor')
        self.action_costs=tuple(_q(v) for v in ([1]*len(self.actions) if action_costs is None else action_costs))
        self.observation_costs=tuple(_q(v) for v in (observation_costs if observation_costs is not None else [0]*len(self.observations)))
        if len(self.action_costs)!=len(self.actions) or any(c<=0 for c in self.action_costs):raise ValueError('positive action costs required')
        if len(self.observation_costs)!=len(self.observations) or any(c<0 for c in self.observation_costs):raise ValueError('nonnegative sensor costs required')
        self.max_states=_int(max_states);self.max_dense_states=_int(max_dense_states)
        if min(self.max_states,self.max_dense_states)<1:raise ValueError('positive resource limits required')
        states=set(tuple(z%self.modulus for z in v) for v in self.seeds.values())
        if len(states)>self.max_states:raise ArithmeticError('initial residue seed-state budget exhausted')
        queue=list(sorted(states));i=0
        while i<len(queue):
            s=queue[i];i+=1
            for a in self.actions.values():
                t=self._action(a,s)
                if t not in states:
                    states.add(t);queue.append(t)
                    if len(states)>self.max_states:raise ArithmeticError('residue orbit-state budget exhausted')
        self.states=tuple(sorted(states));self.index={s:i for i,s in enumerate(self.states)}
        self.seed_states={sid:self.index[tuple(z%self.modulus for z in v)] for sid,v in self.seeds.items()}
        self.transitions=tuple(tuple(self.index[self._action(a,s)] for s in self.states) for a in self.actions.values())
        if not isinstance(provenance,str):raise TypeError('provenance must be a string')
        self.provenance=provenance
    def _action(self,a,s):
        v=(s[0],-s[1]) if a=='conjugation' else a.apply(s)
        return tuple(z%self.modulus for z in v)
    def sensor(self,state,name):
        x,y=state
        return (x if name=='x' else y if name=='y' else x*x-self.unit.D*y*y)%self.modulus
    def compile_operator_system(self):
        n=len(self.states)
        if n>self.max_dense_states:raise ArithmeticError('dense one-hot matrix budget exhausted')
        ops=tuple(tuple(tuple(int(i==t[j]) for j in range(n)) for i in range(n)) for t in self.transitions)
        rows=[];costs=[];labels=[]
        for j,sensor in enumerate(self.observations):
            vals=tuple(self.sensor(s,sensor) for s in self.states)
            for symbol in sorted(set(vals)):
                rows.append(tuple(int(v==symbol) for v in vals));costs.append(self.observation_costs[j]);labels.append((j,symbol))
        self.observation_labels=tuple(labels)
        return OperatorSystem(n,ops,rows,self.action_costs,costs)
    def behavioral_classes(self):
        system=self.compile_operator_system();cert=observable_closure(system);groups={}
        for i in range(len(self.states)):
            signature=tuple(e.row[i] for e in cert.basis);groups.setdefault(signature,[]).append(i)
        classes=tuple(tuple(g) for g in sorted(groups.values(),key=lambda g:g[0]))
        state_class={s:j for j,g in enumerate(classes) for s in g}
        return {'classes':classes,'state_to_class':tuple(state_class[i] for i in range(len(self.states))),
                'seed_to_class':{sid:state_class[i] for sid,i in self.seed_states.items()},'rank':cert.rank}
    def cheapest_witness(self,first_seed,second_seed):
        s=self.compile_operator_system();d=[0]*len(self.states);d[self.seed_states[first_seed]]+=1;d[self.seed_states[second_seed]]-=1
        e=minimum_distinguishing_experiment(s,d)
        if e is None:return None
        sensor,symbol=self.observation_labels[e.observation]
        return {'word':e.word,'actions':tuple(self.action_names[i] for i in e.word),'sensor':self.observations[sensor],
                'symbol':symbol,'cost':e.cost,'difference':sum(a*b for a,b in zip(e.row,d))}
    def cycle(self,seed):
        v=self.seeds[seed] if isinstance(seed,str) else tuple(seed);s=tuple(z%self.modulus for z in v);seen={};orbit=[]
        while s not in seen:
            seen[s]=len(orbit);orbit.append(s);s=tuple(z%self.modulus for z in self.unit.apply(s))
            if len(orbit)>self.max_states:raise ArithmeticError('cycle-state budget exhausted')
        return {'preperiod':seen[s],'cycle':tuple(orbit[seen[s]:]),'prefix':tuple(orbit[:seen[s]])}
    def remote_residue(self,seed,index,*,allow_negative=False):
        """Decimal-stream matrix powering avoids constructing a huge index int."""
        v=self.seeds[seed] if isinstance(seed,str) else tuple(_int(z) for z in seed)
        if len(v)!=2:raise ValueError('seed pair required')
        if isinstance(index,bool) or not isinstance(index,(int,str)):raise TypeError('integer or decimal index required')
        if isinstance(index,int):negative=index<0;digits=str(abs(index))
        else:
            negative=index.startswith('-');digits=index[1:] if negative else index
            if not digits or any(c not in '0123456789' for c in digits):raise ValueError('canonical decimal digits required')
        if negative and not allow_negative:raise ValueError('negative indices require inverse-action contract')
        U=(self.unit.inverse() if negative else self.unit).matrix;m=self.modulus;R=((1%m,0),(0,1%m))
        for c in digits:R=_mm(_mpow(R,10,m),_mpow(U,ord(c)-48,m),m)
        return tuple(sum(R[i][j]*v[j] for j in range(2))%m for i in range(2))
    def receipt(self):
        return {'schema':'singularity.arithmetic-orbit/1','D':self.unit.D,'unit':[self.unit.a,self.unit.b],
                'modulus':self.modulus,'seeds':{sid:list(v) for sid,v in self.seeds.items()},
                'seed_norms':{sid:self.unit.norm(v) for sid,v in self.seeds.items()},'provenance':self.provenance,
                'states':[list(s) for s in self.states],'seed_to_modular_state':self.seed_states,
                'actions':{name:('conjugation' if a=='conjugation' else [a.a,a.b]) for name,a in self.actions.items()},
                'action_costs':[[v.numerator,v.denominator] for v in self.action_costs],
                'observations':list(self.observations),'observation_costs':[[v.numerator,v.denominator] for v in self.observation_costs],
                'transitions':[list(t) for t in self.transitions],'signed_states':self.signed_states,
                'limits':{'max_states':self.max_states,'max_dense_states':self.max_dense_states},
                'scope':'finite declared seed images and generated residue closure; no global Pell completeness'}


def replay_arithmetic_receipt(receipt):
    try:
        r=receipt;u=QuadraticUnit(r['D'],*r['unit'])
        acts={name:('conjugation' if a=='conjugation' else QuadraticUnit(u.D,*a)) for name,a in r['actions'].items()}
        obj=ResidueOrbitSystem(u,r['modulus'],r['seeds'],actions=acts,observations=r['observations'],
              action_costs=[Fraction(*v) for v in r['action_costs']],observation_costs=[Fraction(*v) for v in r['observation_costs']],
              signed_states=r['signed_states'],provenance=r['provenance'],max_states=r['limits']['max_states'],max_dense_states=r['limits']['max_dense_states'])
        return obj.receipt()==r
    except (TypeError,ValueError,KeyError,ArithmeticError):return False
