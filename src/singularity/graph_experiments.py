"""Exact context operators on truncated symmetrized terminal kernels.

Coordinates are the raw population coefficients ``Y_o[v] = [x^v]
x^(s+t) K^+_G(s,t)``.  There is no normalization or division by an
automorphism count.  Context interiors are copied freshly on every gluing.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from .contexts import orbits, symmetrize
from .graph import Graph, _integer
from .terminals import _check_terminals, glue_graphs, terminal_kernel


@dataclass(frozen=True)
class ContextAttachment:
    """A checked simple context with a declared terminal-swap automorphism.

    Forbidding the terminal edge makes any sequence of fresh context copies
    edge disjoint.  Checking the actual permutation, rather than just a
    finite kernel prefix, guarantees swap symmetry at every height.
    """

    name: str
    graph: Graph
    terminals: tuple[int, int] = (0, 1)
    swap_automorphism: tuple[int, ...] | None = None

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("context name must be a nonempty string")
        terminals = _check_terminals(self.graph, self.terminals)
        if len(terminals) != 2:
            raise ValueError("a context must have exactly two terminals")
        object.__setattr__(self, "terminals", terminals)
        if tuple(sorted(terminals)) in self.graph.edges:
            raise ValueError("context terminal edges are forbidden")
        permutation = self.swap_automorphism
        if permutation is None:
            permutation = list(range(self.graph.n))
            a, b = terminals
            permutation[a], permutation[b] = b, a
        permutation = tuple(permutation)
        if self.graph.relabel(permutation) != self.graph:
            raise ValueError("declared terminal swap is not a graph automorphism")
        a, b = terminals
        if permutation[a] != b or permutation[b] != a:
            raise ValueError("automorphism must exchange the terminals")
        object.__setattr__(self, "swap_automorphism", permutation)


def standard_attachments() -> tuple[ContextAttachment, ContextAttachment]:
    """A pendant leaf at each terminal, and a single shared neighbour."""
    return (
        ContextAttachment("pendant_leaf_pair", Graph(4, ((0, 2), (1, 3))),
                          swap_automorphism=(1, 0, 3, 2)),
        ContextAttachment("shared_neighbor", Graph(3, ((0, 2), (1, 2))),
                          swap_automorphism=(1, 0, 2)),
    )


def _exact(value, name="value"):
    """Public numeric inputs are exact: int or Fraction, never bool or float."""
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(f"{name} must be an int or Fraction, not {type(value).__name__}")
    return Fraction(value)


def _row_times(row, matrix):
    return tuple(sum((a * matrix[k][j] for k, a in enumerate(row) if a), Fraction(0))
                 for j in range(len(row)))


class BoundaryExperimentSystem:
    """Compile a declared context language at a rational q and volume budget.

    Operators act on column states.  ``word=(0, 1)`` first attaches context
    zero and then context one.  Output coordinate v is the raw local-series
    population at total volume v of the assembled graph.
    """

    def __init__(self, max_volume: int, q, attachments=None):
        self.max_volume = _integer(max_volume, "max_volume", minimum=0)
        self.q = _exact(q, "q")
        if not 0 < self.q < 1:
            raise ValueError("q must lie strictly between zero and one")
        self.attachments = tuple(standard_attachments() if attachments is None else attachments)
        if any(not isinstance(a, ContextAttachment) for a in self.attachments):
            raise TypeError("attachments must be checked ContextAttachment objects")
        if len({a.name for a in self.attachments}) != len(self.attachments):
            raise ValueError("context names must be distinct")
        R = self.max_volume
        self.coordinates = tuple((o, v) for o in orbits(R) for v in range(sum(o), R + 1))
        self.dimension = len(self.coordinates)
        self.observations = tuple(tuple(Fraction(v == target) for _, v in self.coordinates)
                                  for target in range(R + 1))
        operators = []
        for attachment in self.attachments:
            kernel = terminal_kernel(attachment.graph, attachment.terminals, R)
            coefficients = {}
            for o in orbits(R):
                cells = kernel.get(o, {})
                coefficients[o] = tuple(sum((Fraction(c) * self.q ** e
                                            for (j, e), c in cells.items() if j == k), Fraction(0))
                                        for k in range(R + 1 - sum(o)))
            operators.append(tuple(tuple(coefficients[o][v - j] if o == p and v >= j else Fraction(0)
                                         for p, j in self.coordinates) for o, v in self.coordinates))
        self.operators = tuple(operators)

    def compile_graph(self, graph: Graph, terminals: Sequence[int] = (0, 1)):
        """The exact rational state of a graph, retaining all multiplicities."""
        terminals = _check_terminals(graph, terminals)
        if len(terminals) != 2:
            raise ValueError("the graph must have exactly two terminals")
        kernel = symmetrize(terminal_kernel(graph, terminals, self.max_volume))
        return tuple(sum((Fraction(c) * self.q ** e
                          for (j, e), c in kernel.get(o, {}).items() if j == v - sum(o)), Fraction(0))
                     for o, v in self.coordinates)

    def _word(self, word):
        result = tuple(_integer(i, "attachment index", minimum=0) for i in word)
        if any(i >= len(self.attachments) for i in result):
            raise ValueError("attachment index outside the declared language")
        return result

    def apply_word(self, state, word=()):
        state = tuple(_exact(x, "state entry") for x in state)
        if len(state) != self.dimension:
            raise ValueError("state has the wrong dimension")
        for i in self._word(word):
            state = tuple(sum((a * b for a, b in zip(row, state)), Fraction(0))
                          for row in self.operators[i])
        return state

    def observe(self, state, word=()):
        state = self.apply_word(state, word)
        return tuple(sum((a * b for a, b in zip(row, state)), Fraction(0))
                     for row in self.observations)

    def attached_graph(self, graph: Graph, terminals: Sequence[int] = (0, 1), word=()):
        terminals = _check_terminals(graph, terminals)
        if len(terminals) != 2:
            raise ValueError("the graph must have exactly two terminals")
        for i in self._word(word):
            context = self.attachments[i]
            graph, _ = glue_graphs(graph, terminals, context.graph, context.terminals)
        return graph, terminals

    def direct_observations(self, graph: Graph, terminals: Sequence[int] = (0, 1), word=()):
        """Independent weak-composition counts on the actual assembled graph."""
        from .heights import local_coefficients
        graph, _ = self.attached_graph(graph, terminals, word)
        return tuple(sum((Fraction(c) * self.q ** e for e, c in row.items()), Fraction(0))
                     for row in local_coefficients(graph, self.max_volume))

    def operator_system(self, attachment_costs=None, observation_costs=None):
        from .observability import OperatorSystem
        return OperatorSystem(self.dimension, self.operators, self.observations,
                              attachment_costs, observation_costs)
