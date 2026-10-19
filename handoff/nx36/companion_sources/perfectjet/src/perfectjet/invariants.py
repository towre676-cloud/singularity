"""Clebsch invariants of binary sextics and GL2 orbit comparison.

With unnormalized transvectants (f,g)_k (transvectants.transvectant),

    i = (f,f)_4,  Delta = (i,i)_2,  y1 = (f,i)_4,  y2 = (i,y1)_2,  y3 = (i,y2)_2,
    A = (f,f)_6,  B = (i,i)_4,  C = (i,Delta)_4,  D = (y3,y1)_2,

are invariants of degrees 2, 4, 6, 10 in the coefficients. Under x -> M x they
scale by det(M)^(3k) for degree k, so (A:B:C:D) is a point of weighted projective
space with weights (1,2,3,5) after halving. Two sextics with equal points are
GL2-equivalent over the algebraic closure when both are squarefree (stable); for
forms with repeated roots, orbits need not be closed and equal invariants do not
prove equivalence. The normalization constants differ from Clebsch's, which does
not affect orbit comparison because the same formulas are used throughout.
"""
from fractions import Fraction as Q
from .transvectants import transvectant
from .polynomial import Poly

WEIGHTS = (1, 2, 3, 5)


def _const(p):
    if any(sum(e) for e in p.terms):
        raise ArithmeticError("transvectant chain did not reach a constant")
    return next(iter(p.terms.values()), Q(0))


def clebsch(f):
    if any(sum(e) != 6 for e in f.terms):
        raise ValueError("a homogeneous sextic is required")
    i = transvectant(f, f, 4)
    delta = transvectant(i, i, 2)
    y1 = transvectant(f, i, 4)
    y2 = transvectant(i, y1, 2)
    y3 = transvectant(i, y2, 2)
    return (_const(transvectant(f, f, 6)), _const(transvectant(i, i, 4)),
            _const(transvectant(i, delta, 4)), _const(transvectant(y3, y1, 2)))


def same_weighted_point(u, v, weights=WEIGHTS):
    """u ~ v in weighted projective space over the algebraic closure."""
    if [x == 0 for x in u] != [x == 0 for x in v]:
        return False
    if not any(u):
        return True
    for i in range(len(u)):
        for j in range(len(u)):
            if u[i]**weights[j]*v[j]**weights[i] != v[i]**weights[j]*u[j]**weights[i]:
                return False
    return True


def absolute(inv):
    """A normalized representative: divide by the first nonzero invariant to weight 0 when possible."""
    a, b, c, d = inv
    if a:
        return ("A", b/a**2, c/a**3, d/a**5)
    if b:
        return ("B", c**2/b**3, d**2/b**5)
    if c:
        return ("C", d**3/c**5)
    return ("D",)


def substitute(f, m):
    """f(m00 x + m01 y, m10 x + m11 y)."""
    x, y = Poly.variable(0), Poly.variable(1)
    return f.compose([m[0][0]*x+m[0][1]*y, m[1][0]*x+m[1][1]*y])


def orbit_classes(points, family):
    """Group parameter points whose sextics share their Clebsch point (complex GL2 classes)."""
    inv = {p: clebsch(family(*p)) for p in points}
    classes = []
    for p in points:
        for cls in classes:
            if same_weighted_point(inv[cls[0]], inv[p]):
                cls.append(p)
                break
        else:
            classes.append([p])
    return classes, inv


def cubic_gate_identity(f):
    """det L_3(f) = (A^2 - B/6)/16: f has a cubic correction-free partner exactly when B = 6A^2."""
    from .loci import _det
    from .transvectants import gate_matrix
    a, b, _, _ = clebsch(f)
    det = _det(gate_matrix(f, 3, 3))
    return {"det_L3": det, "A2_minus_B_over_6": a*a-b/6, "identity": det == (a*a-b/6)/16}


def quartic_covariant_partner(f):
    """i = (f,f)_4 always satisfies (f,i)_3 = (f,i)_5 = 0; it is active when (f,i)_1 != 0."""
    i = transvectant(f, f, 4)
    zero = Poly()
    return {"gates_vanish": transvectant(f, i, 3) == zero and transvectant(f, i, 5) == zero,
            "active": transvectant(f, i, 1) != zero, "covariant_nonzero": i != zero}


NAMED_FORMS = {"x^6+y^6 (root set fixed by a dihedral group of order 12 in PGL2)": lambda x, y: x**6+y**6,
               "xy(x^4-y^4) (octahedral root set, order 24 in PGL2)": lambda x, y: x*y*(x**4-y**4),
               "x(x^5-y^5) (cyclic root set, order 5 in PGL2)": lambda x, y: x*(x**5-y**5)}


