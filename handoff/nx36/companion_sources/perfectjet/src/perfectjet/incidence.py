"""Partner incidence over the full sextic space: hypersurface components and their invariants.

For each degree N, the set P_N = {f : ker L_N(f) larger than generic} is closed and
GL2-invariant in the seven-dimensional space of binary sextics. A line f0 + t f1 meets
every hypersurface component of P_N whose defining invariant J has J(f1) != 0, and
generically misses components of codimension two or more. Along the line, the exact
one-parameter locus (loci.rank_locus) is therefore the restriction of the hypersurface
part of P_N. Its degree is the degree of that hypersurface, and dividing invariant
monomials of the matching weight by it identifies the defining invariant exactly.

Lower-dimensional components (for example the octahedral jump in degree 4 or the
isolated degree-5 partners) are not seen by lines; `slice_cells` handles the small
degrees on the dense slice xy(x-y)(x^3+px^2y+qxy^2+ry^3) instead.
"""
import random
from fractions import Fraction as Q
from .polynomial import Poly
from .loci import polynomial_matrix, rank_locus, degree, interpolate, pdivmod, trim
from .transvectants import gate_matrix
from .invariants import clebsch, weighted_monomials
from .exact import nullspace


def random_line(seed, height=4):
    rng = random.Random(seed)
    return [Poly({(6-i, i): Q(rng.randint(-height, height)) for i in range(7)}) for _ in range(2)]


def correction_matrix(f, n):
    return gate_matrix(f, n, 3)+gate_matrix(f, n, 5)


def line_probe(n, line):
    """Generic kernel dimension of L_N and the hypersurface part of the jump locus along a line."""
    f0, f1 = line
    m = polynomial_matrix(lambda t: correction_matrix(f0+t*f1, n), 1)
    r = rank_locus(m)
    return {"degree": n, "generic_kernel": n+1-r["generic_rank"], "locus": r["locus"],
            "hypersurface_degree": degree(r["locus"]),
            "jumps": [{"factor_degree": degree(f["factor"]), "kernel": n+1-f["rank"]} for f in r["factors"]]}


def invariants_on_line(line):
    """A, B, C, D of f0 + t f1 as exact polynomials in t (degrees <= 2, 4, 6, 10)."""
    f0, f1 = line
    nodes = list(range(11))
    vals = [clebsch(f0+Q(t)*f1) for t in nodes]
    return [interpolate(nodes, [v[k] for v in vals]) for k in range(4)]


def _pow_mul(polys, exps):
    from .loci import pmul
    out = [Q(1)]
    for p, k in zip(polys, exps):
        for _ in range(k):
            out = pmul(out, p)
    return out


def identify_hypersurface(locus, line, max_weight=6):
    """Lowest-weight invariant J(A,B,C,D) whose restriction to the line is a multiple of the locus.

    Returns the relation and whether its restriction equals the locus up to a constant,
    which is the exact statement that the hypersurface part of P_N is V(J) on this line.
    """
    inv = invariants_on_line(line)
    target = trim(locus)
    for w in range(1, max_weight+1):
        monos = weighted_monomials(w)
        restricted = [_pow_mul(inv, m) for m in monos]
        remainders = [trim(pdivmod(p, target)[1]) for p in restricted]
        width = max((len(r) for r in remainders), default=0)
        mat = [[(r[i] if i < len(r) else Q(0)) for r in remainders] for i in range(width)]
        sols = nullspace(mat, len(monos)) if width else [[Q(int(i == j)) for i in range(len(monos))]
                                                       for j in range(len(monos))]
        for s in sols:
            comb = [Q(0)]*max(len(p) for p in restricted)
            for c, p in zip(s, restricted):
                for i, v in enumerate(p):
                    comb[i] += c*v
            comb = trim(comb)
            if not comb:
                continue
            quotient, rem = pdivmod(comb, target)
            assert not rem
            return {"weight": w, "coefficient_degree": 2*w,
                    "relation": {"*".join(f"{n}^{k}" for n, k in zip("ABCD", m) if k): c
                                 for m, c in zip(monos, s) if c},
                    "restriction_equals_locus": degree(quotient) == 0}
    return None


