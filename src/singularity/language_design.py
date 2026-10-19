"""Exact finite capability activation plus robust target-aware panel purchase."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from .dynacomp_adapter import exact

@dataclass(frozen=True)
class Capability:
    identifier: str
    install_cost: Q
    kind: str = 'sensor'
    source_contract: str = 'synthetic, uncalibrated catalogue'
    def __post_init__(self):
        object.__setattr__(self,'install_cost',exact(self.install_cost))
        if not self.identifier or self.install_cost<0 or self.kind not in ('sensor','actuator','other') or not self.source_contract:raise ValueError('invalid capability')

@dataclass(frozen=True)
class RequiredExperiment:
    identifier: str
    requires: tuple
    readings: tuple
    radii: tuple
    run_cost: Q
    protocol: tuple = ()
    source_contract: str = 'declared exact finite readings'
    def __post_init__(self):
        object.__setattr__(self,'run_cost',exact(self.run_cost));object.__setattr__(self,'readings',tuple(map(exact,self.readings)));object.__setattr__(self,'radii',tuple(map(exact,self.radii)))
        if not self.identifier or self.run_cost<0 or len(self.readings)!=len(self.radii) or any(r<0 for r in self.radii) or len(set(self.requires))!=len(self.requires):raise ValueError('invalid required experiment')

@dataclass(frozen=True)
class LanguageDesignProblem:
    capabilities: tuple
    experiments: tuple
    candidate_ids: tuple
    target_labels: tuple
    deployments: int = 1
    def __post_init__(self):
        caps=tuple(c.identifier for c in self.capabilities)
        if len(set(caps))!=len(caps) or len({e.identifier for e in self.experiments})!=len(self.experiments):raise ValueError('duplicate catalogue/experiment ID')
        if len(set(self.candidate_ids))!=len(self.candidate_ids) or len(self.candidate_ids)<2 or len(self.target_labels)!=len(self.candidate_ids):raise ValueError('distinct candidates and matching targets required')
        if type(self.deployments) is not int or self.deployments<1:raise ValueError('positive integer accounting horizon required')
        for e in self.experiments:
            if not set(e.requires)<=set(caps) or len(e.readings)!=len(self.candidate_ids):raise ValueError('unknown requirement or candidate dimension mismatch')


def _masks(problem):
    pairs=tuple((i,j) for i in range(len(problem.candidate_ids)) for j in range(i+1,len(problem.candidate_ids)) if problem.target_labels[i]!=problem.target_labels[j])
    masks=tuple(sum(1<<k for k,(i,j) in enumerate(pairs) if abs(e.readings[i]-e.readings[j])>e.radii[i]+e.radii[j]) for e in problem.experiments)
    return pairs,masks


def minimum_installation_panel(problem,*,max_catalogue_subsets=256,max_panel_nodes=1000000,max_ties=1024):
    if not isinstance(problem,LanguageDesignProblem):raise TypeError('LanguageDesignProblem required')
    if any(type(v) is not int or v<1 for v in (max_catalogue_subsets,max_panel_nodes,max_ties)):raise ValueError('positive integer search and tie budgets required')
    k=len(problem.capabilities)
    if 1<<k>max_catalogue_subsets:raise ValueError('resource_limit: installation catalogue subset budget exceeded')
    pairs,masks=_masks(problem);full=(1<<len(pairs))-1
    nodes=0;best=None;optima=[];frontier=[];exhausted=False;ties_truncated=False
    for installedmask in range(1<<k):
        installed=tuple(c.identifier for i,c in enumerate(problem.capabilities) if installedmask>>i&1)
        install=sum((c.install_cost for i,c in enumerate(problem.capabilities) if installedmask>>i&1),Q(0))
        dp={0:(Q(0),((),))}
        for e,mask in zip(problem.experiments,masks):
            if not mask or not set(e.requires)<=set(installed):continue
            nxt=dict(dp)
            for covered,(cost,panels) in dp.items():
                nodes+=1
                if nodes>max_panel_nodes:exhausted=True;break
                newmask=covered|mask;newcost=cost+e.run_cost
                newpanels=tuple(p+(e.identifier,) for p in panels)
                if newmask not in nxt or newcost<nxt[newmask][0]:nxt[newmask]=(newcost,newpanels[:max_ties])
                elif newcost==nxt[newmask][0]:
                    combined=tuple(dict.fromkeys(nxt[newmask][1]+newpanels))
                    if len(combined)>max_ties:ties_truncated=True
                    nxt[newmask]=(newcost,combined[:max_ties])
            dp=nxt
            if exhausted:break
        if full in dp:
            run,panels=dp[full];total=install+problem.deployments*run
            row={'installed':installed,'installation_cost':install,'run_cost':run,'total_cost':total,'panels':panels}
            frontier.append(row)
            if best is None or total<best:best=total;optima=[row]
            elif total==best:optima.append(row)
        if exhausted:break
    pareto=tuple(row for row in frontier if not any(other['installation_cost']<=row['installation_cost'] and other['run_cost']<=row['run_cost'] and (other['installation_cost']<row['installation_cost'] or other['run_cost']<row['run_cost']) for other in frontier))
    return {'schema':'singularity.language-design/1','status':('optimality_unresolved' if best is not None else 'resource_limit') if exhausted else ('optimal' if best is not None else 'unseparable'),'total_cost':best,'optima':tuple(optima),'pareto_frontier':pareto,'target_pairs':tuple((problem.candidate_ids[i],problem.candidate_ids[j]) for i,j in pairs),'deployments':problem.deployments,'catalogue_subsets':(1<<k) if not exhausted else installedmask+1,'panel_nodes':nodes,'ties_truncated':ties_truncated,'scope':'complete finite supplied catalogue, target map, independent-reset pool and accounting horizon'}


def verify_installation_result(problem,result,**limits):
    fresh=minimum_installation_panel(problem,**limits)
    if fresh!=result:raise ValueError('installation solution does not replay')
    # Check every selected original panel separately from the optimization DP.
    pairs,_=_masks(problem);byid={e.identifier:e for e in problem.experiments};caps={c.identifier:c for c in problem.capabilities}
    for row in result['optima']:
        for panel in row['panels']:
            selected=[byid[e] for e in panel]
            if any(not set(e.requires)<=set(row['installed']) for e in selected):raise ValueError('inactive experiment requirement')
            if any(not any(abs(e.readings[i]-e.readings[j])>e.radii[i]+e.radii[j] for e in selected) for i,j in pairs):raise ValueError('uncovered target pair')
            install=sum((caps[c].install_cost for c in row['installed']),Q(0));run=sum((e.run_cost for e in selected),Q(0))
            if install!=row['installation_cost'] or run!=row['run_cost'] or install+problem.deployments*run!=result['total_cost']:raise ValueError('cost witness mismatch')
    return True


def enumerate_installation_frontier(problem,deployments=(1,2,10,100),**limits):
    from dataclasses import replace
    return tuple(minimum_installation_panel(replace(problem,deployments=n),**limits) for n in deployments)


def thermal_capability_catalogue(candidates,*,horizons=(1,2,3,4),radius=0):
    """Four sensor purchases plus one synthetic independently selected heater.

    Every experiment uses one fixed installed heater, not simultaneous input
    channels. Existing six-model source objects are never changed in place.
    """
    from .thermal_diagnostics import AffineCandidate,simulate_protocol
    candidates=tuple(candidates);n=candidates[0].dimension
    if any(c.dimension!=n or len(c.sensors)<4 for c in candidates):raise ValueError('common four-channel plate candidates required')
    caps=tuple(Capability('sensor:'+str(j),Q(1+j),'sensor') for j in range(4))+(Capability('asymmetric_heater',Q(3),'actuator'),)
    asymmetric=tuple(Q(int(i==n//2)) for i in range(n));experiments=[]
    for heater in ('original','asymmetric'):
        models=candidates if heater=='original' else tuple(AffineCandidate(c.identifier,c.dimension,c.entries,asymmetric,c.sensors) for c in candidates)
        for horizon in horizons:
            if type(horizon) is not int or horizon<1:raise ValueError('positive horizons required')
            for sensor in range(4):
                word=(Q(1),)*horizon;requires=('sensor:'+str(sensor),)+(('asymmetric_heater',) if heater=='asymmetric' else ())
                readings=tuple(simulate_protocol(c,word,sensor) for c in models)
                experiments.append(RequiredExperiment(f'{heater}:t{horizon}:s{sensor}',requires,readings,(exact(radius),)*len(candidates),Q(horizon+2),word,'synthetic 4x4 capability family; exact source-derived stencil; independent zero reset'))
    return LanguageDesignProblem(caps,tuple(experiments),tuple(c.identifier for c in candidates),tuple(c.identifier for c in candidates))
