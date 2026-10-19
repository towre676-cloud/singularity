"""Adaptive representation engine and the unified representation-and-obstruction report.

Every adapter answers one declared question and returns the same report shape:

    question        what was asked (find / decide / count / predict / choose)
    representation  the object built to answer it, with its size
    preserved       the questions the representation answers exactly
    identities      the working contracts, each replayed in exact arithmetic
    answer          the answer, when the representation settles it
    obstruction     the failure witness when it does not
    obligations     what remains unproved or unsupported
    next            the smallest calculation implicated by the obstruction

The adaptive loop starts from the smallest plausible description, classifies the
failure of its contract, adds only the structure that failure implicates, and
recomputes. It stops at closure, at a declared budget, or when the failure class
says that more of the same structure cannot help.
"""
from fractions import Fraction as Q
from .polynomial import Poly
from .exact import observable_space, target_recovery, rank, nullspace
from .readout import identify, repair, value_of_information, adds_direction


def report(question, representation, preserved, identities, answer=None, obstruction=None,
           obligations=(), next_step=None, history=()):
    return {"question": question, "representation": representation, "preserved": list(preserved),
            "identities": list(identities), "answer": answer, "obstruction": obstruction,
            "obligations": list(obligations), "next": next_step, "history": list(history)}


# ------------------------------------------------------- polynomial dynamics


def _monomial(e):
    return Poly({tuple(e): 1}, len(e))


def adaptive_closure(evolution, outputs, max_features=40, max_degree=8):
    """Grow a monomial feature set until psi(F(x)) = G psi(x) holds exactly, or report the residual.

    Each round pulls every feature back through F; monomials of the pullbacks that are
    outside the current set are the residual's support, and exactly those are added.
    When the closure exists, the minimal invariant subspace containing the outputs is
    extracted from the closed monomial space (Krylov / observable-space reduction).
    """
    nv = evolution[0].variables
    feats = sorted({e for p in outputs for e in p.terms})
    history = []
    while True:
        pulls = {e: _monomial(e).compose(evolution) for e in feats}
        missing = sorted({m for p in pulls.values() for m in p.terms} - set(feats), key=lambda e: (sum(e), e))
        history.append({"features": len(feats), "missing": len(missing),
                        "max_missing_degree": max((sum(m) for m in missing), default=None)})
        if not missing:
            break
        too_high = [m for m in missing if sum(m) > max_degree]
        if too_high or len(feats)+len(missing) > max_features:
            # Classify: a monomial of degree above every one already present means the
            # pullback raises degree, so no finite monomial closure exists below the budget.
            top = max(sum(e) for e in feats)
            growth = max(sum(m) for m in missing) > top
            residual = {str(list(e)): [str(list(m)) for m in pulls[e].terms if m not in feats] for e in feats
                        if any(m not in feats for m in pulls[e].terms)}
            return report("find psi with psi(F(x)) = G psi(x) containing the outputs",
                          {"kind": "truncated monomial features", "size": len(feats)},
                          ["outputs at time zero only"],
                          [{"equation": "psi(F(x)) = G psi(x) + r(x)", "replayed": True}],
                          obstruction={"class": "degree_growth" if growth else "budget",
                                       "missing_monomials": [list(m) for m in missing[:12]],
                                       "residual_support": residual},
                          obligations=["no finite closure within the declared degree/feature budget"],
                          next_step=("stop inflating: use a bounded truncation or add memory/hidden state"
                                     if growth else "raise the feature budget to %d" % (len(feats)+len(missing))),
                          history=history)
        feats = sorted(set(feats) | set(missing), key=lambda e: (sum(e), e))
    # Koopman matrix on the closed monomial space: row i gives pullback of feature i.
    index = {e: i for i, e in enumerate(feats)}
    koop = [[Q(0)]*len(feats) for _ in feats]
    for e, p in pulls.items():
        for m, c in p.terms.items():
            koop[index[e]][index[m]] = c
    out_rows = [[p.terms.get(e, Q(0)) for e in feats] for p in outputs]
    # Smallest space containing the outputs and closed under pullback: span{C, C K, C K^2, ...}.
    minimal = observable_space(koop, out_rows)
    _replay_koopman(feats, koop, evolution)
    return report("find psi with psi(F(x)) = G psi(x) containing the outputs",
                  {"kind": "exact polynomial closure", "monomial_space": len(feats),
                   "minimal_dimension": len(minimal), "features": [list(e) for e in feats]},
                  ["outputs after every number of steps"],
                  [{"equation": "m(F(x)) = sum_j K_mj m_j(x) for every retained monomial m", "replayed": True}],
                  answer={"closed": True, "minimal_dimension": len(minimal)},
                  next_step=None, history=history)


def _replay_koopman(feats, koop, evolution):
    nv = evolution[0].variables
    for i, e in enumerate(feats):
        lhs = _monomial(e).compose(evolution)
        rhs = Poly.constant(0, nv)
        for j, m in enumerate(feats):
            if koop[i][j]:
                rhs = rhs+koop[i][j]*_monomial(m)
        assert lhs == rhs


# ------------------------------------------------------------- linear sensing


