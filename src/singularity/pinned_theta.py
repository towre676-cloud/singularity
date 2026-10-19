"""Exact affine-lattice limits of positively pinned height coefficients.

FR04 is a structural companion to fixed-pinning completeness research.  It
provides necessary full-series invariants, not a completeness criterion.
Every enclosure here is rational. Centered bounds use q=t**(n*n); the
affine-lift bounds instead retain a graph-independent residue factor and
work at every rational q, including the project parameter q=1/2.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import comb

from .graph import Graph, _integer
from .heights import weak_compositions


def _probability(value: Fraction | int, name: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError(f"{name} must be an exact rational integer or Fraction")
    value = Fraction(value)
    if not 0 < value < 1:
        raise ValueError(f"{name} must lie strictly between zero and one")
    return value


def _parameters(graph: Graph, pinning: int) -> int:
    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    return _integer(pinning, "pinning", minimum=1)


def _budget(states: int, maximum: int) -> None:
    maximum = _integer(maximum, "max_states", minimum=1)
    if states > maximum:
        raise ValueError(f"declared state bound {states} exceeds max_states={maximum}")


@dataclass(frozen=True)
class RationalEnclosure:
    """An inclusive rational interval with the number of retained lattice states."""

    lower: Fraction
    upper: Fraction
    terms: int

    @property
    def width(self) -> Fraction:
        return self.upper - self.lower

    def to_dict(self) -> dict[str, object]:
        return {"lower": str(self.lower), "upper": str(self.upper),
                "width": str(self.width), "terms": self.terms}


def pinned_coefficient(graph: Graph, volume: int, pinning: int,
                       q: Fraction | int, *, max_states: int = 100_000) -> Fraction:
    """Compute sum_{h>=0, |h|=volume} q**(E(h)+pinning*||h||^2).

    This small-instance oracle preserves all labeled profiles.  It is not an
    efficient replacement for the graph's separator or locality compilers.
    """
    pinning = _parameters(graph, pinning)
    volume = _integer(volume, "volume", minimum=0)
    q = _probability(q, "q")
    _budget(comb(volume + graph.n - 1, graph.n - 1), max_states)
    return sum((q ** (graph.energy(h) + pinning * sum(a * a for a in h))
                for h in weak_compositions(volume, graph.n)), Fraction())


def scaled_pinned_coefficient(graph: Graph, volume: int, pinning: int,
                              t: Fraction | int, *, max_states: int = 100_000) -> Fraction:
    """Return q**(-pinning*volume**2/n) A_volume(q), q=t**(n*n).

    Centering is performed in integer exponents, without floating-point roots.
    The returned values increase when volume is advanced by exactly n.
    """
    pinning = _parameters(graph, pinning)
    volume = _integer(volume, "volume", minimum=0)
    t = _probability(t, "t")
    n = graph.n
    _budget(comb(volume + n - 1, n - 1), max_states)
    return sum((t ** (n*n*(graph.energy(h) + pinning*sum(a*a for a in h))
                       - n*pinning*volume*volume)
                for h in weak_compositions(volume, n)), Fraction())


def _gaussian_tail(t: Fraction, pinning: int, first: int, step: int) -> Fraction:
    """Bound sum_{m>=0} t**(pinning*(first+step*m)**2), first>0."""
    return t ** (pinning * first * first) / (
        1 - t ** (pinning * (2 * first * step + step * step)))


def _one_coordinate_bound(n: int, residue: int, pinning: int,
                          t: Fraction, half_width: int) -> tuple[Fraction, Fraction]:
    """Full shifted Gaussian upper bound and mass outside [-H,H+1]."""
    lower, upper = -half_width, half_width + 1
    finite = sum((t ** (pinning * (n*z-residue)**2)
                  for z in range(lower, upper + 1)), Fraction())
    outside = (_gaussian_tail(t, pinning, n*(half_width+2)-residue, n)
               + _gaussian_tail(t, pinning, n*(half_width+1)+residue, n))
    return finite + outside, outside


def theta_enclosure(graph: Graph, pinning: int, t: Fraction | int,
                    residue: int, half_width: int, *,
                    max_states: int = 100_000) -> RationalEnclosure:
    """Enclose the complete affine-root-lattice theta invariant Theta_residue.

    Sum all integer z with sum(z)=residue and -H<=z_i<=H+1, then bound the
    omitted lattice states using C=L+pinning*I >= pinning*I and a union bound.
    The bound is rigorous but deliberately inexpensive rather than sharp.
    Each of at most (2H+2)**(n-1) partial states determines its last coordinate.
    """
    pinning = _parameters(graph, pinning)
    t = _probability(t, "t")
    residue = _integer(residue, "residue", minimum=0)
    half_width = _integer(half_width, "half_width", minimum=0)
    n = graph.n
    if residue >= n:
        raise ValueError("residue must be smaller than graph order")
    _budget((2*half_width+2)**(n-1), max_states)
    if n == 1:
        return RationalEnclosure(Fraction(1), Fraction(1), 1)
    lo, hi = -half_width, half_width + 1
    total, terms = Fraction(), 0
    for prefix in product(range(lo, hi+1), repeat=n-1):
        last = residue - sum(prefix)
        if lo <= last <= hi:
            z = prefix + (last,)
            exponent = n*n*graph.energy(z) + pinning*sum((n*a-residue)**2 for a in z)
            total += t ** exponent
            terms += 1
    one, outside = _one_coordinate_bound(n, residue, pinning, t, half_width)
    error = n * one**(n-1) * outside
    return RationalEnclosure(total, total + error, terms)


def boundary_enclosure(graph: Graph, volume: int, pinning: int,
                       t: Fraction | int, *, gaussian_half_width: int = 1,
                       max_states: int = 100_000) -> RationalEnclosure:
    """Enclose Theta_(volume mod n) from one nonnegative-height coefficient.

    Missing centered profiles have a coordinate n*z_i-r <= -(volume+n).
    The returned width is an explicit Gaussian boundary correction.  Values
    in one residue class have the same limit; this is not a tail estimate for
    the unscaled generating series and does not settle full-series equality.
    """
    pinning = _parameters(graph, pinning)
    volume = _integer(volume, "volume", minimum=0)
    t = _probability(t, "t")
    gaussian_half_width = _integer(gaussian_half_width, "gaussian_half_width", minimum=0)
    n = graph.n
    lower = scaled_pinned_coefficient(graph, volume, pinning, t, max_states=max_states)
    terms = comb(volume+n-1, n-1)
    if n == 1:
        return RationalEnclosure(lower, lower, terms)
    one, _ = _one_coordinate_bound(n, volume % n, pinning, t, gaussian_half_width)
    tail = _gaussian_tail(t, pinning, volume+n, n)
    return RationalEnclosure(lower, lower+n*one**(n-1)*tail, terms)


def coefficient_decay_bounds(graph: Graph, volume: int, pinning: int,
                             t: Fraction | int) -> RationalEnclosure:
    """Exact bounds exhibiting the invariant quadratic rate, q=t**(n*n).

    q**(pinning*R**2/n + |E| + pinning*n/4) <= A_R <=
    binomial(R+n-1,n-1) q**(pinning*R**2/n).

    To keep the executable bound integral, replace pinning*n/4 by its ceiling.
    This lower bound uses a balanced profile and is conservative for n=1.
    """
    pinning = _parameters(graph, pinning)
    volume = _integer(volume, "volume", minimum=0)
    t = _probability(t, "t")
    n = graph.n
    central = n * pinning * volume * volume
    additive = len(graph.edges) + (pinning*n+3)//4
    lower = t ** (central+n*n*additive)
    upper = comb(volume+n-1, n-1) * t ** central
    return RationalEnclosure(lower, upper, 1)


def affine_lift_enclosure(graph: Graph, pinning: int, q: Fraction | int,
                          residue: int, half_width: int, *,
                          max_states: int = 100_000) -> RationalEnclosure:
    """Enclose T_r(q)=sum_{sum z=r} q**(E(z)+pinning*||z||^2).

    This graph-independent rescaling of Theta_r works at every rational q,
    including q=1/2, without extracting an algebraic root.  Different graphs
    of the same order can be compared directly in these exact coordinates.
    """
    pinning = _parameters(graph, pinning)
    q = _probability(q, "q")
    residue = _integer(residue, "residue", minimum=0)
    half_width = _integer(half_width, "half_width", minimum=0)
    n = graph.n
    if residue >= n:
        raise ValueError("residue must be smaller than graph order")
    _budget((2*half_width+2)**(n-1), max_states)
    if n == 1:
        return RationalEnclosure(Fraction(1), Fraction(1), 1)
    lo, hi = -half_width, half_width+1
    total, terms = Fraction(), 0
    for prefix in product(range(lo, hi+1), repeat=n-1):
        last = residue-sum(prefix)
        if lo <= last <= hi:
            z = prefix+(last,)
            total += q**(graph.energy(z)+pinning*sum(a*a for a in z))
            terms += 1
    outside = (_gaussian_tail(q, pinning, half_width+2, 1)
               + _gaussian_tail(q, pinning, half_width+1, 1))
    one = sum((q**(pinning*z*z) for z in range(lo, hi+1)), Fraction())+outside
    return RationalEnclosure(total, total+n*one**(n-1)*outside, terms)


def affine_boundary_enclosure(graph: Graph, volume: int, pinning: int,
                                      q: Fraction | int, *,
                                      gaussian_half_width: int = 2,
                                      max_states: int = 100_000) -> RationalEnclosure:
    """Enclose the affine lift T_(R mod n) from one coefficient at rational q.

    The lower endpoint is q**(-pinning*(n*k*k+2*k*r))*A_R, R=n*k+r.
    Its integer exponent makes this route exact at arbitrary rational q.
    """
    pinning = _parameters(graph, pinning)
    volume = _integer(volume, "volume", minimum=0)
    q = _probability(q, "q")
    half_width = _integer(gaussian_half_width, "gaussian_half_width", minimum=0)
    n = graph.n
    k, r = divmod(volume, n)
    _budget(comb(volume+n-1, n-1), max_states)
    shift = pinning*(n*k*k+2*k*r)
    lower = sum((q**(graph.energy(h)+pinning*sum(a*a for a in h)-shift)
                 for h in weak_compositions(volume, n)), Fraction())
    terms = comb(volume+n-1, n-1)
    if n == 1:
        return RationalEnclosure(lower, lower, terms)
    outside = (_gaussian_tail(q, pinning, half_width+2, 1)
               + _gaussian_tail(q, pinning, half_width+1, 1))
    one = sum((q**(pinning*z*z) for z in range(-half_width, half_width+2)), Fraction())+outside
    error = n*one**(n-1)*_gaussian_tail(q, pinning, k+1, 1)
    return RationalEnclosure(lower, lower+error, terms)