def partner_table(degrees=range(3, 17), seeds=(1, 2)):
    """Per degree: generic kernel and the hypersurface component of the jump locus, on independent lines."""
    rows = []
    for n in degrees:
        per_line = []
        for s in seeds:
            line = random_line(s)
            pr = line_probe(n, line)
            ident = identify_hypersurface(pr["locus"], line) if pr["hypersurface_degree"] > 0 else None
            per_line.append({"seed": s, "hypersurface_degree": pr["hypersurface_degree"], "jumps": pr["jumps"],
                             "generic_kernel": pr["generic_kernel"], "invariant": ident})
        rows.append({"degree": n, "generic_kernel": per_line[0]["generic_kernel"], "lines": per_line})
    return rows


# ------------------------------------------------- exact covariants over a quotient ring


class QuotientRing:
    """Q[t1..tk]/I with I given by a Groebner basis; elements are normal-form dicts."""

    def __init__(self, gb, nvars):
        self.gb, self.n = gb, nvars

    def nf(self, p):
        from .parametric import reduce
        return reduce(p, self.gb) if self.gb else dict(p)

    def mul(self, a, b):
        from .parametric import mul
        return self.nf(mul(a, b))

    def add(self, a, b):
        from .parametric import add
        return add(a, b)

    def scale(self, a, c):
        from .parametric import scale
        return scale(a, Q(c))

    def const(self, c):
        from .parametric import const
        return const(c, self.n)


def _fd(ring, c, ox, oy):
    """Partial derivatives of a binary form given by coefficients of x^(m-i) y^i."""
    for _ in range(ox):
        m = len(c)-1
        c = [ring.scale(c[i], m-i) for i in range(m)] if m > 0 else [{}]
    for _ in range(oy):
        m = len(c)-1
        c = [ring.scale(c[i+1], i+1) for i in range(m)] if m > 0 else [{}]
    return c


def _fmul(ring, a, b):
    out = [{} for _ in range(len(a)+len(b)-1)]
    for i, x in enumerate(a):
        if not x:
            continue
        for j, y in enumerate(b):
            if y:
                out[i+j] = ring.add(out[i+j], ring.mul(x, y))
    return out


def form_transvectant(ring, f, g, k):
    from math import comb
    out = None
    for i in range(k+1):
        term = [ring.scale(c, (-1)**i*comb(k, i)) for c in _fmul(ring, _fd(ring, f, k-i, i), _fd(ring, g, i, k-i))]
        out = term if out is None else [ring.add(x, y) for x, y in zip(out, term)]
    return out


def clebsch_over(ring, f):
    t = lambda a, b, k: form_transvectant(ring, a, b, k)
    i = t(f, f, 4)
    delta = t(i, i, 2)
    y1 = t(f, i, 4)
    y2 = t(i, y1, 2)
    y3 = t(i, y2, 2)
    return [t(f, f, 6)[0], t(i, i, 4)[0], t(i, delta, 4)[0], t(y3, y1, 2)[0]]


def slice_coefficients(nvars=3):
    """Coefficients of xy(x-y)(x^3+p x^2y+q xy^2+r y^3) as polynomials in (p,q,r)."""
    from .parametric import var, const, sub
    p, q, r = (var(i, nvars) for i in range(3))
    one = const(1, nvars)
    return [{}, one, sub(p, one), sub(q, p), sub(r, q), {k: -v for k, v in r.items()}, {}]


def degree5_ideal():
    """Ideal of the degree-5 partner locus on the slice, saturated away from repeated roots at 0 and 1."""
    import itertools
    from .parametric import groebner, saturate_by, var, add, const, polynomial_matrix as pmat
    from .strata import bareiss_det
    from .invariants import slice_form
    m = pmat(lambda p, q, r: correction_matrix(slice_form(p, q, r), 5), 3, 1)
    minors = [d for rows in itertools.combinations(range(len(m)), 6) if (d := bareiss_det([m[i] for i in rows], 3))]
    g = groebner(minors)
    p, q, r = var(0, 3), var(1, 3), var(2, 3)
    g = saturate_by(g, r, 3)
    return saturate_by(g, add(add(add(p, q), r), const(1, 3)), 3)


