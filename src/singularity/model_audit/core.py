"""Portable behavioral audit packages (standard library only).

An audit package records, for a frozen panel of probe inputs, the reference
model's observations, per-probe tolerances frozen from clean reruns, the
declared execution contract, and evidence that each declared fault is
separated by at least ``requirement`` panel probes. Checking a deployment
needs the package and the deployed model only: no dataset download and no
second forward pass of the reference model.

Observations of one probe are lists keyed by name:

* ``argmax`` and ``continuation`` are discrete token ids, compared exactly at
  positions whose reference top-two log-probability gap exceeds
  ``tie_margin`` (near-ties are not evidence of change);
* ``top_logprob``, ``entropy`` and ``continuation_logprob`` are continuous
  and compared by maximum absolute deviation against the probe tolerance;
* ``top_gap`` is reference-only and defines the tie positions.

A probe *flags* a run when lengths differ, a non-tie discrete value differs,
or a continuous deviation exceeds its tolerance. Tolerances are
``factor * (largest clean deviation) + floor``, with declared factor and
floor. Separation of a fault by a probe means that probe flags the fault's
observations; the panel is chosen by exact minimum-cost r-robust coverage
(``singularity.robust_coverage``), so any ``requirement - 1`` missing probe
results still leave every declared construction fault separated.

Scope: detection of the declared construction faults on the construction
models is exact for the recorded observations. Transfer to other models,
fault strengths or families, and false-alarm rates are empirical questions;
a passing check is not proof that two models are equivalent.
"""
from __future__ import annotations

import hashlib
import json
import math

from ..robust_coverage import (
    check_robust_witness, coverage_problem, greedy_robust_panel, minimum_robust_panel, panel_coverage,
    robust_witness,
)

PACKAGE_SCHEMA = "singularity.audit-package/1"
DISCRETE = ("argmax", "continuation")
CONTINUOUS = ("top_logprob", "entropy", "continuation_logprob")
REFERENCE_ONLY = ("top_gap",)

__all__ = [
    "PACKAGE_SCHEMA", "deviation", "flags", "tolerances_from_clean", "build_package", "check_package",
    "verify_package", "package_digest", "save_package", "load_package",
]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def package_digest(package):
    body = {key: value for key, value in package.items() if key != "package_sha256"}
    return hashlib.sha256(canonical(body)).hexdigest()


def _finite(values, name):
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{name} must contain finite numbers")


def _validate_observation(observation):
    if not isinstance(observation, dict) or "argmax" not in observation:
        raise ValueError("each observation needs at least an argmax list")
    for key, values in observation.items():
        if key not in DISCRETE + CONTINUOUS + REFERENCE_ONLY:
            raise ValueError("unknown observation key " + repr(key))
        if not isinstance(values, list):
            raise ValueError(f"{key} must be a list")
        if key in DISCRETE:
            if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in values):
                raise ValueError(f"{key} must contain token ids")
        else:
            _finite(values, key)
    if "top_gap" in observation and len(observation["top_gap"]) != len(observation["argmax"]):
        raise ValueError("top_gap must align with argmax")


def deviation(observed, expected, tie_margin=0.):
    """Compare one probe's observation with its reference observation."""
    _validate_observation(observed)
    _validate_observation(expected)
    report = {"length_mismatch": False, "discrete_mismatches": 0, "tie_positions_ignored": 0, "max_abs": {}}
    for key in DISCRETE:
        if key not in expected:
            continue
        got, want = observed.get(key), expected[key]
        if got is None or len(got) != len(want):
            report["length_mismatch"] = True
            continue
        gaps = expected.get("top_gap") if key == "argmax" else None
        for index, (a, b) in enumerate(zip(got, want)):
            if a != b:
                if gaps is not None and gaps[index] <= tie_margin:
                    report["tie_positions_ignored"] += 1
                else:
                    report["discrete_mismatches"] += 1
    for key in CONTINUOUS:
        if key not in expected:
            continue
        got, want = observed.get(key), expected[key]
        if got is None or len(got) != len(want):
            report["length_mismatch"] = True
            continue
        report["max_abs"][key] = max((abs(a - b) for a, b in zip(got, want)), default=0.)
    return report


def flags(report, tolerance):
    """Whether a deviation report exceeds a probe's frozen tolerance."""
    if report["length_mismatch"] or report["discrete_mismatches"]:
        return True
    return any(value > tolerance[key] for key, value in report["max_abs"].items())


def tolerances_from_clean(reference, clean_runs, factor, floor, tie_margin):
    """Per-probe continuous tolerances from clean reruns of the reference.

    A clean run with a non-tie discrete change or a length change is a
    reference-instability error, not a tolerance to absorb.
    """
    if isinstance(factor, bool) or not isinstance(factor, (int, float)) or not factor >= 1:
        raise ValueError("tolerance factor must be at least one")
    if isinstance(floor, bool) or not isinstance(floor, (int, float)) or not floor > 0:
        raise ValueError("tolerance floor must be positive")
    if not clean_runs:
        raise ValueError("at least one clean rerun is required")
    tolerances, clean_maxima = [], []
    for index, expected in enumerate(reference):
        largest = {key: 0. for key in CONTINUOUS if key in expected}
        for run in clean_runs:
            report = deviation(run[index], expected, tie_margin)
            if report["length_mismatch"] or report["discrete_mismatches"]:
                raise ValueError(f"clean rerun changed discrete output of probe {index}; reference unstable")
            for key, value in report["max_abs"].items():
                largest[key] = max(largest[key], value)
        clean_maxima.append(largest)
        tolerances.append({key: factor * value + floor for key, value in largest.items()})
    return tolerances, clean_maxima


