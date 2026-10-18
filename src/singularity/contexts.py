"""Restricted-context quotients of two-terminal blocks (SNG-F47, SNG-F48).

A context is a second block glued to the first along the ordered terminals
(SNG-F41).  It is *swap-symmetric* when it has an automorphism exchanging
its two terminals; then K_C(s,t) = K_C(t,s) and the glued series

    L = sum_b x^|b| K(b) K_C(b) = sum_o x^|o| K^+(o) K_C(o)

runs over unordered orbits o = {s, t}, with K^+(o) = K(s,t) + K(t,s) for
s != t and K^+(o) = K(s,s).  So swap-symmetric contexts see a block only
through its symmetrized kernel (SNG-F47).

Whether they see all of it under a volume budget R is the interface-rank
question.  The unknowns are the coefficients Y_o[v] of
Y_o = x^|o| K^+(o), |o| <= v <= R, specialized at a rational q0.  At
interior volume zero a context with d leaves on each terminal and an
optional terminal edge has kernel q0^(d (s^2 + t^2) + eps (s - t)^2).
Without a terminal edge every swap-symmetric context has this form with
eps = 0, so two orbits with the same s^2 + t^2 (first {0,5}, {3,4}) can
never be told apart at the top degree v = R (SNG-F48(a)).  With the edge
the degree-by-degree triangular system is invertible as long as no three
orbits with |o| <= R share s^2 + t^2 (SNG-F48(b)); recover_symmetrized_kernel
is that construction.

SNG-F49 makes the top-degree picture exact for the whole class of simple
swap-symmetric contexts and records the realizability refinement: the
interior-volume-zero coefficient of x^|o| K^+(o) is fixed by the unordered
terminal degrees.  SNG-F50: a terminal edge of integer weight e < mu, mu the
largest collision multiplicity, restores recovery at every budget.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction
from typing import Sequence

from .graph import Graph, _integer

Orbit = tuple[int, int]


def symmetrize(kernel: dict) -> dict[Orbit, dict[tuple[int, int], int]]:
    """K^+ on orbits (s <= t) of a two-terminal kernel."""
    out: defaultdict[Orbit, Counter] = defaultdict(Counter)
    for b, cells in kernel.items():
        if len(b) != 2:
            raise ValueError("symmetrization is defined for two terminals")
        out[tuple(sorted(b))].update(cells)
    return {o: dict(sorted((k, c) for k, c in cells.items() if c)) for o, cells in sorted(out.items())}


def orbits(max_volume: int) -> list[Orbit]:
    R = _integer(max_volume, "max_volume", minimum=0)
    return [(s, t) for s in range(R + 1) for t in range(s, R + 1) if s + t <= R]


def orbit_groups(max_volume: int) -> dict[int, list[Orbit]]:
    """Orbits with |o| <= R grouped by s^2 + t^2, the only quantity seen at x^0 without an edge."""
    groups: defaultdict[int, list[Orbit]] = defaultdict(list)
    for s, t in orbits(max_volume):
        groups[s * s + t * t].append((s, t))
    return dict(sorted(groups.items()))


def top_degree_defect(max_volume: int) -> int:
    """Lower bound for the rank defect of edge-free symmetric contexts at budget R (SNG-F48(a))."""
    groups = orbit_groups(max_volume)
    return sum(len(g) for g in groups.values()) - len(groups)


def symmetric_context(leaves: int, terminal_edge: bool = False, common: int = 0) -> tuple[Graph, tuple[int, int]]:
    """Terminals 0, 1 with ``leaves`` pendant leaves each, ``common`` shared neighbours, optional edge 01."""
    d = _integer(leaves, "leaves", minimum=0)
    c = _integer(common, "common", minimum=0)
    edges, nxt = [(0, 1)] if terminal_edge else [], 2
    for _ in range(d):
        edges += [(0, nxt), (1, nxt + 1)]
        nxt += 2
    for _ in range(c):
        edges += [(0, nxt), (1, nxt)]
        nxt += 1
    return Graph(nxt, edges), (0, 1)


def _mul(a: list, b: list, R: int) -> list:
    out = [Fraction(0)] * (R + 1)
    for i, x in enumerate(a[: R + 1]):
        if x:
            for j in range(R + 1 - i):
                out[i + j] += x * b[j]
    return out


def _context_series(orbit: Orbit, leaves: int, edge: int, common: int, R: int, q0: Fraction) -> list:
    """K_C(orbit) at q0 modulo x^(R+1) for symmetric_context(leaves, edge, common)."""
    s, t = orbit
    leaf = lambda h: [q0 ** ((c - h) ** 2) for c in range(R + 1)]
    shared = [q0 ** ((w - s) ** 2 + (w - t) ** 2) for w in range(R + 1)]
    out = [q0 ** (edge * (s - t) ** 2)] + [Fraction(0)] * R
    pair = _mul(leaf(s), leaf(t), R)
    for _ in range(leaves):
        out = _mul(out, pair, R)
    for _ in range(common):
        out = _mul(out, shared, R)
    return out


def symmetric_probe_set(max_volume: int, max_edge_weight: int = 1) -> list[tuple[int, int]]:
    """(leaves, edge weight) pairs used by recover_symmetrized_kernel: G (W + 1) probes, G = #distinct s^2+t^2."""
    G = len(orbit_groups(max_volume))
    W = _integer(max_edge_weight, "max_edge_weight", minimum=0)
    return [(d, e) for d in range(G) for e in range(W + 1)]


