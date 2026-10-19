"""NX35 proof-directed finite scalar-box refinement with exact cover bounds."""
from __future__ import annotations
from dataclasses import dataclass,replace
from fractions import Fraction as Q
from .period_observations import _q


@dataclass(frozen=True)
class MarginEnclosure:
    experiment_id: str
    pair: tuple
    lower: Q
    upper: Q
    fidelity: int = 0
    binding: tuple = ()

    def __post_init__(self):
        object.__setattr__(self,"lower",_q(self.lower))
        object.__setattr__(self,"upper",_q(self.upper))
        if not self.experiment_id or len(self.pair)!=2 or any(type(v)is not int or v<0 for v in self.pair) or self.pair[0]>=self.pair[1]:
            raise ValueError("experiment and ordered candidate pair required")
        if self.lower>self.upper or type(self.fidelity)is not int or self.fidelity<0:
            raise ValueError("ordered endpoints and nonnegative fidelity required")
        if not isinstance(self.binding,tuple):raise TypeError("immutable binding tuple required")


@dataclass(frozen=True)
class RefinementProblem:
    experiment_ids: tuple
    costs: tuple
    candidate_ids: tuple
    pairs: tuple
    margins: tuple
    target_labels: tuple

    def __init__(self,experiment_ids,costs,candidate_ids,margins,target_labels=None):
        ids=tuple(experiment_ids);costs=tuple(map(_q,costs));candidates=tuple(candidate_ids)
        labels=candidates if target_labels is None else tuple(target_labels)
        if len(candidates)<2 or len(set(candidates))!=len(candidates) or len(labels)!=len(candidates):
            raise ValueError("distinct original candidates and matching target map required")
        if len(ids)!=len(costs) or len(set(ids))!=len(ids) or any(c<=0 for c in costs):
            raise ValueError("distinct experiments and positive costs required")
        pairs=tuple((a,b)for a in range(len(candidates))for b in range(a+1,len(candidates))if labels[a]!=labels[b])
        margins=tuple(tuple(row)for row in margins)
        if len(margins)!=len(ids):raise ValueError("one margin row per experiment required")
        for identifier,row in zip(ids,margins):
            if len(row)!=len(pairs) or any(not isinstance(m,MarginEnclosure) or m.experiment_id!=identifier or m.pair!=p for m,p in zip(row,pairs)):
                raise ValueError("complete typed margin rows required")
        for name,value in (("experiment_ids",ids),("costs",costs),("candidate_ids",candidates),
                           ("pairs",pairs),("margins",margins),("target_labels",labels)):
            object.__setattr__(self,name,value)


def margin_from_readings(identifier,pair,left,right,*,fidelity=0,binding=()):
    from .fidelity_design import BoundedReading
    if not isinstance(left,BoundedReading)or not isinstance(right,BoundedReading):
        raise TypeError("NX09 BoundedReading inputs required")
    if (left.units,left.horizon,left.domain_id)!=(right.units,right.horizon,right.domain_id):
        raise ValueError("reading units/horizon/reset-domain mismatch")
    centre=abs(left.center-right.center)
    computation=left.computational_radius+right.computational_radius
    physical=left.physical_radius+right.physical_radius
    return MarginEnclosure(identifier,pair,max(Q(0),centre-computation)-physical,
        centre+computation-physical,fidelity,tuple(binding)+(left.units,left.horizon,left.domain_id))


def coverage_bounds(problem,margins=None):
    rows=problem.margins if margins is None else margins
    return (tuple(sum(1<<i for i,m in enumerate(row)if m.lower>0)for row in rows),
            tuple(sum(1<<i for i,m in enumerate(row)if m.upper>0)for row in rows))


def _cover(costs,masks,pairs,max_states=1000000):
    full=(1<<pairs)-1;states={0:(Q(0),())}
    for e,(cost,mask)in enumerate(zip(costs,masks)):
        updated=dict(states)
        for covered,(old,panel)in states.items():
            new=covered|mask;record=(old+cost,panel+(e,))
            if new not in updated or record<updated[new]:updated[new]=record
        states=updated
        if len(states)>max_states:raise ValueError("exact cover state budget exhausted")
    return states.get(full)


