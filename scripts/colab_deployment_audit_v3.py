#!/usr/bin/env python3
"""Prospective v3: exact multicover of measured faults AND all caps 1..T.

python scripts/colab_deployment_audit_v3.py --output deployment_audit_v3_RUN
python scripts/colab_deployment_audit_v3.py --phase verify --output deployment_audit_v3_RUN

Requires the optional pretrained dependencies and a GPU, or --local-test for
a tiny random CPU model. Does not install dependencies, pull branches, alter
v2, or claim new GPU results. Panels are frozen before any evaluation runs.
The shape theorem is conditional on returning every retained token's logits.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SPEC = importlib.util.spec_from_file_location("frozen_v2_adapter", ROOT / "scripts/colab_deployment_audit_v2.py")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
from singularity.model_audit.core import build_package, check_package, verify_package, deviation, flags, tolerances_from_clean
from singularity.model_audit.truncation import OBSERVABILITY, specification, compare, certificate, verify_certificate

SCHEMA = "singularity.gpu-deployment-audit/3"
# Original v2 faults are exposed retests. Position-offset fault is diagnostic:
# it was invisible to the original pool, and RoPE can be shift invariant.
CONSTRUCTION = {k: v for k, v in base.CONSTRUCTION.items() if k != "positions_not_offset_for_left_padding"}
DIAGNOSTIC = {"positions_not_offset_for_left_padding": base.CONSTRUCTION["positions_not_offset_for_left_padding"]}
NEW_HELDOUT = {"alternating_attention_mask": {"wrapper": "alternating_mask"},
               "output_vocabulary_permutation": {"wrapper": "vocabulary_permutation"},
               "uniform_logit_translation": {"wrapper": "logit_translation"}}


def write(path, value):
    base.write_json(path, value)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bindings():
    return {p: file_hash(ROOT / p) for p in ("scripts/colab_deployment_audit_v3.py", "scripts/colab_deployment_audit_v2.py",
            "src/singularity/model_audit/truncation.py", "src/singularity/model_audit/core.py", "src/singularity/robust_coverage.py")}


def long_probe(tokenizer, name, target, sentence):
    text = sentence
    while len(tokenizer(text, add_special_tokens=False)["input_ids"]) < target:
        text += " " + sentence
    tokens = tokenizer(text, add_special_tokens=False)["input_ids"]
    candidate = tokenizer.decode(tokens[:target], skip_special_tokens=False)
    if len(tokenizer(candidate, add_special_tokens=False)["input_ids"]) >= target:
        text = candidate
    n = len(tokenizer(text, add_special_tokens=False)["input_ids"])
    return {"id": name, "text": text, "tokens": n, "cost": n}


def freeze(args, output):
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("output must be a new empty directory; frozen v2 directories cannot be reused")
    if not 1 <= args.maximum_cap <= 192:
        raise ValueError("maximum-cap must be in 1..192 (runner context budget)")
    from transformers import AutoTokenizer
    import torch
    import transformers
    machine = base.hardware()
    if args.local_test:
        model, revision, dtype = base.local_test_model(output.parent / "v3_local_test_model"), None, "float32"
    else:
        if machine["device"] != "cuda":
            raise RuntimeError("a GPU is required; --local-test is a separate random-model CPU smoke test")
        model = args.model or base.choose_model(machine)
        revision = base.resolve_revision(model)
        dtype = "bfloat16" if machine["bf16"] else "float16"
    tokenizer = AutoTokenizer.from_pretrained(model, **({"revision": revision} if revision else {}))
    probes = base.probe_records(tokenizer)
    probes += [long_probe(tokenizer, "length_guard_history", args.maximum_cap + 1,
                         "The archive records each voyage, its departure date, cargo and destination, so that later readers can reconstruct the complete journey."),
               long_probe(tokenizer, "length_guard_experiment", args.maximum_cap + 1,
                          "The laboratory notebook records each measurement, the instrument setting and the time of observation, allowing another researcher to repeat the experiment.")]
    tokenized = [tokenizer(p["text"], add_special_tokens=False)["input_ids"] for p in probes]
    if tokenized[-1] == tokenized[-2]:
        raise ValueError("length guards must have distinct token sequences")
    # No fault observations enter this check. Padding is not counted as length.
    if sum(p["tokens"] > args.maximum_cap for p in probes) < 2:
        raise ValueError("pool cannot support the declared cap family")
    construction = copy.deepcopy(CONSTRUCTION)
    if args.local_test:
        construction.pop("int8_bitsandbytes")  # explicitly absent from CPU protocol
    protocol = {"schema": SCHEMA, "version": 3, "frozen_at_utc": base.now(), "model": model, "revision": revision,
                "dtype": dtype, "hardware": machine, "local_test": args.local_test,
                "software": {"python": sys.version.split()[0], "torch": torch.__version__, "transformers": transformers.__version__},
                "code_sha256": bindings(), "probes": probes, "maximum_cap": args.maximum_cap, "requirement": 2,
                "observation_contract": OBSERVABILITY,
                "tokenizer_vocabulary_sha256": base.sha(json.dumps(sorted(tokenizer.get_vocab().items())).encode()),
                "probe_token_ids_sha256": base.sha(base.canonical(tokenized)),
                "construction_variants": construction, "diagnostic_variants": DIAGNOSTIC,
                "calibration_clean_runs": base.CALIBRATION, "validation_clean_runs": base.VALIDATION,
                "tolerance": base.TOLERANCE, "representative_ids": base.TYPICAL,
                "known_v2_retests": base.HELDOUT,
                "family_implementation_checks": {f"suffix_cap_{t}": {"truncate_to": t} for t in sorted({1, 32, 48, 64, 72, 96, args.maximum_cap}) if t <= args.maximum_cap},
                "new_heldout_variants": NEW_HELDOUT,
                "candidate_configurations": base.CANDIDATES,
                "selection": "minimum-cost two-witness multicover of every declared construction variant and every integer cap 1..maximum_cap; any deficient column aborts selection",
                "cost": "pad width (or real input length) plus continuation steps; same cost for all selectors",
                "lineage": "V2 unchanged; all nine old held-out cases are known retests. Family implementation checks are inside the declared shape family, not out-of-family generalization.",
                "claim_boundary": "Shape theorem assumes non-fabricating full teacher-forced observations. No guarantee for generation-only or full-shaped hidden-context truncation. No A100 transfer claim."}
    protocol["protocol_sha256"] = base.sha(base.canonical(protocol))
    output.mkdir(parents=True, exist_ok=True)
    write(output / "protocol.json", protocol)
    return protocol


def checked_protocol(output, require_code=True):
    p = json.loads((output / "protocol.json").read_text())
    if p.get("schema") != SCHEMA or p["protocol_sha256"] != base.sha(base.canonical({k: v for k, v in p.items() if k != "protocol_sha256"})):
        raise ValueError("protocol identity mismatch")
    if require_code and p["code_sha256"] != bindings():
        raise ValueError("code changed after freezing")
    return p


class WrappedModel:
    """Faults at the model boundary, excluded from construction/selection."""
    def __init__(self, model, kind, torch):
        self.model, self.kind, self.torch = model, kind, torch
    def __getattr__(self, name):
        return getattr(self.model, name)
    def __call__(self, **kwargs):
        if self.kind == "alternating_mask" and "attention_mask" in kwargs:
            kwargs = dict(kwargs)
            mask = kwargs["attention_mask"].clone()
            mask[:, ::2] = 0
            mask[:, -1] = 1
            kwargs["attention_mask"] = mask
        result = self.model(**kwargs)
        if self.kind == "vocabulary_permutation":
            result.logits = result.logits.roll(1, dims=-1)
        elif self.kind == "logit_translation":
            result.logits = result.logits + 1.0
        return result


def capture(deployment, probes, change):
    if "wrapper" in change:
        return base.observe(deployment, WrappedModel(deployment.model, change["wrapper"], deployment.torch), probes, {})
    return base.run_change(deployment, probes, change)


def calibrated(protocol, observed):
    """Checks full shapes and finite calibration BEFORE stabilization."""
    n = len(protocol["probes"])
    reference = observed["reference/reference"]
    calibration = [observed["calibration/" + k] for k in protocol["calibration_clean_runs"]]
    for run in [reference, *calibration]:
        if len(run) != n:
            raise ValueError("misaligned observations")
        for p, row in zip(protocol["probes"], run):
            if len(row["argmax"]) != p["tokens"] or any(len(row[k]) != p["tokens"] for k in ("top_logprob", "top_gap", "entropy")):
                raise ValueError("clean full teacher-forced shape is unstable")
            if any(not math.isfinite(v) for k, values in row.items() if k not in ("argmax", "continuation") for v in values):
                raise base.NumericalHealthFailure("reference/calibration non-finite; cannot calibrate")
    spec = protocol["tolerance"]
    stable, ties, prefixes = base.stabilize(reference, calibration, spec["tie_margin"])
    shown = [base.views(run, stable) for run in calibration]
    tolerance, maxima = tolerances_from_clean(stable, shown, spec["factor"], spec["floor"], spec["tie_margin"])
    return stable, shown, tolerance, {"ties_added": ties, "prefixes": prefixes, "maxima": maxima}


def selection(protocol, observed):
    stable, clean, tolerance, stabilization = calibrated(protocol, observed)
    margin = protocol["tolerance"]["tie_margin"]
    rows = {k: base.views(observed["construction/" + k], stable) for k in protocol["construction_variants"]}
    table = {k: [flags(deviation(o, r, margin), t) for o, r, t in zip(run, stable, tolerance)] for k, run in rows.items()}
    spec = specification(protocol["probes"], table, protocol["maximum_cap"], protocol["requirement"])
    compared = compare(spec, protocol["representative_ids"])
    return stable, clean, tolerance, stabilization, rows, spec, compared


def run(output):
    protocol = checked_protocol(output)
    if (output / "selection_started.json").exists():
        raise FileExistsError("run already started; use a fresh output directory")
    write(output / "selection_started.json", {"protocol_sha256": protocol["protocol_sha256"], "started_at_utc": base.now()})
    deployment = base.deployment_for(protocol, output)
    observed, health = {}, {}
    probes = protocol["probes"]
    if "probe_token_ids_sha256" in protocol:
        tokenized = [deployment.tokenizer(p["text"], add_special_tokens=False)["input_ids"] for p in probes]
        vocabulary = base.sha(json.dumps(sorted(deployment.tokenizer.get_vocab().items())).encode())
        if base.sha(base.canonical(tokenized)) != protocol["probe_token_ids_sha256"] or vocabulary != protocol["tokenizer_vocabulary_sha256"]:
            raise ValueError("tokenizer changed after freeze")

    def take(group, name, change):
        rows = capture(deployment, probes, change)
        if rows is None:
            raise RuntimeError(f"declared variant unavailable: {group}/{name}; no silent exclusion")
        counts = base.nonfinite_by_probe(rows)
        key = group + "/" + name
        if any(counts):
            health[key] = {p["id"]: c for p, c in zip(probes, counts) if c}
            write(output / "numerical_health.json", health)
            if group in ("reference", "calibration", "construction"):
                raise base.NumericalHealthFailure(key + ": unhealthy selection data; refusing a numerical-failure coverage certificate")
        observed[key] = rows
        write(output / "observations.json", observed)

    take("reference", "reference", {})
    for name, change in protocol["calibration_clean_runs"].items():
        take("calibration", name, change)
    # Fail before collecting faults if calibration is unhealthy/shape unstable.
    calibrated(protocol, observed)
    for name, change in protocol["construction_variants"].items():
        take("construction", name, change)
    stable, clean, tolerance, stabilization, construction_rows, spec, compared = selection(protocol, observed)
    if not compared["feasible"]:
        write(output / "infeasible.json", compared)
        raise ValueError("declared family infeasible; see infeasible.json, enlarge pool in a NEW protocol")
    frozen = {"protocol_sha256": protocol["protocol_sha256"], "frozen_at_utc": base.now(),
              "construction_observations_sha256": file_hash(output / "observations.json"),
              "comparison": compared, "before_evaluation": True}
    write(output / "frozen_panels.json", frozen)
    # All evaluation families first observed AFTER the panel file exists.
    for group, variants in (("known_v2_retest", protocol["known_v2_retests"]),
                            ("family_check", protocol["family_implementation_checks"]),
                            ("new_heldout", protocol["new_heldout_variants"]),
                            ("validation", protocol["validation_clean_runs"]),
                            ("diagnostic", protocol["diagnostic_variants"]),
                            ("candidate", protocol["candidate_configurations"])):
        for name, change in variants.items():
            # CPU smoke test cannot run bitsandbytes; it remains explicitly skipped.
            if protocol["local_test"] and change.get("load") in ("int8", "nf4"):
                continue
            take(group, name, change)
    evaluation = evaluate(protocol, observed, stable, tolerance, compared, health)
    package = build_package(probes, stable, clean, construction_rows, contract=deployment.contract(),
                            requirement=2, tolerance_factor=protocol["tolerance"]["factor"],
                            tolerance_floor=protocol["tolerance"]["floor"], tie_margin=protocol["tolerance"]["tie_margin"],
                            panel_ids=compared["panels"]["exact"]["probe_ids"],
                            metadata={"version": 3, "protocol_sha256": protocol["protocol_sha256"],
                                      "shape_certificate": "certificate.json", "shape_claim_requires_full_teacher_forced_observer": True})
    if not verify_package(package)["verified"]:
        raise ArithmeticError("portable construction package failed")
    write(output / "package.json", package)
    cert = certificate(spec, compared, {"protocol_sha256": protocol["protocol_sha256"],
                                      "observations_sha256": file_hash(output / "observations.json"),
                                      "package_sha256": file_hash(output / "package.json")})
    if not verify_certificate(cert):
        raise ArithmeticError("independent multicover certificate failed")
    write(output / "certificate.json", cert)
    write(output / "results.json", {"schema": SCHEMA, "completed_at_utc": base.now(), "protocol_sha256": protocol["protocol_sha256"],
                                   "local_test": protocol["local_test"], "comparison": compared, "evaluation": evaluation,
                                   "numerical_health": health, "stabilization": stabilization,
                                   "skipped": ["known_v2_retest/nf4_4bit_bitsandbytes"] if protocol["local_test"] else [],
                                   "claim_boundary": protocol["claim_boundary"]})
    verify(output)
    print(json.dumps({"panels": {k: {"cost": v["cost"], "satisfies_requirement": v["satisfies_requirement"]} for k, v in compared["panels"].items()},
                      "verified": True, "output": str(output)}, indent=2))


def evaluate(protocol, observed, stable, tolerances, compared, health):
    tables = {}
    for key, rows in observed.items():
        if key.split("/")[0] in ("reference", "calibration"):
            continue
        if len(rows) != len(stable):
            raise ValueError("misaligned evaluation observations")
        tables[key] = [flags(deviation(o, r, protocol["tolerance"]["tie_margin"]), t)
                       for o, r, t in zip(base.views(rows, stable), stable, tolerances)]
    for name, change in protocol["family_implementation_checks"].items():
        rows = observed.get("family_check/" + name)
        if rows is None or any(len(row["argmax"]) != min(p["tokens"], change["truncate_to"]) for p, row in zip(protocol["probes"], rows)):
            raise ValueError("family check violates declared shape observability")
    out = {}
    for name, panel in compared["panels"].items():
        counts = {k: sum(col[e] for e in panel["indices"]) for k, col in tables.items()}
        out[name] = {"separators": counts,
                     "false_alarms": [k for k, c in counts.items() if k.startswith("validation/") and c],
                     "new_heldout_missed": [k for k, c in counts.items() if k.startswith("new_heldout/") and not c],
                     "candidate_status": {k: ("not_approved_numerical_health" if k in health else "not_approved_behavior_change" if any(tables[k]) else "approved_for_tested_configuration") for k in tables if k.startswith("candidate/")}}
    return out


def verify(output):
    protocol = checked_protocol(output, require_code=True)
    observed = json.loads((output / "observations.json").read_text())
    stable, clean, tolerance, stabilization, rows, spec, compared = selection(protocol, observed)
    required_keys = {"reference/reference"}
    for group, field in (("calibration", "calibration_clean_runs"), ("construction", "construction_variants"),
                         ("known_v2_retest", "known_v2_retests"), ("family_check", "family_implementation_checks"),
                         ("new_heldout", "new_heldout_variants"), ("validation", "validation_clean_runs"),
                         ("diagnostic", "diagnostic_variants"), ("candidate", "candidate_configurations")):
        required_keys.update(group + "/" + k for k, change in protocol[field].items()
                             if not (protocol["local_test"] and change.get("load") in ("int8", "nf4")))
    if set(observed) != required_keys:
        raise ValueError("evaluation or construction rows missing/undeclared")
    cert = json.loads((output / "certificate.json").read_text())
    frozen = json.loads((output / "frozen_panels.json").read_text())
    result = json.loads((output / "results.json").read_text())
    # Bind the pre-evaluation snapshot even though observations.json now also
    # contains evaluation rows. Canonical encoding matches base.write_json.
    snapshot = {k: v for k, v in observed.items() if k.startswith(("reference/", "calibration/", "construction/"))}
    snapshot_bytes = (json.dumps(snapshot, indent=1, sort_keys=True, allow_nan=False) + "\n").encode()
    if hashlib.sha256(snapshot_bytes).hexdigest() != frozen["construction_observations_sha256"]:
        raise ValueError("frozen construction snapshot differs")
    if frozen["comparison"] != compared or cert["specification"] != spec or cert["comparison"] != compared or not verify_certificate(cert):
        raise ValueError("selection certificate replay differs")
    if cert["provenance"] != {"protocol_sha256": protocol["protocol_sha256"], "observations_sha256": file_hash(output / "observations.json"), "package_sha256": file_hash(output / "package.json")}:
        raise ValueError("source binding mismatch")
    package = json.loads((output / "package.json").read_text())
    if not verify_package(package)["verified"]:
        raise ValueError("package failed verification")
    if [p["id"] for p in package["probes"]] != compared["panels"]["exact"]["probe_ids"]:
        raise ValueError("package selected a different panel")
    # Numerical failures were serialized as -1e9 sentinels, with explicit
    # counts. Recount them instead of trusting a candidate approval label.
    reconstructed_health = {}
    for key, run_rows in observed.items():
        counts = {p["id"]: sum(v == -1e9 for name, values in row.items()
                               if name not in ("argmax", "continuation") for v in values)
                  for p, row in zip(protocol["probes"], run_rows)}
        if any(counts.values()):
            reconstructed_health[key] = {k: n for k, n in counts.items() if n}
    if reconstructed_health != result["numerical_health"] or any(k.startswith(("reference/", "calibration/", "construction/")) for k in reconstructed_health):
        raise ValueError("numerical-health receipt differs or selection data unhealthy")
    expected_package = build_package(protocol["probes"], stable, clean, rows, contract=package["contract"],
                                     requirement=2, tolerance_factor=protocol["tolerance"]["factor"],
                                     tolerance_floor=protocol["tolerance"]["floor"], tie_margin=protocol["tolerance"]["tie_margin"],
                                     panel_ids=compared["panels"]["exact"]["probe_ids"],
                                     metadata={"version": 3, "protocol_sha256": protocol["protocol_sha256"],
                                               "shape_certificate": "certificate.json", "shape_claim_requires_full_teacher_forced_observer": True})
    if expected_package != package:
        raise ValueError("package does not match raw construction evidence")
    replay = evaluate(protocol, observed, stable, tolerance, compared, reconstructed_health)
    if result["evaluation"] != replay or result["comparison"] != compared or result["protocol_sha256"] != protocol["protocol_sha256"]:
        raise ValueError("evaluation replay differs")
    if not frozen["before_evaluation"] or not protocol["frozen_at_utc"] <= frozen["frozen_at_utc"] <= result["completed_at_utc"]:
        raise ValueError("phase order inconsistent")
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=Path("deployment_audit_v3_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")))
    p.add_argument("--maximum-cap", type=int, default=127)
    p.add_argument("--model")
    p.add_argument("--local-test", action="store_true")
    p.add_argument("--phase", choices=("all", "freeze", "run", "verify"), default="all")
    args = p.parse_args()
    if args.phase in ("all", "freeze"):
        freeze(args, args.output)
    if args.phase in ("all", "run"):
        run(args.output)
    if args.phase == "verify":
        verify(args.output)
        print("Verified v3 observations, frozen panels, package and independent optimum")

if __name__ == "__main__":
    main()