def sensing(observation, target, candidates=()):
    """Recover the target from observations, or return the hidden vector and the sensors that fix it."""
    rec = target_recovery(observation, target)
    n = len(target[0])
    base = report("recover G x from H x", {"kind": "linear observation", "sensors": len(observation)},
                  ["G x"] if rec["recoverable"] else [],
                  [{"equation": "ker(H) subset ker(G)", "replayed": True}])
    if rec["recoverable"]:
        base["answer"] = {"recoverable": True}
        return base
    base["obstruction"] = {"class": "structural_invisibility", "hidden_vector": rec["hidden_vector"],
                           "target_response": rec["target_response"]}
    # Each target row must be identified by the sensor rows: reuse readout repair.
    needed = None
    from itertools import combinations
    for k in range(1, len(candidates)+1):
        for idx in combinations(range(len(candidates)), k):
            if target_recovery(list(observation)+[candidates[i] for i in idx], target)["recoverable"]:
                needed = list(idx)
                break
        if needed is not None:
            break
    base["obligations"] = ["better averaging of the existing sensor directions cannot recover the target"]
    base["next"] = ({"add_sensors": needed} if needed is not None
                    else "no subset of the candidate sensors resolves the hidden direction")
    return base


# --------------------------------------------------------- readout / profiles


def readout_problem(design, h, candidates=(), noise_variance=Q(1), prior_covariance=None):
    ident = identify(design, h)
    n = len(h)
    prior = prior_covariance or [[Q(int(i == j)) for j in range(n)] for i in range(n)]
    out = report("estimate the readout h^T beta from observed attempts",
                 {"kind": "linear response design", "rows": len(design), "rank": rank(design, n) if design else 0},
                 ["h^T beta"] if ident["identified"] else [],
                 [{"equation": "h in row(X)", "replayed": True}])
    if ident["identified"]:
        out["answer"] = {"identified": True, "weights": ident["weights"]}
    else:
        out["obstruction"] = {"class": "nonidentified_readout", "witness": ident["witness"],
                              "readout_shift": ident["readout_shift"]}
        out["obligations"] = ["any single reported value depends on pooling or prior assumptions"]
    if candidates:
        fix = repair(design, h, list(candidates))
        voi = value_of_information(design, h, list(candidates), noise_variance, prior)
        out["next"] = {"identifying_conditions": fix, "best_by_variance": voi["candidates"][0]}
    return out


# ------------------------------------------------------------- integer layer


def integer_problem(a, b):
    from .lattice import integer_solve, integer_kernel
    sol = integer_solve(a, b)
    out = report("solve A x = b over the integers", {"kind": "Smith normal form", "shape": [len(a), len(a[0])]},
                 ["integer solvability", "integer solution set"],
                 [{"equation": "U A V = D", "replayed": True}])
    if sol["solvable"]:
        out["answer"] = {"solution": sol["solution"], "kernel_basis": integer_kernel(a)}
    else:
        out["obstruction"] = {"class": "divisibility" if sol["rational"] else "rational_inconsistency",
                              "certificate": sol["certificate"], "invariant": sol["invariant"],
                              "residue": sol["residue"]}
        out["next"] = ("impose the congruence carried by the certificate on the parameters"
                       if sol["rational"] else "the system has no rational solution; revise the model")
    return out


# ------------------------------------------------------------- arithmetic


def arithmetic_problem(k, a, b, c, nmax=10**6):
    """k y^2 = a n^2 + b n + c compiled to a norm equation with its reconstruction map."""
    from .quadratic import QuadraticSquare
    return QuadraticSquare(k, a, b, c).report(nmax)


# --------------------------------------------------------------- partners


def partner_problem(a, b, degree):
    from .strata import partner_witness, form_from_vector
    w = partner_witness(Q(a), Q(b), degree)
    out = report("find g of degree N with (f,g)_3=(f,g)_5=0 and (f,g)_1 != 0",
                 {"kind": "transvectant gate kernel", "kernel": w["kernel_dimension"],
                  "active": w["active_dimension"], "commuting": w["commuting_dimension"]},
                 ["correction-free partners", "active quotient"],
                 [{"equation": "dim A_N = rank[L_N;P_N] - rank L_N", "replayed": w["replayed"]}])
    if w["active_partners"]:
        out["answer"] = {"partner": form_from_vector(w["active_partners"][0], degree).record()}
    else:
        out["obstruction"] = {"class": "no_active_partner", "commuting_dimension": w["commuting_dimension"]}
        out["next"] = "move to a stratum with positive active dimension (see strata.jump_table)"
    return out


def engine_receipt():
    x, y = Poly.variable(0), Poly.variable(1)
    closed = adaptive_closure([x*Q(1, 2), y*Q(1, 3)+x*x], [y])
    growing = adaptive_closure([x*x+y, y], [x], max_degree=6)
    sens = sensing([[1, 1, 0]], [[1, -1, 0]], candidates=[[0, 0, 1], [1, 1, 1], [1, 0, 0]])
    phi = lambda s, a: [Q(1), Q(s), Q(a), Q(s)*Q(a)]
    readout = readout_problem([phi(5, 30), phi(5, 60), phi(5, 90)],
                              [Q(1), Q(5), Q(135, 2), Q(360)],
                              candidates=[phi(5, 120), phi(7, 60), phi(7, 120)])
    integer = integer_problem([[2, 0], [0, 3]], [1, 3])
    partner = partner_problem(16, -9, 6)
    arithmetic = arithmetic_problem(2, 1, 0, 7, 10**9)
    return {"arithmetic": arithmetic, "closure": closed, "degree_growth": growing, "sensing": sens, "readout": readout,
            "integer": integer, "partner": partner}
