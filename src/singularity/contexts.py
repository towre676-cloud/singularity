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


REALIZABLE_MODES = (False, True, "slice", "balanced", "interpolated")


def _free(orbit: Orbit, v: int, realizable) -> bool:
    """Whether the coordinate Y_o[v] can differ between two indistinguishable blocks.

    ``False``: the formal space, every coordinate.  ``True``: interior
    volume j = v - |o| >= 1 (j = 0 is fixed by the terminal degrees,
    SNG-F49(c)).  ``"slice"``: also j = 1 once v >= 6 (SNG-F52(a), which
    reads the slice from states of total volume <= 5).  ``"balanced"``,
    for blocks whose terminals have equal internal degree: j >= 1 and
    3j >= v, since slice j is read from the states with s, t <= j, of total
    volume <= 3j (SNG-F52(b)).  ``"interpolated"``: the same rule for every
    block, by the unequal-degree interpolation theorem SNG-F59 (valid over
    Q(q) and at every rational q in (0, 1)).
    """
    if realizable not in REALIZABLE_MODES:
        raise ValueError(f"realizable must be one of {REALIZABLE_MODES}")
    j = v - sum(orbit)
    if realizable is False:
        return True
    if realizable is True:
        return j >= 1
    if realizable == "slice":
        return j >= (2 if v >= 6 else 1)
    return j >= 1 and 3 * j >= v  # "balanced" and "interpolated"


def _first_free(orbit: Orbit, realizable) -> int:
    v = sum(orbit)
    while not _free(orbit, v, realizable):
        v += 1
    return v


def max_group_size(max_volume: int) -> int:
    """Largest number of orbits with |o| <= R sharing s^2 + t^2."""
    return max(len(g) for g in orbit_groups(max_volume).values())


def diagonal_defects(max_volume: int, kappa: int, realizable=False) -> list[int]:
    """delta_v = sum over s^2+t^2 groups of max(0, |g| - kappa), v = 0..R (SNG-F49).

    kappa is the number of distinct terminal-edge weights available: 1 with
    no terminal edge, 2 for simple contexts, W + 1 with weights 0..W.  The
    group at degree v holds the orbits with |o| <= v whose coordinate is
    free in the sense of ``_free``: in the realizable modes, coordinates
    fixed by lower-degree data (terminal degrees, rigid interior slices)
    are removed.
    """
    R = _integer(max_volume, "max_volume", minimum=0)
    kappa = _integer(kappa, "kappa", minimum=1)
    out = []
    for v in range(R + 1):
        sizes = Counter(s * s + t * t for s, t in orbits(v) if _free((s, t), v, realizable))
        out.append(sum(max(0, size - kappa) for size in sizes.values()))
    return out


def interface_status(max_volume: int, kappa: int, realizable=False) -> dict:
    """What SNG-F49 proves about the invisible subspace at budget R.

    The invisible subspace of the formal (or realizable) coefficient space
    has dimension at least the top defect delta_R, and exactly delta_R when
    every lower diagonal block is injective (delta_v = 0 for v < R).
    """
    R = _integer(max_volume, "max_volume", minimum=0)
    defects = diagonal_defects(R, kappa, realizable)
    unknowns = sum(_free(o, v, realizable) for o in orbits(R) for v in range(sum(o), R + 1))
    exact = not any(defects[:-1])
    return {"budget": R, "kappa": kappa, "realizable": realizable, "unknowns": unknowns,
            "top_defect": defects[-1], "lower_defects": sum(defects[:-1]),
            "invisible_dimension": defects[-1] if exact else None,
            "invisible_dimension_bounds": [defects[-1], sum(defects)]}


def top_degree_kernel(max_volume: int, kappa: int, realizable=False) -> list[dict[Orbit, dict[int, int]]]:
    """A basis of the top-degree invisible vectors, as polynomials in q (SNG-F49).

    For each s^2+t^2 group with more than kappa orbits o_0 < o_1 < ... (in
    the realizable modes only the free orbits), and each j >= kappa, the
    vector on S = (o_0..o_{kappa-1}, o_j) with entry (-1)^i times the
    Vandermonde determinant of the nodes q^(d_o), o in S minus S_i, is
    annihilated by every row q^(delta m + e d), e < kappa.
    """
    from .polynomials import mul, normalize, sub

    R = _integer(max_volume, "max_volume", minimum=0)
    kappa = _integer(kappa, "kappa", minimum=1)
    groups: defaultdict[int, list[Orbit]] = defaultdict(list)
    for s, t in orbits(R):
        if _free((s, t), R, realizable):
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


