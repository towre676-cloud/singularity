"""Exact recurrence execution, finite modular filters and OEIS prefix discovery.

Formal generating functions and fast values are derived from a supplied
recurrence. Discovery from samples stays prefix evidence, never a definition
proof or complete perfect-power enumeration.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from .core import mul
from . import polyalg as P
from .modular_reconstruction import berlekamp_massey,reconstruct_system


class CycleLimit(ValueError):pass


@dataclass(frozen=True)
class Recurrence:
    coefficients:tuple
    initial:tuple

    def __post_init__(self):
        for xs in (self.coefficients,self.initial):
            if any(type(x) not in (int,Q) for x in xs):
                raise ValueError('exact integer or Fraction recurrence values required')
        c,a=tuple(map(Q,self.coefficients)),tuple(map(Q,self.initial))
        if not c or len(a)!=len(c):raise ValueError('matching nonzero recurrence order required')
        object.__setattr__(self,'coefficients',c);object.__setattr__(self,'initial',a)

    @property
    def order(self):return len(self.coefficients)

    @property
    def annihilator(self):return tuple(-c for c in self.coefficients)+(Q(1),)

    def terms(self,count):
        if type(count) is not int or count<0:raise ValueError('nonnegative term count required')
        out=list(self.initial)
        while len(out)<count:
            out.append(sum(c*x for c,x in zip(self.coefficients,out[-self.order:])))
        return out[:count]

    def nth(self,n):
        """Binary powering of E modulo the monic annihilator, incl. signed n."""
        if type(n) is not int:raise ValueError('integer index required')
        r=self.order;mod=self.annihilator
        if n>=0:base=P.divmod_poly((Q(0),Q(1)),mod)[1]
        else:
            if not self.coefficients[0]:raise ValueError('backward recurrence not invertible')
            # E^-1=(E^(r-1)-sum_(i>=1)c_i E^(i-1))/c_0.
            base=[-self.coefficients[i]/self.coefficients[0] for i in range(1,r)]+[1/self.coefficients[0]]
        value=P.ONE
        for bit in bin(abs(n))[2:]:
            value=P.divmod_poly(mul(value,value),mod)[1]
            if bit=='1':value=P.divmod_poly(mul(value,base),mod)[1]
        return sum(v*self.initial[i] for i,v in enumerate(value))

    def generating_function(self):
        denominator=(Q(1),)+tuple(-c for c in reversed(self.coefficients))
        numerator=tuple(sum(denominator[j]*self.initial[i-j] for j in range(i+1))
                        for i in range(self.order))
        return P.poly(numerator),P.poly(denominator)

    def minimal_generating_function(self):
        """Cancellation-aware OGF, incl. exact sequence realization/minimality."""
        from .generating import from_recurrence
        return from_recurrence(self.coefficients,self.initial)

    def cycle(self,modulus,*,state_limit=100_000):
        if type(modulus) is not int or modulus<2 or type(state_limit) is not int or state_limit<1:
            raise ValueError('modulus>=2 and positive state budget required')
        if any(x.denominator!=1 for x in self.coefficients+self.initial):
            raise ValueError('integral recurrence required for modular dynamics')
        state=tuple(int(x)%modulus for x in self.initial);seen={};states=[]
        while state not in seen:
            if len(states)>=state_limit:raise CycleLimit('no completed modular cycle within budget')
            seen[state]=len(states);states.append(state)
            nxt=sum(int(c)*x for c,x in zip(self.coefficients,state))%modulus
            state=state[1:]+(nxt,)
        start=seen[state]
        return {'modulus':modulus,'states':states,'preperiod':start,
                'period':len(states)-start,'execution_verified':False}

    def residue_filter(self,modulus,accept,*,state_limit=100_000):
        """accept receives the entire modular recurrence state, not just a_n."""
        c=self.cycle(modulus,state_limit=state_limit);mu=c['preperiod']
        return {**c,'prefix_hits':[i for i,s in enumerate(c['states'][:mu]) if accept(s)],
                'cycle_hits':[i for i,s in enumerate(c['states'][mu:]) if accept(s)],
                'scope':'nonnegative indices of this supplied recurrence modulo the stated modulus'}


def filter_count(certificate,stop):
    """Number of accepted indices 0<=n<stop from a completed cycle table."""
    if type(stop) is not int or stop<0:raise ValueError('nonnegative exclusive endpoint required')
    mu,period=certificate['preperiod'],certificate['period']
    if type(mu) is not int or mu<0 or type(period) is not int or period<1:
        raise ValueError('valid preperiod/period required')
    prefix,good=certificate['prefix_hits'],certificate['cycle_hits']
    if len(set(prefix))!=len(prefix) or len(set(good))!=len(good) or any(
        type(j) is not int or not 0<=j<mu for j in prefix) or any(
        type(j) is not int or not 0<=j<period for j in good):raise ValueError('invalid accepted indices')
    length=max(0,stop-mu);blocks,tail=divmod(length,period)
    return sum(i<stop for i in prefix)+blocks*len(good)+sum(i<tail for i in good)


def discover_prefix(terms,*,training_count=None,max_order=8,
                    reconstruction_primes=(1009,1013,1019,1021,1031),
                    heldout_primes=(1061,1063),coefficient_bound=1_000_000):
    """Modular training, bounded rational reconstruction, exact held-out terms.

    Prefix agreement remains evidence even if every supplied term agrees.
    """
    from .local_quartic import _prime
    terms=tuple(terms);train=training_count if training_count is not None else min(32,len(terms)//2)
    if any(type(x) is not int for x in terms):raise ValueError('integer sequence samples required')
    if type(train) is not int or not 4<=train<=len(terms)-4:
        raise ValueError('at least four training and four held-out terms required')
    if type(max_order) is not int or max_order<1 or type(coefficient_bound) is not int or coefficient_bound<1:
        raise ValueError('positive order and coefficient bounds required')
    primes=tuple(reconstruction_primes);held=tuple(heldout_primes)
    if not primes or not held or len(set(primes+held))!=len(primes+held) or any(not _prime(p) for p in primes+held):
        raise ValueError('distinct nonempty reconstruction and held-out prime sets required')
    rows=[berlekamp_massey(terms[:train],p) for p in primes]
    order=len(rows[0])
    if not order or order>max_order or 2*order>train or any(len(row)!=order for row in rows):
        raise ValueError('no stable supported modular recurrence order')
    coefficients=[];reconstruction=[]
    for j in range(order):
        record=reconstruct_system([(row[j],p) for row,p in zip(rows,primes)],coefficient_bound,coefficient_bound)
        coefficients.append(Q(record['value']));reconstruction.append(record)
    model=Recurrence(tuple(coefficients),terms[:order])
    if model.terms(len(terms))!=list(map(Q,terms)):
        raise ValueError('reconstructed recurrence fails exact prefix or held-out terms')
    for p in held:
        modular=tuple(int(c.numerator)*pow(c.denominator,-1,p)%p for c in coefficients)
        if any((terms[n+order]-sum(c*terms[n+i] for i,c in enumerate(modular)))%p
               for n in range(len(terms)-order)):
            raise ValueError('held-out prime mismatch')
    numerator,denominator=model.generating_function()
    return {'status':'PREFIX_RECURRENCE_CANDIDATE','coefficients':list(map(str,coefficients)),
            'initial':list(map(str,model.initial)),'order':order,
            'training_terms':train,'heldout_terms':len(terms)-train,
            'reconstruction_primes':list(primes),'heldout_primes':list(held),
            'reconstruction':reconstruction,'numerator':list(map(str,numerator)),
            'denominator':list(map(str,denominator)),
            'execution_verified':False,'definition_proved':False,
            'scope':f'exact agreement on {len(terms)} supplied terms; no infinite-sequence conclusion'}


def scan_seq_directory(directory,**options):
    """Read actual .seq files, preserving their offsets and source-file hashes."""
    from pathlib import Path
    from hashlib import sha256
    from .oeis_source import parse_seq
    directory=Path(directory);paths=sorted(directory.rglob('*.seq'))
    if not paths:raise ValueError('no staged .seq files found')
    candidates=[];rejections=[]
    for path in paths:
        raw=path.read_bytes();entry=parse_seq(raw.decode('utf-8'))
        provenance={'id':entry.id,'offset':entry.offset,'name':entry.name,
                    'file':str(path.relative_to(directory)),'sha256':sha256(raw).hexdigest()}
        try:result=discover_prefix(entry.terms,**options)
        except ValueError as error:
            rejections.append({**provenance,'reason':str(error)});continue
        from .oeis_dsl import parse_gf
        supplied=parse_gf(entry.name)
        if supplied is not None and entry.offset>=0:
            model=from_generating_function(supplied.P,supplied.Q)
            matches=model.terms(entry.offset+len(entry.terms))[entry.offset:]==list(map(Q,entry.terms))
            result['supplied_GF_bridge']={'source':entry.name,'prefix_matches':matches,
                'coefficients':list(map(str,model.coefficients)),
                'initial':list(map(str,model.initial)),
                'definition_proved':False,'status':'TRANSLATED_SOURCE_GF' if matches else 'REJECTED_TRANSLATION'}
        candidates.append({**provenance,**result})
    return {'files':len(paths),'candidates':candidates,'rejections':rejections,
            'infinite_definitions_proved':0,'execution_verified':False}


def from_generating_function(numerator,denominator):
    """Construct a homogeneous recurrence for any supplied rational formal GF.

    Polynomial numerators of large degree give a finite initial transient,
    encoded by leading zero chronological recurrence coefficients.
    """
    if any(type(x) not in (int,Q) for xs in (numerator,denominator) for x in xs):
        raise ValueError('exact rational GF coefficients required')
    numerator,denominator=P.poly(numerator),P.poly(denominator)
    if not denominator[0]:raise ValueError('formal GF denominator must have nonzero constant term')
    r=max(1,P.degree(denominator),P.degree(numerator)+1)
    initial=[]
    for n in range(r):
        value=numerator[n] if n<len(numerator) else Q(0)
        value-=sum(denominator[j]*initial[n-j] for j in range(1,min(n,len(denominator)-1)+1))
        initial.append(value/denominator[0])
    coefficients=tuple(-denominator[r-i]/denominator[0] if r-i<len(denominator) else Q(0)
                       for i in range(r))
    return Recurrence(coefficients,tuple(initial))
