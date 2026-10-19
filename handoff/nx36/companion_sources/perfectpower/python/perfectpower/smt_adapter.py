"""A host-solver adapter: replace solved arithmetic conjuncts in an SMT problem by their complete
solution sets.

Given a problem in SMT-LIB 2 (quantifier-free nonlinear integer arithmetic), every top-level
conjunct that is an equality `P = 0` with

    P(n, m) = ± (m^2 - F(n)),   F(n) = (r n + s)^3 + k,   F integral,

is recognized (`compiler.match_affine_cube`).  If `y^2 = x^3 + k` has a complete integral-point
list proved in Lean (`compiler.mordell_complete`: the solved-family registry, the 1163 curves
without points, and the hand-proved curves), the conjunct is replaced by the exact finite
disjunction of its integer solutions (`n` ranges over **all** integers here), or by `false`:

    m^2 = F(n)  <=>  OR_{(t, y) in L, r | t - s} (n = (t - s)/r  and  m = y).

**Justification of one replacement:** the cited Lean theorem gives the complete list `L` of the
curve, and the identity `F(n) = (r n + s)^3 + k` is checked exactly by the adapter (polynomial
coefficients).  The adapter does not emit a Lean proof of the *replacement*; that step is the
elementary substitution `x = r n + s`.  Every other conjunct is left to the host solver unchanged,
and an unrecognized problem is returned unchanged.

Fail-closed by default: only replacements whose complete theorem is re-parsed from the Lean
source are applied (see `smt_cert.py` for the script-level, source-bound, independently checked
version).  `allow_unchecked` / `--allow-unchecked` also applies theorem-cited curves and bounded
Pell/radical enumerations; each replacement records its evidence level.

Requires the `z3-solver` package (imported lazily); nothing else in the repository depends on it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from math import isqrt

from .compiler import QuadraticRootConstraint, compile_constraint, match_affine_cube, mordell_complete


Poly = dict  # {tuple of (var, exp) pairs sorted: coefficient}


def _mono_mul(a, b):
    d = dict(a)
    for v, e in b:
        d[v] = d.get(v, 0) + e
    return tuple(sorted(d.items()))


def _pmul(p, q):
    out = {}
    for ma, ca in p.items():
        for mb, cb in q.items():
            m = _mono_mul(ma, mb)
            out[m] = out.get(m, 0) + ca * cb
    return {m: c for m, c in out.items() if c}


def _padd(p, q, sign=1):
    out = dict(p)
    for m, c in q.items():
        out[m] = out.get(m, 0) + sign * c
    return {m: c for m, c in out.items() if c}


class Unsupported(Exception):
    pass


def to_poly(e) -> Poly:
    """A z3 integer arithmetic term as an exact polynomial, or Unsupported."""
    import z3
    if z3.is_int_value(e):
        v = e.as_long()
        return {(): v} if v else {}
    if z3.is_rational_value(e):          # a Real numeral: accepted only when it is an integer
        if e.denominator_as_long() != 1:
            raise Unsupported('non-integer numeral')
        v = e.numerator_as_long()
        return {(): v} if v else {}
    if z3.is_const(e) and e.sort() == z3.IntSort():
        return {((str(e), 1),): 1}
    k = e.decl().kind()
    if k == z3.Z3_OP_TO_REAL:            # z3py's `**` on Int terms coerces to Real
        return to_poly(e.arg(0))
    args = [to_poly(a) for a in e.children()] if k != z3.Z3_OP_POWER else None
    if k == z3.Z3_OP_ADD:
        out = {}
        for a in args:
            out = _padd(out, a)
        return out
    if k == z3.Z3_OP_SUB:
        out = args[0]
        for a in args[1:]:
            out = _padd(out, a, -1)
        return out
    if k == z3.Z3_OP_UMINUS:
        return {m: -c for m, c in args[0].items()}
    if k == z3.Z3_OP_MUL:
        out = {(): 1}
        for a in args:
            out = _pmul(out, a)
        return out
    if k == z3.Z3_OP_POWER:
        base, ex = e.children()
        ex = to_poly(ex)
        if set(ex) - {()} or ex.get((), 0) < 0:
            raise Unsupported('power')
        out, b = {(): 1}, to_poly(base)
        for _ in range(ex.get((), 0)):
            out = _pmul(out, b)
        return out
    raise Unsupported(str(e.decl()))


def recognize(P: Poly):
    """(n, m, F as coefficient list low->high) with P = ±(m^2 - F(n)), else None."""
    vars_ = sorted({v for mono in P for v, _ in mono})
    if len(vars_) != 2:
        return None
    for m in vars_:
        n = vars_[0] if vars_[1] == m else vars_[1]
        for sign in (1, -1):
            Q = {mono: sign * c for mono, c in P.items()}
            if Q.get(((m, 2),)) != 1:
                continue
            rest = {mono: c for mono, c in Q.items() if mono != ((m, 2),)}
            if any(v != n for mono in rest for v, _ in mono):
                continue
            deg = max((e for mono in rest for _, e in mono), default=0)
            F = [0] * (deg + 1)
            for mono, c in rest.items():
                F[mono[0][1] if mono else 0] = -c
            return n, m, F
    return None


def recognize_quadratic(P: Poly) -> list:
    """Every reading (N, S, a, b, c, F low->high) of P = ±(a S^2 + b S + c - F(N)), deg F = 2,
    a != 0.  Both variables may qualify; the caller picks the one whose N is bounded."""
    vars_ = sorted({v for mono in P for v, _ in mono})
    out = []
    if len(vars_) != 2:
        return out
    for S in vars_:
        N = vars_[0] if vars_[1] == S else vars_[1]
        if any(len(mono) > 1 for mono in P):                 # no mixed terms
            continue
        a = P.get(((S, 2),), 0)
        if a == 0 or any(v == S and e > 2 for mono in P for v, e in mono):
            continue
        if any(v == N and e > 2 for mono in P for v, e in mono):
            continue
        sg = 1 if a > 0 else -1
        Q = {mono: sg * c for mono, c in P.items()}
        F = [-Q.get((), 0), -Q.get(((N, 1),), 0), -Q.get(((N, 2),), 0)]
        if F[2] == 0:
            continue
        out.append((N, S, Q[((S, 2),)], Q.get(((S, 1),), 0), 0, F))
    return out


def _bounds(flat, var):
    """Numeric bounds lo <= var <= hi read from top-level conjuncts (None when absent)."""
    import z3
    lo = hi = None
    for a in flat:
        if not (z3.is_le(a) or z3.is_ge(a) or z3.is_lt(a) or z3.is_gt(a)):
            continue
        l, r = a.arg(0), a.arg(1)
        if z3.is_const(l) and str(l) == var and z3.is_int_value(r):
            v, side = r.as_long(), 'hi' if (z3.is_le(a) or z3.is_lt(a)) else 'lo'
        elif z3.is_const(r) and str(r) == var and z3.is_int_value(l):
            v, side = l.as_long(), 'lo' if (z3.is_le(a) or z3.is_lt(a)) else 'hi'
        else:
            continue
        strict = z3.is_lt(a) or z3.is_gt(a)
        if side == 'hi':
            v -= strict
            hi = v if hi is None else min(hi, v)
        else:
            v += strict
            lo = v if lo is None else max(lo, v)
    return lo, hi


def _roots_at(a, b, c, f):
    """Integer y with a y^2 + b y + c = f."""
    disc = b * b - 4 * a * (c - f)
    if disc < 0 or isqrt(disc) ** 2 != disc:
        return []
    r = isqrt(disc)
    return sorted({(-b + sg * r) // (2 * a) for sg in (1, -1) if (-b + sg * r) % (2 * a) == 0})


def bounded_quadratic_hits(a, b, c, F, lo, hi):
    """All (n, y) with lo <= n <= hi and a y^2 + b y + c = F(n), by the compiler's Pell/radical
    orbits (n >= 1 directly, n <= -1 by reflection n -> -n, n = 0 by the quadratic formula).
    None when the compiler has no exact enumeration."""
    out = []
    for sgn, top in ((1, hi), (-1, -lo)):
        if top < 1:
            continue
        G = (F[0], sgn * F[1], F[2])
        plan = compile_constraint(QuadraticRootConstraint(a, b, c, G, 'int'))
        if not getattr(plan, 'exact_to_any_N', False):
            return None
        for n, ys in plan.iter_hits(top):
            if (lo <= sgn * n <= hi) if sgn > 0 else (lo <= -n <= hi):
                out += [(sgn * n, y) for y in ys]
    if lo <= 0 <= hi:
        out += [(0, y) for y in _roots_at(a, b, c, F[0])]
    return sorted(set(out)), plan.justification


@dataclass
class Replacement:
    conjunct: str
    n: str
    m: str
    substitution: str
    curve: str
    solutions: list
    lean: list
    evidence: str = ''      # lean_statement_parsed | theorem_cited | python_enumeration_unchecked


@dataclass
class Result:
    assertions: list
    replacements: list = field(default_factory=list)


def reduce_assertions(assertions, allow_unchecked: bool = False) -> Result:
    """Split top-level conjunctions and replace recognized solved conjuncts.

    Fail-closed by default: a conjunct is replaced only when its complete theorem's statement is
    re-parsed from the Lean source (`smt_cert._lean_list`).  Theorem-cited curves and bounded
    Pell/radical enumerations (Python) are applied only with `allow_unchecked=True`, and every
    replacement records its evidence level."""
    from .smt_cert import _lean_list
    import z3
    flat, todo = [], list(assertions)
    while todo:
        a = todo.pop(0)
        if z3.is_and(a):
            todo = list(a.children()) + todo
        else:
            flat.append(a)
    out = Result(assertions=[])
    for a in flat:
        rep = None
        if z3.is_eq(a) and a.arg(0).sort() in (z3.IntSort(), z3.RealSort()):  # variables must be Int
            try:
                P = _padd(to_poly(a.arg(0)), to_poly(a.arg(1)), -1)
                rec = recognize(P)
            except Unsupported:
                rec = None
            if rec is not None:
                n, m, F = rec
                F = tuple(F) + (0,) * max(0, 4 - len(F))
                mac = match_affine_cube(F) if len(F) == 4 else None
                if mac is not None:
                    r, s, k = mac
                    solved = mordell_complete(k) if k != 0 else None
                    parsed = _lean_list(k) if solved is not None else None
                    if solved is not None and (parsed is not None or allow_unchecked):
                        T, lean = solved
                        sols = sorted((Fraction(t - s, r), sg * y) for t, ys in T.items() for y in ys
                                      for sg in ((1, -1) if y else (1,)) if (t - s) % r == 0)
                        sols = [(int(x), y) for x, y in sols]
                        N, Mv = z3.Int(n), z3.Int(m)
                        new = z3.Or([z3.And(N == x, Mv == y) for x, y in sols]) if sols else z3.BoolVal(False)
                        rep = Replacement(conjunct=str(a), n=n, m=m, substitution=f'x = {r}*{n} + ({s})',
                                          curve=f'y^2 = x^3 + ({k})', solutions=sols, lean=lean,
                                          evidence='lean_statement_parsed' if parsed else 'theorem_cited')
                        out.assertions.append(new)
                        out.replacements.append(rep)
        if rep is None and z3.is_eq(a) and a.arg(0).sort() in (z3.IntSort(), z3.RealSort()):
            try:
                readings = recognize_quadratic(_padd(to_poly(a.arg(0)), to_poly(a.arg(1)), -1))
            except Unsupported:
                readings = []
            for N, S, qa, qb, qc, F in readings:
                lo, hi = _bounds(flat, N)
                got = bounded_quadratic_hits(qa, qb, qc, F, lo, hi) if lo is not None and hi is not None else None
                evidence, just_lean = 'python_enumeration_unchecked', None
                if got is not None:
                    # default path: the bounded list as a kernel-checked Lean theorem
                    from .bounded_pell import Unsupported as BPUnsupported, kernel_check, plan
                    try:
                        P = plan(qa, qb, qc, F[2], F[1], F[0], lo, hi)
                        if sorted(P['L0']) == sorted(got[0]):
                            ok, detail = kernel_check(P)
                            if ok:
                                evidence, just_lean = 'lean_kernel_checked', [
                                    'PerfectPower.BoundedPell.quad_bounded', f'instance {detail}']
                    except BPUnsupported:
                        pass
                if got is not None and (evidence == 'lean_kernel_checked' or allow_unchecked):
                    sols, just = got
                    if just_lean:
                        just = just_lean
                    Nv, Sv = z3.Int(N), z3.Int(S)
                    new = z3.Or([z3.And(Nv == x, Sv == y) for x, y in sols]) if sols else z3.BoolVal(False)
                    rep = Replacement(conjunct=str(a), n=N, m=S, substitution=f'{lo} <= {N} <= {hi}',
                                      curve=f'{qa}*{S}^2 + {qb}*{S} + {qc} = {F[2]}*{N}^2 + {F[1]}*{N} + {F[0]}',
                                      solutions=sols, lean=list(just), evidence=evidence)
                    out.assertions.append(new)
                    out.replacements.append(rep)
                    break
        if rep is None:
            out.assertions.append(a)
    return out


def reduce_smt2(text: str, allow_unchecked: bool = False) -> Result:
    import z3
    return reduce_assertions(list(z3.parse_smt2_string(text)), allow_unchecked)


def main(argv=None):
    """python3 -m perfectpower.smt_adapter TASK.smt2 [--out REDUCED.smt2] [--report REPORT.json]

    Reads an SMT-LIB 2 task (for example one saved by a verification tool), writes the reduced
    task, and reports every replacement with its justification.  Each replacement is an
    *equivalence* of the replaced conjunct over the integers, so the task's satisfiability (and a
    verification condition's validity) is preserved exactly; nothing is weakened or dropped."""
    import argparse
    import json
    import z3
    ap = argparse.ArgumentParser()
    ap.add_argument('task')
    ap.add_argument('--out')
    ap.add_argument('--report')
    ap.add_argument('--allow-unchecked', action='store_true',
                    help='also apply theorem-cited curves and bounded Pell/radical enumerations (Python)')
    a = ap.parse_args(argv)
    res = reduce_smt2(open(a.task).read(), a.allow_unchecked)
    s = z3.Solver()
    s.add(res.assertions)
    if a.out:
        open(a.out, 'w').write(s.to_smt2())
    report = {'task': a.task, 'replacements': [{
        'conjunct': r.conjunct, 'recognized_as': r.curve, 'domain_or_substitution': r.substitution,
        'solutions': r.solutions, 'justification': r.lean, 'evidence': r.evidence,
        'equivalence': 'over Z, of the replaced conjunct (bounds kept as separate conjuncts)'}
        for r in res.replacements]}
    text = json.dumps(report, indent=1)
    if a.report:
        open(a.report, 'w').write(text + '\n')
    else:
        print(text)


if __name__ == '__main__':
    main()
