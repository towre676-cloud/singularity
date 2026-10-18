"""Connected-support compiler for pinned height series (SNG-F55 to SNG-F57).

For a graph H and an integer shift lam >= 0 put w_v = deg_H(v) + lam and

    F_lam(H) = sum over h: V -> N of x^|h| q^(sum_v w_v h_v^2 - 2 sum_{uv in E} h_u h_v).

lam = 0 is the local series L_H; lam = 2 is the dominating-block interior
sequence A_H of SNG-F53(b).  With one variable x_v per vertex, Z_T is
F_lam with x_v = 0 outside T (ambient degrees kept), and

    Phi_S = sum_{T subset S} (-1)^(|S|-|T|) log Z_T

is the part of log F whose monomials use every vertex of S.  It vanishes
unless H[S] is connected, is O(x^|S|), and depends only on the
degree-decorated isomorphism type of H[S].  So log F modulo x^(R+1) is a
sum over connected sets of at most R vertices, and F is recovered by the
exact recursion n F_n = sum_r B_r F_(n-r), B_r = r [x^r] log F.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from itertools import permutations
from typing import Iterable, Sequence

from .graph import Graph, _integer
from .heights import weak_compositions
from .polynomials import add, mul, normalize, scale, series_log, sub

Series = list


def connected_sets(graph: Graph, max_size: int) -> Iterable[frozenset]:
    """Every vertex set inducing a connected subgraph with at most ``max_size`` vertices, once each.

    Each set is grown from its least vertex, adding only larger neighbours
    of the current set through an exclusion set (the standard extension
    scheme for connected induced subgraphs).
    """
    k = _integer(max_size, "max_size", minimum=0)
    neighbours = [set(graph.neighbors[v]) for v in range(graph.n)]

    def extend(current: frozenset, frontier: set, excluded: set, root: int):
        yield current
        if len(current) == k:
            return
        frontier = sorted(frontier)
        blocked = set(excluded)
        for i, v in enumerate(frontier):
            new_frontier = (set(frontier[i + 1:]) | {w for w in neighbours[v] if w > root and w not in current
                                                      and w not in blocked and w not in frontier}) - {v}
            yield from extend(current | {v}, new_frontier, blocked | set(frontier[: i + 1]), root)
            blocked.add(v)

    if k == 0:
        return
    for root in range(graph.n):
        yield from extend(frozenset({root}), {w for w in neighbours[root] if w > root}, set(), root)


def _type_key(graph: Graph, subset: frozenset, lam: int) -> tuple:
    """An exact isomorphism key for H[S] decorated by the weights w_v.

    Trees get the AHU encoding rooted at a centre (weights as labels).
    Other sets are canonized by brute force over orders that respect the
    refined classes (weight, internal degree) when that is cheap; otherwise
    the set itself is the key, which only forgoes sharing.
    """
    from math import factorial, prod

    verts = sorted(subset)
    weight = {v: len(graph.neighbors[v]) + lam for v in verts}
    inside = {v: [w for w in graph.neighbors[v] if w in subset] for v in verts}
    edge_count = sum(len(a) for a in inside.values()) // 2
    if edge_count == len(verts) - 1:
        leaves = [v for v in verts if len(inside[v]) <= 1]
        degree = {v: len(inside[v]) for v in verts}
        remaining = set(verts)
        while len(remaining) > 2:
            for leaf in leaves:
                remaining.discard(leaf)
            nxt = []
            for leaf in leaves:
                for w in inside[leaf]:
                    if w in remaining:
                        degree[w] -= 1
                        if degree[w] == 1:
                            nxt.append(w)
            leaves = nxt

        def encode(v, parent):
            return "(" + str(weight[v]) + "".join(sorted(encode(w, v) for w in inside[v] if w != parent)) + ")"

        return ("tree", min(encode(c, None) for c in remaining))
    classes: dict[tuple, list[int]] = {}
    for v in verts:
        classes.setdefault((weight[v], len(inside[v])), []).append(v)
    ordered = [classes[k] for k in sorted(classes)]
    if prod(factorial(len(c)) for c in ordered) > 40320:
        return ("set", tuple(verts))
    edges = set(graph.edges)
    best = None

    def orders(i):
        if i == len(ordered):
            yield []
            return
        for perm in permutations(ordered[i]):
            for rest in orders(i + 1):
                yield list(perm) + rest

    for order in orders(0):
        key = tuple(int((min(order[a], order[b]), max(order[a], order[b])) in edges)
                    for a in range(len(order)) for b in range(a + 1, len(order)))
        if best is None or key < best:
            best = key
    return ("graph", tuple(sorted(classes)), tuple(len(c) for c in ordered), best)


def _restricted_log(graph: Graph, subset: tuple, lam: int | None, R: int) -> Series:
    """log Z_T modulo x^(R+1), Z_T counted over heights supported in T.

    ``lam=None`` is moment mode: the energy uses the ambient degrees and the
    squared height S is carried in the key E (R^2 + 1) + S, which is
    additive and stays decodable because S <= R^2 through degree R.
    """
    moment = lam is None
    weight = [len(graph.neighbors[v]) + (0 if moment else lam) for v in subset]
    position = {v: i for i, v in enumerate(subset)}
    inner = [(position[u], position[v]) for u, v in graph.edges if u in position and v in position]
    base = R * R + 1
    rows: list[Counter] = [Counter() for _ in range(R + 1)]
    for volume in range(R + 1):
        for h in weak_compositions(volume, len(subset)):
            energy = sum(w * x * x for w, x in zip(weight, h)) - 2 * sum(h[a] * h[b] for a, b in inner)
            rows[volume][energy * base + sum(x * x for x in h) if moment else energy] += 1
    return series_log([dict(r) for r in rows], R)


def _components(graph: Graph, subset: tuple) -> list[tuple]:
    inside, seen, out = set(subset), set(), []
    for v in subset:
        if v in seen:
            continue
        comp, stack = [], [v]
        seen.add(v)
        while stack:
            u = stack.pop()
            comp.append(u)
            for w in graph.neighbors[u]:
                if w in inside and w not in seen:
                    seen.add(w)
                    stack.append(w)
        out.append(tuple(sorted(comp)))
    return out


def exact_support_log(graph: Graph, subset: frozenset, lam: int, max_volume: int, memo: dict | None = None) -> Series:
    """Phi_S modulo x^(R+1): the part of log F using every vertex of S (zero below x^|S|).

    log Z_T is additive over the components of H[T]; component logs are
    memoized by decorated type in ``memo``.
    """
    R = _integer(max_volume, "max_volume", minimum=0)
    memo = {} if memo is None else memo
    verts = sorted(subset)
    total: Series = [{} for _ in range(R + 1)]
    for mask in range(1, 1 << len(verts)):
        T = tuple(v for i, v in enumerate(verts) if mask >> i & 1)
        sign = -1 if (len(verts) - len(T)) % 2 else 1
        for comp in _components(graph, T):
            key = (_type_key(graph, frozenset(comp), lam or 0), R)
            if key not in memo:
                memo[key] = _restricted_log(graph, comp, lam, R)
            total = [add(a, scale(b, sign)) for a, b in zip(total, memo[key])]
    return total


def pinned_log(graph: Graph, max_volume: int, lam: int = 2, statistics: dict | None = None) -> Series:
    """log F_lam(H) modulo x^(R+1) as a sum of Phi_S over connected sets |S| <= R, memoized by type."""
    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    R = _integer(max_volume, "max_volume", minimum=0)
    lam = None if lam is None else _integer(lam, "lam", minimum=0)
    memo: dict[tuple, Series] = {}
    logs: dict = {}
    count: Counter = Counter()
    sets = 0
    for subset in connected_sets(graph, R):
        sets += 1
        key = _type_key(graph, subset, lam or 0)
        count[key] += 1
        if key not in memo:
            memo[key] = exact_support_log(graph, subset, lam, R, logs)
    total: Series = [{} for _ in range(R + 1)]
    for key, multiplicity in count.items():
        total = [add(a, scale(b, multiplicity)) for a, b in zip(total, memo[key])]
    if statistics is not None:
        statistics.update({"connected_sets": sets, "types": len(memo)})
    return [normalize(t) for t in total]


def series_from_log(log: Series) -> Series:
    """F from log F by n F_n = sum_{r=1}^n B_r F_(n-r), B_r = r [x^r] log F (exact division)."""
    R = len(log) - 1
    B = [scale(log[r], r) for r in range(R + 1)]
    F: Series = [{0: Fraction(1)}]
    for n in range(1, R + 1):
        total: dict = {}
        for r in range(1, n + 1):
            total = add(total, mul(B[r], F[n - r]))
        F.append(scale(total, Fraction(1, n)))
    return F


def pinned_series(graph: Graph, max_volume: int, lam: int = 2) -> Series:
    """F_lam(H) modulo x^(R+1) by the connected-support compiler."""
    return series_from_log(pinned_log(graph, max_volume, lam))


def pinned_series_by_enumeration(graph: Graph, max_volume: int, lam: int = 2) -> Series:
    """Independent oracle: every weak composition of every volume <= R."""
    R = _integer(max_volume, "max_volume", minimum=0)
    weight = [len(graph.neighbors[v]) + lam for v in range(graph.n)]
    rows = []
    for volume in range(R + 1):
        row: Counter = Counter()
        for h in weak_compositions(volume, graph.n):
            row[sum(w * x * x for w, x in zip(weight, h)) - 2 * sum(h[u] * h[v] for u, v in graph.edges)] += 1
        rows.append({e: Fraction(c) for e, c in sorted(row.items()) if c})
    return rows


def cycle(n: int) -> Graph:
    return Graph(n, [(i, (i + 1) % n) for i in range(n)])


def disjoint_union(*graphs: Graph) -> Graph:
    edges, offset = [], 0
    for g in graphs:
        edges += [(u + offset, v + offset) for u, v in g.edges]
        offset += g.n
    return Graph(offset, edges)


def kappa(lam: int = 2, degree: int = 2) -> dict[int, Fraction]:
    """Per-edge cycle factor q^(d + lam - 2) (1 - q^2) of SNG-F56 as a polynomial (d = degree)."""
    return normalize({degree + lam - 2: 1, degree + lam: -1})


def cycle_log_difference(max_volume: int, lam: int = 2) -> tuple[Series, dict[int, Series]]:
    """b and D_l = log F(C_l) - l b modulo x^(R+1) for 2-regular graphs (SNG-F57).

    b = sum_k phi_k with phi_k the exact-support log of a k-vertex path whose
    vertices have ambient degree 2; D_l = O(x^l) with leading coefficient
    kappa^l.  D_l vanishes modulo x^(R+1) for l > R.
    """
    R = _integer(max_volume, "max_volume", minimum=0)
    big = cycle(2 * R + 3)  # paths of at most R vertices inside a long cycle carry ambient degree 2
    b: Series = [{} for _ in range(R + 1)]
    memo: dict = {}
    for k in range(1, R + 1):
        phi = exact_support_log(big, frozenset(range(k)), lam, R, memo)
        b = [add(x, y) for x, y in zip(b, phi)]
    D = {}
    for ell in range(3, R + 1):
        log = pinned_log(cycle(ell), R, lam)
        D[ell] = [normalize(sub(x, scale(y, ell))) for x, y in zip(log, b)]
    return b, D


def reconstruct_cycle_type(log: Series, n: int, max_volume: int, lam: int = 2, q=Fraction(1, 2),
                           tables: tuple | None = None) -> dict[int, int]:
    """Cycle counts of a 2-regular graph on n vertices from log F modulo x^(R+1) (SNG-F57).

    Recovers c_l for l <= R triangularly at q0, then, when the remaining
    vertices cannot form two longer cycles (n - sum l c_l <= 2R + 1),
    the last cycle.  Raises if the data are inconsistent with a 2-regular graph.
    """
    R = _integer(max_volume, "max_volume", minimum=0)
    n = _integer(n, "n", minimum=0)
    q0 = Fraction(q)
    b, D = tables if tables is not None else cycle_log_difference(R, lam)
    at = lambda poly: sum((c * q0 ** e for e, c in poly.items()), Fraction(0))
    residual = [at(x) - n * at(y) for x, y in zip(log, b)]
    k0 = at(kappa(lam))
    counts: dict[int, int] = {}
    for ell in range(3, R + 1):
        value = residual[ell] / k0 ** ell
        if value.denominator != 1 or value < 0:
            raise ArithmeticError(f"non-integral cycle count at length {ell}")
        counts[ell] = int(value)
        if counts[ell]:
            residual = [r - counts[ell] * at(d) for r, d in zip(residual, D[ell])]
    if any(residual[1:]):
        raise ArithmeticError("residual does not vanish: not a 2-regular graph with these data")
    rest = n - sum(ell * c for ell, c in counts.items())
    if rest < 0:
        raise ArithmeticError("cycle counts exceed the vertex count")
    if rest:
        if rest <= R:
            raise ArithmeticError("leftover vertices too few for a cycle longer than R")
        if rest > 2 * R + 1:
            raise ArithmeticError(f"{rest} leftover vertices: budget {R} cannot split them")
        counts[rest] = counts.get(rest, 0) + 1
    return {ell: c for ell, c in sorted(counts.items()) if c}


def moment_series(graph: Graph, max_volume: int) -> list[dict[tuple[int, int], Fraction]]:
    """P_H(x, u, q) modulo x^(R+1) by the compiler: [x^j] as {(S, E): count}, S = sum h^2 (SNG-F58).

    F_lam is the specialization u = q^lam: [x^j] F_lam = sum C_{j,S,E} q^(E + lam S).
    """
    R = _integer(max_volume, "max_volume", minimum=0)
    base = R * R + 1
    encoded = series_from_log(pinned_log(graph, R, None))
    return [{(k % base, k // base): c for k, c in sorted(row.items())} for row in encoded]


def moment_series_by_enumeration(graph: Graph, max_volume: int) -> list[dict[tuple[int, int], Fraction]]:
    R = _integer(max_volume, "max_volume", minimum=0)
    rows = []
    for volume in range(R + 1):
        row: Counter = Counter()
        for h in weak_compositions(volume, graph.n):
            row[sum(x * x for x in h), graph.energy(h)] += 1
        rows.append({k: Fraction(c) for k, c in sorted(row.items())})
    return rows


def specialize_moments(moments: list, lam: int) -> Series:
    """F_lam from P_H: substitute u = q^lam."""
    out = []
    for row in moments:
        poly: Counter = Counter()
        for (S, E), c in row.items():
            poly[E + lam * S] += c
        out.append(normalize(dict(poly)))
    return out


def moments_from_pinnings(values: dict[int, Sequence], max_volume: int, q) -> list[dict[int, Fraction]]:
    """Recover C_{j,S}(q0) from F_lam(q0) for C(R,2) + 1 distinct pinnings lam (SNG-F58(b)).

    ``values[lam][j]`` is [x^j] F_lam at q0.  With S = j + 2k,
    q0^(-lam j) [x^j] F_lam = sum_k C_{j,j+2k} (q0^(2 lam))^k, a Vandermonde system.
    """
    R, q0 = _integer(max_volume, "max_volume", minimum=0), Fraction(q)
    lams = sorted(values)
    out = []
    for j in range(R + 1):
        size = j * (j - 1) // 2 + 1
        if len(lams) < size:
            raise ValueError(f"volume {j} needs {size} distinct pinnings")
        use = lams[:size]
        rows = [[(q0 ** (2 * lam)) ** k for k in range(size)] + [Fraction(values[lam][j]) / q0 ** (lam * j)] for lam in use]
        for c in range(size):
            p = next(i for i in range(c, size) if rows[i][c])
            rows[c], rows[p] = rows[p], rows[c]
            inv = 1 / rows[c][c]
            rows[c] = [x * inv for x in rows[c]]
            for i in range(size):
                if i != c and rows[i][c]:
                    f = rows[i][c]
                    rows[i] = [x - f * y for x, y in zip(rows[i], rows[c])]
        out.append({j + 2 * k: rows[k][-1] for k in range(size) if rows[k][-1]})
    return out