def _solve(rows: list[list[Fraction]], rhs: list[Fraction], unknowns: int) -> list[Fraction]:
    """Exact solution of a consistent overdetermined system of full column rank."""
    m = [r[:] + [v] for r, v in zip(rows, rhs)]
    rank = 0
    for col in range(unknowns):
        pivot = next((i for i in range(rank, len(m)) if m[i][col]), None)
        if pivot is None:
            raise ArithmeticError("probe system is not of full column rank")
        m[rank], m[pivot] = m[pivot], m[rank]
        inv = 1 / m[rank][col]
        m[rank] = [x * inv for x in m[rank]]
        for i in range(len(m)):
            if i != rank and m[i][col]:
                f = m[i][col]
                m[i] = [x - f * y for x, y in zip(m[i], m[rank])]
        rank += 1
    if any(row[-1] for row in m[rank:]):
        raise ArithmeticError("probe values are inconsistent with a symmetrized kernel")
    return [m[i][-1] for i in range(unknowns)]


def recover_symmetrized_kernel(probe_values: dict[tuple[int, int], Sequence], max_volume: int, q,
                               max_edge_weight: int = 1) -> dict[Orbit, list]:
    """Recover Y_o = x^|o| K^+(o)(x, q0) mod x^(R+1) from symmetric probes (SNG-F48(b)).

    ``probe_values[(d, eps)]`` is the glued series at q0 (index = volume)
    with d leaves on each terminal and a terminal edge of weight eps (eps = 0:
    no edge); keys must cover symmetric_probe_set(R, W).  With W = 1 these
    are the simple contexts symmetric_context(d, eps); with larger W the
    Vandermonde in eps handles groups of up to W + 1 orbits (SNG-F50).
    Degree v is solved after degrees < v are known: the residual equals
    sum_o Y_o[v] q0^(d m_o + eps d_o) with m_o = s^2 + t^2, d_o = (s - t)^2,
    which is injective when no W + 2 orbits share m (Vandermonde in d over
    the distinct q0^m, then a Vandermonde in eps over the distinct q0^(d_o)).
    """
    R, q0 = _integer(max_volume, "max_volume", minimum=0), Fraction(q)
    W = _integer(max_edge_weight, "max_edge_weight", minimum=0)
    if not 0 < q0 < 1:
        raise ValueError("q must lie strictly between 0 and 1 so that the nodes are distinct")
    if max_group_size(R) > W + 1:
        raise ArithmeticError(f"{max_group_size(R)} orbits share s^2 + t^2; edge weights 0..{W} do not suffice (SNG-F49)")
    probes = symmetric_probe_set(R, W)
    missing = [p for p in probes if p not in probe_values]
    if missing:
        raise ValueError(f"missing probe values for {missing}")
    os = orbits(R)
    kernels = {(p, o): _context_series(o, p[0], p[1], 0, R, q0) for p in probes for o in os}
    values = {p: [Fraction(v) for v in probe_values[p]] + [Fraction(0)] * (R + 1 - len(probe_values[p])) for p in probes}
    Y = {o: [Fraction(0)] * (R + 1) for o in os}
    for v in range(R + 1):
        active = [o for o in os if sum(o) <= v]
        rows, rhs = [], []
        for p in probes:
            residual = values[p][v] - sum(Y[o][j] * kernels[p, o][v - j] for o in os for j in range(sum(o), v))
            rows.append([kernels[p, o][0] for o in active])
            rhs.append(residual)
        for o, y in zip(active, _solve(rows, rhs, len(active))):
            Y[o][v] = y
    return Y


