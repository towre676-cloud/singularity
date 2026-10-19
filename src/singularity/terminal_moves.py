"""Noncommuting graph operations with closed state semantics (OE13).

The symmetric compiler of graph_experiments symmetrizes kernels and therefore
only supports operations that respect the terminal swap.  Moving one terminal
breaks that symmetry, so this module keeps ORDERED states

    Y[(s, t), v] = [x^v] x^(s+t) K_G(s, t),   s, t >= 0,  s + t <= v <= R,

raw labeled counts with no averaging.  Three kinds of operation act on them.

* Context attachment (any context with two terminals, no terminal-terminal
  edge, fresh interior; swap symmetry is NOT required here):
  Y'[(s,t), v] = sum_j [x^j] K_C(s,t) Y[(s,t), v-j].
* Terminal extension at terminal a: a new vertex l is joined to the current
  terminal a, l becomes terminal a and the old terminal becomes interior.
  With the old height s now interior,
  Y'[(s',t), v] = sum_s q^((s-s')^2) Y[(s,t), v-s'].
* Terminal extension at terminal b, symmetrically.

Proof of the extension rule: the new kernel is K'(s',t) = sum_s x^s
q^((s-s')^2) K(s,t), because the only new edge is (old a, l) and the old
terminal's height joins the interior volume.  Extracting [x^v] x^(s'+t) gives
the formula; every term uses Y at volume v - s' <= v, so the truncated space
is closed and no budget growth is needed.  Context attachment is SNG-O05
without the symmetrization step.  Every operation maps a realizable graph
state to the state of the actual modified graph, which tests check by direct
enumeration.

Extension and the shared neighbour do not commute: attaching a shared
neighbour before or after moving terminal a gives different graphs (the new
neighbour is adjacent to the old or to the new terminal) and different
operators.  Words are chronological, exactly as in observability.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from .graph import Graph, _integer
from .graph_experiments import ContextAttachment, _exact, standard_attachments
from .heights import local_coefficients
from .observability import OperatorSystem
from .terminals import _check_terminals, glue_graphs, terminal_kernel

EXTEND_A, EXTEND_B = "extend_a", "extend_b"


class OrderedMoveSystem:
    """Ordered truncated kernels under contexts and terminal extensions.

    ``moves`` is a sequence whose items are ContextAttachment objects or the
    strings "extend_a" / "extend_b".  Output v is the local coefficient at
    volume v of the current graph.
    """

    def __init__(self, max_volume: int, q, moves=None):
        self.max_volume = _integer(max_volume, "max_volume", minimum=0)
        self.q = _exact(q, "q")
        if not 0 < self.q < 1:
            raise ValueError("q must lie strictly between zero and one")
        moves = tuple(standard_attachments()) + (EXTEND_A, EXTEND_B) if moves is None else tuple(moves)
        for m in moves:
            if not (isinstance(m, ContextAttachment) or m in (EXTEND_A, EXTEND_B)):
                raise TypeError("moves must be ContextAttachment objects or 'extend_a'/'extend_b'")
        self.moves = moves
        R = self.max_volume
        self.coordinates = tuple(((s, t), v) for s in range(R + 1) for t in range(R + 1 - s)
                                 for v in range(s + t, R + 1))
        self.dimension = len(self.coordinates)
        index = {c: i for i, c in enumerate(self.coordinates)}
        self.observations = tuple(tuple(Fraction(v == target) for _, v in self.coordinates)
                                  for target in range(R + 1))
        operators = []
        for move in moves:
            matrix = [[Fraction(0)] * self.dimension for _ in range(self.dimension)]
            if isinstance(move, ContextAttachment):
                kernel = terminal_kernel(move.graph, move.terminals, R)
                for (st, v), row in index.items():
                    cells = kernel.get(st, {})
                    for (j, e), c in cells.items():
                        if v - j >= sum(st):
                            matrix[row][index[(st, v - j)]] += Fraction(c) * self.q ** e
            elif move == EXTEND_A:
                # Y'[(s2,t),v] = sum_s q^((s-s2)^2) Y[(s,t), v-s2]
                for ((s2, t), v), row in index.items():
                    for s in range(R + 1):
                        old = ((s, t), v - s2)
                        if old in index:
                            matrix[row][index[old]] += self.q ** ((s - s2) ** 2)
            else:
                # Y'[(s,t2),v] = sum_t q^((t-t2)^2) Y[(s,t), v-t2]
                for ((s, t2), v), row in index.items():
                    for t in range(R + 1):
                        old = ((s, t), v - t2)
                        if old in index:
                            matrix[row][index[old]] += self.q ** ((t - t2) ** 2)
            operators.append(tuple(tuple(r) for r in matrix))
        self.operators = tuple(operators)

    def compile_graph(self, graph: Graph, terminals: Sequence[int] = (0, 1)):
        """The ordered state of a two-terminal graph."""
        terminals = _check_terminals(graph, terminals)
        if len(terminals) != 2:
            raise ValueError("the graph must have exactly two terminals")
        kernel = terminal_kernel(graph, terminals, self.max_volume)
        return tuple(sum((Fraction(c) * self.q ** e for (j, e), c in kernel.get(st, {}).items()
                          if j == v - sum(st)), Fraction(0)) for st, v in self.coordinates)

    def apply_word(self, state, word=()):
        state = tuple(_exact(x, "state entry") for x in state)
        if len(state) != self.dimension:
            raise ValueError("state has the wrong dimension")
        for i in word:
            i = _integer(i, "move index", minimum=0)
            if i >= len(self.moves):
                raise ValueError("move index outside the declared language")
            state = tuple(sum((a * b for a, b in zip(row, state)), Fraction(0)) for row in self.operators[i])
        return state

    def observe(self, state, word=()):
        state = self.apply_word(state, word)
        return tuple(sum((a * b for a, b in zip(row, state)), Fraction(0)) for row in self.observations)

    def assemble(self, graph: Graph, terminals: Sequence[int] = (0, 1), word=()):
        """The actual graph and terminals after the chronological word."""
        terminals = tuple(_check_terminals(graph, terminals))
        for i in word:
            move = self.moves[_integer(i, "move index", minimum=0)]
            if isinstance(move, ContextAttachment):
                graph, _ = glue_graphs(graph, terminals, move.graph, move.terminals)
            else:
                k = 0 if move == EXTEND_A else 1
                new = graph.n
                graph = Graph(graph.n + 1, tuple(graph.edges) + ((terminals[k], new),))
                terminals = (new, terminals[1]) if k == 0 else (terminals[0], new)
        return graph, terminals

    def direct_observations(self, graph: Graph, terminals: Sequence[int] = (0, 1), word=()):
        """Independent check: enumerate heights on the assembled graph."""
        graph, _ = self.assemble(graph, terminals, word)
        return tuple(sum((Fraction(c) * self.q ** e for e, c in row.items()), Fraction(0))
                     for row in local_coefficients(graph, self.max_volume))

    def operator_system(self, attachment_costs=None, observation_costs=None):
        return OperatorSystem(self.dimension, self.operators, self.observations,
                              attachment_costs, observation_costs)
