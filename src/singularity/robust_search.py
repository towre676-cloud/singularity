"""Cost-bounded robust experiment search (maximum normalized margin).

This layer sits beside the exact cheapest-witness engine of
``observability.py`` and does not change it.  States are columns, words are
chronological, and attachment costs are positive, exactly as in
``OperatorSystem``.  The experiment ``(j, w)`` reads ``L_j M_w v`` and costs
``gamma_j + c(w)``.  Observation ``j`` carries a declared positive rational
noise bound ``sigma_j``: a reading has deterministic additive error at most
``sigma_j`` in absolute value.

Margins
-------
For a difference ``d`` the normalized margin of ``(j, w)`` is
``|L_j M_w d| / sigma_j``.  For a finite candidate family ``v_1..v_k``
(``k >= 2``) the family margin of ``(j, w)`` is the weakest pair under that
single experiment, ``min_{a<b} |L_j M_w (v_a - v_b)| / sigma_j``.

Bounded problem
---------------
Given a budget ``C >= 0``, maximize the margin over every experiment of cost
at most ``C``.  Every attachment cost is at least ``c_min > 0``, so a word of
cost at most ``C`` has length at most ``C / c_min``; there are finitely many
such experiments and the maximum exists whenever one experiment is
affordable (some ``gamma_j <= C``).  Unbounded budgets have no optimum in
general: see ``amplification`` in the tests and research note (SNG-O04).

Pruning bound (proof)
---------------------
Use the vector infinity norm.  For a row ``L`` and column ``v``,
``|L v| = |sum_k L_k v_k| <= sum_k |L_k| |v_k| <= ||L||_1 ||v||_inf``.  For a
matrix ``M``, ``|(M v)_r| <= sum_k |M_rk| |v_k| <= (sum_k |M_rk|) ||v||_inf``,
so ``||M v||_inf <= ||M||_inf ||v||_inf`` with ``||M||_inf`` the maximum
absolute row sum, a nonnegative rational.  Iterating, a suffix word ``u``
satisfies ``||M_u v||_inf <= prod_{i in u} ||M_i||_inf ||v||_inf``.  Put

    kappa(b) = max { prod_{i in u} ||M_i||_inf : cost(u) <= b },  b >= 0,

which is at least 1 because of the empty word.  If the current word ``w``
is extended to ``w.u`` (``M_{w.u} = M_u M_w``) and ``(j, w.u)`` is
affordable, then ``cost(u) <= C - c(w) - gamma_j`` and

    |L_j M_u M_w d| / sigma_j
        <= (||L_j||_1 / sigma_j) * kappa(C - c(w) - gamma_j) * ||M_w d||_inf.

For a family the minimum over pairs is at most the minimum of the per-pair
bounds, so the factor ``||M_w d||_inf`` is replaced by its minimum over the
pair differences.  The node bound is the maximum of this quantity over the
observations still affordable at ``w``; it bounds every experiment in the
subtree of ``w``, including ``w`` itself (``u`` empty).

``kappa`` is computed exactly by dynamic programming: let ``S`` be the
finite set of attachment-cost sums not exceeding ``C`` and
``K(t) = max { prod : cost(u) = t }`` for ``t`` in ``S``.  Then ``K(0) = 1``
and ``K(t) = max_{i : t - c_i in S} K(t - c_i) ||M_i||_inf``, because every
nonempty word of cost ``t`` ends with some letter ``i`` after a prefix of
cost ``t - c_i`` in ``S``, and multiplying by ``||M_i||_inf >= 0`` preserves
the order of prefix products.  Finally ``kappa(b) = max_{t in S, t <= b} K(t)``.

Exactness of branch-and-bound (proof)
-------------------------------------
Nodes are words grown by appending a letter on the state side,
``v_{w.i} = M_i v_w``; a child ``w.i`` is generated only if some observation
is still affordable after it.  Nodes are popped in decreasing bound order; a
node whose bound is at most the incumbent margin is pruned (not expanded),
otherwise its affordable experiments are evaluated and its children pushed.

The incumbent is always the margin of an actually evaluated affordable
experiment, so the returned value is at most the optimum.  Conversely let
``(j, u)`` be any affordable experiment.  Every chronological prefix ``w`` of
``u`` satisfies ``c(w) + gamma_j <= C``, so it is generated unless an earlier
prefix was pruned.  Either every prefix including ``u`` was evaluated, in
which case ``(j, u)`` was evaluated and its margin is at most the final
incumbent, or some prefix ``w`` was pruned with bound at most the incumbent
at that moment, which is at most the final incumbent since the incumbent
only increases; by the pruning bound the margin of ``(j, u)`` is at most the
bound of ``w``.  Hence no affordable experiment beats the returned margin,
which therefore equals the exhaustive optimum.  Termination follows from
finiteness of the affordable words.  Ties are broken differently from the
exhaustive search, so only the value, not the word, is guaranteed equal.

Limitations: the infinity-norm bound can be loose (for instance when
``||M_i||_inf > 1`` but the relevant directions contract), so pruning may be
weak; nothing here optimizes a shared panel of several experiments.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from fractions import Fraction
import heapq
from itertools import count
from typing import Sequence

from .observability import Experiment, OperatorSystem, experiment

Row = tuple[Fraction, ...]

DEFAULT_MAX_NODES = 10**6


def _q(value) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(f"exact rational values must be int or Fraction, not {type(value).__name__}")
    return Fraction(value)


def _sequence(value, name):
    if isinstance(value, (str, bytes, bool)) or not hasattr(value, "__iter__"):
        raise TypeError(f"{name} must be a sequence")
    return tuple(value)


def _vector(values, dimension: int, name: str) -> Row:
    result = tuple(_q(x) for x in _sequence(values, name))
    if len(result) != dimension:
        raise ValueError(f"{name} has the wrong dimension")
    return result


def _system(system) -> OperatorSystem:
    if not isinstance(system, OperatorSystem):
        raise TypeError("system must be an OperatorSystem")
    return system


def _noise(system: OperatorSystem, noise) -> Row:
    sigma = tuple(_q(x) for x in _sequence(noise, "noise"))
    if len(sigma) != len(system.observations):
        raise ValueError("one noise bound is required per observation")
    if any(s <= 0 for s in sigma):
        raise ValueError("noise bounds must be positive")
    return sigma


def _budget(budget) -> Fraction:
    value = _q(budget)
    if value < 0:
        raise ValueError("budget must be nonnegative")
    return value


def _max_nodes(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("max_nodes must be an int")
    if value < 1:
        raise ValueError("max_nodes must be positive")
    return value


def _family_differences(system: OperatorSystem, states) -> tuple[Row, ...]:
    family = tuple(_vector(v, system.dimension, "state") for v in _sequence(states, "states"))
    if len(family) < 2:
        raise ValueError("a candidate family needs at least two states")
    return tuple(tuple(x - y for x, y in zip(family[a], family[b]))
                 for a in range(len(family)) for b in range(a + 1, len(family)))


def _dot(a, b) -> Fraction:
    return sum((x * y for x, y in zip(a, b)), Fraction(0))


def _apply(matrix, vector) -> Row:
    return tuple(_dot(row, vector) for row in matrix)


def row_one_norm(row) -> Fraction:
    """||L||_1, the sum of absolute entries of a row."""
    return sum((abs(_q(x)) for x in row), Fraction(0))


def vector_inf_norm(vector) -> Fraction:
    """||v||_inf, the largest absolute entry (0 for the empty vector)."""
    return max((abs(_q(x)) for x in vector), default=Fraction(0))


def matrix_inf_norm(matrix) -> Fraction:
    """||M||_inf, the maximum absolute row sum (0 for the empty matrix)."""
    return max((row_one_norm(r) for r in matrix), default=Fraction(0))


@dataclass(frozen=True)
class PrunedNode:
    """A subtree discarded by branch-and-bound: the word, its cost, its bound."""
    word: tuple[int, ...]
    cost: Fraction
    bound: Fraction


@dataclass(frozen=True)
class SearchResult:
    """Outcome of a bounded search.

    ``experiment`` and ``margin`` are ``None`` only when no experiment is
    affordable.  ``nodes`` counts search nodes visited (words for
    branch-and-bound, one per observation; experiments for the exhaustive
    oracle, which enumerates each observation separately); ``experiments`` counts the
    experiments ``(j, w)`` whose margins were evaluated; ``pruned`` counts
    discarded subtrees; ``pruned_nodes`` lists them when recording was asked.
    """
    budget: Fraction
    experiment: Experiment | None
    margin: Fraction | None
    nodes: int
    experiments: int
    pruned: int = 0
    pruned_nodes: tuple[PrunedNode, ...] = ()


class _Kappa:
    """kappa(b) = max product of ||M_i||_inf over words of cost <= b."""

    def __init__(self, costs, norms, budget, max_nodes):
        reachable = {Fraction(0)}
        heap = [Fraction(0)]
        while heap:
            t = heapq.heappop(heap)
            for c in costs:
                s = t + c
                if s <= budget and s not in reachable:
                    reachable.add(s)
                    if len(reachable) > max_nodes:
                        raise ValueError("work budget exceeded while computing kappa")
                    heapq.heappush(heap, s)
        self.sums = sorted(reachable)
        best = {}
        for t in self.sums:
            if t == 0:
                best[t] = Fraction(1)
                continue
            best[t] = max(best[t - c] * n for c, n in zip(costs, norms) if (t - c) in best)
        self.exact = best
        self.prefix = []
        running = Fraction(0)
        for t in self.sums:
            running = max(running, best[t])
            self.prefix.append(running)

    def __call__(self, b) -> Fraction:
        k = bisect_right(self.sums, b)
        if k == 0:
            raise ValueError("kappa is defined only for nonnegative remaining budgets")
        return self.prefix[k - 1]


def kappa_table(system: OperatorSystem, budget) -> dict[Fraction, Fraction]:
    """The exact function b -> kappa(b) at every reachable cost sum b <= budget."""
    system, budget = _system(system), _budget(budget)
    k = _Kappa(system.attachment_costs, [matrix_inf_norm(m) for m in system.operators],
               budget, DEFAULT_MAX_NODES)
    return dict(zip(k.sums, k.prefix))


def _margin_of_row(row, differences, sigma) -> Fraction:
    return min(abs(_dot(row, d)) for d in differences) / sigma


def margin(system: OperatorSystem, observation: int, word, difference, noise) -> Fraction:
    """|L_j M_w d| / sigma_j for the experiment (observation, word)."""
    system = _system(system)
    sigma = _noise(system, noise)
    d = _vector(difference, system.dimension, "difference")
    e = experiment(system, observation, word)
    return _margin_of_row(e.row, (d,), sigma[e.observation])


def family_margin(system: OperatorSystem, observation: int, word, states, noise) -> Fraction:
    """min_{a<b} |L_j M_w (v_a - v_b)| / sigma_j, the weakest pair under (j, w)."""
    system = _system(system)
    sigma = _noise(system, noise)
    differences = _family_differences(system, states)
    e = experiment(system, observation, word)
    return _margin_of_row(e.row, differences, sigma[e.observation])


def _exhaustive(system, differences, sigma, budget, max_nodes) -> SearchResult:
    """Every affordable experiment, enumerated row-side by PREPENDING letters
    (L_j M_{(i,w)} = (L_j M_w) M_i), independently of the state-side search."""
    best = None
    nodes = evaluated = 0
    ops, costs = system.operators, system.attachment_costs
    n = system.dimension
    for j, (row0, gamma) in enumerate(zip(system.observations, system.observation_costs)):
        if gamma > budget:
            continue
        stack = [((), row0, gamma)]
        while stack:
            word, row, cost = stack.pop()
            nodes += 1
            evaluated += 1
            if nodes > max_nodes:
                raise ValueError("work budget exceeded in exhaustive search")
            value = _margin_of_row(row, differences, sigma[j])
            if best is None or value > best[0]:
                best = (value, j, word)
            for i in reversed(range(len(ops))):
                c = cost + costs[i]
                if c <= budget:
                    new_row = tuple(sum((row[k] * ops[i][k][col] for k in range(n)), Fraction(0))
                                    for col in range(n))
                    stack.append(((i,) + word, new_row, c))
    if best is None:
        return SearchResult(budget, None, None, nodes, evaluated)
    value, j, word = best
    return SearchResult(budget, experiment(system, j, word), value, nodes, evaluated)


def _branch_and_bound(system, differences, sigma, budget, max_nodes, record) -> SearchResult:
    gammas = system.observation_costs
    affordable = [j for j, g in enumerate(gammas) if g <= budget]
    if not affordable:
        return SearchResult(budget, None, None, 0, 0)
    gmin = min(gammas[j] for j in affordable)
    scale = [row_one_norm(L) / s for L, s in zip(system.observations, sigma)]
    kappa = _Kappa(system.attachment_costs, [matrix_inf_norm(m) for m in system.operators],
                   budget, max_nodes)

    def bound(cost, states):
        weakest = min(vector_inf_norm(v) for v in states)
        if not weakest:
            return Fraction(0)
        return weakest * max(scale[j] * kappa(budget - cost - gammas[j])
                             for j in affordable if gammas[j] + cost <= budget)

    incumbent = None
    best = None
    nodes = evaluated = pruned = 0
    pruned_nodes = []
    serial = count()
    root = tuple(differences)
    heap = [(-bound(Fraction(0), root), next(serial), (), Fraction(0), root)]

    def prune(word, cost, b):
        nonlocal pruned
        pruned += 1
        if record:
            pruned_nodes.append(PrunedNode(word, cost, b))

    while heap:
        negative, _, word, cost, states = heapq.heappop(heap)
        b = -negative
        if incumbent is not None and b <= incumbent:
            prune(word, cost, b)
            continue
        nodes += 1
        if nodes > max_nodes:
            raise ValueError("work budget exceeded in branch-and-bound")
        for j in affordable:
            if gammas[j] + cost > budget:
                continue
            evaluated += 1
            value = min(abs(_dot(system.observations[j], v)) for v in states) / sigma[j]
            if incumbent is None or value > incumbent:
                incumbent, best = value, (j, word)
        for i, (operator, c) in enumerate(zip(system.operators, system.attachment_costs)):
            child_cost = cost + c
            if child_cost + gmin > budget:
                continue
            child_states = tuple(_apply(operator, v) for v in states)
            child_word = word + (i,)
            cb = bound(child_cost, child_states)
            if cb <= incumbent:
                prune(child_word, child_cost, cb)
                continue
            heapq.heappush(heap, (-cb, next(serial), child_word, child_cost, child_states))
    j, word = best
    return SearchResult(budget, experiment(system, j, word), incumbent, nodes, evaluated,
                        pruned, tuple(pruned_nodes))


def exhaustive_margin_search(system, difference, noise, budget, *, max_nodes=DEFAULT_MAX_NODES):
    """Reference oracle: the best pair margin over every experiment of cost <= budget."""
    system = _system(system)
    d = _vector(difference, system.dimension, "difference")
    return _exhaustive(system, (d,), _noise(system, noise), _budget(budget), _max_nodes(max_nodes))


def exhaustive_family_search(system, states, noise, budget, *, max_nodes=DEFAULT_MAX_NODES):
    """Reference oracle for the family margin (weakest pair) under a budget."""
    system = _system(system)
    differences = _family_differences(system, states)
    return _exhaustive(system, differences, _noise(system, noise), _budget(budget),
                       _max_nodes(max_nodes))


def bounded_margin_search(system, difference, noise, budget, *, max_nodes=DEFAULT_MAX_NODES,
                          record_pruned=False):
    """Branch-and-bound for the bounded maximum pair margin; exact by the
    module docstring.  Returns a ``SearchResult``."""
    system = _system(system)
    d = _vector(difference, system.dimension, "difference")
    return _branch_and_bound(system, (d,), _noise(system, noise), _budget(budget),
                             _max_nodes(max_nodes), bool(record_pruned))


def bounded_family_search(system, states, noise, budget, *, max_nodes=DEFAULT_MAX_NODES,
                          record_pruned=False):
    """Branch-and-bound for the bounded maximum family margin (weakest pair)."""
    system = _system(system)
    differences = _family_differences(system, states)
    return _branch_and_bound(system, differences, _noise(system, noise), _budget(budget),
                             _max_nodes(max_nodes), bool(record_pruned))