def symmetric_interface_rank(max_volume: int, q, terminal_edge: bool, max_common: int | None = None,
                             max_leaves: int | None = None) -> tuple[int, int]:
    """(number of unknowns Y_o[v], exact rank of the probe map) for symmetric_context(d, eps, c).

    d ranges over 0..max_leaves (default: number of orbits), c over
    0..max_common (default R), eps over {0} or {0, 1}.  The rank is that of
    this family; SNG-F48(a) bounds every edge-free symmetric family.
    """
    R, q0 = _integer(max_volume, "max_volume", minimum=0), Fraction(q)
    os = orbits(R)
    max_common = R if max_common is None else _integer(max_common, "max_common", minimum=0)
    max_leaves = len(os) if max_leaves is None else _integer(max_leaves, "max_leaves", minimum=0)
    columns = [(o, j) for o in os for j in range(sum(o), R + 1)]
    rows = []
    for d in range(max_leaves + 1):
        for e in ((0, 1) if terminal_edge else (0,)):
            for c in range(max_common + 1):
                kern = {o: _context_series(o, d, e, c, R, q0) for o in os}
                for w in range(R + 1):
                    rows.append([kern[o][w - j] if w >= j else Fraction(0) for o, j in columns])
    rank = 0
    for col in range(len(columns)):
        pivot = next((i for i in range(rank, len(rows)) if rows[i][col]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(rank + 1, len(rows)):
            if rows[i][col]:
                f = rows[i][col] / rows[rank][col]
                rows[i] = [x - f * y for x, y in zip(rows[i], rows[rank])]
        rank += 1
    return len(columns), rank


def max_group_size(max_volume: int) -> int:
    """Largest number of orbits with |o| <= R sharing s^2 + t^2."""
    return max(len(g) for g in orbit_groups(max_volume).values())


def diagonal_defects(max_volume: int, kappa: int, realizable: bool = False) -> list[int]:
    """delta_v = sum over s^2+t^2 groups of max(0, |g| - kappa), v = 0..R (SNG-F49).

    kappa is the number of distinct terminal-edge weights available: 1 with
    no terminal edge, 2 for simple contexts, W + 1 with weights 0..W.  The
    group at degree v holds the orbits with |o| <= v, or |o| < v when
    ``realizable``: coefficients with |o| = v have interior volume zero and
    are fixed by the unordered terminal degrees, which degree 1 reveals.
    """
    R = _integer(max_volume, "max_volume", minimum=0)
    kappa = _integer(kappa, "kappa", minimum=1)
    out = []
    for v in range(R + 1):
        sizes = Counter(s * s + t * t for s, t in orbits(v) if not realizable or s + t < v)
        out.append(sum(max(0, size - kappa) for size in sizes.values()))
    return out


def interface_status(max_volume: int, kappa: int, realizable: bool = False) -> dict:
    """What SNG-F49 proves about the invisible subspace at budget R.

    The invisible subspace of the formal (or realizable) coefficient space
    has dimension at least the top defect delta_R, and exactly delta_R when
    every lower diagonal block is injective (delta_v = 0 for v < R).
    """
    R = _integer(max_volume, "max_volume", minimum=0)
    defects = diagonal_defects(R, kappa, realizable)
    unknowns = sum(R + 1 - sum(o) - (1 if realizable else 0) for o in orbits(R))
    exact = not any(defects[:-1])
    return {"budget": R, "kappa": kappa, "realizable": realizable, "unknowns": unknowns,
            "top_defect": defects[-1], "lower_defects": sum(defects[:-1]),
            "invisible_dimension": defects[-1] if exact else None,
            "invisible_dimension_bounds": [defects[-1], sum(defects)]}


def top_degree_kernel(max_volume: int, kappa: int, realizable: bool = False) -> list[dict[Orbit, dict[int, int]]]:
    """A basis of the top-degree invisible vectors, as polynomials in q (SNG-F49).

    For each s^2+t^2 group with more than kappa orbits o_0 < o_1 < ... (in
    the realizable case only those with |o| < R), and each j >= kappa, the
    vector on S = (o_0..o_{kappa-1}, o_j) with entry (-1)^i times the
    Vandermonde determinant of the nodes q^(d_o), o in S minus S_i, is
    annihilated by every row q^(delta m + e d), e < kappa.
    """
    from .polynomials import mul, normalize, sub

    R = _integer(max_volume, "max_volume", minimum=0)
    kappa = _integer(kappa, "kappa", minimum=1)
    groups: defaultdict[int, list[Orbit]] = defaultdict(list)
    for s, t in orbits(R):
        if not realizable or s + t < R:
            groups[s * s + t * t].append((s, t))
    basis = []
    for m, group in sorted(groups.items()):
        for j in range(kappa, len(group)):
            S = group[:kappa] + [group[j]]
            vector = {}
            for i, o in enumerate(S):
                nodes = [(u - w) ** 2 for u, w in S[:i] + S[i + 1:]]
                det = {0: 1}
                for b in range(len(nodes)):
                    for a in range(b):
                        det = mul(det, sub({nodes[b]: 1}, {nodes[a]: 1}))
                vector[o] = normalize({e: (-1) ** i * c for e, c in det.items()})
            basis.append(vector)
    return basis


def interior_zero_coefficient(degrees: tuple[int, int], orbit: Orbit) -> dict[int, int]:
    """Coefficient of x^|o| in x^|o| K^+(o) for a block whose terminals have
    internal degrees (a, b) and no terminal edge: q^(a s^2 + b t^2) + q^(b s^2 + a t^2), or q^((a+b) s^2) for s = t."""
    (a, b), (s, t) = degrees, orbit
    if s == t:
        return {(a + b) * s * s: 1}
    out = Counter({a * s * s + b * t * t: 1})
    out[b * s * s + a * t * t] += 1
    return dict(sorted(out.items()))


def weighted_probe(block: Graph, leaves: int, edge_weight: int):
    """Block glued to d leaves on each terminal and a terminal edge of the given weight, as a WeightedGraph."""
    from .weighted import WeightedGraph

    if (0, 1) in block.edges and edge_weight:
        raise ValueError("the block already has a terminal edge")
    edges, nxt = [(u, v, 1) for u, v in block.edges], block.n
    for _ in range(_integer(leaves, "leaves", minimum=0)):
        edges += [(0, nxt, 1), (1, nxt + 1, 1)]
        nxt += 2
    if _integer(edge_weight, "edge_weight", minimum=0):
        edges.append((0, 1, edge_weight))
    return WeightedGraph((1,) * nxt, tuple(edges))


def symmetric_interface_rank_mod(max_volume: int, terminal_edge: bool, prime: int = (1 << 61) - 1, q: int = 3,
                                 target: int | None = None, seed: int = 0) -> tuple[int, int]:
    """Rank of the symmetric_context(d, eps, c) probe map modulo a prime, at q = q mod p.

    The entries are integer polynomials in q evaluated at q, so a rank r
    found modulo p is a lower bound for the rank over Q(q).  Contexts are
    taken in a seeded random order and the elimination stops at ``target``.
    """
    import random

    R = _integer(max_volume, "max_volume", minimum=0)
    os_ = orbits(R)
    columns = [(o, j) for o in os_ for j in range(sum(o), R + 1)]
    contexts = [(d, e, c) for d in range(len(os_) + 1) for e in ((0, 1) if terminal_edge else (0,)) for c in range(R + 1)]
    random.Random(seed).shuffle(contexts)
    P = prime

    def smul(a, b):
        out = [0] * (R + 1)
        for i, x in enumerate(a):
            if x:
                for j in range(R + 1 - i):
                    out[i + j] = (out[i + j] + x * b[j]) % P
        return out

    def qp(e):
        return pow(q, e, P)

    basis: dict[int, list[int]] = {}
    for d, e, c in contexts:
        kern = {}
        for s, t in os_:
            series = [qp(e * (s - t) ** 2)] + [0] * R
            pair = smul([qp((k - s) ** 2) for k in range(R + 1)], [qp((k - t) ** 2) for k in range(R + 1)])
            shared = [qp((w - s) ** 2 + (w - t) ** 2) for w in range(R + 1)]
            for _ in range(d):
                series = smul(series, pair)
            for _ in range(c):
                series = smul(series, shared)
            kern[s, t] = series
        for w in range(R + 1):
            row = [kern[o][w - j] if w >= j else 0 for o, j in columns]
            for col, (pivot_row) in sorted(basis.items()):
                if row[col]:
                    f = row[col]
                    row = [(x - f * y) % P for x, y in zip(row, pivot_row)]
            lead = next((i for i, x in enumerate(row) if x), None)
            if lead is not None:
                inv = pow(row[lead], P - 2, P)
                basis[lead] = [x * inv % P for x in row]
                if target is not None and len(basis) >= target:
                    return len(columns), len(basis)
    return len(columns), len(basis)


def _rank_mod(rows: list[list[int]], prime: int) -> int:
    rows = [[x % prime for x in r] for r in rows]
    rank = 0
    for col in range(len(rows[0]) if rows else 0):
        pivot = next((i for i in range(rank, len(rows)) if rows[i][col]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inv = pow(rows[rank][col], prime - 2, prime)
        for i in range(rank + 1, len(rows)):
            if rows[i][col]:
                f = rows[i][col] * inv % prime
                rows[i] = [(x - f * y) % prime for x, y in zip(rows[i], rows[rank])]
        rank += 1
    return rank


def top_block_rank_mod(max_volume: int, kappa: int, realizable: bool = False,
                       prime: int = (1 << 61) - 1, q: int = 3) -> tuple[int, int]:
    """(columns, rank) of the degree-R diagonal block q^(delta m_o + e d_o), e < kappa, modulo a prime.

    delta ranges over 0..G-1 with G the number of distinct m among the
    columns, which is enough for the Vandermonde in delta.
    """
    R = _integer(max_volume, "max_volume", minimum=0)
    cols = [o for o in orbits(R) if not realizable or sum(o) < R]
    if not cols:
        return 0, 0
    G = len({s * s + t * t for s, t in cols})
    rows = [[pow(q, delta * (s * s + t * t) + e * (s - t) ** 2, prime) for s, t in cols]
            for delta in range(G) for e in range(kappa)]
    return len(cols), _rank_mod(rows, prime)


def lower_degree_condition(max_degree: int, kappa: int, realizable: bool = False,
                           prime: int = (1 << 61) - 1, q: int = 1234567891) -> int | None:
    """Least degree v <= max_degree at which the SNG-F49(b) condition fails, or None.

    At degree v the group of orbits sharing m (|o| <= v, or |o| < v when
    ``realizable``) must have full column rank for the functionals
    y^e tau^i (e < kappa, i <= 1), with y_o = q^((s-t)^2) and
    tau_o = q^(1-2s) + q^(1-2t) - q^(2-2(s+t)).  Columns are scaled by
    q^(2(s+t)) to clear denominators; a nonzero minor modulo p at one q
    proves full rank over Q(q).
    """
    V = _integer(max_degree, "max_degree", minimum=0)
    kappa = _integer(kappa, "kappa", minimum=1)
    groups: defaultdict[int, list[Orbit]] = defaultdict(list)
    for s in range(V + 1):
        for t in range(s, V + 1 - s):
            groups[s * s + t * t].append((s, t))
    worst = None
    for group in groups.values():
        group.sort(key=sum)
        for k in range(2, len(group) + 1):
            prefix = group[:k]
            rows = []
            for e in range(kappa):
                for i in (0, 1):
                    row = []
                    for s, t in prefix:
                        y = pow(q, e * (s - t) ** 2, prime)
                        scale = pow(q, 2 * (s + t), prime)
                        tau = (pow(q, 1 + 2 * t, prime) + pow(q, 1 + 2 * s, prime) - q * q) % prime
                        row.append(y * (tau if i else scale) % prime)
                    rows.append(row)
            if _rank_mod(rows, prime) < k:
                degree = sum(prefix[-1]) + (1 if realizable else 0)
                if degree <= V and (worst is None or degree < worst):
                    worst = degree
                break
    return worst
