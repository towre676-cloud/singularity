"""Finite original-object masses, exact exponential tilts and target decisions.

Compression is a pushforward, never a replacement of class masses by one.
Probability assumptions and robust consistency/guarantees remain distinct.
"""
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations,product


def _q(x):
    if isinstance(x,bool) or not isinstance(x,(int,Fraction)):raise TypeError('exact rational required')
    return Fraction(x)


class UnsupportedObservation(ValueError):
    """The declared likelihood assigns zero mass: reject this model observation."""


@dataclass(frozen=True)
class PopulationObject:
    identifier: str
    features: tuple
    target: object
    weight: Fraction=Fraction(1)

    def __post_init__(self):
        if not isinstance(self.identifier,str) or not self.identifier:raise ValueError('original ID required')
        f=tuple(self.features)
        if any(isinstance(x,bool) or not isinstance(x,int) for x in f):raise TypeError('integer features required')
        w=_q(self.weight)
        if w<0:raise ValueError('negative original weight')
        hash(self.target)
        object.__setattr__(self,'features',f);object.__setattr__(self,'weight',w)


class WeightedPopulation:
    def __init__(self,objects,finiteness_certificate='explicit finite original ID list'):
        self.objects=tuple(objects)
        if not self.objects or any(not isinstance(o,PopulationObject) for o in self.objects):raise ValueError('finite PopulationObject list required')
        self.original_ids=tuple(o.identifier for o in self.objects)
        if len(set(self.original_ids))!=len(self.objects):raise ValueError('original IDs must be unique')
        self.dimension=len(self.objects[0].features)
        if any(len(o.features)!=self.dimension for o in self.objects):raise ValueError('feature dimension mismatch')
        if not any(o.weight for o in self.objects):raise ValueError('zero total original mass')
        if not isinstance(finiteness_certificate,str) or not finiteness_certificate:raise ValueError('finiteness certificate required')
        self.finiteness_certificate=finiteness_certificate

    def count(self):return len(self.objects)
    def rank(self,identifier):
        try:return self.original_ids.index(identifier)
        except ValueError as exc:raise ValueError('unknown original object') from exc
    def unrank(self,index):
        if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(self.objects):raise ValueError('rank outside original population')
        return self.objects[index]


def pushforward_mass(population):
    out={}
    for o in population.objects:out[o.features]=out.get(o.features,Fraction())+o.weight
    return out


def joint_target_mass(population):
    out={}
    for o in population.objects:
        key=o.features,o.target;out[key]=out.get(key,Fraction())+o.weight
    return out


def _tilted_weights(population,tilt=None):
    tilt=(Fraction(1),)*population.dimension if tilt is None else tuple(map(_q,tilt))
    if len(tilt)!=population.dimension or any(t<=0 for t in tilt):raise ValueError('positive rational tilt of correct dimension required')
    weights=[]
    for o in population.objects:
        w=o.weight
        for t,f in zip(tilt,o.features):w*=t**f
        weights.append(w)
    Z=sum(weights,Fraction())
    return tuple(weights),Z


def tilted_moments(population,tilt=None):
    weights,Z=_tilted_weights(population,tilt);d=population.dimension
    mean=tuple(sum((w*o.features[i] for o,w in zip(population.objects,weights)),Fraction())/Z for i in range(d))
    covariance=tuple(tuple(sum((w*(o.features[i]-mean[i])*(o.features[j]-mean[j])
                                for o,w in zip(population.objects,weights)),Fraction())/Z for j in range(d)) for i in range(d))
    return {'normalization':Z,'mean':mean,'covariance':covariance,
            'original_count':population.count(),'compressed_keys':len(pushforward_mass(population)),
            'target_keys':len(joint_target_mass(population)),
            'probabilities':tuple(w/Z for w in weights),'original_ids':population.original_ids}


@dataclass(frozen=True)
class FiniteObservationChannel:
    identifier: str
    alphabet: tuple
    likelihoods: tuple
    cost: Fraction=Fraction(1)

    def __post_init__(self):
        if not isinstance(self.identifier,str) or not self.identifier:raise ValueError('channel ID required')
        alphabet=tuple(self.alphabet)
        if not alphabet or len(set(alphabet))!=len(alphabet):raise ValueError('observation labels must be distinct')
        rows=tuple((identifier,tuple(map(_q,row))) for identifier,row in self.likelihoods)
        if len({i for i,_ in rows})!=len(rows):raise ValueError('duplicate original likelihood ID')
        if any(len(row)!=len(alphabet) or any(p<0 for p in row) or sum(row)!=1 for _,row in rows):
            raise ValueError('likelihood rows must be normalized nonnegative rationals')
        cost=_q(self.cost)
        if cost<=0:raise ValueError('positive declared experiment cost required')
        object.__setattr__(self,'alphabet',alphabet);object.__setattr__(self,'likelihoods',rows);object.__setattr__(self,'cost',cost)

    def table(self,population):
        table=dict(self.likelihoods)
        if set(table)!=set(population.original_ids):raise ValueError('channel must cover every original ID exactly')
        return table


