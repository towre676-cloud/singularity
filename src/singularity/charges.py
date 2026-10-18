"""Boundary charges: compressed interfaces and context transport (SNG-F53, SNG-F54).

For a block with terminals b_1..b_k, give every interior vertex v its
terminal-neighbourhood pattern eta_v in {0,1}^k.  For interior heights h
of total j the energy is

    E = [E_int(h) + sum_v |eta_v| h_v^2] + sum_i d_i b_i^2 + E_T(b) - 2 <b, Q(h)>,

with Q(h) = sum_v h_v eta_v the boundary charge, d_i the number of
interior neighbours of terminal i and E_T the energy of edges among the
terminals.  So the kernel is determined by the charge table

    A_{j,Q} = sum over |h| = j with Q(h) = Q of q^(E_int(h) + sum_v |eta_v| h_v^2),

and Q ranges over the lattice points of j conv{eta_v}: O(j^d) values with d
the affine dimension of the patterns.  When both terminals of a
two-terminal block dominate the interior and are nonadjacent, every
pattern is (1,1), Q = (j, j), and the interface is the single sequence
A_j: R + 1 polynomials through volume R.

For a known context C the closed series is Z_C = T_C A, where T_C is lower
triangular with unit diagonal and does not depend on the interior, so one
closure determines A and every other closure: Z_D = T_D T_C^(-1) Z_C.

Charge tables also compose directly: parallel gluing is graded convolution,
and forgetting a terminal sums its height with an exact energy shift.
Every interface records its complete interior-volume depth, since its sparse
support alone does not reveal how far it was computed.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction
from itertools import product
from typing import Sequence

from .graph import Graph, _integer
from .heights import weak_compositions


def _patterns(graph: Graph, terminals: tuple[int, ...]) -> tuple[list[int], dict[int, tuple[int, ...]]]:
    edges = set(graph.edges)
    adjacent = lambda u, v: (min(u, v), max(u, v)) in edges
    interior = [v for v in range(graph.n) if v not in terminals]
    return interior, {v: tuple(int(adjacent(v, b)) for b in terminals) for v in interior}


def charge_interface(graph: Graph, terminals: Sequence[int], max_volume: int) -> dict:
    """The charge table {(j, Q): {energy: count}} through interior volume R, with boundary data.

    Computed by enumerating interior weak compositions (the interior is
    assumed small); ``kernel_from_charges`` rebuilds the terminal kernel.
    ``max_volume`` in the returned dictionary declares the complete prefix;
    depth-sensitive operations reject a request beyond that bound.
    """
    from .terminals import _check_terminals

    terminals = _check_terminals(graph, terminals)
    R = _integer(max_volume, "max_volume", minimum=0)
    interior, eta = _patterns(graph, terminals)
    position = {v: i for i, v in enumerate(interior)}
    inner = [(position[u], position[v]) for u, v in graph.edges if u in position and v in position]
    weight = [sum(eta[v]) for v in interior]
    table: defaultdict[tuple, Counter] = defaultdict(Counter)
    for j in range(R + 1):
        for h in weak_compositions(j, len(interior)):
            charge = tuple(sum(h[i] * eta[v][k] for i, v in enumerate(interior)) for k in range(len(terminals)))
            energy = sum((h[a] - h[b]) ** 2 for a, b in inner) + sum(w * x * x for w, x in zip(weight, h))
            table[j, charge][energy] += 1
    index = {b: k for k, b in enumerate(terminals)}
    return {"terminals": terminals,
            "max_volume": R,
            "terminal_degrees": tuple(sum(eta[v][k] for v in interior) for k in range(len(terminals))),
            "terminal_edges": tuple(sorted(tuple(sorted((index[u], index[v])))
                                           for u, v in graph.edges if u in index and v in index)),
            "patterns": sorted(set(eta.values())),
            "charges": {key: dict(sorted(c.items())) for key, c in sorted(table.items())}}


def _charge_depth(interface: dict, max_volume: int | None) -> int:
    """Require a declared complete prefix; sparse support cannot reveal its depth."""
    if "max_volume" not in interface:
        raise ValueError("charge interface needs max_volume completeness metadata; rebuild it with charge_interface")
    source = _integer(interface["max_volume"], "interface max_volume", minimum=0)
    requested = source if max_volume is None else _integer(max_volume, "max_volume", minimum=0)
    if requested > source:
        raise ValueError(f"requested volume {requested} exceeds charge interface depth {source}")
    return requested


def parallel_interfaces(first: dict, second: dict, max_volume: int | None = None) -> dict:
    """Glue independent interiors along the same ordered terminal labels.

    The caller supplies edge-disjoint blocks meeting only in their terminals;
    interiors are treated as disjoint copies, since their vertex identities
    have already been summed out.  Repeated terminal edges are rejected.
    The new charge polynomial is the product of the two charge polynomials,
    truncated in *interior* volume.  No terminal-height table is expanded.
    By default the result uses the smaller declared complete source depth.
    """
    if tuple(first["terminals"]) != tuple(second["terminals"]):
        raise ValueError("parallel interfaces require the same ordered terminal labels")
    depth = min(_charge_depth(first, None), _charge_depth(second, None))
    R = depth if max_volume is None else _integer(max_volume, "max_volume", minimum=0)
    _charge_depth(first, R)
    _charge_depth(second, R)
    edges1 = {tuple(sorted(e)) for e in first["terminal_edges"]}
    edges2 = {tuple(sorted(e)) for e in second["terminal_edges"]}
    if edges1 & edges2:
        raise ValueError("parallel blocks must not share an edge between terminals")
    table: defaultdict[tuple, Counter] = defaultdict(Counter)
    for (j1, Q1), cells1 in first["charges"].items():
        for (j2, Q2), cells2 in second["charges"].items():
            if j1 + j2 > R:
                continue
            row = table[j1 + j2, tuple(a + b for a, b in zip(Q1, Q2))]
            for e1, count1 in cells1.items():
                for e2, count2 in cells2.items():
                    row[e1 + e2] += count1 * count2
    return {"terminals": tuple(first["terminals"]), "max_volume": R,
            "terminal_degrees": tuple(a + b for a, b in zip(first["terminal_degrees"], second["terminal_degrees"])),
            "terminal_edges": tuple(sorted(edges1 | edges2)),
            "patterns": sorted({tuple(p) for p in first["patterns"] + second["patterns"]}),
            "charges": {key: dict(sorted(c.items())) for key, c in sorted(table.items())}}


def forget_terminal(interface: dict, terminal: int, max_volume: int | None = None) -> dict:
    """Turn the named terminal into an interior vertex, summing its height.

    If zeta records its edges to the retained terminals, a cell (j,Q,E)
    at forgotten height h becomes
        (j+h, Q_without_terminal+h*zeta,
         E+(d_terminal+sum(zeta))*h*h-2*h*Q_terminal).
    Here d_terminal counts its old interior neighbours.  Only h <= R-j
    is needed: interior volume never decreases, so prefix truncation is safe.
    Forgetting the last terminal is allowed and returns the closed series
    as the cells (j, ()).  Remaining terminal labels keep their original order.
    """
    R = _charge_depth(interface, max_volume)
    terminal = _integer(terminal, "terminal", minimum=0)
    terminals = tuple(interface["terminals"])
    if terminal not in terminals:
        raise ValueError("terminal is not among the interface terminal labels")
    t = terminals.index(terminal)
    retained = [i for i in range(len(terminals)) if i != t]
    edges = {tuple(sorted(e)) for e in interface["terminal_edges"]}
    zeta = tuple(int(tuple(sorted((t, i))) in edges) for i in retained)
    total_degree = interface["terminal_degrees"][t] + sum(zeta)
    table: defaultdict[tuple, Counter] = defaultdict(Counter)
    for (j, Q), cells in interface["charges"].items():
        for h in range(R + 1 - j):
            charge = tuple(Q[i] + h * adjacent for i, adjacent in zip(retained, zeta))
            shift = total_degree * h * h - 2 * h * Q[t]
            row = table[j + h, charge]
            for energy, count in cells.items():
                row[energy + shift] += count
    position = {old: new for new, old in enumerate(retained)}
    return {"terminals": tuple(terminals[i] for i in retained), "max_volume": R,
            "terminal_degrees": tuple(interface["terminal_degrees"][i] + adjacent for i, adjacent in zip(retained, zeta)),
            "terminal_edges": tuple(sorted((position[u], position[v]) for u, v in edges if t not in (u, v))),
            "patterns": sorted({tuple(p[i] for i in retained) for p in interface["patterns"]} | {zeta}),
            "charges": {key: dict(sorted(c.items())) for key, c in sorted(table.items())}}


def kernel_from_charges(interface: dict, max_volume: int) -> dict:
    """Terminal kernel {b: {(interior volume, energy): count}} through total volume R from the charge table."""
    R = _charge_depth(interface, max_volume)
    k = len(interface["terminals"])
    degrees, tedges = interface["terminal_degrees"], interface["terminal_edges"]
    out: defaultdict[tuple, Counter] = defaultdict(Counter)
    for b in product(range(R + 1), repeat=k):
        base = sum(b)
        if base > R:
            continue
        boundary = sum(d * x * x for d, x in zip(degrees, b)) + sum((b[u] - b[v]) ** 2 for u, v in tedges)
        for (j, charge), cells in interface["charges"].items():
            if base + j > R:
                continue
            shift = boundary - 2 * sum(x * c for x, c in zip(b, charge))
            for energy, count in cells.items():
                out[b][j, energy + shift] += count
    return {b: dict(sorted(c.items())) for b, c in sorted(out.items())}


def pattern_dimension(interface: dict) -> int:
    """Affine dimension of the neighbourhood patterns (charges of volume j fill j times their hull)."""
    pats = [tuple(Fraction(x) for x in p) for p in interface["patterns"]]
    if len(pats) <= 1:
        return 0
    rows = [[a - b for a, b in zip(p, pats[0])] for p in pats[1:]]
    rank = 0
    for col in range(len(rows[0])):
        pivot = next((i for i in range(rank, len(rows)) if rows[i][col]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(len(rows)):
            if i != rank and rows[i][col]:
                f = rows[i][col] / rows[rank][col]
                rows[i] = [x - f * y for x, y in zip(rows[i], rows[rank])]
        rank += 1
    return rank


def interface_sizes(interface: dict, max_volume: int) -> dict:
    """Number of charge cells (j, Q) against the raw table of (b, interior volume) with |b| + j <= R."""
    from math import comb

    R = _charge_depth(interface, max_volume)
    k = len(interface["terminals"])
    return {"charge_cells": sum(1 for j, _ in interface["charges"] if j <= R),
            "raw_kernel_cells": comb(R + k + 1, k + 1)}


def dominating_block(interior: Graph) -> tuple[Graph, tuple[int, int]]:
    """G_H: terminals 0, 1, nonadjacent, each joined to every vertex of H (relabelled 2..m+1)."""
    if not isinstance(interior, Graph):
        raise TypeError("interior must be a Graph")
    m = interior.n
    edges = [(u + 2, v + 2) for u, v in interior.edges] + [(t, v + 2) for t in (0, 1) for v in range(m)]
    return Graph(m + 2, edges), (0, 1)


def dominating_sequence(interior: Graph, max_volume: int) -> list[dict[int, int]]:
    """A_{H,j} = sum over |h| = j of q^(E_H(h) + 2 sum h_i^2), j = 0..R, as polynomials in q."""
    R = _integer(max_volume, "max_volume", minimum=0)
    out = []
    for j in range(R + 1):
        row: Counter = Counter()
        for h in weak_compositions(j, interior.n):
            row[interior.energy(h) + 2 * sum(x * x for x in h)] += 1
        out.append(dict(sorted(row.items())))
    return out


def _at(poly: dict, q: Fraction) -> Fraction:
    return sum((c * q ** e for e, c in poly.items()), Fraction(0))


def closure_operator(context: Graph, context_terminals: Sequence[int], m: int, max_volume: int, q) -> list[list[Fraction]]:
    """T_C at q0: (T_C)_{v,j} = sum over s+t+u = v-j of q0^(m(s^2+t^2) - 2j(s+t)) [x^u] K_C(s,t).

    Lower triangular with unit diagonal; independent of the interior graph.
    """
    from .terminals import terminal_kernel

    R, q0 = _integer(max_volume, "max_volume", minimum=0), Fraction(q)
    m = _integer(m, "m", minimum=0)
    if not 0 < q0:
        raise ValueError("q must be positive")
    kc = terminal_kernel(context, context_terminals, R)
    series = {b: [Fraction(0)] * (R + 1) for b in kc}
    for b, cells in kc.items():
        for (u, e), count in cells.items():
            series[b][u] += count * q0 ** e
    T = [[Fraction(0)] * (R + 1) for _ in range(R + 1)]
    for (s, t), ser in series.items():
        for j in range(R + 1 - s - t):
            factor = q0 ** (m * (s * s + t * t) - 2 * j * (s + t))
            for u in range(R + 1 - s - t - j):
                if ser[u]:
                    T[j + s + t + u][j] += factor * ser[u]
    assert all(T[v][v] == 1 for v in range(R + 1)), "closure operator must have unit diagonal"
    return T


def apply(T: list[list[Fraction]], A: Sequence) -> list[Fraction]:
    return [sum((T[v][j] * Fraction(A[j]) for j in range(v + 1)), Fraction(0)) for v in range(len(T))]


def recover_sequence(Z: Sequence, T: list[list[Fraction]]) -> list[Fraction]:
    """A from one closure Z = T A by forward substitution (unit diagonal)."""
    A: list[Fraction] = []
    for v in range(len(T)):
        A.append(Fraction(Z[v]) - sum((T[v][j] * A[j] for j in range(v)), Fraction(0)))
    return A


def transport(T_to: list[list[Fraction]], T_from: list[list[Fraction]]) -> list[list[Fraction]]:
    """U = T_to T_from^(-1): carries the closure series for one context to another, for every interior."""
    size = len(T_from)
    inverse = []
    for col in range(size):
        e = [Fraction(int(i == col)) for i in range(size)]
        inverse.append(recover_sequence(e, T_from))  # column col of T_from^(-1)
    return [[sum((T_to[i][k] * inverse[j][k] for k in range(size)), Fraction(0)) for j in range(size)] for i in range(size)]


def charge_chart(interface: dict, max_volume: int, coordinates: Sequence[int] | None = None) -> dict:
    """An ordered observation chart for the charge table (SNG-F62).

    For each slice j the distinct charges Q are projected to the terminal
    ``coordinates`` (by default the first coordinate set, in lexicographic
    order, of size equal to the pattern dimension on which every slice is
    injective).  The sample states are the projected charges, embedded with
    zeros elsewhere; the ordered kernel at those states determines the slice
    because the matrix q^(-2 v.w) on distinct points is positive definite.
    """
    from itertools import combinations as _comb

    R = _charge_depth(interface, max_volume)
    k = len(interface["terminals"])
    slices: dict[int, list] = {}
    for (j, Q) in interface["charges"]:
        if j <= R:
            slices.setdefault(j, []).append(Q)
    a = pattern_dimension(interface)
    candidates = [tuple(coordinates)] if coordinates is not None else [c for size in range(a, k + 1) for c in _comb(range(k), size)]
    for coords in candidates:
        if all(len({tuple(Q[i] for i in coords) for Q in qs}) == len(qs) for qs in slices.values()):
            states = {j: [tuple(Q[i] if i in coords else 0 for i in range(k)) for Q in sorted(qs)]
                      for j, qs in slices.items()}
            budget = max((sum(b) + j for j, bs in states.items() for b in bs), default=0)
            return {"coordinates": coords, "charges": {j: sorted(qs) for j, qs in slices.items()},
                    "states": states, "budget": budget}
    raise ValueError("no coordinate projection is injective on every slice")


def chart_observations(kernel: dict, chart: dict, q) -> dict[int, list[Fraction]]:
    """Read the chart's observations [x^j] K(b) at q0 from an ordered terminal kernel."""
    q0 = Fraction(q)
    out = {}
    for j, states in chart["states"].items():
        row = []
        for b in states:
            row.append(sum((c * q0 ** e for (v, e), c in kernel.get(b, {}).items() if v == j), Fraction(0)))
        out[j] = row
    return out


