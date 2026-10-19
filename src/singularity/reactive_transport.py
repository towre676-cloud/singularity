"""Conservative exact linear species/cell toy and finite robust hypothesis sets."""
from fractions import Fraction as Q
from itertools import combinations
from ._application_exact import matrix,vector,rational,multiply,apply,dot


def conversion_mixing(mixing,conversion):
    d=matrix(mixing);r=rational(conversion);n=len(d)
    if not d or any(len(row)!=n for row in d) or not 0<=r<=1:raise ValueError("invalid mixing/rate")
    if any(x<0 for row in d for x in row) or any(sum((d[i][j] for i in range(n)),Q())!=1 for j in range(n)):raise ValueError("mixing must be nonnegative column stochastic")
    zero=(Q(),)*n
    return tuple(tuple((1-r)*x for x in row)+zero for row in d)+tuple(tuple(r*x for x in row)+row for row in d)


def verify_positive_step(a):return all(v>=0 for r in matrix(a) for v in r)


def verify_conservation(a,weights=None):
    a=matrix(a);w=(Q(1),)*len(a) if weights is None else vector(weights)
    return multiply((w,),a)[0]==w


def reaction_flux_step(state,mixing,conversion):
    """Independent reaction-then-cell-flux oracle; never assembles the block matrix."""
    c=vector(state);d=matrix(mixing);r=rational(conversion);n=len(d)
    if len(c)!=2*n or any(x<0 for x in c):raise ValueError("nonnegative species state required")
    aa=tuple((1-r)*x for x in c[:n]);bb=tuple(y+r*x for x,y in zip(c[:n],c[n:]))
    return apply(d,aa)+apply(d,bb)


def reactive_target_rows(a,target,horizon):
    a=matrix(a);row=vector(target)
    if type(horizon) is not int or not 0<=horizon<=16:raise ValueError("horizon budget")
    out=[row]
    for _ in range(horizon):out.append(multiply((out[-1],),a)[0])
    return tuple(out)


def species_sensor_panel(hypotheses,experiments):
    """Find cheapest panel separating all finite labels despite rate/noise sets.

    hypotheses is {label: tuple(states)} with model uncertainty already compiled
    into each experiment's attainable values: experiment=(id,{label:values},e,c).
    One coordinate may certify separation via disjoint intervals. Correlations
    retained in the source values are not asserted to fill their interval hull.
    """
    labels=tuple(hypotheses);exps=tuple(experiments)
    if len(exps)>12 or len(labels)>512:raise ValueError("finite pilot budget")
    pairs=tuple(combinations(labels,2));best=None
    for eid,values,e,c in exps:
        if rational(e)<0 or rational(c)<0 or set(values)!=set(labels):raise ValueError("bad experiment schema")
        if any(not values[label] for label in labels):raise ValueError("empty attainable population")
    def separates(exp,a,b):
        _,v,e,_=exp;e=rational(e);av=vector(v[a]);bv=vector(v[b])
        return max(av)+e<min(bv)-e or max(bv)+e<min(av)-e
    for k in range(len(exps)+1):
        for ix in combinations(range(len(exps)),k):
            if not all(any(separates(exps[i],a,b) for i in ix) for a,b in pairs):continue
            score=(sum((rational(exps[i][3]) for i in ix),Q()),tuple(exps[i][0] for i in ix))
            if best is None or score<best:best=score
    return {"status":"infeasible_interval_separation" if best is None else "optimal_finite_interval_panel","cost":None if best is None else best[0],"selected":None if best is None else best[1],"uncertainty_scope":"declared_finite_hypotheses_and_rate_populations","overlap_does_not_prove_joint_identity":True}