def _evidence(report, tolerance):
    return {"length_mismatch": report["length_mismatch"], "discrete_mismatches": report["discrete_mismatches"],
            "max_abs": report["max_abs"], "flags": flags(report, tolerance)}


def build_package(probes, reference, clean_runs, faults, *, contract, requirement=2, tolerance_factor=4.,
                  tolerance_floor=1e-6, tie_margin=1e-4, max_nodes=10**6, metadata=None, panel_ids=None):
    """Select a minimum-cost r-robust panel and export a self-contained package.

    ``probes`` are dicts with unique ``id``, nonnegative integer ``cost`` and
    the adapter's input fields (``text`` and optional ``pad_to``,
    ``continuation_tokens``). ``reference`` and each clean run are lists of
    observations aligned with ``probes``; ``faults`` maps a fault label to such
    a list. Only probes, observations and declared constants are used.

    ``panel_ids`` freezes a panel chosen elsewhere (for example on other
    checkpoints). Its coverage is then only reported: faults it fails to
    separate ``requirement`` times are listed as ``deficient_faults``, have no
    witness row, and make ``verify_package`` fail.
    """
    if not probes or len(reference) != len(probes) or any(len(run) != len(probes) for run in clean_runs):
        raise ValueError("observations must align with probes")
    ids = [probe["id"] for probe in probes]
    if len(set(ids)) != len(ids):
        raise ValueError("probe ids must be unique")
    if not faults:
        raise ValueError("declare at least one construction fault")
    for observation in reference:
        _validate_observation(observation)
    tolerances, clean_maxima = tolerances_from_clean(reference, clean_runs, tolerance_factor, tolerance_floor, tie_margin)
    labels = list(faults)
    reports = {label: [deviation(faults[label][e], reference[e], tie_margin) for e in range(len(probes))]
               for label in labels}
    separates = [[flags(reports[label][e], tolerances[e]) for label in labels] for e in range(len(probes))]
    problem = coverage_problem([probe["cost"] for probe in probes], separates, ids, labels)
    exact = minimum_robust_panel(problem, requirement, max_nodes=max_nodes)
    greedy = greedy_robust_panel(problem, requirement)
    selection = {"requirement": requirement, "feasible": exact.feasible,
                 "deficient_faults": [labels[p] for p in exact.deficient],
                 "pool_probe_count": len(probes), "pool_cost": sum(probe["cost"] for probe in probes),
                 "pool_separator_counts": {labels[p]: len(cover) for p, cover in enumerate(problem.coverers)},
                 "exact_cost": None if exact.cost is None else int(exact.cost) if exact.cost.denominator == 1 else str(exact.cost),
                 "exact_nodes": exact.nodes,
                 "greedy_cost": None if greedy.cost is None else int(greedy.cost) if greedy.cost.denominator == 1 else str(greedy.cost),
                 "greedy_panel": None if greedy.panel is None else [ids[e] for e in greedy.panel]}
    if panel_ids is not None:
        if len(set(panel_ids)) != len(panel_ids) or not set(panel_ids) <= set(ids):
            raise ValueError("panel_ids must be distinct pool probe ids")
        panel = sorted(ids.index(probe_id) for probe_id in panel_ids)
        selection["frozen_panel"] = True
    elif not exact.feasible:
        raise ValueError("no panel meets the requirement; deficient faults: " + ", ".join(selection["deficient_faults"]))
    else:
        panel = list(exact.panel)
    coverage = dict(zip(labels, panel_coverage(problem, panel)))
    deficient = [label for label in labels if coverage[label] < requirement]
    covered = [p for p, label in enumerate(labels) if coverage[label] >= requirement]
    witness_problem = coverage_problem([probe["cost"] for probe in probes],
                                       [[separates[e][p] for p in covered] for e in range(len(probes))],
                                       ids, [labels[p] for p in covered]) if covered else None
    package = {
        "schema": PACKAGE_SCHEMA,
        "contract": contract,
        "constants": {"tolerance_factor": tolerance_factor, "tolerance_floor": tolerance_floor, "tie_margin": tie_margin},
        "requirement": requirement,
        "probes": [{**probes[e], "expected": reference[e], "tolerance": tolerances[e], "clean_maximum": clean_maxima[e]}
                   for e in panel],
        "fault_evidence": {label: {ids[e]: _evidence(reports[label][e], tolerances[e]) for e in panel} for label in labels},
        "coverage": coverage,
        "deficient_faults": deficient,
        "witness": robust_witness(witness_problem, panel, requirement) if witness_problem else [],
        "selection": selection,
        "metadata": metadata or {},
        "claim_boundary": ("Every listed construction fault flags at least `requirement` panel probes on the "
                           "construction observations, so that many minus one missing results cannot hide it there. "
                           "Other models, faults and false-alarm rates are empirical; passing is not equivalence."),
    }
    package["package_sha256"] = package_digest(package)
    return package


