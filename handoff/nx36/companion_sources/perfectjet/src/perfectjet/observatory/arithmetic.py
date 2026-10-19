"""Transport a seeded Pell orbit into exact finite observable dynamics.

This module compiles one supplied orbit of x^2-D*y^2=N.  It does not claim that
one seed represents every integer solution of the norm equation.  A generator
need not be fundamental; that distinction is recorded explicitly.
"""
from __future__ import annotations

from math import isqrt, comb
from typing import Any, Iterable

from ..quadratic import fundamental_unit
from .model import FiniteSystem


class ArithmeticOrbitLimitError(ValueError):
    """The finite orbit exceeds the explicitly requested state allowance."""


def _integer(value: Any, name: str, minimum: int | None = None) -> int:
    if type(value) is not int or (minimum is not None and value < minimum):
        suffix = "" if minimum is None else f" >= {minimum}"
        raise ValueError(f"{name} must be an integer{suffix}.")
    return value


def _pair(value: Iterable[int], name: str) -> tuple[int, int]:
    if isinstance(value, (str, bytes, dict)):
        raise ValueError(f"{name} must be a pair of integers.")
    try:
        result = tuple(value)
    except TypeError as error:
        raise ValueError(f"{name} must be a pair of integers.") from error
    if len(result) != 2 or any(type(component) is not int for component in result):
        raise ValueError(f"{name} must be a pair of integers.")
    return result


def _validate(D: int, unit: Iterable[int], seed: Iterable[int]) -> tuple[tuple[int, int], tuple[int, int]]:
    _integer(D, "D", 1)
    if isqrt(D) ** 2 == D:
        raise ValueError("D must be nonsquare.")
    a, b = _pair(unit, "unit")
    origin = _pair(seed, "seed")
    if a <= 1 or b <= 0:
        raise ValueError("unit must have a > 1 and b > 0; retreat uses its exact inverse.")
    if a * a - D * b * b != 1:
        raise ValueError("unit must satisfy a^2 - D*b^2 = 1 exactly.")
    return (a, b), origin


def _multiply(left: tuple[int, int], right: tuple[int, int], D: int,
              modulus: int | None = None) -> tuple[int, int]:
    x = left[0] * right[0] + D * left[1] * right[1]
    y = left[0] * right[1] + left[1] * right[0]
    return (x, y) if modulus is None else (x % modulus, y % modulus)


def pell_point(D: int, unit: Iterable[int], seed: Iterable[int], n: int,
               modulus: int | None = None, *, max_bits: int = 1_000_000) -> tuple[int, int]:
    """Compute seed*(a+b*sqrt(D))**n by exact binary powering.

    Negative indices use a-b*sqrt(D).  A modulus permits arbitrarily remote
    indices without constructing the enormous original integers.  ``max_bits``
    is a conservative allocation guard for requests without a modulus.
    """
    (a, b), origin = _validate(D, unit, seed)
    _integer(n, "n")
    if modulus is not None:
        _integer(modulus, "modulus", 1)
    else:
        _integer(max_bits, "max_bits", 1)
        # The infinity norm grows by at most the largest absolute row sum
        # of the Pell matrix (the inverse has the same absolute row sums).
        # A zero seed remains zero even at an enormous index.
        if origin != (0, 0):
            bound = max(abs(origin[0]).bit_length(), abs(origin[1]).bit_length()) + 2
            bound += abs(n) * max(a + D*b, a + b).bit_length()
            if bound > max_bits:
                raise ArithmeticOrbitLimitError("Original coordinates exceed max_bits; request modular coordinates or increase max_bits.")
    if origin == (0, 0):
        return (0, 0)
    base = (a, -b if n < 0 else b)
    exponent = abs(n)
    result = (1, 0)
    if modulus is not None:
        base = base[0] % modulus, base[1] % modulus
        result = 1 % modulus, 0
        origin = origin[0] % modulus, origin[1] % modulus
    while exponent:
        if exponent & 1:
            result = _multiply(result, base, D, modulus)
        exponent >>= 1
        if exponent:
            base = _multiply(base, base, D, modulus)
    return _multiply(origin, result, D, modulus)