def quotient_dimension(gb, nvars, bound=16):
    import itertools
    from .parametric import lead, _divides
    leads = [lead(x)[0] for x in gb]
    return sum(1 for e in itertools.product(range(bound), repeat=nvars) if not any(_divides(l, e) for l in leads))


def degree5_classification():
    """Every slice sextic with a degree-5 partner has the Clebsch point of x^6 + 40/7 x^3y^3 + y^6.

    Exact: B - 486 A^2, C + 26244 A^3 and D + 419904 A^5 reduce to zero modulo the locus
    ideal, and A is a unit there (the ideal plus A is the unit ideal).
    """
    from .parametric import groebner, is_unit_ideal
    g = degree5_ideal()
    ring = QuotientRing(g, 3)
    a, b, c, d = clebsch_over(ring, slice_coefficients())
    a2 = ring.mul(a, a)
    a3 = ring.mul(a2, a)
    a5 = ring.mul(a3, a2)
    rel = {"B-486A^2": ring.nf(ring.add(b, ring.scale(a2, -486))) == {},
           "C+26244A^3": ring.nf(ring.add(c, ring.scale(a3, 26244))) == {},
           "D+419904A^5": ring.nf(ring.add(d, ring.scale(a5, 419904))) == {}}
    from .polynomial import Poly
    from .invariants import clebsch
    x, y = Poly.variable(0), Poly.variable(1)
    ca, cb, cc, cd = clebsch(x**6+Q(40, 7)*x**3*y**3+y**6)
    target = {"B/A^2": cb/ca**2, "C/A^3": cc/ca**3, "D/A^5": cd/ca**5}
    return {"slice_points_with_multiplicity": quotient_dimension(g, 3), "relations_hold": rel,
            "A_is_unit": is_unit_ideal(groebner(g+[a])) if a else False, "C3_40_over_7_absolute": target}


# ------------------------------------------------- zero-dimensional jump loci on the slice


def standard_monomials(gb, nvars, bound=24):
    import itertools
    from .parametric import lead, _divides, _key
    leads = [lead(x)[0] for x in gb]
    std = [e for e in itertools.product(range(bound), repeat=nvars) if not any(_divides(l, e) for l in leads)]
    return sorted(std, key=_key)


def element_matrix(ring, element, std):
    """Matrix of multiplication by `element` on Q[t]/I in the standard-monomial basis."""
    idx = {e: i for i, e in enumerate(std)}
    cols = []
    for e in std:
        nf = ring.mul(element, {e: Q(1)})
        col = [Q(0)]*len(std)
        for mono, c in nf.items():
            col[idx[mono]] = c
        cols.append(col)
    return [list(r) for r in zip(*cols)]


def minimal_polynomial(mat):
    """Monic minimal polynomial of a rational matrix acting on Q^n (Krylov on the unit vectors)."""
    from .exact import rank
    from .loci import pgcd, trim
    n = len(mat)

    def apply(v):
        return [sum((a*b for a, b in zip(row, v)), Q(0)) for row in mat]

    def local(v):
        seq = [v]
        while rank(seq+[apply(seq[-1])], n) > len(seq):
            seq.append(apply(seq[-1]))
        nxt = apply(seq[-1])
        k = len(seq)
        aug = [[seq[j][i] for j in range(k)]+[nxt[i]] for i in range(n)]
        from .exact import rref
        rr, piv = rref(aug, k+1)
        coef = [Q(0)]*k
        for i, p in enumerate(piv):
            coef[p] = rr[i][-1]
        return trim([-c for c in coef]+[Q(1)])
    from .loci import pmul, pdivmod
    out = [Q(1)]
    for i in range(n):
        e = [Q(int(j == i)) for j in range(n)]
        m = local(e)
        g = pgcd(out, m)
        out = trim(pdivmod(pmul(out, m), g)[0])
    return [c/out[-1] for c in out]


