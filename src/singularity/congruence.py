"""Exact volume-residue filters: degree selection and character averaging.

For a modulus m >= 1, a residue a and a finite x-series L whose coefficients
are q-polynomials,

    (1/m) sum_{j=0}^{m-1} w^(-a j) L(w^j x, q) = sum_{v = a mod m} [x^v]L x^v,

where w is a primitive m-th root of unity (SNG-F27).  ``volume_residue``
selects degrees directly.  ``character_average`` evaluates the left side
literally: each twisted series L(w^j x, q) has coefficients in
Z[t]/Phi_m(t) (the exact ring of ``conductor.py``, with t = w), the
weighted twisted series are added in that ring, and only the final sum is
divided by m.  It raises if that sum is not an integer multiple of m times
the identity, so an incomplete character sum can never return fractional
counts.  This filters the volume variable x; it is unrelated to the energy
specialization q = w of ``conductor.py`` and cannot recover span or binary
profiles once those marks have been summed away.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from math import lcm
from typing import Mapping, Sequence

from .conductor import CyclotomicRing
from .graph import Graph, _integer

Series = Sequence[Mapping[int, int | Fraction]]


def _modulus_and_residue(modulus: int, residue: int) -> tuple[int, int]:
    modulus = _integer(modulus, "modulus", minimum=1)
    residue = _integer(residue, "residue")
    return modulus, residue % modulus


def _coefficient(value) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError("series coefficients must be integers or Fractions")
    return Fraction(value)


def volume_residue(series: Series, modulus: int, residue: int) -> list[dict[int, int | Fraction]]:
    """Keep rows v with v = residue (mod modulus); other rows become {}.

    The residue is normalized to 0..modulus-1.  The truncation length is
    unchanged, so a class with no degree in range returns only empty rows.
    """
    modulus, residue = _modulus_and_residue(modulus, residue)
    return [dict(row) if volume % modulus == residue else {} for volume, row in enumerate(series)]


def twisted_series(series: Series, modulus: int, power: int) -> list[dict[int, tuple[int, ...]]]:
    """L(w^power x, q): row v, energy e has coefficient [x^v q^e]L * w^(power v).

    Coefficients are tuples in Z[t]/Phi_modulus(t), constant first, scaled by
    the integer numerator; rational inputs must share denominator one here,
    which ``character_average`` arranges.
    """
    modulus = _integer(modulus, "modulus", minimum=1)
    power = _integer(power, "power")
    ring = CyclotomicRing(modulus)
    rows = []
    for volume, row in enumerate(series):
        phase = ring.phase(power * volume)
        twisted = {}
        for energy, value in row.items():
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("twisted_series expects integer coefficients")
            twisted[energy] = ring.scale(phase, value)
        rows.append(twisted)
    return rows


def character_average(series: Series, modulus: int, residue: int) -> list[dict[int, int | Fraction]]:
    """Evaluate (1/m) sum_j w^(-a j) L(w^j x, q) exactly in Z[t]/Phi_m(t)."""
    modulus, residue = _modulus_and_residue(modulus, residue)
    ring = CyclotomicRing(modulus)
    # Clear denominators so the ring arithmetic is over the integers.
    denominator = lcm(1, *(_coefficient(value).denominator for row in series for value in row.values()))
    integral = [{e: int(_coefficient(c) * denominator) for e, c in row.items()} for row in series]
    totals: list[dict[int, tuple[int, ...]]] = [{} for _ in series]
    for power in range(modulus):
        weight = ring.phase(-residue * power)
        for volume, row in enumerate(twisted_series(integral, modulus, power)):
            target = totals[volume]
            for energy, element in row.items():
                target[energy] = ring.add(target.get(energy, ring.zero), ring.multiply(weight, element))
    result: list[dict[int, int | Fraction]] = []
    for volume, row in enumerate(totals):
        out: dict[int, int | Fraction] = {}
        for energy, element in sorted(row.items()):
            if any(element[1:]):
                raise ArithmeticError(f"character sum left an irrational residue at volume {volume}, energy {energy}")
            if element[0] % modulus:
                raise ArithmeticError(f"character sum is not divisible by the modulus at volume {volume}, energy {energy}")
            value = Fraction(element[0], modulus * denominator)
            if value:
                out[energy] = int(value) if value.denominator == 1 else value
        result.append(out)
    return result


def residue_class_coefficients(graph: Graph, max_volume: int, modulus: int, residue: int) -> list[dict[int, int]]:
    """Count labeled profiles of volume v <= R, v = residue (mod m), by energy.

    Profiles are enumerated directly as tuples in the box {0..R}^n and
    filtered by their own volume; no series operation is involved.
    """
    from itertools import product

    if not isinstance(graph, Graph):
        raise TypeError("graph must be a Graph")
    max_volume = _integer(max_volume, "max_volume", minimum=0)
    modulus, residue = _modulus_and_residue(modulus, residue)
    rows: list[Counter[int]] = [Counter() for _ in range(max_volume + 1)]
    for profile in product(range(max_volume + 1), repeat=graph.n):
        volume = sum(profile)
        if volume <= max_volume and volume % modulus == residue:
            rows[volume][sum((profile[u] - profile[v]) ** 2 for u, v in graph.edges)] += 1
    return [dict(sorted(row.items())) for row in rows]