def bounded_partitions(w, parts, largest):
    """Number of partitions of w into at most `parts` parts, each at most `largest`."""
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def count(w, parts, largest):
        if w == 0:
            return 1
        if parts == 0 or largest == 0 or w < 0:
            return 0
        return sum(count(w-k, parts-1, k) for k in range(1, min(largest, w)+1))
    return count(w, parts, largest)


def covariant_count(n, d, m):
    """Cayley-Sylvester: dimension of covariants of degree d and order m of a binary n-ic."""
    if (n*d-m) % 2 or m < 0 or m > n*d:
        return 0
    w = (n*d-m)//2
    return bounded_partitions(w, d, n)-(bounded_partitions(w-1, d, n) if w > 0 else 0)


def invariants_receipt(random_checks=20, seed=7):
    import random
    from .parametric import sextic_family, evaluate, fmt
    from .strata import EXPLAINED_POINTS, surface_discriminant, strata
    from .parametric import dimension
    disc = surface_discriminant()
    pts = [tuple(Q(x) for x in p) for p in EXPLAINED_POINTS]
    pts += [(-a, b) for a, b in pts if a]
    classes, inv = orbit_classes(pts, sextic_family)
    x, y = Poly.variable(0), Poly.variable(1)
    named = {k: clebsch(fn(x, y)) for k, fn in NAMED_FORMS.items()}
    rng = random.Random(seed)
    cubic, quartic = 0, 0
    for _ in range(random_checks):
        f = Poly({(6-i, i): Q(rng.randint(-5, 5)) for i in range(7)})
        cubic += cubic_gate_identity(f)["identity"]
        q = quartic_covariant_partner(f)
        quartic += q["gates_vanish"]
    fam = family_invariants()
    curves = []
    for n in (3, 8, 12):
        for c in strata(n):
            if (dimension(c["equations"], 2) == 1 and len(c["equations"]) == 1 and c["kernel_dimension"] > 0
                    and any(sum(e) > 1 for e in c["equations"][0])):
                curves.append({"degree": n, "curve": fmt(c["equations"][0], ["a", "b"]),
                               "invariant_relation": invariant_relations(c["equations"], 8, fam)})
    return {"invariants": "Clebsch A,B,C,D from unnormalized transvectants; weights 2,4,6,10",
            "cayley_sylvester": {"degree4_invariants": covariant_count(6, 4, 0),
                                 "degree3_invariants": covariant_count(6, 3, 0),
                                 "degree3_order4_covariants": covariant_count(6, 3, 4)},
            "cubic_partner_theorem": {"statement": "det L_3(f) = (A^2 - B/6)/16 for every binary sextic",
                                      "random_sextics_checked": random_checks, "identity_held": cubic},
            "quartic_covariant_partner": {"statement": "(f,(f,f)_4)_3 = (f,(f,f)_4)_5 = 0 for every binary sextic",
                                          "random_sextics_checked": random_checks, "held": quartic},
            "certificates": partner_certificates(),
            "degree12_partner": {"statement": "if A^2 = 25B/96 then G(f) satisfies (f,G)_3 = (f,G)_5 = 0",
                                 "formula": "G = 144A^2 f^2 + 216/5 A iH + 24A f(f,i)_2 - 9/4 i^3 - 9 Delta H + (f,i)_2^2",
                                 "converse": "open; random sextics off the hypersurface have no degree-12 partner"},
            "drop_curves_as_invariant_loci": curves,
            "points": [{"a": str(a), "b": str(b), "squarefree": evaluate(disc, (a, b)) != 0,
                        "absolute": [str(v) for v in absolute(inv[(a, b)])],
                        "equivalent_to": [k for k, v in named.items() if same_weighted_point(inv[(a, b)], v)]}
                       for a, b in pts],
            "classes": [[[str(a), str(b)] for a, b in c] for c in classes],
            "scope": "equal invariants prove GL2(Qbar)-equivalence only for squarefree sextics"}


def family_invariants(family=None, degree=10):
    """A, B, C, D as exact polynomials in the two family parameters (interpolated on a grid)."""
    from .parametric import polynomial_matrix, sextic_family
    family = family or sextic_family
    return polynomial_matrix(lambda a, b: [list(clebsch(family(a, b)))], 2, degree)[0]