def pell_residue_system(
    D: int,
    unit: Iterable[int],
    seed: Iterable[int],
    modulus: int,
    accepted_x: int | Iterable[int] | None = None,
    *,
    costs: tuple[int, int] = (1, 1),
    max_states: int = 100_000,
) -> tuple[FiniteSystem, dict[str, Any]]:
    """Compile the complete reachable seed orbit modulo ``modulus``.

    Actions ``advance`` and ``retreat`` multiply by the supplied norm-one unit
    and its inverse.  The sensor reads x modulo the modulus.  Accepted endpoints
    have x in ``accepted_x`` modulo that same modulus; ``None`` accepts all.
    The return value is ``(system, transport_record)``.
    """
    (a, b), origin = _validate(D, unit, seed)
    _integer(modulus, "modulus", 1)
    _integer(max_states, "max_states", 1)
    try:
        cost_pair = tuple(costs)
    except TypeError as error:
        raise ValueError("costs must contain two positive integer action costs.") from error
    if len(cost_pair) != 2:
        raise ValueError("costs must contain two positive integer action costs.")
    for cost in cost_pair:
        _integer(cost, "action cost", 1)
    if accepted_x is None:
        accepted = None
    else:
        if type(accepted_x) is int:
            values = (accepted_x,)
        else:
            if isinstance(accepted_x, (str, bytes, dict)):
                raise ValueError("accepted_x must be an integer or iterable of integers.")
            try:
                values = tuple(accepted_x)
            except TypeError as error:
                raise ValueError("accepted_x must be an integer or iterable of integers.") from error
        for value in values:
            _integer(value, "accepted_x residue")
        accepted = frozenset(value % modulus for value in values)

    start = origin[0] % modulus, origin[1] % modulus
    orbit: list[tuple[int, int]] = []
    visited: dict[tuple[int, int], int] = {}
    current = start
    while current not in visited:
        if len(orbit) >= max_states:
            raise ArithmeticOrbitLimitError(f"The Pell residue orbit exceeds max_states={max_states}.")
        visited[current] = len(orbit)
        orbit.append(current)
        current = _multiply(current, (a, b), D, modulus)
    # Determinant one makes the action invertible over every Z/modulus Z,
    # including composite moduli, so a forward orbit cannot have a transient.
    if current != start:
        raise AssertionError("An invertible Pell action unexpectedly has a transient.")
    period = len(orbit)
    transitions = tuple(((i + 1) % period, (i - 1) % period) for i in range(period))
    inverse_checked = all(
        _multiply(point, (a, b), D, modulus) == orbit[transitions[i][0]]
        and _multiply(point, (a, -b), D, modulus) == orbit[transitions[i][1]]
        for i, point in enumerate(orbit)
    )
    if not inverse_checked:
        raise AssertionError("Pell residue transport failed its forward/inverse replay.")
    acceptance = tuple(accepted is None or point[0] in accepted for point in orbit)
    system = FiniteSystem(
        states=tuple(f"({x},{y})" for x, y in orbit),
        actions=("advance", "retreat"), costs=cost_pair,
        transitions=transitions, observations=tuple(x for x, _ in orbit),
        targets=tuple(f"({x},{y})" for x, y in orbit), accepting=acceptance,
        name=f"Pell orbit x² − {D}y² = {origin[0] ** 2 - D * origin[1] ** 2} (mod {modulus})",
        initial=0,
    )
    norm = origin[0] ** 2 - D * origin[1] ** 2
    fundamental = fundamental_unit(D)
    norm_coefficients = [a * a - D * b * b, 2 * a * D * b - 2 * D * a * b,
                         D * D * b * b - D * a * a]
    record = {
        "D": D, "seed": list(origin), "original_norm": norm, "modulus": modulus,
        "unit": {"a": a, "b": b, "norm": a * a - D * b * b,
                 "fundamental_unit": list(fundamental), "is_fundamental": (a, b) == fundamental},
        "forward_matrix": [[a, D * b], [b, a]],
        "inverse_matrix": [[a, -D * b], [-b, a]],
        "determinant": a * a - D * b * b,
        "characteristic_coefficients_ascending": [1, -2 * a, 1],
        "coordinate_recurrence": f"z[n+2] = {2*a}*z[n+1] - z[n]",
        "symbolic_norm_coefficients_x2_xy_y2": norm_coefficients,
        "expected_norm_coefficients_x2_xy_y2": [1, 0, -D],
        "period": period, "preperiod": 0,
        "orbit_index_classes": [{"index": i, "x": x, "y": y, "accepting": acceptance[i]}
                                 for i, (x, y) in enumerate(orbit)],
        "accepted_x": None if accepted is None else sorted(accepted),
        "accepted_index_classes": [i for i, value in enumerate(acceptance) if value],
        "certificate": {
            "symbolic_norm_preserved": norm_coefficients == [1, 0, -D],
            "forward_inverse_replayed": inverse_checked,
            "all_residues_have_seed_norm": all((x*x-D*y*y-norm) % modulus == 0 for x, y in orbit),
            "closed_cycle": current == start,
            "distinct_cycle_states": len(set(orbit)) == period,
        },
        "completeness": {
            "scope": "Exactly the finite residue orbit generated by the supplied seed and supplied unit/inverse.",
            "covers_all_integer_norm_solutions": False,
            "index_transport": "The integer orbit point at index n maps to cycle state n modulo period.",
            "generator_warning": None if (a, b) == fundamental else
                "The supplied unit is a proper power of the fundamental unit; only its generated seed orbit is compiled.",
        },
    }
    return system, record


