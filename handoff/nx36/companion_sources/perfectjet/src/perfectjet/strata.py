"""Active partner strata: correction rank and active capacity on common cells.

For a sextic f, L_N(f) sends a degree-N form g to ((f,g)_3,(f,g)_5) and P_N(f)
sends it to the Poisson bracket (f,g)_1. The correction-free kernel is ker L_N
and the active quotient is

    A_N(f) = ker L_N / (ker L_N intersect ker P_N),
    dim A_N = rank [L_N; P_N] - rank L_N.

On a parameter family both ranks are constant on constructible cells. This
module refines the correction cells by the joint cells, so each stratum
carries both dimensions, and then builds actual partners at a rational point
of every stratum where one exists: a form g with (f,g)_3=(f,g)_5=0 and
(f,g)_1 != 0, replayed with exact transvectants. The sextic discriminant
separates repeated-root degeneracy from squarefree exceptional structure.
"""
from fractions import Fraction as Q
from itertools import product
from .exact import nullspace, rank, matmul, transpose
from .parametric import (clean, const, var, sub, mul, divide, evaluate, groebner, saturate_by, is_unit_ideal,
                         rank_cells, rational_points, dimension, fmt, nonempty, polynomial_matrix,
                         sextic_family, total_degree)
from .polynomial import Poly
from .transvectants import gate_matrix, transvectant

NAMES = ["a", "b"]


# ------------------------------------------------------------ determinants


def bareiss_det(m, nvars):
    """Determinant of a square matrix over Q[t] by fraction-free Bareiss elimination."""
    m = [[clean(p) for p in row] for row in m]
    n = len(m)
    if n == 0:
        return const(1, nvars)
    sign, prev = 1, const(1, nvars)
    for k in range(n-1):
        if not m[k][k]:
            swap = next((i for i in range(k+1, n) if m[i][k]), None)
            if swap is None:
                return {}
            m[k], m[swap] = m[swap], m[k]
            sign = -sign
        for i in range(k+1, n):
            for j in range(k+1, n):
                num = sub(mul(m[i][j], m[k][k]), mul(m[i][k], m[k][j]))
                q = divide(num, prev) if num else {}
                if q is None:
                    raise ArithmeticError("Bareiss division was not exact")
                m[i][j] = q
            m[i][k] = {}
        prev = m[k][k]
    det = m[n-1][n-1]
    return {e: sign*c for e, c in det.items()}


def binary_coefficients(form_fn, nvars, degree=6):
    """Coefficients c_i of x^(degree-i) y^i as polynomials in the parameters (affine in each)."""
    return polynomial_matrix(lambda *t: [[form_fn(*t).terms.get((degree-i, i), Q(0)) for i in range(degree+1)]],
                             nvars, 1)[0]


def discriminant_resultant(coeffs, nvars):
    """Res(F, F') for F(x)=sum c_i x^(d-i), the dehomogenized form; zero iff a repeated finite root.

    With a constant nonzero leading coefficient this is a nonzero constant multiple
    of the discriminant, which is all that is used: only its zero set matters.
    """
    d = len(coeffs)-1
    deriv = [mul(const(d-i, nvars), c) for i, c in enumerate(coeffs[:-1])]
    size = 2*d-1
    rows = []
    for r in range(d-1):
        rows.append([{}]*r + list(coeffs) + [{}]*(size-r-d-1))
    for r in range(d):
        rows.append([{}]*r + deriv + [{}]*(size-r-d))
    return bareiss_det(rows, nvars)


# ------------------------------------------------------------- the strata


def _correction(n):
    return lambda a, b: gate_matrix(sextic_family(a, b), n, 3)+gate_matrix(sextic_family(a, b), n, 5)


def _joint(n):
    return lambda a, b: (gate_matrix(sextic_family(a, b), n, 3)+gate_matrix(sextic_family(a, b), n, 5)
                         + gate_matrix(sextic_family(a, b), n, 1))


def strata(n):
    """Common refinement of correction cells and joint cells for degree-n partners."""
    lmat = polynomial_matrix(_correction(n), 2, 1)
    jmat = polynomial_matrix(_joint(n), 2, 1)
    out = []
    for cell in rank_cells(lmat, 2):
        for sub_cell in rank_cells(jmat, 2, cell["equations"], cell["inequations"]):
            out.append({"equations": sub_cell["equations"], "inequations": sub_cell["inequations"],
                        "correction_rank": cell["rank"], "joint_rank": sub_cell["rank"],
                        "kernel_dimension": n+1-cell["rank"],
                        "active_dimension": sub_cell["rank"]-cell["rank"]})
    return out


def _admissible(cell, point):
    return (all(evaluate(p, point) == 0 for p in cell["equations"])
            and all(evaluate(q, point) != 0 for q in cell["inequations"]))


