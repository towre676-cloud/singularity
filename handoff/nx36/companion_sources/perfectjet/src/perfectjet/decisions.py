"""Certified decisions and the evolution-defect split for reduced linear models.

A decision is settled within the declared model once the leader's lower bound
exceeds every competitor's upper bound,

    J(a*) - eps(a*) > max_{b != a*} J(b) + eps(b),

after which further accuracy cannot change the choice. `refine_until_settled`
spends refinement only on actions whose intervals still overlap the leader's.

For x' = A x + B u observed through a reduced state z' = G z + H u with lift V,
the error e = x - V z obeys exactly

    e_{t+1} = A e_t + (A V - V G) z_t + (B - V H) u_t,

so initial error, evolution defect and input defect are separated before any
norm bound is applied.
"""
from fractions import Fraction as Q
from .exact import matrix, matmul


def interval(est, err):
    return (Q(est)-Q(err), Q(est)+Q(err))


def certified_choice(bounds, maximize=True):
    """bounds: {action: (estimate, error)}. Returns the settled action or the contenders."""
    if not bounds:
        raise ValueError("no actions")
    sign = 1 if maximize else -1
    lo = {a: sign*Q(e)-Q(r) for a, (e, r) in bounds.items()}
    hi = {a: sign*Q(e)+Q(r) for a, (e, r) in bounds.items()}
    leader = max(bounds, key=lambda a: (lo[a], hi[a]))
    rivals = [b for b in bounds if b != leader]
    best_rival = max((hi[b] for b in rivals), default=None)
    settled = best_rival is None or lo[leader] > best_rival
    contenders = [leader]+[b for b in rivals if hi[b] >= lo[leader]]
    return {"settled": settled, "choice": leader if settled else None, "leader": leader,
            "contenders": contenders, "margin": (lo[leader]-best_rival) if best_rival is not None else None}


def refine_until_settled(actions, evaluate, max_level=40, maximize=True):
    """evaluate(action, level) -> (estimate, error) with error shrinking in level.

    Refines the widest contender each round. Returns the decision, the levels spent
    per action, and the cost of refining every action to the same final level.
    """
    level = {a: 0 for a in actions}
    bounds = {a: evaluate(a, 0) for a in actions}
    calls = len(actions)
    while True:
        dec = certified_choice(bounds, maximize)
        if dec["settled"]:
            break
        open_ = [a for a in dec["contenders"] if level[a] < max_level]
        if not open_:
            break
        a = max(open_, key=lambda b: (Q(bounds[b][1]), str(b)))
        level[a] += 1
        bounds[a] = evaluate(a, level[a])
        calls += 1
    uniform = len(actions)*(max(level.values())+1)
    return {**dec, "levels": level, "evaluations": calls, "uniform_evaluations": uniform}


def _mv(a, v):
    return [sum((x*y for x, y in zip(row, v)), Q(0)) for row in a]


def _sub(u, v):
    return [x-y for x, y in zip(u, v)]


def _add(*vs):
    return [sum(x, Q(0)) for x in zip(*vs)]


def norm_inf(v):
    return max((abs(x) for x in v), default=Q(0))


def op_norm_inf(a):
    return max((sum((abs(x) for x in row), Q(0)) for row in a), default=Q(0))


def defect_split(a, b, v, g, h, x0, z0, inputs):
    """Replay e_{t+1} = A e_t + (AV-VG) z_t + (B-VH) u_t and a finite-horizon bound."""
    a, b, v, g, h = map(matrix, (a, b, v, g, h))
    evo = [[p-q for p, q in zip(r1, r2)] for r1, r2 in zip(matmul(a, v), matmul(v, g))]
    inp = [[p-q for p, q in zip(r1, r2)] for r1, r2 in zip(b, matmul(v, h))]
    x, z = [Q(t) for t in x0], [Q(t) for t in z0]
    e = _sub(x, _mv(v, z))
    na = op_norm_inf(a)
    bound = norm_inf(e)
    rows = []
    for u in inputs:
        u = [Q(t) for t in u]
        evo_term, inp_term = _mv(evo, z), _mv(inp, u)
        predicted = _add(_mv(a, e), evo_term, inp_term)
        x, z = _add(_mv(a, x), _mv(b, u)), _add(_mv(g, z), _mv(h, u))
        e = _sub(x, _mv(v, z))
        assert e == predicted, "defect identity failed"
        bound = na*bound+norm_inf(evo_term)+norm_inf(inp_term)
        rows.append({"error": norm_inf(e), "bound": bound, "evolution_defect": norm_inf(evo_term),
                     "input_defect": norm_inf(inp_term)})
    exact = not any(any(r) for r in evo) and not any(any(r) for r in inp)
    return {"identity_replayed": True, "exact_reduction": exact, "operator_norm_A": na, "steps": rows}


def decisions_receipt():
    from math import factorial
    # Three actions whose values are exp(c) for different c, bracketed by Taylor partial sums.
    targets = {"hold": Q(1, 2), "advance": Q(3, 4), "retreat": Q(-1)}

    def evaluate(action, level):
        c = targets[action]
        terms = level+2
        s = sum((c**k/factorial(k) for k in range(terms)), Q(0))
        err = 2*abs(c)**terms/factorial(terms)  # remainder bound valid for |c| <= 1
        return s, err
    run = refine_until_settled(list(targets), evaluate)
    split = defect_split([[Q(1, 2), Q(1, 4)], [0, Q(1, 3)]], [[1], [1]], [[1], [1]], [[Q(1, 2)]], [[1]],
                         [1, 1], [1], [[1], [0], [Q(1, 2)]])
    return {"refinement": {k: (str(v) if isinstance(v, Q) else v) for k, v in run.items()},
            "defect_split": split}