def unit_inverse(ring, element, std):
    """Inverse of a unit in Q[t]/I, as a normal-form dict."""
    from .exact import rref
    m = element_matrix(ring, element, std)
    n = len(std)
    one = [Q(int(e == (0,)*ring.n)) for e in std]
    rr, piv = rref([row+[b] for row, b in zip(m, one)], n+1)
    if n in piv:
        raise ZeroDivisionError("not a unit")
    sol = [Q(0)]*n
    for i, p in enumerate(piv):
        sol[p] = rr[i][-1]
    return {e: c for e, c in zip(std, sol) if c}


def jump_ideal(n, kernel, nvars=3):
    """Slice ideal where dim ker L_N >= kernel, saturated away from repeated roots at 0 and 1."""
    import itertools
    from .parametric import groebner, saturate_by, var, add, const, polynomial_matrix as pmat
    from .strata import bareiss_det
    from .invariants import slice_form
    m = pmat(lambda p, q, r: correction_matrix(slice_form(p, q, r), n), 3, 1)
    size = n+1-kernel+1  # rank <= n+1-kernel  <=>  all minors of this size vanish
    minors = []
    for rows in itertools.combinations(range(len(m)), size):
        for cols in itertools.combinations(range(n+1), size):
            d = bareiss_det([[m[i][j] for j in cols] for i in rows], 3)
            if d:
                minors.append(d)
    g = groebner(minors)
    p, q, r = var(0, 3), var(1, 3), var(2, 3)
    g = saturate_by(g, r, 3)
    return saturate_by(g, add(add(add(p, q), r), const(1, 3)), 3)


def classify_zero_dimensional(g):
    """Minimal polynomials of the absolute invariants B/A^2, C/A^3, D/A^5 over a 0-dimensional slice locus."""
    from .parametric import dimension, is_unit_ideal, groebner
    from .loci import rational_roots
    if dimension(g, 3) != 0:
        raise ValueError("locus is not zero-dimensional")
    ring = QuotientRing(g, 3)
    std = standard_monomials(g, 3)
    a, b, c, d = clebsch_over(ring, slice_coefficients())
    if not is_unit_ideal(groebner(g+[a])) if a else True:
        return {"points": len(std), "A_unit": False}
    ai = unit_inverse(ring, a, std)
    ai2 = ring.mul(ai, ai)
    ai3 = ring.mul(ai2, ai)
    ai5 = ring.mul(ai3, ai2)
    out = {"points": len(std), "A_unit": True}
    for name, num, den in (("B/A^2", b, ai2), ("C/A^3", c, ai3), ("D/A^5", d, ai5)):
        mp = minimal_polynomial(element_matrix(ring, ring.mul(num, den), std))
        out[name] = {"minimal_polynomial": [str(x) for x in mp], "rational_values": [str(v) for v in rational_roots(mp)]}
    return out


def relations_on_locus(g, max_weight=8):
    """Lowest-weight relations J(A,B,C,D)=0 holding on V(g) (A,B,C,D are algebraically independent)."""
    from .exact import nullspace
    ring = QuotientRing(g, 3)
    inv = clebsch_over(ring, slice_coefficients())
    found = []
    for w in range(1, max_weight+1):
        monos = weighted_monomials(w)
        vals = []
        for m in monos:
            v = ring.const(1)
            for base, k in zip(inv, m):
                for _ in range(k):
                    v = ring.mul(v, base)
            vals.append(v)
        keys = sorted({e for v in vals for e in v})
        mat = [[v.get(e, Q(0)) for v in vals] for e in keys]
        for s in (nullspace(mat, len(monos)) if keys else []):
            found.append({"weight": w, "relation": {"*".join(f"{n}^{k}" for n, k in zip("ABCD", m) if k): c
                                                    for m, c in zip(monos, s) if c}})
        if found:
            return found
    return found


def slice_jump(n, kernel):
    from .parametric import dimension, is_unit_ideal
    g = jump_ideal(n, kernel)
    if is_unit_ideal(g):
        return {"degree": n, "kernel_at_least": kernel, "dimension": -1}
    dim = dimension(g, 3)
    out = {"degree": n, "kernel_at_least": kernel, "dimension": dim}
    if dim == 0:
        out["classification"] = classify_zero_dimensional(g)
    elif dim in (1, 2):
        out["relations"] = relations_on_locus(g)
    return out


# ---------------------------------------------- sextics with fewer than three simple roots


