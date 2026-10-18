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
            "terminal_degrees": tuple(sum(eta[v][k] for v in interior) for k in range(len(terminals))),
            "terminal_edges": tuple((index[u], index[v]) for u, v in graph.edges if u in index and v in index),
            "patterns": sorted(set(eta.values())),
            "charges": {key: dict(sorted(c.items())) for key, c in sorted(table.items())}}


def kernel_from_charges(interface: dict, max_volume: int) -> dict:
    """Terminal kernel {b: {(interior volume, energy): count}} through total volume R from the charge table."""
    R = _integer(max_volume, "max_volume", minimum=0)
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

    R = _integer(max_volume, "max_volume", minimum=0)
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
