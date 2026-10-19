"""Exact constrained populations of action histories without word enumeration."""
from __future__ import annotations

from collections import defaultdict
import random
from typing import Any, Iterable

from .model import FiniteSystem, _integer, labels_equal, scalar_key


class PopulationLimitError(ValueError):
    """The requested dynamic program exceeds its explicit state allowance."""


class HistoryPopulation:
    """Length-exact, cost-bounded accepted words in original action order.

    ``trace`` has one sensor value per visited time, including time zero.
    ``None`` is a wildcard.  Costs constrain the sum along a word, and final
    acceptance is checked only at its terminal state.  Different action words
    remain different population members even when their state paths coincide.
    """

    MAX_HORIZON = 512
    MAX_DP_STATES = 1_000_000

    def __init__(self, system: FiniteSystem, horizon: int, budget: int | None = None,
                 start: int | None = None, trace: Iterable[Any] | None = None):
        if not isinstance(system, FiniteSystem):
            raise ValueError("system must be a FiniteSystem")
        _integer(horizon, "horizon")
        if horizon > self.MAX_HORIZON:
            raise ValueError(f"horizon must be at most {self.MAX_HORIZON}")
        if budget is not None:
            _integer(budget, "budget")
        if start is None:
            start = system.initial
        _integer(start, "start state")
        if start >= system.n:
            raise ValueError("start state outside state range")
        if trace is None:
            normalized_trace = (None,) * (horizon + 1)
        else:
            if isinstance(trace, (str, bytes, dict)):
                raise ValueError("trace must be an array of sensor labels or null wildcards")
            try:
                normalized_trace = tuple(trace)
            except TypeError as error:
                raise ValueError("trace must be an array") from error
            if len(normalized_trace) != horizon + 1:
                raise ValueError("trace must contain horizon + 1 observations")
            for label in normalized_trace:
                scalar_key(label)
        self.system, self.horizon, self.budget = system, horizon, budget
        self.start, self.trace = start, normalized_trace
        self._minimum_action_cost = min(system.costs, default=1)
        self._maximum_action_cost = max(system.costs, default=0)
        # Sufficiently generous budgets carry no information; dropping that
        # coordinate can reduce a large query from quadratic to linear size.
        effective_budget = budget
        if budget is not None and budget >= horizon * self._maximum_action_cost:
            effective_budget = None
        self._root = (horizon, start, effective_budget)
        self._cache: dict[tuple[int, int, int | None], int] = {}
        self._seen: set[tuple[int, int, int | None]] = set()
        self._histogram: dict[int, int] | None = None
        self._histogram_cells = 0

    def _trace_matches(self, remaining: int, state: int) -> bool:
        expected = self.trace[self.horizon - remaining]
        return expected is None or labels_equal(expected, self.system.observations[state])

    def _terminal_value(self, key: tuple[int, int, int | None]) -> int | None:
        remaining, state, budget = key
        if not self._trace_matches(remaining, state):
            return 0
        if budget is not None and budget < remaining * self._minimum_action_cost:
            return 0
        if remaining == 0:
            return int(self.system.accepting[state])
        if self.system.alphabet == 0:
            return 0
        return None

    def _child(self, key: tuple[int, int, int | None], action: int) -> tuple[int, int, int | None] | None:
        remaining, state, budget = key
        target = self.system.transitions[state][action]
        if remaining == 0 or target is None:
            return None
        cost = self.system.costs[action]
        if budget is not None and cost > budget:
            return None
        return (remaining - 1, target, None if budget is None else budget - cost)

    def _count_from(self, root: tuple[int, int, int | None]) -> int:
        if root in self._cache:
            return self._cache[root]
        # Explicit postorder evaluation: horizon 512 never consumes the
        # interpreter's recursion stack.  Repeated edges share a cached cell.
        stack = [(root, False)]
        self._register(root)
        while stack:
            key, expanded = stack.pop()
            if key in self._cache:
                continue
            terminal = self._terminal_value(key)
            if terminal is not None:
                self._cache[key] = terminal
                continue
            if expanded:
                self._cache[key] = sum(self._cache[child] for action in range(self.system.alphabet)
                                       if (child := self._child(key, action)) is not None)
                continue
            stack.append((key, True))
            for action in range(self.system.alphabet):
                child = self._child(key, action)
                if child is not None and child not in self._cache:
                    self._register(child)
                    # Duplicated stack entries are harmless, and are needed
                    # when a transposition is pending below another branch.
                    stack.append((child, False))
        return self._cache[root]

    def _register(self, key: tuple[int, int, int | None]) -> None:
        if key not in self._seen:
            if len(self._seen) >= self.MAX_DP_STATES:
                raise PopulationLimitError(f"history query exceeds {self.MAX_DP_STATES:,} dynamic states")
            self._seen.add(key)

    def count(self) -> int:
        return self._count_from(self._root)

    def _word(self, word: Iterable[int | str]) -> tuple[int, ...]:
        if isinstance(word, (str, bytes, dict)):
            raise ValueError("word must be an array of action names or indices")
        try:
            actions = tuple(self.system.action_index(action) for action in word)
        except TypeError as error:
            raise ValueError("word must be an array of actions") from error
        if len(actions) != self.horizon:
            raise ValueError("word length must equal the population horizon")
        return actions

    def rank(self, word: Iterable[int | str]) -> int:
        actions = self._word(word)
        if self.count() == 0:
            raise ValueError("word is not a member of the empty population")
        rank, key = 0, self._root
        for chosen in actions:
            for action in range(chosen):
                child = self._child(key, action)
                if child is not None:
                    rank += self._count_from(child)
            child = self._child(key, chosen)
            if child is None or self._count_from(child) == 0:
                raise ValueError("word violates transition, trace, budget or acceptance constraints")
            key = child
        if not self._cache.get(key, self._terminal_value(key)):
            raise ValueError("word is not accepted")
        return rank

    def unrank(self, rank: int) -> tuple[int, ...]:
        _integer(rank, "rank")
        population = self.count()
        if rank >= population:
            raise ValueError("rank outside population")
        key, word = self._root, []
        for _ in range(self.horizon):
            for action in range(self.system.alphabet):
                child = self._child(key, action)
                subtotal = 0 if child is None else self._count_from(child)
                if rank < subtotal:
                    word.append(action)
                    key = child
                    break
                rank -= subtotal
            else:
                raise AssertionError("count/unrank disagreement")
        return tuple(word)

    def sample(self, rng: random.Random | None = None) -> tuple[int, ...]:
        population = self.count()
        if population == 0:
            raise ValueError("cannot sample an empty population")
        if rng is None:
            rng = random.SystemRandom()
        return self.unrank(rng.randrange(population))

    def cost_histogram(self) -> dict[int, int]:
        """Map total cost to its exact population, including trace/budget."""
        if self._histogram is not None:
            return dict(self._histogram)
        if not self._trace_matches(self.horizon, self.start):
            self._histogram = {}
            return {}
        layer = {(self.start, 0): 1}
        cells = 1
        for elapsed in range(self.horizon):
            next_layer: dict[tuple[int, int], int] = defaultdict(int)
            remaining = self.horizon - elapsed - 1
            for (state, total_cost), multiplicity in layer.items():
                for action, target in enumerate(self.system.transitions[state]):
                    if target is None or not self._trace_matches(remaining, target):
                        continue
                    cost = total_cost + self.system.costs[action]
                    if self.budget is not None and cost + remaining * self._minimum_action_cost > self.budget:
                        continue
                    key = (target, cost)
                    if key not in next_layer:
                        cells += 1
                        if cells > self.MAX_DP_STATES:
                            raise PopulationLimitError(f"cost histogram exceeds {self.MAX_DP_STATES:,} dynamic states")
                    next_layer[key] += multiplicity
            layer = next_layer
            if not layer:
                break
        histogram: dict[int, int] = defaultdict(int)
        for (state, cost), multiplicity in layer.items():
            if self.system.accepting[state]:
                histogram[cost] += multiplicity
        self._histogram = dict(sorted(histogram.items()))
        self._histogram_cells = cells
        return dict(self._histogram)

    def minimum_cost(self) -> int | None:
        """Min-plus dynamic program; does not materialize a cost histogram."""
        if not self._trace_matches(self.horizon, self.start):
            return None
        layer = {self.start: 0}
        cells = 1
        for elapsed in range(self.horizon):
            next_layer: dict[int, int] = {}
            remaining = self.horizon - elapsed - 1
            for state, total_cost in layer.items():
                for action, target in enumerate(self.system.transitions[state]):
                    if target is None or not self._trace_matches(remaining, target):
                        continue
                    cost = total_cost + self.system.costs[action]
                    if self.budget is not None and cost > self.budget:
                        continue
                    if target not in next_layer or cost < next_layer[target]:
                        next_layer[target] = cost
            cells += len(next_layer)
            if cells > self.MAX_DP_STATES:
                raise PopulationLimitError(f"minimum-cost query exceeds {self.MAX_DP_STATES:,} dynamic states")
            layer = next_layer
            if not layer:
                return None
        feasible = [cost for state, cost in layer.items() if self.system.accepting[state]]
        return min(feasible, default=None)

    @property
    def metrics(self) -> dict[str, Any]:
        value = self._cache.get(self._root)
        return {"horizon": self.horizon, "budget": self.budget, "start": self.start,
                "dynamic_states": len(self._seen), "cache_entries": len(self._cache),
                "histogram_states": self._histogram_cells,
                "count_bits": None if value is None else value.bit_length(),
                "word_enumeration": False}
