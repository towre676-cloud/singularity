"""Parameter-aware observability over Q[q] (unit OE09).

An operator system whose generators and observation rows have entries in
Q[q] is specialized at a rational or algebraic q0 by evaluating every entry.
This module answers, exactly and without floating point:

* the generic rank r of the observation space over the field Q(q);
* the r-th determinantal divisor D_r(q) of the matrix W of all experiment
  rows of word length <= n-1, computed from a Hermite basis of the Q[q]-row
  module of W (built by the recursion N_k = N_0 + sum_i N_{k-1} M_i, so the
  exponentially many rows of W are never listed) and a Smith normal form;
* the exceptional parameters: q0 is exceptional, i.e. the observation rank
  at q0 is below r, if and only if D_r(q0) = 0;
* exact real-root isolation of D_r on a declared domain, factorization of
  D_r into irreducible factors over Q with an irreducibility certificate,
  and exact replays of the rank drop.

Word order and costs follow ``observability``: a word (i1,...,im) applies
i1 first, and right multiplication of an experiment row prepends a letter.
Proofs are in docs/research/PARAMETRIC_OBSERVABILITY.md.

Polynomials are exchanged as ``{exponent: Fraction}`` dictionaries, as in
``polynomials``.  Internally they are dense tuples of Fractions, lowest
degree first, with no trailing zero; the zero polynomial is ``()``.

Exception contract: bool, float and str (and other non-exact types) raise
TypeError; valid types with invalid values or shapes raise ValueError.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import heapq
from itertools import combinations, count, product
from math import gcd as _igcd, lcm as _ilcm
from typing import Mapping, Sequence

from .observability import OperatorSystem, observable_closure
from .parameters import count_roots, isolate_roots

P = tuple  # dense polynomial: tuple of Fraction, low degree first
_ZERO: tuple = ()
_ONE = (Fraction(1),)


# ------------------------------------------------------------ type checks
def _exact(value, name="value") -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(f"{name} must be an int or Fraction, not {type(value).__name__}")
    return Fraction(value)


def _int(value, name="value", minimum=None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, not {type(value).__name__}")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


# ------------------------------------------------- dense polynomial algebra
def _trim(c) -> P:
    c = list(c)
    while c and not c[-1]:
        c.pop()
    return tuple(c)


def _deg(f: P) -> int:
    return len(f) - 1


def _add(f: P, g: P) -> P:
    if len(f) < len(g):
        f, g = g, f
    return _trim(tuple(a + b for a, b in zip(f, g)) + f[len(g):])


def _sub(f: P, g: P) -> P:
    return _add(f, tuple(-b for b in g))


def _scale(f: P, s: Fraction) -> P:
    return () if not s else tuple(a * s for a in f)


def _mul(f: P, g: P) -> P:
    if not f or not g:
        return ()
    out = [Fraction(0)] * (len(f) + len(g) - 1)
    for i, a in enumerate(f):
        if a:
            for j, b in enumerate(g):
                if b:
                    out[i + j] += a * b
    return _trim(out)


def _divmod(f: P, g: P):
    if not g:
        raise ZeroDivisionError("polynomial division by zero")
    rem = list(f)
    dg, lead = _deg(g), g[-1]
    if len(rem) <= dg:
        return (), _trim(rem)
    quo = [Fraction(0)] * (len(rem) - dg)
    for k in range(len(rem) - 1, dg - 1, -1):
        c = rem[k]
        if c:
            c = c / lead
            quo[k - dg] = c
            for j, b in enumerate(g):
                if b:
                    rem[k - dg + j] -= c * b
    return _trim(quo), _trim(rem[:dg])


def _monic(f: P) -> P:
    return f if not f or f[-1] == 1 else _scale(f, 1 / f[-1])


def _gcd(f: P, g: P) -> P:
    while g:
        f, g = g, _divmod(f, g)[1]
    return _monic(f)


def _xgcd(f: P, g: P):
    """(d, s, t) with s f + t g = d = monic gcd."""
    r0, r1, s0, s1, t0, t1 = f, g, _ONE, (), (), _ONE
    while r1:
        quo, rem = _divmod(r0, r1)
        r0, r1 = r1, rem
        s0, s1 = s1, _sub(s0, _mul(quo, s1))
        t0, t1 = t1, _sub(t0, _mul(quo, t1))
    if not r0:
        return (), (), ()
    inv = 1 / r0[-1]
    return _scale(r0, inv), _scale(s0, inv), _scale(t0, inv)


def _eval(f: P, x: Fraction) -> Fraction:
    acc = Fraction(0)
    for a in reversed(f):
        acc = acc * x + a
    return acc


def _deriv(f: P) -> P:
    return _trim(tuple(k * a for k, a in enumerate(f))[1:])


def _pow(f: P, e: int) -> P:
    out = _ONE
    for _ in range(e):
        out = _mul(out, f)
    return out


def _to_dict(f: P) -> dict:
    return {k: a for k, a in enumerate(f) if a}


def _from_dict(d: Mapping) -> P:
    if not d:
        return ()
    out = [Fraction(0)] * (max(d) + 1)
    for k, a in d.items():
        out[k] += a
    return _trim(out)


def _poly(value, name="entry") -> P:
    """Public polynomial input: a Mapping {int exponent >= 0: int|Fraction},
    or an int/Fraction constant."""
    if isinstance(value, Mapping):
        out = {}
        for e, c in value.items():
            e = _int(e, f"{name} exponent", minimum=0)
            out[e] = out.get(e, Fraction(0)) + _exact(c, f"{name} coefficient")
        return _from_dict(out)
    return _trim((_exact(value, name),))


def to_polynomial(value) -> dict:
    """Normalize a public polynomial input to ``{exponent: Fraction}``."""
    return _to_dict(_poly(value))


def _poly_str(f: P, var="q") -> str:
    if not f:
        return "0"
    terms = []
    for k in range(len(f) - 1, -1, -1):
        a = f[k]
        if not a:
            continue
        mon = "" if k == 0 else (var if k == 1 else f"{var}^{k}")
        mag = abs(a)
        if mon and mag == 1:
            body = mon
        elif mon:
            body = f"{mag}*{mon}"
        else:
            body = str(mag)
        terms.append(("-" if a < 0 else "+", body))
    s = ("-" if terms[0][0] == "-" else "") + terms[0][1]
    for sign, body in terms[1:]:
        s += f" {sign} {body}"
    return s


def polynomial_json(f) -> list:
    """[[exponent, "numerator/denominator"], ...] for a dense or dict polynomial."""
    f = f if isinstance(f, tuple) else _poly(f)
    return [[k, f"{a.numerator}/{a.denominator}"] for k, a in enumerate(f) if a]


# --------------------------------------------------------- the system
def _poly_matrix(values, rows, columns, name) -> tuple:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{name} must be a sequence of rows")
    out = []
    for row in values:
        if isinstance(row, (str, bytes)) or not isinstance(row, Sequence):
            raise TypeError(f"{name} rows must be sequences")
        r = tuple(_poly(x, f"{name} entry") for x in row)
        if len(r) != columns:
            raise ValueError(f"{name} row dimension mismatch")
        out.append(r)
    if rows is not None and len(out) != rows:
        raise ValueError(f"{name} dimension mismatch")
    return tuple(out)


@dataclass(frozen=True)
class PolynomialOperatorSystem:
    """Generators M_i and observation rows L_j with entries in Q[q].

    Costs are exact rationals, as in ``observability.OperatorSystem``:
    attachment costs positive, observation costs nonnegative.
    """

    dimension: int
    operators: tuple
    observations: tuple
    attachment_costs: tuple
    observation_costs: tuple

    def __init__(self, dimension, operators, observations,
                 attachment_costs=None, observation_costs=None):
        n = _int(dimension, "dimension", minimum=0)
        if isinstance(operators, (str, bytes)) or not isinstance(operators, Sequence):
            raise TypeError("operators must be a sequence of matrices")
        ops = tuple(_poly_matrix(m, n, n, "operator") for m in operators)
        obs = _poly_matrix(observations, None, n, "observation")
        ac = tuple(_exact(c, "attachment cost") for c in
                   (attachment_costs if attachment_costs is not None else [1] * len(ops)))
        oc = tuple(_exact(c, "observation cost") for c in
                   (observation_costs if observation_costs is not None else [0] * len(obs)))
        if len(ac) != len(ops) or any(c <= 0 for c in ac):
            raise ValueError("attachment costs must be positive, one per operator")
        if len(oc) != len(obs) or any(c < 0 for c in oc):
            raise ValueError("observation costs must be nonnegative, one per row")
        object.__setattr__(self, "dimension", n)
        object.__setattr__(self, "operators", ops)
        object.__setattr__(self, "observations", obs)
        object.__setattr__(self, "attachment_costs", ac)
        object.__setattr__(self, "observation_costs", oc)

    def specialize(self, q0) -> OperatorSystem:
        """The rational operator system at q = q0 (every q0 is admissible:
        entries are polynomials, so there are no poles)."""
        x = _exact(q0, "q0")
        ev = lambda m: tuple(tuple(_eval(f, x) for f in row) for row in m)  # noqa: E731
        return OperatorSystem(self.dimension, tuple(ev(m) for m in self.operators),
                              ev(self.observations), self.attachment_costs, self.observation_costs)

    def operator_entries(self, index):
        """Generator ``index`` as a matrix of ``{exponent: Fraction}`` entries."""
        index = _int(index, "operator index", minimum=0)
        if index >= len(self.operators):
            raise ValueError("operator index out of range")
        return tuple(tuple(_to_dict(f) for f in row) for row in self.operators[index])


def _row_times(row, matrix, n):
    out = []
    for j in range(n):
        acc = ()
        for k, a in enumerate(row):
            if a and matrix[k][j]:
                acc = _add(acc, _mul(a, matrix[k][j]))
        out.append(acc)
    return tuple(out)


def experiment_row(system: PolynomialOperatorSystem, observation, word=()) -> tuple:
    """L_j M_w as a tuple of dense polynomials (letters applied in order)."""
    observation = _int(observation, "observation index", minimum=0)
    if observation >= len(system.observations):
        raise ValueError("observation index out of range")
    word = tuple(_int(i, "operator index", minimum=0) for i in word)
    if any(i >= len(system.operators) for i in word):
        raise ValueError("operator index out of range")
    row = system.observations[observation]
    for i in reversed(word):
        row = _row_times(row, system.operators[i], system.dimension)
    return row


# --------------------------------------- linear algebra over Q(q) and Q[q]
def _content_free(v):
    """Divide a nonzero polynomial vector by the monic gcd of its entries."""
    g = ()
    for a in v:
        if a:
            g = _gcd(g, a) if g else _monic(a)
            if len(g) == 1:
                break
    lead = next(a for a in v if a)[-1]
    if len(g) > 1:
        v = tuple(_divmod(a, g)[0] if a else () for a in v)
    lead = next(a for a in v if a)[-1]
    return tuple(_scale(a, 1 / lead) for a in v) if lead != 1 else v


class _FractionFreeEchelon:
    """Incremental echelon basis over Q(q) with polynomial rows."""

    def __init__(self):
        self.rows = []  # (pivot column, polynomial row)

    def reduce(self, v):
        for p, e in self.rows:
            if v[p]:
                a, b = e[p], v[p]
                g = _gcd(a, b)
                a, b = _divmod(a, g)[0], _divmod(b, g)[0]
                v = tuple(_sub(_mul(a, x), _mul(b, y)) for x, y in zip(v, e))
                if any(v):
                    v = _content_free(v)
                else:
                    return v
        return v

    def insert(self, v) -> bool:
        v = self.reduce(tuple(v))
        if not any(v):
            return False
        self.rows.append((next(j for j, a in enumerate(v) if a), _content_free(v)))
        return True


def generic_rank(matrix) -> int:
    """Rank over Q(q) of a matrix of public polynomial entries."""
    rows = _public_matrix(matrix)
    ech = _FractionFreeEchelon()
    return sum(ech.insert(r) for r in rows)


def _public_matrix(matrix):
    if isinstance(matrix, (str, bytes)) or not isinstance(matrix, Sequence):
        raise TypeError("matrix must be a sequence of rows")
    rows = list(matrix)
    if not rows:
        return ()
    if isinstance(rows[0], (str, bytes)) or not isinstance(rows[0], Sequence):
        raise TypeError("matrix rows must be sequences")
    return _poly_matrix(rows, None, len(rows[0]), "matrix")


@dataclass(frozen=True)
class GenericExperiment:
    observation: int
    word: tuple
    cost: Fraction
    row: tuple  # dense polynomials

    @property
    def row_polynomials(self):
        return tuple(_to_dict(a) for a in self.row)


@dataclass(frozen=True)
class GenericClosure:
    """Cost-ordered closure over Q(q): basis words and the generic rank."""

    basis: tuple

    @property
    def rank(self):
        return len(self.basis)

    @property
    def matrix(self):
        return tuple(e.row for e in self.basis)


def generic_closure(system: PolynomialOperatorSystem) -> GenericClosure:
    """observable_closure run over the field Q(q).

    Candidates are processed in nondecreasing cost; a candidate is kept iff
    it is independent over Q(q) of the kept rows, and only kept rows are
    extended.  The pruning argument of SNG-O03 is field independent, so the
    kept rows span the observation space over Q(q).
    """
    if not isinstance(system, PolynomialOperatorSystem):
        raise TypeError("system must be a PolynomialOperatorSystem")
    heap, serial = [], count()
    for j, row in enumerate(system.observations):
        heapq.heappush(heap, (system.observation_costs[j], next(serial),
                              GenericExperiment(j, (), system.observation_costs[j], row)))
    ech, basis = _FractionFreeEchelon(), []
    while heap and len(basis) < system.dimension:
        _, _, e = heapq.heappop(heap)
        if not ech.insert(e.row):
            continue
        basis.append(e)
        for i, op in enumerate(system.operators):
            child = GenericExperiment(e.observation, (i,) + e.word, e.cost + system.attachment_costs[i],
                                      _row_times(e.row, op, system.dimension))
            heapq.heappush(heap, (child.cost, next(serial), child))
    return GenericClosure(tuple(basis))


def _hnf(rows, n):
    """Row Hermite normal form over Q[q]: echelon rows with monic pivots and
    entries above each pivot of smaller degree.  Canonical for the module."""
    rows = [list(r) for r in rows if any(r)]
    pr = 0
    pivots = []
    for c in range(n):
        while True:
            nz = [i for i in range(pr, len(rows)) if rows[i][c]]
            if not nz:
                break
            i0 = min(nz, key=lambda i: (len(rows[i][c]), i))
            rows[pr], rows[i0] = rows[i0], rows[pr]
            piv = rows[pr][c]
            clean = True
            for i in range(pr + 1, len(rows)):
                if rows[i][c]:
                    quo, rem = _divmod(rows[i][c], piv)
                    rows[i] = [_sub(x, _mul(quo, y)) for x, y in zip(rows[i], rows[pr])]
                    clean = clean and not rem
            rows = rows[:pr + 1] + [r for r in rows[pr + 1:] if any(r)]
            if clean:
                break
        if pr < len(rows) and rows[pr][c]:
            lead = rows[pr][c][-1]
            if lead != 1:
                rows[pr] = [_scale(x, 1 / lead) for x in rows[pr]]
            piv = rows[pr][c]
            for i in range(pr):
                if rows[i][c] and len(rows[i][c]) >= len(piv):
                    quo = _divmod(rows[i][c], piv)[0]
                    rows[i] = [_sub(x, _mul(quo, y)) for x, y in zip(rows[i], rows[pr])]
            pivots.append(c)
            pr += 1
    return tuple(tuple(r) for r in rows[:pr]), tuple(pivots)


@dataclass(frozen=True)
class ObservationModule:
    """Hermite bases of N_k, the Q[q]-span of experiment rows of length <= k.

    ``chain[k]`` is the HNF of N_k for k = 0..len(chain)-1; the chain is
    computed through k = max(n-1, first k with N_{k+1} = N_k).
    """

    dimension: int
    chain: tuple
    stable_from: int  # least k with N_{k+1} = N_k

    @property
    def length_bound(self):
        return max(self.dimension - 1, 0)

    @property
    def at_length_bound(self):
        """HNF of the row module of W = all rows of length <= n-1."""
        return self.chain[self.length_bound]

    @property
    def full(self):
        """HNF of the row module of all experiment rows."""
        return self.chain[self.stable_from]


def observation_module(system: PolynomialOperatorSystem, max_steps: int = 10_000) -> ObservationModule:
    """Exact Q[q]-row module of the experiment rows, never listing W.

    N_0 is spanned by the observations and N_k = N_0 + sum_i N_{k-1} M_i,
    because the rows of length <= k are the observations together with
    (row of length <= k-1) * M_i.  Once N_{k+1} = N_k the chain is constant.
    """
    if not isinstance(system, PolynomialOperatorSystem):
        raise TypeError("system must be a PolynomialOperatorSystem")
    max_steps = _int(max_steps, "max_steps", minimum=0)
    n = system.dimension
    obs = list(system.observations)
    chain = [_hnf(obs, n)[0]]
    stable = None
    target = max(n - 1, 0)
    while stable is None or len(chain) - 1 < target:
        if stable is not None:
            chain.append(chain[-1])  # constant after stabilization
            continue
        if len(chain) > max_steps:
            raise ArithmeticError("observation module did not stabilize within max_steps")
        prev = chain[-1]
        h = _hnf(obs + [_row_times(r, op, n) for op in system.operators for r in prev], n)[0]
        if h == prev:
            stable = len(chain) - 1
        else:
            chain.append(h)
    return ObservationModule(n, tuple(chain), stable)


def smith_invariant_factors(matrix) -> tuple:
    """Monic invariant factors d_1 | d_2 | ... (nonzero ones) of a matrix over
    Q[q], by elementary row and column operations with polynomial Euclid."""
    a = [list(r) for r in matrix]
    if not a:
        return ()
    m, n = len(a), len(a[0])
    factors = []
    t = 0
    while t < min(m, n):
        entries = [(len(a[i][j]), i, j) for i in range(t, m) for j in range(t, n) if a[i][j]]
        if not entries:
            break
        _, i0, j0 = min(entries)
        a[t], a[i0] = a[i0], a[t]
        for row in a:
            row[t], row[j0] = row[j0], row[t]
        while True:
            piv = a[t][t]
            changed = False
            for i in range(t + 1, m):
                if a[i][t]:
                    quo, rem = _divmod(a[i][t], piv)
                    a[i] = [_sub(x, _mul(quo, y)) for x, y in zip(a[i], a[t])]
                    if rem:
                        changed = True
            for j in range(t + 1, n):
                if a[t][j]:
                    quo, rem = _divmod(a[t][j], piv)
                    for i in range(m):
                        if a[i][t]:
                            a[i][j] = _sub(a[i][j], _mul(quo, a[i][t]))
                    if rem:
                        changed = True
            if changed:
                entries = [(len(a[i][t]), i, t) for i in range(t, m) if a[i][t]] + \
                          [(len(a[t][j]), t, j) for j in range(t, n) if a[t][j]]
                _, i0, j0 = min(entries)
                a[t], a[i0] = a[i0], a[t]
                for row in a:
                    row[t], row[j0] = row[j0], row[t]
                continue
            bad = next(((i, j) for i in range(t + 1, m) for j in range(t + 1, n)
                        if a[i][j] and _divmod(a[i][j], piv)[1]), None)
            if bad is None:
                break
            a[t] = [_add(x, y) for x, y in zip(a[t], a[bad[0]])]
        factors.append(_monic(a[t][t]))
        t += 1
    return tuple(factors)


def _determinantal_divisor_dense(rows, r) -> P:
    """D_r, the monic gcd of the r x r minors.

    Shortcut when the matrix has exactly r rows and rank r (a Hermite basis
    of a module, or a generic basis): unimodular row operations on the
    transpose preserve every determinantal divisor, and the Hermite form of
    the n x r transpose is [T; 0] with T upper triangular r x r, whose only
    nonzero r x r minor is det T, the product of the pivots.  Otherwise the
    Smith form is used."""
    if r == 0:
        return _ONE
    rows = [tuple(r_) for r_ in rows]
    if not rows or r > min(len(rows), len(rows[0])):
        return ()
    if len(rows) == r:
        transpose = [tuple(row[j] for row in rows) for j in range(len(rows[0]))]
        h, pivots = _hnf(transpose, r)
        if len(h) < r:
            return ()
        out = _ONE
        for i, c in enumerate(pivots):
            out = _mul(out, h[i][c])
        return _monic(out)
    inv = smith_invariant_factors(rows)
    if len(inv) < r:
        return ()
    out = _ONE
    for f in inv[:r]:
        out = _mul(out, f)
    return out


def determinantal_divisor(matrix, r=None) -> dict:
    """D_r = monic gcd of all r x r minors, as the product of the first r
    Smith invariant factors.  ``r`` defaults to the rank over Q(q); the
    result is {} (zero) when r exceeds the rank."""
    rows = _public_matrix(matrix)
    if r is None:
        ech = _FractionFreeEchelon()
        r = sum(ech.insert(v) for v in rows)
    r = _int(r, "r", minimum=0)
    return _to_dict(_determinantal_divisor_dense(rows, r))


def _det(m) -> P:
    k = len(m)
    if k == 0:
        return _ONE
    if k == 1:
        return m[0][0]
    total = ()
    for j in range(k):
        if m[0][j]:
            minor = [row[:j] + row[j + 1:] for row in m[1:]]
            term = _mul(m[0][j], _det(minor))
            total = _add(total, term) if j % 2 == 0 else _sub(total, term)
    return total


def determinantal_divisor_by_minors(matrix, r) -> dict:
    """Independent oracle: monic gcd of every r x r minor (Laplace expansion).
    Exponential; for tiny matrices only."""
    rows = _public_matrix(matrix)
    r = _int(r, "r", minimum=0)
    if r == 0:
        return {0: Fraction(1)}
    if not rows or r > min(len(rows), len(rows[0])):
        return {}
    g = ()
    for I in combinations(range(len(rows)), r):
        for J in combinations(range(len(rows[0])), r):
            d = _det([[rows[i][j] for j in J] for i in I])
            if d:
                g = _gcd(g, d) if g else _monic(d)
    return _to_dict(g)


# ----------------------------------------- factorization over Q
def _squarefree_decomposition(f: P):
    """Yun: monic f = prod a_i^i with a_i square-free and pairwise coprime."""
    f = _monic(f)
    out = []
    if _deg(f) <= 0:
        return out
    b = _gcd(f, _deriv(f))
    c = _divmod(f, b)[0]
    d = _sub(_divmod(_deriv(f), b)[0], _deriv(c))
    i = 1
    while _deg(c) > 0:
        a = _gcd(c, d)
        c = _divmod(c, a)[0]
        d = _sub(_divmod(d, a)[0], _deriv(c))
        if _deg(a) > 0:
            out.append((a, i))
        i += 1
    return out


def _integral(f: P):
    den = _ilcm(*(a.denominator for a in f))
    v = [int(a * den) for a in f]
    g = 0
    for x in v:
        g = _igcd(g, x)
    return [x // g for x in v]


def _divisors(n):
    n = abs(n)
    small = [d for d in range(1, int(n ** 0.5) + 1) if n % d == 0]
    return sorted(set(small + [n // d for d in small]))


def _rational_roots(f: P):
    if not f:
        raise ValueError("zero polynomial")
    roots = []
    low = next(k for k, a in enumerate(f) if a)
    if low:
        roots.append(Fraction(0))
    v = _integral(f[low:])
    if len(v) == 1:
        return roots
    if max(abs(v[0]), abs(v[-1])) > 10 ** 9:
        raise ArithmeticError("rational root search limit exceeded")
    for p in _divisors(v[0]):
        for q in _divisors(v[-1]):
            for x in (Fraction(p, q), Fraction(-p, q)):
                if x not in roots and _eval(f, x) == 0:
                    roots.append(x)
    return sorted(roots)


_CYCLOTOMIC: dict = {}


def _cyclotomic(m: int) -> P:
    """Phi_m = (q^m - 1) / prod_{d | m, d < m} Phi_d, memoized, exact."""
    if m not in _CYCLOTOMIC:
        f = _trim([Fraction(-1)] + [Fraction(0)] * (m - 1) + [Fraction(1)])
        for d in range(1, m):
            if m % d == 0:
                f = _divmod(f, _cyclotomic(d))[0]
        _CYCLOTOMIC[m] = f
    return _CYCLOTOMIC[m]


def _totients(limit):
    phi = list(range(limit + 1))
    for p in range(2, limit + 1):
        if phi[p] == p:
            for k in range(p, limit + 1, p):
                phi[k] -= phi[k] // p
    return phi


def _is_prime(n):
    if n < 2:
        return False
    k = 2
    while k * k <= n:
        if n % k == 0:
            return False
        k += 1
    return True


def _may_have_cyclotomic_factor(v, m):
    """Sound filter: if Phi_m divides the integer polynomial v, then v(zeta)
    = 0 mod p for a primitive m-th root of unity zeta mod a prime p = 1 mod m
    not dividing the leading coefficient.  False proves Phi_m does not divide v."""
    p = m + 1
    while not (_is_prime(p) and v[-1] % p):
        p += m
    primes, k, rest = [], 2, m
    while k * k <= rest:
        if rest % k == 0:
            primes.append(k)
            while rest % k == 0:
                rest //= k
        k += 1
    if rest > 1:
        primes.append(rest)
    for a in range(2, p):
        z = pow(a, (p - 1) // m, p)
        if all(pow(z, m // l, p) != 1 for l in primes):
            break
    acc = 0
    for c in reversed(v):
        acc = (acc * z + c) % p
    return acc == 0


# --- arithmetic over F_p, for irreducibility certificates
def _fp_trim(c):
    while c and c[-1] == 0:
        c.pop()
    return c


def _fp_divmod(f, g, p):
    f = f[:]
    inv = pow(g[-1], p - 2, p)
    dg = len(g) - 1
    quo = [0] * max(len(f) - dg, 0)
    for k in range(len(f) - 1, dg - 1, -1):
        c = f[k] * inv % p
        if c:
            quo[k - dg] = c
            for j, b in enumerate(g):
                f[k - dg + j] = (f[k - dg + j] - c * b) % p
    return _fp_trim(quo), _fp_trim(f[:dg])


def _fp_gcd(f, g, p):
    while g:
        f, g = g, _fp_divmod(f, g, p)[1]
    if f:
        inv = pow(f[-1], p - 2, p)
        f = [x * inv % p for x in f]
    return f


def _fp_mulmod(a, b, f, p):
    out = [0] * (len(a) + len(b) - 1) if a and b else []
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                out[i + j] = (out[i + j] + x * y) % p
    return _fp_divmod(_fp_trim(out), f, p)[1]


def _fp_powmod(base, e, f, p):
    result, base = [1], _fp_divmod(base, f, p)[1]
    while e:
        if e & 1:
            result = _fp_mulmod(result, base, f, p)
        base = _fp_mulmod(base, base, f, p)
        e >>= 1
    return result


def _fp_degree_pattern(v, p):
    """Distinct-degree factorization of a square-free monic f mod p:
    a sorted list of irreducible factor degrees, or None if f is not
    square-free mod p or p divides the leading coefficient."""
    if v[-1] % p == 0:
        return None
    f = [x % p for x in v]
    inv = pow(f[-1], p - 2, p)
    f = [x * inv % p for x in f]
    df = _fp_trim([(k * a) % p for k, a in enumerate(f)][1:])
    if not df or len(_fp_gcd(f, df, p)) > 1:
        return None
    degrees = []
    h = [0, 1]
    d = 0
    while len(f) - 1 >= 2 * (d + 1):
        d += 1
        h = _fp_powmod(h, p, f, p)
        diff = _fp_trim([((h[k] if k < len(h) else 0) - (1 if k == 1 else 0)) % p
                         for k in range(max(len(h), 2))])
        g = _fp_gcd(f, diff, p) if diff else f
        k = (len(g) - 1) // d
        degrees += [d] * k
        if len(g) > 1:
            f = _fp_divmod(f, g, p)[0]
    if len(f) > 1:
        degrees.append(len(f) - 1)
    return sorted(degrees)


def _subset_sums(parts):
    sums = {0}
    for d in parts:
        sums |= {s + d for s in sums}
    return sums


_PRIMES = [p for p in range(3, 400) if all(p % k for k in range(2, int(p ** 0.5) + 1))]


def _irreducibility_certificate(f: P):
    """Certify that a square-free, rational-root-free primitive f is
    irreducible over Q from factor-degree patterns modulo primes.

    A factor of degree e over Q reduces (Gauss's lemma) to a product of
    factors mod p of total degree e, so e is a subset sum of every pattern.
    If the only common proper subset sum is none, f is irreducible.
    Returns (True, primes used) or (False, possible proper degrees).
    """
    v = _integral(f)
    d = len(v) - 1
    possible = set(range(1, d))
    used = []
    for p in _PRIMES:
        pattern = _fp_degree_pattern(v, p)
        if pattern is None:
            continue
        sums = _subset_sums(pattern)
        if possible & sums != possible:
            used.append([p, pattern])
        possible &= sums
        if not possible:
            return True, used
    return False, sorted(possible)


def _kronecker_split(f: P):
    """Find a proper factor of a primitive integer polynomial by Kronecker's
    method (exhaustive interpolation), or None if irreducible.  Exponential:
    used only for small degree when the modular certificate is inconclusive."""
    v = _integral(f)
    d = len(v) - 1
    points = [Fraction(k) for k in range(-(d // 2 + 1), d + 2)]
    for e in range(1, d // 2 + 1):
        xs = points[:e + 1]
        values = [_eval(tuple(Fraction(c) for c in v), x) for x in xs]
        if any(val == 0 for val in values):
            return None  # caller removed rational roots; cannot happen
        choices = [[s * t for t in _divisors(int(val)) for s in (1, -1)] for val in values]
        for ys in product(*choices):
            g = _interpolate(xs, ys)
            if g is None or _deg(g) != e or any(a.denominator != 1 for a in g):
                continue
            quo, rem = _divmod(tuple(Fraction(c) for c in v), g)
            if not rem:
                return g
    return None


def _interpolate(xs, ys):
    total = ()
    for i, xi in enumerate(xs):
        basis = _ONE
        den = Fraction(1)
        for j, xj in enumerate(xs):
            if j != i:
                basis = _mul(basis, (-xj, Fraction(1)))
                den *= xi - xj
        total = _add(total, _scale(basis, Fraction(ys[i]) / den))
    return total


def _factor_squarefree(f: P, kronecker_max_degree):
    """Irreducible monic factors of a square-free monic f with no rational
    root and no cyclotomic factor, with irreducibility certificates."""
    out = []
    pending = [f] if _deg(f) > 0 else []
    while pending:
        g = _monic(pending.pop())
        if _deg(g) == 1:
            out.append((g, {"method": "linear"}))
            continue
        ok, data = _irreducibility_certificate(g)
        if ok:
            out.append((g, {"method": "modular degree patterns", "primes_and_patterns": data}))
            continue
        if _deg(g) <= kronecker_max_degree:
            h = _kronecker_split(g)
            if h is None:
                out.append((g, {"method": "Kronecker exhaustive search"}))
            else:
                pending += [_monic(h), _monic(_divmod(g, h)[0])]
            continue
        out.append((g, {"method": "not certified irreducible", "possible_factor_degrees": data}))
    return out


def _divide_out(f: P, g: P):
    k = 0
    while _deg(f) >= _deg(g):
        quo, rem = _divmod(f, g)
        if rem:
            break
        f, k = quo, k + 1
    return f, k


def factor_over_q(f, kronecker_max_degree: int = 8):
    """Factor a nonzero polynomial over Q.

    Returns (leading coefficient, [(monic factor dict, multiplicity,
    certificate)]).  Linear factors come from the rational-root theorem and
    cyclotomic factors Phi_m (irreducible over Q) from a complete search over
    every m with phi(m) <= degree (using phi(m) >= sqrt(m/2)); each is divided
    out with its full multiplicity.  The rest is split into square-free parts
    and each part is certified irreducible by modular degree patterns or by
    Kronecker's method.  "not certified irreducible" is reported, never hidden.
    """
    f = _poly(f, "polynomial")
    if not f:
        raise ValueError("the zero polynomial has no factorization")
    kronecker_max_degree = _int(kronecker_max_degree, "kronecker_max_degree", minimum=0)
    lead = f[-1]
    rest = _monic(f)
    result = []
    if _deg(rest) > 0:
        for x in _rational_roots(rest):
            rest, k = _divide_out(rest, (-x, Fraction(1)))
            result.append(((-x, Fraction(1)), k, {"method": "linear (rational root)"}))
    if _deg(rest) >= 2:
        d = _deg(rest)
        phi = _totients(2 * d * d + 2)
        v = _integral(rest)
        for m in range(3, len(phi)):
            if phi[m] > _deg(rest):
                continue
            if not _may_have_cyclotomic_factor(v, m):
                continue
            rest, k = _divide_out(rest, _cyclotomic(m))
            if k:
                v = _integral(rest)
                result.append((_cyclotomic(m), k,
                               {"method": f"cyclotomic polynomial Phi_{m} (irreducible over Q)"}))
            if _deg(rest) < 2:
                break
    for a, i in _squarefree_decomposition(rest):
        for g, cert in _factor_squarefree(a, kronecker_max_degree):
            result.append((g, i, cert))
    result = [(_to_dict(g), i, c) for g, i, c in result]
    result.sort(key=lambda t: (max(t[0]), sorted(t[0].items())))
    check = (lead,)
    for g, i, _ in result:
        check = _mul(check, _pow(_from_dict(g), i))
    if check != f:
        raise ArithmeticError("factorization does not reproduce the polynomial")
    return lead, result


# ------------------------------------- algebraic specialization
class _NumberField:
    """Q[t]/(f) for f irreducible over Q (certified by the caller).  A
    non-invertible nonzero element would expose a factor of f; it raises."""

    def __init__(self, f: P):
        self.f = _monic(f)

    def red(self, a):
        return _divmod(a, self.f)[1] if len(a) >= len(self.f) else a

    def mul(self, a, b):
        return self.red(_mul(a, b))

    def inv(self, a):
        d, s, _ = _xgcd(a, self.f)
        if _deg(d) != 0:
            raise ArithmeticError("defining polynomial is reducible: zero divisor found")
        return self.red(s)


def _rank_over_field(rows, mul, inv, sub):
    rows = [list(r) for r in rows if any(r)]
    rank, n = 0, len(rows[0]) if rows else 0
    for c in range(n):
        k = next((i for i in range(rank, len(rows)) if rows[i][c]), None)
        if k is None:
            continue
        rows[rank], rows[k] = rows[k], rows[rank]
        pinv = inv(rows[rank][c])
        for i in range(rank + 1, len(rows)):
            if rows[i][c]:
                factor = mul(rows[i][c], pinv)
                rows[i] = [sub(x, mul(factor, y)) for x, y in zip(rows[i], rows[rank])]
        rank += 1
    return rank


def rank_at_rational(module_rows, q0) -> int:
    """Rank of the module generators specialized at rational q0."""
    x = _exact(q0, "q0")
    rows = [[_eval(f, x) for f in r] for r in module_rows]
    return _rank_over_field(rows, lambda a, b: a * b, lambda a: 1 / a, lambda a, b: a - b)


def rank_at_algebraic(module_rows, minimal_polynomial) -> int:
    """Rank of the module generators over Q(alpha) = Q[t]/(f), f irreducible:
    the entries are reduced modulo f, so q is replaced by alpha exactly."""
    K = _NumberField(_poly(minimal_polynomial, "minimal polynomial"))
    rows = [[K.red(f) for f in r] for r in module_rows]
    return _rank_over_field(rows, K.mul, K.inv, _sub)


# ------------------------------------------ real roots and the report
def _cauchy_bound(f: P) -> Fraction:
    lead = abs(f[-1])
    return 1 + max((abs(a) / lead for a in f[:-1]), default=Fraction(0))


def _fstr(x: Fraction) -> str:
    return f"{x.numerator}/{x.denominator}"


def _real_roots_from_factors(factors, domain):
    out = []
    for g, _, cert in factors:
        g = _from_dict(g)
        if _deg(g) == 1:
            x = -g[0] / g[1]
            if domain == "real" or 0 < x < 1:
                out.append({"rational": x, "factor": g})
            continue
        if cert["method"].startswith("cyclotomic"):
            continue  # Phi_m, m >= 3: its roots are non-real roots of unity
        if domain == "open_unit":
            low, high = Fraction(0), Fraction(1)
        else:
            bound = _cauchy_bound(g)
            low, high = -bound, bound
        for root in isolate_roots(_to_dict(g), low, high):
            root = dict(root)
            root["factor"] = g
            out.append(root)
    others = [_from_dict(h) for h, _, _ in factors]
    for root in out:
        if "interval" in root:
            root["interval"] = _refine(root["factor"], root["interval"],
                                       [h for h in others if h != root["factor"]])
    return sorted(out, key=lambda r: r.get("rational", r.get("interval", (0, 0))[0]))


_REFINE_WIDTH = Fraction(1, 1024)


def _roots_in_closed(h: P, a: Fraction, b: Fraction) -> int:
    return count_roots(_to_dict(h), a, b) + (_eval(h, a) == 0)


def _refine(g: P, interval, others):
    """Bisect an isolating interval of an irreducible g (degree >= 2, so no
    rational root) until its closure meets no root of any other factor and
    its width is at most 1/1024."""
    a, b = interval
    while b - a > _REFINE_WIDTH or any(_roots_in_closed(h, a, b) for h in others):
        mid = (a + b) / 2
        if count_roots(_to_dict(g), a, mid):
            b = mid
        else:
            a = mid
    return a, b


def real_roots(f, domain: str = "real"):
    """Every distinct real root of a nonzero f in the domain, isolated exactly.

    ``domain`` is "real" (all of R) or "open_unit" (0 < q < 1).  The roots
    are collected factor by factor from ``factor_over_q``: linear factors give
    rational roots, cyclotomic factors Phi_m (m >= 3) have no real root, and
    every other factor is isolated by Sturm sequences inside its Cauchy
    bound.  Each root is {"rational": x, "factor": dict} or
    {"interval": (a, b), "factor": dict}, the open interval containing exactly
    one root of that irreducible factor and none at the endpoints.
    """
    f = _poly(f, "polynomial")
    if not f:
        raise ValueError("the zero polynomial has every real root")
    if domain not in ("real", "open_unit"):
        raise ValueError('domain must be "real" or "open_unit"')
    if _deg(f) == 0:
        return []
    roots = _real_roots_from_factors(factor_over_q(_to_dict(f))[1], domain)
    for r in roots:
        r["factor"] = _to_dict(r["factor"])
    return roots


def _module_D(rows, r):
    return _determinantal_divisor_dense(rows, r)


def _root_record(root, factors, module_rows, generic, system, replay):
    """Exact evidence for one exceptional parameter."""
    if "rational" in root:
        x = root["rational"]
        record = {"value": _fstr(x)}
        if replay:
            cert = observable_closure(system.specialize(x))
            record["closure_rank"] = cert.rank
            record["module_rank"] = rank_at_rational(module_rows, x)
            record["rank_drop_confirmed"] = cert.rank < generic and record["module_rank"] == cert.rank
            record["closure_basis_words"] = [list(e.word) for e in cert.basis]
        return record
    a, b = root["interval"]
    g = root["factor"]
    cert = next(c for h, _, c in factors if _from_dict(h) == g)
    record = {"isolating_interval": [_fstr(a), _fstr(b)],
              "minimal_polynomial": polynomial_json(g),
              "minimal_polynomial_text": _poly_str(g),
              "irreducibility": cert["method"],
              "certification": "theorem: rank at alpha < r iff D_r(alpha) = 0; this factor divides D_r"}
    if cert["method"] != "not certified irreducible":
        record["rank_over_number_field"] = rank_at_algebraic(module_rows, _to_dict(g))
        record["rank_drop_confirmed"] = record["rank_over_number_field"] < generic
    return record


def parametric_observability(system: PolynomialOperatorSystem, replay: bool = True,
                             basis_divisor: bool = True) -> dict:
    """Generic rank, D_r of W, its factorization, the exceptional parameters
    in (0,1) and in R, exact replays, and (optionally) the determinantal
    divisor of the generic basis matrix B for comparison."""
    if not isinstance(system, PolynomialOperatorSystem):
        raise TypeError("system must be a PolynomialOperatorSystem")
    if not isinstance(replay, bool) or not isinstance(basis_divisor, bool):
        raise TypeError("replay and basis_divisor must be bool")
    closure = generic_closure(system)
    r = closure.rank
    module = observation_module(system)
    W = module.at_length_bound
    if len(W) != r:
        raise ArithmeticError("module rank differs from the generic closure rank")
    D = _module_D(W, r)
    D_full = _module_D(module.full, r)
    if _divmod(D, D_full)[1]:
        raise ArithmeticError("determinantal divisibility failed")
    lead, factors = factor_over_q(_to_dict(D))
    out = {
        "dimension": system.dimension,
        "generic_rank": r,
        "generic_basis_words": [[e.observation, list(e.word), _fstr(e.cost)] for e in closure.basis],
        "module_chain_ranks": [len(h) for h in module.chain],
        "module_stable_from_length": module.stable_from,
        "D_r_degree": _deg(D),
        "D_r_factors": [{"factor": _poly_str(_from_dict(g)), "multiplicity": i,
                         "irreducibility": c["method"]} for g, i, c in factors],
        "D_r_full_module_degree": _deg(D_full),
        "same_zero_set_as_full_module": _squarefree(D) == _squarefree(D_full),
        "endpoint_values_zero": {"q=0": _eval(D, Fraction(0)) == 0, "q=1": _eval(D, Fraction(1)) == 0},
        "non_real_exceptional_factors": [_poly_str(_from_dict(g)) for g, _, c in factors
                                         if c["method"].startswith("cyclotomic")],
    }
    for domain in ("open_unit", "real"):
        roots = _real_roots_from_factors(factors, domain)
        out[f"exceptional_{domain}"] = [_root_record(x, factors, W, r, system, replay) for x in roots]
    ranks = [r] + [x.get("closure_rank", x.get("rank_over_number_field", r)) for x in out["exceptional_real"]]
    out["minimum_rank_over_real_parameters"] = min(ranks) if replay or not out["exceptional_real"] else None
    out["rank_equals_generic_on_open_unit_interval"] = not out["exceptional_open_unit"]
    out["rank_equals_generic_on_real_line"] = not out["exceptional_real"]
    if basis_divisor:
        D_basis = _module_D(closure.matrix, r)
        if _divmod(D_basis, D)[1]:
            raise ArithmeticError("D_r(W) must divide D_r(B)")
        _, basis_factors = factor_over_q(_to_dict(D_basis))
        out["generic_basis_D_r_factors"] = [{"factor": _poly_str(_from_dict(g)), "multiplicity": i}
                                            for g, i, _ in basis_factors]
        spurious = []
        for g, _, _ in basis_factors:
            if _divmod(D, _from_dict(g))[1]:
                item = {"factor": _poly_str(_from_dict(g))}
                if len(g) == 2 or max(g) == 1:
                    x = -_from_dict(g)[0] / _from_dict(g)[1]
                    item["value"] = _fstr(x)
                    item["basis_rank"] = rank_at_rational(closure.matrix, x)
                    if replay:
                        item["closure_rank"] = observable_closure(system.specialize(x)).rank
                spurious.append(item)
        out["generic_basis_spurious_factors"] = spurious
    return out


def _squarefree(f: P) -> P:
    if _deg(f) <= 0:
        return _monic(f)
    return _monic(_divmod(f, _gcd(f, _deriv(f)))[0])


# ----------------------------------------- symbolic graph compiler
def symbolic_boundary_system(max_volume, attachments=None, attachment_costs=None,
                             observation_costs=None):
    """BoundaryExperimentSystem with q symbolic.

    Entry ((o,v),(o,j)) of the operator for context C is sum over kernel
    cells (k, e) of K_C(o) with k = v - j of count * q^e: an integer
    polynomial.  Returns (coordinates, PolynomialOperatorSystem).
    """
    from .contexts import orbits
    from .graph_experiments import ContextAttachment, standard_attachments
    from .terminals import terminal_kernel
    R = _int(max_volume, "max_volume", minimum=0)
    atts = tuple(standard_attachments() if attachments is None else attachments)
    if any(not isinstance(a, ContextAttachment) for a in atts):
        raise TypeError("attachments must be checked ContextAttachment objects")
    coordinates = tuple((o, v) for o in orbits(R) for v in range(sum(o), R + 1))
    observations = tuple(tuple(1 if v == target else 0 for _, v in coordinates)
                         for target in range(R + 1))
    operators = []
    for att in atts:
        kernel = terminal_kernel(att.graph, att.terminals, R)
        coefficients = {}
        for o in orbits(R):
            cells = kernel.get(o, {})
            coefficients[o] = [{} for _ in range(R + 1 - sum(o))]
            for (k, e), c in cells.items():
                if k < len(coefficients[o]):
                    d = coefficients[o][k]
                    d[e] = d.get(e, 0) + c
        operators.append(tuple(tuple(coefficients[o][v - j] if o == p and v >= j else 0
                                     for p, j in coordinates) for o, v in coordinates))
    return coordinates, PolynomialOperatorSystem(len(coordinates), operators, observations,
                                                 attachment_costs, observation_costs)