def degenerate_forms():
    """Every sextic with fewer than three simple roots is GL2-equivalent to one of these, or to s_form(s)."""
    x, y = Poly.variable(0), Poly.variable(1)
    return {"x^6": x**6, "x^5y": x**5*y, "x^4y^2": x**4*y**2, "x^3y^3": x**3*y**3,
            "x^4y(x-y)": x**4*y*(x-y), "x^3y^2(x-y)": x**3*y**2*(x-y), "x^2y^2(x-y)^2": x**2*y**2*(x-y)**2}


def s_form(s):
    x, y = Poly.variable(0), Poly.variable(1)
    return x**2*y**2*(x-y)*(x-Q(s)*y)


def degenerate_profile(degrees=range(3, 13)):
    from .loci import rational_roots
    out = {"fixed": {}, "x^2y^2(x-y)(x-sy)": []}
    for name, f in degenerate_forms().items():
        out["fixed"][name] = [{"degree": n, "kernel": n+1-_rank(correction_matrix(f, n), n+1)}
                              for n in degrees if n+1-_rank(correction_matrix(f, n), n+1)]
    for n in degrees:
        m = polynomial_matrix(lambda s: correction_matrix(s_form(s), n), 1)
        r = rank_locus(m)
        jumps = [{"factor": [str(c) for c in f["factor"]], "kernel": n+1-f["rank"],
                  "rational_s": [str(v) for v in rational_roots(f["factor"]) if v not in (0, 1)]}
                 for f in r["factors"]]
        out["x^2y^2(x-y)(x-sy)"].append({"degree": n, "generic_kernel": n+1-r["generic_rank"], "jumps": jumps})
    return out


def _rank(m, ncols):
    from .exact import rank
    return rank(m, ncols) if m else 0


THEOREMS = [
    {"degree": 3, "statement": "ker L_3(f) != 0 iff B = 6A^2; dim ker L_3 >= 2 (three simple roots) iff f ~ x^6+y^6",
     "status": "exact: det identity certified on the slice; jump classified on the slice"},
    {"degree": 4, "statement": "dim ker L_4 >= 1 always ((f,f)_4); >= 2 iff f ~ xy(x^4-y^4) or f has a root of multiplicity >= 5",
     "status": "exact on the slice plus the degenerate forms"},
    {"degree": 5, "statement": "ker L_5(f) != 0 iff f ~ x^6+40/7 x^3y^3+y^6 or f has a root of multiplicity >= 4; never >= 2 on the slice",
     "status": "exact on the slice plus the degenerate forms"},
    {"degree": 6, "statement": "dim ker L_6 >= 2 iff f has a root of multiplicity >= 4",
     "status": "conditional global classification: archived msolve over Q; independent two-prime evidence and exact degenerate-form replay"},
    {"degree": 7, "statement": "ker L_7 != 0 iff f has a root of multiplicity >= 4",
     "status": "conditional global classification: archived msolve over Q; independent two-prime evidence and exact degenerate-form replay"},
    {"degree": 8, "statement": "ker L_8 != 0 iff f has a root of multiplicity >= 4 or an automorphism of order 3 (f ~ x^6+lambda x^3y^3+y^6 or x^3y^3)",
     "status": "converse exact; forward classification conditional on archived msolve over Q, supported by modular and numerical evidence"},
    {"degree": "9-20", "statement": "odd N: extra partners iff a root of multiplicity >= 4; N=10 adds x^3y^3 and x^6+y^6; N=14 adds x^3y^3 and the octahedral sextic; N=12 is governed by A^2=25B/96; N=16,18,20 add x^3y^3",
     "status": "slice verdicts over Q by msolve and modulo two primes by Singular; degenerate forms exact"},
    {"degree": 12, "statement": "ker L_12 != 0 iff A^2 = 25B/96 over the algebraic closure; sufficiency uses G and closedness",
     "status": "conditional global converse: archived msolve over Q; exact covariant construction and degenerate profiles"},
]


