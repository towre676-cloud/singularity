#!/usr/bin/env python3
"""Reproduce the Observatory's arithmetic and experimental-design showcases.

The independent safety-count calculations below use arithmetic formulas directly,
without consulting the compiler's model or transitions. Timings describe this
script's recorded workload and are not claims about arbitrary machines.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from collections import defaultdict, deque
import itertools
import json
from pathlib import Path
import sys
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from perfectjet.observatory.model import FiniteSystem, compile_system
from perfectjet.observatory.histories import HistoryPopulation
from perfectjet.observatory.series import compile_series, compile_observable_closure
from perfectjet.observatory.experiments import adaptive_experiment, pair_experiment
from perfectjet.observatory.examples import (
    arithmetic_interferometer, protocol_machine, irreversible_machine,
    write_example_fixtures,
)


def independent_counts(prime: int, horizon: int, *, lifted: bool = False,
                       sign_classes: bool = False) -> list[int]:
    """Integer forward propagation from the formulas, not a compiled model."""
    p = prime
    start = (1, 0, 0) if lifted else (1, 0)
    population = {start: 1}
    totals = []
    for _ in range(horizon + 1):
        totals.append(sum(population.values()))
        following: dict[tuple[int, ...], int] = defaultdict(int)
        for point, weight in population.items():
            if lifted:
                x, y, z = point
                images = [((x + y - z) % p, y, z), (x, (y + x - z) % p, z)]
            else:
                u, v = point
                images = [((u + v) % p, v), (u, (v + u) % p)]
            for image in images:
                u, v = ((image[0] - image[2]) % p, (image[1] - image[2]) % p) if lifted else image
                if (u * u + v * v) % p == 0:
                    continue
                if sign_classes:
                    image = min((u, v), ((-u) % p, (-v) % p))
                following[image] += weight
        population = following
    return totals


def independent_brute_count(prime: int, horizon: int) -> int:
    total = 0
    for word in itertools.product((0, 1), repeat=horizon):
        u, v = 1, 0
        valid = True
        for action in word:
            u, v = (((u + v) % prime, v) if action == 0 else (u, (u + v) % prime))
            if (u * u + v * v) % prime == 0:
                valid = False
                break
        total += valid
    return total


def formula_sign_class(name: str, prime: int) -> tuple[int, int]:
    point = tuple(map(int, name.split(",")))
    u, v = ((point[0] - point[2]) % prime, (point[1] - point[2]) % prime) if len(point) == 3 else point
    return min((u, v), ((-u) % prime, (-v) % prime))


def independent_reachable(prime: int) -> set[tuple[int, int]]:
    states = {(1, 0)}
    frontier = [(1, 0)]
    while frontier:
        u, v = frontier.pop()
        for point in [((u + v) % prime, v), (u, (v + u) % prime)]:
            if sum(x * x for x in point) % prime and point not in states:
                states.add(point)
                frontier.append(point)
    return states



def independent_remote_count(prime: int, index: int, modulus: int) -> int:
    """Direct modular matrix powering on independently derived sign orbits.

    This does not read the quotient, its recurrence, or any series coefficients.
    It therefore supplies a separate algorithm for the astronomically distant
    population query, while never expanding its exponentially many histories.
    """
    canonical = lambda point: min(point, ((-point[0]) % prime, (-point[1]) % prime))
    points = sorted({canonical(point) for point in independent_reachable(prime)})
    position = {point: i for i, point in enumerate(points)}
    dimension = len(points)
    matrix = [[0] * dimension for _ in points]
    for row, (u, v) in enumerate(points):
        for point in [((u + v) % prime, v), (u, (v + u) % prime)]:
            if sum(x*x for x in point) % prime:
                matrix[row][position[canonical(point)]] += 1
    vector = [int(point == canonical((1, 0))) for point in points]
    exponent = index
    while exponent:
        columns = list(zip(*matrix))
        if exponent & 1:
            vector = [sum(a*b for a, b in zip(vector, column)) % modulus for column in columns]
        exponent >>= 1
        if exponent:
            matrix = [[sum(a*b for a, b in zip(row, column)) % modulus
                       for column in columns] for row in matrix]
    return sum(vector) % modulus

def preset_identification_search(system: FiniteSystem, belief: list[int]) -> dict[str, Any]:
    """Exhaust all preset-word monitors, retaining complete observation traces.

    A missing transition enters one absorbing undefined state and never drops
    a hypothesis. Initial target labels remain attached to each hypothesis.
    This search is independent of the adaptive planner.
    """
    labels = [system.targets[state] for state in belief]

    def canonical_partition(keys: list[Any]) -> tuple[int, ...]:
        seen: dict[Any, int] = {}
        return tuple(seen.setdefault(key, len(seen)) for key in keys)

    initial_partition = canonical_partition([json.dumps(system.observations[s], sort_keys=True) for s in belief])
    start = (tuple(belief), initial_partition)
    queue = deque([(start, ())])
    seen = {start}
    while queue:
        (states, partition), word = queue.popleft()
        if all(labels[i] == labels[j] for i in range(len(belief)) for j in range(i)
               if partition[i] == partition[j]):
            return {"status": "finite", "word": list(word), "explored_monitors": len(seen)}
        for action in range(system.alphabet):
            following = tuple(None if state is None else system.transitions[state][action] for state in states)
            observed = [(partition[i], "undefined" if state is None else json.dumps(system.observations[state], sort_keys=True))
                        for i, state in enumerate(following)]
            monitor = following, canonical_partition(observed)
            if monitor not in seen:
                seen.add(monitor)
                queue.append((monitor, word + (system.actions[action],)))
    return {"status": "infinite", "explored_monitors": len(seen)}



def independent_polynomial_gcd_degree(left: list[int], right: list[int]) -> int:
    """Euclidean algorithm over Q, used to check the scalar GF is reduced."""
    def trim(values: list[Fraction]) -> list[Fraction]:
        while values and values[-1] == 0:
            values.pop()
        return values
    a, b = trim(list(map(Fraction, left))), trim(list(map(Fraction, right)))
    while b:
        remainder = a[:]
        while len(remainder) >= len(b):
            shift = len(remainder) - len(b)
            multiple = remainder[-1] / b[-1]
            for i, value in enumerate(b):
                remainder[i + shift] -= multiple * value
            trim(remainder)
        a, b = b, remainder
    return len(a) - 1

def run_benchmark(*, prime: int = 13, horizon: int = 80, remote_index: int = 10**100,
                  modulus: int = 1_000_000_007) -> dict[str, Any]:
    if prime != 13:
        raise ValueError("The retained benchmark uses prime=13; create a separate record for other fields.")
    timings: dict[str, float] = {}
    began = perf_counter()
    original = arithmetic_interferometer(prime, lifted=True)
    timings["build_lift_seconds"] = perf_counter() - began
    began = perf_counter()
    compilation = compile_system(original)
    timings["compile_lift_seconds"] = perf_counter() - began
    quotient = compilation.system
    expected = (prime * prime + 1) // 2
    assert quotient.n == expected

    # Check the compiler's COMPLETE partition against the independently derived
    # translation/sign orbit relation, rather than only checking its size.
    block_to_sign: dict[int, tuple[int, int]] = {}
    sign_to_block: dict[tuple[int, int], int] = {}
    for i, name in enumerate(original.states):
        block, sign = compilation.mapping[i], formula_sign_class(name, prime)
        assert block_to_sign.setdefault(block, sign) == sign
        assert sign_to_block.setdefault(sign, block) == block

    began = perf_counter()
    absolute_counts = independent_counts(prime, horizon, lifted=True)
    relative_counts = independent_counts(prime, horizon)
    orbit_counts = independent_counts(prime, horizon, sign_classes=True)
    timings["independent_three_coordinate_counts_seconds"] = perf_counter() - began
    assert absolute_counts == relative_counts == orbit_counts
    began = perf_counter()
    compiled_counts = [HistoryPopulation(quotient, depth).count() for depth in range(horizon + 1)]
    timings["compiled_history_counts_seconds"] = perf_counter() - began
    assert compiled_counts == absolute_counts

    brute_counts = [independent_brute_count(5, depth) for depth in range(13)]
    assert brute_counts == independent_counts(5, 12)
    p5 = arithmetic_interferometer(5)
    for depth, expected_count in enumerate(brute_counts):
        population = HistoryPopulation(p5, depth)
        count = population.count()
        assert count == expected_count
        if count:
            for rank in sorted({0, count // 2, count - 1}):
                assert population.rank(population.unrank(rank)) == rank

    began = perf_counter()
    series = compile_series(quotient)
    timings["compile_series_seconds"] = perf_counter() - began
    for depth, expected_count in enumerate(absolute_counts):
        assert series.coefficient(depth) == expected_count
    began = perf_counter()
    distant = series.coefficient(remote_index, modulus=modulus)
    timings["remote_modular_query_seconds"] = perf_counter() - began
    began = perf_counter()
    direct_distant = independent_remote_count(prime, remote_index, modulus)
    timings["independent_remote_matrix_power_seconds"] = perf_counter() - began
    assert distant == direct_distant


    began = perf_counter()
    sensor_closure = compile_observable_closure(quotient, [quotient.observations])
    acceptance_closure = compile_observable_closure(quotient)
    timings["compile_two_ordered_observable_closures_seconds"] = perf_counter() - began
    assert sensor_closure.dimension == 57 and acceptance_closure.dimension == 15
    source_replays = 0
    for closure, seeds in ((sensor_closure, (quotient.accepting, quotient.observations)),
                           (acceptance_closure, (quotient.accepting,))):
        for basis_vector, (seed, word) in zip(closure.basis, closure.basis_sources):
            for state in range(quotient.n):
                current = state
                for action in word:
                    current = None if current is None else quotient.transitions[current][action]
                expected_value = 0 if current is None else seeds[seed][current]
                assert basis_vector[state] == expected_value
                source_replays += 1


    relative_model = arithmetic_interferometer(prime)
    same_sensor_distinct_future = pair_experiment(relative_model, prime, 1)
    antipodal_indistinguishable = pair_experiment(relative_model, prime, (prime - 1) * prime)
    assert same_sensor_distinct_future["status"] == "finite" and same_sensor_distinct_future["cost"] == 1
    assert antipodal_indistinguishable["status"] == "infinite"

    protocol = protocol_machine()
    adaptive = adaptive_experiment(protocol, belief=[0, 1, 2, 3])
    preset = preset_identification_search(protocol, [0, 1, 2, 3])
    assert adaptive["status"] == "finite" and adaptive["worst_cost"] == 2
    assert preset["status"] == "infinite"
    erased = irreversible_machine()
    inspect = pair_experiment(erased, 0, 1)
    assert inspect["status"] == "finite" and inspect["cost"] == 3
    assert erased.transitions[0][1] == erased.transitions[1][1] == 2

    reachable = independent_reachable(prime)
    sign_reachable = {min(point, ((-point[0]) % prime, (-point[1]) % prime)) for point in reachable}
    record = series.record()
    if hasattr(record, "to_dict"):
        record = record.to_dict()
    gcd_degree = independent_polynomial_gcd_degree(record["numerator"], record["denominator"])
    assert gcd_degree == 0
    return {
        "schema": "perfectjet-observatory-benchmark/1", "prime": prime,
        "scope": "Exact finite-field example; no empirical or predictive performance claim.",
        "history_semantics": {"initial_absolute_state": [1, 0, 0], "initial_sensor": 1,
                              "all_terminal_states_accepting": True,
                              "constraint": "Each next sensor value must be nonzero; a step to q=0 is undefined.",
                              "scope": "Counts start at this fixed nonzero state. Arbitrary zero starts are not asserted safe."},
        "model": {"absolute_states": original.n, "relative_states": prime**2,
                  "quotient_states": quotient.n, "reachable_relative_states": len(reachable),
                  "reachable_quotient_states": len(sign_reachable),
                  "partition_matches_independent_translation_sign_orbits": True,
                  "compression_ratio": original.n / quotient.n},
        "safe_history_counts": {str(depth): count for depth, count in enumerate(absolute_counts)},
        "independent_checks": {"absolute_relative_and_sign_counts_agree_through": horizon,
                               "complete_word_enumeration_prime": 5,
                               "complete_word_enumeration_through": 12,
                               "complete_word_count": sum(2**n for n in range(13)),
                               "rank_unrank_roundtrips": True},
        "order_witness": {"initial_relative": [1, 0], "AB_terminal_relative": [1, 1],
                          "BA_terminal_relative": [2, 1], "AB_observation": 2,
                          "BA_observation": 5, "same_action_histogram": True},
        "ordered_numeric_sensor_closure": sensor_closure.record(),
        "ordered_acceptance_closure": acceptance_closure.record(),
        "demand_compression": {
            "absolute_state_count": original.n,
            "label_preserving_quotient_state_count": quotient.n,
            "ordered_numeric_sensor_dimension": sensor_closure.dimension,
            "ordered_acceptance_dimension": acceptance_closure.dimension,
            "aggregated_length_count_vector_dimension": record["closure_dimension"],
            "generating_function_denominator_degree": len(record["denominator"]) - 1,
            "scalar_gf_numerator_denominator_gcd_degree": gcd_degree,
            "fixed_initial_minimal_scalar_order": len(record["denominator"]) - 1,
            "global_and_scalar_distinction": "The all-state vector identity uses 8 coordinates. The fixed-start scalar generating function is coprime with denominator degree7; its zero-mode contribution vanishes.",
            "ordered_basis_source_evaluations_replayed": source_replays,
            "meaning": "The required answer determines how much structure must survive: all future labels, ordered numeric readings, ordered safety, or counts by length.",
            "rank_scope": "Exact rational vector dimensions, not approximate numerical ranks."
        },
        "series": record,
        "remote_query": {"index": str(remote_index), "modulus": modulus, "residue": distant,
                         "independent_matrix_power_agrees": True},
        "pair_experiments": {
            "same_current_sensor_different_future": same_sensor_distinct_future,
            "antipodal_states_identical_for_every_future_word": antipodal_indistinguishable,
            "cost_scope": "Exact minimum summed action cost among separating words. Equal current sensor values alone do not establish behavioral equivalence."
        },
        "adaptive_protocol": {"adaptive": adaptive, "preset_word_search": preset,
                              "meaning": "Two adaptive actions identify the bit; exhaustive finite monitor search finds no preset word that can identify it."},
        "irreversible_button": {"best_initial_pair_experiment": inspect,
                                "reset_merges_both_hypotheses_to": 2,
                                "meaning": "After reset the initial bit cannot affect any future observation."},
        "timings_seconds": timings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results/observatory/benchmark.json")
    parser.add_argument("--horizon", type=int, default=80)
    parser.add_argument("--write-examples", action="store_true")
    args = parser.parse_args()
    if args.write_examples:
        write_example_fixtures(ROOT / "examples/observatory")
    result = run_benchmark(horizon=args.horizon)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "model": result["model"],
                      "horizon": args.horizon, "count": result["safe_history_counts"][str(args.horizon)],
                      "remote_query": result["remote_query"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
