"""Terminal kernels, two-terminal gluing and the Whitney twist (SNG-F41).

A block is a graph G with an ordered tuple of distinct terminal vertices.
Its kernel records, for every terminal height vector b, the interior
population:

    K_G(b) = sum over interior heights a_I >= 0 of x^(sum a_I) q^(E_G(a_I, b)),

stored as {b: {(interior volume, energy): count}} through a volume budget
that includes |b|.  If two blocks share no edge and meet only in their
terminals, identified in order, the glued graph has

    L = sum_b x^|b| K_1(b) K_2(b).

For two terminals the Whitney twist identifies them in the opposite order,
and with A_i(b) = (K_i(s,t) - K_i(t,s))/2,

    L_glued - L_twisted = 2 sum_b x^|b| A_1(b) A_2(b).

Kernels are computed on a checked tree decomposition in which every bag
holds the terminals (non-terminals eliminated first by minimum degree); an
independent enumeration over weak compositions is the oracle.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Sequence

from .decomposition import _box, check_decomposition, elimination_decomposition
from .graph import Graph, _integer
from .heights import weak_compositions

Kernel = dict[tuple[int, ...], dict[tuple[int, int], int]]


def _check_terminals(graph: Graph, terminals: Sequence[int]) -> tuple[int, ...]:
    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    terminals = tuple(_integer(v, "terminal", minimum=0) for v in terminals)
    if not terminals or len(set(terminals)) != len(terminals) or max(terminals) >= graph.n:
        raise ValueError("terminals must be distinct vertices of the graph")
    return terminals


def kernel_by_enumeration(graph: Graph, terminals: Sequence[int], max_volume: int) -> Kernel:
    """Oracle: group every profile of volume <= R by its terminal heights."""
    terminals = _check_terminals(graph, terminals)
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    out: defaultdict[tuple[int, ...], Counter] = defaultdict(Counter)
    for volume in range(max_volume + 1):
        for a in weak_compositions(volume, graph.n):
            b = tuple(a[v] for v in terminals)
            out[b][volume - sum(b), graph.energy(a)] += 1
    return {b: dict(sorted(c.items())) for b, c in sorted(out.items())}


def terminal_kernel(graph: Graph, terminals: Sequence[int], max_volume: int, height: int | None = None) -> Kernel:
    """Kernel via bag messages with the terminals in every bag (SNG-F26).

    ``height`` restricts every vertex, terminals included, to 0..H (a box
    kernel, used for span recovery after gluing); by default H = max_volume,
    which by SNG-F24 imposes no restriction through that volume.
    """
    terminals = _check_terminals(graph, terminals)
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    height = max_volume if height is None else _integer(height, "height", minimum=0)
    rest = [v for v in range(graph.n) if v not in terminals]
    # Greedy min-degree order on non-terminals, terminals eliminated last.
    remaining = {v: set(graph.neighbors[v]) for v in range(graph.n)}
    order = []
    while len(order) < len(rest):
        v = min((u for u in remaining if u not in terminals), key=lambda u: (len(remaining[u]), u))
        neighbours = remaining.pop(v)
        for a in neighbours:
            remaining[a] |= neighbours - {a}
            remaining[a].discard(v)
        order.append(v)
    order += list(terminals)
    base = elimination_decomposition(graph, order)
    # Adding every terminal to every bag keeps the axioms (each terminal's
    # bags are then the whole tree) and puts all terminals in the root bag.
    from .decomposition import TreeDecomposition
    decomposition = TreeDecomposition([sorted(set(b) | set(terminals)) for b in base.bags], base.edges, base.root)
    root = decomposition.root
    errors = check_decomposition(graph, decomposition)
    if errors:
        raise ArithmeticError("terminal decomposition invalid: " + "; ".join(errors))
    root_bag = decomposition.bags[root]
    message: dict = {}
    _box(graph, decomposition, height, max_volume, None, root_message=message)
    position = {v: i for i, v in enumerate(root_bag)}
    out: defaultdict[tuple[int, ...], Counter] = defaultdict(Counter)
    for assignment, histogram in message.items():
        b = tuple(assignment[position[v]] for v in terminals)
        for (volume, energy), count in histogram.items():
            out[b][volume - sum(b), energy] += count
    return {b: dict(sorted(c.items())) for b, c in sorted(out.items()) if c}


def glue(first: Kernel, second: Kernel, max_volume: int, permutation: Sequence[int] | None = None) -> list[dict[int, int]]:
    """Local coefficients of the glued graph through max_volume.

    Terminal i of the first block is identified with terminal
    permutation[i] of the second (identity by default).
    """
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    rows: list[Counter[int]] = [Counter() for _ in range(max_volume + 1)]
    for b, k1 in first.items():
        b2 = b if permutation is None else tuple(b[permutation.index(j)] for j in range(len(b)))
        k2 = second.get(b2, {})
        base = sum(b)
        for (v1, e1), c1 in k1.items():
            for (v2, e2), c2 in k2.items():
                volume = base + v1 + v2
                if volume <= max_volume:
                    rows[volume][e1 + e2] += c1 * c2
    return [dict(sorted((e, c) for e, c in r.items() if c)) for r in rows]


def glue_graphs(first: Graph, first_terminals: Sequence[int], second: Graph, second_terminals: Sequence[int]) -> tuple[Graph, dict]:
    """The glued graph: first's labels kept, second's interior appended after them.

    second_terminals[i] is identified with first_terminals[i].  Shared edges
    between identified terminals are rejected (the blocks must be edge-disjoint).
    """
    t1, t2 = _check_terminals(first, first_terminals), _check_terminals(second, second_terminals)
    if len(t1) != len(t2):
        raise ValueError("terminal tuples must have equal length")
    mapping = {t2[i]: t1[i] for i in range(len(t2))}
    nxt = first.n
    for v in range(second.n):
        if v not in mapping:
            mapping[v] = nxt
            nxt += 1
    edges = set(first.edges)
    for u, v in second.edges:
        e = tuple(sorted((mapping[u], mapping[v])))
        if e in edges:
            raise ValueError("blocks share an edge between terminals; they must be edge-disjoint")
        edges.add(e)
    return Graph(nxt, sorted(edges)), mapping


def antisymmetric_part(kernel: Kernel) -> dict[tuple[int, int], dict[tuple[int, int], int]]:
    """2 A(b) = K(s, t) - K(t, s) for a two-terminal kernel (kept doubled: integers)."""
    out = {}
    for (s, t), k in kernel.items():
        other = kernel.get((t, s), {})
        diff = Counter(k)
        diff.subtract(other)
        diff = {key: c for key, c in diff.items() if c}
        if diff:
            out[s, t] = dict(sorted(diff.items()))
    return out


def twist_difference(first: Kernel, second: Kernel, max_volume: int) -> list[dict[int, int]]:
    """2 sum_b x^|b| A_1(b) A_2(b) = (1/2) sum_b x^|b| (2A_1)(2A_2), as coefficients."""
    a1, a2 = antisymmetric_part(first), antisymmetric_part(second)
    rows: list[Counter[int]] = [Counter() for _ in range(max_volume + 1)]
    for b, d1 in a1.items():
        d2 = a2.get(b, {})
        for (v1, e1), c1 in d1.items():
            for (v2, e2), c2 in d2.items():
                volume = sum(b) + v1 + v2
                if volume <= max_volume:
                    rows[volume][e1 + e2] += c1 * c2
    out = []
    for r in rows:
        row = {}
        for e, c in r.items():
            if c % 2:
                raise ArithmeticError("antisymmetric pairing is not an even integer")
            if c:
                row[e] = c // 2
        out.append(dict(sorted(row.items())))
    return out


def marked_glue(first: Graph, first_terminals: Sequence[int], second: Graph, second_terminals: Sequence[int],
                max_volume: int) -> dict[tuple[int, int, int], int]:
    """(volume, energy, span) counts of the glued graph from box kernels (SNG-F43).

    For each H the glued box histogram C_H is assembled from the blocks' box
    kernels; D_H = C_H - x^n C_{H-1} and D_H - D_{H-1} give exact span H, as in
    SNG-F25.  Negative differences raise instead of being clipped.
    """
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    t1, t2 = _check_terminals(first, first_terminals), _check_terminals(second, second_terminals)
    n = first.n + second.n - len(t1)

    def box(h: int, budget: int) -> Counter:
        if h < 0 or budget < 0:
            return Counter()
        rows = glue(terminal_kernel(first, t1, budget, h), terminal_kernel(second, t2, budget, h), budget)
        return Counter({(v, e): c for v, row in enumerate(rows) for e, c in row.items()})

    def min_zero(h: int) -> Counter:
        out = box(h, max_volume)
        for (v, e), c in box(h - 1, max_volume - n).items():
            out[v + n, e] -= c
        return out

    result: dict[tuple[int, int, int], int] = {}
    previous: Counter = Counter()
    for span in range(max_volume + 1):
        current = min_zero(span)
        for key in set(current) | set(previous):
            count = current.get(key, 0) - previous.get(key, 0)
            if count < 0:
                raise ArithmeticError(f"negative exact-span count at span {span}, cell {key}")
            if count:
                result[key[0], key[1], span] = count
        previous = current
    return dict(sorted(result.items()))
