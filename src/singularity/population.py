"""Finite constrained labeled populations with exact count, rank and unrank.

The recursion remembers only the assigned graph frontier, accumulated volume
and energy, and extrema.  Its cache therefore shares completion counts when
different prefixes induce the same future problem.  No automorphism quotient
or floating approximation is involved.  Worst-case complexity remains
exponential; the reported state count makes that limitation inspectable.
"""

from __future__ import annotations

from functools import lru_cache
from math import isqrt
from typing import Iterator, Sequence

from .graph import Graph, _integer


def _diameter(graph: Graph) -> int:
    longest = 0
    for start in range(graph.n):
        distance = {start: 0}
        queue = [start]
        for vertex in queue:
            for neighbor in graph.neighbors[vertex]:
                if neighbor not in distance:
                    distance[neighbor] = distance[vertex] + 1
                    queue.append(neighbor)
        if len(distance) != graph.n:
            raise ValueError("diameter bound requires connectedness")
        longest = max(longest, max(distance.values()))
    return longest


class HeightPopulation:
    """A finite, original-labeled population ordered lexicographically.

    ``volume``, ``energy`` and ``span`` request exact values.  Their ``max_``
    forms give upper bounds.  ``min_zero=True`` selects the canonical
    representatives.  Finiteness must follow from an explicit height/volume
    bound, a min-zero span bound, or a connected min-zero energy bound.

    For the last case, if h is the span and D the graph diameter, Cauchy--
    Schwarz along a path from a minimum to a maximum gives h^2 <= D E.
    This is an upper-bound certificate, not an assumed sampling cutoff.
    """

    def __init__(
        self,
        graph: Graph,
        *,
        max_height: int | None = None,
        volume: int | None = None,
        max_volume: int | None = None,
        energy: int | None = None,
        max_energy: int | None = None,
        span: int | None = None,
        max_span: int | None = None,
        min_zero: bool = True,
    ) -> None:
        if not isinstance(graph, Graph):
            raise TypeError("graph must be a Graph")
        if not isinstance(min_zero, bool):
            raise TypeError("min_zero must be a boolean")
        parameters = {
            "max_height": max_height,
            "volume": volume,
            "max_volume": max_volume,
            "energy": energy,
            "max_energy": max_energy,
            "span": span,
            "max_span": max_span,
        }
        for name, value in parameters.items():
            if value is not None:
                _integer(value, name, minimum=0)
        self.graph = graph
        self.constraints = {**parameters, "min_zero": min_zero}
        bounds: list[tuple[str, int]] = []
        if max_height is not None:
            bounds.append(("explicit max_height", max_height))
        if volume is not None:
            bounds.append(("exact total volume", volume))
        if max_volume is not None:
            bounds.append(("upper total volume", max_volume))
        if min_zero:
            if span is not None:
                bounds.append(("exact min-zero span", span))
            if max_span is not None:
                bounds.append(("upper min-zero span", max_span))
            if graph.n == 1:
                bounds.append(("one-vertex min-zero normalization", 0))
        energy_caps = [value for value in (energy, max_energy) if value is not None]
        energy_cap = min(energy_caps) if energy_caps else None
        if min_zero and graph.connected and energy_cap is not None:
            diameter = _diameter(graph)
            bounds.append((f"connected diameter {diameter}: span^2 <= diameter * energy", isqrt(diameter * energy_cap)))
        if not bounds:
            raise ValueError(
                "population is not certified finite: supply max_height or a volume bound; "
                "min-zero populations can also use a span bound or connected energy bound"
            )
        self.height_bound = min(value for _, value in bounds)
        self.bound_certificates = tuple(bounds)
        n, height_bound = graph.n, self.height_bound
        volume_caps = [value for value in (volume, max_volume) if value is not None]
        volume_cap = min(volume_caps) if volume_caps else n * height_bound
        span_caps = [value for value in (span, max_span) if value is not None]
        span_cap = min(span_caps) if span_caps else height_bound

        # Frontier i contains previous labels which still touch an unassigned
        # vertex.  Values of other previous vertices no longer affect energy.
        frontiers = tuple(
            tuple(j for j in range(i) if any(t >= i for t in graph.neighbors[j]))
            for i in range(n + 1)
        )
        previous_neighbors = tuple(
            tuple(j for j in graph.neighbors[i] if j < i) for i in range(n)
        )
        positions = tuple({vertex: p for p, vertex in enumerate(row)} for row in frontiers)
        initial = (0, (), 0, 0, height_bound + 1, -1)

        def advance(state: tuple, value: int) -> tuple:
            i, active, used_volume, used_energy, low, high = state
            lookup = positions[i]
            increment = sum((value - active[lookup[j]]) ** 2 for j in previous_neighbors[i])
            next_active = tuple(
                value if vertex == i else active[lookup[vertex]]
                for vertex in frontiers[i + 1]
            )
            return (
                i + 1,
                next_active,
                used_volume + value,
                used_energy + increment,
                min(low, value),
                max(high, value),
            )

        @lru_cache(maxsize=None)
        def completions(state: tuple) -> int:
            i, active, used_volume, used_energy, low, high = state
            remaining = n - i
            if used_volume > volume_cap:
                return 0
            if volume is not None and used_volume + remaining * height_bound < volume:
                return 0
            if energy_cap is not None and used_energy > energy_cap:
                return 0
            if i and high - low > span_cap:
                return 0
            if remaining == 0:
                return int(
                    (volume is None or used_volume == volume)
                    and (energy is None or used_energy == energy)
                    and (span is None or high - low == span)
                    and (not min_zero or low == 0)
                )
            if min_zero and low > 0 and remaining == 0:
                return 0
            # A total-volume cap also tightens each branch immediately.
            upper = min(height_bound, volume_cap - used_volume)
            return sum(completions(advance(state, value)) for value in range(upper + 1))

        self._initial = initial
        self._advance = advance
        self._completions = completions
        self._frontiers = frontiers

    def count(self) -> int:
        return self._completions(self._initial)

    def __len__(self) -> int:
        """Python may overflow len(); count() always returns the full integer."""
        return self.count()

    def contains(self, values: Sequence[int]) -> bool:
        try:
            a = self.graph.validate_heights(values, nonnegative=True)
        except (TypeError, ValueError):
            return False
        if max(a) > self.height_bound:
            return False
        state = self._initial
        for value in a:
            state = self._advance(state, value)
        return self._completions(state) == 1

    def rank(self, values: Sequence[int]) -> int:
        """Return the zero-based lexicographic rank of a valid original tuple."""
        a = self.graph.validate_heights(values, nonnegative=True)
        if not self.contains(a):
            raise ValueError("height tuple does not satisfy this population's constraints")
        rank = 0
        state = self._initial
        for value in a:
            for smaller in range(value):
                rank += self._completions(self._advance(state, smaller))
            state = self._advance(state, value)
        return rank

    def unrank(self, rank: int) -> tuple[int, ...]:
        """Return the original labeled tuple at a zero-based lexicographic rank."""
        rank = _integer(rank, "rank", minimum=0)
        if rank >= self.count():
            raise IndexError("rank is outside the finite population")
        state = self._initial
        result = []
        for _ in range(self.graph.n):
            for value in range(self.height_bound + 1):
                candidate = self._advance(state, value)
                size = self._completions(candidate)
                if rank < size:
                    result.append(value)
                    state = candidate
                    break
                rank -= size
            else:
                raise ArithmeticError("completion counts failed to locate an in-range rank")
        return tuple(result)

    def iter_tuples(self, limit: int | None = None) -> Iterator[tuple[int, ...]]:
        if limit is not None:
            _integer(limit, "limit", minimum=0)
        stop = self.count() if limit is None else min(limit, self.count())
        for index in range(stop):
            yield self.unrank(index)

    def witness(self, values: Sequence[int]) -> dict[str, object]:
        """Provide exact source-coordinate diagnostics for a candidate witness."""
        a = self.graph.validate_heights(values, nonnegative=True)
        valid = self.contains(a)
        return {
            "heights": list(a),
            "valid": valid,
            "volume": sum(a),
            "energy": self.graph.energy(a),
            "minimum": min(a),
            "span": max(a) - min(a),
            "rank": self.rank(a) if valid else None,
        }

    def to_dict(self, *, sample: int = 3) -> dict[str, object]:
        """JSON-compatible source, constraints, count, bound proof and witnesses."""
        _integer(sample, "sample", minimum=0)
        count = self.count()
        witnesses = [self.witness(a) for a in self.iter_tuples(sample)]
        cache = self._completions.cache_info()
        return {
            "schema": "singularity-height-population/1",
            "graph": self.graph.to_dict(),
            "coordinates": "original labels 0,...,n-1; lexicographic tuple order",
            "constraints": dict(self.constraints),
            "height_bound": self.height_bound,
            "bound_certificates": [
                {"reason": reason, "bound": bound} for reason, bound in self.bound_certificates
            ],
            "count": count,
            "frontier_width": max(map(len, self._frontiers)),
            "cached_states": cache.currsize,
            "cache_hits": cache.hits,
            "witnesses": witnesses,
            "sample_is_complete": sample >= count,
        }


FiniteHeightPopulation = HeightPopulation
