"""Retain exact FR01 examples; no sampled agreement is a completeness claim."""
from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path

from singularity.graph import Graph
from singularity.pole_divisors import (
    anchored_gaussian_box, divisor_sum_profile, pole_order_certificate,
    recover_component_sizes, theta_upper,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "fr01_pole_divisors.json"


def rational(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {str(key): rational(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [rational(item) for item in value]
    return value


def receipt():
    edge = Graph(2, [(0, 1)])
    triangle = Graph(3, [(0, 1), (1, 2), (0, 2)])
    mixed = Graph(5, [(0, 1), (2, 3), (3, 4), (2, 4)])
    examples = []
    for label, graph, q, order, cutoff in (
        ("edge_at_minus_one", edge, Fraction(1, 2), 2, 4),
        ("triangle_at_primitive_third_root", triangle, Fraction(1, 3), 3, 3),
    ):
        box = anchored_gaussian_box(graph, q, order, cutoff)
        assert all(c == 0 for c in box.coefficients[1:])
        lower = box.coefficients[0] - box.absolute_error
        assert lower > 0
        examples.append({"label": label, "n": graph.n, "edges": graph.edges,
                         "q": q, "root_order": order, "cutoff": cutoff,
                         "profiles": box.profiles,
                         "cyclotomic_coefficients": box.coefficients,
                         "absolute_error": box.absolute_error,
                         "positive_rational_lower_bound": lower})
    sizes = (1, 1, 2, 3, 3, 6)
    profile = divisor_sum_profile(sizes)
    return rational({
        "schema": "singularity.frontier-pole-divisors/1",
        "theorems": {
            "connected": "Every nth root is a simple pole for connected n-vertex graphs, 0<q<1",
            "disconnected_at_one": "Pole order at x=1 equals connected-component count",
            "small_q": "If theta_upper(q)^(N-1)<2, all component numerators of sizes <=N are unit-disk zero-free",
            "uniform_size": "Divisor inversion is also valid at every 0<q<1 when nontrivial components all have one size",
        },
        "gaussian_enclosures": examples,
        "small_q_bound": {"q": Fraction(1, 16), "N": 6,
                           "theta_upper": theta_upper(Fraction(1, 16)),
                           "strict_power_less_than_two": theta_upper(Fraction(1, 16))**5 < 2},
        "mixed_component_scope": [pole_order_certificate(mixed, Fraction(1, 16)),
                                  pole_order_certificate(mixed, Fraction(1, 2))],
        "divisor_inversion": {"component_sizes": sizes, "pole_orders": profile,
                              "recovered_multiplicities": recover_component_sizes(profile),
                              "scope": "analytic pole orders must be justified independently; q=1/16 certifies sizes<=6"},
        "not_claimed": ["general-q disconnected noncancellation", "fixed-quadratic-pinning completeness",
                        "finite-prefix cutoff", "formal proof-assistant verification"],
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = json.dumps(receipt(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != content:
            raise SystemExit("FR01 retained receipt differs; regenerate and inspect")
        print("FR01 exact Gaussian enclosures, scope refusals and divisor inversion agree")
    else:
        OUTPUT.write_text(content)
        print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
