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


def symmetric_probe_set(max_volume: int) -> list[tuple[int, int]]:
    """(leaves, edge) pairs used by recover_symmetrized_kernel: 2G probes, G = #distinct s^2+t^2."""
    G = len(orbit_groups(max_volume))
    return [(d, e) for d in range(G) for e in (0, 1)]


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


def recover_symmetrized_kernel(probe_values: dict[tuple[int, int], Sequence], max_volume: int, q) -> dict[Orbit, list]:
    """Recover Y_o = x^|o| K^+(o)(x, q0) mod x^(R+1) from symmetric probes (SNG-F48(b)).

    ``probe_values[(d, eps)]`` is the glued series at q0 (index = volume)
    with symmetric_context(d, eps); keys must cover symmetric_probe_set(R).
    Degree v is solved after degrees < v are known: the residual equals
    sum_o Y_o[v] q0^(d m_o + eps d_o) with m_o = s^2 + t^2, d_o = (s - t)^2,
    which is injective when no three orbits share m (Vandermonde in d over
    the distinct q0^m, then a 2 x 2 system in eps).
    """
    R, q0 = _integer(max_volume, "max_volume", minimum=0), Fraction(q)
    if not 0 < q0 < 1:
        raise ValueError("q must lie strictly between 0 and 1 so that the nodes are distinct")
    if any(len(g) > 2 for g in orbit_groups(R).values()):
        raise ArithmeticError("three orbits share s^2 + t^2; the leaf-and-edge probes do not suffice")
    probes = symmetric_probe_set(R)
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
