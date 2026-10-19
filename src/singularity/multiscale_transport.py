"""Exact finite-dimensional commutation defects and target error transport.

Physical source error is deliberately not estimated from algebraic residuals.
"""
from fractions import Fraction as Q
from ._application_exact import (matrix,vector,rational,dot,multiply,apply,
                                subtract,row_factorization,transpose)


def linear_commutation_defect(fine,coarse,E,*,fine_units,coarse_units,time_step):
    if not fine_units or not coarse_units or not time_step:raise ValueError("units and time step required")
    fine,coarse,E=matrix(fine),matrix(coarse),matrix(E)
    if len(fine)!=len(fine[0]) or len(coarse)!=len(coarse[0]):raise ValueError("square dynamics required")
    return subtract(multiply(E,fine),multiply(coarse,E))


def zonotope_range(rows,center,generators):
    """Exact separate component ranges over center + generators [-1,1]^k.

    All component endpoints are attainable individually, not necessarily jointly.
    """
    rows,center,generators=matrix(rows),vector(center),matrix(generators)
    if len(generators)!=len(center):raise ValueError("generator dimension mismatch")
    means=apply(rows,center);a=multiply(rows,generators)
    radii=tuple(sum(map(abs,r),Q()) for r in a)
    return tuple((m-r,m+r) for m,r in zip(means,radii))


def box_defect_bound(defect,center,radii):
    radii=vector(radii)
    if any(x<0 for x in radii):raise ValueError("negative domain radius")
    g=tuple(tuple(radii[i] if i==j else Q() for j in range(len(radii))) for i in range(len(radii)))
    ranges=zonotope_range(defect,center,g)
    return tuple(max(abs(a),abs(b)) for a,b in ranges)


def induced_infinity_norm(a):return max((sum(map(abs,r),Q()) for r in matrix(a)),default=Q())


def propagate_scale_error(initial_error,lipschitz,defect_bounds):
    e=rational(initial_error);ds=vector(defect_bounds)
    ls=(rational(lipschitz),)*len(ds) if isinstance(lipschitz,(int,Q)) and not isinstance(lipschitz,bool) else vector(lipschitz)
    if e<0 or len(ls)!=len(ds) or any(v<0 for v in ls+ds):raise ValueError("nonnegative horizon bounds required")
    if len(ds)>32:raise ValueError("horizon budget")
    out=[e]
    for l,d in zip(ls,ds):out.append(l*out[-1]+d)
    return tuple(out)


def target_transfer_bound(representation_error,target_lipschitz,state_error):
    a,b,c=vector((representation_error,target_lipschitz,state_error))
    if min(a,b,c)<0:raise ValueError("negative error budget")
    return {"representation_error":a,"dynamic_error":b*c,"total_bound":a+b*c,"physical_model_error":"not_estimated","arithmetic_error":Q()}


def exact_target_quotient(fine,rows):
    fine,rows=matrix(fine),matrix(rows)
    target=multiply(rows,fine)
    return row_factorization(rows,target)


def reachable_zonotopes(transition,center,generators,horizon,input_generators=None):
    """Exact linear reachable set with independent per-step input coefficients.

    Initial generator correlation is retained at every step. Empty input means
    no forcing. A source-domain statement remains a separate model hypothesis.
    """
    a,c,g=matrix(transition),vector(center),matrix(generators)
    if type(horizon) is not int or not 0<=horizon<=32:raise ValueError("horizon budget")
    u=None if input_generators is None else matrix(input_generators)
    if len(a)!=len(c) or len(g)!=len(c) or (u is not None and len(u)!=len(c)):raise ValueError("dimension mismatch")
    out=[(c,g)]
    for _ in range(horizon):
        c=apply(a,c);g=multiply(a,g)
        if u is not None:g=tuple(r+s for r,s in zip(g,u))
        out.append((c,g))
    return tuple(out)


def compose_linear_defects(fine,middle,coarse,Efm,Emc):
    fine,middle,coarse,Efm,Emc=map(matrix,(fine,middle,coarse,Efm,Emc))
    d1=subtract(multiply(Efm,fine),multiply(middle,Efm))
    d2=subtract(multiply(Emc,middle),multiply(coarse,Emc))
    direct=subtract(multiply(multiply(Emc,Efm),fine),multiply(coarse,multiply(Emc,Efm)))
    p,q=multiply(Emc,d1),multiply(d2,Efm)
    transported=tuple(tuple(x+y for x,y in zip(r,s)) for r,s in zip(p,q))
    return {"direct":direct,"transported_sum":transported,"identity_holds":direct==transported,"composed_map":multiply(Emc,Efm)}
