#!/usr/bin/env python3
"""NX08 receipt: exact target-recovery conditioning, sensor layouts and forecasts.

Writes results/target_recovery.json.  ``--check`` recomputes everything,
compares it byte-for-byte with the retained JSON, replays every stored
``singularity.target-recovery/1`` receipt, and runs independent oracles that
do not use the module's elimination (principal minors by permutation
expansion, brute-force catalogue optima, direct adversarial replays).
Timings are printed and never retained.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
from itertools import combinations, permutations
import hashlib
import json
from pathlib import Path
import random
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from singularity import target_recovery as tr  # noqa: E402
from singularity.target_recovery import (  # noqa: E402
    PSDCertificate, SensorOption, TargetRecoveryProblem, adversarial_witness,
    amplification_form, bracket_decoder_norm, bracket_target_amplification,
    certify_decoder_norm, cheapest_conditioned_layout, cheapest_identifying_layout,
    conditioning_frontier, layout_problem, layout_table, linear_forecast_problem,
    minimum_norm_decoder, psd_certificate, target_identifiability, target_recovery_receipt,
    thermal_target_problem, verify_psd_certificate, verify_target_recovery_receipt)

TARGET = ROOT / "results" / "target_recovery.json"
TOL = F(1, 10 ** 6)


def enc(value):
    if isinstance(value, F):
        return [value.numerator, value.denominator]
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, dict):
        return {str(k): enc(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [enc(v) for v in value]
    raise TypeError(type(value))


# ------------------------------ independent oracles ------------------------------

def perm_det(a):
    n = len(a)
    total = F(0)
    for perm in permutations(range(n)):
        sign = (-1) ** sum(1 for i in range(n) for j in range(i + 1, n) if perm[i] > perm[j])
        term = F(sign)
        for i in range(n):
            term *= a[i][perm[i]]
        total += term
    return total


def psd_by_minors(a):
    n = len(a)
    return all(perm_det([[a[i][j] for j in idx] for i in idx]) >= 0
               for size in range(1, n + 1) for idx in combinations(range(n), size))


def bracket_json(br):
    return {"status": br.status, "lower": br.lower, "upper": br.upper,
            "lower_witness": br.lower_witness, "hidden_witness": br.hidden_witness,
            "upper_zero_pivots": None if br.upper_certificate is None else br.upper_certificate.zero_pivots}


# ------------------------------------- NX08-A -------------------------------------

def unit_a():
    examples = {}
    receipts = {}
    g = [(0, 1)]
    cases = {
        "H_a_diag_1_1/100": TargetRecoveryProblem([(1, 0), (0, F(1, 100))], g),
        "H_b_identity": TargetRecoveryProblem([(1, 0), (0, 1)], g),
        "hidden_target_H_10": TargetRecoveryProblem([(1, 0)], g),
        "constrained_x2_eq_2x1": TargetRecoveryProblem([(1, 0)], g, [(1,), (2,)]),
        "zero_target_no_sensors": TargetRecoveryProblem([], [(0, 0)]),
        "nonzero_target_no_sensors": TargetRecoveryProblem([], [(1, 0)]),
        "zero_dimensional_admissible": TargetRecoveryProblem([(1, 1)], [(3, 4)], [(), ()], centre=(1, 2)),
        "irrational_two_row_target": TargetRecoveryProblem(
            [(1, 1, 0), (0, 1, 1), (1, 0, 2), (0, 0, 1)], [(1, 2, 3), (0, 1, -1)],
            [(1, 0), (0, 1), (1, 1)], units={"state": "K", "observations": "K", "target": "K"}),
    }
    for name, problem in cases.items():
        br = bracket_target_amplification(problem, TOL)
        row = bracket_json(br)
        row["rank"] = target_identifiability(problem).rank
        if br.status != "unobservable":
            dec = minimum_norm_decoder(problem)
            cert = certify_decoder_norm(problem, dec, br.upper)
            assert isinstance(cert, tr.DecoderCertificate)
            rows = target_identifiability(problem).decoder
            nr = bracket_decoder_norm(problem, rows, TOL)
            row["minimum_norm_decoder"] = dec
            row["row_space_decoder"] = rows
            row["row_space_decoder_gain_squared"] = [nr.lower, nr.upper]
            receipts[name] = target_recovery_receipt(problem, br, cert, {"unit": "NX08-A", "example": name})
        else:
            receipts[name] = target_recovery_receipt(problem, br, None, {"unit": "NX08-A", "example": name})
        examples[name] = row
    eps2 = F(1, 10 ** 6)
    guarantee = {name: examples[name]["upper"] * eps2 for name in ("H_a_diag_1_1/100", "H_b_identity")}
    # Deterministic population of tiny symmetric matrices, many singular.
    rng = random.Random(20261019)
    agree = psd = singular_psd = 0
    for trial in range(600):
        n = rng.randint(1, 4)
        rank = rng.randint(0, n)
        m = [[rng.randint(-2, 2) for _ in range(n)] for _ in range(rank)]
        s = [[F(sum(m[t][i] * m[t][j] for t in range(rank))) for j in range(n)] for i in range(n)]
        if trial % 3 == 0:
            i, j = rng.randrange(n), rng.randrange(n)
            s[i][j] += F(rng.randint(-1, 1), rng.randint(1, 3))
            s[j][i] = s[i][j]
        cert = psd_certificate(s)
        oracle = psd_by_minors(s)
        assert isinstance(cert, PSDCertificate) == oracle, s
        if oracle:
            assert verify_psd_certificate(s, cert)
            psd += 1
            singular_psd += bool(cert.zero_pivots)
        else:
            z = cert.vector
            assert sum(z[i] * s[i][j] * z[j] for i in range(n) for j in range(n)) < 0
        agree += 1
    return {"examples": examples,
            "target_error_squared_at_eps_1/1000": guarantee,
            "psd_oracle_population": {"matrices": agree, "psd": psd, "psd_with_zero_pivot": singular_psd,
                                      "seed": 20261019, "oracle": "all principal minors, permutation expansion"},
            "receipts": receipts}


def tamper_count(receipts):
    """Targeted edits that always falsify a claim (an edit that leaves a
    different but still valid receipt, e.g. an L entry under a zero pivot, is
    not tampering).  Q is doubled (S scales by 4, so the stored LDL fails unless
    S = 0); a decoder entry facing a nonzero row of H0 is incremented (L H0
    changes); the first positive LDL pivot is doubled (entry S_jj changes)."""
    import copy
    rejected = total = 0

    def rehash(r):
        r["problem_sha256"] = tr._digest(r["problem"])
        r["admissible_basis_sha256"] = tr._digest(r["problem"]["admissible_basis"])

    for name, receipt in receipts.items():
        if receipt["status"] == "unobservable":
            continue
        variants = []
        diag = receipt["amplification_squared"]["upper_ldl"]["diagonal"]
        positive = [i for i, x in enumerate(diag) if x[0] > 0]
        if positive:
            r = copy.deepcopy(receipt)
            for row in r["problem"]["admissible_basis"]["entries"]:
                for x in row:
                    value = 2 * F(x[0], x[1])
                    x[0], x[1] = value.numerator, value.denominator
            variants.append(r)
            r = copy.deepcopy(receipt)
            cell = r["amplification_squared"]["upper_ldl"]["diagonal"][positive[0]]
            value = 2 * F(cell[0], cell[1])
            cell[0], cell[1] = value.numerator, value.denominator
            variants.append(r)
        h = receipt["problem"]["observations"]["entries"]
        q = receipt["problem"]["admissible_basis"]["entries"]
        h0_nonzero = [j for j, row in enumerate(h)
                      if any(sum(F(*row[t]) * F(*q[t][c]) for t in range(len(row)))
                             for c in range(len(q[0]) if q else 0))]
        if h0_nonzero:
            for section, field in (("identifiability", "row_space_decoder"), ("decoder", "matrix")):
                if section in receipt and receipt[section][field]["entries"]:
                    r = copy.deepcopy(receipt)
                    cell = r[section][field]["entries"][0][h0_nonzero[0]]
                    cell[0] += cell[1]
                    variants.append(r)
        for r in variants:
            rehash(r)
            total += 1
            rejected += not verify_target_recovery_receipt(r)
    return {"tampered": total, "rejected": rejected}


# ------------------------------------- NX08-B -------------------------------------

CATALOGUE_RAW = (
    ("cheap_x1", ((1, 0, 0),), 1, (1,)),
    ("cheap_x1_weak_x2", ((1, F(1, 50), 0),), 1, (1,)),
    ("direct_x2", ((0, 1, 0),), 5, (1,)),
    ("pair_x2x3_x3", ((0, 1, 1), (0, 0, 1)), 3, (1, 4)),
    ("cheap_x3", ((0, 0, 1),), 1, (1,)),
    ("noisy_sum", ((1, 1, 1),), 2, (9,)),
)
CATALOGUE_TARGET = ((0, 1, 0),)
THRESHOLDS = (F(1, 2), F(2, 3), 1, F(3, 2), 2, 5, 12, 100, 5000)


def catalogue():
    return tuple(SensorOption(name, rows, cost,
                              [[w if i == j else 0 for j in range(len(rows))] for i, w in enumerate(shape)],
                              "K")
                 for name, rows, cost, shape in CATALOGUE_RAW)


def brute_force(kappa2):
    """From raw rows only; kappa2 None means the kernel condition."""
    best = None
    d = 3
    for size in range(len(CATALOGUE_RAW) + 1):
        for layout in combinations(range(len(CATALOGUE_RAW)), size):
            pairs = [(row, F(w)) for i in layout for row, w in zip(CATALOGUE_RAW[i][1], CATALOGUE_RAW[i][3])]
            a = [[sum(F(r[i]) * r[j] / w for r, w in pairs) for j in range(d)] for i in range(d)]
            b = [[sum(F(t[i]) * t[j] for t in CATALOGUE_TARGET) for j in range(d)] for i in range(d)]
            if kappa2 is None:
                # For PSD A, B: ker(A + B) = ker A cap ker B, so the kernel
                # condition ker A in ker B is rank(A) = rank(A + B), by minors.
                ok = rank_by_minors(a) == rank_by_minors([[a[i][j] + b[i][j] for j in range(d)] for i in range(d)])
            else:
                ok = psd_by_minors([[kappa2 * a[i][j] - b[i][j] for j in range(d)] for i in range(d)])
            if ok:
                key = (sum(F(CATALOGUE_RAW[i][2]) for i in layout), len(layout), layout)
                best = key if best is None or key < best else best
    return best


def rank_by_minors(a):
    n = len(a)
    for size in range(n, 0, -1):
        for rows in combinations(range(n), size):
            for cols in combinations(range(n), size):
                if perm_det([[a[i][j] for j in cols] for i in rows]):
                    return size
    return 0


def unit_b():
    options = catalogue()
    table = layout_table(options, CATALOGUE_TARGET, tolerance=TOL)
    comparisons = []
    for kappa2 in (None,) + THRESHOLDS:
        if kappa2 is None:
            pruned = cheapest_identifying_layout(options, CATALOGUE_TARGET)
            full = cheapest_identifying_layout(options, CATALOGUE_TARGET, method="exhaustive")
        else:
            pruned = cheapest_conditioned_layout(options, CATALOGUE_TARGET, kappa2)
            full = cheapest_conditioned_layout(options, CATALOGUE_TARGET, kappa2, method="exhaustive")
        brute = brute_force(kappa2)
        assert (pruned.status, pruned.layout, pruned.cost) == (full.status, full.layout, full.cost)
        assert (brute is None) == (pruned.status == "infeasible")
        if brute is not None:
            assert (pruned.cost, pruned.layout) == (brute[0], brute[2])
            if kappa2 is not None:
                problem = layout_problem(options, pruned.layout, CATALOGUE_TARGET)
                assert verify_psd_certificate(amplification_form(problem, kappa2), pruned.certificate)
        comparisons.append({"kappa_max_squared": kappa2, "objective": "kernel" if kappa2 is None else "conditioning",
                            "status": pruned.status, "layout": pruned.identifiers, "cost": pruned.cost,
                            "pruned_tests": pruned.tests, "exhaustive_tests": full.tests,
                            "brute_force_agrees": True})
    frontier = conditioning_frontier(options, CATALOGUE_TARGET, THRESHOLDS, tolerance=TOL)
    cheap = layout_problem(options, (0, 1), CATALOGUE_TARGET)
    direct = layout_problem(options, (0, 2), CATALOGUE_TARGET)
    equal_rank = {
        "cheap_layout": ["cheap_x1", "cheap_x1_weak_x2"], "cheap_cost": F(2),
        "cheap_rank": target_identifiability(cheap).rank,
        "cheap_kappa_squared": bracket_json(bracket_target_amplification(cheap, TOL)),
        "comparison_layout": ["cheap_x1", "direct_x2"], "comparison_cost": F(6),
        "comparison_rank": target_identifiability(direct).rank,
        "comparison_kappa_squared": bracket_json(bracket_target_amplification(direct, TOL)),
    }
    return {"catalogue": [{"id": n, "rows": r, "cost": F(c), "noise_shape_diagonal": [F(w) for w in s]}
                          for n, r, c, s in CATALOGUE_RAW],
            "target": CATALOGUE_TARGET,
            "noise_contract": "joint ellipsoid eta^T R^-1 eta <= eps^2, R block diagonal by sensor",
            "cost_units": "normalized installation units",
            "layout_table": table, "optimum_comparisons": comparisons, "frontier": frontier,
            "equal_rank_example": equal_rank}


# ------------------------------------- NX08-C -------------------------------------

def thermal_setup():
    from singularity.thermal_diagnostics import build_plate_candidates
    nominal = build_plate_candidates(4)[0]
    n = 16
    cells = {"centre": {5, 6, 9, 10}, "edge_ring": {1, 2, 4, 7, 8, 11, 13, 14}, "corners": {0, 3, 12, 15}}
    cols = [tuple(F(int(i in s)) for i in range(n)) for s in cells.values()]
    cols.append(tuple(F(1 if i % 4 < 2 else -1) for i in range(n)))
    q = tuple(tuple(col[i] for col in cols) for i in range(n))
    mean = (tuple(F(1, 16) for _ in range(n)),)
    model = {"entries": [[i, j, v] for i, j, v in nominal.entries], "sensors": nominal.sensors}
    source = {"module": "singularity.thermal_diagnostics.build_plate_candidates",
              "arguments": {"grid": 4}, "candidate": nominal.identifier,
              "model_sha256": hashlib.sha256(json.dumps(enc(model), sort_keys=True,
                                                        separators=(",", ":")).encode()).hexdigest(),
              "input": "zero heater input (free decay); a known input is a subtracted centre",
              "admissible_modes": list(cells) + ["left_right_antisymmetric"],
              "target": "plate-mean excess temperature after 4 steps"}
    units = {"state": "K_model excess temperature", "observations": "K_model excess temperature",
             "target": "K_model excess temperature", "time": "model steps"}
    return nominal, q, mean, source, units


def unit_c():
    start = perf_counter()
    nominal, q, mean, source, units = thermal_setup()
    sweep = []
    for sensors in ((0, 1, 2, 3), (0, 1), (1,), (2, 3), (0,)):
        for times in ((0,), (0, 1), (0, 1, 2)):
            p = thermal_target_problem(nominal, sensors, times, mean, 4, q, units=units)
            sweep.append({"sensors": sensors, "times": times,
                          **bracket_json(bracket_target_amplification(p, TOL))})
    chosen = thermal_target_problem(nominal, (0, 1), (0, 1, 2), mean, 4, q, units=units)
    ident = target_identifiability(chosen)
    br = bracket_target_amplification(chosen, TOL)
    best = minimum_norm_decoder(chosen)
    cert = certify_decoder_norm(chosen, best, br.upper)
    witness = adversarial_witness(chosen, br.lower_witness, best)
    rows = ident.decoder
    row_gain = bracket_decoder_norm(chosen, rows, TOL)
    # Thermal sensor catalogue: each sensor records at steps 0,1,2 (three rows).
    labels = ("corner_mean", "center_mean", "left_center_mean", "right_center_mean")
    costs = (1, 1, 2, 2)
    options = []
    for s, (label, cost) in enumerate(zip(labels, costs)):
        rows_s = thermal_target_problem(nominal, (s,), (0, 1, 2), mean, 0).observations
        options.append(SensorOption(label, rows_s, cost, None, "K_model excess temperature"))
    # chosen.target is the full-state forecast row (1/16) 1^T A^4.
    thermal_frontier = conditioning_frontier(options, chosen.target, (F(1, 2), 1, 3, 200), q,
                                             tolerance=TOL)
    thermal = {
        "source": source, "units": units,
        "sweep": sweep,
        "chosen": {"sensors": ["corner_mean", "center_mean"], "times": [0, 1, 2],
                   "kernel_basis_admissible_coordinates": ident.kernel_basis,
                   "nuisance_interpretation": "left-right antisymmetric mode is invisible and leaves the plate mean unchanged",
                   "kappa_squared": bracket_json(br),
                   "adversarial": {"z": witness.z, "noise_squared": witness.noise_squared,
                                   "target_gap_squared": witness.target_gap_squared,
                                   "attained_ratio": witness.ratio,
                                   "minimum_norm_decoder_errors_squared": witness.decoder_errors_squared,
                                   "certified_error_squared_bound": br.upper * witness.noise_squared,
                                   "conservatism_upper_minus_attained": br.upper - witness.ratio},
                   "row_space_decoder_gain_squared": [row_gain.lower, row_gain.upper]},
        "catalogue_frontier": thermal_frontier,
        "receipt": target_recovery_receipt(chosen, br, cert, source),
    }
    # Synthetic linear forecast: position, velocity, constant bias, decaying mode.
    f = ((1, 1, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, F(1, 2)))
    c = ((1, 0, 1, 1),)
    qf = ((1, 0, 0), (0, 1, 0), (0, 0, 0), (0, 0, 1))
    funits = {"state": ["m", "m/step", "m", "m"], "observations": "m", "target": "m"}
    raw = linear_forecast_problem(f, c, (0, 1, 2), ((1, 0, 0, 0),), 2, units=funits)
    raw_br = bracket_target_amplification(raw)
    horizons = []
    for tau in range(6):
        one = linear_forecast_problem(f, c, (0, 1, 2, 3), ((1, 0, 0, 0),), tau, qf, units=funits)
        two = linear_forecast_problem(f, c, (0, 1, 2, 3), ((1, 0, 0, 0), (0, 1, 0, 0)), tau, qf,
                                      units={**funits, "target": ["m", "m/step"]})
        b1, b2 = bracket_target_amplification(one, TOL), bracket_target_amplification(two, TOL)
        w = adversarial_witness(two, b2.lower_witness, minimum_norm_decoder(two))
        horizons.append({"tau": tau, "position_kappa_squared": bracket_json(b1),
                         "position_velocity_kappa_squared": bracket_json(b2),
                         "adversarial_attained_ratio": w.ratio,
                         "decoder_errors_squared": w.decoder_errors_squared,
                         "noise_squared": w.noise_squared})
    final = linear_forecast_problem(f, c, (0, 1, 2, 3), ((1, 0, 0, 0), (0, 1, 0, 0)), 5, qf,
                                    units={**funits, "target": ["m", "m/step"]})
    fbr = bracket_target_amplification(final, TOL)
    fcert = certify_decoder_norm(final, minimum_norm_decoder(final), fbr.upper)
    forecast = {
        "transition": f, "sensor": c, "observation_times": [0, 1, 2, 3], "units": funits,
        "unconstrained_bias": {"status": raw_br.status, "hidden_witness": raw_br.hidden_witness,
                               "meaning": "position +1 with bias -1 leaves every reading unchanged"},
        "admissible_basis": qf, "admissible_meaning": "calibrated sensor: bias fixed at its known centre 0",
        "horizons": horizons,
        "receipt": target_recovery_receipt(final, fbr, fcert, {"unit": "NX08-C", "example": "forecast tau=5"}),
    }
    print(f"NX08-C computed in {perf_counter() - start:.2f}s")
    return {"thermal": thermal, "forecast": forecast,
            "scope": "exact linear claims for fixed known transitions and declared ellipsoids; "
                     "no calibrated physical, statistical or nonlinear-global claim"}


def build():
    t0 = perf_counter()
    a = unit_a()
    a["tamper"] = tamper_count(a["receipts"])
    t1 = perf_counter()
    b = unit_b()
    t2 = perf_counter()
    c = unit_c()
    print(f"timings (not retained): A {t1 - t0:.2f}s, B {t2 - t1:.2f}s, C {perf_counter() - t2:.2f}s")
    return {"schema": "singularity.nx08-receipt/1", "track": "NX08",
            "tolerance_kappa_squared": TOL,
            "rational_encoding": "[numerator, denominator]",
            "NX08-A": a, "NX08-B": b, "NX08-C": c}


def independent_checks(result):
    receipts = list(result["NX08-A"]["receipts"].values())
    receipts += [result["NX08-C"]["thermal"]["receipt"], result["NX08-C"]["forecast"]["receipt"]]
    for receipt in receipts:
        assert verify_target_recovery_receipt(receipt), receipt["source"]
    tamper = result["NX08-A"]["tamper"]
    assert tamper["tampered"] == tamper["rejected"] > 0
    # Adversarial replays reproduce the claimed ratios and stay below certified bounds.
    for row in result["NX08-C"]["forecast"]["horizons"]:
        br = row["position_velocity_kappa_squared"]
        lo, hi = F(*br["lower"]), F(*br["upper"])
        ratio = F(*row["adversarial_attained_ratio"])
        assert lo <= ratio <= hi
        noise = F(*row["noise_squared"])
        assert all(F(*e) <= hi * noise for e in row["decoder_errors_squared"])
    return len(receipts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    start = perf_counter()
    result = enc(build())
    text = json.dumps(result, indent=1, sort_keys=True) + "\n"
    count = independent_checks(result)
    if args.check:
        stored = TARGET.read_text(encoding="utf-8")
        if stored != text:
            print("NX08 receipt differs from results/target_recovery.json")
            return 1
        print(f"NX08 check passed: {count} receipts replayed, "
              f"{result['NX08-A']['tamper']['rejected']} tampered receipts rejected, "
              f"{perf_counter() - start:.2f}s")
        return 0
    TARGET.write_text(text, encoding="utf-8")
    print(f"wrote {TARGET.relative_to(ROOT)} in {perf_counter() - start:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