def decision_bounds(problem,margins=None,max_states=1000000):
    certain,possible=coverage_bounds(problem,margins)
    lower=_cover(problem.costs,possible,len(problem.pairs),max_states)
    upper=_cover(problem.costs,certain,len(problem.pairs),max_states)
    return {"lower":None if lower is None else lower[0],
            "upper":None if upper is None else upper[0],
            "optimistic_panel":None if lower is None else lower[1],
            "certain_panel":None if upper is None else upper[1],
            "certain_masks":certain,"possible_masks":possible}


def refine_decision(problem,oracle,*,max_refinements=100,max_states=1000000):
    """Refine unresolved cells on a cheapest optimistic competitor.

    Valid enclosures may be intersected; disjoint purported certificates are
    rejected. A stalled or exhausted oracle returns a valid unresolved gap.
    """
    if type(max_refinements)is not int or max_refinements<0:
        raise ValueError("nonnegative refinement budget required")
    rows=[list(row)for row in problem.margins];history=[];blocked=set()
    for _ in range(max_refinements+1):
        bounds=decision_bounds(problem,rows,max_states)
        if bounds['lower']is None:
            status='proved_unseparable';break
        if bounds['upper']is not None and bounds['lower']==bounds['upper']:
            status='optimal';break
        if len(history)>=max_refinements:
            status='optimality_unresolved';break
        cells=[(e,p)for e in bounds['optimistic_panel']for p,m in enumerate(rows[e])
               if m.lower<=0<m.upper and (e,p)not in blocked]
        if not cells:
            status='optimality_unresolved';break
        e,p=min(cells);old=rows[e][p];new=oracle(e,p,old)
        if not isinstance(new,MarginEnclosure) or (new.experiment_id,new.pair,new.binding)!=(old.experiment_id,old.pair,old.binding):
            raise ValueError("oracle changed the source/candidate/domain binding")
        lo,hi=max(old.lower,new.lower),min(old.upper,new.upper)
        if lo>hi or new.fidelity<old.fidelity:
            raise ValueError("inconsistent certified refinement or fidelity reversal")
        combined=replace(new,lower=lo,upper=hi)
        history.append((e,p,old,combined))
        rows[e][p]=combined
        if (lo,hi)==(old.lower,old.upper):blocked.add((e,p))
    return {"schema":"singularity.refinement-decision/1","status":status,
            **bounds,"margins":tuple(tuple(row)for row in rows),"history":tuple(history),
            "refinement_calls":len(history),"blocked_cells":tuple(sorted(blocked)),
            "scope":"finite supplied pool, target map, positive costs and independent scalar boxes"}


def replay_refinement(problem,result):
    if result.get('status')not in ('optimal','proved_unseparable','optimality_unresolved'):
        raise ValueError("unknown refinement decision status")
    rows=[list(row)for row in problem.margins]
    for e,p,old,new in result['history']:
        if rows[e][p]!=old or (new.experiment_id,new.pair,new.binding)!=(old.experiment_id,old.pair,old.binding):
            raise ValueError("refinement transcript binding mismatch")
        if not old.lower<=new.lower<=new.upper<=old.upper:
            raise ValueError("nonmonotone refinement transcript")
        if new.fidelity<old.fidelity:
            raise ValueError("refinement transcript reverses fidelity")
        rows[e][p]=new
    if tuple(tuple(row)for row in rows)!=result['margins']:
        raise ValueError("final margin table mismatch")
    fresh=decision_bounds(problem,rows)
    if any(result[k]!=v for k,v in fresh.items()):raise ValueError("decision bounds fail replay")
    if result['status']=='optimal'and(result['lower']is None or result['lower']!=result['upper']):
        raise ValueError("unsupported optimality claim")
    if result['status']=='proved_unseparable'and result['lower']is not None:
        raise ValueError("unsupported unseparability claim")
    if result.get('refinement_calls')!=len(result['history']):
        raise ValueError("refinement work count mismatch")
    return True