def sample_points(cell, search=range(-6, 7), limit=3):
    """Rational points of a cell: grid for open cells, slices for curves, exact points if finite."""
    eqs = cell["equations"]
    dim = dimension(eqs, 2)
    found = []
    if dim == 2:
        for pt in sorted(product(search, repeat=2), key=lambda p: (abs(p[0])+abs(p[1]), p)):
            pt = (Q(pt[0]), Q(pt[1]))
            if _admissible(cell, pt):
                found.append(pt)
            if len(found) >= limit:
                break
    elif dim == 1:
        for k in sorted(search, key=lambda v: (abs(v), v)):
            for i in range(2):
                line = sub(var(i, 2), const(k, 2))
                g = groebner(eqs+[line])
                if is_unit_ideal(g) or dimension(g, 2) != 0:
                    continue
                for pt in rational_points(g, 2):
                    if _admissible(cell, pt) and pt not in found:
                        found.append(pt)
            if len(found) >= limit:
                break
    elif dim == 0:
        found = [pt for pt in rational_points(eqs, 2) if _admissible(cell, pt)]
    return found[:limit]


def small_rationals(height):
    """Rationals p/q with |p|,q <= height in lowest terms, ordered by height."""
    from math import gcd
    out = {Q(p, q) for q in range(1, height+1) for p in range(-height, height+1) if gcd(p, q) == 1}
    return sorted(out, key=lambda r: (max(abs(r.numerator), r.denominator), r))


def curve_points(cell, height=12):
    """Rational points of a curve cell found by slicing b=b0 for every b0 of bounded height."""
    eqs = cell["equations"]
    found = []
    for b0 in small_rationals(height):
        g = groebner(eqs+[sub(var(1, 2), const(b0, 2))])
        if is_unit_ideal(g) or dimension(g, 2) != 0:
            continue
        for pt in rational_points(g, 2):
            if _admissible(cell, pt) and pt not in found:
                found.append(pt)
    return sorted(found, key=lambda p: (p[1], p[0]))


def form_from_vector(v, n):
    return Poly({(n-j, j): c for j, c in enumerate(v) if c})


def partner_witness(a, b, n):
    """Exact partner basis at one rational parameter point, replayed with transvectants."""
    f = sextic_family(a, b)
    lmat = gate_matrix(f, n, 3)+gate_matrix(f, n, 5)
    pmat = gate_matrix(f, n, 1)
    kernel = nullspace(lmat, n+1) if lmat else [[Q(int(i == j)) for i in range(n+1)] for j in range(n+1)]
    images = matmul(pmat, transpose(kernel)) if kernel and pmat else []
    # Columns of images are P-images of kernel vectors; pick a maximal independent set.
    active, chosen = [], []
    for idx, vec in enumerate(kernel):
        if images and rank([[row[j] for j in chosen+[idx]] for row in images]) > len(chosen):
            chosen.append(idx)
            active.append(vec)
    commuting = []
    if kernel:
        # ker L intersect ker P: combinations of kernel vectors killed by P.
        for c in nullspace(images, len(kernel)) if images else []:
            commuting.append([sum((ci*k[j] for ci, k in zip(c, kernel)), Q(0)) for j in range(n+1)])
    replay = []
    for vec in active:
        g = form_from_vector(vec, n)
        replay.append(transvectant(f, g, 3) == Poly() and transvectant(f, g, 5) == Poly()
                      and transvectant(f, g, 1) != Poly())
    for vec in commuting:
        g = form_from_vector(vec, n)
        replay.append(transvectant(f, g, 3) == Poly() and transvectant(f, g, 5) == Poly()
                      and transvectant(f, g, 1) == Poly())
    return {"point": (a, b), "kernel_dimension": len(kernel), "active_dimension": len(active),
            "commuting_dimension": len(commuting), "active_partners": active, "commuting_partners": commuting,
            "replayed": all(replay)}


def classify_degeneracy(cell, disc):
    """Where the sextic has a repeated root on the Zariski closure of a cell.

    repeated_root: the discriminant vanishes on a component of the closure of full dimension;
    squarefree: it vanishes nowhere on the closure; generically_squarefree: only on a
    lower-dimensional part of it.
    """
    eqs = cell["equations"]
    dim = dimension(eqs, 2)
    if dim == 2:
        return "generically_squarefree" if disc else "repeated_root"
    g = groebner(eqs+[disc])
    if is_unit_ideal(g):
        return "squarefree"
    return "repeated_root" if dimension(g, 2) == dim else "generically_squarefree"


def surface_discriminant():
    return discriminant_resultant(binary_coefficients(sextic_family, 2), 2)


def orbit_representative(pt):
    """y -> -y maps (a,b) to (-a,b) and x <-> y fixes the family; keep a >= 0."""
    a, b = pt
    return (abs(a), b)


