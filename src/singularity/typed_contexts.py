"""A finite typed boundary grammar for graph assembly at a fixed volume budget (NX13-B).

Four boundary types, all at volume budget R and a rational 0 < q < 1:

* ``closed``   no terminal;        Y[v]       = [x^v] L_G(x, q);
* ``one``      ordered terminal a; Y[(s), v]   = [x^v] x^s K_G(s);
* ``two``      ordered (a, b), a and b NOT adjacent;
* ``two_adj``  ordered (a, b), a and b adjacent;
  for both two-terminal types Y[(s, t), v] = [x^v] x^(s+t) K_G(s, t).

Here K_G(b) is the terminal kernel of ``terminals.py``: interior heights are
summed, the energy is the full graph energy (terminal-terminal edge
included), and 0 <= |b| <= v <= R.  ``two`` and ``two_adj`` have identical
coordinates; the edge status is legality metadata.  Splitting them is what
makes "add the terminal edge twice" ill-typed instead of a silent
multigraph: the matrix identity alone cannot see whether the edge exists.

Actions (operation names; typed identifiers carry the source type):

=============  ==================  =========================================
operation      typing              graph semantics (chronological)
=============  ==================  =========================================
open           closed -> one       new isolated vertex becomes terminal a
close          one -> closed       terminal a becomes interior
intro          one -> two          new isolated vertex becomes terminal b
intro_adj      one -> two_adj      new vertex joined to a becomes terminal b
pendant        one -> one          fresh leaf attached at a
join           two -> two_adj      add the edge ab
cut            two_adj -> two      delete the edge ab
forget_a/b     two*, -> one        that terminal becomes interior; the other
                                   one is the new terminal a
extend_a/b     two* -> two         new vertex joined to that terminal becomes
                                   the terminal; old one becomes interior
swap           two -> two,         exchange terminal order
               two_adj -> two_adj
contexts       two -> two,         glue a fresh copy of a checked ordered
               two_adj -> two_adj  two-terminal context (no terminal edge)
=============  ==================  =========================================

Every formula (docs/research/TYPED_OBSERVABILITY.md) writes an output
coordinate of volume v through input coordinates of volume <= v, so the
truncated spaces are closed under every legal word at the same R.  Context
and terminal-extension matrices are the existing ``OrderedMoveSystem``
operators, reused unchanged.

The algebraic replay of a typed certificate does not prove this adapter.
The adapter is checked separately against height enumeration on the
actually assembled graphs (``direct_state``, ``direct_observations``).
"""
from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from .graph import Graph, _integer
from .graph_experiments import _exact
from .heights import local_coefficients
from .separator_compiler import compile_graph as _separator_coefficients
from .terminal_moves import EXTEND_A, EXTEND_B, OrderedContextAttachment, OrderedMoveSystem
from .terminals import _check_terminals, glue_graphs, kernel_by_enumeration, terminal_kernel
from .typed_observability import StateType, TypedAction, TypedObservation, TypedOperatorSystem

CLOSED, ONE, TWO, TWO_ADJ = "closed", "one", "two", "two_adj"
ARITY = {CLOSED: 0, ONE: 1, TWO: 2, TWO_ADJ: 2}

DEFAULT_COSTS = {"open": 1, "close": 1, "intro": 1, "intro_adj": 2, "pendant": 2, "join": 1,
                 "cut": 1, "forget_a": 1, "forget_b": 1, "extend_a": 1, "extend_b": 1, "swap": 1}


def default_contexts() -> tuple[OrderedContextAttachment, ...]:
    """A one-sided leaf at a (asymmetric) and a shared neighbour."""
    return (OrderedContextAttachment("leaf_a", Graph(3, ((0, 2),))),
            OrderedContextAttachment("shared", Graph(3, ((0, 2), (1, 2)))))


def _coordinates(R: int, arity: int):
    if arity == 0:
        return tuple(((), v) for v in range(R + 1))
    if arity == 1:
        return tuple(((s,), v) for s in range(R + 1) for v in range(s, R + 1))
    # Same order as OrderedMoveSystem, so its operators are reused verbatim.
    return tuple(((s, t), v) for s in range(R + 1) for t in range(R + 1 - s) for v in range(s + t, R + 1))