def weighted_monomials(weight, weights=WEIGHTS):
    out = []

    def rec(i, left, cur):
        if i == len(weights):
            if left == 0:
                out.append(tuple(cur))
            return
        for k in range(left//weights[i]+1):
            rec(i+1, left-k*weights[i], cur+[k])
    rec(0, weight, [])
    return out


def invariant_relations(equations, max_weight=6, invariants=None, nvars=2):
    """Weighted-homogeneous relations among (A,B,C,D) that hold on V(equations) but not on the whole family.

    Each monomial A^i B^j C^k D^l (weight i+2j+3k+5l, halved degrees) is reduced modulo a
    Groebner basis of the cell; a rational dependence among the normal forms is a relation
    on the cell's closure. Relations that vanish identically on the family are discarded.
    """
    from .parametric import groebner, reduce, mul, const, clean
    from .exact import nullspace
    inv = invariants or family_invariants()
    g = groebner(equations)
    found = []
    for w in range(1, max_weight+1):
        monos = weighted_monomials(w)
        values = []
        for m in monos:
            p = const(1, nvars)
            for base, k in zip(inv, m):
                for _ in range(k):
                    p = mul(p, base)
            values.append(p)
        normal = [reduce(p, g) for p in values]
        keys = sorted({e for p in normal for e in p})
        mat = [[p.get(e, Q(0)) for p in normal] for e in keys]
        for vec in nullspace(mat, len(monos)) if keys else [[Q(int(i == j)) for i in range(len(monos))] for j in range(len(monos))]:
            total = {}
            for c, p in zip(vec, values):
                for e, v in p.items():
                    total[e] = total.get(e, 0)+c*v
            if not clean(total):
                continue  # holds on the whole family
            found.append({"weight": w, "relation": {"*".join(f"{n}^{k}" for n, k in zip("ABCD", m) if k) or "1": c
                                                    for m, c in zip(monos, vec) if c}})
        if found:
            return found
    return found


# ------------------------------------------------- degree-12 partner and certificates


def degree12_partner(f):
    """G(f) = 144A^2 f^2 + 216/5 A iH + 24A f(f,i)_2 - 9/4 i^3 - 9 Delta H + (f,i)_2^2, H=(f,f)_2."""
    a, _, _, _ = clebsch(f)
    i = transvectant(f, f, 4)
    h = transvectant(f, f, 2)
    delta = transvectant(i, i, 2)
    fi2 = transvectant(f, i, 2)
    return (144*a*a*f*f+Q(216, 5)*a*i*h+24*a*f*fi2-Q(9, 4)*i*i*i-9*delta*h+fi2*fi2)


def degree12_gate_identities(f):
    """(f,G)_3 = -432 s (f,H)_1 and (f,G)_5 = 25920 s (f,i)_1 with s = A^2 - 25B/96."""
    a, b, _, _ = clebsch(f)
    s = a*a-Q(25, 96)*b
    g = degree12_partner(f)
    h = transvectant(f, f, 2)
    i = transvectant(f, f, 4)
    return (transvectant(f, g, 3) == transvectant(f, h, 1)*(-432*s)
            and transvectant(f, g, 5) == transvectant(f, i, 1)*(25920*s))


def slice_form(p, q, r):
    """xy(x-y)(x^3+p x^2y+q xy^2+r y^3): roots 0, 1, infinity fixed; its GL2-orbit is dense."""
    x, y = Poly.variable(0), Poly.variable(1)
    return x*y*(x-y)*(x**3+Q(p)*x*x*y+Q(q)*x*y*y+Q(r)*y**3)


def grid_certificate(identity, degree):
    """Check a covariant identity of coefficient degree <= degree on the grid {0..degree}^3 of the slice.

    Both sides are covariants of the same degree, order and weight, so the set of sextics
    where the identity holds is closed and GL2-stable. The slice's GL2-orbit is dense, so
    the identity holds for every sextic once it holds on the slice; and a polynomial in
    (p,q,r) of degree <= degree in each variable vanishing on a grid with degree+1 values
    per coordinate is zero.
    """
    pts = [(p, q, r) for p in range(degree+1) for q in range(degree+1) for r in range(degree+1)]
    failures = [pt for pt in pts if not identity(slice_form(*pt))]
    return {"grid_points": len(pts), "degree_bound": degree, "failures": failures[:5], "certified": not failures}


def partner_certificates(include_degree12=True):
    out = {"cubic: det L_3 = (A^2-B/6)/16": grid_certificate(lambda f: cubic_gate_identity(f)["identity"], 4),
           "quartic: (f,(f,f)_4)_3 = (f,(f,f)_4)_5 = 0": grid_certificate(
               lambda f: quartic_covariant_partner(f)["gates_vanish"], 3)}
    if include_degree12:
        out["degree 12: (f,G)_3, (f,G)_5 divisible by A^2-25B/96"] = grid_certificate(degree12_gate_identities, 7)
    return out
