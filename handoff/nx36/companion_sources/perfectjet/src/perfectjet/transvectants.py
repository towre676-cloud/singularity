"""Exact odd-transvectant gates and active partner dimensions for sextics."""
from fractions import Fraction as Q
from math import comb
from .polynomial import Poly
from .exact import rank


def transvectant(f, g, order):
    if f.variables != 2 or g.variables != 2 or order < 0:
        raise ValueError("binary forms and nonnegative order required")
    out = Poly()
    for i in range(order+1):
        out += ((-1)**i*comb(order, i) * f.derivative((order-i, i))
                * g.derivative((i, order-i)))
    return out


def c3_family(lam):
    x, y = Poly.variable(0), Poly.variable(1)
    f = x**6 + Q(lam)*x**3*y**3 + y**6
    h = x*y*(x**3-y**3)
    g8 = x*y*(x**6+y**6-Q(7,20)*Q(lam)*x**3*y**3)
    return f, h, g8


def gate_matrix(f, degree, order):
    out_degree = 6 + degree - 2*order
    if out_degree < 0:
        return []
    cols = [transvectant(f, Poly({(degree-j, j): 1}), order) for j in range(degree+1)]
    return [[p.terms.get((out_degree-i, i), Q(0)) for p in cols]
            for i in range(out_degree+1)]


def partner_dimensions(f, degree):
    if any(sum(e) != 6 for e in f.terms):
        raise ValueError("a homogeneous sextic is required")
    gates = gate_matrix(f, degree, 3)+gate_matrix(f, degree, 5)
    correction_rank = rank(gates, degree+1)
    joint_rank = rank(gates+gate_matrix(f, degree, 1), degree+1)
    return {"degree": degree, "kernel_dimension": degree+1-correction_rank,
            "active_dimension": joint_rank-correction_rank}


def census(parameters=(0, 1, Q(40,7), 20, -20), degrees=range(3,13)):
    return {str(p): [partner_dimensions(c3_family(p)[0], n) for n in degrees]
            for p in parameters}


def molecular_receipt():
    x, y = Poly.variable(0), Poly.variable(1)
    rows = []
    for lam in (Q(0), Q(1), Q(40,7), Q(-3,2)):
        f, h, g8 = c3_family(lam)
        rows.append({"lambda": str(lam),
                     "g8_T3_zero": transvectant(f,g8,3)==0,
                     "g8_T5_zero": transvectant(f,g8,5)==0,
                     "g8_Poisson_nonzero": transvectant(f,g8,1)!=0,
                     "quintic_obstruction_replay": transvectant(f,h,3)==72*(7*lam-40)*(x**4*y+x*y**4),
                     "quintic_T5_zero": transvectant(f,h,5)==0})
    _, h, g8 = c3_family(Q(40,7))
    return {"arithmetic": "exact rational", "scope": "retained finite checks; parameter identities documented separately",
            "rows": rows, "exceptional_factorization": g8==(x**3-y**3)*h,
            "partner_census": census()}
