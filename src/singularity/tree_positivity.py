"""Ordered tree-kernel positivity, with a safe box (FR03).

These statements concern the complete analytic ordered kernel for 0 < x,q < 1,
not a global-volume truncation and not the symmetrized interface.  The exact
box evaluator below sums every interior height independently in 0,...,H.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from .graph import Graph, _integer


def _rational(value: object, name: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(f"{name} must be an exact rational (int or Fraction)")
    value = Fraction(value)
    if not 0 < value < 1:
        raise ValueError(f"{name} must lie strictly between zero and one")
    return value


def terminal_path(tree: Graph, terminals: Sequence[int]) -> tuple[int, ...]:
    """The unique ordered terminal path; reject disconnected graphs and cycles."""
    if not isinstance(tree, Graph):
        raise TypeError("tree must be a Graph")
    if not tree.connected or len(tree.edges) != tree.n - 1:
        raise ValueError("graph must be a connected tree")
    terminals = tuple(_integer(v, "terminal", minimum=0) for v in terminals)
    if len(terminals) != 2 or len(set(terminals)) != 2 or max(terminals) >= tree.n:
        raise ValueError("exactly two distinct terminal vertices are required")
    start, target = terminals
    parents = {start: None}
    stack = [start]
    while stack:
        vertex = stack.pop()
        if vertex == target:
            break
        for neighbor in tree.neighbors[vertex]:
            if neighbor not in parents:
                parents[neighbor] = vertex
                stack.append(neighbor)
    path = [target]
    while path[-1] != start:
        path.append(parents[path[-1]])
    return tuple(reversed(path))


def consecutive_minor_lead(
    tree: Graph, terminals: Sequence[int], q: Fraction, order: int = 2,
) -> dict[str, object]:
    """First term of the full kernel minor on consecutive pins 0,...,k-1.

    For terminal distance d and c edges leaving the terminal path, put
    S=k(k-1)/2 and T=k(k-1)(2k-1)/6.  The leading term is
    x**((d-1)*S) * q**(c*T) * product(1-q**(2*r))**(d*(k-r)).
    This describes the formal series exactly, not a determinant of a kernel
    whose coefficient budget is too short to compute that leading degree.
    """
    q = _rational(q, "q")
    order = _integer(order, "order", minimum=1)
    if order > 256:
        raise ValueError("order exceeds the declared formula-work bound 256")
    path = terminal_path(tree, terminals)
    distance = len(path) - 1
    branch_edges = sum(tree.degrees[v] for v in path) - 2 * distance
    index_sum = order * (order - 1) // 2
    square_sum = order * (order - 1) * (2 * order - 1) // 6
    coefficient = q ** (branch_edges * square_sum)
    for r in range(1, order):
        coefficient *= (1 - q ** (2 * r)) ** (distance * (order - r))
    return {
        "order": order,
        "path": path,
        "distance": distance,
        "off_path_edges": branch_edges,
        "first_volume": (distance - 1) * index_sum,
        "coefficient": coefficient,
    }


def distance_minor_lead(tree: Graph, terminals: Sequence[int], q: Fraction) -> dict[str, object]:
    """The k=2 distance witness: x**(d-1) q**c (1-q**2)**d."""
    return consecutive_minor_lead(tree, terminals, q, order=2)


def _pins(values: Sequence[int], name: str) -> tuple[int, ...]:
    values = tuple(_integer(v, name, minimum=0) for v in values)
    if not values:
        raise ValueError(f"{name} must not be empty")
    return values


def boxed_tree_kernel(
    tree: Graph,
    terminals: Sequence[int],
    row_heights: Sequence[int],
    column_heights: Sequence[int],
    height_bound: int,
    x: Fraction,
    q: Fraction,
    *,
    max_work: int = 1_000_000,
) -> tuple[tuple[Fraction, ...], ...]:
    """Exact ordered kernel with every *interior* height in the same box.

    Terminals are pinned to the supplied nonnegative heights; they receive no
    factor of x and need not lie in the box.  Off-path trees are integrated by
    messages, then the unique terminal path is contracted.  ``max_work``
    bounds a conservative preflight count of scalar summands, not bit cost.
    Increasing rational numerator sizes remain a caller-visible cost.
    """
    path = terminal_path(tree, terminals)
    rows = _pins(row_heights, "row height")
    columns = _pins(column_heights, "column height")
    height_bound = _integer(height_bound, "height_bound", minimum=0)
    max_work = _integer(max_work, "max_work", minimum=1)
    x, q = _rational(x, "x"), _rational(q, "q")
    size = height_bound + 1
    # Off-path subtree messages use at most n size-by-size sums; messages to
    # an endpoint may have more pin values than the height box.
    estimate = (tree.n * size * size + tree.n * size * (len(rows) + len(columns))
                + len(path) * len(rows) * size * size
                + len(rows) * len(columns) * max(1, size))
    if estimate > max_work:
        raise ValueError(f"boxed-tree work estimate {estimate} exceeds max_work={max_work}")
    path_set = set(path)
    edge_cache: dict[tuple[int, int], Fraction] = {}

    def edge(a: int, b: int) -> Fraction:
        key = (min(a, b), max(a, b))
        if key not in edge_cache:
            edge_cache[key] = q ** ((a - b) ** 2)
        return edge_cache[key]

    # Root every off-path component at its attachment to the path.  Reversed
    # traversal is iterative, so long pendant paths do not hit recursion limits.
    parent: dict[int, int] = {}
    order: list[int] = []
    for root in path:
        stack = [(v, root) for v in tree.neighbors[root] if v not in path_set]
        while stack:
            vertex, predecessor = stack.pop()
            parent[vertex] = predecessor
            order.append(vertex)
            stack.extend((v, vertex) for v in tree.neighbors[vertex] if v != predecessor)
    children: dict[int, list[int]] = {v: [] for v in range(tree.n)}
    for child, predecessor in parent.items():
        children[predecessor].append(child)
    weights: dict[int, tuple[Fraction, ...]] = {}
    for vertex in reversed(order):
        own = [x ** h for h in range(size)]
        for child in children[vertex]:
            message = [sum((edge(h, k) * weights[child][k] for k in range(size)), Fraction())
                       for h in range(size)]
            own = [a * b for a, b in zip(own, message)]
        weights[vertex] = tuple(own)

    def branch_factors(vertex: int, domain: tuple[int, ...]) -> tuple[Fraction, ...]:
        factors = [Fraction(1)] * len(domain)
        for child in children[vertex]:
            message = [sum((edge(h, k) * weights[child][k] for k in range(size)), Fraction())
                       for h in domain]
            factors = [a * b for a, b in zip(factors, message)]
        return tuple(factors)

    left = branch_factors(path[0], rows)
    right = branch_factors(path[-1], columns)
    if len(path) == 2:
        return tuple(tuple(left[i] * edge(s, t) * right[j] for j, t in enumerate(columns))
                     for i, s in enumerate(rows))
    domain = tuple(range(size))
    diagonal = {v: tuple(x ** h * factor for h, factor in zip(domain, branch_factors(v, domain)))
                for v in path[1:-1]}
    output = []
    for i, s in enumerate(rows):
        vector = [left[i] * edge(s, h) * diagonal[path[1]][h] for h in domain]
        for vertex in path[2:-1]:
            vector = [sum((vector[h] * edge(h, k) for h in domain), Fraction())
                      * diagonal[vertex][k] for k in domain]
        output.append(tuple(sum((vector[h] * edge(h, t) for h in domain), Fraction()) * right[j]
                            for j, t in enumerate(columns)))
    return tuple(output)


def exact_determinant(matrix: Sequence[Sequence[Fraction]]) -> Fraction:
    """Fraction-preserving elimination for a square matrix (empty det = 1)."""
    rows = [list(map(Fraction, row)) for row in matrix]
    n = len(rows)
    if any(len(row) != n for row in rows):
        raise ValueError("determinant requires a square matrix")
    answer = Fraction(1)
    for j in range(n):
        pivot = next((i for i in range(j, n) if rows[i][j]), None)
        if pivot is None:
            return Fraction()
        if pivot != j:
            rows[j], rows[pivot] = rows[pivot], rows[j]
            answer = -answer
        diagonal = rows[j][j]
        answer *= diagonal
        for i in range(j + 1, n):
            factor = rows[i][j] / diagonal
            for k in range(j + 1, n):
                rows[i][k] -= factor * rows[j][k]
            rows[i][j] = Fraction()
    return answer