def incidence_receipt(line_degrees=range(3, 13), seed=1):
    line = random_line(seed)
    table = []
    for n in line_degrees:
        pr = line_probe(n, line)
        row = {"degree": n, "generic_kernel": pr["generic_kernel"], "hypersurface_degree": pr["hypersurface_degree"]}
        if pr["hypersurface_degree"]:
            row["invariant"] = identify_hypersurface(pr["locus"], line)
        table.append(row)
    return {"method": "Exact restrictions on seeded lines; genericity is not certified. Dense slice for lower-dimensional loci",
            "hypersurfaces": table,
            "slice_jumps": [slice_jump(3, 2), slice_jump(4, 2), slice_jump(5, 1), slice_jump(5, 2)],
            "quintic_certificate": degree5_classification(),
            "degenerate_forms": degenerate_profile(range(3, 13)),
            "theorems": THEOREMS}


# --------------------------------------------------- modular emptiness for degrees 6 and 7


def slice_locus_empty_mod_p(n, kernel, prime=None):
    """Is {dim ker L_N >= kernel} empty on the slice away from repeated roots at 0 and 1, modulo a prime?

    Evidence rather than proof: a rational ideal with a point over the algebraic closure
    reduces to a proper ideal modulo every prime outside a finite bad set.
    """
    from . import modular
    from .parametric import var, add, const, mul, polynomial_matrix as pmat
    from .invariants import slice_form
    old = modular.P
    if prime:
        modular.P = prime
    try:
        m = pmat(lambda p, q, r: correction_matrix(slice_form(p, q, r), n), 3, 1)
        ideal = modular.ideal_of_minors(m, n+2-kernel, 3)
        p, q, r = var(0, 3), var(1, 3), var(2, 3)
        avoid = modular.to_mod(mul(r, add(add(add(p, q), r), const(1, 3))))
        return {"degree": n, "kernel_at_least": kernel, "prime": modular.P, "minors": len(ideal),
                "empty": modular.saturated_unit(ideal, avoid, 3)}
    finally:
        modular.P = old


# ------------------------------------------------------------- degree 8 and order-3 symmetry


def c3_degree8_certificate():
    """g8 = xy(x^6+y^6-7/20 lambda x^3y^3) is a partner of x^6+lambda x^3y^3+y^6 for every lambda.

    The gate coefficients are polynomials in lambda of degree at most 2, so vanishing at
    three values of lambda proves vanishing identically; five are checked.
    """
    from .transvectants import c3_family, transvectant
    zero = Poly()
    rows = []
    for lam in range(-2, 3):
        f, _, g8 = c3_family(Q(lam))
        rows.append(transvectant(f, g8, 3) == zero and transvectant(f, g8, 5) == zero)
    return {"lambdas_checked": 5, "degree_bound_in_lambda": 2, "identity": all(rows)}


def c3_curve_relations():
    """Invariant relations of x^6+lambda x^3y^3+y^6: R5 = AB^2+BC/6-9D/2 = 0 and C^2 = 6B^3."""
    from .transvectants import c3_family
    from .loci import interpolate
    nodes = list(range(12))
    vals = [clebsch(c3_family(Q(t))[0]) for t in nodes]
    a, b, c, d = (interpolate(nodes, [v[k] for v in vals]) for k in range(4))
    from .loci import pmul, padd, trim
    r5 = trim(padd(padd(pmul(a, pmul(b, b)), [x/6 for x in pmul(b, c)]), [-Q(9, 2)*x for x in d]))
    c6 = trim(padd(pmul(c, c), [-6*x for x in pmul(b, pmul(b, b))]))
    return {"R5_vanishes": not r5, "C2_minus_6B3_vanishes": not c6}


def slice_invariants():
    """A, B, C, D of the slice form as exact polynomials in (p, q, r)."""
    return clebsch_over(QuotientRing([], 3), slice_coefficients())


