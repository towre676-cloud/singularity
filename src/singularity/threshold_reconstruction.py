"""Exact fixed-rational reconstruction in the promised threshold-graph class.

Only the order, pinning, uniform diagonal shift, and a coefficient prefix are
read.  The input graph, its degree sequence, and an isomorphism oracle are not
available to the inverse algorithm.  Arithmetic operation counts do not bound
the bit cost of the exact rational coefficients.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from .denominator_recovery import _rational, recover_degree_extremum, recovery_volume
from .graph import Graph, _integer


def _prefix(values: Sequence[Fraction]) -> tuple[Fraction, ...]:
    result = tuple(_rational(value, "coefficient") for value in values)
    if not result or result[0] != 1:
        raise ValueError("a coefficient prefix must start with constant coefficient one")
    if any(value < 0 for value in result):
        raise ValueError("population coefficients must be nonnegative")
    return result


def _convolve(a: Sequence[Fraction], b: Sequence[Fraction]) -> tuple[Fraction, ...]:
    return tuple(sum((a[j] * b[r - j] for j in range(r + 1)), Fraction()) for r in range(len(a)))


def isolated_factor(count: int, q: Fraction, volume: int, diagonal_shift: int = 0) -> tuple[Fraction, ...]:
    """Prefix of (sum_h x**h q**(lambda*h*h))**count."""
    count = _integer(count, "count", minimum=0)
    volume = _integer(volume, "volume", minimum=0)
    diagonal_shift = _integer(diagonal_shift, "diagonal_shift", minimum=0)
    q = _rational(q, "q")
    if not 0 < q < 1:
        raise ValueError("q must lie strictly between zero and one")
    one = (Fraction(1),) + (Fraction(),) * volume
    single = tuple(q ** (diagonal_shift * h * h) for h in range(volume + 1))
    result = one
    for _ in range(count):
        result = _convolve(result, single)
    return result


def remove_isolated(prefix: Sequence[Fraction], count: int, q: Fraction, diagonal_shift: int = 0) -> tuple[Fraction, ...]:
    """Divide by the known isolated-vertex factor, in the finite series ring."""
    a = _prefix(prefix)
    factor = isolated_factor(count, q, len(a) - 1, diagonal_shift)
    b = [Fraction(1)]
    for r in range(1, len(a)):
        b.append(a[r] - sum((factor[j] * b[r - j] for j in range(1, r + 1)), Fraction()))
    return tuple(b)


def universal_weights(order: int, count: int, q: Fraction, volume: int, diagonal_shift: int = 0) -> tuple[Fraction, ...]:
    """Universal-clique transform weights for a graph of the full order."""
    order = _integer(order, "order", minimum=1)
    count = _integer(count, "count", minimum=1)
    if count > order:
        raise ValueError("universal-vertex count exceeds the full order")
    volume = _integer(volume, "volume", minimum=0)
    diagonal_shift = _integer(diagonal_shift, "diagonal_shift", minimum=0)
    q = _rational(q, "q")
    if not 0 < q < 1:
        raise ValueError("q must lie strictly between zero and one")
    values = isolated_factor(count, q, volume, order + diagonal_shift)
    return tuple(value * q ** (-j * j) for j, value in enumerate(values))


def attach_universal(prefix: Sequence[Fraction], order: int, count: int, q: Fraction, diagonal_shift: int = 0) -> tuple[Fraction, ...]:
    """Forward K_count join transform; input has diagonal shift lambda+count."""
    b = _prefix(prefix)
    c = universal_weights(order, count, q, len(b) - 1, diagonal_shift)
    return tuple(sum((c[j] * q ** (-2 * j * (r - j)) * b[r - j] for j in range(r + 1)), Fraction()) for r in range(len(b)))


def remove_universal(prefix: Sequence[Fraction], order: int, count: int, q: Fraction, diagonal_shift: int = 0) -> tuple[Fraction, ...]:
    """Invert the unit-triangular join transform at the same volume budget."""
    a = _prefix(prefix)
    c = universal_weights(order, count, q, len(a) - 1, diagonal_shift)
    b = [Fraction(1)]
    for r in range(1, len(a)):
        b.append(a[r] - sum((c[j] * q ** (-2 * j * (r - j)) * b[r - j] for j in range(1, r + 1)), Fraction()))
    return tuple(b)


def graph_from_creation_word(word: Sequence[int]) -> Graph:
    """Create a threshold graph: 0 adds an isolate, 1 a universal vertex."""
    bits = tuple(_integer(bit, "creation bit", minimum=0) for bit in word)
    if not bits or any(bit > 1 for bit in bits):
        raise ValueError("a creation word must be nonempty and binary")
    return Graph(len(bits), ((i, j) for j, bit in enumerate(bits) if bit for i in range(j)))


@dataclass(frozen=True)
class ThresholdReconstruction:
    graph: Graph
    creation_word: tuple[int, ...]
    volume: int
    q: Fraction
    diagonal_shift: int
    steps: tuple[dict[str, int | str], ...]

    def to_dict(self) -> dict[str, object]:
        return {"graph": self.graph.to_dict(), "creation_word": list(self.creation_word),
                "volume": self.volume, "q": str(self.q), "diagonal_shift": self.diagonal_shift,
                "steps": list(self.steps), "class_hypothesis": "threshold graph"}


def reconstruct_threshold(order: int, q: Fraction, prefix: Sequence[Fraction], *, diagonal_shift: int = 0) -> ThresholdReconstruction:
    """Reconstruct a promised threshold graph up to isomorphism.

    The supplied prefix must reach recovery_volume(order,q); longer prefixes
    are accepted and used throughout.  This does not decide whether arbitrary
    input data belong to a threshold graph.  Incompatible arithmetic detected
    during peeling is rejected; the class hypothesis remains essential.
    """
    order = _integer(order, "order", minimum=1)
    diagonal_shift = _integer(diagonal_shift, "diagonal_shift", minimum=0)
    q = _rational(q, "q")
    required = recovery_volume(order, q)
    a = _prefix(prefix)
    volume = len(a) - 1
    if volume < required:
        raise ValueError("coefficient prefix is shorter than the strict reconstruction cutoff")
    steps: list[dict[str, int | str]] = []

    # Peeling is iterative: the theorem is not limited by Python's recursion
    # depth for threshold graphs with many alternating creation layers.
    layers: list[tuple[int, ...]] = []
    n, shift, values = order, diagonal_shift, a
    while n:
        decoded = recover_degree_extremum(n, q, values[volume], volume=volume, diagonal_shift=shift)
        degree, multiplicity = decoded.maximum_degree, decoded.multiplicity
        if not 0 <= degree < n:
            raise ValueError("decoded degree is incompatible with the residual order")
        if degree == 0:
            expected = isolated_factor(n, q, volume, shift)
            if values != expected:
                raise ValueError("edgeless residual prefix fails its exact identity")
            steps.append({"order": n, "shift": shift, "operation": "edgeless", "removed": n})
            layers.append((0,) * n)
            n = 0
            values = (Fraction(1),) + (Fraction(),) * volume
            break
        if degree < n - 1:
            count = n - degree - 1
            steps.append({"order": n, "shift": shift, "operation": "isolated", "removed": count})
            values = remove_isolated(values, count, q, shift)
            layers.append((0,) * count)
            n -= count
            continue
        steps.append({"order": n, "shift": shift, "operation": "universal", "removed": multiplicity})
        values = remove_universal(values, n, multiplicity, q, shift)
        layers.append((1,) * multiplicity)
        n -= multiplicity
        shift += multiplicity
    if any(values[1:]):
        raise ValueError("empty residual graph has a nonconstant prefix")
    word = tuple(bit for layer in reversed(layers) for bit in layer)
    # The first vertex has no earlier vertices; choose its unique convention.
    word = (0,) + word[1:]
    return ThresholdReconstruction(graph_from_creation_word(word), word, volume, q, diagonal_shift, tuple(steps))
