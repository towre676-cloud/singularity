"""Target-specific identification for a declared bilinear drill model.

Physical/predictive meaning requires an external source-bound pilot.
"""
from fractions import Fraction as Q
from ._application_exact import vector,matrix,dot,box_estimator
from .forecast_targets import target_factorization,target_null_witness,ForecastTarget,SensorBlock,select_target_panel


def movement_condition(stress,agility,*,normalization,response_definition):
    s,a=vector((stress,agility))
    if not normalization or not response_definition:raise ValueError("normalization and response definition required")
    return (Q(1),s,a,s*a)


def target_identifiable(design,target):
    return target_factorization(design,(vector(target),)) is not None


def movement_null_witness(design,target):return target_null_witness(design,(vector(target),))


def bounded_target_estimator(design,target,radii):return box_estimator(design,target,radii)


def minimum_drill_repair(existing,candidates,target,*,normalization,response_definition,max_error=None,budget=None,existing_radii=None):
    if not normalization or not response_definition:raise ValueError("measurement interpretation required")
    rows=matrix(existing,4)
    base=[]
    if rows:base=[SensorBlock("existing",rows,(Q(),)*len(rows) if existing_radii is None else tuple(existing_radii),Q(),normalization,response_definition)]
    model=ForecastTarget(tuple(tuple(Q(i==j) for j in range(4)) for i in range(4)),vector(target),0,normalization,"one drill",response_definition)
    result=select_target_panel(tuple(base)+tuple(candidates),model,max_error=max_error,budget=budget)
    if "selected" in result:
        result["estimator_sensor_order"]=result["selected"]
        result["selected"]=tuple(name for name in result["selected"] if name!="existing")
    return result


def independent_repeat_variance(radius,repetitions):
    """Variance of mean for explicitly independent symmetric +/-radius errors.

    Worst-case support radius remains radius; no structural direction is added.
    """
    r=vector((radius,))[0]
    if r<0 or type(repetitions) is not int or repetitions<=0:raise ValueError("invalid repeat model")
    return {"variance":r*r/repetitions,"worst_case_radius":r,"error_model":"independent_symmetric_two_point"}