def top_block_rank_mod(max_volume: int, kappa: int, realizable=False,
                       prime: int = (1 << 61) - 1, q: int = 3) -> tuple[int, int]:
    """(columns, rank) of the degree-R diagonal block q^(delta m_o + e d_o), e < kappa, modulo a prime.

    delta ranges over 0..G-1 with G the number of distinct m among the
    columns, which is enough for the Vandermonde in delta.
    """
    R = _integer(max_volume, "max_volume", minimum=0)
    cols = [o for o in orbits(R) if _free(o, R, realizable)]
    if not cols:
        return 0, 0
    G = len({s * s + t * t for s, t in cols})
    rows = [[pow(q, delta * (s * s + t * t) + e * (s - t) ** 2, prime) for s, t in cols]
            for delta in range(G) for e in range(kappa)]
    return len(cols), _rank_mod(rows, prime)


def lower_degree_condition(max_degree: int, kappa: int, realizable=False,
                           prime: int = (1 << 61) - 1, q: int = 1234567891) -> int | None:
    """Least degree v <= max_degree at which the SNG-F49(b) condition fails, or None.

    At degree v the group of free orbits sharing m (see ``_free``) must
    have full column rank for the functionals
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
        group.sort(key=lambda o: _first_free(o, realizable))
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
                degree = _first_free(prefix[-1], realizable)
                if degree <= V and (worst is None or degree < worst):
                    worst = degree
                break
    return worst


def tau(orbit: Orbit, q) -> Fraction:
    """tau_o = q^(1-2s) + q^(1-2t) - q^(2-2(s+t)) = 1 - (q^(1-2s) - 1)(q^(1-2t) - 1)."""
    s, t = orbit
    q = Fraction(q)
    return q ** (1 - 2 * s) + q ** (1 - 2 * t) - q ** (2 - 2 * (s + t))


def finite_difference_budget(max_volume: int) -> int:
    """Observation budget R + m_R - 1 of SNG-F51, m_R the largest s^2+t^2 collision through R."""
    R = _integer(max_volume, "max_volume", minimum=0)
    return R + max_group_size(R) - 1


def finite_difference_probe_set(max_volume: int) -> list[tuple[int, int]]:
    """(leaves per terminal, shared neighbours) contexts used by recover_by_finite_differences.

    For j < m_R and k = j..j+G-1 (G distinct values of s^2+t^2), the
    contexts (k - c, c), c = 0..j; no terminal edge is used.
    """
    R = _integer(max_volume, "max_volume", minimum=0)
    G, m = len(orbit_groups(R)), max_group_size(R)
    return sorted({(k - c, c) for j in range(m) for k in range(j, j + G) for c in range(j + 1)})


def recover_by_finite_differences(probe_values: dict[tuple[int, int], Sequence], max_volume: int, q) -> dict[Orbit, list]:
    """Recover Y_o = x^|o| K^+(o)(x, q0) mod x^(R+1) from edge-free symmetric probes (SNG-F51).

    ``probe_values[(d, c)]`` is the glued series at q0 through volume
    R + m_R - 1 with d leaves on each terminal and c shared neighbours.
    The j-th difference in c at fixed k = d + c is the context factor
    P^(k-j) (S - P)^j, which vanishes below x^j and has x^j coefficient
    q0^(k m_o) (-tau_o)^j.  Degree n is solved from output volumes n..n+m-1:
    a Vandermonde in k separates the s^2+t^2 groups, a Vandermonde in j
    the orbits of a group, whose tau_o are distinct (strictly decreasing
    toward balance on each circle).
    """
    from math import comb

    R, q0 = _integer(max_volume, "max_volume", minimum=0), Fraction(q)
    if not 0 < q0 < 1:
        raise ValueError("q must lie strictly between 0 and 1")
    B = finite_difference_budget(R)
    probes = finite_difference_probe_set(R)
    missing = [p for p in probes if p not in probe_values]
    if missing:
        raise ValueError(f"missing probe values for {missing}")
    values = {}
    for p in probes:
        series = [Fraction(v) for v in probe_values[p]]
        if len(series) < B + 1:
            raise ValueError(f"probe {p} needs its series through volume {B}")
        values[p] = series[: B + 1]
    os_ = orbits(R)
    G, m = len(orbit_groups(R)), max_group_size(R)
    # Differenced measurement and context factor for each (k, j).
    measured, factor = {}, {}
    for j in range(m):
        for k in range(j, j + G):
            measured[k, j] = [sum((-1) ** (j - c) * comb(j, c) * values[k - c, c][w] for c in range(j + 1)) for w in range(B + 1)]
            for o in os_:
                series = [Fraction(0)] * (B + 1)
                for c in range(j + 1):
                    term = _context_series(o, k - c, 0, c, B, q0)
                    series = [a + (-1) ** (j - c) * comb(j, c) * b for a, b in zip(series, term)]
                factor[k, j, o] = series
    Y = {o: [Fraction(0)] * (R + 1) for o in os_}
    for n in range(R + 1):
        active = [o for o in os_ if sum(o) <= n]
        groups = Counter(s * s + t * t for s, t in active)
        jmax = max(groups.values())
        rows, rhs = [], []
        for j in range(jmax):
            for k in range(j, j + G):
                w = n + j
                residual = measured[k, j][w] - sum(Y[o][i] * factor[k, j, o][w - i] for o in os_ for i in range(sum(o), n))
                rows.append([factor[k, j, o][j] for o in active])
                rhs.append(residual)
        for o, y in zip(active, _solve(rows, rhs, len(active))):
            Y[o][n] = y
    return Y


def boundary_determinant(j: int, d: int, ell: int) -> dict[int, int]:
    """Laurent polynomial in z = 1/q of det[z^(2kt) | z^(2kt - d t^2 - ell t)], t = 1..2j, k < j (SNG-F59).

    Rows t, columns A_k then B_k; computed by the Leibniz expansion (small j only).
    """
    from itertools import permutations

    j, d, ell = _integer(j, "j", minimum=1), _integer(d, "d", minimum=1), _integer(ell, "ell", minimum=0)
    E = [[2 * k * t for k in range(j)] + [2 * k * t - d * t * t - ell * t for k in range(j)] for t in range(1, 2 * j + 1)]
    n = len(E)
    out: Counter = Counter()
    for perm in permutations(range(n)):
        inversions = sum(1 for a in range(n) for b in range(a + 1, n) if perm[a] > perm[b])
        out[sum(E[i][perm[i]] for i in range(n))] += -1 if inversions % 2 else 1
    return {e: c for e, c in sorted(out.items()) if c}


def interpolation_rank(j: int, d: int, ell: int, q) -> tuple[int, int]:
    """(columns, rank) of P -> (F_P(s,t))_{s <= t, s+t <= 2j} at q0 for bidegree (j, j) (SNG-F59).

    F_P(s,t) = q^(d s^2 + ell s) P(q^(-2s), q^(-2t)) + q^(d t^2 + ell t) P(q^(-2t), q^(-2s)).
    The square system ((j+1)^2 states) is injective exactly when rank = columns.
    """
    q0 = Fraction(q)
    monomials = [(a, b) for a in range(j + 1) for b in range(j + 1)]
    rows = []
    for s in range(j + 1):
        for t in range(s, 2 * j - s + 1):
            row = []
            for a, b in monomials:
                row.append(q0 ** (d * s * s + ell * s) * q0 ** (-2 * s * a - 2 * t * b)
                           + q0 ** (d * t * t + ell * t) * q0 ** (-2 * t * a - 2 * s * b))
            rows.append(row)
    rank = 0
    for col in range(len(monomials)):
        pivot = next((i for i in range(rank, len(rows)) if rows[i][col]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(rank + 1, len(rows)):
            if rows[i][col]:
                f = rows[i][col] / rows[rank][col]
                rows[i] = [x - f * y for x, y in zip(rows[i], rows[rank])]
        rank += 1
    return len(monomials), rank