def active_report(degrees=range(3, 13)):
    disc = surface_discriminant()
    rows = []
    for n in degrees:
        cells = []
        for cell in strata(n):
            pts = sample_points(cell)
            witnesses = [partner_witness(a, b, n) for a, b in pts]
            for w in witnesses:
                assert w["kernel_dimension"] == cell["kernel_dimension"], (n, w["point"])
                assert w["active_dimension"] == cell["active_dimension"], (n, w["point"])
                assert w["replayed"], (n, w["point"])
            dim = dimension(cell["equations"], 2)
            cells.append({"closure": [fmt(p, NAMES) for p in cell["equations"]] or ["(open)"],
                          "excluding": [fmt(q, NAMES) for q in cell["inequations"]],
                          "dimension": dim, "kernel_dimension": cell["kernel_dimension"],
                          "active_dimension": cell["active_dimension"],
                          "commuting_dimension": cell["kernel_dimension"]-cell["active_dimension"],
                          "degeneracy": classify_degeneracy(cell, disc),
                          "rational_samples": [[str(a), str(b)] for a, b in pts],
                          "orbit_samples": sorted({tuple(str(x) for x in orbit_representative(p)) for p in pts}),
                          "partner": _partner_text(witnesses, n), "_cell": cell})
        generic = next(c for c in cells if c["dimension"] == 2)
        rows.append({"degree": n, "generic_kernel": generic["kernel_dimension"],
                     "generic_active": generic["active_dimension"], "strata": cells})
    return rows


def _partner_text(witnesses, n):
    for w in witnesses:
        if w["active_partners"]:
            return {"at": [str(x) for x in w["point"]],
                    "g": form_from_vector(w["active_partners"][0], n).record()}
    return None


def jump_table(report, height=12):
    """Strata whose active dimension differs from the generic one, with their explanation."""
    out = []
    for row in report:
        for c in row["strata"]:
            if c["dimension"] < 2 and (c["active_dimension"] != row["generic_active"]
                                       or c["kernel_dimension"] != row["generic_kernel"]):
                out.append({"degree": row["degree"], "closure": c["closure"], "dimension": c["dimension"],
                            "kernel_jump": c["kernel_dimension"]-row["generic_kernel"],
                            "active_jump": c["active_dimension"]-row["generic_active"],
                            "commuting_dimension": c["commuting_dimension"],
                            "degeneracy": c["degeneracy"], "samples": c["rational_samples"],
                            "_cell": c["_cell"]})
    for row in out:
        cell = row.pop("_cell")
        if row["dimension"] == 1:
            row["rational_points_height_%d" % height] = [[str(a), str(b)] for a, b in curve_points(cell, height)]
    return out


def root_structure(a, b):
    """Multiplicity pattern of the roots of f(x,1), from the squarefree decomposition over Q."""
    from .loci import pgcd, pdivmod, derivative, degree, trim
    f = sextic_family(a, b)
    p = trim([f.terms.get((i, 6-i), Q(0)) for i in range(7)])
    pattern, k = [], 1
    while degree(p) > 0:
        g = pgcd(p, derivative(p))
        sqf = pdivmod(p, g)[0]
        nxt = pgcd(sqf, g) if degree(g) > 0 else [Q(1)]
        if degree(sqf)-degree(nxt) > 0:
            pattern.append({"multiplicity": k, "roots": degree(sqf)-degree(nxt)})
        p, k = g, k+1
    return pattern


def point_profile(a, b, degrees=range(3, 13)):
    """Kernel and active dimension in every degree at one parameter point, with replayed partners."""
    a, b = Q(a), Q(b)
    rows = []
    for n in degrees:
        w = partner_witness(a, b, n)
        assert w["replayed"]
        if w["kernel_dimension"]:
            rows.append({"degree": n, "kernel": w["kernel_dimension"], "active": w["active_dimension"],
                         "commuting": w["commuting_dimension"]})
    return {"a": str(a), "b": str(b), "squarefree": evaluate(surface_discriminant(), (a, b)) != 0,
            "root_multiplicities": root_structure(a, b), "nonzero_kernels": rows}


EXPLAINED_POINTS = [(1, 1), (0, 3), (16, -9), (0, 15), (0, -5), (24, -9), (4, 6), (11, 6), (4, -3),
                    (Q(32, 25), Q(-9, 5))]


def strata_receipt(degrees=range(3, 13)):
    report = active_report(degrees)
    disc = surface_discriminant()
    jumps = jump_table(report)
    for row in report:
        for c in row["strata"]:
            c.pop("_cell", None)
    return {"family": "x^6+y^6+a x^3y^3+b(x^4y^2+x^2y^4)",
            "quotient": "A_N=ker L_N/(ker L_N cap ker P_N); dim A_N=rank[L_N;P_N]-rank L_N",
            "discriminant_degree": total_degree(disc),
            "degrees": report, "jumps": jumps,
            "point_profiles": [point_profile(a, b, degrees) for a, b in EXPLAINED_POINTS],
            "scope": "cells over the algebraic closure; partners constructed at rational sample points only"}