def verify_channel_compression(population,channel,target_enriched=False):
    table=channel.table(population);groups={}
    for o in population.objects:
        key=(o.features,o.target) if target_enriched else o.features
        if key in groups and groups[key]!=table[o.identifier]:raise ValueError('compressed key is insufficient for this observation channel')
        groups[key]=table[o.identifier]
    return True


def posterior_target(population,channel,observation,tilt=None):
    table=channel.table(population)
    try:j=channel.alphabet.index(observation)
    except ValueError as exc:raise UnsupportedObservation('observation outside declared model alphabet') from exc
    weights,Z=_tilted_weights(population,tilt);target={}
    for o,w in zip(population.objects,weights):target[o.target]=target.get(o.target,Fraction())+w*table[o.identifier][j]
    total=sum(target.values(),Fraction())
    if not total:raise UnsupportedObservation('zero-probability observation: reject declared model')
    return {'observation_probability':total/Z,'target_probabilities':{t:w/total for t,w in target.items()},
            'original_ids':population.original_ids}


def target_risk(population,channel,tilt=None):
    table=channel.table(population);weights,Z=_tilted_weights(population,tilt)
    correct=Fraction()
    for j in range(len(channel.alphabet)):
        masses={}
        for o,w in zip(population.objects,weights):masses[o.target]=masses.get(o.target,Fraction())+w*table[o.identifier][j]
        correct+=max(masses.values())
    return 1-correct/Z


def _panel_channel(population,channels,max_outcomes):
    if not channels:
        return FiniteObservationChannel('empty',('no_observation',),tuple((i,(1,)) for i in population.original_ids))
    tables=[c.table(population) for c in channels]
    expected=1
    for c in channels:
        expected*=len(c.alphabet)
        if expected>max_outcomes:raise ValueError('panel outcome resource limit')
    outcomes=tuple(product(*(range(len(c.alphabet)) for c in channels)))
    if len(outcomes)>max_outcomes:raise ValueError('panel outcome resource limit')
    rows=[]
    for identifier in population.original_ids:
        ps=[]
        for js in outcomes:
            p=Fraction(1)
            for table,j in zip(tables,js):p*=table[identifier][j]
            ps.append(p)
        rows.append((identifier,tuple(ps)))
    return FiniteObservationChannel('+'.join(c.identifier for c in channels),outcomes,tuple(rows),sum((c.cost for c in channels),Fraction()))


def minimum_expected_target_risk(population,channels,budget,tilt=None,max_channels=16,max_outcomes=100000):
    channels=tuple(channels);budget=_q(budget)
    if budget<0 or len(channels)>max_channels or len({c.identifier for c in channels})!=len(channels):raise ValueError('invalid finite design problem')
    best=None;checked=0
    for size in range(len(channels)+1):
        for inds in combinations(range(len(channels)),size):
            cost=sum((channels[i].cost for i in inds),Fraction())
            if cost>budget:continue
            panel=tuple(channels[i] for i in inds);channel=_panel_channel(population,panel,max_outcomes)
            risk=target_risk(population,channel,tilt);checked+=1
            item=(risk,cost,tuple(c.identifier for c in panel))
            if best is None or item<best:best=item
    return {'risk':best[0],'cost':best[1],'panel':best[2],'checked_feasible_panels':checked,
            'original_ids':population.original_ids,'original_mass':sum((o.weight for o in population.objects),Fraction()),
            'assumptions':'declared rational prior; zero-one target loss; conditional independent panel readings'}


def deterministic_minimax_risk(population,channel,max_rules=100000):
    """Worst original-object conditional error over deterministic target rules.

    This declared decision class excludes randomized decision rules. It does
    not use prior weights and hence differs from population Bayes risk.
    """
    table=channel.table(population);targets=tuple(dict.fromkeys(o.target for o in population.objects))
    rules=len(targets)**len(channel.alphabet)
    if rules>max_rules:raise ValueError('decision rule resource limit')
    best=None
    for rule in product(targets,repeat=len(channel.alphabet)):
        errors=tuple(1-sum((p for label,p in zip(rule,table[o.identifier]) if label==o.target),Fraction()) for o in population.objects)
        item=(max(errors),tuple(targets.index(t) for t in rule))
        if best is None or item<best:best=item
    return {'risk':best[0],'rule':tuple(targets[i] for i in best[1]),'rules_checked':rules,
            'scope':'deterministic decisions; worst original object; no prior averaging'}
