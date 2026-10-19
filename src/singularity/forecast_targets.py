"""Exact horizon-specific target recovery and finite costed sensor design.

The model is a declared discrete linear model, never a weather validation.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import combinations
from ._application_exact import (rational,vector,matrix,dot,identity,multiply,
                                row_factorization,null_witness,box_estimator)


@dataclass(frozen=True)
class ForecastTarget:
    transition: tuple
    target: tuple
    horizon: int
    units: str
    sampling_interval: str
    domain_id: str
    basis: tuple | None = None
    state_center: tuple | None = None
    state_radii: tuple | None = None

    def __post_init__(self):
        a=matrix(self.transition);g=vector(self.target)
        if not a or len(a)!=len(g) or any(len(r)!=len(g) for r in a):raise ValueError("square transition/target required")
        if type(self.horizon) is not int:raise TypeError("horizon must be int")
        if not 0<=self.horizon<=16:raise ValueError("horizon outside 0..16")
        if not all(isinstance(x,str) and x.strip() for x in (self.units,self.sampling_interval,self.domain_id)):raise ValueError("units, time interval and domain are required")
        object.__setattr__(self,"transition",a);object.__setattr__(self,"target",g)
        if self.basis is not None:
            z=matrix(self.basis)
            if len(z)!=len(g):raise ValueError("basis ambient dimension mismatch")
            object.__setattr__(self,"basis",z)
        if (self.state_center is None)!=(self.state_radii is None):raise ValueError("state center and radii must be supplied together")
        if self.state_center is not None:
            c,e=vector(self.state_center),vector(self.state_radii)
            if len(c)!=len(g) or len(e)!=len(g) or any(v<0 for v in e):raise ValueError("invalid declared state box")
            object.__setattr__(self,"state_center",c);object.__setattr__(self,"state_radii",e)


@dataclass(frozen=True)
class SensorBlock:
    identifier: str
    rows: tuple
    radii: tuple
    cost: Q
    state_units: str
    domain_id: str
    admissible: bool = True

    def __post_init__(self):
        h=matrix(self.rows);e=vector(self.radii);c=rational(self.cost)
        if not self.identifier or not self.state_units or not self.domain_id:raise ValueError("sensor identifiers, units and domain required")
        if not h or len(h)!=len(e) or any(x<0 for x in e) or c<0:raise ValueError("invalid sensor rows/error/cost")
        if type(self.admissible) is not bool:raise TypeError("admissible must be bool")
        object.__setattr__(self,"rows",h);object.__setattr__(self,"radii",e);object.__setattr__(self,"cost",c)


def forecast_row(model,horizon=None):
    if not isinstance(model,ForecastTarget):raise TypeError("ForecastTarget required")
    h=model.horizon if horizon is None else horizon
    if type(h) is not int or not 0<=h<=16:raise ValueError("horizon outside 0..16")
    r=(model.target,)
    for _ in range(h):r=multiply(r,model.transition)
    return r[0]


def target_factorization(H,G,basis=None):
    """Return L with GZ=LHZ, or None. Centres and known inputs are separate."""
    return row_factorization(H,G,basis)


def target_null_witness(H,G,basis=None):return null_witness(H,G,basis)


def known_input_offset(model,input_matrix,inputs):
    """Known forcing contribution g sum A^(tau-1-t) B u_t, exactly."""
    b=matrix(input_matrix);us=tuple(vector(u) for u in inputs)
    if len(us)!=model.horizon or len(b)!=len(model.target):raise ValueError("input horizon or state dimension mismatch")
    state=(Q(),)*len(model.target)
    from ._application_exact import apply
    for u in us:
        state=tuple(x+y for x,y in zip(apply(model.transition,state),apply(b,u)))
    return dot(model.target,state)


def select_target_panel(blocks,target,budget=None,max_error=None,strict=False):
    """Minimum acquisition cost among exact estimators below a box-error cap.

    If no cap is supplied, minimize (error, cost). Error geometry is the same
    deterministic independent-coordinate box for every selected panel.
    """
    blocks=tuple(blocks)
    if len(blocks)>12 or len({b.identifier for b in blocks})!=len(blocks):raise ValueError("catalogue must have at most twelve unique sensors")
    if not isinstance(target,ForecastTarget):raise TypeError("ForecastTarget required")
    cap=None if max_error is None else rational(max_error)
    budget=None if budget is None else rational(budget)
    if (cap is not None and cap<0) or (budget is not None and budget<0):raise ValueError("negative bound")
    for b in blocks:
        if b.state_units!=target.units or b.domain_id!=target.domain_id:raise ValueError("incompatible units or domains")
        if any(len(r)!=len(target.target) for r in b.rows):raise ValueError("state dimension mismatch")
    g=forecast_row(target);z=identity(len(g)) if target.basis is None else target.basis
    gz=multiply((g,),z)[0];best=None;checked=0
    for k in range(len(blocks)+1):
        for ix in combinations(range(len(blocks)),k):
            checked+=1
            if any(not blocks[i].admissible for i in ix):continue
            cost=sum((blocks[i].cost for i in ix),Q())
            if budget is not None and cost>budget:continue
            h=tuple(r for i in ix for r in blocks[i].rows)
            e=tuple(v for i in ix for v in blocks[i].radii)
            hz=multiply(h,z) if h else ()
            estimator=box_estimator(hz,gz,e)
            if estimator is None:continue
            w,err=estimator
            if cap is not None and not (err<cap if strict else err<=cap):continue
            names=tuple(blocks[i].identifier for i in ix)
            score=(err,cost,names) if cap is None else (cost,err,names)
            if best is None or score<best[0]:best=(score,names,w,err,cost)
    if best is None:
        h=tuple(r for b in blocks if b.admissible for r in b.rows)
        return {"status":"infeasible_catalogue","panels_checked":checked,"null_witness":target_null_witness(h,(g,),target.basis)}
    _,names,w,err,cost=best
    center=(Q(),)*len(g) if target.state_center is None else target.state_center
    selected_rows=tuple(r for b in blocks if b.identifier in names for r in b.rows)
    offset=dot(g,center)-sum((a*dot(r,center) for a,r in zip(w,selected_rows)),Q())
    return {"status":"optimal_finite_catalogue","selected":names,"weights":w,"affine_offset":offset,"decoder_contract":"target = affine_offset + weights dot raw_readings + known_input_offset; deterministic error bounded separately","known_input_offset":"not_included; compile from declared known inputs","error_radius":err,"cost":cost,"panels_checked":checked,"horizon":target.horizon,"domain_id":target.domain_id,"noise_geometry":"deterministic_coordinate_box"}
