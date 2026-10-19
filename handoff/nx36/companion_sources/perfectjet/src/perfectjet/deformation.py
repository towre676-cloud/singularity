"""Deformation-aware tests of relations among stationary states.

A potential V(x; theta) has stationary points x*_s at theta = 0 (exact, rational). A
relation R(x*_1, ..., x*_r) = 0 holds there. Within the declared perturbation space,
the implicit function theorem gives

    dx*_s/dtheta = -H_s^{-1} M_s,   H_s = d2V/dx2,  M_s = d2V/dx dtheta  at (x*_s, 0),

and the first-order response dR/dtheta_j = sum_s grad_s R . dx*_s/dtheta_j. Directions
with dR != 0 break the relation; a symmetry protects it when every perturbation fixed
by the symmetry lies in the kernel of dR. A relation that holds at theta = 0 but has a
breaking direction inside the declared space is accidental for that space.
"""
from fractions import Fraction as Q
from .polynomial import Poly
from .exact import nullspace, rank, matmul, transpose
from .readout import inverse


def _grad(p, idx):
    out = []
    for i in idx:
        e = [0]*p.variables
        e[i] = 1
        out.append(p.derivative(tuple(e)))
    return out


def _at(p, point):
    return p.evaluate(point)


def stationary_response(potential, nx, point):
    """dx*/dtheta at a nondegenerate stationary point (variables: x_0..x_{nx-1}, then theta)."""
    nv = potential.variables
    xs, ts = list(range(nx)), list(range(nx, nv))
    grads = _grad(potential, xs)
    if any(_at(g, point) for g in grads):
        raise ValueError("point is not stationary at theta = 0")
    h = [[_at(gi, point) for gi in _grad(g, xs)] for g in grads]
    m = [[_at(gi, point) for gi in _grad(g, ts)] for g in grads]
    if rank(h) < nx:
        raise ValueError("degenerate stationary point: Hessian is singular")
    hinv = inverse(h)
    return [[-v for v in row] for row in matmul(hinv, m)], h


def relation_response(potential, nx, points, relation_grads):
    """First-order change of R along each perturbation direction; relation_grads[s] = dR/dx*_s."""
    nt = potential.variables-nx
    total = [Q(0)]*nt
    for pt, g in zip(points, relation_grads):
        dx, _ = stationary_response(potential, nx, pt)
        for j in range(nt):
            total[j] += sum((Q(g[i])*dx[i][j] for i in range(nx)), Q(0))
    return total


def protection(potential, nx, points, relation_grads, symmetry=None):
    """Breaking directions, the preserving subspace, and whether a symmetry protects the relation.

    symmetry: list of matrices acting on theta (the induced action of a group that maps
    the stationary set to itself and preserves R). Its fixed perturbations are the
    common kernel of (S - I).
    """
    d = relation_response(potential, nx, points, relation_grads)
    nt = len(d)
    preserving = nullspace([d], nt) if any(d) else [[Q(int(i == j)) for i in range(nt)] for j in range(nt)]
    witness = None
    if any(d):
        j = next(j for j, v in enumerate(d) if v)
        witness = {"direction": [Q(int(i == j)) for i in range(nt)], "dR": d[j]}
    out = {"dR_dtheta": d, "breaking_witness": witness, "preserving_dimension": len(preserving),
           "verdict": "protected for the declared perturbation space" if not any(d) else "accidental: broken at first order"}
    if symmetry:
        rows = []
        for sm in symmetry:
            rows += [[Q(sm[i][j])-Q(int(i == j)) for j in range(nt)] for i in range(nt)]
        fixed = nullspace(rows, nt) if any(any(r) for r in rows) else [[Q(int(i == j)) for i in range(nt)] for j in range(nt)]
        protected = all(sum((a*b for a, b in zip(d, v)), Q(0)) == 0 for v in fixed)
        out["symmetric_perturbations"] = fixed
        out["symmetry_protects"] = protected
        if protected and any(d):
            out["verdict"] = "protected by the symmetry; broken only by symmetry-breaking perturbations"
    return out


def deformation_receipt():
    # V = x^4/4 - x^2/2 + t1 x + t2 x^3 + t3 x^2 ; minima at x = +/-1 when t = 0.
    x = Poly.variable(0, 4)
    t1, t2, t3 = (Poly.variable(i, 4) for i in (1, 2, 3))
    v = x**4*Q(1, 4)-x**2*Q(1, 2)+t1*x+t2*x**3+t3*x**2
    pts = [(Q(1), 0, 0, 0), (Q(-1), 0, 0, 0)]
    # Relation: x*_+ + x*_- = 0 (mirror-symmetric minima). grad wrt each point's x is 1.
    sym = [[[-1, 0, 0], [0, -1, 0], [0, 0, 1]]]  # x -> -x maps t1 -> -t1, t2 -> -t2, keeps t3
    mirror = protection(v, 1, pts, [[1], [1]], sym)
    # Relation: x*_+ = 1 exactly (a "nice number"): broken by every perturbation that moves the minimum.
    value = protection(v, 1, pts[:1], [[1]], sym)
    return {"potential": "x^4/4 - x^2/2 + t1 x + t2 x^3 + t3 x^2", "mirror_relation": mirror,
            "location_relation": value}