def verify_package(package):
    """Model-free check of a package's integrity and robust-coverage witness.

    Separation is recomputed from stored fault deviations and tolerances, not
    from the stored ``flags`` booleans or coverage counts.
    """
    problems = []
    if package.get("schema") != PACKAGE_SCHEMA:
        problems.append("unsupported schema")
    if package.get("package_sha256") != package_digest(package):
        problems.append("package digest mismatch")
    probes = {probe["id"]: probe for probe in package.get("probes", [])}
    evidence = package.get("fault_evidence", {})

    def separates(probe_id, fault):
        record = evidence[fault][probe_id]
        report = {"length_mismatch": record["length_mismatch"], "discrete_mismatches": record["discrete_mismatches"],
                  "max_abs": record["max_abs"]}
        return flags(report, probes[probe_id]["tolerance"])

    requirement = package.get("requirement", 0)
    deficient = list(package.get("deficient_faults", []))
    if deficient:
        problems.append("declared deficient faults: " + ", ".join(deficient))
    try:
        witness_ok = check_robust_witness(package["witness"], probes, requirement,
                                          [fault for fault in evidence if fault not in deficient], separates)
    except (KeyError, TypeError):
        witness_ok = False
    if not witness_ok:
        problems.append("robust-coverage witness does not verify")
    for fault, rows in evidence.items():
        if set(rows) != set(probes):
            problems.append(f"fault evidence for {fault} does not cover the panel")
            continue
        count = sum(separates(probe_id, fault) for probe_id in probes)
        if count < requirement:
            problems.append(f"{fault} is separated by {count} < {requirement} panel probes")
    for probe in probes.values():
        try:
            _validate_observation(probe["expected"])
        except (KeyError, ValueError) as error:
            problems.append(f"probe {probe.get('id')}: {error}")
    return {"verified": not problems, "problems": problems, "panel_probes": len(probes),
            "faults": len(evidence), "requirement": requirement}


def check_package(package, observe, contract, *, missing=()):
    """Check a deployment: ``observe(probes)`` returns observations in order.

    ``missing`` lists probe ids whose results are unavailable; they are not
    observed and the report states which declared faults the remaining panel
    still separates on the construction evidence.
    """
    verification = verify_package(package)
    if not verification["verified"]:
        raise ValueError("package failed verification: " + "; ".join(verification["problems"]))
    missing = set(missing)
    unknown = missing - {probe["id"] for probe in package["probes"]}
    if unknown:
        raise ValueError("unknown missing probe ids: " + ", ".join(sorted(unknown)))
    declared = package["contract"]
    mismatches = sorted(key for key in set(declared) | set(contract) if declared.get(key) != contract.get(key))
    active = [probe for probe in package["probes"] if probe["id"] not in missing]
    inputs = [{key: value for key, value in probe.items()
               if key not in ("expected", "tolerance", "clean_maximum")} for probe in active]
    observations = observe(inputs) if inputs else []
    if len(observations) != len(active):
        raise ValueError("observe returned the wrong number of observations")
    tie_margin = package["constants"]["tie_margin"]
    rows = []
    for probe, observation in zip(active, observations):
        report = deviation(observation, probe["expected"], tie_margin)
        rows.append({"probe": probe["id"], "flags": flags(report, probe["tolerance"]), **report})
    remaining = {probe["id"] for probe in active}
    still_separated = {fault: sum(1 for probe_id, record in rows_.items() if probe_id in remaining and record["flags"])
                       for fault, rows_ in package["fault_evidence"].items()}
    flagged = [row["probe"] for row in rows if row["flags"]]
    return {"verdict": "changed" if flagged or mismatches else "unchanged",
            "contract_mismatches": [{"key": key, "declared": declared.get(key), "deployed": contract.get(key)}
                                    for key in mismatches],
            "flagged_probes": flagged, "probes": rows, "missing_probes": sorted(missing),
            "construction_faults_still_separated": {fault: count >= 1 for fault, count in still_separated.items()},
            "package_sha256": package["package_sha256"],
            "interpretation": "A flag means executed behavior differs from the reference beyond frozen clean tolerances; "
                              "unchanged means no declared observation moved, not that the models are equivalent."}


def save_package(package, path):
    from pathlib import Path
    raw = json.dumps(package, indent=1, sort_keys=True, allow_nan=False) + "\n"
    Path(path).write_text(raw)
    return hashlib.sha256(raw.encode()).hexdigest()


def load_package(path):
    from pathlib import Path
    package = json.loads(Path(path).read_text())
    if package.get("schema") != PACKAGE_SCHEMA:
        raise ValueError("unsupported audit package schema")
    return package
