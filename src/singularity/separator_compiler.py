"""Charge-aware separator compiler (OE11).

An interface on an ordered boundary T is the compressed charge table of
``charges.py``: integer counts n_{j,Q,E} over interior height assignments
of interior volume j, boundary charge Q and interior-side energy E, plus
terminal metadata (interior degrees d_i and terminal-terminal edges).  The
compiler uses three exact operations:

* ``introduce_terminal`` (new here): add a boundary vertex with declared
  edges to existing boundary vertices; the interior is unchanged;
* ``charges.forget_terminal``: a boundary vertex becomes interior;
* ``charges.parallel_interfaces``: join blocks on one ordered boundary with
  disjoint interiors and edge-disjoint terminal graphs.

``compile_graph`` drives them along a vertex order (introduce each vertex,
forget a vertex as soon as all its neighbours have been introduced);
``compile_decomposition`` drives them along a checked tree decomposition,
with join nodes.  When the boundary is empty the cells (j, ()) are the
coefficients [x^j] L_G(x, q), j <= R.  ``build_step_operator`` and
``apply_step_operator`` compile one stationary segment of a schedule into a
reusable linear map on charge cells (periodic strips).

Proofs, the width/cell bound and the bit bound are in
docs/research/SEPARATOR_COMPILER.md.  Only exact integers are used.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Callable, Iterable, Sequence

from .charges import _charge_depth, forget_terminal, parallel_interfaces
from .decomposition import TreeDecomposition, _rooted, charge_owners, check_decomposition
from .graph import Graph, _integer

_KEYS = ("terminals", "max_volume", "terminal_degrees", "terminal_edges", "patterns", "charges")


# ---------------------------------------------------------------------------
# validation helpers


def _check_graph(graph: object) -> Graph:
    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    return graph


def _check_interface(interface: object) -> dict:
    if not isinstance(interface, dict):
        raise TypeError("interface must be a charge-interface dictionary")
    missing = [key for key in _KEYS if key not in interface]
    if missing:
        raise ValueError(f"charge interface lacks {', '.join(missing)}")
    _charge_depth(interface, None)
    return interface


def _labels(values: object, name: str) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError(f"{name} must be a sequence of integers")
    return tuple(_integer(v, name, minimum=0) for v in values)


def _order(graph: Graph, order: object) -> tuple[int, ...]:
    order = _labels(order, "order entry")
    if sorted(order) != list(range(graph.n)):
        raise ValueError("order must be a permutation of the vertices 0..n-1")
    return order


def _finish(table: dict) -> dict:
    return {key: dict(sorted(cells.items())) for key, cells in sorted(table.items())}


# ---------------------------------------------------------------------------
# the new primitive and trivial interfaces


def empty_interface(max_volume: int) -> dict:
    """The interface of the empty block: no boundary, one cell (0, ()) with energy 0."""
    R = _integer(max_volume, "max_volume", minimum=0)
    return {"terminals": (), "max_volume": R, "terminal_degrees": (), "terminal_edges": (),
            "patterns": [], "charges": {(0, ()): {0: 1}}}


def introduce_terminal(interface: dict, vertex: int, neighbours: Sequence[int] = (),
                       position: int | None = None) -> dict:
    """Add boundary vertex ``vertex`` joined to the named existing boundary vertices.

    The new vertex has no interior neighbour, so every interior pattern gets
    a 0 in its coordinate and every cell (j, Q, E) becomes (j, Q with 0
    inserted, E); its terminal degree is 0 and its edges join the
    terminal-edge graph.  ``position`` (default: last) places it in the
    ordered boundary; later terminal indices shift by one.  The caller
    guarantees that ``vertex`` is not already an interior vertex of the block
    (the table has summed interior identities out).  The depth is unchanged.
    """
    _check_interface(interface)
    R = _charge_depth(interface, None)
    vertex = _integer(vertex, "vertex", minimum=0)
    terminals = tuple(interface["terminals"])
    if vertex in terminals:
        raise ValueError("vertex is already a boundary vertex")
    nbrs = _labels(neighbours, "neighbour")
    if len(set(nbrs)) != len(nbrs):
        raise ValueError("neighbours repeat")
    if any(u not in terminals for u in nbrs):
        raise ValueError("neighbours must be existing boundary vertices")
    k = len(terminals)
    p = k if position is None else _integer(position, "position", minimum=0)
    if p > k:
        raise ValueError("position exceeds the boundary size")
    shift = lambda i: i if i < p else i + 1  # noqa: E731
    edges = {tuple(sorted((shift(a), shift(b)))) for a, b in interface["terminal_edges"]}
    edges |= {tuple(sorted((p, shift(terminals.index(u))))) for u in nbrs}
    degrees = tuple(interface["terminal_degrees"])
    charges = {(j, tuple(Q[:p]) + (0,) + tuple(Q[p:])): dict(cells) for (j, Q), cells in interface["charges"].items()}
    return {"terminals": terminals[:p] + (vertex,) + terminals[p:], "max_volume": R,
            "terminal_degrees": degrees[:p] + (0,) + degrees[p:],
            "terminal_edges": tuple(sorted(edges)),
            "patterns": sorted({tuple(q[:p]) + (0,) + tuple(q[p:]) for q in interface["patterns"]}),
            "charges": _finish(charges)}


def boundary_block(terminals: Sequence[int], edges: Iterable[Sequence[int]], max_volume: int) -> dict:
    """Interior-free interface on ordered ``terminals`` carrying the given edges among them."""
    terminals = _labels(terminals, "terminal")
    if len(set(terminals)) != len(terminals):
        raise ValueError("terminals repeat")
    pending = defaultdict(list)
    seen = set()
    rank = {v: i for i, v in enumerate(terminals)}
    for edge in edges:
        u, v = _labels(edge, "edge endpoint")
        if u not in rank or v not in rank or u == v:
            raise ValueError("edges must join two distinct listed terminals")
        if frozenset((u, v)) in seen:
            raise ValueError("edges repeat")
        seen.add(frozenset((u, v)))
        later, earlier = (u, v) if rank[u] > rank[v] else (v, u)
        pending[later].append(earlier)
    out = empty_interface(max_volume)
    for v in terminals:
        out = introduce_terminal(out, v, sorted(pending[v], key=rank.__getitem__))
    return out


def closed_coefficients(interface: dict, max_volume: int | None = None) -> list[dict[int, int]]:
    """Query: [x^j] of a closed (empty-boundary) interface as integer q-polynomials, j <= R."""
    _check_interface(interface)
    if tuple(interface["terminals"]):
        raise ValueError("interface still has boundary vertices; forget them first")
    R = _charge_depth(interface, max_volume)
    return [dict(sorted(interface["charges"].get((j, ()), {}).items())) for j in range(R + 1)]


# ---------------------------------------------------------------------------
# measurements and the proved bounds


def interface_statistics(interface: dict) -> dict[str, int]:
    """Charge keys (j,Q), nonzero cells (j,Q,E), count bits, charge and energy range."""
    charges = interface["charges"]
    counts = [c for cells in charges.values() for c in cells.values()]
    energies = [e for cells in charges.values() for e in cells]
    return {"boundary": len(interface["terminals"]),
            "charge_keys": len(charges),
            "cells": len(counts),
            "max_count_bits": max((c.bit_length() for c in counts), default=0),
            "max_charge": max((x for _, Q in charges for x in Q), default=0),
            "min_energy": min(energies, default=0),
            "max_energy": max(energies, default=0)}


def cell_bound(active_terminals: int, max_volume: int, max_degree: int) -> int:
    """Theorem (cell bound): nonzero cells <= sum_{j<=R} (j+1)^k (D j^2 + 1).

    k counts boundary vertices with an interior neighbour (the others have
    charge 0) and D bounds every vertex degree of the represented graph.
    """
    k = _integer(active_terminals, "active_terminals", minimum=0)
    R = _integer(max_volume, "max_volume", minimum=0)
    D = _integer(max_degree, "max_degree", minimum=0)
    return sum((j + 1) ** k * (D * j * j + 1) for j in range(R + 1))


def count_bit_bound(interior_size: int, max_volume: int) -> int:
    """Theorem (bit bound): n_{j,Q,E} <= C(m+j-1, j) <= m^j, so bits <= bit length of C(m+R-1, R)."""
    from math import comb

    m = _integer(interior_size, "interior_size", minimum=0)
    R = _integer(max_volume, "max_volume", minimum=0)
    if m == 0:
        return 1
    return comb(m + R - 1, R).bit_length()


# ---------------------------------------------------------------------------
# elimination-order driver


def elimination_schedule(graph: Graph, order: Sequence[int]) -> list[tuple]:
    """Operations ("introduce", v, neighbours) / ("forget", v) for a vertex order.

    Vertex v is introduced with its edges to boundary vertices; immediately
    afterwards every boundary vertex all of whose neighbours are introduced
    is forgotten, in introduction order.  At the end the boundary is empty.
    """
    graph = _check_graph(graph)
    order = _order(graph, order)
    introduced: set[int] = set()
    boundary: list[int] = []
    ops: list[tuple] = []
    for v in order:
        nbrs = tuple(u for u in boundary if u in graph.neighbors[v])
        if any(u in introduced and u not in boundary for u in graph.neighbors[v]):
            raise AssertionError("a forgotten vertex has an unintroduced neighbour")  # impossible by construction
        ops.append(("introduce", v, nbrs))
        introduced.add(v)
        boundary.append(v)
        for u in list(boundary):
            if all(w in introduced for w in graph.neighbors[u]):
                ops.append(("forget", u))
                boundary.remove(u)
    return ops


def schedule_width(schedule: Sequence[tuple]) -> int:
    """Maximum boundary size along a schedule (attained right after an introduction)."""
    size = width = 0
    for op in schedule:
        size += 1 if op[0] == "introduce" else -1
        width = max(width, size)
    return width


def order_width(graph: Graph, order: Sequence[int]) -> int:
    return schedule_width(elimination_schedule(graph, order))


def run_schedule(interface: dict, schedule: Sequence[tuple], observe: Callable[[dict], None] | None = None) -> dict:
    """Apply introduce/forget operations to an interface, optionally observing each result."""
    for op in schedule:
        if op[0] == "introduce":
            interface = introduce_terminal(interface, op[1], op[2])
        elif op[0] == "forget":
            interface = forget_terminal(interface, op[1])
        else:
            raise ValueError(f"unknown schedule operation {op[0]!r}")
        if observe is not None:
            observe(interface)
    return interface


def _observer(statistics: dict | None, max_degree: int):
    if statistics is None:
        return None
    statistics.update({"width": 0, "operations": 0, "max_cells": 0, "max_charge_keys": 0, "max_count_bits": 0,
                       "max_charge": 0, "min_energy": 0, "max_energy": 0, "cells_at_widest": 0,
                       "cell_bound_at_widest": 0, "bound_violations": 0, "total_cells": 0})

    def observe(interface: dict) -> None:
        s = interface_statistics(interface)
        statistics["operations"] += 1
        statistics["total_cells"] += s["cells"]
        active = sum(1 for d in interface["terminal_degrees"] if d)
        if s["cells"] > cell_bound(active, interface["max_volume"], max_degree):
            statistics["bound_violations"] += 1
        if s["boundary"] > statistics["width"] or (s["boundary"] == statistics["width"]
                                                    and s["cells"] > statistics["cells_at_widest"]):
            statistics["width"] = s["boundary"]
            statistics["cells_at_widest"] = s["cells"]
            statistics["cell_bound_at_widest"] = cell_bound(active, interface["max_volume"], max_degree)
        statistics["max_cells"] = max(statistics["max_cells"], s["cells"])
        statistics["max_charge_keys"] = max(statistics["max_charge_keys"], s["charge_keys"])
        statistics["max_count_bits"] = max(statistics["max_count_bits"], s["max_count_bits"])
        statistics["max_charge"] = max(statistics["max_charge"], s["max_charge"])
        statistics["min_energy"] = min(statistics["min_energy"], s["min_energy"])
        statistics["max_energy"] = max(statistics["max_energy"], s["max_energy"])
    return observe


def compile_interface(graph: Graph, order: Sequence[int], max_volume: int, statistics: dict | None = None) -> dict:
    """The closed interface of ``graph`` through volume R along a vertex order.

    ``statistics`` (a dict, filled in place) receives width, peak cells and
    charge keys, bit length, charge and energy ranges, and the cell bound
    at the widest step; ``bound_violations`` must stay 0 by the theorem.
    """
    graph = _check_graph(graph)
    R = _integer(max_volume, "max_volume", minimum=0)
    schedule = elimination_schedule(graph, order)
    observe = _observer(statistics, max(graph.degrees, default=0))
    return run_schedule(empty_interface(R), schedule, observe)


def compile_graph(graph: Graph, order: Sequence[int], max_volume: int, statistics: dict | None = None) -> list[dict[int, int]]:
    """[x^j] L_G(x, q) for j <= R as integer q-polynomials, by separator compilation."""
    return closed_coefficients(compile_interface(graph, order, max_volume, statistics))


# ---------------------------------------------------------------------------
# tree-decomposition driver with join nodes


def compile_decomposition(graph: Graph, decomposition: TreeDecomposition, max_volume: int,
                          statistics: dict | None = None) -> list[dict[int, int]]:
    """[x^j] L_G for j <= R along a checked tree decomposition, with joins.

    Each edge is charged at its owning (top) bag (``decomposition.charge_owners``).
    At a node with bag X every child interface forgets its vertices outside
    X, introduces the missing vertices of X without edges (boundary kept in
    increasing label order) and all children are joined, together with the
    interior-free block of the edges owned at X.  The root forgets X.
    """
    graph = _check_graph(graph)
    if not isinstance(decomposition, TreeDecomposition):
        raise TypeError("decomposition must be a TreeDecomposition")
    R = _integer(max_volume, "max_volume", minimum=0)
    errors = check_decomposition(graph, decomposition)
    if errors:
        raise ValueError("invalid tree decomposition: " + "; ".join(errors))
    order, parent = _rooted(decomposition)
    _, edge_owner = charge_owners(graph, decomposition)
    owned = defaultdict(list)
    for edge, node in edge_owner.items():
        owned[node].append(edge)
    children = defaultdict(list)
    for node in order[1:]:
        children[parent[node]].append(node)
    observe = _observer(statistics, max(graph.degrees, default=0))
    note = observe if observe is not None else (lambda interface: None)
    joins = 0
    done: dict[int, dict] = {}
    for node in reversed(order):
        bag = sorted(decomposition.bags[node])
        blocks = [boundary_block(bag, owned[node], R)]
        for child in sorted(children[node]):
            block = done.pop(child)
            for v in [t for t in block["terminals"] if t not in bag]:
                block = forget_terminal(block, v)
                note(block)
            for v in bag:
                if v not in block["terminals"]:
                    block = introduce_terminal(block, v, (), position=sorted(block["terminals"] + (v,)).index(v))
                    note(block)
            blocks.append(block)
        current = blocks[0]
        for block in blocks[1:]:
            current = parallel_interfaces(current, block)
            joins += 1
            note(current)
        note(current)
        done[node] = current
    closed = done[decomposition.root]
    for v in list(closed["terminals"]):
        closed = forget_terminal(closed, v)
        note(closed)
    if statistics is not None:
        statistics["joins"] = joins
    return closed_coefficients(closed)


# ---------------------------------------------------------------------------
# reusable step operators for stationary schedule segments


def _same_metadata(a: dict, b: dict) -> bool:
    return (len(a["terminals"]) == len(b["terminals"]) and tuple(a["terminal_degrees"]) == tuple(b["terminal_degrees"])
            and {tuple(e) for e in a["terminal_edges"]} == {tuple(e) for e in b["terminal_edges"]})


def build_step_operator(template: dict, segment: Sequence[tuple], seeds: Iterable[tuple] | None = None) -> dict:
    """Compile a schedule segment into a linear map on charge keys.

    ``template`` supplies the boundary labels and metadata the segment
    starts from; the segment's result must have the same boundary size,
    terminal degrees and terminal-edge indices (a stationary step), else
    ValueError.  Every operation is linear in the cell vector and commutes
    with multiplication by q, so the map is determined by its rows
    (j, Q) -> {(j', Q'): {energy shift: count}}, computed on unit cells.
    Rows are built for every key reachable from ``seeds`` (default: the
    template's own keys).  Shifts can be negative; actual energies are not.
    """
    _check_interface(template)
    R = _charge_depth(template, None)
    base = {key: template[key] for key in _KEYS if key != "charges"}
    rows: dict[tuple, dict] = {}
    frontier = list(template["charges"] if seeds is None else seeds)
    out_terminals = None
    while frontier:
        key = frontier.pop()
        if key in rows:
            continue
        unit = dict(base, charges={key: {0: 1}})
        image = run_schedule(unit, segment)
        if not _same_metadata(image, template):
            raise ValueError("segment is not stationary on this template")
        out_terminals = tuple(image["terminals"])
        rows[key] = image["charges"]
        frontier.extend(k for k in image["charges"] if k not in rows)
    return {"max_volume": R, "terminal_degrees": tuple(template["terminal_degrees"]),
            "terminal_edges": tuple(sorted(tuple(e) for e in template["terminal_edges"])),
            "input_terminals": tuple(template["terminals"]), "output_terminals": out_terminals,
            "segment": tuple(segment), "rows": rows}


def operator_size(operator: dict) -> dict[str, int]:
    rows = operator["rows"]
    return {"rows": len(rows), "entries": sum(len(r) for r in rows.values()),
            "terms": sum(len(c) for r in rows.values() for c in r.values())}


def apply_step_operator(operator: dict, interface: dict, terminals: Sequence[int]) -> dict:
    """Apply a compiled step to an interface with the template's metadata, naming the new boundary."""
    _check_interface(interface)
    R = _charge_depth(interface, operator["max_volume"])
    if R != operator["max_volume"] or interface["max_volume"] != R:
        raise ValueError("interface depth differs from the operator depth")
    if not _same_metadata(interface, {"terminals": operator["input_terminals"],
                                      "terminal_degrees": operator["terminal_degrees"],
                                      "terminal_edges": operator["terminal_edges"]}):
        raise ValueError("interface metadata differs from the operator template")
    terminals = _labels(terminals, "terminal")
    if len(terminals) != len(operator["input_terminals"]) or len(set(terminals)) != len(terminals):
        raise ValueError("new boundary labels must be distinct and match the boundary size")
    # Patterns evolve independently of the cells: replay the segment on metadata alone.
    shape = run_schedule(dict(interface, terminals=operator["input_terminals"], charges={}), operator["segment"])
    rows = operator["rows"]
    table: defaultdict[tuple, Counter] = defaultdict(Counter)
    for key, cells in interface["charges"].items():
        if key not in rows:
            raise ValueError(f"operator has no row for charge key {key}; build it with this key as a seed")
        for target, shifts in rows[key].items():
            row = table[target]
            for s, m in shifts.items():
                for e, c in cells.items():
                    row[e + s] += c * m
    return {"terminals": terminals, "max_volume": R, "terminal_degrees": operator["terminal_degrees"],
            "terminal_edges": operator["terminal_edges"], "patterns": shape["patterns"],
            "charges": _finish(table)}


# ---------------------------------------------------------------------------
# periodic strips: stationary segments of an elimination schedule


def strip_graph(rows: int, columns: int, cyclic: bool = False) -> Graph:
    """P_rows x P_columns with vertex r + rows*c (rows=1: path; 2: ladder; 3: 3 x n strip).

    ``cyclic`` joins the first and last columns (rows=1, columns>=3: the cycle C_n).
    """
    p = _integer(rows, "rows", minimum=1)
    n = _integer(columns, "columns", minimum=1)
    if not isinstance(cyclic, bool):
        raise TypeError("cyclic must be a boolean")
    edges = [(r + p * c, r + 1 + p * c) for c in range(n) for r in range(p - 1)]
    edges += [(r + p * c, r + p * (c + 1)) for c in range(n - 1) for r in range(p)]
    if cyclic:
        if n < 3:
            raise ValueError("a cyclic strip needs at least three columns")
        edges += [(r, r + p * (n - 1)) for r in range(p)]
    return Graph(p * n, edges)


def _positional_metadata(graph: Graph, boundary: Sequence[int], forgotten: set) -> tuple:
    index = {v: i for i, v in enumerate(boundary)}
    degrees = tuple(sum(1 for w in graph.neighbors[v] if w in forgotten) for v in boundary)
    edges = tuple(sorted(tuple(sorted((index[u], index[v]))) for u, v in graph.edges if u in index and v in index))
    return degrees, edges


def periodic_plan(graph: Graph, order: Sequence[int], period: int, anchors: Iterable[int] = ()) -> dict:
    """Split an elimination schedule into prefix, stationary steps and suffix.

    Column c is order[c*p:(c+1)*p]; the translation tau moves order[i] to
    order[i+p] and fixes ``anchors``.  Step c is the segment from the
    introduction of column c to that of column c+1.  The plan starts at the
    first c0 whose boundary metadata (terminal degrees, terminal edges by
    position) equals that of the next cut, and uses steps c0, c0+1, ... as
    long as each step and the next boundary are the tau-translates of step
    c0 and its boundary.  Returns the operation lists and the labels.
    """
    graph = _check_graph(graph)
    order = _order(graph, order)
    p = _integer(period, "period", minimum=1)
    anchors = set(_labels(anchors, "anchor"))
    if graph.n % p:
        raise ValueError("period must divide the number of vertices")
    position = {v: i for i, v in enumerate(order)}
    columns = graph.n // p

    def tau(v: int, m: int) -> int:
        if v in anchors:
            return v
        i = position[v] + m * p
        if not 0 <= i < graph.n:
            raise ValueError("translation leaves the order")
        return order[i]

    def translate(op: tuple, m: int) -> tuple:
        if op[0] == "introduce":
            return ("introduce", tau(op[1], m), tuple(tau(u, m) for u in op[2]))
        return ("forget", tau(op[1], m))

    ops = elimination_schedule(graph, order)
    cut = [next(i for i, op in enumerate(ops) if op[:2] == ("introduce", order[c * p])) for c in range(columns)]
    states = []  # boundary and forgotten set just before each cut
    boundary: list[int] = []
    forgotten: set[int] = set()
    i = 0
    for c in range(columns):
        while i < cut[c]:
            op = ops[i]
            if op[0] == "introduce":
                boundary.append(op[1])
            else:
                boundary.remove(op[1])
                forgotten.add(op[1])
            i += 1
        states.append((tuple(boundary), set(forgotten)))
    meta = [_positional_metadata(graph, b, f) for b, f in states]
    plan = None
    for c0 in range(columns - 1):
        if meta[c0] != meta[c0 + 1]:
            continue
        try:
            segment = ops[cut[c0]:cut[c0 + 1]]
            steps = 0
            for c in range(c0, columns - 1):
                expected = [translate(op, c - c0) for op in segment]
                if ops[cut[c]:cut[c + 1]] != expected or meta[c] != meta[c0] or \
                        states[c][0] != tuple(tau(v, c - c0) for v in states[c0][0]):
                    break
                steps += 1
        except ValueError:
            continue
        if steps:
            plan = c0, segment, steps
            break
    if plan is None:
        return {"prefix": ops, "segment": [], "steps": 0, "labels": [], "suffix": []}
    c0, segment, steps = plan
    labels = [tuple(tau(v, m) for v in states[c0][0]) for m in range(steps + 1)]
    return {"prefix": ops[:cut[c0]], "segment": segment, "steps": steps, "labels": labels,
            "suffix": ops[cut[c0 + steps]:] if c0 + steps < columns else []}


def periodic_compile(graph: Graph, order: Sequence[int], period: int, max_volume: int,
                     anchors: Iterable[int] = ()) -> tuple[list[dict[int, int]], dict]:
    """Coefficients through R by prefix, one compiled step operator applied repeatedly, suffix."""
    R = _integer(max_volume, "max_volume", minimum=0)
    plan = periodic_plan(graph, order, period, anchors)
    interface = run_schedule(empty_interface(R), plan["prefix"])
    operator = None
    if plan["steps"]:
        operator = build_step_operator(interface, plan["segment"])
        for m in range(plan["steps"]):
            interface = apply_step_operator(operator, interface, plan["labels"][m + 1])
        interface = run_schedule(interface, plan["suffix"])
    info = {"steps": plan["steps"], "operator": operator_size(operator) if operator else None}
    return closed_coefficients(interface), info
