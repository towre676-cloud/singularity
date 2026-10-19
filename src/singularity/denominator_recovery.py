"""Recover an extremal graph invariant from one rational local coefficient.

The decoder receives no graph, adjacency, polynomial support, or marked data.
Its input is the graph order, the exact rational pinning, and one coefficient
of the raw nonnegative-height series L.  See FR02_DENOMINATOR_RECOVERY.md for
the gap theorem, including the essential lower-degree-spike case.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import comb, gcd

from .graph import _integer


def _rational(value: object, name: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(f"{name} must be an exact integer or Fraction")
    return Fraction(value)


def recovery_volume(order: int, q: Fraction) -> int:
    """Least R >= 2 with denominator(q)**(2*(R-1)) > order.

    Every larger volume is also valid.  This is an observation cutoff, not a
    bound on the cost of computing the supplied coefficient.
    """
    order = _integer(order, "order", minimum=1)
    q = _rational(q, "q")
    if not 0 < q < 1:
        raise ValueError("q must lie strictly between zero and one")
    base = q.denominator
    volume, power = 2, base * base
    while power <= order:
        volume += 1
        power *= base * base
    return volume


def denominator_depth(denominator: int, base: int, *, max_depth: int | None = None) -> int:
    """Least k for which denominator divides base**k, without factorization.

    Reject a denominator containing a prime factor absent from base.  The
    optional limit rejects excessive clearing depth before building powers.
    Composite bases are supported: this is not a prime-adic valuation.
    """
    denominator = _integer(denominator, "denominator", minimum=1)
    base = _integer(base, "base", minimum=2)
    if max_depth is not None:
        max_depth = _integer(max_depth, "max_depth", minimum=0)
    depth = 0
    while denominator > 1:
        if max_depth is not None and depth >= max_depth:
            raise ValueError("denominator clearing depth exceeds the declared bound")
        divisor = gcd(denominator, base)
        if divisor == 1:
            raise ValueError("denominator has a prime factor absent from the pinning denominator")
        denominator //= divisor
        depth += 1
    return depth


@dataclass(frozen=True)
class DegreeExtremum:
    """Exact decoded invariant and its arithmetic certificate parameters."""

    order: int
    q: Fraction
    volume: int
    maximum_degree: int
    multiplicity: int
    diagonal_shift: int
    denominator_depth: int
    maximum_energy: int
    energy_gap: int
    modulus: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "order": self.order,
            "q": str(self.q),
            "volume": self.volume,
            "maximum_degree": self.maximum_degree,
            "multiplicity": self.multiplicity,
            "diagonal_shift": self.diagonal_shift,
            "denominator_depth": self.denominator_depth,
            "maximum_energy": self.maximum_energy,
            "energy_gap": self.energy_gap,
            "modulus": self.modulus,
        }


def recover_degree_extremum(
    order: int,
    q: Fraction,
    coefficient: Fraction,
    *,
    volume: int | None = None,
    diagonal_shift: int = 0,
) -> DegreeExtremum:
    """Recover (maximum degree, its multiplicity) from [x**R] L_G(x,q).

    Preconditions: G is a finite simple graph of the supplied positive order,
    q is an exact rational in (0,1), and the supplied coefficient is raw L's
    coefficient at R.  The default R is recovery_volume(order,q).  A supplied
    R must satisfy the same strict cutoff.  The checks reject several invalid
    inputs but do not recognize every coefficient realizable by a graph.
    With integer diagonal_shift=lambda>=0, the coefficient instead belongs to
    sum_h x**sum(h) q**(E_G(h)+lambda*sum(h_i**2)); lambda=2 is the existing
    dominating-terminal interior sequence A_H.
    """
    order = _integer(order, "order", minimum=1)
    q = _rational(q, "q")
    if not 0 < q < 1:
        raise ValueError("q must lie strictly between zero and one")
    coefficient = _rational(coefficient, "coefficient")
    diagonal_shift = _integer(diagonal_shift, "diagonal_shift", minimum=0)
    if volume is None:
        volume = recovery_volume(order, q)
    volume = _integer(volume, "volume", minimum=2)
    a, b = q.numerator, q.denominator
    if b ** (2 * (volume - 1)) <= order:
        raise ValueError("volume is below the strict denominator recovery cutoff")
    profiles = comb(order + volume - 1, volume)
    if not 0 < coefficient <= profiles:
        raise ValueError("coefficient lies outside the positive population bound")
    square = volume * volume
    depth = denominator_depth(
        coefficient.denominator, b, max_depth=(order - 1 + diagonal_shift) * square
    )
    leading_diagonal = (depth + square - 1) // square
    degree = leading_diagonal - diagonal_shift
    if degree < 0:
        raise ValueError("coefficient is incompatible with the declared diagonal shift")
    if leading_diagonal == 0:
        if coefficient != profiles:
            raise ValueError("an integer coefficient at this cutoff must be the edgeless coefficient")
        return DegreeExtremum(order, q, volume, 0, order, 0, 0, 0, 0, 1)
    maximum_energy = leading_diagonal * square
    gap = min(square, 2 * leading_diagonal * (volume - 1))
    modulus = b ** gap
    scaled = coefficient * b ** maximum_energy
    if scaled.denominator != 1:
        raise ValueError("coefficient fails the inferred energy denominator bound")
    multiplicity = (scaled.numerator * pow(pow(a, maximum_energy, modulus), -1, modulus)) % modulus
    if not 1 <= multiplicity <= order:
        raise ValueError("coefficient has no admissible extremal multiplicity")
    return DegreeExtremum(
        order, q, volume, degree, multiplicity, diagonal_shift, depth,
        maximum_energy, gap, modulus,
    )


def reconstruct_complete_split(
    order: int,
    q: Fraction,
    coefficient: Fraction,
    *,
    volume: int | None = None,
    diagonal_shift: int = 0,
) -> tuple[int, int]:
    """Recover canonical (clique size, independent size) in the known family.

    The family is K_c joined to an independent set of size order-c.  The
    complete graph is represented canonically by (order,0), including order 1.
    This family membership is a caller-supplied hypothesis, not certified here.
    """
    result = recover_degree_extremum(
        order, q, coefficient, volume=volume, diagonal_shift=diagonal_shift
    )
    if result.maximum_degree == 0:
        return (order, 0) if order == 1 else (0, order)
    if result.maximum_degree != order - 1:
        raise ValueError("invariant is incompatible with a nonempty complete split graph")
    if result.multiplicity == order:
        return order, 0
    return result.multiplicity, order - result.multiplicity