def chart_matrix(interface: dict, chart: dict, j: int, q) -> list[list[Fraction]]:
    """J_j: observations of slice j as a linear function of (A_{j,Q}(q0))_Q, prefactor included."""
    q0 = Fraction(q)
    degrees, tedges = interface["terminal_degrees"], interface["terminal_edges"]
    rows = []
    for b in chart["states"][j]:
        pre = sum(d * x * x for d, x in zip(degrees, b)) + sum((b[u] - b[v]) ** 2 for u, v in tedges)
        rows.append([q0 ** (pre - 2 * sum(x * c for x, c in zip(b, Q))) for Q in chart["charges"][j]])
    return rows


def _solve_square(M: list[list[Fraction]], y: Sequence[Fraction]) -> list[Fraction]:
    n = len(M)
    aug = [list(r) + [Fraction(v)] for r, v in zip(M, y)]
    for c in range(n):
        p = next(i for i in range(c, n) if aug[i][c])
        aug[c], aug[p] = aug[p], aug[c]
        inv = 1 / aug[c][c]
        aug[c] = [x * inv for x in aug[c]]
        for i in range(n):
            if i != c and aug[i][c]:
                f = aug[i][c]
                aug[i] = [x - f * z for x, z in zip(aug[i], aug[c])]
    return [aug[i][-1] for i in range(n)]


def recover_from_chart(interface: dict, chart: dict, observations: dict, q) -> dict[tuple, Fraction]:
    """(A_{j,Q}(q0)) from chart observations, slice by slice."""
    out = {}
    for j in sorted(chart["states"]):
        values = _solve_square(chart_matrix(interface, chart, j, q), observations[j])
        for Q, v in zip(chart["charges"][j], values):
            out[j, Q] = v
    return out


def chart_transport(interface: dict, chart_from: dict, chart_to: dict, j: int, q) -> list[list[Fraction]]:
    """U_j = J'_j J_j^(-1): carries slice-j observations in one complete chart to another."""
    J, Jp = chart_matrix(interface, chart_from, j, q), chart_matrix(interface, chart_to, j, q)
    n = len(J)
    inverse_columns = [_solve_square(J, [Fraction(int(i == c)) for i in range(n)]) for c in range(n)]
    return [[sum(Jp[r][k] * inverse_columns[c][k] for k in range(n)) for c in range(n)] for r in range(len(Jp))]