def degree8_relations(seed=1, plane=True, projections=10):
    """Modulo P: R5 and C^2-6B^3 vanish wherever ker L_8 != 0 on the slice (off repeated roots at 0, 1).

    The zero set is cut out by random projections det(R L_8), which contain the true locus, so a
    relation vanishing there vanishes on the locus. With plane=True the slice is first intersected
    with a random plane r = al p + be q + ga (finite, fast; meets every curve component); with
    plane=False the full three-variable radical test is run (slower; also covers isolated points).
    """
    import random
    from . import modular as M
    from .parametric import var, add, const, mul, scale, sub, polynomial_matrix as pmat
    from .invariants import slice_form
    rng = random.Random(seed)
    nv = 2 if plane else 3
    al, be, ga = (rng.randrange(1, M.P) for _ in range(3))
    lin = {(1, 0): al, (0, 1): be, (0, 0): ga}
    powers = {0: {(0, 0): 1}}

    def lp(k):
        if k not in powers:
            powers[k] = M.mul_mod(lp(k-1), lin)
        return powers[k]

    def restrict(p):
        if not plane:
            return p
        out = {}
        for (a, b, c), v in p.items():
            for e, w in lp(c).items():
                f = (e[0]+a, e[1]+b)
                out[f] = (out.get(f, 0)+v*w) % M.P
        return M._clean(out)
    m = pmat(lambda p, q, r: correction_matrix(slice_form(p, q, r), 8), 3, 1)
    mm = [[restrict(M.to_mod(x)) for x in row] for row in m]
    dets = []
    for _ in range(projections):
        rmat = [[rng.randrange(M.P) for _ in range(len(mm))] for _ in range(9)]
        rows = []
        for i in range(9):
            row = []
            for j in range(9):
                acc = {}
                for l in range(len(mm)):
                    for e, c in mm[l][j].items():
                        acc[e] = (acc.get(e, 0)+rmat[i][l]*c) % M.P
                row.append(M._clean(acc))
            rows.append(row)
        dets.append(M.det_mod(rows, nv))
    p, q, r = var(0, 3), var(1, 3), var(2, 3)
    h = restrict(M.to_mod(mul(r, add(add(add(p, q), r), const(1, 3)))))
    a, b, c, d = slice_invariants()
    rels = {"R5": add(add(mul(a, mul(b, b)), scale(mul(b, c), Q(1, 6))), scale(d, Q(-9, 2))),
            "C^2-6B^3": sub(mul(c, c), scale(mul(b, mul(b, b)), 6)), "A (control)": a}
    out = {"prime": M.P, "plane": plane}
    for name, rel in rels.items():
        out[name] = M.saturated_unit(dets, M.mul_mod(h, restrict(M.to_mod(rel))), nv)
    return out


def projected_slice_test(n, relations=None, seed=1, projections=12, prime=None, check_empty=True):
    """Modulo a prime: is {ker L_N != 0} empty on the slice off repeated roots at 0 and 1, and which
    invariant relations vanish on it?

    Random projections det(R L_N) (R of size (N+1) x rows) vanish wherever L_N drops rank, so their
    common zero set contains the locus: emptiness of the superset implies emptiness of the locus, and
    a relation vanishing on the superset vanishes on the locus.
    """
    import random
    from . import modular as M
    from .parametric import var, add, const, mul, polynomial_matrix as pmat
    from .invariants import slice_form
    old = M.P
    if prime:
        M.P = prime
    try:
        rng = random.Random(seed)
        m = pmat(lambda p, q, r: correction_matrix(slice_form(p, q, r), n), 3, 1)
        mm = [[M.to_mod(x) for x in row] for row in m]
        dets = []
        for _ in range(projections):
            rmat = [[rng.randrange(M.P) for _ in range(len(mm))] for _ in range(n+1)]
            rows = []
            for i in range(n+1):
                row = []
                for j in range(n+1):
                    acc = {}
                    for l in range(len(mm)):
                        for e, c in mm[l][j].items():
                            acc[e] = (acc.get(e, 0)+rmat[i][l]*c) % M.P
                    row.append(M._clean(acc))
                rows.append(row)
            dets.append(M.det_mod(rows, 3))
        p, q, r = var(0, 3), var(1, 3), var(2, 3)
        h = M.to_mod(mul(r, add(add(add(p, q), r), const(1, 3))))
        out = {"degree": n, "prime": M.P}
        if check_empty:
            out["empty"] = M.saturated_unit(dets, h, 3)
        for name, rel in (relations or {}).items():
            out[name] = M.saturated_unit(dets, M.mul_mod(h, M.to_mod(rel)), 3)
        return out
    finally:
        M.P = old
