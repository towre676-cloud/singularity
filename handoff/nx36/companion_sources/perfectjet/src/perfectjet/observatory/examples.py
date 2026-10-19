"""Small, complete mathematical laboratories for the Observatory.

The examples are generated from formulas; the JSON fixtures are portable copies.
They contain no empirical data or fitted parameters.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import FiniteSystem


def _require_prime(prime: int) -> None:
    if isinstance(prime, bool) or not isinstance(prime, int) or prime < 3:
        raise ValueError("prime must be an odd prime")
    if any(prime % d == 0 for d in range(2, int(prime ** 0.5) + 1)):
        raise ValueError("prime must be an odd prime")


def interferometer_spec(
    prime: int = 13, *, lifted: bool = False, avoid_zero: bool = True
) -> dict[str, Any]:
    """Two noncommuting shears, with a finite-field quadratic sensor.

    In relative coordinates A(u,v)=(u+v,v), B(u,v)=(u,v+u).
    A lifted state (x,y,z) has relative coordinates (x-z,y-z); changing
    all three phases by the same amount cannot affect any future reading.
    With avoid_zero, an action is undefined if its NEXT sensor value is zero.
    The initial state has relative coordinates (1,0).
    """
    _require_prime(prime)
    p = prime
    coords = (
        [(x, y, z) for x in range(p) for y in range(p) for z in range(p)]
        if lifted else [(u, v) for u in range(p) for v in range(p)]
    )
    index = {point: i for i, point in enumerate(coords)}

    def relative(point: tuple[int, ...]) -> tuple[int, int]:
        if lifted:
            x, y, z = point
            return (x - z) % p, (y - z) % p
        return point[0], point[1]

    def sensor(point: tuple[int, ...]) -> int:
        u, v = relative(point)
        return (u * u + v * v) % p

    rows: list[list[int | None]] = []
    for point in coords:
        if lifted:
            x, y, z = point
            images = [((x + y - z) % p, y, z), (x, (y + x - z) % p, z)]
        else:
            u, v = point
            images = [((u + v) % p, v), (u, (v + u) % p)]
        rows.append([
            None if avoid_zero and sensor(image) == 0 else index[image]
            for image in images
        ])
    return {
        "name": f"Arithmetic interferometer F_{p}" + (" — absolute phases" if lifted else " — relative phases"),
        "description": (
            "Order-sensitive arithmetic motion with sensor q=u²+v². "
            "The two shears have identical action inventories but different ordered effects. "
            + ("Global translation and simultaneous sign reversal are invisible. " if lifted else "Simultaneous sign reversal is invisible. ")
            + ("An action that reaches q=0 is blocked." if avoid_zero else "All actions are available.")
        ),
        "states": [",".join(map(str, point)) for point in coords],
        "actions": [{"name": "A", "cost": 1}, {"name": "B", "cost": 1}],
        "transitions": rows,
        "observations": [sensor(point) for point in coords],
        "targets": [sensor(point) for point in coords],
        "accepting": [True] * len(coords),
        "initial": index[(1, 0, 0) if lifted else (1, 0)],
        "mathematics": {
            "prime": p, "lifted": lifted, "avoid_zero": avoid_zero,
            "sensor": "u²+v² mod p", "relative_coordinates": "u=x-z, v=y-z",
            "expected_sign_orbit_count": (p * p + 1) // 2,
        },
    }


def arithmetic_interferometer(
    prime: int = 13, *, lifted: bool = False, avoid_zero: bool = True
) -> FiniteSystem:
    return FiniteSystem.from_dict(interferometer_spec(prime, lifted=lifted, avoid_zero=avoid_zero))


def protocol_spec() -> dict[str, Any]:
    """A branch-sensitive inspection protocol with a two-step adaptive solution.

    The hidden target is a bit. Routing first reveals a device family, after
    which only that family's inspection retains the bit. A wrong inspection
    destroys it, so no universal preset word can replace the adaptive tree.
    """
    states = [f"{phase}:{family}:{bit}" for phase in ("hidden", "routed", "read")
              for family in ("alpha", "beta") for bit in (0, 1)]
    index = {name: i for i, name in enumerate(states)}
    rows: list[list[int | None]] = []
    observations: list[str] = []
    targets: list[int] = []
    for name in states:
        phase, family, text_bit = name.split(":")
        bit = int(text_bit)
        targets.append(bit)
        observations.append("unread" if phase == "hidden" else family if phase == "routed" else f"bit {bit}")
        rows.append([
            index[f"routed:{family}:{bit}"] if phase == "hidden" else None,
            index[f"read:{family}:{bit}"] if phase == "routed" and family == "alpha" else None,
            index[f"read:{family}:{bit}"] if phase == "routed" and family == "beta" else None,
        ])
    return {
        "name": "The branching laboratory",
        "description": "Identify a hidden bit by choosing the second experiment after seeing the first result. A wrong-family inspection irreversibly loses the bit.",
        "states": states,
        "actions": [{"name": "route", "cost": 1}, {"name": "inspect alpha", "cost": 1}, {"name": "inspect beta", "cost": 1}],
        "transitions": rows, "observations": observations, "targets": targets,
        "accepting": [True] * len(states), "initial": 0,
        "initial_belief": [0, 1, 2, 3],
        "mathematics": {"adaptive_worst_cost": 2, "preset_identification_possible": False},
    }


def protocol_machine() -> FiniteSystem:
    return FiniteSystem.from_dict(protocol_spec())


def irreversible_spec() -> dict[str, Any]:
    return {
        "name": "The irreversible button",
        "description": "Inspecting a hidden bit costs three units. Reset costs one unit and merges both possibilities forever. A planner can distinguish cheap motion from useful information.",
        "states": ["hidden 0", "hidden 1", "erased", "read 0", "read 1"],
        "actions": [{"name": "inspect", "cost": 3}, {"name": "reset", "cost": 1}],
        "transitions": [[3, 2], [4, 2], [2, 2], [3, 2], [4, 2]],
        "observations": ["unread", "unread", "erased", "bit 0", "bit 1"],
        "targets": [0, 1, "erased", 0, 1],
        "accepting": [True] * 5, "initial": 0, "initial_belief": [0, 1],
        "mathematics": {"initial_identification_cost": 3, "after_reset_identification_possible": False},
    }


def irreversible_machine() -> FiniteSystem:
    return FiniteSystem.from_dict(irreversible_spec())


def example_catalog() -> dict[str, dict[str, Any]]:
    from .arithmetic import pell_residue_system
    pell_system, transport = pell_residue_system(2, (3, 2), (1, 0), 35, accepted_x=[1])
    pell = pell_system.to_dict()
    pell.update(description="An unbounded integer Pell orbit becomes a finite residue cycle. Count advance/retreat histories returning x to 1 modulo 35, or recover a remote original orbit point.",
                pell={"D": 2, "unit": [3, 2], "seed": [1, 0], "residue_modulus": 35},
                transport=transport)
    specs = {
        "interferometer": interferometer_spec(13, lifted=True),
        "relative-interferometer": interferometer_spec(13),
        "branching-lab": protocol_spec(),
        "irreversible-button": irreversible_spec(),
        "pell-orbit": pell,
    }
    return {
        slug: {"title": spec["name"], "description": spec["description"],
               "model": spec, "initial_belief": spec.get("initial_belief", [spec["initial"]]),
               "default_horizon": 2 if slug == "branching-lab" else 40,
               "comparison_pair": [spec["initial"], 13 if slug == "interferometer" else 1]}
        for slug, spec in specs.items()
    }


def write_example_fixtures(directory: str | Path) -> list[Path]:
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    result = []
    for slug, example in example_catalog().items():
        path = destination / f"{slug}.json"
        path.write_text(json.dumps(example["model"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result.append(path)
    return result