class BoundaryGrammar:
    """Compile the declared finite grammar into a ``TypedOperatorSystem``.

    ``contexts`` are checked ``OrderedContextAttachment`` objects (no
    terminal-terminal edge; order retained).  ``costs`` overrides
    ``DEFAULT_COSTS`` by operation name; context costs default to the
    number of context interior vertices.  Observations at every type are the
    local coefficients [x^v] L of the current graph, v = 0..R, cost 0.
    """

    def __init__(self, max_volume: int, q, contexts=None, costs=None, context_costs=None):
        self.max_volume = R = _integer(max_volume, "max_volume", minimum=0)
        self.q = _exact(q, "q")
        if not 0 < self.q < 1:
            raise ValueError("q must lie strictly between zero and one")
        self.contexts = default_contexts() if contexts is None else tuple(contexts)
        for c in self.contexts:
            if not isinstance(c, OrderedContextAttachment):
                raise TypeError("contexts must be OrderedContextAttachment objects")
        names = [c.name for c in self.contexts]
        if len(set(names)) != len(names) or set(names) & set(DEFAULT_COSTS):
            raise ValueError("context names must be distinct from each other and from operations")
        self.costs = dict(DEFAULT_COSTS)
        for k, v in (costs or {}).items():
            if k not in DEFAULT_COSTS:
                raise ValueError(f"unknown operation {k!r}")
            self.costs[k] = v
        ccosts = {c.name: c.graph.n - 2 for c in self.contexts}
        for k, v in (context_costs or {}).items():
            if k not in ccosts:
                raise ValueError(f"unknown context {k!r}")
            ccosts[k] = v
        self.coordinates = {ty: _coordinates(R, ARITY[ty]) for ty in ARITY}
        self.index = {ty: {c: i for i, c in enumerate(cs)} for ty, cs in self.coordinates.items()}
        moves = OrderedMoveSystem(R, self.q, self.contexts + (EXTEND_A, EXTEND_B))
        if moves.coordinates != self.coordinates[TWO]:
            raise ArithmeticError("ordered coordinate convention changed")
        reused = dict(zip([c.name for c in self.contexts] + ["extend_a", "extend_b"], moves.operators))
        self.rules = {}  # action identifier -> (operation, source, target)
        actions = []

        def add(operation, source, target, matrix, cost, suffix=""):
            identifier = operation + suffix
            self.rules[identifier] = (operation, source, target)
            actions.append(TypedAction(identifier, source, target, matrix, cost))

        add("open", CLOSED, ONE, self._open(), self.costs["open"])
        add("close", ONE, CLOSED, self._close(), self.costs["close"])
        add("intro", ONE, TWO, self._intro(False), self.costs["intro"])
        add("intro_adj", ONE, TWO_ADJ, self._intro(True), self.costs["intro_adj"])
        add("pendant", ONE, ONE, self._pendant(), self.costs["pendant"])
        add("join", TWO, TWO_ADJ, self._edge(+1), self.costs["join"])
        add("cut", TWO_ADJ, TWO, self._edge(-1), self.costs["cut"])
        for source, sfx in ((TWO, ""), (TWO_ADJ, "@adj")):
            add("forget_a", source, ONE, self._forget(0), self.costs["forget_a"], sfx)
            add("forget_b", source, ONE, self._forget(1), self.costs["forget_b"], sfx)
            add("extend_a", source, TWO, reused["extend_a"], self.costs["extend_a"], sfx)
            add("extend_b", source, TWO, reused["extend_b"], self.costs["extend_b"], sfx)
            add("swap", source, source, self._swap(), self.costs["swap"], sfx)
            for c in self.contexts:
                add(c.name, source, source, reused[c.name], ccosts[c.name], sfx)
        observations = [TypedObservation(f"L{v}@{ty}", ty,
                                         tuple(Fraction(w == v) for _, w in self.coordinates[ty]), 0)
                        for ty in ARITY for v in range(R + 1)]
        types = [StateType(ty, len(self.coordinates[ty])) for ty in ARITY]
        self.system = TypedOperatorSystem(types, actions, observations)

    # -- matrices ---------------------------------------------------------

    def _zero(self, target, source):
        return [[Fraction(0)] * len(self.coordinates[source]) for _ in self.coordinates[target]]

    @staticmethod
    def _freeze(m):
        return tuple(tuple(r) for r in m)

    def _open(self):
        # K'(s) = L_G: Y'[(s),v] = Y0[v-s].
        m, ix = self._zero(ONE, CLOSED), self.index
        for ((s,), v), row in ix[ONE].items():
            m[row][ix[CLOSED][((), v - s)]] = Fraction(1)
        return self._freeze(m)

    def _close(self):
        # Y'[v] = sum_s Y[(s),v].
        m, ix = self._zero(CLOSED, ONE), self.index
        for ((s,), v), col in ix[ONE].items():
            m[ix[CLOSED][((), v)]][col] += 1
        return self._freeze(m)

    def _intro(self, adjacent):
        # K'(s,t) = q^((s-t)^2 [adjacent]) K(s): Y'[(s,t),v] = q^.. Y[(s),v-t].
        target = TWO_ADJ if adjacent else TWO
        m, ix = self._zero(target, ONE), self.index
        for ((s, t), v), row in ix[target].items():
            m[row][ix[ONE][((s,), v - t)]] = self.q ** ((s - t) ** 2) if adjacent else Fraction(1)
        return self._freeze(m)

    def _pendant(self):
        # K'(s) = K(s) sum_h x^h q^((s-h)^2), computed from the leaf kernel.
        kernel = terminal_kernel(Graph(2, ((0, 1),)), (0,), self.max_volume)
        m, ix = self._zero(ONE, ONE), self.index
        for ((s,), v), row in ix[ONE].items():
            for (j, e), c in kernel.get((s,), {}).items():
                if v - j >= s:
                    m[row][ix[ONE][((s,), v - j)]] += c * self.q ** e
        return self._freeze(m)

    def _edge(self, sign):
        # join: K' = q^((s-t)^2) K;  cut: K' = q^(-(s-t)^2) K.
        source, target = (TWO, TWO_ADJ) if sign > 0 else (TWO_ADJ, TWO)
        m, ix = self._zero(target, source), self.index
        for ((s, t), v), row in ix[target].items():
            m[row][ix[source][((s, t), v)]] = self.q ** (sign * (s - t) ** 2)
        return self._freeze(m)

    def _forget(self, which):
        # Forget a: K'(t) = sum_s x^s K(s,t), so Y'[(t),v] = sum_s Y[(s,t),v].
        m, ix = self._zero(ONE, TWO), self.index
        for ((s, t), v), col in ix[TWO].items():
            kept = t if which == 0 else s
            m[ix[ONE][((kept,), v)]][col] += 1
        return self._freeze(m)

    def _swap(self):
        m, ix = self._zero(TWO, TWO), self.index
        for ((s, t), v), row in ix[TWO].items():
            m[row][ix[TWO][((t, s), v)]] = Fraction(1)
        return self._freeze(m)

    # -- graph side ---------------------------------------------------------

    def type_of(self, graph: Graph, terminals: Sequence[int]) -> str:
        """The boundary type of a placed graph."""
        if not isinstance(graph, Graph):
            raise TypeError("graph must be a Graph")
        terminals = tuple(terminals)
        if not terminals:
            return CLOSED
        terminals = _check_terminals(graph, terminals)
        if len(terminals) == 1:
            return ONE
        if len(terminals) != 2:
            raise ValueError("the grammar has at most two terminals")
        return TWO_ADJ if tuple(sorted(terminals)) in graph.edges else TWO

    def compile_state(self, graph: Graph, terminals: Sequence[int] = ()):
        """State of a placed graph, from the bag-message kernel / separator compiler."""
        ty = self.type_of(graph, terminals)
        R = self.max_volume
        if ty == CLOSED:
            rows = _separator_coefficients(graph, tuple(range(graph.n)), R)
            return ty, tuple(sum((c * self.q ** e for e, c in rows[v].items()), Fraction(0))
                             for _, v in self.coordinates[ty])
        return ty, self._from_kernel(ty, terminal_kernel(graph, tuple(terminals), R))

    def _from_kernel(self, ty, kernel):
        return tuple(sum((Fraction(c) * self.q ** e for (j, e), c in kernel.get(b, {}).items()
                          if j == v - sum(b)), Fraction(0)) for b, v in self.coordinates[ty])

    def direct_state(self, graph: Graph, terminals: Sequence[int] = ()):
        """Independent oracle: weak-composition enumeration on the placed graph."""
        ty = self.type_of(graph, terminals)
        if ty == CLOSED:
            rows = local_coefficients(graph, self.max_volume)
            return ty, tuple(sum((c * self.q ** e for e, c in rows[v].items()), Fraction(0))
                             for _, v in self.coordinates[ty])
        return ty, self._from_kernel(ty, kernel_by_enumeration(graph, tuple(terminals), self.max_volume))

    def assemble(self, graph: Graph, terminals: Sequence[int], word=()):
        """The actual graph and terminals after a chronological word.

        The word is first type-checked from the graph's own boundary type,
        so an ill-typed word (for example ``join`` twice) is rejected before
        any graph is built.  Fresh vertices are appended; context interiors
        are fresh copies through ``glue_graphs``.
        """
        ty = self.type_of(graph, terminals)
        word = tuple(word)
        self.system.path(word, ty)
        terminals = tuple(terminals)
        for identifier in word:
            operation, _, _ = self.rules[identifier]
            n, edges = graph.n, list(graph.edges)
            if operation == "open":
                graph, terminals = Graph(n + 1, edges), (n,)
            elif operation == "close":
                terminals = ()
            elif operation in ("intro", "intro_adj"):
                extra = [(terminals[0], n)] if operation == "intro_adj" else []
                graph, terminals = Graph(n + 1, edges + extra), (terminals[0], n)
            elif operation == "pendant":
                graph = Graph(n + 1, edges + [(terminals[0], n)])
            elif operation == "join":
                graph = Graph(n, edges + [terminals])  # Graph rejects a duplicate edge
            elif operation == "cut":
                pair = tuple(sorted(terminals))
                if pair not in graph.edges:
                    raise ValueError("cut needs an existing terminal edge")
                graph = Graph(n, [e for e in edges if e != pair])
            elif operation == "forget_a":
                terminals = (terminals[1],)
            elif operation == "forget_b":
                terminals = (terminals[0],)
            elif operation in ("extend_a", "extend_b"):
                k = 0 if operation == "extend_a" else 1
                graph = Graph(n + 1, edges + [(terminals[k], n)])
                terminals = (n, terminals[1]) if k == 0 else (terminals[0], n)
            elif operation == "swap":
                terminals = (terminals[1], terminals[0])
            else:
                context = next(c for c in self.contexts if c.name == operation)
                graph, _ = glue_graphs(graph, terminals, context.graph, context.terminals)
        return graph, terminals

    def direct_observations(self, graph: Graph, terminals: Sequence[int], word=()):
        """Independent check: local coefficients of the assembled graph."""
        graph, _ = self.assemble(graph, terminals, word)
        return tuple(sum((Fraction(c) * self.q ** e for e, c in row.items()), Fraction(0))
                     for row in local_coefficients(graph, self.max_volume))

    def observe(self, start_type, state, word=()):
        """Readings L0..LR after the word, computed by the typed matrices."""
        from .typed_observability import typed_apply_word
        end, state = typed_apply_word(self.system, start_type, state, word)
        return tuple(sum((a * b for a, b in zip(o.row, state)), Fraction(0))
                     for o in self.system.observations_at[end])

    def provenance(self) -> dict:
        """Adapter metadata kept separately from the algebraic certificate."""
        return {
            "adapter": "singularity.typed_contexts.BoundaryGrammar",
            "volume_convention": "raw labeled local coefficients [x^v] L_G(x,q), 0 <= v <= R, no normalization",
            "max_volume": self.max_volume, "q": [self.q.numerator, self.q.denominator],
            "types": {ty: {"terminals": ARITY[ty], "terminal_edge": ty == TWO_ADJ,
                           "coordinates": [[list(b), v] for b, v in self.coordinates[ty]]} for ty in ARITY},
            "actions": {k: {"operation": op, "source": s, "target": t} for k, (op, s, t) in self.rules.items()},
            "contexts": {c.name: {"n": c.graph.n, "edges": [list(e) for e in c.graph.edges],
                                  "terminals": list(c.terminals)} for c in self.contexts},
            "assembly_rule": "fresh appended vertices; fresh context interiors; ordered terminals; "
                             "terminal edge only via join from type two",
            "note": "generic algebraic replay does not prove this adapter",
        }
