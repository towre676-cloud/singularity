#!/usr/bin/env python3
"""Receipt for SNG-F36: pendant-cycle pairs checked by independent enumeration.

For every 2 <= p < l <= 7 the first local difference of G(l,p) and G(l,l) is
recomputed by weak compositions; for every 1 <= p < l <= 7 the complete
binary difference is recomputed over all vertex subsets and compared with the
closed form.  ``--check`` compares with the retained file.
"""
import argparse
import json
from pathlib import Path

from singularity.euler import first_difference
from singularity.families import (
    binary_discrepancy_closed_form, binary_discrepancy_enumerated, first_discrepancy, pendant_cycle,
)
from singularity.heights import local_coefficients
from singularity.polynomials import polynomial_to_json

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "results/pendant_family.json"


def compute():
    depth_records, binary_records = [], []
    for l in range(2, 8):
        for p in range(1, l):
            binary = binary_discrepancy_enumerated(l, p)
            binary_records.append({"l": l, "p": p, "closed_form_matches_all_subsets": binary == binary_discrepancy_closed_form(l, p),
                                   "subsets_per_graph": 2 ** (2 * l + 2)})
            if p >= 2:
                a = local_coefficients(pendant_cycle(l, p), p + 1)
                b = local_coefficients(pendant_cycle(l, l), p + 1)
                volume, difference = first_difference(a, b)
                depth_records.append({"l": l, "p": p, "n": 2 * l + 2, "first_difference_volume": volume,
                                      "difference": polynomial_to_json(difference),
                                      "equals_q2_1mq_2_1mq2_p": difference == first_discrepancy(p)})
    return {"schema": "singularity.pendant-family/1", "theorem": "SNG-F36",
            "family": "C_2l with leaves at 0 and p versus at 0 and l",
            "depth_checks": depth_records, "binary_checks": binary_records,
            "interpretation": "finite confirmation of a proved theorem on the listed parameters"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = compute()
    assert all(r["equals_q2_1mq_2_1mq2_p"] and r["first_difference_volume"] == r["p"] + 1 for r in result["depth_checks"])
    assert all(r["closed_form_matches_all_subsets"] for r in result["binary_checks"])
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if TARGET.read_text() != text:
            raise SystemExit("pendant family receipt differs")
        print("Pendant family receipt matches:", len(result["depth_checks"]), "depth checks,", len(result["binary_checks"]), "binary checks")
        return
    TARGET.write_text(text)
    print(len(result["depth_checks"]), len(result["binary_checks"]))


if __name__ == "__main__":
    main()