def arithmetic_receipt() -> dict[str, Any]:
    """A reproducible bridge from an unbounded Pell orbit to exact histories."""
    from .histories import HistoryPopulation

    D, unit, seed, modulus = 2, (3, 2), (1, 0), 35
    system, transport = pell_residue_system(D, unit, seed, modulus, accepted_x=[1])
    direct = seed
    replayed = True
    samples = []
    for n in range(51):
        fast = pell_point(D, unit, seed, n)
        replayed = replayed and fast == direct and (fast[0]*fast[0]-D*fast[1]*fast[1] == 1)
        if n in (0, 1, 2, 10, 50):
            samples.append({"index": n, "x": str(fast[0]), "y": str(fast[1])})
        direct = _multiply(direct, unit, D)
    remote_n, remote_modulus = 10 ** 100, 1_000_000_007
    remote = pell_point(D, unit, seed, remote_n, remote_modulus)
    residue = pell_point(D, unit, seed, remote_n, modulus)
    period = transport["period"]
    indexed = transport["orbit_index_classes"][remote_n % period]
    horizon = 100
    population = HistoryPopulation(system, horizon)
    count = population.count()
    # Independently count words by their number of advances.  Their net Pell
    # exponent is 2*k-horizon; each such fiber has binomial(horizon,k) words.
    binomial_count = sum(comb(horizon, k) for k in range(horizon + 1)
                         if system.accepting[(2*k-horizon) % period])
    return {
        "name": "Unbounded Pell orbit → finite observable cycle → exact history population",
        "transport": transport,
        "integer_replay": {"checked_indices": [0, 50], "all_equal": replayed, "samples": samples},
        "remote_query": {"index": str(remote_n), "modulus": remote_modulus,
                         "x": remote[0], "y": remote[1],
                         "norm_replayed": (remote[0]**2-D*remote[1]**2-1) % remote_modulus == 0,
                         "cycle_index_mod_35": remote_n % period,
                         "cycle_transport_replayed": residue == (indexed["x"], indexed["y"])},
        "history_query": {"horizon": horizon, "accepted_x_mod_35": [1],
                          "all_action_words": str(2 ** horizon), "accepted_action_words": str(count),
                          "independent_binomial_count": str(binomial_count),
                          "independent_count_agrees": count == binomial_count,
                          "interpretation": "Counts action words with an accepted endpoint, not distinct integer Pell solutions."},
    }
